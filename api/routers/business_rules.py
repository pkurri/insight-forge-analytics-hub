"""
Business Rules Router

This module provides API endpoints for managing AI-generated business rules.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from api.services.ai_agent_service import generate_business_rules, get_chat_suggestions
from api.auth import get_current_user

router = APIRouter()

class BusinessRuleRequest(BaseModel):
    """Request model for generating business rules"""
    dataset_id: str
    model_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class BusinessRuleResponse(BaseModel):
    """Response model for business rules"""
    success: bool
    rules: List[Dict[str, Any]]
    dataset_id: str
    generated_at: str
    error: Optional[str] = None

@router.post("/generate", response_model=BusinessRuleResponse)
async def generate_rules(
    request: BusinessRuleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate business rules for a dataset using AI
    
    Args:
        request: BusinessRuleRequest containing dataset_id and optional model_id and context
        
    Returns:
        BusinessRuleResponse with generated rules or error
    """
    try:
        result = await generate_business_rules(
            dataset_id=request.dataset_id,
            model_id=request.model_id,
            context=request.context
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Failed to generate business rules')
            )
            
        return BusinessRuleResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating business rules: {str(e)}"
        )

@router.get("/suggestions", response_model=List[Dict[str, Any]])
async def get_rule_suggestions(
    dataset_id: Optional[str] = Query(None, description="Dataset ID to get suggestions for"),
    category: Optional[str] = Query(None, description="Filter suggestions by category"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get suggested business rules for a dataset
    
    Args:
        dataset_id: Optional dataset ID to get specific suggestions for
        category: Optional category to filter suggestions
        
    Returns:
        List of suggested business rules
    """
    try:
        suggestions = await get_chat_suggestions(
            dataset_id=dataset_id,
            category=category,
            include_rules=True
        )
        
        # Filter for business rules category
        rule_suggestions = [
            s for s in suggestions 
            if s.get('category') == 'business_rules'
        ]
        
        return rule_suggestions[:5]  # Return top 5 rule suggestions
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting rule suggestions: {str(e)}"
        )
