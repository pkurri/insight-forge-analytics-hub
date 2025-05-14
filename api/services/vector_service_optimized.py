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
from api.config.settings import get_settings

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
            self.cache = {}
            self.cache_ttl = 3600  # Cache TTL in seconds (1 hour)
            self.cache_max_size = 1000  # Maximum number of cached queries
            self.use_approximate_search = True  # Use approximate search for large datasets
            self.approximate_search_threshold = 100000  # Threshold for using approximate search
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
            
            -- Create index on dataset_id for faster filtering
            CREATE INDEX IF NOT EXISTS idx_vector_embeddings_dataset_id ON vector_embeddings(dataset_id);
            
            -- Create index on record_id for faster lookups
            CREATE INDEX IF NOT EXISTS idx_vector_embeddings_record_id ON vector_embeddings(record_id);
            
            -- Create GIN index on vector_metadata for faster JSON queries
            CREATE INDEX IF NOT EXISTS idx_vector_embeddings_metadata ON vector_embeddings USING GIN(vector_metadata);
            
            -- Create composite index on dataset_id and embedding for faster vector search within datasets
            CREATE INDEX IF NOT EXISTS idx_vector_embeddings_dataset_embedding ON vector_embeddings(dataset_id, embedding);
            """
            
            # Execute the create table query
            await execute_command(create_table_query)
            
            # Create HNSW index for approximate nearest neighbor search
            try:
                hnsw_index_query = """
                CREATE INDEX IF NOT EXISTS vector_embeddings_hnsw_idx ON vector_embeddings 
                USING hnsw (embedding vector_cosine_ops) 
                WITH (m=16, ef_construction=64);
                """
                await execute_command(hnsw_index_query)
                logger.info("HNSW index created successfully")
            except Exception as e:
                # HNSW index might not be supported in all PostgreSQL versions with pgvector
                logger.warning(f"Failed to create HNSW index, falling back to exact search: {str(e)}")
            
            # Create IVF index for faster vector search
            create_indexes_query = """
            CREATE INDEX IF NOT EXISTS vector_embeddings_embedding_idx ON vector_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
            """
            await execute_command(create_indexes_query)
            
            logger.info("Vector database initialization complete")
        except Exception as e:
            logger.error(f"Error initializing vector database: {str(e)}")
    
    async def add_vectors(
        self,
        vectors: List[Dict[str, Any]],
        dataset_id: int,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Add vectors to the database
        
        Args:
            vectors: List of vector dictionaries with record_id, content, embedding, and metadata
            dataset_id: ID of the dataset
            batch_size: Number of vectors to insert in each batch
            
        Returns:
            Dictionary with success status and count of added vectors
        """
        try:
            # Prepare values for bulk insert
            values_list = []
            
            for vector in vectors:
                record_id = vector.get("record_id", "")
                content = vector.get("content", "")
                chunk_index = vector.get("chunk_index", 0)
                chunk_text = vector.get("chunk_text", content)
                embedding = vector.get("embedding", [])
                metadata = vector.get("metadata", {})
                
                # Validate embedding dimension
                if len(embedding) != self.vector_dim:
                    logger.warning(f"Skipping vector with incorrect dimension: {len(embedding)} != {self.vector_dim}")
                    continue
                
                # Add to values list
                values_list.append((
                    dataset_id,
                    record_id,
                    content,
                    chunk_index,
                    chunk_text,
                    embedding,
                    json.dumps(metadata)
                ))
            
            # Insert query with ON CONFLICT DO UPDATE
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

    def _get_cache_key(self, query_vector, dataset_id, limit, threshold, metadata_filter):
        """Generate a cache key for vector search"""
        # Convert query vector to a hash for cache key
        vector_hash = hash(str(query_vector))
        metadata_str = json.dumps(metadata_filter, sort_keys=True) if metadata_filter else ""
        return f"search:{vector_hash}:{dataset_id}:{limit}:{threshold}:{metadata_str}"
    
    def _cache_result(self, key, result):
        """Cache a search result"""
        # Implement LRU cache - remove oldest entry if cache is full
        if len(self.cache) >= self.cache_max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[key] = {
            "result": result,
            "timestamp": datetime.now()
        }
    
    def _get_cached_result(self, key):
        """Get a cached result if it exists and is not expired"""
        if key in self.cache:
            cache_entry = self.cache[key]
            cache_age = (datetime.now() - cache_entry["timestamp"]).total_seconds()
            
            if cache_age < self.cache_ttl:
                return cache_entry["result"]
            else:
                # Remove expired cache entry
                del self.cache[key]
        
        return None
    
    async def search_vectors(
        self,
        query_vector: List[float],
        dataset_id: Optional[int] = None,
        limit: int = 10,
        threshold: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None,
        include_chunks: bool = True,
        use_cache: bool = True
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
            use_cache: Whether to use caching for this query
            
        Returns:
            List of similar vectors with their similarity scores and content
        """
        try:
            # Check cache first if enabled
            if use_cache:
                cache_key = self._get_cache_key(query_vector, dataset_id, limit, threshold, metadata_filter)
                cached_result = self._get_cached_result(cache_key)
                if cached_result:
                    logger.info("Using cached vector search result")
                    return cached_result
            
            # Determine if we should use approximate search
            # Get count of vectors in the dataset to decide on search method
            count_query = "SELECT COUNT(*) FROM vector_embeddings"
            count_params = []
            
            if dataset_id is not None:
                count_query += " WHERE dataset_id = $1"
                count_params.append(dataset_id)
            
            count_result = await execute_query(count_query, *count_params)
            vector_count = count_result[0]["count"]
            
            use_approximate = self.use_approximate_search and vector_count > self.approximate_search_threshold
            
            # Build the query
            if use_approximate:
                # Use HNSW index for approximate search
                query = """
                SELECT 
                    id, record_id, dataset_id,
                    1 - (embedding <=> $1::vector) as similarity
                """
            else:
                # Use exact search
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
            
            # Add metadata pre-filtering - this is more efficient than post-filtering
            if metadata_filter:
                for key, value in metadata_filter.items():
                    # Use proper JSONB path operators for better performance
                    where_clauses.append(f"vector_metadata @> '{{\"" + key + "\": \"" + str(value) + "\"}}'::jsonb")
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
            
            # Execute query with timing for performance monitoring
            start_time = datetime.now()
            results = await execute_query(query, *params)
            query_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Vector search completed in {query_time:.3f}s with {len(results)} results")
            
            # Format results
            formatted_results = []
            for row in results:
                result_item = {
                    "id": row["id"],
                    "record_id": row["record_id"],
                    "similarity": row["similarity"],
                    "metadata": row["vector_metadata"],
                    "dataset_id": row["dataset_id"]
                }
                
                # Include content if requested
                if include_chunks:
                    result_item["content"] = row["content"]
                    result_item["chunk_text"] = row["chunk_text"]
                
                formatted_results.append(result_item)
            
            # Cache the result if caching is enabled
            if use_cache:
                cache_key = self._get_cache_key(query_vector, dataset_id, limit, threshold, metadata_filter)
                self._cache_result(cache_key, formatted_results)
            
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
                id, chunk_index, chunk_text, content, vector_metadata
            FROM 
                vector_embeddings
            WHERE 
                dataset_id = $1 AND record_id = $2
            """
            
            params = [dataset_id, record_id]
            param_idx = 3  # Starting with $3
            
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
            query += " ORDER BY chunk_index ASC"
            
            # Execute query
            results = await execute_query(query, *params)
            
            # Format results
            formatted_results = []
            for row in results:
                result_item = {
                    "id": row["id"],
                    "chunk_index": row["chunk_index"],
                    "chunk_text": row["chunk_text"],
                    "content": row["content"],
                    "metadata": row["vector_metadata"]
                }
                
                formatted_results.append(result_item)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error getting ordered chunks: {str(e)}")
            return []
    
    async def get_dataset_info(self, dataset_id: int) -> Dict[str, Any]:
        """
        Get information about a dataset's vector embeddings
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            Dictionary with dataset information
        """
        try:
            # Get count of vectors
            count_query = """
            SELECT COUNT(*) as count
            FROM vector_embeddings
            WHERE dataset_id = $1
            """
            
            count_result = await execute_query(count_query, dataset_id)
            count = count_result[0]["count"]
            
            # Get count of unique records
            record_count_query = """
            SELECT COUNT(DISTINCT record_id) as record_count
            FROM vector_embeddings
            WHERE dataset_id = $1
            """
            
            record_count_result = await execute_query(record_count_query, dataset_id)
            record_count = record_count_result[0]["record_count"]
            
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
