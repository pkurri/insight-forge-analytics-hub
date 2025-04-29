
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

async def fetch_from_api(
    dataset_id: int, 
    api_endpoint: str, 
    output_format: str, 
    auth_config: Dict[str, Any],
    dataset_repo
):
    """
    Fetch data from an external API and save it for pipeline processing
    """
    try:
        # Prepare headers based on auth config
        headers = {}
        if auth_config.get("type") == "bearer":
            headers["Authorization"] = f"Bearer {auth_config.get('token')}"
        elif auth_config.get("type") == "api_key":
            headers[auth_config.get("key_name", "X-API-Key")] = auth_config.get("key")
        elif auth_config.get("type") == "basic":
            import base64
            auth_string = f"{auth_config.get('username')}:{auth_config.get('password')}"
            encoded = base64.b64encode(auth_string.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        
        # Add any additional headers
        if auth_config.get("additional_headers"):
            headers.update(auth_config.get("additional_headers"))
        
        # Make the API request
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=auth_config.get("method", "GET"),
                url=api_endpoint,
                headers=headers,
                timeout=auth_config.get("timeout", 30)
            )
            response.raise_for_status()
        
        # Create directory for dataset files if it doesn't exist
        upload_dir = os.getenv("UPLOAD_DIR", "/tmp/uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Parse the response based on expected format
        if response.headers.get("content-type", "").startswith("application/json"):
            data = response.json()
            
            # Handle array vs object responses
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Check if there's a results/data/items key that contains the array
                for key in ["data", "results", "items", "records"]:
                    if key in data and isinstance(data[key], list):
                        df = pd.DataFrame(data[key])
                        break
                else:
                    # If no array found, convert the single object to a dataframe
                    df = pd.DataFrame([data])
            else:
                raise ValueError(f"Unexpected JSON structure: {type(data)}")
        
        elif response.headers.get("content-type", "").startswith("text/csv"):
            import io
            df = pd.read_csv(io.StringIO(response.text))
        
        else:
            # Default to JSON parsing
            try:
                data = response.json()
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame([data])
            except Exception:
                raise ValueError(f"Unsupported content type: {response.headers.get('content-type')}")
        
        # Save the data in the requested format
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = os.path.join(upload_dir, f"api_data_{dataset_id}_{timestamp}.{output_format}")
        
        if output_format == "csv":
            df.to_csv(file_path, index=False)
        elif output_format == "json":
            df.to_json(file_path, orient="records")
        elif output_format == "excel":
            df.to_excel(file_path, index=False)
        else:
            # Default to CSV
            df.to_csv(file_path, index=False)
        
        # Update the dataset with file info and record count
        await dataset_repo.update_dataset_file_info(
            dataset_id=dataset_id,
            file_path=file_path,
            record_count=len(df),
            column_count=len(df.columns),
            status="ready"
        )
        
        return {
            "dataset_id": dataset_id,
            "record_count": len(df),
            "column_count": len(df.columns),
            "file_path": file_path
        }
    
    except Exception as e:
        # Update the dataset status to error
        await dataset_repo.update_dataset_status(
            dataset_id=dataset_id,
            status="error",
            error_message=str(e)
        )
        raise

async def fetch_from_database(
    dataset_id: int,
    connection_id: str,
    query: Optional[str],
    table_name: Optional[str],
    output_format: str,
    dataset_repo
):
    """
    Fetch data from a database and save it for pipeline processing
    """
    try:
        # Get database connection details
        # In a real application, this would fetch from a connection store
        from services.db_connection_service import get_connection_config
        
        connection_config = await get_connection_config(connection_id)
        if not connection_config:
            raise ValueError(f"Database connection with ID '{connection_id}' not found")
        
        # Import appropriate database connector based on the connection type
        if connection_config["type"] == "postgresql":
            import asyncpg
            
            # Connect to the database
            conn = await asyncpg.connect(
                host=connection_config["host"],
                port=connection_config["port"],
                user=connection_config["username"],
                password=connection_config["password"],
                database=connection_config["database"]
            )
            
            # Execute query or fetch table data
            if query:
                result = await conn.fetch(query)
                columns = result[0].keys() if result else []
                rows = [dict(row) for row in result]
            else:
                # Fetch all from table
                result = await conn.fetch(f"SELECT * FROM {table_name}")
                columns = result[0].keys() if result else []
                rows = [dict(row) for row in result]
            
            await conn.close()
        
        elif connection_config["type"] == "mysql":
            import aiomysql
            
            # Connect to the database
            conn = await aiomysql.connect(
                host=connection_config["host"],
                port=connection_config["port"],
                user=connection_config["username"],
                password=connection_config["password"],
                db=connection_config["database"]
            )
            
            # Execute query or fetch table data
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                if query:
                    await cursor.execute(query)
                else:
                    await cursor.execute(f"SELECT * FROM {table_name}")
                
                result = await cursor.fetchall()
                columns = result[0].keys() if result else []
                rows = result
            
            conn.close()
        
        else:
            # Mock data for demonstration or unsupported DB types
            await asyncio.sleep(2)  # Simulate DB query time
            columns = ["id", "name", "value", "created_at"]
            rows = [
                {"id": 1, "name": "Item 1", "value": 100, "created_at": datetime.utcnow().isoformat()},
                {"id": 2, "name": "Item 2", "value": 200, "created_at": datetime.utcnow().isoformat()},
                {"id": 3, "name": "Item 3", "value": 300, "created_at": datetime.utcnow().isoformat()}
            ]
        
        # Create a DataFrame from the results
        df = pd.DataFrame(rows)
        
        # Create directory for dataset files if it doesn't exist
        upload_dir = os.getenv("UPLOAD_DIR", "/tmp/uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the data in the requested format
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = os.path.join(upload_dir, f"db_data_{dataset_id}_{timestamp}.{output_format}")
        
        if output_format == "csv":
            df.to_csv(file_path, index=False)
        elif output_format == "json":
            df.to_json(file_path, orient="records")
        elif output_format == "excel":
            df.to_excel(file_path, index=False)
        else:
            # Default to CSV
            df.to_csv(file_path, index=False)
        
        # Update the dataset with file info and record count
        await dataset_repo.update_dataset_file_info(
            dataset_id=dataset_id,
            file_path=file_path,
            record_count=len(df),
            column_count=len(df.columns),
            status="ready"
        )
        
        return {
            "dataset_id": dataset_id,
            "record_count": len(df),
            "column_count": len(df.columns),
            "file_path": file_path
        }
    
    except Exception as e:
        # Update the dataset status to error
        await dataset_repo.update_dataset_status(
            dataset_id=dataset_id,
            status="error",
            error_message=str(e)
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
