import logging
import json
import pandas as pd
import numpy as np
import asyncpg
from typing import Dict, Any, List, Optional
import uuid

from api.config import get_db_config
from api.services.ai_service import generate_embedding

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
    
    async def load_to_vector_db(self, dataset_id: int, chunk_size: int = 1000, overlap: int = 200) -> Dict[str, Any]:
        """
        Load a dataset into the vector database by creating embeddings
        
        Args:
            dataset_id: ID of the dataset to vectorize
            chunk_size: Size of text chunks for vectorization
            overlap: Overlap between chunks
            
        Returns:
            Dictionary with vectorization results
        """
        await self.initialize()
        
        try:
            # Get dataset information
            async with self.pool.acquire() as conn:
                dataset = await conn.fetchrow(
                    """
                    SELECT id, name, file_path, transformed_file_path
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
                
                # Get dataset metadata
                metadata_row = await conn.fetchrow(
                    """
                    SELECT metadata
                    FROM dataset_metadata
                    WHERE dataset_id = $1
                    """,
                    dataset_id
                )
                
                metadata = json.loads(metadata_row["metadata"]) if metadata_row else {}
            
            # Use transformed file if available, otherwise use original
            file_path = dataset["transformed_file_path"] or dataset["file_path"]
            
            # Load the dataset
            file_format = metadata.get("file_format", "csv").lower()
            
            if file_format == "csv":
                df = pd.read_csv(file_path)
            elif file_format == "json":
                df = pd.read_json(file_path)
            elif file_format == "excel" or file_format == "xlsx":
                df = pd.read_excel(file_path)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file format: {file_format}"
                }
            
            # Create text chunks from the dataset
            chunks = []
            
            # Convert each row to a JSON string
            for i, row in df.iterrows():
                row_json = row.to_json()
                chunks.append({
                    "id": f"row_{i}",
                    "text": row_json,
                    "metadata": {
                        "row_index": i,
                        "dataset_id": dataset_id
                    }
                })
            
            # Create embeddings for each chunk and store in vector database
            embeddings_created = 0
            errors = 0
            
            for chunk in chunks:
                try:
                    # Generate embedding for the chunk
                    embedding = await generate_embedding(chunk["text"])
                    
                    if not embedding:
                        logger.warning(f"Failed to generate embedding for chunk {chunk['id']}")
                        errors += 1
                        continue
                    
                    # Store embedding in database
                    async with self.pool.acquire() as conn:
                        await conn.execute(
                            """
                            INSERT INTO vector_embeddings (
                                id, dataset_id, chunk_text, vector_embedding, metadata, created_at
                            )
                            VALUES ($1, $2, $3, $4, $5, NOW())
                            """,
                            str(uuid.uuid4()),
                            dataset_id,
                            chunk["text"],
                            embedding,  # This assumes the database supports storing arrays directly
                            json.dumps(chunk["metadata"])
                        )
                    
                    embeddings_created += 1
                    
                except Exception as e:
                    logger.error(f"Error creating embedding for chunk {chunk['id']}: {str(e)}")
                    errors += 1
            
            # Update dataset status
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE datasets
                    SET vectorized = TRUE, vectorized_at = NOW()
                    WHERE id = $1
                    """,
                    dataset_id
                )
            
            return {
                "success": True,
                "dataset_id": dataset_id,
                "embeddings_created": embeddings_created,
                "errors": errors,
                "total_chunks": len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Error loading dataset to vector database: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to load dataset to vector database: {str(e)}"
            }
    
    async def search_vectors(self, query_vector: List[float], dataset_id: Optional[int] = None, 
                            limit: int = 5, threshold: float = 0.7, include_chunks: bool = False) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in the database
        
        Args:
            query_vector: The query vector to search for
            dataset_id: Optional dataset ID to filter results
            limit: Maximum number of results to return
            threshold: Similarity threshold (0-1)
            include_chunks: Whether to include the chunk text in results
            
        Returns:
            List of similar vectors with metadata
        """
        await self.initialize()
        
        try:
            async with self.pool.acquire() as conn:
                # Prepare query
                query = """
                SELECT 
                    id, 
                    dataset_id, 
                    metadata,
                    1 - (vector_embedding <=> $1) as similarity
                """
                
                if include_chunks:
                    query += ", chunk_text"
                
                query += """
                FROM vector_embeddings
                WHERE 1 - (vector_embedding <=> $1) > $2
                """
                
                params = [query_vector, threshold]
                
                if dataset_id:
                    query += " AND dataset_id = $3"
                    params.append(dataset_id)
                
                query += " ORDER BY similarity DESC LIMIT $" + str(len(params) + 1)
                params.append(limit)
                
                # Execute query
                rows = await conn.fetch(query, *params)
                
                # Process results
                results = []
                for row in rows:
                    result = {
                        "id": row["id"],
                        "dataset_id": row["dataset_id"],
                        "similarity": row["similarity"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
                    }
                    
                    if include_chunks:
                        result["chunk_text"] = row["chunk_text"]
                    
                    results.append(result)
                
                return results
                
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
            async with self.pool.acquire() as conn:
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
                
                # Extract number of deleted rows
                deleted_count = int(result.split(" ")[1])
                
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
