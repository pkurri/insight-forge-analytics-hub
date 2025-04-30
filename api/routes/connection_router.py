"""
Connection Router for managing API and database connections.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from api.services.connection_service import ConnectionService

router = APIRouter(prefix="/datasource", tags=["datasource"])
service = ConnectionService()

# API Connections
# API Connections
@router.get("/api", response_model=List[Dict[str, Any]])
async def list_api_connections():
    # For demo, user_id=1; in real use, get from auth/session
    return await service.list_api_connections(user_id=1)

@router.get("/api/{connection_id}", response_model=Dict[str, Any])
async def get_api_connection(connection_id: int):
    return await service.get_api_connection(connection_id)

@router.post("/api", response_model=Dict[str, Any])
async def create_api_connection(payload: Dict[str, Any]):
    return await service.create_api_connection(**payload)

@router.put("/api/{connection_id}", response_model=Dict[str, Any])
async def update_api_connection(connection_id: int, payload: Dict[str, Any]):
    # Not implemented in service, placeholder for future
    return {"success": False, "error": "Update not implemented"}

@router.delete("/api/{connection_id}", response_model=Dict[str, Any])
async def delete_api_connection(connection_id: int):
    return await service.delete_api_connection(connection_id, user_id=1)

@router.post("/api/test", response_model=Dict[str, Any])
async def test_api_connection_post(payload: Dict[str, Any]):
    # Accepts full connection object for testing
    # Not implemented in service, placeholder for future
    return {"success": False, "error": "Test by object not implemented"}

@router.post("/api/{connection_id}/test", response_model=Dict[str, Any])
async def test_api_connection(connection_id: int):
    return await service.test_api_connection(connection_id, user_id=1)

# DB Connections
@router.get("/db", response_model=List[Dict[str, Any]])
async def list_db_connections():
    return await service.list_db_connections(user_id=1)

@router.get("/db/{connection_id}", response_model=Dict[str, Any])
async def get_db_connection(connection_id: int):
    return await service.get_database_connection(connection_id)

@router.post("/db", response_model=Dict[str, Any])
async def create_db_connection(payload: Dict[str, Any]):
    return await service.create_database_connection(**payload)

@router.put("/db/{connection_id}", response_model=Dict[str, Any])
async def update_db_connection(connection_id: int, payload: Dict[str, Any]):
    # Not implemented in service, placeholder for future
    return {"success": False, "error": "Update not implemented"}

@router.delete("/db/{connection_id}", response_model=Dict[str, Any])
async def delete_db_connection(connection_id: int):
    return await service.delete_db_connection(connection_id, user_id=1)

@router.post("/db/test", response_model=Dict[str, Any])
async def test_db_connection_post(payload: Dict[str, Any]):
    # Accepts full connection object for testing
    # Not implemented in service, placeholder for future
    return {"success": False, "error": "Test by object not implemented"}

@router.post("/db/{connection_id}/test", response_model=Dict[str, Any])
async def test_db_connection(connection_id: int):
    return await service.test_db_connection(connection_id, user_id=1)
