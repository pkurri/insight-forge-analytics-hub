
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
import json
import asyncio
import logging
from fastapi.responses import JSONResponse

# Configure logging
logger = logging.getLogger("ai_router")

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

# Helper function to handle exceptions consistently
async def handle_request(func, *args, **kwargs):
    try:
        result = await func(*args, **kwargs)
        return {"success": True, "data": result}
    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}", exc_info=True)
        return JSONResponse(
            status_code=e.status_code,
            content={"success": False, "error": e.detail}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}

# Routes
@router.get("/models")
async def get_models():
    """
    Get available AI models
    """
    return await handle_request(get_available_models)

@router.get("/agents")
async def get_agents():
    """
    Get available agent types
    """
    return await handle_request(get_available_agents)

@router.post("/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    """
    Generate embeddings for text
    """
    return await handle_request(generate_embeddings, request.text, request.model)

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Get a response from an AI agent
    """
    return await handle_request(
        get_agent_response,
        query=request.query,
        agent_type=request.agent_type,
        model_id=request.model_id,
        dataset_id=request.dataset_id,
        chat_history=request.chat_history,
        context=request.context
    )

@router.post("/chat/stream")
async def stream_chat(request: StreamingChatRequest):
    """
    Get a streaming response from an AI agent
    """
    try:
        # Create generator function for streaming response
        async def response_generator():
            try:
                async for chunk in get_streaming_response(request.dict()):
                    yield f"data: {chunk}\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            response_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Stream setup error: {str(e)}", exc_info=True)
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
    return await handle_request(
        get_chat_suggestions,
        dataset_id=request.dataset_id,
        category=request.category
    )

@router.post("/evaluate")
async def evaluate_response(request: EvaluateResponseRequest):
    """
    Evaluate an AI agent's response for accuracy and consistency
    """
    return await handle_request(
        openevals_service.evaluate_agent_response,
        query=request.query,
        response=request.response,
        facts=request.facts,
        conversation_id=request.conversation_id,
        message_id=request.message_id
    )

@router.post("/improve-response")
async def improve_response(request: ImproveResponseRequest):
    """
    Generate an improved response based on evaluation feedback
    """
    # Get evaluation if evaluation_id is provided
    evaluation = None
    if request.evaluation_id:
        evaluation = await openevals_service.get_evaluation(request.evaluation_id)
        
    return await handle_request(
        openevals_service.get_improved_response,
        query=request.query,
        initial_response=request.initial_response,
        conversation_id=request.conversation_id,
        evaluation=evaluation
    )

@router.post("/user-feedback")
async def process_user_feedback(request: UserFeedbackRequest):
    """
    Process user feedback and add to continuous learning system
    """
    # Format feedback for processing
    feedback = {
        "rating": request.rating,
        "feedback_text": request.feedback_text,
        "improvement_areas": request.improvement_areas,
        "tags": request.tags
    }
    
    return await handle_request(
        openevals_service.process_continuous_learning,
        conversation_id=request.conversation_id,
        message_id=request.message_id,
        user_feedback=feedback
    )

@router.post("/evaluate-insights")
async def evaluate_insights(request: InsightsEvaluationRequest):
    """
    Evaluate the quality and usefulness of insights generated in a conversation
    """
    return await handle_request(
        openevals_service.evaluate_conversation_insights,
        conversation_id=request.conversation_id,
        insights=request.insights
    )

@router.get("/health")
async def health_check():
    """
    Health check endpoint for AI services
    """
    return {"status": "ok", "service": "ai_router", "timestamp": str(asyncio.get_event_loop().time())}
