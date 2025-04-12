
from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from typing import Dict, Any, Optional, List

from api.routes.auth_router import get_current_user_or_api_key
from api.services.ai_service import get_ai_response, analyze_dataset, generate_embeddings
from api.services.vector_service import store_vector_embeddings, search_vector_embeddings

router = APIRouter()

@router.post("/assistant", response_model=Dict[str, Any])
async def ai_assistant(
    message: str = Body(..., description="User message to the AI assistant"),
    context: Optional[Dict[str, Any]] = Body({}, description="Additional context for the AI"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Get a response from the AI assistant."""
    try:
        # Add user information to the context
        ai_context = {
            **context,
            "user_id": current_user.id,
            "user_name": current_user.username,
            "timestamp": "2023-04-11T12:00:00Z"
        }
        
        # Get AI response
        response = await get_ai_response(message, ai_context)
        
        return {
            "message": message,
            "response": response["text"],
            "context": response["context"],
            "timestamp": response["timestamp"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get AI response: {str(e)}")

@router.post("/ask", response_model=Dict[str, Any])
async def ask_about_dataset(
    dataset_id: str = Body(..., description="ID of the dataset to query"),
    question: str = Body(..., description="Question about the dataset"),
    context: Optional[Dict[str, Any]] = Body({}, description="Additional context for the AI"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Ask questions about a specific dataset."""
    try:
        # Analyze dataset and get response
        analysis_result = await analyze_dataset(dataset_id, question, context)
        
        return {
            "answer": analysis_result["answer"],
            "confidence": analysis_result["confidence"],
            "context": analysis_result["context"],
            "query_analysis": analysis_result["query_analysis"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze dataset: {str(e)}")

@router.post("/generate-rules/{dataset_id}", response_model=Dict[str, Any])
async def generate_business_rules(
    dataset_id: str,
    config: Dict[str, Any] = Body({}, description="Configuration for rule generation"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Generate business rules for a dataset using AI."""
    from api.services.rule_service import generate_rules_with_ai
    
    try:
        rules = await generate_rules_with_ai(dataset_id, config)
        
        return {
            "dataset_id": dataset_id,
            "rules_generated": len(rules),
            "rules": rules,
            "generation_metadata": {
                "method": config.get("method", "pattern_mining"),
                "confidence_threshold": config.get("confidence_threshold", 0.8),
                "timestamp": "2023-04-11T12:00:00Z"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate rules: {str(e)}")

@router.post("/analyze-anomalies/{dataset_id}", response_model=Dict[str, Any])
async def analyze_anomalies(
    dataset_id: str,
    config: Dict[str, Any] = Body({}, description="Configuration for anomaly analysis"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Analyze anomalies in a dataset and provide explanations."""
    from api.services.anomaly_service import analyze_anomalies_with_ai
    
    try:
        anomaly_analysis = await analyze_anomalies_with_ai(dataset_id, config)
        
        return {
            "dataset_id": dataset_id,
            "anomaly_count": len(anomaly_analysis["anomalies"]),
            "anomalies": anomaly_analysis["anomalies"],
            "root_causes": anomaly_analysis["root_causes"],
            "recommendations": anomaly_analysis["recommendations"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze anomalies: {str(e)}")

# New AI Chat and Vector DB Routes

@router.post("/embeddings", response_model=Dict[str, Any])
async def create_embeddings(
    text: str = Body(..., description="Text to generate embeddings for"),
    model: str = Body("sentence-transformers/all-MiniLM-L6-v2", description="Embedding model name"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Generate embeddings for text using Hugging Face models."""
    try:
        embedding_result = await generate_embeddings(text, model)
        
        return {
            "text": text,
            "embedding": embedding_result["embedding"],
            "model": model,
            "dimensions": len(embedding_result["embedding"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")

@router.post("/embeddings/store", response_model=Dict[str, Any])
async def store_embeddings(
    dataset_id: str = Body(..., description="Dataset ID to associate with"),
    record_id: str = Body(..., description="Record ID within the dataset"),
    embedding: List[float] = Body(..., description="Vector embedding"),
    metadata: Dict[str, Any] = Body(..., description="Associated metadata"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Store vector embeddings for future retrieval."""
    try:
        result = await store_vector_embeddings(dataset_id, record_id, embedding, metadata)
        
        return {
            "success": True,
            "embedding_id": result["embedding_id"],
            "dataset_id": dataset_id,
            "record_id": record_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store embeddings: {str(e)}")

@router.post("/embeddings/search", response_model=Dict[str, Any])
async def search_embeddings(
    dataset_id: str = Body(..., description="Dataset ID to search within"),
    query_vector: List[float] = Body(..., description="Query vector for similarity search"),
    limit: int = Body(10, description="Number of results to return"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Search for similar vectors in the database."""
    try:
        search_results = await search_vector_embeddings(dataset_id, query_vector, limit)
        
        return {
            "dataset_id": dataset_id,
            "results": search_results,
            "count": len(search_results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search embeddings: {str(e)}")

@router.post("/suggestions", response_model=Dict[str, Any])
async def get_chat_suggestions(
    dataset_id: Optional[str] = Body(None, description="Dataset ID to get suggestions for"),
    context: Dict[str, Any] = Body({}, description="User context for personalized suggestions"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Get suggested questions for the AI chat interface."""
    try:
        # This would call an AI service to generate suggestions
        # For now, return static suggestions
        suggestions = [
            {"id": "1", "text": "What's the distribution of values in column X?", "category": "exploration"},
            {"id": "2", "text": "Show me the relationship between column A and B", "category": "correlation"},
            {"id": "3", "text": "What are the top outliers in this dataset?", "category": "anomalies"},
            {"id": "4", "text": "Summarize the key statistics of this dataset", "category": "statistics"},
            {"id": "5", "text": "What trends do you notice over time?", "category": "trends"}
        ]
        
        if dataset_id:
            # Add dataset-specific suggestions
            from api.services.dataset_service import get_dataset_columns
            try:
                columns = await get_dataset_columns(dataset_id)
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
            except:
                pass
        
        return {
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat suggestions: {str(e)}")

@router.get("/models", response_model=Dict[str, Any])
async def get_available_models(
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Get available AI models for use with the chat interface."""
    try:
        # This would query available models from a service
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
                "is_default": True
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
        raise HTTPException(status_code=500, detail=f"Failed to store chat history: {str(e)}")
