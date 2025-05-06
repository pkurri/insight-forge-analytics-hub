"""
External Data Service for fetching data from APIs and databases
"""
import os
import json
import tempfile
import httpx
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio
import aiohttp
import asyncpg
import logging
from models.dataset import DatasetStatus, FileType
from repositories.dataset_repository import DatasetRepository

logger = logging.getLogger(__name__)

async def fetch_from_api(dataset_id: int, config: Dict[str, Any]) -> None:
    """Fetch data from an external API and save it to a file."""
    dataset_repo = DatasetRepository()
    
    try:
        # Update dataset status
        await dataset_repo.update_dataset(
            dataset_id,
            {"status": DatasetStatus.PROCESSING}
        )
        
        # Make API request
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=config.get("method", "GET"),
                url=config["url"],
                headers=config.get("headers", {}),
                json=config.get("body")
            ) as response:
                if response.status != 200:
                    raise Exception(f"API request failed with status {response.status}")
                    
                data = await response.json()
                
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Save to file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"api_data_{timestamp}.csv"
        file_path = os.path.join("uploads", filename)
        os.makedirs("uploads", exist_ok=True)
        
        df.to_csv(file_path, index=False)
        
        # Update dataset record
        await dataset_repo.update_dataset(
            dataset_id,
            {
                "status": DatasetStatus.COMPLETED,
                "metadata": {
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": df.columns.tolist(),
                    "file_path": file_path,
                    "file_type": FileType.CSV
                }
            }
        )
        
    except Exception as e:
        await dataset_repo.update_dataset(
            dataset_id,
            {
                "status": DatasetStatus.ERROR,
                "error_message": str(e)
            }
        )
        raise

async def fetch_from_database(dataset_id: int, config: Dict[str, Any]) -> None:
    """Fetch data from a database and save it to a file."""
    dataset_repo = DatasetRepository()
    
    try:
        # Update dataset status
        await dataset_repo.update_dataset(
            dataset_id,
            {"status": DatasetStatus.PROCESSING}
        )
        
        # Connect to database
        conn = await asyncpg.connect(
            host=config["host"],
            port=config["port"],
            user=config["username"],
            password=config["password"],
            database=config["database"]
        )
        
        try:
            # Execute query
            rows = await conn.fetch(config["query"])
            
            # Convert to DataFrame
            df = pd.DataFrame([dict(row) for row in rows])
            
            # Save to file
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"db_data_{timestamp}.csv"
            file_path = os.path.join("uploads", filename)
            os.makedirs("uploads", exist_ok=True)
            
            df.to_csv(file_path, index=False)
            
            # Update dataset record
            await dataset_repo.update_dataset(
                dataset_id,
                {
                    "status": DatasetStatus.COMPLETED,
                    "metadata": {
                        "row_count": len(df),
                        "column_count": len(df.columns),
                        "columns": df.columns.tolist(),
                        "file_path": file_path,
                        "file_type": FileType.CSV
                    }
                }
            )
            
        finally:
            await conn.close()
            
    except Exception as e:
        await dataset_repo.update_dataset(
            dataset_id,
            {
                "status": DatasetStatus.ERROR,
                "error_message": str(e)
            }
        )
        raise

# Sample function for getting database connection configuration
# In a real app, this would be retrieved from a secure storage
async def get_connection_config(connection_id: str) -> Dict[str, Any]:
    """Get database connection configuration."""
    # This is a mock implementation
    connections = {
        "postgres_main": {
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "username": "postgres",
            "password": "postgres",
            "database": "main_db"
        },
        "mysql_analytics": {
            "type": "mysql",
            "host": "localhost",
            "port": 3306,
            "username": "admin",
            "password": "password",
            "database": "analytics"
        },
        "mongodb_events": {
            "type": "mongodb",
            "host": "localhost",
            "port": 27017,
            "username": "admin",
            "password": "password",
            "database": "events"
        }
    }
    
    return connections.get(connection_id)
