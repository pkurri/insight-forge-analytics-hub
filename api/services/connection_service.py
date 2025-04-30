"""
Connection Service Module

This module handles API and database connections.
"""

import logging
import json
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import sqlalchemy
import requests
from sqlalchemy import create_engine
import psycopg2
import mysql.connector

from api.config.settings import get_settings
from api.repositories.dataset_repository import DatasetRepository
from api.services.pipeline_service import DataPipeline

settings = get_settings()
logger = logging.getLogger(__name__)
dataset_repo = DatasetRepository()
pipeline = DataPipeline()

class ConnectionService:
    """Service for managing API and database connections."""

    # --- API Connections ---
    async def list_api_connections(self, user_id: int) -> list:
        """List all API connections for a user."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text("SELECT * FROM api_connections WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )
                rows = result.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error listing API connections: {str(e)}")
            raise

    async def delete_api_connection(self, connection_id: int, user_id: int) -> dict:
        """Delete an API connection for a user."""
        try:
            async with get_db_session() as session:
                await session.execute(
                    text("DELETE FROM api_connections WHERE id = :id AND user_id = :user_id"),
                    {"id": connection_id, "user_id": user_id}
                )
                await session.commit()
                return {"success": True}
        except Exception as e:
            logger.error(f"Error deleting API connection: {str(e)}")
            return {"success": False, "error": str(e)}

    async def test_api_connection(self, connection_id: int, user_id: int) -> dict:
        """Test an API connection by making a sample request."""
        try:
            connection = await self.get_api_connection(connection_id)
            if not connection or connection.get("user_id") != user_id:
                return {"success": False, "status": "not found"}
            config = json.loads(connection["config"])
            url = config.get("url")
            if not url:
                return {"success": False, "status": "missing url"}
            # Basic GET request for test
            resp = requests.get(url, timeout=5)
            return {"success": resp.ok, "status": "ok" if resp.ok else "fail", "http_status": resp.status_code}
        except Exception as e:
            logger.error(f"Error testing API connection: {str(e)}")
            return {"success": False, "status": "error", "error": str(e)}

    # --- DB Connections ---
    async def list_db_connections(self, user_id: int) -> list:
        """List all DB connections for a user."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text("SELECT * FROM database_connections WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )
                rows = result.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error listing DB connections: {str(e)}")
            raise

    async def delete_db_connection(self, connection_id: int, user_id: int) -> dict:
        """Delete a DB connection for a user."""
        try:
            async with get_db_session() as session:
                await session.execute(
                    text("DELETE FROM database_connections WHERE id = :id AND user_id = :user_id"),
                    {"id": connection_id, "user_id": user_id}
                )
                await session.commit()
                return {"success": True}
        except Exception as e:
            logger.error(f"Error deleting DB connection: {str(e)}")
            return {"success": False, "error": str(e)}

    async def test_db_connection(self, connection_id: int, user_id: int) -> dict:
        """Test a DB connection by attempting to connect."""
        try:
            connection = await self.get_database_connection(connection_id)
            if not connection or connection.get("user_id") != user_id:
                return {"success": False, "status": "not found"}
            config = json.loads(connection["config"])
            db_type = connection["db_type"]
            if db_type == "postgresql":
                import psycopg2
                try:
                    conn = psycopg2.connect(
                        host=config["host"],
                        port=config["port"],
                        user=config["username"],
                        password=config["password"],
                        dbname=config["database"]
                    )
                    conn.close()
                    return {"success": True, "status": "ok"}
                except Exception as e:
                    return {"success": False, "status": "fail", "error": str(e)}
            elif db_type == "mysql":
                import mysql.connector
                try:
                    conn = mysql.connector.connect(
                        host=config["host"],
                        port=config["port"],
                        user=config["username"],
                        password=config["password"],
                        database=config["database"]
                    )
                    conn.close()
                    return {"success": True, "status": "ok"}
                except Exception as e:
                    return {"success": False, "status": "fail", "error": str(e)}
            else:
                return {"success": False, "status": f"unsupported db_type: {db_type}"}
        except Exception as e:
            logger.error(f"Error testing DB connection: {str(e)}")
            return {"success": False, "status": "error", "error": str(e)}

    async def create_api_connection(
        self,
        name: str,
        user_id: int,
        api_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new API connection.
        
        Args:
            name: Name of the connection
            user_id: ID of the user
            api_type: Type of API (e.g., 'rest', 'graphql')
            config: API configuration including auth details
            
        Returns:
            Created connection details
        """
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text("""
                    INSERT INTO api_connections 
                    (name, user_id, api_type, config)
                    VALUES (:name, :user_id, :api_type, :config)
                    RETURNING id
                    """),
                    {
                        "name": name,
                        "user_id": user_id,
                        "api_type": api_type,
                        "config": json.dumps(config)
                    }
                )
                connection_id = result.scalar_one()
                await session.commit()
                
                return await self.get_api_connection(connection_id)
                
        except Exception as e:
            logger.error(f"Error creating API connection: {str(e)}")
            raise
    
    async def create_database_connection(
        self,
        name: str,
        user_id: int,
        db_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new database connection.
        
        Args:
            name: Name of the connection
            user_id: ID of the user
            db_type: Type of database (e.g., 'postgresql', 'mysql')
            config: Database configuration including credentials
            
        Returns:
            Created connection details
        """
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text("""
                    INSERT INTO database_connections 
                    (name, user_id, db_type, config)
                    VALUES (:name, :user_id, :db_type, :config)
                    RETURNING id
                    """),
                    {
                        "name": name,
                        "user_id": user_id,
                        "db_type": db_type,
                        "config": json.dumps(config)
                    }
                )
                connection_id = result.scalar_one()
                await session.commit()
                
                return await self.get_database_connection(connection_id)
                
        except Exception as e:
            logger.error(f"Error creating database connection: {str(e)}")
            raise
    
    async def load_data_from_api(
        self,
        connection_id: int,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load data from an API endpoint.
        
        Args:
            connection_id: ID of the API connection
            endpoint: API endpoint to call
            params: Optional query parameters
            
        Returns:
            Dataset details after processing
        """
        try:
            # Get connection details
            connection = await self.get_api_connection(connection_id)
            if not connection:
                raise ValueError(f"API connection {connection_id} not found")
            
            config = json.loads(connection["config"])
            headers = config.get("headers", {})
            
            # Make API request
            response = requests.get(
                f"{config['base_url']}{endpoint}",
                params=params,
                headers=headers
            )
            response.raise_for_status()
            
            # Convert response to DataFrame
            data = response.json()
            df = pd.DataFrame(data)
            
            # Save to temporary CSV
            temp_path = f"/tmp/api_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(temp_path, index=False)
            
            # Create dataset
            dataset_data = {
                "name": f"API Data - {connection['name']}",
                "description": f"Data loaded from {endpoint}",
                "source_type": "api",
                "file_path": temp_path,
                "user_id": connection["user_id"],
                "metadata": {
                    "api_connection_id": connection_id,
                    "endpoint": endpoint,
                    "params": params
                }
            }
            
            # Process through pipeline
            dataset = await dataset_repo.create_dataset(dataset_data)
            await pipeline.process_dataset(dataset["id"])
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error loading data from API: {str(e)}")
            raise
    
    async def load_data_from_database(
        self,
        connection_id: int,
        query: str
    ) -> Dict[str, Any]:
        """
        Load data from a database query.
        
        Args:
            connection_id: ID of the database connection
            query: SQL query to execute
            
        Returns:
            Dataset details after processing
        """
        try:
            # Get connection details
            connection = await self.get_database_connection(connection_id)
            if not connection:
                raise ValueError(f"Database connection {connection_id} not found")
            
            config = json.loads(connection["config"])
            
            # Create SQLAlchemy engine
            if connection["db_type"] == "postgresql":
                engine = create_engine(
                    f"postgresql://{config['user']}:{config['password']}@"
                    f"{config['host']}:{config['port']}/{config['database']}"
                )
            elif connection["db_type"] == "mysql":
                engine = create_engine(
                    f"mysql+mysqlconnector://{config['user']}:{config['password']}@"
                    f"{config['host']}:{config['port']}/{config['database']}"
                )
            else:
                raise ValueError(f"Unsupported database type: {connection['db_type']}")
            
            # Execute query
            df = pd.read_sql(query, engine)
            
            # Save to temporary CSV
            temp_path = f"/tmp/db_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(temp_path, index=False)
            
            # Create dataset
            dataset_data = {
                "name": f"Database Data - {connection['name']}",
                "description": f"Data loaded from database query",
                "source_type": "database",
                "file_path": temp_path,
                "user_id": connection["user_id"],
                "metadata": {
                    "database_connection_id": connection_id,
                    "query": query
                }
            }
            
            # Process through pipeline
            dataset = await dataset_repo.create_dataset(dataset_data)
            await pipeline.process_dataset(dataset["id"])
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error loading data from database: {str(e)}")
            raise
    
    async def get_api_connection(self, connection_id: int) -> Optional[Dict[str, Any]]:
        """Get API connection details."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text("""
                    SELECT * FROM api_connections 
                    WHERE id = :connection_id
                    """),
                    {"connection_id": connection_id}
                )
                row = result.first()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Error getting API connection: {str(e)}")
            raise
    
    async def get_database_connection(self, connection_id: int) -> Optional[Dict[str, Any]]:
        """Get database connection details."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text("""
                    SELECT * FROM database_connections 
                    WHERE id = :connection_id
                    """),
                    {"connection_id": connection_id}
                )
                row = result.first()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Error getting database connection: {str(e)}")
            raise
