"""
Vector Embedding API Service

This module provides an API-centric approach for generating vector embeddings
and interacting with the vector database for semantic search capabilities.
"""

from datetime import date, datetime
import json
import concurrent
import asyncpg
import requests
import pandas as pd
import logging
import math
from concurrent.futures import ThreadPoolExecutor
import threading

from api.config.settings import get_settings
from api.db.connection import execute_query, execute_command, get_db_connection

logger = logging.getLogger(__name__)
settings = get_settings()

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
                # Make API request
                response = requests.post(api_endpoint, headers=headers, json=data)
                
                if response.status_code == 200:
                    batch_vectors = response.json()
                    
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
                else:
                    logger.error(f"Batch {batch_num} failed: {response.status_code} - {response.text}")
                    return {"success": False, "error": f"API error: {response.status_code} - {response.text}"}
            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {str(e)}")
                return {"success": False, "error": str(e)}
        
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
    
    async def generate_embeddings(self, texts, dataset_id=None):
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to generate embeddings for
            dataset_id: Optional dataset ID for tracking
            
        Returns:
            List of embeddings
        """
        try:
            # Prepare the API request
            headers = {
                "Authorization": f"Basic {self.api_key}" if self.api_key else None,
                "Content-Type": "application/json"
            }
            
            # Remove None values from headers
            headers = {k: v for k, v in headers.items() if v is not None}
            
            # Prepare the request payload
            payload = {
                "inputs": texts,
                "model": settings.VECTOR_EMBEDDING_API_MODEL
            }
            
            # Make the API request
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "embeddings": result.get("embeddings", []),
                    "model": settings.VECTOR_EMBEDDING_API_MODEL,
                    "count": len(texts)
                }
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "message": response.text
                }
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_dataset(self, dataset_id, file_path, chunk_size=1000, overlap=200):
        """
        Process a dataset to generate embeddings and store them in the vector database.
        
        Args:
            dataset_id: ID of the dataset to process
            file_path: Path to the dataset file
            chunk_size: Size of text chunks for processing
            overlap: Overlap between chunks
            
        Returns:
            Processing results
        """
        try:
            logger.info(f"Processing dataset {dataset_id} from file {file_path}")
            
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
                
            # Convert dataframe to text for processing
            # For large datasets, we'll process directly instead of pre-chunking
            # to avoid memory issues
            
            # Prepare config for API call
            config = settings
            
            # For very large datasets, we'll use direct API invocation with batching
            if record_count > 10000:
                logger.info(f"Large dataset detected ({record_count} records). Using direct API invocation with batching.")
                
                # Convert records to text inputs for the API
                inputs = []
                for i, record in enumerate(df.to_dict('records')):
                    # Convert record to JSON string
                    record_text = json.dumps(record)
                    inputs.append(record_text)
                
                # Call the API with batching
                api_result = await self.invoke_api(inputs, config, dataset_id)
                
                return {
                    "success": api_result["success"],
                    "total_vectors": api_result.get("total_vectors", 0),
                    "total_records": record_count,
                    "message": api_result.get("message", "")
                }
            
            # For smaller datasets, use the standard approach with more control
            logger.info(f"Processing {record_count} records with chunk size {chunk_size}")
            
            # Get database connection pool for direct database operations
            from api.db.connection import get_db_pool
            pool = await get_db_pool()
            
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
