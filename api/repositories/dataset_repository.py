from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np
import json
import os
from api.config.redis_config import get_redis_client
from api.services.analytics_service import (
    process_dataset,
    cleaning_metadata,
    detect_anomalies,
    get_data_profile
)
from models.dataset import Dataset, DatasetCreate, DatasetStatus, SourceType
from db.connection import (
    get_db_connection, 
    execute_query, 
    execute_transaction,
    execute_single,
    execute_value,
    execute_command,
    execute_many
)

class DatasetRepository:
    """Repository for dataset-related database operations."""
    
    def __init__(self):
        """Initialize the repository with Redis connection."""
        self.redis = get_redis_client()
        self.cache_ttl = 3600  # Cache TTL in seconds
        self.data_cache = {}  # In-memory cache for dataset data
        
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
        """Store embeddings for a dataset."""
        query = """
        INSERT INTO dataset_embeddings (dataset_id, embedding)
        VALUES ($1, $2)
        """
        await execute_command(query, dataset_id, embeddings.tolist())

    async def get_dataset(self, dataset_id: int) -> Optional[Dataset]:
        """Get a dataset by ID."""
        query = "SELECT * FROM datasets WHERE id = $1"
        result = await execute_query(query, dataset_id)
        return Dataset(**dict(result[0])) if result else None

    async def get_datasets_by_user(self, user_id: int) -> List[Dataset]:
        """Get all datasets for a user."""
        query = "SELECT * FROM datasets WHERE user_id = $1"
        result = await execute_query(query, user_id)
        return [Dataset(**dict(row)) for row in result]

    async def search_similar_datasets(
        self,
        query_embedding: np.ndarray,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar datasets using vector similarity."""
        query = """
        SELECT 
            d.*,
            e.embedding <=> $1 as similarity
        FROM datasets d
        JOIN dataset_embeddings e ON d.id = e.dataset_id
        ORDER BY similarity ASC
        LIMIT $2
        """
        result = await execute_query(query, query_embedding.tolist(), limit)
        return [dict(row) for row in result]

    async def update_dataset_status(
        self,
        dataset_id: int,
        status: DatasetStatus,
        dataset_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update the status and metadata of a dataset."""
        # First get the current dataset
        query = "SELECT * FROM datasets WHERE id = $1"
        result = await execute_single(query, dataset_id)
        
        if result:
            dataset = dict(result)
            dataset["status"] = status.value
            
            # Update metadata if provided
            if dataset_metadata:
                current_metadata = json.loads(dataset.get("dataset_metadata", "{}"))
                updated_metadata = {**current_metadata, **dataset_metadata}
                dataset["dataset_metadata"] = json.dumps(updated_metadata)
            
            # Update the dataset
            update_query = """
            UPDATE datasets 
            SET status = $1, dataset_metadata = $2, updated_at = $3
            WHERE id = $4
            """
            await execute_command(
                update_query,
                dataset["status"],
                dataset.get("dataset_metadata", "{}"),
                datetime.utcnow(),
                dataset_id
            )

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
    
    async def get_dataset_data(self, dataset_id: int) -> List[Dict[str, Any]]:
        """Get dataset data from in-memory cache or database."""
        # Check if data is in memory cache
        cache_key = f"data:{dataset_id}"
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        
        # If not in cache, try to load from database or file
        # This is a placeholder for actual database retrieval
        # In our new approach, we'll load from file instead
        return None
    
    async def get_transformed_data(self, dataset_id: int) -> List[Dict[str, Any]]:
        """Get transformed dataset data from in-memory cache."""
        cache_key = f"transformed_data:{dataset_id}"
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        return None
    
    async def get_enriched_data(self, dataset_id: int) -> List[Dict[str, Any]]:
        """Get enriched dataset data from in-memory cache."""
        cache_key = f"enriched_data:{dataset_id}"
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        return None
    
    async def save_transformed_data(self, dataset_id: int, data: List[Dict[str, Any]]) -> bool:
        """Save transformed dataset data to in-memory cache."""
        cache_key = f"transformed_data:{dataset_id}"
        self.data_cache[cache_key] = data
        
        # Also save to a file in the temp directory for persistence
        dataset = await self.get_dataset(dataset_id)
        if dataset and hasattr(dataset, 'metadata') and dataset.metadata:
            metadata = dataset.metadata if isinstance(dataset.metadata, dict) else {}
            file_path = metadata.get('file_path')
            
            if file_path:
                # Create a transformed data file path
                dir_path = os.path.dirname(file_path)
                file_name = os.path.basename(file_path)
                name, ext = os.path.splitext(file_name)
                transformed_file_path = os.path.join(dir_path, f"{name}_transformed{ext}")
                
                # Save the data to the file
                try:
                    if ext.lower() == '.csv':
                        pd.DataFrame(data).to_csv(transformed_file_path, index=False)
                    elif ext.lower() in ['.xlsx', '.xls']:
                        pd.DataFrame(data).to_excel(transformed_file_path, index=False)
                    elif ext.lower() == '.json':
                        with open(transformed_file_path, 'w') as f:
                            json.dump(data, f)
                    
                    # Update metadata with transformed file path
                    metadata['transformed_file_path'] = transformed_file_path
                    await self.update_dataset_metadata(dataset_id, metadata)
                    return True
                except Exception as e:
                    print(f"Error saving transformed data to file: {str(e)}")
        
        return False
    
    async def save_enriched_data(self, dataset_id: int, data: List[Dict[str, Any]]) -> bool:
        """Save enriched dataset data to in-memory cache."""
        cache_key = f"enriched_data:{dataset_id}"
        self.data_cache[cache_key] = data
        
        # Also save to a file in the temp directory for persistence
        dataset = await self.get_dataset(dataset_id)
        if dataset and hasattr(dataset, 'metadata') and dataset.metadata:
            metadata = dataset.metadata if isinstance(dataset.metadata, dict) else {}
            file_path = metadata.get('file_path')
            
            if file_path:
                # Create an enriched data file path
                dir_path = os.path.dirname(file_path)
                file_name = os.path.basename(file_path)
                name, ext = os.path.splitext(file_name)
                enriched_file_path = os.path.join(dir_path, f"{name}_enriched{ext}")
                
                # Save the data to the file
                try:
                    if ext.lower() == '.csv':
                        pd.DataFrame(data).to_csv(enriched_file_path, index=False)
                    elif ext.lower() in ['.xlsx', '.xls']:
                        pd.DataFrame(data).to_excel(enriched_file_path, index=False)
                    elif ext.lower() == '.json':
                        with open(enriched_file_path, 'w') as f:
                            json.dump(data, f)
                    
                    # Update metadata with enriched file path
                    metadata['enriched_file_path'] = enriched_file_path
                    await self.update_dataset_metadata(dataset_id, metadata)
                    return True
                except Exception as e:
                    print(f"Error saving enriched data to file: {str(e)}")
        
        return False
    
    async def get_embeddings(self, dataset_id: int) -> List[Dict[str, Any]]:
        """Get embeddings for a dataset from in-memory cache."""
        cache_key = f"embeddings:{dataset_id}"
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        return None
    
    async def save_embeddings(self, dataset_id: int, embeddings: List[Dict[str, Any]]) -> bool:
        """Save embeddings for a dataset to in-memory cache."""
        cache_key = f"embeddings:{dataset_id}"
        self.data_cache[cache_key] = embeddings
        
        # Also save to a file in the temp directory for persistence
        dataset = await self.get_dataset(dataset_id)
        if dataset and hasattr(dataset, 'metadata') and dataset.metadata:
            metadata = dataset.metadata if isinstance(dataset.metadata, dict) else {}
            file_path = metadata.get('file_path')
            
            if file_path:
                # Create an embeddings file path
                dir_path = os.path.dirname(file_path)
                file_name = os.path.basename(file_path)
                name, ext = os.path.splitext(file_name)
                embeddings_file_path = os.path.join(dir_path, f"{name}_embeddings.json")
                
                # Save the embeddings to the file
                try:
                    with open(embeddings_file_path, 'w') as f:
                        json.dump(embeddings, f)
                    
                    # Update metadata with embeddings file path
                    metadata['embeddings_file_path'] = embeddings_file_path
                    await self.update_dataset_metadata(dataset_id, metadata)
                    return True
                except Exception as e:
                    print(f"Error saving embeddings to file: {str(e)}")
        
        return False
    
    async def save_insights(self, dataset_id: int, insights: List[Dict[str, Any]]) -> bool:
        """Save insights for a dataset."""
        cache_key = f"insights:{dataset_id}"
        self.data_cache[cache_key] = insights
        
        # Also save to a file in the temp directory for persistence
        dataset = await self.get_dataset(dataset_id)
        if dataset and hasattr(dataset, 'metadata') and dataset.metadata:
            metadata = dataset.metadata if isinstance(dataset.metadata, dict) else {}
            file_path = metadata.get('file_path')
            
            if file_path:
                # Create an insights file path
                dir_path = os.path.dirname(file_path)
                file_name = os.path.basename(file_path)
                name, ext = os.path.splitext(file_name)
                insights_file_path = os.path.join(dir_path, f"{name}_insights.json")
                
                # Save the insights to the file
                try:
                    with open(insights_file_path, 'w') as f:
                        json.dump(insights, f)
                    
                    # Update metadata with insights file path
                    metadata['insights_file_path'] = insights_file_path
                    await self.update_dataset_metadata(dataset_id, metadata)
                    return True
                except Exception as e:
                    print(f"Error saving insights to file: {str(e)}")
        
        return False
