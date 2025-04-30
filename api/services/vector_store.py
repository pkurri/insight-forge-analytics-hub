import numpy as np
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector, l2_distance
from datetime import datetime
import os
import json
import requests

from api.db.connection import get_db_session
Base = declarative_base()

from sqlalchemy.dialects.postgresql import JSONB
from api.config.settings import get_settings

settings = get_settings()

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
                stmt = stmt.limit(limit)
                result = await session.execute(stmt)
                search_results = []
                for entry in result.scalars():
                    similarity = float(1.0 / (1.0 + l2_distance(entry.embedding, query_np)))
                    if similarity >= threshold:
                        search_results.append({
                            "similarity": similarity,
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

    async def store_data(self, df: pd.DataFrame, vector_metadata: Dict[str, Any]) -> bool:
        """Store data and its embeddings in the vector database."""
        try:
            collection_name = f"dataset_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create collection fields
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="content_vector", dtype=DataType.FLOAT_VECTOR, dim=self.vector_dim),
                FieldSchema(name="vector_metadata", dtype=DataType.VARCHAR, max_length=65535),
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
                [json.dumps(vector_metadata)] * len(text_data),
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
                output_fields=["vector_metadata", "text_content"]
            )

            # Format results
            search_results = []
            for hits in results:
                for hit in hits:
                    search_results.append({
                        "score": float(hit.score),
                        "text_content": hit.entity.get("text_content"),
                        "vector_metadata": json.loads(hit.entity.get("vector_metadata"))
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
