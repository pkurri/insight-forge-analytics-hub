"""
Vector Embedding API Service

This module provides an API-centric approach for generating vector embeddings
and interacting with the vector database for semantic search capabilities.
"""

from datetime import date, datetime
import aiohttp
import json
import concurrent
import asyncpg
import pandas as pd
import logging
import math
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
from typing import Dict, List, Any, Optional, Union

from api.config.settings import get_settings
from api.db.connection import execute_query, execute_command, get_db_connection

logger = logging.getLogger(__name__)
settings = get_settings()

# Define supported embedding models
EMBEDDING_MODELS = {
    "all-MiniLM-L6-v2": {
        "id": "all-MiniLM-L6-v2",
        "name": "all-MiniLM-L6-v2",
        "provider": "huggingface",
        "dimensions": 384,
        "description": "General purpose embedding model for text similarity",
        "endpoint": "sentence-transformers/all-MiniLM-L6-v2"
    },
    "nomic-embed-text-v1.5": {
        "id": "nomic-embed-text-v1.5",
        "name": "Nomic Embed Text v1.5",
        "provider": "huggingface",
        "dimensions": 768,
        "description": "High-quality text embeddings for semantic search",
        "endpoint": "nomic-ai/nomic-embed-text-v1.5"
    },
    "roberta-base-go_emotions-SapBERT": {
        "id": "roberta-base-go_emotions-SapBERT",
        "name": "RoBERTa Emotions SapBERT",
        "provider": "huggingface",
        "dimensions": 768,
        "description": "Emotion-aware text embeddings",
        "endpoint": "cambridgeltl/roberta-base-go_emotions-SapBERT"
    },
    "BioLinkBERT-large": {
        "id": "BioLinkBERT-large",
        "name": "BioLinkBERT Large",
        "provider": "huggingface",
        "dimensions": 1024,
        "description": "Specialized for biomedical text",
        "endpoint": "michiyasunaga/BioLinkBERT-large"
    }
}

# Define supported text generation models
TEXT_GEN_MODELS = {
    "Mistral-3.2-instruct": {
        "id": "Mistral-3.2-instruct",
        "name": "Mistral 3.2 Instruct",
        "provider": "internal",
        "description": "Mistral's latest instruction-tuned model",
        "max_tokens": 8192
    },
    "llama-3.3-70b-instruct": {
        "id": "llama-3.3-70b-instruct",
        "name": "Llama 3.3 70B Instruct",
        "provider": "internal",
        "description": "Meta's largest instruction-tuned model",
        "max_tokens": 8192
    },
    "pythia28b": {
        "id": "pythia28b",
        "name": "Pythia 28B",
        "provider": "internal",
        "description": "EleutherAI's Pythia model",
        "max_tokens": 4096
    }
}

class VectorEmbeddingAPI:
    def __init__(self, endpoint=None, api_key=None):
        """
        Initialize the Vector Embedding API client.
        
        Args:
            endpoint: API endpoint for vector embeddings
            api_key: API key for authentication
        """
        self.endpoint = endpoint or settings.VECTOR_EMBEDDING_API_ENDPOINT
        self.api_key = api_key or settings.VECTOR_EMBEDDING_API_KEY
        self.batch_size = getattr(settings, "VECTOR_BATCH_SIZE", 10000)
        
    async def delete_dataset_vectors(self, dataset_id: int) -> dict:
        """
        Delete all vector embeddings for a dataset from the vector database.
        
        Args:
            dataset_id: ID of the dataset to delete vectors for
            
        Returns:
            Dictionary with deletion results
        """
        try:
            logger.info(f"Deleting vector embeddings for dataset {dataset_id}")
            
            # Get database connection pool
            from api.db.connection import get_db_pool
            pool = await get_db_pool()
            
            # Start a transaction to ensure atomicity
            async with pool.acquire() as conn:
                async with conn.transaction():
                    # Count vectors before deletion for reporting
                    count_result = await conn.fetchval(
                        "SELECT COUNT(*) FROM vector_embeddings WHERE dataset_id = $1",
                        dataset_id
                    )
                    
                    # Delete all vectors for the dataset
                    await conn.execute(
                        "DELETE FROM vector_embeddings WHERE dataset_id = $1",
                        dataset_id
                    )
                    
                    # Update dataset status
                    await conn.execute(
                        """UPDATE datasets 
                           SET vectorized = FALSE, vectorized_at = NULL 
                           WHERE id = $1""",
                        dataset_id
                    )
                    
                    # Update dataset metadata
                    dataset_row = await conn.fetchrow(
                        "SELECT metadata FROM datasets WHERE id = $1",
                        dataset_id
                    )
                    
                    if dataset_row and dataset_row['metadata']:
                        metadata = dataset_row['metadata']
                        if isinstance(metadata, str):
                            try:
                                metadata = json.loads(metadata)
                            except json.JSONDecodeError:
                                metadata = {}
                        else:
                            metadata = {}
                            
                        # Remove vector-related metadata
                        keys_to_remove = [
                            'embedding_model', 'embedding_model_dimensions',
                            'embedding_timestamp', 'vectorized', 'vectorized_at',
                            'total_vectors', 'vector_model'
                        ]
                        
                        for key in keys_to_remove:
                            if key in metadata:
                                del metadata[key]
                        
                        # Save updated metadata
                        await conn.execute(
                            "UPDATE datasets SET metadata = $1 WHERE id = $2",
                            json.dumps(metadata),
                            dataset_id
                        )
            
            return {
                "success": True,
                "dataset_id": dataset_id,
                "deleted_count": count_result or 0,
                "message": f"Successfully deleted {count_result or 0} vector embeddings for dataset {dataset_id}"
            }
            
        except Exception as e:
            logger.error(f"Error deleting vector embeddings for dataset {dataset_id}: {str(e)}")
            return {
                "success": False,
                "dataset_id": dataset_id,
                "error": str(e),
                "message": f"Failed to delete vector embeddings for dataset {dataset_id}: {str(e)}"
            }
        
    async def invoke_api(self, inputs, config, dataset_id):
        """
        Invoke the vector embedding API to generate embeddings.
        
        Args:
            inputs: List of text inputs to generate embeddings for
            config: Configuration for the API call
            dataset_id: ID of the dataset being processed
            
        Returns:
            API response with generated embeddings
        """
        api_endpoint = config.VECTOR_EMBEDDING_API_ENDPOINT
        api_key = config.VECTOR_EMBEDDING_API_KEY
        batch_size = config.VECTOR_BATCH_SIZE
        
        headers = {"Authorization": f"Basic {api_key}"}
        
        # Get database connection pool
        from api.db.connection import get_db_pool
        pool = await get_db_pool()
        
        logger.info("Connected to PostgreSQL database")
        
        num_batches = math.ceil(len(inputs) / batch_size)
        logger.info(f"Number of batches: {num_batches}")
        
        logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Define async function for batch processing
        async def process_batch(batch_num):
            start_index = batch_num * batch_size
            end_index = min((batch_num + 1) * batch_size, len(inputs))
            
            batch_inputs = inputs[start_index:end_index]
            
            json_object = json.dumps(batch_inputs, default=lambda o: o.isoformat() if isinstance(o, (datetime, date)) else None)
            data = {"inputs": json_object}
            
            try:
                # Make API request using aiohttp
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.post(
                            api_endpoint,
                            headers=headers,
                            json=data
                        ) as response:
                            response_text = await response.text()
                            
                            if response.status == 200:
                                try:
                                    batch_vectors = json.loads(response_text) if isinstance(response_text, str) else response_text
                                    
                                    # Get connection from pool
                                    async with pool.acquire() as conn:
                                        # Insert vectors into database
                                        values_list = []
                                        for i, vector in enumerate(batch_vectors):
                                            record_id = f"batch_{batch_num}_item_{i}"
                                            values_list.append((
                                                dataset_id,
                                                record_id,
                                                batch_inputs[i],  # content
                                                batch_num * batch_size + i,  # chunk_index
                                                batch_inputs[i],  # chunk_text
                                                vector,  # embedding
                                                json.dumps({"batch": batch_num, "index": i})  # metadata
                                            ))
                                        
                                        # Execute batch insert
                                        await conn.executemany(
                                            """
                                            INSERT INTO vector_embeddings 
                                                (dataset_id, record_id, content, chunk_index, chunk_text, embedding, vector_metadata)
                                            VALUES 
                                                ($1, $2, $3, $4, $5, $6::vector, $7::jsonb)
                                            ON CONFLICT (dataset_id, record_id) DO UPDATE SET
                                                content = EXCLUDED.content,
                                                chunk_index = EXCLUDED.chunk_index,
                                                chunk_text = EXCLUDED.chunk_text,
                                                embedding = EXCLUDED.embedding,
                                                vector_metadata = EXCLUDED.vector_metadata,
                                                created_at = CURRENT_TIMESTAMP
                                            """,
                                            values_list
                                        )
                                    
                                    logger.info(f"Batch {batch_num} completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                                    return {"success": True, "count": len(batch_inputs)}
                                except json.JSONDecodeError as e:
                                    error_msg = f"Failed to decode API response for batch {batch_num}: {str(e)}"
                                    logger.error(error_msg)
                                    return {"success": False, "error": error_msg}
                            else:
                                error_msg = f"Batch {batch_num} failed: {response.status} - {response_text}"
                                logger.error(error_msg)
                                return {"success": False, "error": f"API error: {response.status}", "message": response_text}
                    except aiohttp.ClientError as e:
                        error_msg = f"HTTP client error in batch {batch_num}: {str(e)}"
                        logger.error(error_msg)
                        return {"success": False, "error": error_msg}
            except Exception as e:
                error_msg = f"Error processing batch {batch_num}: {str(e)}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
        
        # Process batches with concurrency control
        tasks = []
        semaphore = asyncio.Semaphore(10)  # Limit concurrent tasks
        
        async def bounded_process_batch(batch_num):
            async with semaphore:
                return await process_batch(batch_num)
        
        # Create tasks for all batches
        for i in range(num_batches):
            tasks.append(bounded_process_batch(i))
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        # Count successful batches
        successful_batches = sum(1 for r in results if r["success"])
        total_vectors = sum(r.get("count", 0) for r in results if r["success"])
        
        return {
            "success": successful_batches > 0,
            "message": f"Vector embedding processing completed: {successful_batches}/{num_batches} batches successful",
            "total_vectors": total_vectors
        }
    
    async def generate_embeddings(self, texts, model_id=None, dataset_id=None):
        """
        Generate embeddings for a list of texts using the specified model.
        
        Args:
            texts: List of texts to generate embeddings for
            model_id: ID of the embedding model to use
            dataset_id: Optional dataset ID for tracking
            
        Returns:
            Dictionary with embeddings and metadata
        """
        try:
            # Use default model if none specified or if specified model is not supported
            if not model_id or model_id not in EMBEDDING_MODELS:
                model_id = settings.VECTOR_EMBEDDING_API_MODEL
                logger.info(f"Using default embedding model: {model_id}")
            
            model_config = EMBEDDING_MODELS.get(model_id)
            if not model_config:
                logger.warning(f"Model {model_id} not found in EMBEDDING_MODELS, using default configuration")
                # Use a fallback configuration
                model_config = {
                    "id": model_id,
                    "name": model_id,
                    "provider": "huggingface",
                    "dimensions": 384,  # Default dimension
                    "endpoint": f"sentence-transformers/{model_id}"
                }
            
            logger.info(f"Generating embeddings using model: {model_id}")
            
            # Prepare the API request
            headers = {
                "Authorization": f"Basic {self.api_key}" if self.api_key else None,
                "Content-Type": "application/json"
            }
            
            # Remove None values from headers
            headers = {k: v for k, v in headers.items() if v is not None}
            
            # Ensure texts is a list
            if not isinstance(texts, list):
                texts = [texts]
            
            # Prepare the request payload
            payload = {
                "inputs": texts,
                "model": model_id
            }
            
            # Make the API request using aiohttp
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        self.endpoint,
                        headers=headers,
                        json=payload
                    ) as response:
                        response_text = await response.text()
                        
                        # Check if the request was successful
                        if response.status == 200:
                            try:
                                result = json.loads(response_text) if isinstance(response_text, str) else response_text
                                return {
                                    "success": True,
                                    "embeddings": result.get("embeddings", []),
                                    "model": model_id,
                                    "dimensions": model_config.get("dimensions", len(result.get("embeddings", [[]])[0]) if result.get("embeddings") else 0),
                                    "count": len(texts)
                                }
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to decode API response: {e}")
                                return {
                                    "success": False,
                                    "error": "Failed to decode API response",
                                    "message": response_text
                                }
                        else:
                            logger.error(f"API error: {response.status} - {response_text}")
                            return {
                                "success": False,
                                "error": f"API error: {response.status}",
                                "message": response_text
                            }
                except aiohttp.ClientError as e:
                    logger.error(f"HTTP client error: {str(e)}")
                    return {
                        "success": False,
                        "error": f"HTTP client error: {str(e)}",
                        "message": str(e)
                    }
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_dataset(self, dataset_id, file_path, chunk_size=1000, overlap=200, model_id=None, config=None):
        """
        Process a dataset to generate embeddings and store them in the vector database.
        
        Args:
            dataset_id: ID of the dataset to process
            file_path: Path to the dataset file
            chunk_size: Size of text chunks for processing
            overlap: Overlap between chunks
            model_id: ID of the embedding model to use
            config: Additional configuration options
            
        Returns:
            Processing results
        """
        try:
            # Use the specified model or default from settings
            if not model_id or model_id not in EMBEDDING_MODELS:
                model_id = settings.VECTOR_EMBEDDING_API_MODEL
                logger.info(f"Using default embedding model: {model_id}")
            else:
                logger.info(f"Using specified embedding model: {model_id}")
            
            # Get model configuration
            model_config = EMBEDDING_MODELS.get(model_id, {
                "id": model_id,
                "name": model_id,
                "dimensions": 384,  # Default dimension
                "provider": "huggingface"
            })
            
            logger.info(f"Processing dataset {dataset_id} from file {file_path} using model {model_id}")
            
            # Load the dataset using pandas
            file_ext = file_path.split('.')[-1].lower()
            
            if file_ext == 'csv':
                df = pd.read_csv(file_path)
            elif file_ext == 'json':
                df = pd.read_json(file_path)
            elif file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file format: {file_ext}"
                }
            
            # Get record count
            record_count = len(df)
            logger.info(f"Loaded {record_count} records from {file_path}")
            
            if record_count == 0:
                return {
                    "success": False,
                    "error": "No records found in dataset"
                }
            
            # Get database connection pool for direct database operations
            from api.db.connection import get_db_pool
            pool = await get_db_pool()
            
            # Store model information in dataset metadata
            async with pool.acquire() as conn:
                # Get current metadata
                dataset_row = await conn.fetchrow(
                    "SELECT metadata FROM datasets WHERE id = $1",
                    dataset_id
                )
                
                if dataset_row and dataset_row['metadata']:
                    metadata = dataset_row['metadata']
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except json.JSONDecodeError:
                            metadata = {}
                else:
                    metadata = {}
                
                # Update metadata with embedding model information
                metadata.update({
                    "embedding_model": model_id,
                    "embedding_model_dimensions": model_config.get("dimensions", 384),
                    "embedding_timestamp": datetime.now().isoformat(),
                    "chunk_size": chunk_size,
                    "overlap": overlap
                })
                
                # Save updated metadata
                await conn.execute(
                    "UPDATE datasets SET metadata = $1 WHERE id = $2",
                    json.dumps(metadata),
                    dataset_id
                )
            
            # For very large datasets, we'll use direct API invocation with batching
            if record_count > 10000:
                logger.info(f"Large dataset detected ({record_count} records). Using direct API invocation with batching.")
                
                # Convert records to text inputs for the API
                inputs = []
                for i, record in enumerate(df.to_dict('records')):
                    # Convert record to JSON string
                    record_text = json.dumps(record)
                    inputs.append(record_text)
                
                # Create a custom config object for the API call
                api_config = type('Config', (), {})()
                api_config.VECTOR_EMBEDDING_API_ENDPOINT = self.endpoint
                api_config.VECTOR_EMBEDDING_API_KEY = self.api_key
                api_config.VECTOR_BATCH_SIZE = getattr(settings, "VECTOR_BATCH_SIZE", 1000)
                api_config.VECTOR_EMBEDDING_API_MODEL = model_id
                
                # Call the API with batching
                api_result = await self.invoke_api(inputs, api_config, dataset_id)
                
                # Update dataset with vectorization status
                async with pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE datasets SET vectorized = TRUE, vectorized_at = NOW() WHERE id = $1",
                        dataset_id
                    )
                
                return {
                    "success": api_result["success"],
                    "total_vectors": api_result.get("total_vectors", 0),
                    "total_records": record_count,
                    "model": model_id,
                    "dimensions": model_config.get("dimensions", 384),
                    "message": api_result.get("message", "")
                }
            
            # For smaller datasets, use the standard approach with more control
            logger.info(f"Processing {record_count} records with chunk size {chunk_size}")
            
            # Process in batches
            batch_size = min(1000, record_count)
            total_vectors = 0
            total_batches = math.ceil(record_count / batch_size)
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min((batch_idx + 1) * batch_size, record_count)
                
                logger.info(f"Processing batch {batch_idx+1}/{total_batches} (records {start_idx}-{end_idx})")
                
                # Get batch of records
                batch_df = df.iloc[start_idx:end_idx]
                batch_records = batch_df.to_dict('records')
                
                # Convert records to text
                texts = [json.dumps(record) for record in batch_records]
                
                # Generate embeddings
                embedding_result = await self.generate_embeddings(texts)
                
                if not embedding_result["success"]:
                    logger.error(f"Failed to generate embeddings for batch {batch_idx}: {embedding_result.get('error', 'Unknown error')}")
                    continue
                
                # Get embeddings
                embeddings = embedding_result.get("embeddings", [])
                
                if not embeddings:
                    logger.warning(f"No embeddings returned for batch {batch_idx}")
                    continue
                    
                # Insert vectors directly into database using asyncpg
                async with pool.acquire() as conn:
                    # Prepare values for bulk insert
                    values_list = []
                    for i, (record, embedding) in enumerate(zip(batch_records, embeddings)):
                        record_id = f"record_{start_idx + i}"
                        record_text = json.dumps(record)
                        
                        values_list.append((
                            dataset_id,
                            record_id,
                            record_text,  # content
                            start_idx + i,  # chunk_index
                            record_text,  # chunk_text
                            embedding,  # embedding
                            json.dumps({  # metadata
                                "record_index": start_idx + i,
                                "batch": batch_idx
                            })
                        ))
                    
                    # Execute bulk insert
                    await conn.executemany(
                        """
                        INSERT INTO vector_embeddings 
                            (dataset_id, record_id, content, chunk_index, chunk_text, embedding, vector_metadata)
                        VALUES 
                            ($1, $2, $3, $4, $5, $6::vector, $7::jsonb)
                        ON CONFLICT (dataset_id, record_id) DO UPDATE SET
                            content = EXCLUDED.content,
                            chunk_index = EXCLUDED.chunk_index,
                            chunk_text = EXCLUDED.chunk_text,
                            embedding = EXCLUDED.embedding,
                            vector_metadata = EXCLUDED.vector_metadata,
                            created_at = CURRENT_TIMESTAMP
                        """,
                        values_list
                    )
                
                # Update total vectors count
                total_vectors += len(values_list)
                logger.info(f"Added {len(values_list)} vectors for batch {batch_idx+1}/{total_batches}")
            
            return {
                "success": True,
                "total_vectors": total_vectors,
                "total_records": record_count,
                "total_batches": total_batches,
                "message": f"Successfully processed {total_vectors} vectors from {record_count} records"
            }
            
        except Exception as e:
            logger.error(f"Error processing dataset: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Create singleton instance
vector_embedding_api = VectorEmbeddingAPI()
