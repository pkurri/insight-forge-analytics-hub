
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
    import openai
    from sentence_transformers import SentenceTransformer
except ImportError:
    pass  # Handle gracefully in production code

# Initialize environment-specific configurations
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")  # Default to gpt-4o-mini
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Initialize Sentence Transformer model for embeddings
_embedding_model = None

def get_embedding_model():
    """Get or initialize the embedding model."""
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
    """
    try:
        # If OpenAI API key is available, use it
        if OPENAI_API_KEY:
            openai.api_key = OPENAI_API_KEY
            
            # Construct the message payload
            system_message = "You are an AI assistant for a data processing platform. Answer questions about data processing, pipelines, analytics, and data quality."
            
            # Add context to system message if provided
            if context:
                context_str = json.dumps(context, indent=2)
                system_message += f"\n\nContext:\n{context_str}"
            
            # Call OpenAI API
            completion = await openai.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": message}
                ]
            )
            
            response_text = completion.choices[0].message.content
            
            return {
                "text": response_text,
                "context": {
                    "sources": ["OpenAI API response"],
                    "model": AI_MODEL,
                    "confidence": 0.9
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Fallback to rule-based responses
            return rule_based_response(message, context)
    
    except Exception as e:
        print(f"AI service error: {str(e)}")
        # Fallback to rule-based responses
        return rule_based_response(message, context)

def rule_based_response(message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate a response using simple rule-based matching."""
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
        "timestamp": datetime.utcnow().isoformat()
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

async def generate_business_rules(dataset, columns) -> List[Dict[str, Any]]:
    """
    Generate business rules for a dataset using AI.
    This is a mock implementation.
    """
    # Wait to simulate processing time
    await asyncio.sleep(2)
    
    # Sample generated rules
    rules = [
        {
            "id": "auto-1",
            "name": "Price Range",
            "condition": "data['price'] >= 0 and data['price'] <= 2000",
            "severity": "high",
            "message": "Price must be between 0 and 2000",
            "confidence": 0.95,
            "model_generated": True
        },
        {
            "id": "auto-2",
            "name": "Valid Stock",
            "condition": "data['stock'] >= 0",
            "severity": "high",
            "message": "Stock cannot be negative",
            "confidence": 0.99,
            "model_generated": True
        },
        {
            "id": "auto-3",
            "name": "Rating Range",
            "condition": "data['rating'] >= 1 and data['rating'] <= 5",
            "severity": "medium",
            "message": "Rating must be between 1 and 5",
            "confidence": 0.98,
            "model_generated": True
        },
        {
            "id": "auto-4",
            "name": "Category Check",
            "condition": "data['category'] in ['Electronics', 'Clothing', 'Home', 'Books', 'Food', 'Sports', 'Beauty', 'Other']",
            "severity": "medium",
            "message": "Category must be from approved list",
            "confidence": 0.96,
            "model_generated": True
        },
        {
            "id": "auto-5",
            "name": "Price-Stock Correlation",
            "condition": "data['price'] < 100 or data['stock'] >= 5",
            "severity": "low",
            "message": "High-priced items should maintain minimum stock",
            "confidence": 0.82,
            "model_generated": True
        }
    ]
    
    return rules
