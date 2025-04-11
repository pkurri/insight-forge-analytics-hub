
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, Optional, List

from api.routes.auth_router import get_current_user_or_api_key
from api.services.ai_service import get_ai_response, analyze_dataset

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

@router.post("/recommend-actions/{dataset_id}", response_model=Dict[str, Any])
async def recommend_actions(
    dataset_id: str,
    analysis_type: str = Body(..., description="Type of analysis to base recommendations on"),
    context: Dict[str, Any] = Body({}, description="Additional context"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Get AI-powered recommendations for actions based on dataset analysis."""
    try:
        # This would call an AI service to generate recommendations
        # For now, return mock recommendations
        return {
            "dataset_id": dataset_id,
            "recommendations": [
                {
                    "action": "Clean missing values in 'customer_email' column",
                    "priority": "high",
                    "impact": "Improves data quality by 8.5%",
                    "effort": "low",
                    "details": "23 rows (2.3%) have missing or invalid email formats"
                },
                {
                    "action": "Investigate outliers in 'transaction_amount' column",
                    "priority": "medium",
                    "impact": "Potential fraud detection",
                    "effort": "medium",
                    "details": "5 transactions exceed 3σ from the mean"
                },
                {
                    "action": "Standardize values in 'product_category' column",
                    "priority": "medium",
                    "impact": "Improves reporting accuracy",
                    "effort": "low",
                    "details": "Multiple variations of the same category found ('electronics', 'Electronics', 'ELECTRONICS')"
                }
            ],
            "analysis_context": {
                "analysis_type": analysis_type,
                "insights_used": ["data profile", "anomaly detection", "business rules"],
                "confidence": 0.87
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")
