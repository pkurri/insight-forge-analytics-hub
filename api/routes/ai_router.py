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
    generate_embeddings as ai_service_generate_embeddings,
    get_agent_response,
    get_chat_suggestions,
    get_streaming_response
)
from ..services.openevals_service import openevals_service
from ..services.conversation_memory import conversation_memory
from ..services.vector_embedding_api import vector_embedding_api, EMBEDDING_MODELS, TEXT_GEN_MODELS
from ..services.vector_service import vector_service

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
    use_all_datasets: Optional[bool] = False

class StreamingChatRequest(BaseModel):
    query: str
    model_id: Optional[str] = None
    agent_type: Optional[str] = None
    dataset_id: Optional[str] = None
    chat_history: Optional[List[Dict[str, Any]]] = None
    context: Optional[Dict[str, Any]] = None
    use_all_datasets: Optional[bool] = False

class DatasetListResponse(BaseModel):
    id: str
    name: str
    record_count: int
    column_count: int
    vectorized: bool
    embedding_model: Optional[str] = None
    last_updated: str

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
    # Convert embedding models dictionary to list format for frontend
    embedding_models = []
    for model_id, model_info in EMBEDDING_MODELS.items():
        embedding_models.append({
            "id": model_id,
            "name": model_info.get("name", model_id),
            "provider": model_info.get("provider", "huggingface"),
            "dimensions": model_info.get("dimensions", 384),
            "description": model_info.get("description", "Embedding model"),
            "type": "embedding"
        })
    
    # Convert text generation models dictionary to list format for frontend
    text_gen_models = []
    for model_id, model_info in TEXT_GEN_MODELS.items():
        text_gen_models.append({
            "id": model_id,
            "name": model_info.get("name", model_id),
            "provider": model_info.get("provider", "internal"),
            "max_tokens": model_info.get("max_tokens", 4096),
            "description": model_info.get("description", "Text generation model"),
            "type": "text_generation"
        })
    
    # Get allowed model IDs from settings
    from api.config.settings import get_settings
    settings = get_settings()
    
    return {
        "success": True,
        "models": embedding_models + text_gen_models,
        "allowed_embedding_models": list(EMBEDDING_MODELS.keys()),
        "allowed_text_gen_models": list(TEXT_GEN_MODELS.keys())
    }
@router.get("/vectorized-datasets")
async def get_vectorized_datasets():
    """
    Get a list of datasets that have been vectorized and can be used for semantic search
    
    This endpoint returns datasets that have vector embeddings available for use with the chat interface.
    The response includes metadata about each dataset, including the embedding model used.
    """
    try:
        # Get database connection
        from api.db.connection import get_db_pool
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Query for datasets that have been vectorized
            rows = await conn.fetch(
                """
                SELECT d.id, d.name, d.row_count, d.column_count, d.vectorized, 
                       d.vectorized_at, d.metadata, d.updated_at
                FROM datasets d
                WHERE d.vectorized = TRUE
                ORDER BY d.updated_at DESC
                """
            )
            
            datasets = []
            for row in rows:
                # Extract embedding model from metadata if available
                embedding_model = None
                if row['metadata']:
                    metadata = row['metadata']
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                            embedding_model = metadata.get('embedding_model')
                        except json.JSONDecodeError:
                            pass
                    elif isinstance(metadata, dict):
                        embedding_model = metadata.get('embedding_model')
                
                datasets.append({
                    "id": str(row['id']),
                    "name": row['name'],
                    "record_count": row['row_count'] or 0,
                    "column_count": row['column_count'] or 0,
                    "vectorized": row['vectorized'] or False,
                    "embedding_model": embedding_model,
                    "last_updated": row['updated_at'].isoformat() if row['updated_at'] else None
                })
            
            return {"success": True, "data": datasets}
    except Exception as e:
        return {"success": False, "error": str(e)}

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
    Generate embeddings for text using the specified model
    
    This endpoint supports all allowed embedding models and integrates with the vector database.
    The embedding is generated using the vector_embedding_api service, which provides optimized
    performance for large datasets and supports batch processing.
    """
    try:
        # Check if the model is allowed
        if request.model and request.model not in EMBEDDING_MODELS:
            return {
                "success": False, 
                "error": f"Model {request.model} is not allowed. Allowed models: {list(EMBEDDING_MODELS.keys())}",
                "status": 400
            }
        
        # Use the vector_embedding_api service for generating embeddings
        result = await vector_embedding_api.generate_embeddings(
            texts=request.text,
            model_id=request.model
        )
        
        if not result["success"]:
            # Fallback to the ai_service if vector_embedding_api fails
            legacy_result = await ai_service_generate_embeddings(request.text, request.model)
            return {"success": True, "data": legacy_result}
        
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
    Get a response from an AI agent with context from vector embeddings
    
    This endpoint integrates with the vector database to provide relevant context
    from the dataset based on semantic similarity to the query. The embedding model
    specified in the request is used to generate the query embedding, which is then
    used to search for similar content in the vector database.
    
    If use_all_datasets is set to True, the endpoint will search across all vectorized
    datasets instead of just the specified dataset_id.
    """
    try:
        # Prepare context from vector search if dataset is specified or if using all datasets
        vector_context = None
        if request.dataset_id or request.use_all_datasets:
            try:
                # Determine which embedding model to use
                embedding_model = None
                if request.model_id and request.model_id in TEXT_GEN_MODELS:
                    # If a text generation model is specified, we need to determine which embedding model to use
                    # First, check if there's a preferred embedding model in the context
                    if request.context and "embedding_model" in request.context:
                        embedding_model = request.context["embedding_model"]
                    else:
                        # Use the default embedding model
                        from api.config.settings import get_settings
                        settings = get_settings()
                        embedding_model = settings.VECTOR_EMBEDDING_API_MODEL
                
                # Generate embeddings for the query using the vector_embedding_api
                embedding_result = await vector_embedding_api.generate_embeddings(
                    texts=request.query,
                    model_id=embedding_model
                )
                
                if embedding_result["success"]:
                    query_embedding = embedding_result["embeddings"][0]
                    
                    # Search for similar vectors using the vector_service
                    if request.use_all_datasets:
                        # Search across all datasets
                        search_results = await vector_service.search_vectors(
                            query_vector=query_embedding,
                            dataset_id=None,  # None means search across all datasets
                            limit=10,  # Increase limit for cross-dataset search
                            include_chunks=True
                        )
                    else:
                        # Search in the specified dataset
                        search_results = await vector_service.search_vectors(
                            query_vector=query_embedding,
                            dataset_id=int(request.dataset_id),
                            limit=5,
                            include_chunks=True
                        )
                    
                    if search_results:
                        # Format the context for the AI agent
                        vector_context = {
                            "similarContent": [
                                {
                                    "id": str(item.get("id")),
                                    "content": item.get("chunk_text", ""),
                                    "dataset_id": str(item.get("dataset_id")),
                                    "metadata": item.get("metadata", {}),
                                    "score": item.get("similarity", 0)
                                } for item in search_results
                            ],
                            "embeddingModel": embedding_model or "unknown",
                            "searchMode": "all_datasets" if request.use_all_datasets else "single_dataset"
                        }
                        
                        # Add the vector context to the request context
                        if not request.context:
                            request.context = {}
                        request.context["vector_search_results"] = vector_context
            except Exception as e:
                # Log the error but continue without vector context
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error searching vectors: {str(e)}")
        
        # Get response from the AI agent
        result = await get_agent_response(
            query=request.query,
            agent_type=request.agent_type,
            model_id=request.model_id,
            dataset_id=request.dataset_id,
            chat_history=request.chat_history,
            context=request.context
        )
        
        # Add vector context information to the response if available
        if vector_context:
            if "context" not in result:
                result["context"] = {}
            result["context"]["vector_search_results"] = vector_context
        
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
    Get a streaming response from an AI agent with context from vector embeddings
    
    This endpoint integrates with the vector database to provide relevant context
    from the dataset based on semantic similarity to the query. The embedding model
    specified in the request is used to generate the query embedding, which is then
    used to search for similar content in the vector database.
    
    If use_all_datasets is set to True, the endpoint will search across all vectorized
    datasets instead of just the specified dataset_id.
    """
    try:
        # Prepare context from vector search if dataset is specified or if using all datasets
        if request.dataset_id or request.use_all_datasets:
            try:
                # Determine which embedding model to use
                embedding_model = None
                if request.model_id and request.model_id in TEXT_GEN_MODELS:
                    # If a text generation model is specified, we need to determine which embedding model to use
                    # First, check if there's a preferred embedding model in the context
                    if request.context and "embedding_model" in request.context:
                        embedding_model = request.context["embedding_model"]
                    else:
                        # Use the default embedding model
                        from api.config.settings import get_settings
                        settings = get_settings()
                        embedding_model = settings.VECTOR_EMBEDDING_API_MODEL
                
                # Generate embeddings for the query using the vector_embedding_api
                embedding_result = await vector_embedding_api.generate_embeddings(
                    texts=request.query,
                    model_id=embedding_model
                )
                
                if embedding_result["success"]:
                    query_embedding = embedding_result["embeddings"][0]
                    
                    # Search for similar vectors using the vector_service
                    if request.use_all_datasets:
                        # Search across all datasets
                        search_results = await vector_service.search_vectors(
                            query_vector=query_embedding,
                            dataset_id=None,  # None means search across all datasets
                            limit=10,  # Increase limit for cross-dataset search
                            include_chunks=True
                        )
                    else:
                        # Search in the specified dataset
                        search_results = await vector_service.search_vectors(
                            query_vector=query_embedding,
                            dataset_id=int(request.dataset_id),
                            limit=5,
                            include_chunks=True
                        )
                    
                    if search_results:
                        # Format the context for the AI agent
                        vector_context = {
                            "similarContent": [
                                {
                                    "id": str(item.get("id")),
                                    "content": item.get("chunk_text", ""),
                                    "dataset_id": str(item.get("dataset_id")),
                                    "metadata": item.get("metadata", {}),
                                    "score": item.get("similarity", 0)
                                } for item in search_results
                            ],
                            "embeddingModel": embedding_model or "unknown",
                            "searchMode": "all_datasets" if request.use_all_datasets else "single_dataset"
                        }
                        
                        # Add the vector context to the request context
                        if not request.context:
                            request.context = {}
                        request.context["vector_search_results"] = vector_context
            except Exception as e:
                # Log the error but continue without vector context
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error searching vectors for streaming: {str(e)}")
        
        # Create generator function for streaming response
        async def response_generator():
            # Convert request to dict and pass to streaming response function
            request_dict = request.dict()
            async for chunk in get_streaming_response(request_dict):
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
