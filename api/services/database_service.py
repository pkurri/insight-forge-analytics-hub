from typing import Dict, Any, List, Optional
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import ARRAY, FLOAT
from config.settings import get_settings
from models.dataset import Dataset, DatasetMetadata
from utils.db import get_db_connection
import faiss
import asyncpg
import pandas as pd

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from api.config.settings import get_settings

class DatabaseService:
    def __init__(self):
        self.settings = get_settings()
        self.engine = create_async_engine(
            f'postgresql+asyncpg://{self.settings.DB_USER}:{self.settings.DB_PASSWORD}@{self.settings.DB_HOST}:{self.settings.DB_PORT}/{self.settings.DB_NAME}',
            pool_size=10, max_overflow=20, pool_timeout=30, pool_recycle=1800
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_async_session(self):
        async with self.async_session() as session:
            yield session

    async def search_similar_vectors(self, table_name: str, query_vector, limit: int = 10):
        """
        Search for similar vectors using pgvector (<=> operator)
        """
        from sqlalchemy import text
        sql = text(f"""
            SELECT id, content, embedding <=> :query_vector AS distance
            FROM {table_name}
            ORDER BY distance ASC
            LIMIT :limit
        """)
        async with self.async_session() as session:
            result = await session.execute(sql, {"query_vector": query_vector.tolist(), "limit": limit})
            return result.fetchall()
    async def initialize(self):
        """Initialize the database connection pool"""
        self.pool = await asyncpg.create_pool(
            user=self.config['user'],
            password=self.config['password'],
            database=self.config['database'],
            host=self.config['host'],
            port=self.config['port']
        )
        
        # Register vector extension with all connections in the pool
        async with self.pool.acquire() as conn:
            await register_vector(conn)
            # Enable pgvector extension if not already enabled
            await conn.execute('CREATE EXTENSION IF NOT EXISTS vector;')

    async def search_similar_datasets(self, query_embedding: np.ndarray, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar datasets using vector similarity."""
        async with self.async_session() as session:
            result = await session.execute(
                text(
                    'SELECT d.*, ('
                    'SELECT embedding <=> :query_embedding AS distance '
                    'FROM dataset_embeddings de '
                    'WHERE de.dataset_id = d.id'
                    ') as similarity '
                    'FROM datasets d '
                    'ORDER BY similarity ASC '
                    'LIMIT :limit'
                ),
                {
                    'query_embedding': query_embedding.tolist(),
                    'limit': limit
                }
            )
            return [dict(r._mapping) for r in result]

    async def store_dataset(self, data: Dict[str, Any], embeddings: Optional[np.ndarray] = None) -> str:
        """Store dataset with optional vector embeddings."""
        async with self.async_session() as session:
            try:
                # Create dataset entry
                dataset = Dataset(
                    name=data['name'],
                    description=data.get('description', ''),
                    file_path=data.get('file_path', ''),
                    status='active'
                )
                session.add(dataset)
                await session.flush()

                # Store metadata
                if 'metadata' in data:
                    metadata = DatasetMetadata(
                        dataset_id=dataset.id,
                        column_info=data['metadata'].get('column_info', {}),
                        row_count=data['metadata'].get('row_count', 0),
                        column_count=data['metadata'].get('column_count', 0)
                    )
                    session.add(metadata)

                # Store vector embeddings if provided
                if embeddings is not None:
                    await session.execute(
                        text(
                            'INSERT INTO dataset_embeddings (dataset_id, embedding) '
                            'VALUES (:dataset_id, :embedding)'
                        ),
                        {
                            'dataset_id': dataset.id,
                            'embedding': embeddings.tolist()
                        }
                    )

                await session.commit()
                return str(dataset.id)

            except Exception as e:
                await session.rollback()
                raise e

    async def store_vectors(self, table_name: str, vectors: List[np.ndarray], metadata: List[Dict[str, Any]]):
        """Store vectors and their metadata in PostgreSQL"""
        async with self.pool.acquire() as conn:
            # Create table if it doesn't exist
            await conn.execute(f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    embedding vector({self.vector_dimension}),
                    metadata JSONB
                )
            ''')
            
            # Store vectors and metadata
            for vector, meta in zip(vectors, metadata):
                await conn.execute(
                    f'INSERT INTO {table_name} (embedding, metadata) VALUES ($1, $2)',
                    vector.tolist(),
                    meta
                )

    async def search_similar_vectors(
        self,
        table_name: str,
        query_vector: np.ndarray,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors using cosine similarity"""
        async with self.pool.acquire() as conn:
            results = await conn.fetch(f'''
                SELECT id, embedding, metadata,
                       1 - (embedding <=> $1) as similarity
                FROM {table_name}
                ORDER BY embedding <=> $1
                LIMIT $2
            ''', query_vector.tolist(), limit)
            
            return [
                {
                    'id': r['id'],
                    'similarity': r['similarity'],
                    'metadata': r['metadata']
                }
                for r in results
            ]

    async def store_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: str = 'replace'
    ):
        """Store a pandas DataFrame in PostgreSQL"""
        engine = create_engine(
            f"postgresql://{self.config['user']}:{self.config['password']}@"
            f"{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )
        
        df.to_sql(
            table_name,
            engine,
            if_exists=if_exists,
            index=False
        )

    async def query_to_dataframe(self, query: str) -> pd.DataFrame:
        """Execute a query and return results as a pandas DataFrame"""
        async with self.pool.acquire() as conn:
            results = await conn.fetch(query)
            return pd.DataFrame(results)

    async def create_faiss_index(
        self,
        table_name: str,
        index_type: str = 'IVFFlat'
    ):
        """Create a FAISS index from vectors stored in PostgreSQL"""
        async with self.pool.acquire() as conn:
            # Fetch all vectors
            vectors = await conn.fetch(f'SELECT embedding FROM {table_name}')
            vectors = np.array([v['embedding'] for v in vectors])
            
            # Create and train FAISS index
            if index_type == 'IVFFlat':
                quantizer = faiss.IndexFlatL2(self.vector_dimension)
                index = faiss.IndexIVFFlat(
                    quantizer,
                    self.vector_dimension,
                    min(int(len(vectors) / 10), 100),  # number of centroids
                    faiss.METRIC_L2
                )
                if len(vectors) > 0:
                    index.train(vectors)
                    index.add(vectors)
                return index
            else:
                raise ValueError(f"Unsupported index type: {index_type}")

    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            await self.pool.close()
