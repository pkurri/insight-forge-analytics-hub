from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Body
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import pandas as pd
import json
from datetime import datetime

# Import services
from ..services.openevals_service import openevals_service, EvalType, EvalStatus
from ..services.dataset_metadataset_processor import get_dataset_metadataset, process_dataset_metadataset
from ..services.business_rules_service import BusinessRulesService

# Create router
router = APIRouter(prefix="/openevals", tags=["OpenEvals"])

# Initialize services
business_rules_service = BusinessRulesService()

@router.post("/business-rules/evaluate/{dataset_metadataset_id}")
async def evaluate_business_rules(dataset_metadataset_id: str):
    """
    Evaluate business rules for a dataset_metadataset
    """
    try:
        # Get dataset_metadataset
        dataset_metadataset_info = await get_dataset_metadataset(dataset_metadataset_id)
        if not dataset_metadataset_info:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_metadataset_id} not found")
        
        # Load dataset_metadataset
        file_path = dataset_metadataset_info.get("file_path")
        if not file_path:
            raise HTTPException(status_code=404, detail="Dataset file not found")
        
        # Read dataset_metadataset
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".json"):
            df = pd.read_json(file_path)
        elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            df = pd.read_excel(file_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_path}")
        
        # Evaluate business rules
        evaluation = await openevals_service.evaluate_business_rules(dataset_metadataset_id, df, dataset_metadataset_info.get("dataset_metadata", {}))
        
        return {"success": True, "dataset_metadata": evaluation}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/business-rules/generate/{dataset_metadataset_id}")
async def generate_business_rules_with_openeval(dataset_metadataset_id: str, request: Request):
    # Extract engine parameter from request body
    body = await request.json()
    engine = body.get("engine", "ai_default")
    """
    Generate business rules with OpenEvals for a dataset_metadataset
    """
    try:
        # Get dataset_metadataset
        dataset_metadataset_info = await get_dataset_metadataset(dataset_metadataset_id)
        if not dataset_metadataset_info:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_metadataset_id} not found")
        
        # Get dataset_metadatadataset_metadata
        ds_metadataset_metadata = dataset_metadataset_info.get("dataset_metadata", {})
        
        # Load dataset_metadataset for validation
        file_path = dataset_metadataset_info.get("file_path")
        if not file_path:
            raise HTTPException(status_code=404, detail="Dataset file not found")
        
        # Read dataset_metadataset (sample)
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path, nrows=100)  # Limit to 100 rows for validation
        elif file_path.endswith(".json"):
            df = pd.read_json(file_path)
            df = df.head(100) if len(df) > 100 else df
        elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            df = pd.read_excel(file_path, nrows=100)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_path}")
        
        # Generate rules with OpenEvals using the specified engine
        result = await openevals_service.generate_business_rules_with_openeval(
            dataset_metadataset_id=dataset_metadataset_id,
            ds_metadataset_metadata=ds_metadataset_metadata,
            dataset_metadata_sample=df,
            engine=engine
        )
        
        return {"success": True, "dataset_metadata": result}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dataset_metadata-quality/{dataset_metadataset_id}")
async def evaluate_dataset_metadata_quality(dataset_metadataset_id: str):
    """
    Evaluate dataset_metadata quality for a dataset_metadataset
    """
    try:
        # Get dataset_metadataset
        dataset_metadataset_info = await get_dataset_metadataset(dataset_metadataset_id)
        if not dataset_metadataset_info:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_metadataset_id} not found")
        
        # Load dataset_metadataset
        file_path = dataset_metadataset_info.get("file_path")
        if not file_path:
            raise HTTPException(status_code=404, detail="Dataset file not found")
        
        # Read dataset_metadataset
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".json"):
            df = pd.read_json(file_path)
        elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            df = pd.read_excel(file_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_path}")
        
        # Evaluate dataset_metadata quality
        evaluation = await openevals_service.evaluate_dataset_metadata_quality(dataset_metadataset_id, df, dataset_metadataset_info.get("dataset_metadata", {}))
        
        return {"success": True, "dataset_metadata": evaluation}
    
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
        
        return {"success": True, "dataset_metadata": evaluation}
    
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
        return {"success": True, "dataset_metadata": history}
    
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
        
        return {"success": True, "dataset_metadata": evaluation}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
