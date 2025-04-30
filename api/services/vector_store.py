import numpy as np
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector, l2_distance
from datetime import datetime
import os
import json
import requests

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://user:password@localhost:5432/yourdb")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

from sqlalchemy.dialects.postgresql import JSONB
from api.config.settings import get_settings

settings = get_settings()

class VectorEntry(Base):
    __tablename__ = "vector_embeddings"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, index=True)
    record_id = Column(String(255), nullable=False)
    # Embedding dimension must match the database schema (default 1536, configurable)
    embedding = Column(Vector(settings.VECTOR_DIMENSION))
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

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

class VectorStoreService:
    def __init__(self, vector_dim: int = 384):
        self.vector_dim = vector_dim

    async def store_data(self, data: List[Dict[str, Any]], dataset_id: int, metadata: Dict[str, Any]) -> bool:
        """
        Store data and its embeddings in the vector_embeddings table.
        data: List of {"record_id": ..., "embedding": ...} dicts
        """
        session = SessionLocal()
        try:
            entries = []
            for item in data:
                entries.append(VectorEntry(
                    dataset_id=dataset_id,
                    record_id=item["record_id"],
                    embedding=item["embedding"],
                    metadata={**metadata, **item.get("metadata", {})},
                ))
            session.add_all(entries)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error storing data in vector_embeddings: {str(e)}")
            return False
        finally:
            session.close()

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
        session = SessionLocal()
        try:
            query_np = np.array(query_vector)
            q = session.query(VectorEntry)
            if dataset_id:
                q = q.filter(VectorEntry.dataset_id == dataset_id)
            q = q.order_by(l2_distance(VectorEntry.vector, query_np)).limit(limit)
            search_results = []
            for entry in q:
                similarity = float(1.0 / (1.0 + l2_distance(entry.vector, query_np)))
                if similarity >= threshold:
                    search_results.append({
                        "similarity": similarity,
                        "text_content": entry.content,
                        "metadata": json.loads(entry.metadata)
                    })
            return search_results
        except Exception as e:
            print(f"Error searching vector database: {str(e)}")
            return []
        finally:
            session.close()

    async def get_dataset_info(self, dataset_id: str) -> Dict[str, Any]:
        session = SessionLocal()
        try:
            count = session.query(VectorEntry).filter(VectorEntry.dataset_id == dataset_id).count()
            return {
                "dataset_id": dataset_id,
                "row_count": count
            }
        except Exception as e:
            print(f"Error getting dataset info: {str(e)}")
            return {}
        finally:
            session.close()

class VectorStoreService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_dim = 384  # Dimension of the sentence transformer model
        
        # Connect to Milvus
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )

    async def store_data(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> bool:
        """Store data and its embeddings in the vector database."""
        try:
            collection_name = f"dataset_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create collection fields
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="content_vector", dtype=DataType.FLOAT_VECTOR, dim=self.vector_dim),
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="text_content", dtype=DataType.VARCHAR, max_length=65535)
            ]
            
            schema = CollectionSchema(fields=fields, description=f"Dataset collection {collection_name}")
            collection = Collection(name=collection_name, schema=schema)

            # Convert DataFrame to text representation
            text_data = df.apply(lambda x: ' '.join(x.astype(str)), axis=1).tolist()
            
            # Generate embeddings
            embeddings = self.model.encode(text_data)
            
            # Prepare data for insertion
            data = [
                [],  # id will be auto-generated
                embeddings.tolist(),
                [json.dumps(metadata)] * len(text_data),
                text_data
            ]
            
            # Insert data
            collection.insert(data)
            
            # Create index for vector field
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            collection.create_index(field_name="content_vector", index_params=index_params)
            
            # Load collection for searching
            collection.load()
            
            return True
            
        except Exception as e:
            print(f"Error storing data in vector database: {str(e)}")
            return False

    async def search_similar_data(
        self,
        query: str,
        limit: int = 5,
        collection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar data in the vector database."""
        try:
            # If no collection specified, use the most recent one
            if not collection_name:
                collections = utility.list_collections()
                if not collections:
                    return []
                collection_name = max(collections)  # Get the most recent collection

            collection = Collection(collection_name)
            collection.load()

            # Generate query embedding
            query_embedding = self.model.encode([query])[0]

            # Search parameters
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }

            # Perform search
            results = collection.search(
                data=[query_embedding.tolist()],
                anns_field="content_vector",
                param=search_params,
                limit=limit,
                output_fields=["metadata", "text_content"]
            )

            # Format results
            search_results = []
            for hits in results:
                for hit in hits:
                    search_results.append({
                        "score": float(hit.score),
                        "text_content": hit.entity.get("text_content"),
                        "metadata": json.loads(hit.entity.get("metadata"))
                    })

            return search_results

        except Exception as e:
            print(f"Error searching vector database: {str(e)}")
            return []

    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection."""
        try:
            collection = Collection(collection_name)
            
            return {
                "name": collection_name,
                "row_count": collection.num_entities,
                "schema": collection.schema.to_dict(),
                "indexes": collection.indexes
            }
        except Exception as e:
            print(f"Error getting collection info: {str(e)}")
            return {}
