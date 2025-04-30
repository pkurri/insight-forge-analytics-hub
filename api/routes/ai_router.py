from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
import json
import asyncio

# Import services
from ..services.ai_agent_service import (
    get_available_models,
    get_available_agents,
    generate_embeddings,
    get_agent_response,
    get_chat_suggestions,
    get_streaming_response
)
from ..services.openevals_service import openevals_service
from ..services.conversation_memory import conversation_memory

# Create router
router = APIRouter(prefix="/ai", tags=["AI"])

# Models
class EmbeddingRequest(BaseModel):
    text: str
    model: Optional[str] = None

class ChatRequest(BaseModel):
    query: str
    model_id: Optional[str] = None
    agent_type: Optional[str] = None
    dataset_id: Optional[str] = None
    chat_history: Optional[List[Dict[str, Any]]] = None
    context: Optional[Dict[str, Any]] = None

class StreamingChatRequest(BaseModel):
    query: str
    model_id: Optional[str] = None
    agent_type: Optional[str] = None
    dataset_id: Optional[str] = None
    chat_history: Optional[List[Dict[str, Any]]] = None
    context: Optional[Dict[str, Any]] = None

class SuggestionsRequest(BaseModel):
    dataset_id: Optional[str] = None
    category: Optional[str] = None

class EvaluateResponseRequest(BaseModel):
    query: str
    response: str
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    facts: Optional[List[Dict[str, Any]]] = None

class ImproveResponseRequest(BaseModel):
    query: str
    initial_response: str
    conversation_id: Optional[str] = None
    evaluation_id: Optional[str] = None
    
class UserFeedbackRequest(BaseModel):
    conversation_id: str
    message_id: str
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = None
    improvement_areas: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    
class InsightsEvaluationRequest(BaseModel):
    conversation_id: str
    insights: List[str]

# Routes

@router.get("/allowed-models")
async def get_allowed_models():
    """
    Get allowed embedding and text generation models for UI validation.
    """
    from api.config.settings import get_settings
    settings = get_settings()
    return {
        "success": True,
        "allowed_embedding_models": settings.ALLOWED_EMBEDDING_MODELS,
        "allowed_text_gen_models": settings.ALLOWED_TEXT_GEN_MODELS
    }
@router.get("/models")
async def get_models():
    """
    Get available AI models
    """
    models = await get_available_models()
    return {"success": True, "data": models}

@router.get("/agents")
async def get_agents():
    """
    Get available agent types
    """
    agents = await get_available_agents()
    return {"success": True, "data": agents}

@router.post("/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    """
    Generate embeddings for text
    """
    try:
        result = await generate_embeddings(request.text, request.model)
        return {"success": True, "data": result}
    except ValueError as e:
        return {"success": False, "error": str(e), "status": 400}
    except HTTPException as e:
        return {"success": False, "error": e.detail, "status": e.status_code}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Get a response from an AI agent
    """
    try:
        result = await get_agent_response(
            query=request.query,
            agent_type=request.agent_type,
            model_id=request.model_id,
            dataset_id=request.dataset_id,
            chat_history=request.chat_history,
            context=request.context
        )
        return {"success": True, "data": result}
    except ValueError as e:
        return {"success": False, "error": str(e), "status": 400}
    except HTTPException as e:
        return {"success": False, "error": e.detail, "status": e.status_code}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/chat/stream")
async def stream_chat(request: StreamingChatRequest):
    """
    Get a streaming response from an AI agent
    """
    try:
        # Create generator function for streaming response
        async def response_generator():
            async for chunk in get_streaming_response(request.dict()):
                yield f"data: {chunk}\n\n"
        
        return StreamingResponse(
            response_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        # Return error as SSE event
        async def error_generator():
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream"
        )

@router.post("/suggestions")
async def get_suggestions(request: SuggestionsRequest):
    """
    Get suggested chat queries
    """
    try:
        suggestions = await get_chat_suggestions(
            dataset_id=request.dataset_id,
            category=request.category
        )
        return {"success": True, "data": suggestions}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/evaluate")
async def evaluate_response(request: EvaluateResponseRequest):
    """
    Evaluate an AI agent's response for accuracy and consistency
    """
    try:
        result = await openevals_service.evaluate_agent_response(
            query=request.query,
            response=request.response,
            facts=request.facts,
            conversation_id=request.conversation_id,
            message_id=request.message_id
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/improve-response")
async def improve_response(request: ImproveResponseRequest):
    """
    Generate an improved response based on evaluation feedback
    """
    try:
        # Get evaluation if evaluation_id is provided
        evaluation = None
        if request.evaluation_id:
            evaluation = await openevals_service.get_evaluation(request.evaluation_id)
            
        result = await openevals_service.get_improved_response(
            query=request.query,
            initial_response=request.initial_response,
            conversation_id=request.conversation_id,
            evaluation=evaluation
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/user-feedback")
async def process_user_feedback(request: UserFeedbackRequest):
    """
    Process user feedback and add to continuous learning system
    """
    try:
        # Format feedback for processing
        feedback = {
            "rating": request.rating,
            "feedback_text": request.feedback_text,
            "improvement_areas": request.improvement_areas,
            "tags": request.tags
        }
        
        result = await openevals_service.process_continuous_learning(
            conversation_id=request.conversation_id,
            message_id=request.message_id,
            user_feedback=feedback
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/evaluate-insights")
async def evaluate_insights(request: InsightsEvaluationRequest):
    """
    Evaluate the quality and usefulness of insights generated in a conversation
    """
    try:
        result = await openevals_service.evaluate_conversation_insights(
            conversation_id=request.conversation_id,
            insights=request.insights
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
