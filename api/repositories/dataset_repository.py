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
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.dataset import Dataset, DatasetCreate, DatasetStatus, SourceType
from models.db_models import Dataset as DatasetModel

from api.models.db_models import Dataset, DatasetColumn, DatasetEmbedding, PipelineRun
from db.connection import get_db_connection, execute_query, execute_transaction

class DatasetRepository:
    """Repository for dataset-related database operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the repository with database and Redis connection."""
        self.redis = get_redis_client()
        self.cache_ttl = 3600  # Cache TTL in seconds
        self.session = session
        
    async def _get_cache_key(self, key_type: str, key_id: str) -> str:
        """Generate cache key."""
        return f"dataset:{key_type}:{key_id}"

    async def create_dataset(self, dataset: DatasetCreate, user_id: Optional[int] = None) -> Dataset:
        """Create a new dataset record."""
        query = """
        INSERT INTO datasets (
            name, description, file_type, source_type, source_info,
            status, user_id, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
        """
        
        now = datetime.utcnow()
        result = await execute_query(
            query,
            dataset.name,
            dataset.description,
            dataset.file_type,
            dataset.source_type,
            json.dumps(dataset.source_info) if dataset.source_info else None,
            dataset.status,
            user_id,
            now,
            now
        )
        
        return Dataset(**dict(result[0]))

    async def store_embeddings(self, dataset_id: int, embeddings: np.ndarray) -> None:
        db_embedding = DatasetEmbedding(
            dataset_id=dataset_id,
            embedding=embeddings.tolist()
        )
        async with get_db_session() as session:
            session.add(db_embedding)
            await session.flush()

    async def get_dataset(self, dataset_id: int) -> Optional[Dataset]:
        """Get a dataset by ID."""
        query = "SELECT * FROM datasets WHERE id = $1"
        result = await execute_query(query, dataset_id)
        return Dataset(**dict(result[0])) if result else None

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
        dataset_metadata: Optional[Dict[str, Any]] = None
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
                if dataset_metadata:
                    dataset["dataset_metadata"] = json.dumps({**json.loads(dataset["dataset_metadata"]), **dataset_metadata})
                await session.execute(
                    text("""
                    UPDATE datasets 
                    SET status = :status, dataset_metadata = :dataset_metadata
                    WHERE id = :dataset_id
                    """),
                    {
                        "status": dataset["status"],
                        "dataset_metadata": dataset["dataset_metadata"],
                        "dataset_id": dataset_id
                    }
                )
                await session.commit()

    async def add_dataset_columns(self, dataset_id: int, columns: List[Dict[str, Any]]) -> None:
        """Add columns to a dataset."""
        queries = []
        for col in columns:
            queries.append((
                """
                INSERT INTO dataset_columns (
                    dataset_id, name, data_type, nullable, stats
                ) VALUES ($1, $2, $3, $4, $5)
                """,
                dataset_id,
                col["name"],
                col["data_type"],
                col.get("nullable", True),
                json.dumps(col.get("stats", {}))
            ))
        
        await execute_transaction(queries)

    async def get_latest_pipeline_run(self, dataset_id: int) -> Optional[Dict[str, Any]]:
        """Get the latest pipeline run for a dataset."""
        query = """
        SELECT * FROM pipeline_runs 
        WHERE dataset_id = $1
        ORDER BY start_time DESC
        LIMIT 1
        """
        result = await execute_query(query, dataset_id)
        return dict(result[0]) if result else None

    async def update_dataset(self, dataset_id: int, update_data: Dict[str, Any]) -> Optional[Dataset]:
        """Update a dataset record."""
        # Build dynamic update query
        set_clauses = []
        values = []
        param_count = 1
        
        for key, value in update_data.items():
            if key == 'source_info' and value is not None:
                value = json.dumps(value)
            set_clauses.append(f"{key} = ${param_count}")
            values.append(value)
            param_count += 1
        
        # Add updated_at timestamp
        set_clauses.append("updated_at = $" + str(param_count))
        values.append(datetime.utcnow())
        
        query = f"""
        UPDATE datasets 
        SET {', '.join(set_clauses)}
        WHERE id = ${param_count + 1}
        RETURNING *
        """
        values.append(dataset_id)
        
        result = await execute_query(query, *values)
        return Dataset(**dict(result[0])) if result else None

    async def list_datasets(
        self,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        source_type: Optional[SourceType] = None
    ) -> List[Dataset]:
        """List datasets with optional filters."""
        query = "SELECT * FROM datasets WHERE 1=1"
        values = []
        param_count = 1
        
        if user_id is not None:
            query += f" AND user_id = ${param_count}"
            values.append(user_id)
            param_count += 1
            
        if source_type is not None:
            query += f" AND source_type = ${param_count}"
            values.append(source_type)
            param_count += 1
            
        query += f" ORDER BY created_at DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
        values.extend([limit, skip])
        
        result = await execute_query(query, *values)
        return [Dataset(**dict(row)) for row in result]

    async def delete_dataset(self, dataset_id: int) -> bool:
        """Delete a dataset record."""
        query = "DELETE FROM datasets WHERE id = $1 RETURNING id"
        result = await execute_query(query, dataset_id)
        return bool(result)
