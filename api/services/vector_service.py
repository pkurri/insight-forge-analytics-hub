import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import numpy as np
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup for pgvector
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://user:password@localhost:5432/yourdb")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class VectorEntry(Base):
    __tablename__ = "vectors"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String, index=True)
    vector = Column(Vector(384))  # Adjust dimension as needed
    content = Column(String)
    metadata = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

from sqlalchemy.exc import SQLAlchemyError

# Add vectors to the database for a specific dataset
async def add_vectors(dataset_id: str, vectors: List[Dict[str, Any]]):
    session = SessionLocal()
    try:
        entries = []
        for v in vectors:
            entries.append(VectorEntry(
                dataset_id=dataset_id,
                vector=v["vector"],
                content=v.get("content", ""),
                metadata=json.dumps(v.get("metadata", {})),
            ))
        session.add_all(entries)
        session.commit()
        return {"success": True, "count": len(entries)}
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error adding vectors: {e}")
        return {"success": False, "error": str(e)}
    finally:
        session.close()

# Search for similar vectors in the database
async def search_similar_vectors(query_vector: Union[List[float], np.ndarray], dataset_id: Optional[str] = None, limit: int = 5, threshold: float = 0.6) -> Dict[str, Any]:
    session = SessionLocal()
    try:
        query_np = np.array(query_vector) if isinstance(query_vector, list) else query_vector
        q = session.query(VectorEntry)
        if dataset_id:
            q = q.filter(VectorEntry.dataset_id == dataset_id)
        q = q.order_by(l2_distance(VectorEntry.vector, query_np)).limit(limit)
        results = []
        for entry in q:
            # Compute similarity (inverse L2 for demonstration)
            similarity = float(1.0 / (1.0 + l2_distance(entry.vector, query_np)))
            if similarity >= threshold:
                results.append({
                    "content": entry.content,
                    "metadata": json.loads(entry.metadata),
                    "similarity": similarity
                })
        return {"success": True, "results": results}
    except SQLAlchemyError as e:
        logger.error(f"Error searching vectors: {e}")
        return {"success": False, "error": str(e)}
    finally:
        session.close()

# Delete all vectors for a specific dataset
def delete_vectors(dataset_id: str):
    session = SessionLocal()
    try:
        count = session.query(VectorEntry).filter(VectorEntry.dataset_id == dataset_id).delete()
        session.commit()
        return {"success": True, "count": count}
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error deleting vectors: {e}")
        return {"success": False, "error": str(e)}
    finally:
        session.close()

# Get statistics about the vector database
def get_vector_stats():
    session = SessionLocal()
    try:
        total_vectors = session.query(VectorEntry).count()
        datasets = session.query(VectorEntry.dataset_id).distinct()
        stats = {"total_vectors": total_vectors, "datasets": [d[0] for d in datasets]}
        return {"success": True, "stats": stats}
    except SQLAlchemyError as e:
        logger.error(f"Error getting vector stats: {e}")
        return {"success": False, "error": str(e)}
    finally:
        session.close()

# Hugging Face internal API call example (for embedding)
INTERNAL_HF_API_URL = os.getenv("INTERNAL_HF_API_URL", "https://internal.company.com/hf-api")
INTERNAL_HF_API_USER = os.getenv("INTERNAL_HF_API_USER", "user")
INTERNAL_HF_API_PASS = os.getenv("INTERNAL_HF_API_PASS", "pass")

def call_internal_hf_api(payload: dict) -> dict:
    resp = requests.post(
        INTERNAL_HF_API_URL,
        json=payload,
        auth=(INTERNAL_HF_API_USER, INTERNAL_HF_API_PASS)
    )
    resp.raise_for_status()
    return resp.json()
