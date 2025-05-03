from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Body
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import pandas as pd
import json
from datetime import datetime

# Import services
from ..services.openevals_service import openevals_service, EvalType, EvalStatus
from ..services.dataset_processor import get_dataset, process_dataset
from ..services.business_rules_service import BusinessRulesService

# Create router
router = APIRouter(prefix="/openevals", tags=["OpenEvals"])

# Initialize services
business_rules_service = BusinessRulesService()

@router.post("/business-rules/evaluate/{dataset_id}")
async def evaluate_business_rules(dataset_id: str):
    """
    Evaluate business rules for a dataset
    """
    try:
        # Get dataset
        dataset_info = await get_dataset(dataset_id)
        if not dataset_info:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
        
        # Load dataset
        file_path = dataset_info.get("file_path")
        if not file_path:
            raise HTTPException(status_code=404, detail="Dataset file not found")
        
        # Read dataset
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".json"):
            df = pd.read_json(file_path)
        elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            df = pd.read_excel(file_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_path}")
        
        # Evaluate business rules
        evaluation = await openevals_service.evaluate_business_rules(dataset_id, df)
        
        return {"success": True, "data": evaluation}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/business-rules/generate/{dataset_id}")
async def generate_business_rules_with_openeval(dataset_id: str):
    """
    Generate business rules with OpenEvals for a dataset
    """
    try:
        # Get dataset
        dataset_info = await get_dataset(dataset_id)
        if not dataset_info:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
        
        # Get column metadata
        column_metadata = dataset_info.get("statistics", {})
        
        # Load dataset for validation
        file_path = dataset_info.get("file_path")
        if not file_path:
            raise HTTPException(status_code=404, detail="Dataset file not found")
        
        # Read dataset (sample)
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path, nrows=100)  # Limit to 100 rows for validation
        elif file_path.endswith(".json"):
            df = pd.read_json(file_path)
            df = df.head(100) if len(df) > 100 else df
        elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            df = pd.read_excel(file_path, nrows=100)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_path}")
        
        # Generate rules with OpenEvals
        result = await openevals_service.generate_business_rules_with_openeval(
            dataset_id=dataset_id,
            column_metadata=column_metadata,
            data_sample=df
        )
        
        return {"success": True, "data": result}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data-quality/{dataset_id}")
async def evaluate_data_quality(dataset_id: str):
    """
    Evaluate data quality for a dataset
    """
    try:
        # Get dataset
        dataset_info = await get_dataset(dataset_id)
        if not dataset_info:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
        
        # Load dataset
        file_path = dataset_info.get("file_path")
        if not file_path:
            raise HTTPException(status_code=404, detail="Dataset file not found")
        
        # Read dataset
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".json"):
            df = pd.read_json(file_path)
        elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            df = pd.read_excel(file_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_path}")
        
        # Evaluate data quality
        evaluation = await openevals_service.evaluate_data_quality(dataset_id, df)
        
        return {"success": True, "data": evaluation}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai-response/evaluate")
async def evaluate_ai_response(request: Dict[str, Any] = Body(...)):
    """
    Evaluate an AI response for accuracy and consistency
    """
    try:
        query = request.get("query")
        response = request.get("response")
        facts = request.get("facts")
        
        if not query or not response:
            raise HTTPException(status_code=400, detail="Query and response are required")
        
        # Evaluate AI response
        evaluation = await openevals_service.evaluate_agent_response(query, response, facts)
        
        return {"success": True, "data": evaluation}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_evaluation_history(eval_type: Optional[str] = None, limit: int = 100):
    """
    Get evaluation history
    """
    try:
        history = await openevals_service.get_evaluation_history(eval_type, limit)
        return {"success": True, "data": history}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{eval_id}")
async def get_evaluation(eval_id: str):
    """
    Get a specific evaluation by ID
    """
    try:
        evaluation = await openevals_service.get_evaluation(eval_id)
        if not evaluation:
            raise HTTPException(status_code=404, detail=f"Evaluation {eval_id} not found")
        
        return {"success": True, "data": evaluation}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))}
