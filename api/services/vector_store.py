import numpy as np
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, Integer, String, DateTime, select
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector
from datetime import datetime
import os
import json
from sentence_transformers import SentenceTransformer

from db.connection import get_db_session
from config.settings import get_settings

settings = get_settings()
Base = declarative_base()

from sqlalchemy.dialects.postgresql import JSONB

class VectorEmbedding(Base):
    __tablename__ = "vector_embeddings"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, index=True)
    record_id = Column(String(255), nullable=False)
    embedding = Column(Vector(settings.VECTOR_DIMENSION))
    vector_metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.vector_metadata.create_all(bind=engine)

class VectorStoreService:
    def __init__(self, vector_dim: int = 384):
        self.vector_dim = vector_dim
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    async def store_data(self, data: List[Dict[str, Any]], dataset_id: int, vector_metadata: Dict[str, Any]) -> bool:
        """
        Store data and its embeddings in the vector_embeddings table.
        data: List of {"record_id": ..., "embedding": ...} dicts
        """
        async with get_db_session() as session:
            try:
                entries = []
                for item in data:
                    entries.append(VectorEmbedding(
                        dataset_id=dataset_id,
                        record_id=item["record_id"],
                        embedding=item["embedding"],
                        vector_metadata={**vector_metadata, **item.get("vector_metadata", {})},
                    ))
                session.add_all(entries)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                print(f"Error storing data in vector_embeddings: {str(e)}")
                return False

    async def search_similar_data(
        self,
        query_vector: List[float],
        dataset_id: Optional[str] = None,
        limit: int = 5,
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Search for similar data in the vector database by vector.
        """
        async with get_db_session() as session:
            try:
                query_np = np.array(query_vector)
                stmt = select(VectorEmbedding)
                if dataset_id:
                    stmt = stmt.where(VectorEmbedding.dataset_id == dataset_id)
                stmt = stmt.order_by(VectorEmbedding.embedding.cosine_distance(query_np))
                stmt = stmt.limit(limit)
                result = await session.execute(stmt)
                search_results = []
                for entry in result.scalars():
                    similarity = 1 - entry.embedding.cosine_distance(query_np)
                    if similarity >= threshold:
                        search_results.append({
                            "similarity": float(similarity),
                            "record_id": entry.record_id,
                            "vector_metadata": entry.vector_metadata
                        })
                return search_results
            except Exception as e:
                print(f"Error searching vector database: {str(e)}")
                return []

    async def get_dataset_info(self, dataset_id: str) -> Dict[str, Any]:
        async with get_db_session() as session:
            try:
                from sqlalchemy import func
                count = await session.scalar(select(func.count(VectorEmbedding.id)).where(VectorEmbedding.dataset_id == dataset_id))
                return {
                    "dataset_id": dataset_id,
                    "row_count": count
                }
            except Exception as e:
                print(f"Error getting dataset info: {str(e)}")
                return {}
