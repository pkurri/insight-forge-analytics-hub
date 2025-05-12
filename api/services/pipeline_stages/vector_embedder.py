import logging
import json
import pandas as pd
import numpy as np
import asyncpg
from typing import Dict, Any, List, Optional
import uuid
import os
from datetime import datetime

from api.config import get_db_config
from api.services.ai_service import generate_embedding
from api.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class VectorEmbedderService:
    """Service for creating vector embeddings for datasets"""
    
    def __init__(self):
        self.pool = None
        
    async def initialize(self):
        """Initialize the database connection pool"""
        if self.pool is None:
            try:
                db_config = get_db_config()
                self.pool = await asyncpg.create_pool(**db_config)
                logger.info("Vector embedder service initialized with asyncpg connection pool")
            except Exception as e:
                logger.error(f"Failed to initialize vector embedder service: {str(e)}")
                raise
    
    async def load_to_vector_db(self, dataset_id: int, chunk_size: int = 1000, overlap: int = 200, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Load a dataset into the vector database by creating embeddings using the API-centric approach
        
        Args:
            dataset_id: ID of the dataset to vectorize
            chunk_size: Size of text chunks for vectorization
            overlap: Overlap between chunks
            config: Additional configuration options
            
        Returns:
            Dictionary with vectorization results
        """
        await self.initialize()
        
        try:
            # Get dataset information directly from database using asyncpg
            async with self.pool.acquire() as conn:
                dataset = await conn.fetchrow(
                    """
                    SELECT id, name, file_path, transformed_file_path, metadata
                    FROM datasets
                    WHERE id = $1
                    """,
                    dataset_id
                )
                
                if not dataset:
                    return {
                        "success": False,
                        "error": f"Dataset with ID {dataset_id} not found"
                    }
            
            # Use transformed file if available, otherwise use original
            file_path = dataset["transformed_file_path"] or dataset["file_path"]
            
            if not file_path or not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File not found at path: {file_path}"
                }
                
            # Use the vector embedding API for efficient processing
            from api.services.vector_embedding_api import vector_embedding_api
            
            # Process the dataset with the vector embedding API
            config = config or {}
            result = await vector_embedding_api.process_dataset(
                dataset_id=dataset_id,
                file_path=file_path,
                chunk_size=chunk_size,
                overlap=overlap
            )
            
            if result["success"]:
                # Update dataset metadata directly in database
                async with self.pool.acquire() as conn:
                    # Update dataset status
                    await conn.execute(
                        """
                        UPDATE datasets
                        SET vectorized = TRUE, vectorized_at = NOW()
                        WHERE id = $1
                        """,
                        dataset_id
                    )
                    
                    # Update dataset metadata
                    metadata = dataset["metadata"] if dataset["metadata"] else {}
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except json.JSONDecodeError:
                            metadata = {}
                    
                    # Add vector metadata
                    vector_metadata = {
                        "vectorized": True,
                        "vectorized_at": datetime.now().isoformat(),
                        "total_vectors": result["total_vectors"],
                        "vector_model": settings.VECTOR_EMBEDDING_API_MODEL
                    }
                    
                    # Update metadata
                    metadata.update(vector_metadata)
                    
                    # Save updated metadata
                    await conn.execute(
                        """
                        UPDATE datasets
                        SET metadata = $1
                        WHERE id = $2
                        """,
                        json.dumps(metadata),
                        dataset_id
                    )
            
            # Return the result from the vector embedding API
            return result
            
        except Exception as e:
            logger.error(f"Error loading dataset to vector database: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to load dataset to vector database: {str(e)}"
            }
    
    async def search_vectors(self, query_vector: List[float], dataset_id: Optional[int] = None, 
                            limit: int = 5, threshold: float = 0.7, include_chunks: bool = False,
                            metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in the database using cosine similarity
        
        Args:
            query_vector: The query vector to search for
            dataset_id: Optional dataset ID to filter results
            limit: Maximum number of results to return
            threshold: Similarity threshold (0-1)
            include_chunks: Whether to include the chunk text in results
            metadata_filter: Optional metadata filters to apply
            
        Returns:
            List of similar vectors with metadata
        """
        await self.initialize()
        
        try:
            # Use the vector service for consistent search implementation
            from api.services.vector_service import vector_service
            await vector_service.initialize()
            
            # Use the vector service's search method
            results = await vector_service.search_vectors(
                query_vector=query_vector,
                dataset_id=dataset_id,
                limit=limit,
                threshold=threshold,
                metadata_filter=metadata_filter,
                include_chunks=include_chunks
            )
            
            return results
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            
            # Fallback to direct database query if vector service fails
            try:
                async with self.pool.acquire() as conn:
                    # Prepare query
                    query = """
                    SELECT 
                        id, 
                        dataset_id, 
                        record_id,
                        vector_metadata,
                        1 - (embedding <=> $1::vector) as similarity
                    """
                    
                    if include_chunks:
                        query += ", content, chunk_text"
                    
                    query += """
                    FROM vector_embeddings
                    WHERE 1 - (embedding <=> $1::vector) > $2
                    """
                    
                    params = [query_vector, threshold]
                    param_idx = 3
                    
                    if dataset_id is not None:
                        query += f" AND dataset_id = ${param_idx}"
                        params.append(dataset_id)
                        param_idx += 1
                    
                    # Add metadata filters if specified
                    if metadata_filter:
                        for key, value in metadata_filter.items():
                            query += f" AND vector_metadata->>'${key}' = ${param_idx}"
                            params.append(str(value))
                            param_idx += 1
                    
                    query += " ORDER BY similarity DESC LIMIT $" + str(param_idx)
                    params.append(limit)
                    
                    # Execute query
                    rows = await conn.fetch(query, *params)
                    
                    # Process results
                    results = []
                    for row in rows:
                        result = {
                            "id": row["id"],
                            "dataset_id": row["dataset_id"],
                            "record_id": row["record_id"],
                            "similarity": row["similarity"],
                            "metadata": json.loads(row["vector_metadata"]) if row["vector_metadata"] else {}
                        }
                        
                        if include_chunks:
                            result["content"] = row["content"]
                            result["chunk_text"] = row["chunk_text"]
                        
                        results.append(result)
                    
                    return results
            except Exception as inner_e:
                logger.error(f"Error in fallback vector search: {str(inner_e)}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            return []
    
    async def delete_dataset_vectors(self, dataset_id: int) -> Dict[str, Any]:
        """
        Delete all vector embeddings for a dataset
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            Dictionary with deletion results
        """
        await self.initialize()
        
        try:
            # Use the vector embedding API for consistent deletion
            from api.services.vector_embedding_api import vector_embedding_api
            
            # Attempt to use the vector embedding API first
            try:
                result = await vector_embedding_api.delete_dataset_vectors(dataset_id)
                if result["success"]:
                    return result
            except Exception as e:
                logger.warning(f"Vector embedding API deletion failed, falling back to direct DB: {str(e)}")
            
            # Fallback to direct database deletion
            async with self.pool.acquire() as conn:
                # Start a transaction
                async with conn.transaction():
                    # Delete embeddings
                    result = await conn.execute(
                        """
                        DELETE FROM vector_embeddings
                        WHERE dataset_id = $1
                        """,
                        dataset_id
                    )
                    
                    # Update dataset status
                    await conn.execute(
                        """
                        UPDATE datasets
                        SET vectorized = FALSE, vectorized_at = NULL
                        WHERE id = $1
                        """,
                        dataset_id
                    )
                    
                    # Update dataset metadata
                    dataset = await conn.fetchrow(
                        """SELECT metadata FROM datasets WHERE id = $1""", 
                        dataset_id
                    )
                    
                    if dataset and dataset["metadata"]:
                        metadata = dataset["metadata"]
                        if isinstance(metadata, str):
                            try:
                                metadata = json.loads(metadata)
                            except json.JSONDecodeError:
                                metadata = {}
                        
                        # Remove vector metadata
                        if "vectorized" in metadata:
                            metadata["vectorized"] = False
                        if "vectorized_at" in metadata:
                            metadata["vectorized_at"] = None
                        if "total_vectors" in metadata:
                            metadata["total_vectors"] = 0
                        
                        # Save updated metadata
                        await conn.execute(
                            """
                            UPDATE datasets
                            SET metadata = $1
                            WHERE id = $2
                            """,
                            json.dumps(metadata),
                            dataset_id
                        )
                
                # Extract number of deleted rows
                deleted_count = int(result.split(" ")[1]) if result else 0
                
                return {
                    "success": True,
                    "dataset_id": dataset_id,
                    "deleted_count": deleted_count
                }
                
        except Exception as e:
            logger.error(f"Error deleting dataset vectors: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to delete dataset vectors: {str(e)}"
            }
