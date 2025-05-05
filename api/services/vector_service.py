import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import numpy as np
from sqlalchemy import Column, Integer, String, DateTime, Index, text, select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
import os
from functools import wraps

# Import configuration
from config.settings import DATABASE_URL, VECTOR_DIMENSION

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create engine and session factory
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class VectorEmbedding(Base):
    __tablename__ = "vector_embeddings"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, index=True)
    record_id = Column(String(255), nullable=False, index=True)
    
    # Vector data - dimension should match your model's output
    embedding = Column(Vector(VECTOR_DIMENSION))
    
    # Metadata for filtering and reconstruction
    vector_metadata = Column(JSONB)  # Use JSONB for efficient querying of metadata
    document_type = Column(String(50), index=True, nullable=True)  # For type-based filtering
    
    # For incremental updates and versioning
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Create indexes for common query patterns
    __table_args__ = (
        Index('idx_dataset_doc_type', dataset_id, document_type),
    )

# Initialize database function
async def initialize():
    """Initialize the vector database and create tables/indexes if needed"""
    try:
        logger.info("Initializing vector database...")
        async with engine.begin() as conn:
            # Create tables if they don't exist
            await conn.run_sync(Base.metadata.create_all)
            
            # Create vector index if it doesn't exist
            # This is done with raw SQL as SQLAlchemy doesn't directly support pgvector indexes
            try:
                await conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS vector_embeddings_embedding_idx
                    ON vector_embeddings
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                """))
                logger.info("Vector index created or already exists")
            except Exception as e:
                logger.warning(f"Could not create vector index: {e}")
                
        logger.info("Vector database initialization complete")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize vector database: {e}", exc_info=True)
        return False

# Helper function to get a database session
async def get_db_session():
    """Get a database session"""
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()

# Add vectors to the database for a specific dataset
async def add_vectors(dataset_id: int, vectors: List[Dict[str, Any]]):
    """
    Add vectors to the database for a specific dataset
    
    Args:
        dataset_id: ID of the dataset
        vectors: List of vector data dictionaries with record_id, embedding, and optional metadata
        
    Returns:
        Dictionary with success status and count or error message
    """
    async with AsyncSessionLocal() as session:
        try:
            # Begin transaction
            async with session.begin():
                entries = []
                for v in vectors:
                    # Create VectorEmbedding instance with proper data validation
                    entry = VectorEmbedding(
                        dataset_id=dataset_id,
                        record_id=v["record_id"],
                        embedding=v["embedding"],
                        vector_metadata=v.get("metadata", {}),
                        document_type=v.get("document_type")
                    )
                    entries.append(entry)
                
                # Add all entries in bulk
                session.add_all(entries)
                
            # Commit happens automatically when exiting the context manager
            return {"success": True, "count": len(entries)}
        except Exception as e:
            logger.error(f"Error adding vectors: {e}", exc_info=True)
            return {"success": False, "error": str(e), "error_type": type(e).__name__}

# Calculate cosine similarity between two vectors
async def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    
    # Handle zero division
    if norm_a == 0 or norm_b == 0:
        return 0
        
    return dot_product / (norm_a * norm_b)

# Search for similar vectors in the database
async def search_similar_vectors(
    query_vector: Union[List[float], np.ndarray], 
    dataset_id: Optional[int] = None, 
    limit: int = 10, 
    threshold: float = 0.6,
    metadata_filter: Optional[Dict[str, Any]] = None,
    document_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for vectors similar to the query vector with optional filtering.
    
    Args:
        query_vector: The vector to compare against
        dataset_id: Optional filter by dataset ID
        limit: Maximum number of results to return
        threshold: Minimum similarity score (0-1) to include in results 
        metadata_filter: Optional filter on metadata fields
        document_type: Optional filter by document type
        
    Returns:
        Dictionary with success status and results or error message
    """
    try:
        # Convert list to numpy array if needed for consistent handling
        query_np = np.array(query_vector) if isinstance(query_vector, list) else query_vector
        
        # Validate vector dimensions
        if len(query_np) != VECTOR_DIMENSION:
            return {
                "success": False, 
                "error": f"Query vector must have {VECTOR_DIMENSION} dimensions, got {len(query_np)}"
            }
        
        async with AsyncSessionLocal() as session:
            # Start building the query
            stmt = select(VectorEmbedding)
            
            # Apply filters
            if dataset_id is not None:
                stmt = stmt.where(VectorEmbedding.dataset_id == dataset_id)
                
            if document_type is not None:
                stmt = stmt.where(VectorEmbedding.document_type == document_type)
                
            # Order by cosine similarity (using pgvector's operator)
            # Lower distance means higher similarity
            stmt = stmt.order_by(func.cosine_distance(VectorEmbedding.embedding, query_np))
            stmt = stmt.limit(limit)
            
            # Execute query
            result = await session.execute(stmt)
            entries = result.scalars().all()
            
            # Process results
            results = []
            for entry in entries:
                # Calculate similarity (convert distance to similarity score)
                similarity = 1.0 - await cosine_similarity(entry.embedding, query_np)
                
                # Apply threshold filtering
                if similarity >= threshold:
                    # Get metadata for filtering
                    metadata = entry.vector_metadata
                    
                    # Apply metadata filtering if provided
                    if metadata_filter:
                        # Skip if any filter doesn't match
                        if not all(metadata.get(k) == v for k, v in metadata_filter.items()):
                            continue
                    
                    # Add to results
                    results.append({
                        "record_id": entry.record_id,
                        "metadata": metadata,
                        "similarity": float(similarity),  # Ensure JSON serializable
                        "created_at": entry.created_at.isoformat(),
                        "document_type": entry.document_type
                    })
            
            return {
                "success": True, 
                "results": results, 
                "count": len(results),
                "query_time_ms": None  # Will be filled by timing decorator if used
            }
            
    except Exception as e:
        logger.error(f"Error searching vectors: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e), "error_type": type(e).__name__}

# Implement ANN search for better performance on large datasets
async def search_ann_vectors(
    query_vector: Union[List[float], np.ndarray],
    dataset_id: Optional[int] = None,
    limit: int = 10,
    ef_search: int = 40,  # Controls search accuracy vs speed
    metadata_filter: Optional[Dict[str, Any]] = None,
    document_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform approximate nearest neighbor search using HNSW index
    
    Args:
        query_vector: Vector to search against
        dataset_id: Optional dataset filter
        limit: Maximum results to return
        ef_search: HNSW parameter controlling search accuracy/speed tradeoff
        metadata_filter: Optional metadata filters
        document_type: Optional document type filter
        
    Returns:
        Dictionary with results and success status
    """
    async with AsyncSessionLocal() as session:
        try:
            # Convert query vector to the right format
            query_np = np.array(query_vector) if isinstance(query_vector, list) else query_vector
            
            # Set search parameters
            await session.execute(text(f"SET hnsw.ef_search = {ef_search}"))
            
            # Build query using KNN operator for ANN search
            query = """
                SELECT 
                    id, record_id, 1 - (embedding <=> :query_vector) as similarity,
                    vector_metadata, document_type, created_at
                FROM vector_embeddings
                WHERE 1=1
            """
            
            params = {"query_vector": query_vector}
            
            # Add filters
            if dataset_id is not None:
                query += " AND dataset_id = :dataset_id"
                params["dataset_id"] = dataset_id
                
            if document_type is not None:
                query += " AND document_type = :document_type"
                params["document_type"] = document_type
                
            if metadata_filter:
                for k, v in metadata_filter.items():
                    query += f" AND vector_metadata->>'%s' = :%s" % (k, k)
                    params[k] = v
            
            # Add order and limit
            query += " ORDER BY embedding <=> :query_vector LIMIT :limit"
            params["limit"] = limit
            
            # Execute query
            result = await session.execute(text(query), params)
            rows = result.fetchall()
            
            # Process results
            results = [{
                "id": row.id,
                "record_id": row.record_id,
                "similarity": float(row.similarity),
                "metadata": row.vector_metadata,
                "document_type": row.document_type,
                "created_at": row.created_at.isoformat() if row.created_at else None
            } for row in rows]
            
            return {"success": True, "results": results, "count": len(results)}
            
        except Exception as e:
            logger.error(f"ANN search error: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

# Delete all vectors for a specific dataset
async def delete_vectors(dataset_id: int):
    """
    Delete all vectors for a specific dataset
    
    Args:
        dataset_id: ID of the dataset to delete vectors for
        
    Returns:
        Dictionary with success status and count or error message
    """
    async with AsyncSessionLocal() as session:
        try:
            # Use efficient bulk delete
            async with session.begin():
                result = await session.execute(
                    select(func.count()).select_from(VectorEmbedding).where(
                        VectorEmbedding.dataset_id == dataset_id
                    )
                )
                count = result.scalar()
                
                # Delete all matching records
                await session.execute(
                    text("DELETE FROM vector_embeddings WHERE dataset_id = :dataset_id"),
                    {"dataset_id": dataset_id}
                )
                
            return {"success": True, "count": count or 0}
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

# This function is now part of the VectorService class

# This function is now part of the VectorService class

# Function to save vector database (called during shutdown)
async def save_vector_db():
    """Perform any necessary operations to save vector database state"""
    logger.info("Vector database state saved")
    return True

class VectorService:
    """Service for managing vector embeddings and similarity search operations."""
    
    def __init__(self):
        """Initialize the vector service."""
        self.engine = engine
        self.session_factory = AsyncSessionLocal
        self.initialized = False
        self.search_cache = {}
        self.cache_ttl = 300  # 5 minutes in seconds
        self.cache_max_size = 1000
        
    async def initialize(self):
        """Initialize the vector database and create tables/indexes if needed"""
        if self.initialized:
            return True
            
        try:
            logger.info("Initializing vector database...")
            async with self.engine.begin() as conn:
                # Create tables if they don't exist
                await conn.run_sync(Base.metadata.create_all)
                
                # Create vector index if it doesn't exist
                try:
                    await conn.execute(text(f"""
                        CREATE INDEX IF NOT EXISTS vector_embeddings_embedding_idx
                        ON vector_embeddings
                        USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100);
                    """))
                    logger.info("Vector index created or already exists")
                except Exception as e:
                    logger.warning(f"Could not create vector index: {e}")
                    
            logger.info("Vector database initialization complete")
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}", exc_info=True)
            return False
    
    async def get_session(self):
        """Get a database session"""
        session = self.session_factory()
        try:
            yield session
        finally:
            await session.close()
            
    async def add_vectors(self, dataset_id: int, vectors: List[Dict[str, Any]]):
        """Add vectors to the database for a specific dataset"""
        async with self.session_factory() as session:
            try:
                # Begin transaction
                async with session.begin():
                    entries = []
                    for v in vectors:
                        # Create VectorEmbedding instance
                        entry = VectorEmbedding(
                            dataset_id=dataset_id,
                            record_id=v["record_id"],
                            embedding=v["embedding"],
                            vector_metadata=v.get("metadata", {}),
                            document_type=v.get("document_type")
                        )
                        entries.append(entry)
                    
                    # Add all entries to session
                    session.add_all(entries)
                    
                return {"success": True, "count": len(entries)}
            except Exception as e:
                logger.error(f"Error adding vectors: {e}", exc_info=True)
                return {"success": False, "error": str(e)}
    
    def cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        if isinstance(vec1, list):
            vec1 = np.array(vec1)
        if isinstance(vec2, list):
            vec2 = np.array(vec2)
            
        # Normalize vectors
        vec1_norm = vec1 / np.linalg.norm(vec1)
        vec2_norm = vec2 / np.linalg.norm(vec2)
        
        # Calculate similarity
        return float(np.dot(vec1_norm, vec2_norm))
    
    async def search_similar_vectors(
        self, 
        query_vector: Union[List[float], np.ndarray], 
        dataset_id: Optional[int] = None, 
        limit: int = 10, 
        threshold: float = 0.6,
        metadata_filter: Optional[Dict[str, Any]] = None,
        document_type: Optional[str] = None
    ):
        """
        Search for vectors similar to the query vector with optional filtering.
        
        Args:
            query_vector: The vector to compare against
            dataset_id: Optional filter by dataset ID
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold (0-1)
            metadata_filter: Optional filter by metadata fields
            document_type: Optional filter by document type
            
        Returns:
            Dictionary with success status and results or error message
        """
        # Generate cache key for this query
        cache_key = f"{str(dataset_id)}_{str(limit)}_{str(threshold)}_{str(metadata_filter)}_{str(document_type)}_{hash(str(query_vector))}"
        
        # Check cache first
        if cache_key in self.search_cache:
            cache_entry = self.search_cache[cache_key]
            cache_time, cache_result = cache_entry
            
            # Check if cache is still valid (within TTL)
            if (datetime.utcnow() - cache_time).total_seconds() < self.cache_ttl:
                return cache_result
        
        async with self.session_factory() as session:
            try:
                # Build query conditions
                conditions = []
                params = {}
                
                # Add dataset filter if provided
                if dataset_id is not None:
                    conditions.append("dataset_id = :dataset_id")
                    params["dataset_id"] = dataset_id
                    
                # Add document type filter if provided
                if document_type is not None:
                    conditions.append("document_type = :document_type")
                    params["document_type"] = document_type
                    
                # Add metadata filters if provided
                if metadata_filter:
                    for i, (key, value) in enumerate(metadata_filter.items()):
                        conditions.append(f"vector_metadata->:key{i} = :value{i}")
                        params[f"key{i}"] = key
                        params[f"value{i}"] = json.dumps(value)
                
                # Build WHERE clause
                where_clause = " AND ".join(conditions) if conditions else "TRUE"
                
                # Execute query
                query = f"""
                SELECT id, record_id, embedding, vector_metadata, document_type,
                       embedding <=> :query_vector AS distance
                FROM vector_embeddings
                WHERE {where_clause}
                ORDER BY distance
                LIMIT :limit
                """
                params["query_vector"] = query_vector
                params["limit"] = limit
                
                result = await session.execute(text(query), params)
                
                # Process results
                matches = []
                for row in result:
                    # Calculate similarity (1 - distance)
                    similarity = 1.0 - float(row.distance)
                    
                    # Skip if below threshold
                    if similarity < threshold:
                        continue
                        
                    matches.append({
                        "id": row.id,
                        "record_id": row.record_id,
                        "similarity": similarity,
                        "metadata": row.vector_metadata,
                        "document_type": row.document_type
                    })
                    
                # Cache the result
                result_obj = {"success": True, "results": matches}
                self.search_cache[cache_key] = (datetime.utcnow(), result_obj)
                
                # Prune cache if too large
                if len(self.search_cache) > self.cache_max_size:
                    # Remove oldest entries
                    oldest_keys = sorted(
                        self.search_cache.keys(),
                        key=lambda k: self.search_cache[k][0]
                    )[:len(self.search_cache)//2]
                    
                    for k in oldest_keys:
                        del self.search_cache[k]
                
                return result_obj
            except Exception as e:
                logger.error(f"Error searching similar vectors: {e}", exc_info=True)
                return {"success": False, "error": str(e)}
    
    async def search_ann_vectors(
        self,
        query_vector: Union[List[float], np.ndarray],
        dataset_id: Optional[int] = None,
        limit: int = 10,
        ef_search: int = 40,  # Controls search accuracy vs speed
        metadata_filter: Optional[Dict[str, Any]] = None,
        document_type: Optional[str] = None
    ):
        """
        Perform approximate nearest neighbor search using HNSW index
        
        Args:
            query_vector: Vector to search against
            dataset_id: Optional dataset filter
            limit: Maximum results to return
            ef_search: Controls search accuracy vs speed
            metadata_filter: Optional metadata filter
            document_type: Optional document type filter
            
        Returns:
            Dictionary with success status and results or error message
        """
        # Generate cache key for this query
        cache_key = f"ann_{str(dataset_id)}_{str(limit)}_{str(ef_search)}_{str(metadata_filter)}_{str(document_type)}_{hash(str(query_vector))}"
        
        # Check cache first
        if cache_key in self.search_cache:
            cache_entry = self.search_cache[cache_key]
            cache_time, cache_result = cache_entry
            
            # Check if cache is still valid (within TTL)
            if (datetime.utcnow() - cache_time).total_seconds() < self.cache_ttl:
                return cache_result
        
        async with self.session_factory() as session:
            try:
                # Build query conditions
                conditions = []
                params = {}
                
                # Add dataset filter if provided
                if dataset_id is not None:
                    conditions.append("dataset_id = :dataset_id")
                    params["dataset_id"] = dataset_id
                    
                # Add document type filter if provided
                if document_type is not None:
                    conditions.append("document_type = :document_type")
                    params["document_type"] = document_type
                    
                # Add metadata filters if provided
                if metadata_filter:
                    for i, (key, value) in enumerate(metadata_filter.items()):
                        conditions.append(f"vector_metadata->:key{i} = :value{i}")
                        params[f"key{i}"] = key
                        params[f"value{i}"] = json.dumps(value)
                
                # Build WHERE clause
                where_clause = " AND ".join(conditions) if conditions else "TRUE"
                
                # Set HNSW search parameters
                # Higher ef_search = more accurate but slower
                await session.execute(
                    text(f"SET LOCAL hnsw.ef_search = {ef_search}")
                )
                
                # Execute query
                query = f"""
                SELECT id, record_id, embedding, vector_metadata, document_type,
                       1 - (embedding <=> :query_vector) AS similarity
                FROM vector_embeddings
                WHERE {where_clause}
                ORDER BY embedding <=> :query_vector
                LIMIT :limit
                """
                params["query_vector"] = query_vector
                params["limit"] = limit
                
                result = await session.execute(text(query), params)
                
                # Process results
                matches = []
                for row in result:
                    matches.append({
                        "id": row.id,
                        "record_id": row.record_id,
                        "similarity": float(row.similarity),
                        "metadata": row.vector_metadata,
                        "document_type": row.document_type
                    })
                    
                # Cache the result
                result_obj = {"success": True, "results": matches}
                self.search_cache[cache_key] = (datetime.utcnow(), result_obj)
                
                return result_obj
            except Exception as e:
                logger.error(f"Error in ANN search: {e}", exc_info=True)
                return {"success": False, "error": str(e)}
        
    async def save_vector_db(self):
        """Perform any necessary operations to save vector database state"""
        logger.info("Vector database state saved")
        return True
        
    async def delete_vectors(self, dataset_id: int):
        """
        Delete all vectors for a specific dataset
        
        Args:
            dataset_id: ID of the dataset to delete vectors for
            
        Returns:
            Dictionary with success status and count or error message
        """
        async with self.session_factory() as session:
            try:
                # Begin transaction
                async with session.begin():
                    # Delete all vectors for the dataset
                    result = await session.execute(
                        text("DELETE FROM vector_embeddings WHERE dataset_id = :dataset_id"),
                        {"dataset_id": dataset_id}
                    )
                    
                return {"success": True, "count": result.rowcount}
            except Exception as e:
                logger.error(f"Error deleting vectors: {e}", exc_info=True)
                return {"success": False, "error": str(e)}
                
    async def get_vector_stats(self):
        """
        Get statistics about the vector database
        
        Returns:
            Dictionary with success status and statistics or error message
        """
        async with self.session_factory() as session:
            try:
                # Get total vector count
                count_result = await session.execute(
                    select(func.count()).select_from(VectorEmbedding)
                )
                total_vectors = count_result.scalar() or 0
                
                # Get distinct dataset IDs
                datasets_result = await session.execute(
                    select(VectorEmbedding.dataset_id).distinct()
                )
                datasets = [d[0] for d in datasets_result.fetchall()]
                
                # Get count by document type
                doc_type_result = await session.execute(
                    select(
                        VectorEmbedding.document_type,
                        func.count()
                    ).group_by(VectorEmbedding.document_type)
                )
                document_types = {
                    dt if dt else "unspecified": count 
                    for dt, count in doc_type_result.fetchall()
                }
                
                # Compile statistics
                stats = {
                    "total_vectors": total_vectors,
                    "datasets": datasets,
                    "document_types": document_types,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                return {"success": True, "stats": stats}
            except Exception as e:
                logger.error(f"Error getting vector stats: {e}", exc_info=True)
                return {"success": False, "error": str(e)}
                
    async def get_vector_db(self, dataset_id: int) -> List[Dict]:
        """
        Fetch all vector embeddings for a given dataset_id from the vector_embeddings table.
        Returns a list of dicts with record_id, embedding, vector_metadata, created_at.
        
        Args:
            dataset_id: ID of the dataset to fetch vectors for
            
        Returns:
            List of dictionaries with vector data
        """
        async with self.session_factory() as session:
            try:
                result = await session.execute(
                    select(VectorEmbedding).where(VectorEmbedding.dataset_id == dataset_id)
                )
                
                embeddings = []
                for entry in result.scalars():
                    embeddings.append({
                        "record_id": entry.record_id,
                        "embedding": entry.embedding,
                        "metadata": entry.vector_metadata,
                        "document_type": entry.document_type,
                        "created_at": entry.created_at.isoformat() if entry.created_at else None,
                        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
                        "version": entry.version
                    })
                    
                return embeddings
            except Exception as e:
                logger.error(f"Error fetching vector database: {e}", exc_info=True)
                return []

# Create a singleton instance
vector_service = VectorService()
