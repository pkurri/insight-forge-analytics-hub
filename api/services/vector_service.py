import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import numpy as np
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector
import os
from api.db.connection import get_db_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class VectorEmbedding(Base):
    __tablename__ = "vector_embeddings"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, index=True)
    record_id = Column(String(255), nullable=False)
    embedding = Column(Vector(1536))  # Must match VECTOR_DIMENSION in config and DB
    vector_metadata = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.vector_metadata.create_all(bind=engine)

from sqlalchemy.exc import SQLAlchemyError

# Add vectors to the database for a specific dataset
async def add_vectors(dataset_id: int, vectors: List[Dict[str, Any]]):
    async with get_db_session() as session:
        try:
            entries = []
            for v in vectors:
                entries.append(VectorEmbedding(
                    dataset_id=dataset_id,
                    record_id=v["record_id"],
                    embedding=v["embedding"],
                    vector_metadata=json.dumps(v.get("vector_metadata", {})),
                ))
            session.add_all(entries)
            await session.commit()
            return {"success": True, "count": len(entries)}
        except Exception as e:
            await session.rollback()
            logger.error(f"Error adding vectors: {e}")
            return {"success": False, "error": str(e)}

# Search for similar vectors in the database
async def search_similar_vectors(query_vector: Union[List[float], np.ndarray], dataset_id: Optional[int] = None, limit: int = 5, threshold: float = 0.6) -> Dict[str, Any]:
    async with get_db_session() as session:
        try:
            query_np = np.array(query_vector) if isinstance(query_vector, list) else query_vector
            stmt = select(VectorEmbedding)
            if dataset_id:
                stmt = stmt.where(VectorEmbedding.dataset_id == dataset_id)
            stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            results = []
            for entry in result.scalars():
                similarity = float(1.0 / (1.0 + l2_distance(entry.embedding, query_np)))
                if similarity >= threshold:
                    results.append({
                        "record_id": entry.record_id,
                        "vector_metadata": json.loads(entry.vector_metadata),
                        "similarity": similarity
                    })
            return {"success": True, "results": results}
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            return {"success": False, "error": str(e)}

# Delete all vectors for a specific dataset
async def delete_vectors(dataset_id: int):
    async with get_db_session() as session:
        try:
            result = await session.execute(select(VectorEmbedding).where(VectorEmbedding.dataset_id == dataset_id))
            count = 0
            for entry in result.scalars():
                await session.delete(entry)
                count += 1
            await session.commit()
            return {"success": True, "count": count}
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting vectors: {e}")
            return {"success": False, "error": str(e)}

# Get statistics about the vector database
async def get_vector_stats():
    async with get_db_session() as session:
        try:
            from sqlalchemy import func
            total_vectors = await session.scalar(select(func.count(VectorEmbedding.id)))
            datasets_result = await session.execute(select(VectorEmbedding.dataset_id).distinct())
            datasets = [d[0] for d in datasets_result.fetchall()]
            stats = {"total_vectors": total_vectors, "datasets": datasets}
            return {"success": True, "stats": stats}
        except Exception as e:
            logger.error(f"Error getting vector stats: {e}")
            return {"success": False, "error": str(e)}

# Hugging Face internal API call example (for embedding)
INTERNAL_HF_API_URL = os.getenv("INTERNAL_HF_API_URL", "https://internal.company.com/hf-api")
INTERNAL_HF_API_USER = os.getenv("INTERNAL_HF_API_USER", "user")
INTERNAL_HF_API_PASS = os.getenv("INTERNAL_HF_API_PASS", "pass")

# Deprecated: Use centralized internal embedding/textgen API instead.

async def get_vector_db(dataset_id: int) -> list[dict]:
    """
    Fetch all vector embeddings for a given dataset_id from the vector_embeddings table.
    Returns a list of dicts with record_id, embedding, vector_metadata, created_at.
    """
    async with get_db_session() as session:
        result = await session.execute(
            select(VectorEmbedding).where(VectorEmbedding.dataset_id == dataset_id)
        )
        embeddings = []
        for entry in result.scalars():
            embeddings.append({
                "record_id": entry.record_id,
                "embedding": entry.embedding,
                "vector_metadata": entry.vector_metadata,
                "created_at": entry.created_at,
            })
        return embeddings
