import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
import asyncio
from datetime import datetime

import aiohttp
import numpy as np
from fastapi import HTTPException

from .cache_service import get_cache, set_cache
from .vector_service import VectorService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  

# Initialize vector service
vector_service = VectorService()

# Environment variables for API keys
from api.config.settings import get_settings
settings = get_settings()
HF_API_KEY = settings.HUGGINGFACE_API_KEY
OPENAI_API_KEY = settings.OPENAI_API_KEY

# Model endpoints
HF_API_BASE = getattr(settings, "HF_API_BASE", "https://api-inference.huggingface.co/models/")
OPENAI_API_BASE = getattr(settings, "OPENAI_API_BASE", "https://api.openai.com/v1/")

# Available models configuration
AVAILABLE_MODELS = {
    # Hugging Face models
    "mistral-7b-instruct": {
        "id": "mistral-7b-instruct",
        "name": "Mistral 7B Instruct",
        "provider": "huggingface",
        "endpoint": "mistralai/Mistral-7B-Instruct-v0.2",
        "max_tokens": 4096,
        "supports_streaming": True,
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
    },
    "llama-3-8b": {
        "id": "llama-3-8b",
        "name": "Llama 3 8B",
        "provider": "huggingface",
        "endpoint": "meta-llama/Meta-Llama-3-8B-Instruct",
        "max_tokens": 4096,
        "supports_streaming": True,
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
    },
    "zephyr-7b": {
        "id": "zephyr-7b",
        "name": "Zephyr 7B",
        "provider": "huggingface",
        "endpoint": "HuggingFaceH4/zephyr-7b-beta",
        "max_tokens": 2048,
        "supports_streaming": True,
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
    },
    # OpenAI models
    "gpt-3.5-turbo": {
        "id": "gpt-3.5-turbo",
        "name": "GPT-3.5 Turbo",
        "provider": "openai",
        "endpoint": "chat/completions",
        "model": "gpt-3.5-turbo",
        "max_tokens": 4096,
        "supports_streaming": True,
        "embedding_model": "text-embedding-3-small"
    },
    "gpt-4": {
        "id": "gpt-4",
        "name": "GPT-4",
        "provider": "openai",
        "endpoint": "chat/completions",
        "model": "gpt-4",
        "max_tokens": 8192,
        "supports_streaming": True,
        "embedding_model": "text-embedding-3-small"
    }
}

# Default model if none specified
DEFAULT_MODEL = "mistral-7b-instruct"

# Agent types and their configurations
AGENT_TYPES = {
    "data_analyst": {
        "name": "Data Analyst",
        "description": "Analyzes datasets and provides insights",
        "system_prompt": "You are a data analyst assistant. Help the user analyze their data, identify patterns, and provide insights. Use the context provided to answer questions accurately.",
        "capabilities": ["data_analysis", "visualization", "statistics"]
    },
    "business_intelligence": {
        "name": "Business Intelligence",
        "description": "Provides business insights and recommendations",
        "system_prompt": "You are a business intelligence assistant. Help the user understand their business data, identify trends, and make data-driven decisions. Use the context provided to answer questions accurately.",
        "capabilities": ["trend_analysis", "forecasting", "recommendations"]
    },
    "business_rules": {
        "name": "Business Rules Engine",
        "description": "Generates and manages business rules based on data patterns",
        "system_prompt": "You are a business rules expert. Analyze the data and context to generate relevant business rules. Provide clear, actionable rules that can be applied to the data. Format rules in a structured way with conditions and actions.",
        "capabilities": ["rule_generation", "pattern_recognition", "validation"]
    },
    "data_explorer": {
        "name": "Data Explorer",
        "description": "Helps explore and understand datasets",
        "system_prompt": "You are a data exploration assistant. Help the user explore and understand their datasets, explain data structures, and suggest ways to work with the data. Use the context provided to answer questions accurately.",
        "capabilities": ["data_exploration", "schema_analysis", "data_quality"]
    }
}

# Default agent type
DEFAULT_AGENT = "data_analyst"

async def get_available_models() -> List[Dict[str, Any]]:
    """
    Get list of available AI models
    """
    models = []
    for model_id, config in AVAILABLE_MODELS.items():
        models.append({
            "id": model_id,
            "name": config["name"],
            "provider": config["provider"],
            "max_tokens": config["max_tokens"],
            "supports_streaming": config["supports_streaming"]
        })
    return models

async def get_available_agents() -> List[Dict[str, Any]]:
    """
    Get list of available agent types
    """
    agents = []
    for agent_id, config in AGENT_TYPES.items():
        agents.append({
            "id": agent_id,
            "name": config["name"],
            "description": config["description"],
            "capabilities": config["capabilities"]
        })
    return agents

async def generate_embeddings(text: str, model_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate embeddings for text using the specified model
    
    This function uses the vector_embedding_api service for consistent embedding generation
    throughout the application.
    """
    # Import the vector_embedding_api service
    from ..services.vector_embedding_api import vector_embedding_api
    
    # Use default model if none specified
    if not model_id or model_id not in AVAILABLE_MODELS:
        model_id = DEFAULT_MODEL
    
    model_config = AVAILABLE_MODELS[model_id]
    embedding_model = model_config["embedding_model"]
    
    # Check cache first
    cache_key = f"embedding:{embedding_model}:{text}"
    cached_result = get_cache(cache_key)
    if cached_result:
        return cached_result
    
    try:
        # Use the vector_embedding_api service for consistent embedding generation
        result = await vector_embedding_api.generate_embeddings(
            texts=text,
            model_id=embedding_model
        )
        
        if not result["success"]:
            # If the vector_embedding_api fails, log the error and raise an exception
            logger.error(f"Error from vector_embedding_api: {result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=result.get('status', 500), 
                detail=f"Failed to generate embeddings: {result.get('error', 'Unknown error')}"
            )
        
        # Extract embeddings from the result
        embeddings = result["embeddings"]
        
        # If embeddings is a list of embeddings (for multiple texts), take the first one
        if isinstance(embeddings, list) and len(embeddings) > 0:
            embeddings = embeddings[0]
        
        # Cache the result
        response_data = {
            "success": True,
            "model": embedding_model,
            "embeddings": embeddings,
            "dimensions": len(embeddings)
        }
        set_cache(cache_key, response_data, ttl=86400)  # Cache for 24 hours
        
        return response_data
    
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")

async def get_agent_response(
    query: str,
    agent_type: str = DEFAULT_AGENT,
    model_id: str = DEFAULT_MODEL,
    dataset_id: Optional[str] = None,
    chat_history: Optional[List[Dict[str, Any]]] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get a response from an AI agent with enhanced insights generation
    
    This method processes a user query, retrieves relevant context from vector search,
    passes both the query and search results to a generative LLM, and returns insights
    derived from the LLM's analysis.
    
    Args:
        query: The user's question or prompt
        agent_type: Type of AI agent to use
        model_id: ID of the LLM model to use
        dataset_id: Optional dataset ID to search within
        chat_history: Optional conversation history
        context: Optional additional context including vector search results
        
    Returns:
        Dictionary containing the AI response, insights, and metadata
    """
    # Validate model and agent type
    if model_id not in AVAILABLE_MODELS:
        raise HTTPException(status_code=400, detail=f"Invalid model ID: {model_id}")
    
    if agent_type not in AGENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid agent type: {agent_type}")
    
    model_config = AVAILABLE_MODELS[model_id]
    agent_config = AGENT_TYPES[agent_type]
    
    # Check cache first (if not a streaming request)
    cache_key = f"agent:{agent_type}:{model_id}:{dataset_id or 'all'}:{query}"
    if chat_history is None or len(chat_history) == 0:  # Only cache first messages in a conversation
        cached_result = get_cache(cache_key)
        if cached_result:
            return cached_result
    
    # Prepare context from vector search if dataset is specified or provided in context
    vector_context = []
    
    # First check if vector search results are already provided in the context
    if context and isinstance(context, dict) and "vector_search_results" in context:
        vector_context_from_router = context["vector_search_results"]
        if isinstance(vector_context_from_router, dict) and "similarContent" in vector_context_from_router:
            vector_context = vector_context_from_router["similarContent"]
        elif isinstance(vector_context_from_router, list):
            vector_context = vector_context_from_router
    
    # If no vector context yet and dataset_id is provided, perform vector search
    if not vector_context and dataset_id:
        try:
            # Generate embeddings for the query
            embedding_result = await generate_embeddings(query, model_id)
            # Handle both single embedding and list of embeddings
            query_embedding = embedding_result["embeddings"][0] if isinstance(embedding_result["embeddings"], list) else embedding_result["embeddings"]
            
            # Search for similar vectors using the vector_service
            search_results = await vector_service.search_vectors(
                query_vector=query_embedding,
                dataset_id=int(dataset_id) if dataset_id and dataset_id.isdigit() else None,
                limit=5,
                include_chunks=True
            )
            
            if search_results and isinstance(search_results, dict) and "results" in search_results and search_results["results"]:
                vector_context = search_results["results"]
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            # Continue without vector context if there's an error
    
    # Prepare the prompt with context
    system_prompt = agent_config["system_prompt"]
    
    # Check if we have relevant context from vector search
    has_relevant_context = False
    context_relevance_threshold = 0.75  # Minimum similarity score to consider context relevant
    context_text = "\n\nRelevant context from the dataset:\n"
    
    if vector_context:
        # Filter out low-relevance context items
        relevant_items = []
        for item in vector_context:
            similarity = item.get('similarity', 0)
            if similarity >= context_relevance_threshold:
                relevant_items.append(item)
        
        # If we have relevant context, add it to the prompt
        if relevant_items:
            has_relevant_context = True
            for i, item in enumerate(relevant_items):
                # Handle different possible content field names
                content_field = (
                    item.get('content') or 
                    item.get('chunk_text') or 
                    item.get('text') or 
                    str(item.get('metadata', {}).get('content', ''))
                )
                if content_field:
                    # Add source information if available
                    source_info = ""
                    source = (
                        item.get("metadata", {}).get("source") or 
                        item.get("source") or 
                        item.get("dataset_name")
                    )
                    if source:
                        source_info = f" (Source: {source})"
                    
                    context_text += f"[{i+1}] {content_field}{source_info}\n"
            system_prompt += context_text
    
    # Add a note about context availability to the prompt
    if not has_relevant_context and dataset_id:
        system_prompt += "\n\nNote: No highly relevant context was found in the dataset for this query. "
        system_prompt += "Please inform the user that you don't have specific information about this topic from the dataset, "
        system_prompt += "but you can still provide general knowledge if appropriate.\n"
    
    # Add custom context if provided
    if context and isinstance(context, dict):
        if "system_prompt_addition" in context:
            system_prompt += f"\n\n{context['system_prompt_addition']}"
    
    try:
        # Format messages based on provider
        if model_config["provider"] == "huggingface":
            # Initialize messages with system prompt
            messages = [{"role": "system", "content": system_prompt}]
            
            # Process chat history if available
            if chat_history and isinstance(chat_history, list):
                # Check if chat history already contains the system message
                has_system_message = any(msg.get("role") == "system" for msg in chat_history)
                
                # If chat history already has system message, use it directly
                if has_system_message:
                    messages = chat_history.copy()
                else:
                    # Add chat history after system message
                    for msg in chat_history:
                        if msg.get("role") and msg.get("content"):
                            messages.append({
                                "role": msg.get("role"),
                                "content": msg.get("content")
                            })
            
            # Check if the last message is already the current query
            last_message = messages[-1] if messages else None
            if not (last_message and 
                    last_message.get("role") == "user" and 
                    last_message.get("content") == query):
                # Add current query if it's not already the last message
                messages.append({"role": "user", "content": query})
            
            # Call Hugging Face API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{HF_API_BASE}{model_config['endpoint']}",
                    headers={"Authorization": f"Bearer {HF_API_KEY}"},
                    json={"inputs": messages, "parameters": {"max_new_tokens": 1024}}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error from HF API: {error_text}")
                        raise HTTPException(status_code=response.status, detail="Failed to get AI response")
                    
                    result = await response.json()
                    ai_response = result[0]["generated_text"]
        
        elif model_config["provider"] == "openai":
            # Initialize messages with system prompt
            messages = [{"role": "system", "content": system_prompt}]
            
            # Process chat history if available
            if chat_history and isinstance(chat_history, list):
                # Check if chat history already contains the system message
                has_system_message = any(msg.get("role") == "system" for msg in chat_history)
                
                # If chat history already has system message, use it directly
                if has_system_message:
                    messages = chat_history.copy()
                else:
                    # Add chat history after system message
                    for msg in chat_history:
                        if msg.get("role") and msg.get("content"):
                            messages.append({
                                "role": msg.get("role"),
                                "content": msg.get("content")
                            })
            
            # Check if the last message is already the current query
            last_message = messages[-1] if messages else None
            if not (last_message and 
                    last_message.get("role") == "user" and 
                    last_message.get("content") == query):
                # Add current query if it's not already the last message
                messages.append({"role": "user", "content": query})
            
            # Call OpenAI API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{OPENAI_API_BASE}{model_config['endpoint']}",
                    headers={
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_config["model"],
                        "messages": messages,
                        "max_tokens": 1024
                    }
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error from OpenAI API: {error_text}")
                        raise HTTPException(status_code=response.status, detail="Failed to get AI response")
                    
                    result = await response.json()
                    ai_response = result["choices"][0]["message"]["content"]
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {model_config['provider']}")
        
        # Extract insights if possible (simple implementation)
        insights = extract_insights(ai_response)
        
        # Calculate confidence based on context relevance
        confidence = 0.9  # Default confidence
        if dataset_id:
            if not has_relevant_context:
                confidence = 0.4  # Low confidence when no relevant context found
            elif vector_context:
                # Calculate average similarity of top results
                similarities = [item.get('similarity', 0) for item in vector_context[:3]]
                if similarities:
                    avg_similarity = sum(similarities) / len(similarities)
                    confidence = min(0.95, avg_similarity)  # Cap at 0.95
        
        # Generate enhanced insights using the embedding model and search results
        enhanced_insights = insights
        try:
            # Only attempt to generate enhanced insights if we have relevant context
            if has_relevant_context and vector_context:
                # Prepare a specialized prompt for insight generation
                insight_prompt = f"Based on the search results and the query '{query}', provide 3-5 key insights or findings:"
                
                # Prepare context from search results for insight generation
                insight_context = "\n\nSearch Results:\n"
                for i, item in enumerate(vector_context[:3]):
                    content = (
                        item.get('content') or 
                        item.get('chunk_text') or 
                        item.get('text') or 
                        str(item.get('metadata', {}).get('content', ''))
                    )
                    if content:
                        insight_context += f"[{i+1}] {content}\n"
                
                # Create a specialized message for insight extraction
                # Use a clean message array for insight generation to avoid role duplication
                insight_messages = [
                    {"role": "system", "content": "You are an analytical assistant that identifies key insights from data. Focus on extracting patterns, trends, correlations, anomalies, and business implications."}, 
                    {"role": "user", "content": insight_context + "\n" + insight_prompt}
                ]
                
                # Use the same model provider but with a specialized prompt for insights
                if model_config["provider"] == "huggingface":
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{HF_API_BASE}{model_config['endpoint']}",
                            headers={"Authorization": f"Bearer {HF_API_KEY}"},
                            json={"inputs": insight_messages, "parameters": {"max_new_tokens": 512}}
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                insight_response = result[0]["generated_text"]
                                # Parse the insights into a list
                                enhanced_insights = [line.strip() for line in insight_response.split("\n") 
                                                   if line.strip() and not line.strip().startswith("#")]
                
                elif model_config["provider"] == "openai":
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{OPENAI_API_BASE}{model_config['endpoint']}",
                            headers={
                                "Authorization": f"Bearer {OPENAI_API_KEY}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": model_config["model"],
                                "messages": insight_messages,
                                "max_tokens": 512
                            }
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                insight_response = result["choices"][0]["message"]["content"]
                                # Parse the insights into a list
                                enhanced_insights = [line.strip() for line in insight_response.split("\n") 
                                                   if line.strip() and not line.strip().startswith("#")]
        except Exception as e:
            logger.warning(f"Error generating enhanced insights: {str(e)}")
            # Fall back to the original insights if enhanced insight generation fails
        
        # Prepare response with enhanced insights
        response_data = {
            "success": True,
            "answer": ai_response,
            "model": model_id,
            "agent": agent_type,
            "timestamp": datetime.now().isoformat(),
            "confidence": confidence,
            "has_relevant_context": has_relevant_context,
            "insights": enhanced_insights,
            "query": query,  # Include the original query
            "search_results": {
                "count": len(vector_context),
                "relevance_score": confidence,
                "items": vector_context[:3]  # Include top 3 search results for reference
            } if vector_context else None,
            "sources": [
                item.get("metadata", {}).get("source", "") or 
                item.get("source", "") or 
                item.get("dataset_name", "") or
                f"Dataset {item.get('dataset_id', 'unknown')}"
                for item in vector_context
            ] if vector_context else []
        }
        
        # Cache the result if it's the first message in a conversation
        if chat_history is None or len(chat_history) == 0:
            set_cache(cache_key, response_data, ttl=3600)  # Cache for 1 hour
        
        return response_data
    
    except Exception as e:
        logger.error(f"Error getting agent response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent response: {str(e)}")

def extract_insights(text: str) -> List[str]:
    """
    Extract key insights from the AI response
    Simple implementation - in production, this could use NLP techniques
    """
    insights = []
    
    # Look for sentences with insight indicators
    indicators = [
        "key finding", "important to note", "significant", "noteworthy",
        "interesting", "critical", "essential", "crucial", "vital",
        "remarkable", "notable", "stands out", "highlight"
    ]
    
    sentences = text.split(". ")
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Add period if missing
        if not sentence.endswith("."):
            sentence += "."
            
        # Check if sentence contains any insight indicators
        if any(indicator in sentence.lower() for indicator in indicators):
            insights.append(sentence)
            continue
            
        # Check for numerical insights
        if any(term in sentence.lower() for term in ["increase", "decrease", "growth", "decline", "percent", "%", "ratio"]):
            insights.append(sentence)
            
    # Limit to top 5 insights
    return insights[:5]

async def generate_business_rules(
    dataset_id: str,
    model_id: str = DEFAULT_MODEL,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate business rules based on dataset analysis.
    
    Args:
        dataset_id: ID of the dataset to analyze
        model_id: ID of the LLM model to use
        context: Optional additional context including vector search results
        
    Returns:
        Dictionary containing generated rules and metadata
    """
    try:
        # Get dataset metadata
        from api.services.dataset_service import DatasetService
        dataset_service = DatasetService()
        dataset = await dataset_service.get_dataset(dataset_id)
        
        if not dataset:
            return {"success": False, "error": "Dataset not found"}
        
        # Get sample data for analysis
        sample_data = await dataset_service.get_sample_data(dataset_id, limit=100)
        
        # Prepare prompt for business rule generation
        prompt = f"""Analyze the following dataset and generate relevant business rules.
        
        Dataset: {dataset.name}
        Description: {dataset.description or 'No description available'}
        
        Sample Data (first 100 rows):
        {sample_data}
        
        Generate 5-10 business rules that could be applied to this data. For each rule, include:
        1. Rule name
        2. Description
        3. Conditions
        4. Actions
        5. Priority (High/Medium/Low)
        6. Business impact
        
        Format the rules in a structured JSON format."""
        
        # Use the business_rules agent to generate rules
        response = await get_agent_response(
            query=prompt,
            agent_type="business_rules",
            model_id=model_id,
            dataset_id=dataset_id,
            context=context
        )
        
        # Extract and parse the generated rules
        rules = []
        try:
            # Try to parse the response as JSON
            if isinstance(response, str):
                rules = json.loads(response)
            elif isinstance(response, dict) and 'response' in response:
                rules = json.loads(response['response'])
        except (json.JSONDecodeError, AttributeError):
            # If parsing fails, try to extract JSON from the response
            import re
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                rules = json.loads(json_match.group(1))
        
        return {
            "success": True,
            "rules": rules,
            "dataset_id": dataset_id,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating business rules: {str(e)}")
        return {"success": False, "error": str(e)}

async def get_chat_suggestions(
    dataset_id: Optional[str] = None,
    category: Optional[str] = None,
    include_rules: bool = True
) -> List[Dict[str, Any]]:
    """
    Get suggested chat queries based on dataset and category
    
    Args:
        dataset_id: Optional dataset ID to get specific suggestions for
        category: Optional category to filter suggestions
        include_rules: Whether to include AI-generated business rules
        
    Returns:
        List of suggestion dictionaries with text and category
    """
    # Define default suggestions by category
    default_suggestions = {
        "analysis": [
            "What are the key trends in this dataset?",
            "Show me the correlation between variables",
            "What insights can you provide about this data?",
            "Identify outliers in this dataset",
            "What patterns do you see in this data?"
        ],
        "visualization": [
            "Create a chart showing the distribution",
            "Visualize the relationship between variables",
            "Show me a time series plot of this data",
            "Generate a heatmap of correlations",
            "Create a dashboard for this dataset"
        ],
        "exploration": [
            "What columns are in this dataset?",
            "Summarize the data structure",
            "Show me sample records from this dataset",
            "What is the data quality like?",
            "How many missing values are there?"
        ],
        "business": [
            "What business insights can you derive?",
            "How can this data improve decision making?",
            "What KPIs should we track based on this data?",
            "Identify revenue opportunities in this data",
            "What competitive advantages does this data reveal?"
        ]
    }
    
    # Add AI-generated business rules if dataset is provided and rules are requested
    ai_rules = []
    if dataset_id and include_rules and (not category or category == 'business'):
        try:
            rules_result = await generate_business_rules(dataset_id=dataset_id)
            if rules_result.get('success') and rules_result.get('rules'):
                for rule in rules_result['rules'][:3]:  # Limit to top 3 rules
                    ai_rules.append({
                        'text': f"Apply rule: {rule.get('name', 'Business Rule')}",
                        'category': 'business_rules',
                        'metadata': rule
                    })
        except Exception as e:
            logger.warning(f"Failed to generate business rules: {str(e)}")
    
    # Add AI rules to default suggestions
    if ai_rules:
        if 'business_rules' not in default_suggestions:
            default_suggestions['business_rules'] = []
        default_suggestions['business_rules'].extend(ai_rules)
    
    # If no category specified, combine all categories
    if not category:
        all_suggestions = []
        for cat, suggestions in default_suggestions.items():
            all_suggestions.extend([{"text": s, "category": cat} for s in suggestions])
        return all_suggestions[:15]  # Return top 15 suggestions
    
    # Return suggestions for the specified category
    if category in default_suggestions:
        return [{"text": s, "category": category} for s in default_suggestions[category]]
    
    # If category not found, return a mix of suggestions
    mixed_suggestions = []
    for cat, suggestions in default_suggestions.items():
        mixed_suggestions.extend([{"text": s, "category": cat} for s in suggestions[:2]])
    return mixed_suggestions[:10]  # Return top 10 mixed suggestions

async def get_streaming_response(request_data: Dict[str, Any]):
    """
    Get streaming response from AI agent with RAG support.
    
    Args:
        request_data: Dictionary containing request parameters
        
    Yields:
        JSON strings containing streaming response data
    """
    try:
        # Extract request parameters
        query = request_data.get("query", "")
        dataset_id = request_data.get("dataset_id")
        model_id = request_data.get("model_id", "default")
        context = request_data.get("context", {})
        
        # Initialize vector context
        vector_context = []
        
        # Get context from vector search if dataset is specified
        if dataset_id:
            try:
                # Generate embeddings for the query
                embedding_result = await generate_embeddings(query, model_id)
                if not embedding_result["success"]:
                    raise ValueError("Failed to generate embeddings")
                
                query_embedding = embedding_result["embeddings"]
                
                # Search for similar vectors
                vector_service = VectorService()
                search_results = await vector_service.search_vectors(
                    query_vector=query_embedding,
                    dataset_id=dataset_id,
                    limit=5,
                    include_chunks=True
                )
                
                if search_results:
                    vector_context = search_results
                    
                    # Yield context information first
                    yield json.dumps({
                        "type": "context",
                        "content": {
                            "sources": [item.get("vector_metadata", {}).get("source", "") for item in vector_context],
                            "chunks": [item.get("chunk_text", "") for item in vector_context]
                        }
                    })
            except Exception as e:
                logger.error(f"Error searching vectors: {str(e)}")
                # Continue without vector context if there's an error
        
        # Prepare the prompt with context
        system_prompt = agent_config["system_prompt"]
        
        # Add dataset context if available
        if vector_context:
            context_text = "\n\nRelevant context from the dataset:\n"
            for i, item in enumerate(vector_context):
                if item.get("chunk_text"):
                    context_text += f"[{i+1}] {item['chunk_text']}\n"
            system_prompt += context_text
        
        # Add custom context if provided
        if context and isinstance(context, dict):
            if "system_prompt_addition" in context:
                system_prompt += f"\n\n{context['system_prompt_addition']}"
        
        # Generate response
        response = await generate_agent_response(
            query=query,
            system_prompt=system_prompt,
            model_id=model_id,
            context=context
        )
        
        # Stream the response
        if response.get("success"):
            yield json.dumps({
                "type": "response",
                "content": response["response"]
            })
        else:
            yield json.dumps({
                "type": "error",
                "content": response.get("error", "Failed to generate response")
            })
            
    except Exception as e:
        logger.error(f"Error in streaming response: {str(e)}")
        yield json.dumps({
            "type": "error",
            "content": str(e)
        })
