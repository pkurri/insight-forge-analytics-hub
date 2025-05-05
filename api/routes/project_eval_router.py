"""Router for project-wide OpenEvals evaluation.

This router exposes endpoints for evaluating the entire project or specific components.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import time

from services.project_evaluator import project_evaluator
from ..config.openevals_config import ComponentType, EvaluationCategory

# Create router
router = APIRouter(prefix="/project-eval", tags=["Project Evaluation"])

# Request/Response models
class ComponentEvalRequest(BaseModel):
    component_type: ComponentType

class CustomizeThresholdRequest(BaseModel):
    category: EvaluationCategory
    threshold: int

class CustomizeCriteriaRequest(BaseModel):
    component_type: ComponentType
    categories: List[EvaluationCategory]

# Endpoints
@router.get("/components")
async def get_component_types():
    """Get available component types for evaluation."""
    from ..config.openevals_config import openevals_config
    return {
        "success": True,
        "data": [comp.value for comp in openevals_config.get_all_component_types()]
    }

@router.get("/categories")
async def get_eval_categories():
    """Get available evaluation categories."""
    from ..config.openevals_config import openevals_config
    return {
        "success": True,
        "data": [cat.value for cat in openevals_config.get_all_evaluation_categories()]
    }

@router.post("/component")
async def evaluate_component(request: ComponentEvalRequest, background_tasks: BackgroundTasks):
    """Evaluate a specific component type."""
    try:
        # Start evaluation in background if it might take long
        background_tasks.add_task(project_evaluator.evaluate_component, request.component_type)
        
        return {
            "success": True,
            "message": f"Evaluation of {request.component_type} started in background.",
            "data": {
                "component_type": request.component_type,
                "status": "processing"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/all")
async def evaluate_all(background_tasks: BackgroundTasks):
    """Evaluate all components in the project."""
    try:
        # Start evaluation in background as it will take time
        background_tasks.add_task(project_evaluator.evaluate_all)
        
        return {
            "success": True,
            "message": "Full project evaluation started in background.",
            "data": {
                "status": "processing"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scores")
async def get_component_scores():
    """Get latest scores for all components."""
    try:
        scores = project_evaluator.get_component_scores()
        return {
            "success": True,
            "data": scores
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/last-full-evaluation")
async def get_last_full_evaluation():
    """Get results of the last full project evaluation."""
    try:
        result = project_evaluator.get_last_full_evaluation()
        if not result:
            return {
                "success": True,
                "data": None,
                "message": "No full evaluation has been performed yet."
            }
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/improvement-plan/{evaluation_id}")
async def generate_improvement_plan(evaluation_id: str):
    """Generate improvement plan based on evaluation results."""
    try:
        plan = await project_evaluator.generate_improvement_plan(evaluation_id)
        if "error" in plan:
            raise HTTPException(status_code=404, detail=plan["error"])
        return {
            "success": True,
            "data": plan
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/customize/threshold")
async def customize_threshold(request: CustomizeThresholdRequest):
    """Customize evaluation threshold for a category."""
    try:
        from ..config.openevals_config import openevals_config
        openevals_config.customize_threshold(request.category, request.threshold)
        return {
            "success": True,
            "message": f"Threshold for {request.category} updated to {request.threshold}",
            "data": {
                "category": request.category,
                "threshold": request.threshold
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/customize/criteria")
async def customize_criteria(request: CustomizeCriteriaRequest):
    """Customize evaluation criteria for a component type."""
    try:
        from ..config.openevals_config import openevals_config
        openevals_config.customize_criteria(request.component_type, request.categories)
        return {
            "success": True,
            "message": f"Criteria for {request.component_type} updated",
            "data": {
                "component_type": request.component_type,
                "categories": [cat.value for cat in request.categories]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
