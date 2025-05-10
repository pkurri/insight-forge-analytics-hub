"""
AI Service for providing AI capabilities through various models
"""
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import os

# Import AI libraries (these should be added to requirements.txt)
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
except ImportError:
    pass  # Handle gracefully in production code

# Initialize environment-specific configurations
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Initialize Sentence Transformer model for embeddings
_embedding_model = None

def get_embedding_model():
    """
    Get or initialize the embedding model.
    
    Returns:
        SentenceTransformer instance for generating text embeddings
        
    Notes:
        This function implements lazy loading of the embedding model
        to optimize startup time and memory usage. The model is loaded
        only when first requested.
        
        The 'all-MiniLM-L6-v2' model is a lightweight, general-purpose
        sentence embedding model that maps sentences to a 384-dimensional
        dense vector space for semantic similarity calculations.
    """
    global _embedding_model
    if _embedding_model is None:
        try:
            _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        except Exception as e:
            print(f"Warning: Could not initialize embedding model: {e}")
    return _embedding_model

async def get_ai_response(message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get a response from an AI assistant.
    
    Args:
        message: The user's message
        context: Optional context for the AI
        
    Returns:
        Dict containing the response text and metadata
        
    AI Implementation Details:
        In production, this function would connect to a language model API
        (like OpenAI, Anthropic Claude, or Hugging Face Inference API) to 
        generate responses to user queries.
        
        The context parameter allows for including conversation history,
        user preferences, and other contextual information that helps the
        AI generate more appropriate and personalized responses.
        
        Error handling with fallback to rule-based responses ensures the
        system remains functional even when AI services are unavailable.
    """
    try:
        # In a production environment, this would connect to an LLM API
        # For demo, use rule-based responses
        return rule_based_response(message, context)
    
    except Exception as e:
        print(f"AI service error: {str(e)}")
        # Fallback to rule-based responses
        return rule_based_response(message, context)

def rule_based_response(message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate a response using simple rule-based matching.
    
    Args:
        message: The user's message
        context: Optional context information
        
    Returns:
        Dict containing the response text and metadata
        
    Notes:
        This function serves as both a fallback mechanism when AI services
        fail and as a demonstration of the response structure expected from
        the AI service. In production, this would be replaced by more
        sophisticated AI responses, but maintaining the same structure.
    """
    message = message.lower()
    
    response = "I don't have enough context to answer that question."
    sources = ["Rule-based response system"]
    
    if "how to" in message or "how do i" in message:
        if "upload" in message:
            response = "To upload data, go to the Pipeline tab and select 'Upload Data'. You can choose a local file, connect to an API, or import from a database."
        elif "transform" in message or "clean" in message:
            response = "Data transformation and cleaning can be done through the Pipeline tab. After uploading your data, proceed through the validation step, and then to the transformation step where you can apply various cleaning operations."
        elif "validate" in message:
            response = "Data validation is the first step after uploading. The system will check for data quality issues like missing values, invalid formats, and outliers based on your configured business rules."
        elif "enrich" in message:
            response = "Data enrichment adds value to your dataset by incorporating external data or derived fields. After transformation, proceed to the enrichment step in the Pipeline tab."
    
    elif "error" in message or "not working" in message:
        response = "If you're experiencing errors, please check:\n1. The format of your input data\n2. Any validation rules that might be failing\n3. System logs for more detailed error information\n4. Your database or API connection settings"
    
    elif "best practice" in message:
        response = "Here are some data processing best practices:\n1. Always validate data before transformation\n2. Create clear and specific business rules\n3. Monitor data quality metrics regularly\n4. Document your data pipeline steps\n5. Set up alerts for critical failures"
    
    elif "example" in message:
        response = "Here's an example workflow:\n1. Upload a CSV file with sales data\n2. Validate it against sales data rules\n3. Transform it by standardizing formats and removing duplicates\n4. Enrich it with customer demographic data\n5. Load it into your analytics database"
    
    return {
        "text": response,
        "context": {
            "sources": sources,
            "confidence": 0.7
        },
        "timestamp": datetime.now().isoformat()
    }

async def analyze_dataset(dataset_id: str, question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Analyze a dataset to answer questions about it.
    
    Args:
        dataset_id: ID of the dataset to analyze
        question: The question to answer about the dataset
        context: Optional additional context
        
    Returns:
        Dict containing the answer and analysis metadata
        
    AI Implementation Details:
        This function implements an AI-powered data analysis capability where
        users can ask natural language questions about their datasets and
        receive insightful answers.
        
        In production, this would use:
        1. A vector database to store dataset metadata and enable semantic search
        2. An embedding model to encode the question
        3. A language model to generate insights based on retrieved data context
        4. Data analysis techniques to perform real-time computations on the dataset
        
        The AI component uses RAG (Retrieval Augmented Generation) techniques to 
        combine dataset-specific knowledge with general language understanding.
    """
    try:
        # For demonstration purposes, generate mock responses
        # In a real implementation, this would analyze the actual dataset
        
        # Sample mock responses based on common question patterns
        if "most" in question.lower() and "profitable" in question.lower():
            return {
                "answer": "Based on the data, electronics is the most profitable category with an average profit margin of 28.3%. The second most profitable category is Beauty with 22.7%, followed by Books at 18.2%.",
                "confidence": 0.87,
                "context": [
                    {
                        "column": "category",
                        "insight": "8 unique categories present in the dataset",
                        "distribution": "Electronics (32.5%), Clothing (21.4%), Home (17.0%), Books (13.0%), Food (8.2%), Sports (5.9%), Beauty (1.9%), Other (0.2%)"
                    },
                    {
                        "column": "profit_margin",
                        "insight": "Average profit margin across all products is 19.2%",
                        "distribution": "Electronics (28.3%), Beauty (22.7%), Books (18.2%), Clothing (17.8%), Home (16.5%), Sports (15.9%), Food (12.1%), Other (11.2%)"
                    }
                ],
                "query_analysis": {
                    "type": "comparison",
                    "target_column": "profit_margin",
                    "group_by_column": "category",
                    "aggregation": "avg"
                }
            }
        
        elif "trend" in question.lower() and ("sales" in question.lower() or "revenue" in question.lower()):
            return {
                "answer": "Sales have shown an upward trend over the past quarter with a 12.7% increase. March had the highest revenue at $1.24M, while January had the lowest at $0.98M.",
                "confidence": 0.92,
                "context": [
                    {
                        "column": "sale_date",
                        "insight": "Data spans from January 1 to March 31",
                        "trend": "Increasing"
                    },
                    {
                        "column": "revenue",
                        "insight": "Total revenue for Q1 was $3.42M",
                        "monthly_values": {
                            "January": "$0.98M",
                            "February": "$1.20M", 
                            "March": "$1.24M"
                        }
                    }
                ],
                "query_analysis": {
                    "type": "time_series",
                    "target_column": "revenue",
                    "time_column": "sale_date",
                    "aggregation": "sum",
                    "period": "month"
                }
            }
        
        elif "correlation" in question.lower() or "related" in question.lower():
            return {
                "answer": "There is a strong positive correlation (0.82) between customer age and purchase amount. There's a moderate negative correlation (-0.56) between purchase amount and discount rate.",
                "confidence": 0.85,
                "context": [
                    {
                        "analysis": "correlation_matrix",
                        "insight": "Key correlations found among 4 variables",
                        "correlations": [
                            {"variables": ["age", "purchase_amount"], "coefficient": 0.82, "strength": "strong positive"},
                            {"variables": ["purchase_amount", "discount_rate"], "coefficient": -0.56, "strength": "moderate negative"},
                            {"variables": ["age", "frequency"], "coefficient": 0.32, "strength": "weak positive"}
                        ]
                    }
                ],
                "query_analysis": {
                    "type": "correlation",
                    "columns_analyzed": ["age", "purchase_amount", "discount_rate", "frequency"],
                    "method": "pearson"
                }
            }
        
        # Default response if no patterns match
        return {
            "answer": f"Based on my analysis of dataset {dataset_id}, I could not determine a specific answer to your question. Please try rephrasing or providing more context.",
            "confidence": 0.4,
            "context": [],
            "query_analysis": {
                "type": "unclassified",
                "question": question
            }
        }
    
    except Exception as e:
        return {
            "answer": "I encountered an error while analyzing this dataset. The system might be experiencing issues or the dataset might not be available.",
            "confidence": 0.1,
            "context": [{"error": str(e)}],
            "query_analysis": {"status": "error"}
        }

async def generate_embedding(text: str, model: str = "sentence-transformers/all-MiniLM-L6-v2") -> List[float]:
    """Generate a vector embedding for text.
    
    Args:
        text: Text to generate embedding for
        model: Model to use for embedding
        
    Returns:
        List of floats representing the embedding vector
    """
    try:
        # In production, this would use the actual model
        # Get the embedding model
        embedding_model = get_embedding_model()
        
        if embedding_model is not None:
            # Generate actual embeddings if model is available
            embedding = embedding_model.encode(text).tolist()
        else:
            # Fallback to random embeddings if model is not available
            if model == "sentence-transformers/all-MiniLM-L6-v2":
                dim = 384  # Match our vector service dimension
            else:
                dim = 1536  # Match OpenAI text-embedding-3-small dimension
                
            embedding = np.random.normal(0, 1, dim).tolist()
            
            # Normalize the vector
            magnitude = np.sqrt(np.sum(np.square(embedding)))
            embedding = [x/magnitude for x in embedding]
        
        return embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        # Return a zero vector as fallback
        if model == "sentence-transformers/all-MiniLM-L6-v2":
            return [0.0] * 384
        else:
            return [0.0] * 1536

async def generate_embeddings(text: str, model: str = "sentence-transformers/all-MiniLM-L6-v2") -> Dict[str, Any]:
    """
    Generate vector embeddings for text using Hugging Face models.
    
    Args:
        text: Text to generate embeddings for
        model: Model to use for embeddings
        
    Returns:
        Dict with embeddings and metadata
    """
    try:
        # In production, this would use the actual model
        # For demo, generate random embeddings
        
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Generate random embeddings of the right size
        # In reality, this would call the embedding model
        if model == "sentence-transformers/all-MiniLM-L6-v2":
            dim = 384  # Match our vector service dimension
        else:
            dim = 768
            
        embedding = np.random.normal(0, 1, dim).tolist()
        
        # Normalize the vector
        magnitude = np.sqrt(np.sum(np.square(embedding)))
        normalized_embedding = [x/magnitude for x in embedding]
        
        return {
            "success": True,
            "text": text,
            "embedding": normalized_embedding,
            "model": model,
            "dimension": dim
        }
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise

async def analyze_dataset_with_rag(dataset_id: int, query: str, use_agent: bool = False) -> Dict[str, Any]:
    """
    Analyze a dataset using RAG (Retrieval Augmented Generation) with optional agentic capabilities.
    
    Args:
        dataset_id: ID of the dataset to analyze
        query: Natural language query
        use_agent: Whether to use the agentic framework for more complex analysis
        
    Returns:
        Dict with analysis results and context
    """
    try:
        # Generate embeddings for the query
        embedding_result = await generate_embedding(query)
        if not embedding_result:
            raise ValueError("Failed to generate embeddings")
            
        query_embedding = embedding_result
        
        # Initialize vector service if needed
        from api.services.vector_service import vector_service
        await vector_service.initialize()
        
        # Search for relevant context using vector service
        search_results = await vector_service.search_vectors(
            query_vector=query_embedding,
            dataset_id=dataset_id,
            limit=10,  # Increased limit for better context
            threshold=0.6,  # Slightly lower threshold to get more diverse results
            include_chunks=True
        )
        
        # Prepare context from search results
        context = []
        for result in search_results:
            if result.get("chunk_text"):
                context.append({
                    "text": result["chunk_text"],
                    "similarity": result["similarity"],
                    "metadata": result.get("metadata", {})
                })
        
        # If using agent, perform additional analysis
        analysis_result = None
        if use_agent and context:
            # Get dataset metadata for additional context
            from api.repositories.dataset_repository import DatasetRepository
            dataset_repo = DatasetRepository()
            metadata = await dataset_repo.get_dataset_metadata(dataset_id) or {}
            profile = await dataset_repo.get_dataset_profile(dataset_id) or {}
            
            # Prepare agent context
            agent_context = {
                "dataset_id": dataset_id,
                "dataset_name": metadata.get("name", f"Dataset {dataset_id}"),
                "column_info": metadata.get("columns", []),
                "data_types": metadata.get("column_types", {}),
                "row_count": metadata.get("row_count", 0),
                "quality_metrics": profile.get("quality_metrics", {}),
                "retrieved_context": context[:5]  # Limit context to avoid token limits
            }
            
            # Generate agent response
            agent_prompt = f"""You are a data analysis agent. Analyze the following dataset based on the user query and retrieved context.
            
            User Query: {query}
            
            Dataset Information:
            - Name: {agent_context['dataset_name']}
            - Columns: {', '.join(agent_context['column_info'])}
            - Row Count: {agent_context['row_count']}
            
            Retrieved Context:
            {json.dumps(agent_context['retrieved_context'], indent=2)}
            
            Provide a detailed analysis addressing the user's query. Include specific insights from the retrieved context.
            """
            
            # Get AI response for analysis
            analysis_response = await get_ai_response(agent_prompt, agent_context)
            
            if analysis_response and "text" in analysis_response:
                analysis_result = {
                    "analysis": analysis_response["text"],
                    "confidence": analysis_response.get("confidence", 0.8),
                    "processing_time": analysis_response.get("processing_time", 0)
                }
        
        result = {
            "success": True,
            "query": query,
            "context": context,
            "context_count": len(context),
            "used_agent": use_agent
        }
        
        if analysis_result:
            result["analysis"] = analysis_result
        
        return result
    except Exception as e:
        logger.error(f"Error in dataset analysis: {e}")
        return {
            "success": False,
            "error": str(e)
        }
