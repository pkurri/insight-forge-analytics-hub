import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from sentence_transformers import SentenceTransformer
from config.settings import get_settings
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import json

settings = get_settings()

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
