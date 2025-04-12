
from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import logging
import asyncio
from pydantic import BaseModel

from api.routes.auth_router import get_current_user_or_api_key
from api.services.ai_service import get_ai_response, analyze_dataset, generate_embeddings
from api.services.vector_service import store_vector_embeddings, search_vector_embeddings
from api.services.dataset_service import get_dataset_columns, get_all_dataset_ids
from api.services.cache_service import get_cached_response, cache_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request validation
class QuestionRequest(BaseModel):
    dataset_id: Optional[str] = None
    question: str
    model_id: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500
    streaming: Optional[bool] = False

class EmbeddingRequest(BaseModel):
    text: str
    model: Optional[str] = "sentence-transformers/all-MiniLM-L6-v2"

class SuggestionRequest(BaseModel):
    dataset_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}

@router.post("/assistant", response_model=Dict[str, Any])
async def ai_assistant(
    message: str = Body(..., description="User message to the AI assistant"),
    context: Optional[Dict[str, Any]] = Body({}, description="Additional context for the AI"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Get a response from the AI assistant."""
    try:
        # Check cache first
        cache_key = f"ai_assistant:{message}:{str(context)}"
        cached_result = get_cached_response(cache_key)
        if cached_result:
            return cached_result
        
        # Add user information to the context
        ai_context = {
            **context,
            "user_id": current_user.id if current_user else "anonymous",
            "user_name": current_user.username if current_user else "guest",
            "timestamp": datetime.now().isoformat()
        }
        
        # Get AI response
        response = await get_ai_response(message, ai_context)
        
        result = {
            "message": message,
            "response": response["text"],
            "context": response["context"],
            "timestamp": response["timestamp"]
        }
        
        # Cache the response for future reuse
        cache_response(cache_key, result, expiry_seconds=3600)  # Cache for 1 hour
        
        return result
    except Exception as e:
        logger.error(f"Failed to get AI response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get AI response: {str(e)}")

@router.post("/ask", response_model=Dict[str, Any])
async def ask_about_dataset(
    request: QuestionRequest,
    current_user = Depends(get_current_user_or_api_key)
):
    """Ask questions about a specific dataset or all datasets."""
    try:
        # Generate cache key based on request
        cache_key = f"dataset_question:{request.dataset_id or 'all'}:{request.question}:{request.model_id}"
        cached_result = get_cached_response(cache_key)
        if cached_result:
            return cached_result
        
        context = {
            "user_id": current_user.id if current_user else "anonymous",
            "model_id": request.model_id,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }
        
        # If no dataset specified, fetch from all datasets
        if not request.dataset_id:
            # Get all dataset IDs
            dataset_ids = await get_all_dataset_ids()
            results = []
            
            # Process datasets in parallel for better performance
            async def process_dataset(dataset_id):
                try:
                    result = await analyze_dataset(dataset_id, request.question, context)
                    return {**result, "dataset_id": dataset_id}
                except Exception as e:
                    logger.error(f"Error processing dataset {dataset_id}: {str(e)}")
                    return None
            
            # Create tasks for each dataset
            tasks = [process_dataset(ds_id) for ds_id in dataset_ids]
            dataset_results = await asyncio.gather(*tasks)
            
            # Filter out failed results and find the best answer
            valid_results = [r for r in dataset_results if r is not None]
            if not valid_results:
                raise HTTPException(status_code=404, detail="No valid results from any datasets")
            
            # Sort by confidence score to get the best answer
            best_result = sorted(valid_results, key=lambda x: x.get("confidence", 0), reverse=True)[0]
            
            result = {
                "answer": best_result["answer"],
                "confidence": best_result["confidence"],
                "context": best_result["context"],
                "query_analysis": best_result["query_analysis"],
                "dataset_id": best_result["dataset_id"],
                "combined_datasets": True,
                "datasets_analyzed": len(valid_results)
            }
        else:
            # Analyze the specified dataset
            result = await analyze_dataset(request.dataset_id, request.question, context)
            result["dataset_id"] = request.dataset_id
            result["combined_datasets"] = False
        
        # Cache the result
        cache_response(cache_key, result, expiry_seconds=1800)  # Cache for 30 minutes
        
        return result
    except Exception as e:
        logger.error(f"Failed to analyze dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze dataset: {str(e)}")

@router.post("/embeddings", response_model=Dict[str, Any])
async def create_embeddings(
    request: EmbeddingRequest,
    current_user = Depends(get_current_user_or_api_key)
):
    """Generate embeddings for text using Hugging Face models."""
    try:
        # Check cache for existing embeddings
        cache_key = f"embeddings:{request.model}:{request.text}"
        cached_result = get_cached_response(cache_key)
        if cached_result:
            return cached_result
            
        # Generate new embeddings
        embedding_result = await generate_embeddings(request.text, request.model)
        
        result = {
            "text": request.text,
            "embedding": embedding_result["embedding"],
            "model": request.model,
            "dimensions": len(embedding_result["embedding"])
        }
        
        # Cache the embeddings
        cache_response(cache_key, result, expiry_seconds=86400)  # Cache for 24 hours
        
        return result
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")

@router.post("/suggestions", response_model=Dict[str, Any])
async def get_chat_suggestions(
    request: SuggestionRequest,
    current_user = Depends(get_current_user_or_api_key)
):
    """Get suggested questions for the AI chat interface."""
    try:
        # Check cache
        cache_key = f"chat_suggestions:{request.dataset_id or 'all'}"
        cached_result = get_cached_response(cache_key)
        if cached_result:
            return cached_result
            
        suggestions = [
            {"id": "1", "text": "What's the distribution of values in column X?", "category": "exploration"},
            {"id": "2", "text": "Show me the relationship between column A and B", "category": "correlation"},
            {"id": "3", "text": "What are the top outliers in this dataset?", "category": "anomalies"},
            {"id": "4", "text": "Summarize the key statistics of this dataset", "category": "statistics"},
            {"id": "5", "text": "What trends do you notice over time?", "category": "trends"}
        ]
        
        if request.dataset_id:
            # Add dataset-specific suggestions
            try:
                columns = await get_dataset_columns(request.dataset_id)
                if columns and len(columns) > 1:
                    col1 = columns[0]
                    col2 = columns[1]
                    suggestions.append({
                        "id": "ds-1", 
                        "text": f"What's the distribution of {col1}?", 
                        "category": "dataset-specific"
                    })
                    suggestions.append({
                        "id": "ds-2", 
                        "text": f"Is there a correlation between {col1} and {col2}?", 
                        "category": "dataset-specific"
                    })
            except Exception as e:
                logger.error(f"Error getting dataset columns: {str(e)}")
        
        result = {"suggestions": suggestions}
        
        # Cache the suggestions
        cache_response(cache_key, result, expiry_seconds=3600)  # Cache for 1 hour
        
        return result
    except Exception as e:
        logger.error(f"Failed to get chat suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat suggestions: {str(e)}")

@router.get("/models", response_model=Dict[str, Any])
async def get_available_models(
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Get available AI models for use with the chat interface."""
    try:
        # This would be expanded to query available models from a database or service
        models = [
            {
                "id": "sentence-transformers/all-MiniLM-L6-v2",
                "type": "embedding",
                "dimensions": 384,
                "is_default": True
            },
            {
                "id": "google/flan-t5-base",
                "type": "generation",
                "is_default": True,
                "max_tokens": 512
            },
            {
                "id": "google/flan-t5-large",
                "type": "generation",
                "max_tokens": 1024
            },
            {
                "id": "facebook/bart-large-mnli",
                "type": "zero-shot-classification"
            },
            {
                "id": "onnx-community/whisper-tiny.en",
                "type": "speech-to-text"
            }
        ]
        
        if model_type:
            models = [m for m in models if m["type"] == model_type]
        
        return {
            "models": models
        }
    except Exception as e:
        logger.error(f"Failed to get available models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get available models: {str(e)}")

@router.get("/chat-history/{dataset_id}", response_model=Dict[str, Any])
async def get_chat_history(
    dataset_id: str = Path(..., description="Dataset ID to get chat history for"),
    limit: int = Query(50, description="Maximum number of messages to return"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Get chat history for a dataset."""
    try:
        # This would retrieve chat history from a database
        # For now, return empty history as we use local storage in the frontend
        return {
            "history": [],
            "metadata": {
                "dataset_id": dataset_id,
                "count": 0
            }
        }
    except Exception as e:
        logger.error(f"Failed to get chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")

@router.post("/chat-history/{dataset_id}", response_model=Dict[str, Any])
async def store_chat_history(
    dataset_id: str = Path(..., description="Dataset ID to store chat history for"),
    messages: List[Dict[str, Any]] = Body(..., description="Messages to store"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Store chat history for a dataset."""
    try:
        # This would store chat history in a database
        # For now, just return success
        return {
            "stored": True,
            "message": "Chat history stored successfully"
        }
    except Exception as e:
        logger.error(f"Failed to store chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store chat history: {str(e)}")

# Create a new service for caching responses
<lov-write file_path="api/services/cache_service.py">
import time
import logging
from typing import Dict, Any, Optional
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple in-memory cache
_cache: Dict[str, Dict[str, Any]] = {}

def get_cached_response(key: str) -> Optional[Dict[str, Any]]:
    """
    Get a response from the cache if it exists and is not expired
    
    Args:
        key: The cache key
        
    Returns:
        The cached data if found and valid, otherwise None
    """
    if key not in _cache:
        return None
    
    cache_item = _cache[key]
    
    # Check if expired
    if cache_item["expires_at"] < time.time():
        # Expired, remove from cache
        del _cache[key]
        return None
    
    # Update access stats
    _cache[key]["access_count"] += 1
    _cache[key]["last_accessed"] = time.time()
    
    logger.debug(f"Cache hit for key: {key}")
    return cache_item["data"]

def cache_response(key: str, data: Dict[str, Any], expiry_seconds: int = 3600) -> None:
    """
    Store a response in the cache
    
    Args:
        key: The cache key
        data: The data to cache
        expiry_seconds: How long the cache should be valid for (in seconds)
    """
    now = time.time()
    
    _cache[key] = {
        "data": data,
        "created_at": now,
        "expires_at": now + expiry_seconds,
        "last_accessed": now,
        "access_count": 0
    }
    
    logger.debug(f"Stored in cache: {key} (expires in {expiry_seconds}s)")
    
    # Perform cache cleanup if it's getting large
    if len(_cache) > 1000:  # Arbitrary limit
        _cleanup_cache()

def invalidate_cache(key: str) -> bool:
    """
    Remove a specific item from the cache
    
    Args:
        key: The cache key to remove
        
    Returns:
        True if the item was in the cache and removed, False otherwise
    """
    if key in _cache:
        del _cache[key]
        logger.debug(f"Invalidated cache key: {key}")
        return True
    return False

def clear_cache() -> int:
    """
    Clear the entire cache
    
    Returns:
        The number of items that were in the cache
    """
    count = len(_cache)
    _cache.clear()
    logger.info(f"Cleared {count} items from cache")
    return count

def _cleanup_cache() -> int:
    """
    Clean up the cache by removing expired or least recently used items
    
    Returns:
        The number of items removed from the cache
    """
    now = time.time()
    expired_keys = [k for k, v in _cache.items() if v["expires_at"] < now]
    
    # Remove expired items
    for key in expired_keys:
        del _cache[key]
    
    # If still too many items, remove least recently accessed
    if len(_cache) > 800:  # Target size
        items = list(_cache.items())
        # Sort by last accessed time
        items.sort(key=lambda x: x[1]["last_accessed"])
        # Remove oldest 20% of items
        items_to_remove = items[:int(len(items) * 0.2)]
        for key, _ in items_to_remove:
            del _cache[key]
    
    removed = len(expired_keys) + (len(_cache) - 800 if len(_cache) > 800 else 0)
    logger.info(f"Cache cleanup: removed {removed} items")
    return removed

# Helper function for dataset service
@lru_cache(maxsize=100)
async def get_all_dataset_ids():
    """Mock function to get all dataset IDs - would be replaced with actual DB call"""
    # This would be replaced with actual database query
    return ["ds001", "ds002", "ds003"]

@lru_cache(maxsize=100)
async def get_dataset_columns(dataset_id: str):
    """Mock function to get columns for a dataset - would be replaced with actual DB call"""
    # This would be replaced with actual database query
    columns_map = {
        "ds001": ["name", "age", "salary", "department"],
        "ds002": ["product_id", "price", "quantity", "date"],
        "ds003": ["customer_id", "order_date", "total_value", "items"]
    }
    return columns_map.get(dataset_id, [])
