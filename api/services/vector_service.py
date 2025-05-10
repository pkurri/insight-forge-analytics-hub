import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import numpy as np
import os
from functools import wraps

# Import database connection
from api.db.connection import execute_query, execute_command, execute_transaction, get_db_connection

# Import configuration
from config.settings import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

class VectorService:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.vector_dim = 1536  # Standard dimension for vector embeddings (text-embedding-3-small)
            self._initialized = True
    
    async def initialize(self):
        """Initialize the vector database and create tables/indexes if needed"""
        try:
            logger.info("Initializing vector database...")
            
            # Create vector_embeddings table if it doesn't exist
            create_table_query = """
            CREATE TABLE IF NOT EXISTS vector_embeddings (
                id SERIAL PRIMARY KEY,
                dataset_id INTEGER NOT NULL,
                record_id VARCHAR(100) NOT NULL,
                content TEXT,
                chunk_index INTEGER,
                chunk_text TEXT,
                embedding vector(1536),
                vector_metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(dataset_id, record_id)
            );
            """
            
            # Create indexes if they don't exist
            create_indexes_query = """
            CREATE INDEX IF NOT EXISTS idx_vector_embeddings_dataset_id ON vector_embeddings(dataset_id);
            CREATE INDEX IF NOT EXISTS vector_embeddings_embedding_idx ON vector_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
            """
            
            # Execute queries
            await execute_command(create_table_query)
            await execute_command(create_indexes_query)
            
            logger.info("Vector database initialization complete")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}", exc_info=True)
            return False

    async def add_vectors(self, dataset_id: int, vectors: List[Dict[str, Any]]):
        """
        Add vectors to the database for a specific dataset
        
        Args:
            dataset_id: ID of the dataset
            vectors: List of vector data dictionaries with record_id, embedding, content, and optional metadata
            
        Returns:
            Dictionary with success status and count or error message
        """
        try:
            # Prepare values for bulk insert
            values_list = []
            for v in vectors:
                values_list.append((
                    dataset_id,
                    v['record_id'],
                    v.get('content', ''),  # Store original content for RAG
                    v.get('chunk_index'),  # Store chunk index
                    v.get('chunk_text', ''),  # Store chunk text
                    v['embedding'],  # Vector embedding
                    json.dumps(v.get('metadata', {}))  # JSON metadata
                ))
            
            # Bulk insert query
            insert_query = """
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
            """
            
            # Execute transaction with all inserts
            async with get_db_connection() as conn:
                # Use execute_many for bulk operations
                await conn.executemany(insert_query, values_list)
            
            return {
                "success": True,
                "count": len(values_list),
                "message": f"Successfully added {len(values_list)} vectors for dataset {dataset_id}"
            }
        except Exception as e:
            logger.error(f"Error adding vectors: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def search_vectors(
        self,
        query_vector: List[float],
        dataset_id: Optional[int] = None,
        limit: int = 10,
        threshold: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None,
        include_chunks: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors using cosine similarity
        
        Args:
            query_vector: The query vector to compare against
            dataset_id: Optional dataset ID to filter results
            limit: Maximum number of results to return
            threshold: Minimum similarity score (0-1)
            metadata_filter: Optional metadata filters to apply
            include_chunks: Whether to include chunk text in results
            
        Returns:
            List of similar vectors with their similarity scores and content
        """
        try:
            # Build the query
            query = """
            SELECT 
                id, record_id, dataset_id,
                1 - (embedding <=> $1::vector) as similarity
            """
            
            # Add content and chunk_text if requested
            if include_chunks:
                query += ", content, chunk_text"
                
            # Add metadata
            query += ", vector_metadata"
            
            # From clause
            query += " FROM vector_embeddings"
            
            # Where clause
            params = [query_vector]
            param_idx = 2  # Starting with $2 since $1 is already used
            
            where_clauses = []
            
            # Add dataset filter if specified
            if dataset_id is not None:
                where_clauses.append(f"dataset_id = ${param_idx}")
                params.append(dataset_id)
                param_idx += 1
            
            # Add metadata filters if specified
            if metadata_filter:
                for key, value in metadata_filter.items():
                    where_clauses.append(f"vector_metadata->>'${key}' = ${param_idx}")
                    params.append(str(value))
                    param_idx += 1
            
            # Add where clause if any filters
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Add similarity threshold
            if where_clauses:
                query += f" AND (1 - (embedding <=> $1::vector)) >= ${param_idx}"
            else:
                query += f" WHERE (1 - (embedding <=> $1::vector)) >= ${param_idx}"
            params.append(threshold)
            param_idx += 1
            
            # Order by similarity and limit
            query += """
            ORDER BY similarity DESC
            LIMIT $""" + str(param_idx) + """
            """
            params.append(limit)
            
            # Execute query
            results = await execute_query(query, *params)
            
            # Format results
            formatted_results = []
            for row in results:
                result_item = {
                    "id": row["id"],
                    "record_id": row["record_id"],
                    "similarity": row["similarity"],
                    "metadata": row["vector_metadata"]
                }
                
                # Include content if requested
                if include_chunks:
                    result_item["content"] = row["content"]
                    result_item["chunk_text"] = row["chunk_text"]
                
                formatted_results.append(result_item)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            return []
    async def get_ordered_chunks(
        self,
        dataset_id: int,
        record_id: str,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get ordered chunks for a specific record
        
        Args:
            dataset_id: ID of the dataset
            record_id: ID of the record
            start_index: Optional start chunk index
            end_index: Optional end chunk index
            
        Returns:
            List of ordered chunks with their content
        """
        try:
            # Build the query
            query = """
            SELECT 
                id, record_id, dataset_id, chunk_index, chunk_text, content, vector_metadata
            FROM vector_embeddings
            WHERE dataset_id = $1 AND record_id = $2
            """
            
            params = [dataset_id, record_id]
            param_idx = 3
            
            # Add index filters if specified
            if start_index is not None:
                query += f" AND chunk_index >= ${param_idx}"
                params.append(start_index)
                param_idx += 1
                
            if end_index is not None:
                query += f" AND chunk_index <= ${param_idx}"
                params.append(end_index)
                param_idx += 1
                
            # Order by chunk index
            query += " ORDER BY chunk_index"
            
            # Execute query
            results = await execute_query(query, *params)
            
            # Format results
            return [{
                "chunk_index": row["chunk_index"],
                "chunk_text": row["chunk_text"],
                "content": row["content"],
                "metadata": row["vector_metadata"]
            } for row in results]
            
        except Exception as e:
            logger.error(f"Error getting ordered chunks: {str(e)}")
            return []

    async def delete_vectors(self, dataset_id: int) -> Dict[str, Any]:
        """Delete all vectors for a specific dataset"""
        try:
            # Delete query
            query = "DELETE FROM vector_embeddings WHERE dataset_id = $1"
            
            # Execute query
            result = await execute_command(query, dataset_id)
            
            return {
                "success": True,
                "message": f"Deleted vectors for dataset {dataset_id}"
            }
        except Exception as e:
            logger.error(f"Error deleting vectors: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def get_dataset_info(self, dataset_id: int) -> Dict[str, Any]:
        """Get information about vectors stored for a specific dataset"""
        try:
            # Count query
            count_query = "SELECT COUNT(*) as count FROM vector_embeddings WHERE dataset_id = $1"
            
            # Record count query (unique record_ids)
            record_count_query = """
            SELECT COUNT(DISTINCT record_id) as record_count 
            FROM vector_embeddings 
            WHERE dataset_id = $1
            """
            
            # Execute queries
            count_result = await execute_query(count_query, dataset_id)
            record_count_result = await execute_query(record_count_query, dataset_id)
            
            count = count_result[0]["count"] if count_result else 0
            record_count = record_count_result[0]["record_count"] if record_count_result else 0
            
            return {
                "dataset_id": dataset_id,
                "vector_count": count,
                "record_count": record_count,
                "vector_dimension": self.vector_dim
            }
        except Exception as e:
            logger.error(f"Error getting dataset info: {str(e)}")
            return {}

# Create singleton instance
vector_service = VectorService()
