"""
Chat Router Module

This module defines API routes for AI chat functionality.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

from services.chat_service import (
    get_chat_sessions,
    get_chat_session,
    create_chat_session,
    delete_chat_session,
    send_message
)
from repositories.chat_repository import get_chat_repository_user_or_api_key

router = APIRouter()

# Request/Response models
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: str

class ChatSession(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[ChatMessage]

class ChatSessionCreate(BaseModel):
    title: str

class ChatCompletionRequest(BaseModel):
    session_id: str
    message: str
    context: Optional[Dict[str, Any]] = None

@router.get("/sessions")
async def list_chat_sessions(
    current_user = Depends(get_current_user_or_api_key)
):
    """Get all chat sessions for the current user."""
    try:
        sessions = await get_chat_sessions(current_user.id)
        return {"success": True, "data": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user = Depends(get_current_user_or_api_key)
):
    """Get a specific chat session by ID."""
    try:
        session = await get_chat_session(session_id, current_user.id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return {"success": True, "data": session}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions")
async def create_session(
    session: ChatSessionCreate,
    current_user = Depends(get_current_user_or_api_key)
):
    """Create a new chat session."""
    try:
        new_session = await create_chat_session(session.title, current_user.id)
        return {"success": True, "data": new_session}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user = Depends(get_current_user_or_api_key)
):
    """Delete a chat session."""
    try:
        await delete_chat_session(session_id, current_user.id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/completion")
async def chat_completion(
    request: ChatCompletionRequest,
    current_user = Depends(get_current_user_or_api_key)
):
    """Send a message and get AI completion."""
    try:
        response = await send_message(request.session_id, request.message, request.context, current_user.id)
        return {"success": True, "data": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
