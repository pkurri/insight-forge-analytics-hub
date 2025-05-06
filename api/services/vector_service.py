import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import numpy as np
from sqlalchemy import Column, Integer, String, DateTime, Index, text, select, func, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
import os
from functools import wraps

# Import configuration
from config.settings import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create engine and session factory
engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class VectorEmbedding(Base):
    __tablename__ = "dataset_embeddings"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, nullable=False)
    record_id = Column(String(100), nullable=False)
    content = Column(Text, nullable=True)  # Original text content for RAG
    chunk_index = Column(Integer, nullable=True)  # Index of chunk in document
    chunk_text = Column(Text, nullable=True)  # The actual text chunk
    embedding = Column(Vector(384))  # Using standard dimension for vector embeddings
    vector_metadata = Column(JSONB, default=dict)  # Additional metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('dataset_embeddings_idx', embedding, postgresql_using='ivfflat', 
              postgresql_with={'lists': 100}, postgresql_ops={'embedding': 'vector_cosine_ops'}),
        Index('dataset_record_idx', dataset_id, record_id, unique=True),
        Index('dataset_content_idx', dataset_id, chunk_index),  # For ordered retrieval
    )

class VectorService:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.vector_dim = 384  # Standard dimension for vector embeddings
            self._initialized = True
    
    async def initialize(self):
        """Initialize the vector database and create tables/indexes if needed"""
        try:
            logger.info("Initializing vector database...")
            async with engine.begin() as conn:
                # Create tables if they don't exist
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Vector database initialization complete")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}", exc_info=True)
            return False

    async def get_session(self):
        """Get a database session"""
        session = AsyncSessionLocal()
        try:
            yield session
        finally:
            await session.close()

    async def add_vectors(self, dataset_id: int, vectors: List[Dict[str, Any]]):
        """
        Add vectors to the database for a specific dataset
        
        Args:
            dataset_id: ID of the dataset
            vectors: List of vector data dictionaries with record_id, embedding, content, and optional metadata
            
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
                            record_id=v['record_id'],
                            content=v.get('content', ''),  # Store original content for RAG
                            chunk_index=v.get('chunk_index'),  # Store chunk index
                            chunk_text=v.get('chunk_text', ''),  # Store chunk text
                            embedding=v['embedding'],
                            vector_metadata=v.get('metadata', {})
                        )
                        entries.append(entry)
                    
                    # Bulk insert all entries
                    session.add_all(entries)
                    
                return {
                    "success": True,
                    "count": len(entries),
                    "message": f"Successfully added {len(entries)} vectors for dataset {dataset_id}"
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
        async with AsyncSessionLocal() as session:
            try:
                # Start with base query
                stmt = select(VectorEmbedding)
                
                # Apply filters
                if dataset_id is not None:
                    stmt = stmt.where(VectorEmbedding.dataset_id == dataset_id)
                
                # Order by cosine similarity
                stmt = stmt.order_by(VectorEmbedding.embedding.cosine_distance(query_vector))
                stmt = stmt.limit(limit)
                
                # Execute query
                result = await session.execute(stmt)
                entries = result.scalars().all()
                
                # Process results
                search_results = []
                for entry in entries:
                    # Calculate similarity
                    similarity = 1 - entry.embedding.cosine_distance(query_vector)
                    
                    # Apply threshold filtering
                    if similarity >= threshold:
                        # Check metadata filter if provided
                        if metadata_filter:
                            metadata_match = all(
                                entry.vector_metadata.get(k) == v 
                                for k, v in metadata_filter.items()
                            )
                            if not metadata_match:
                                continue
                        
                        result = {
                            "similarity": float(similarity),
                            "record_id": entry.record_id,
                            "content": entry.content,  # Include content for RAG
                            "vector_metadata": entry.vector_metadata
                        }
                        
                        # Include chunk information if requested
                        if include_chunks and entry.chunk_text:
                            result.update({
                                "chunk_index": entry.chunk_index,
                                "chunk_text": entry.chunk_text
                            })
                        
                        search_results.append(result)
                
                return search_results
            except Exception as e:
                logger.error(f"Error searching vector database: {str(e)}")
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
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(VectorEmbedding).where(
                    VectorEmbedding.dataset_id == dataset_id,
                    VectorEmbedding.record_id == record_id
                ).order_by(VectorEmbedding.chunk_index)
                
                if start_index is not None:
                    stmt = stmt.where(VectorEmbedding.chunk_index >= start_index)
                if end_index is not None:
                    stmt = stmt.where(VectorEmbedding.chunk_index <= end_index)
                
                result = await session.execute(stmt)
                entries = result.scalars().all()
                
                return [{
                    "chunk_index": entry.chunk_index,
                    "chunk_text": entry.chunk_text,
                    "content": entry.content,
                    "metadata": entry.vector_metadata
                } for entry in entries]
            except Exception as e:
                logger.error(f"Error getting ordered chunks: {str(e)}")
                return []

    async def delete_vectors(self, dataset_id: int) -> Dict[str, Any]:
        """Delete all vectors for a specific dataset"""
        async with AsyncSessionLocal() as session:
            try:
                async with session.begin():
                    await session.execute(
                        text("DELETE FROM dataset_embeddings WHERE dataset_id = :dataset_id"),
                        {"dataset_id": dataset_id}
                    )
                return {"success": True, "message": f"Deleted vectors for dataset {dataset_id}"}
            except Exception as e:
                logger.error(f"Error deleting vectors: {e}", exc_info=True)
                return {"success": False, "error": str(e)}

    async def get_dataset_info(self, dataset_id: int) -> Dict[str, Any]:
        """Get information about vectors stored for a specific dataset"""
        async with AsyncSessionLocal() as session:
            try:
                count = await session.scalar(
                    select(func.count(VectorEmbedding.id))
                    .where(VectorEmbedding.dataset_id == dataset_id)
                )
                
                # Get unique record count
                record_count = await session.scalar(
                    select(func.count(func.distinct(VectorEmbedding.record_id)))
                    .where(VectorEmbedding.dataset_id == dataset_id)
                )
                
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
