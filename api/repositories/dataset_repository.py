from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from api.db.connection import get_db_session
from api.config.redis_config import get_redis_client
from api.services.analytics_service import (
    process_dataset,
    cleaning_metadata,
    detect_anomalies,
    get_data_profile
)
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import numpy as np

from api.models.db_models import Dataset, DatasetColumn, DatasetEmbedding, PipelineRun
from api.models.dataset import DatasetCreate, DatasetStatus

class DatasetRepository:
    """Repository for dataset-related database operations."""
    
    def __init__(self):
        """Initialize the repository with database and Redis connection."""
        self.redis = get_redis_client()
        self.cache_ttl = 3600  # Cache TTL in seconds
        
    async def _get_cache_key(self, key_type: str, key_id: str) -> str:
        """Generate cache key."""
        return f"dataset:{key_type}:{key_id}"

    async def create_dataset(self, dataset: DatasetCreate, user_id: int) -> Dataset:
        db_dataset = Dataset(
            user_id=user_id,
            name=dataset.name,
            description=dataset.description,
            file_type=dataset.file_type,
            status=DatasetStatus.PENDING
        )
        async with get_db_session() as session:
            session.add(db_dataset)
            await session.flush()
        return db_dataset

    async def store_embeddings(self, dataset_id: int, embeddings: np.ndarray) -> None:
        db_embedding = DatasetEmbedding(
            dataset_id=dataset_id,
            embedding=embeddings.tolist()
        )
        async with get_db_session() as session:
            session.add(db_embedding)
            await session.flush()

    async def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get a dataset by ID."""
        try:
            # Check cache first
            cache_key = await self._get_cache_key("dataset", dataset_id)
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            
            # Query database
            async with get_db_session() as session:
                result = await session.execute(
                    text(f"""
                    SELECT * FROM {settings.DB_SCHEMA}.datasets 
                    WHERE id = :dataset_id
                    """),
                    {"dataset_id": dataset_id}
                )
                row = result.first()
                if row:
                    dataset = dict(row)
                    dataset["ds_metadata"] = json.loads(dataset["ds_metadata"])
                    
                    # Cache the result
                    await self.redis.setex(
                        cache_key,
                        self.cache_ttl,
                        json.dumps(dataset)
                    )
                    return dataset
                return None
                
        except Exception as e:
            logger.error(f"Error getting dataset: {str(e)}")
            raise

    async def get_datasets_by_user(self, user_id: int) -> List[Dataset]:
        async with get_db_session() as session:
            result = await session.execute(
                text(f"""
                SELECT * FROM {settings.DB_SCHEMA}.datasets 
                WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )
            return [dict(row) for row in result]

    async def search_similar_datasets(
        self,
        query_embedding: np.ndarray,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar datasets using vector similarity."""
        async with get_db_session() as session:
            result = await session.execute(
                text("""
                SELECT 
                    d.*,
                    e.embedding <=> :query_embedding as similarity
                FROM datasets d
                JOIN dataset_embeddings e ON d.id = e.dataset_id
                ORDER BY similarity ASC
                LIMIT :limit
                """),
                {
                    "query_embedding": query_embedding.tolist(),
                    "limit": limit
                }
            )
            return [dict(r._mapping) for r in result]

    async def update_dataset_status(
        self,
        dataset_id: int,
        status: DatasetStatus,
        ds_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        async with get_db_session() as session:
            result = await session.execute(
                text("""
                SELECT * FROM datasets 
                WHERE id = :dataset_id
                """),
                {"dataset_id": dataset_id}
            )
            row = result.first()
            if row:
                dataset = dict(row)
                dataset["status"] = status.value
                if ds_metadata:
                    dataset["ds_metadata"] = json.dumps({**json.loads(dataset["ds_metadata"]), **ds_metadata})
                await session.execute(
                    text("""
                    UPDATE datasets 
                    SET status = :status, ds_metadata = :ds_metadata
                    WHERE id = :dataset_id
                    """),
                    {
                        "status": dataset["status"],
                        "ds_metadata": dataset["ds_metadata"],
                        "dataset_id": dataset_id
                    }
                )
                await session.commit()

    async def add_dataset_columns(
        self,
        dataset_id: int,
        columns: List[Dict[str, Any]]
    ) -> None:
        async with get_db_session() as session:
            for col in columns:
                db_column = DatasetColumn(
                    dataset_id=dataset_id,
                    name=col["name"],
                    data_type=col["data_type"],
                    nullable=col.get("nullable", True),
                    stats=col.get("stats", {})
                )
                session.add(db_column)
            await session.commit()

    async def get_latest_pipeline_run(self, dataset_id: int) -> Optional[PipelineRun]:
        async with get_db_session() as session:
            result = await session.execute(
                text("""
                SELECT * FROM pipeline_runs 
                WHERE dataset_id = :dataset_id
                ORDER BY start_time DESC
                LIMIT 1
                """),
                {"dataset_id": dataset_id}
            )
            row = result.first()
            if row:
                return PipelineRun(**dict(row))
            return None

    async def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset."""
        try:
            # Get dataset first for cache invalidation
            dataset = await self.get_dataset(dataset_id)
            if dataset:
                async with get_db_session() as session:
                    await session.execute(
                        text("DELETE FROM datasets WHERE id = :id"),
                        {"id": dataset_id}
                    )
                    await session.commit()
                    
                    # Invalidate cache
                    cache_keys = [
                        await self._get_cache_key("dataset", dataset_id),
                        await self._get_cache_key("user_datasets", str(dataset["user_id"])),
                        await self._get_cache_key("user_datasets", "all")
                    ]
                    for key in cache_keys:
                        await self.redis.delete(key)
                    
                    return True
            return False
                
        except Exception as e:
            logger.error(f"Error deleting dataset: {str(e)}")
            raise
        return False
