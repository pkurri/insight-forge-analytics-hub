from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import time
import os

from services.openevals_service import OpenEvalsService
from config.openevals_config import ComponentType, EvaluationCategory

class RuntimeComponentRequest(BaseModel):
    component_name: str
    component_type: Optional[str] = None
    code_content: Optional[str] = None

class SuggestionRequest(BaseModel):
    component_name: str
    suggestion_id: Optional[str] = None

router = APIRouter(
    prefix="/openevals/runtime",
    tags=["openevals-runtime"],
    responses={404: {"description": "Not found"}},
)

@router.post("/evaluate")
async def evaluate_runtime_component(
    request: RuntimeComponentRequest,
    background_tasks: BackgroundTasks,
    openevals_service: OpenEvalsService = Depends()
):
    """Evaluate a component's code quality at runtime."""
    try:
        # Find the component's code content if not provided
        if not request.code_content:
            # Try to find the component in the codebase
            component_path = await find_component_path(request.component_name)
            if not component_path:
                raise HTTPException(status_code=404, detail=f"Component '{request.component_name}' not found in codebase")
            
            with open(component_path, "r") as file:
                request.code_content = file.read()
        
        # Determine component type if not provided
        if not request.component_type:
            component_type = determine_component_type(component_path)
        else:
            component_type = request.component_type
        
        # Run the evaluation
        result = await openevals_service.evaluate_code(
            code=request.code_content,
            component_name=request.component_name,
            component_type=component_type,
            evaluation_type="runtime"
        )
        
        # Store results for later retrieval
        runtime_suggestions = {
            "component_name": request.component_name,
            "timestamp": time.time(),
            "score": result.get("score", 0),
            "suggestions": result.get("improvement_suggestions", []),
            "component_type": component_type,
            "status": "ready"
        }
        
        # Save suggestions to a file
        suggestion_id = f"{request.component_name}_{int(time.time())}"
        save_runtime_suggestions(suggestion_id, runtime_suggestions)
        
        return {
            "success": True,
            "data": {
                "score": result.get("score", 0),
                "component_name": request.component_name,
                "component_type": component_type,
                "has_suggestions": len(result.get("improvement_suggestions", [])) > 0,
                "suggestion_id": suggestion_id,
                "status": "completed"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/suggestions")
async def get_component_suggestions(
    request: SuggestionRequest,
    openevals_service: OpenEvalsService = Depends()
):
    """Get improvement suggestions for a component."""
    try:
        if not request.suggestion_id:
            # Find the latest suggestion for this component
            suggestion_id, suggestions = get_latest_suggestion(request.component_name)
        else:
            suggestion_id = request.suggestion_id
            suggestions = load_suggestion(suggestion_id)
        
        if not suggestions:
            raise HTTPException(status_code=404, detail=f"No suggestions found for component '{request.component_name}'")
        
        return {
            "success": True,
            "data": {
                "suggestion_id": suggestion_id,
                "component_name": request.component_name,
                "score": suggestions.get("score", 0),
                "suggestions": suggestions.get("suggestions", []),
                "component_type": suggestions.get("component_type", "UI")
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/apply")
async def apply_component_suggestions(
    request: SuggestionRequest,
    openevals_service: OpenEvalsService = Depends()
):
    """Apply improvement suggestions to a component."""
    try:
        if not request.suggestion_id:
            raise HTTPException(status_code=400, detail="Suggestion ID is required")
        
        # Load the suggestion
        suggestions = load_suggestion(request.suggestion_id)
        if not suggestions:
            raise HTTPException(status_code=404, detail=f"Suggestion with ID '{request.suggestion_id}' not found")
        
        # Find the component path
        component_path = await find_component_path(request.component_name)
        if not component_path:
            raise HTTPException(status_code=404, detail=f"Component '{request.component_name}' not found in codebase")
        
        # Generate improved code
        improved_code = await openevals_service.generate_improved_code(
            original_code=suggestions.get("original_code", ""),
            component_name=request.component_name,
            component_type=suggestions.get("component_type", "UI"),
            suggestions=suggestions.get("suggestions", [])
        )
        
        # Backup original file
        backup_file(component_path)
        
        # Apply the improved code
        with open(component_path, "w") as file:
            file.write(improved_code)
        
        # Mark suggestion as applied
        suggestions["status"] = "applied"
        suggestions["applied_at"] = time.time()
        save_suggestion(request.suggestion_id, suggestions)
        
        return {
            "success": True,
            "data": {
                "message": f"Improvements applied to {request.component_name}",
                "component_name": request.component_name,
                "component_path": component_path
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def find_component_path(component_name: str) -> Optional[str]:
    """Find the file path for a component by name."""
    # Define common directories to search for components
    search_dirs = [
        os.path.join(os.getcwd(), "src", "components"),
        os.path.join(os.getcwd(), "src", "dashboard", "components"),
        os.path.join(os.getcwd(), "src", "analytics", "components")
    ]
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for root, _, files in os.walk(search_dir):
                for file in files:
                    if file.endswith(".tsx") or file.endswith(".jsx"):
                        file_path = os.path.join(root, file)
                        # Check if the component name is in the file
                        with open(file_path, "r") as f:
                            content = f.read()
                            if f"const {component_name}" in content or f"class {component_name}" in content:
                                return file_path
    return None

def determine_component_type(file_path: str) -> str:
    """Determine the component type based on the file path."""
    if "dashboard" in file_path:
        return ComponentType.DASHBOARD.value
    elif "analytics" in file_path:
        return ComponentType.ANALYTICS.value
    elif "pipeline" in file_path:
        return ComponentType.PIPELINE.value
    elif "ai" in file_path:
        return ComponentType.AI.value
    elif "ui" in file_path:
        return ComponentType.UI.value
    else:
        return ComponentType.UI.value

def save_runtime_suggestions(suggestion_id: str, suggestions: Dict) -> None:
    """Save runtime suggestions to a file."""
    suggestions_dir = os.path.join(os.getcwd(), "data", "openevals", "runtime")
    os.makedirs(suggestions_dir, exist_ok=True)
    
    file_path = os.path.join(suggestions_dir, f"{suggestion_id}.json")
    with open(file_path, "w") as file:
        json.dump(suggestions, file, indent=2)

def save_suggestion(suggestion_id: str, suggestions: Dict) -> None:
    """Save or update a suggestion."""
    suggestions_dir = os.path.join(os.getcwd(), "data", "openevals", "runtime")
    os.makedirs(suggestions_dir, exist_ok=True)
    
    file_path = os.path.join(suggestions_dir, f"{suggestion_id}.json")
    with open(file_path, "w") as file:
        json.dump(suggestions, file, indent=2)

def load_suggestion(suggestion_id: str) -> Optional[Dict]:
    """Load a suggestion by ID."""
    file_path = os.path.join(os.getcwd(), "data", "openevals", "runtime", f"{suggestion_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)
    return None

def get_latest_suggestion(component_name: str) -> tuple[Optional[str], Optional[Dict]]:
    """Get the latest suggestion for a component."""
    suggestions_dir = os.path.join(os.getcwd(), "data", "openevals", "runtime")
    if not os.path.exists(suggestions_dir):
        return None, None
    
    # Filter files for this component
    component_files = [
        f for f in os.listdir(suggestions_dir) 
        if f.startswith(f"{component_name}_") and f.endswith(".json")
    ]
    
    if not component_files:
        return None, None
    
    # Sort by timestamp (part after the underscore)
    sorted_files = sorted(
        component_files, 
        key=lambda x: int(x.split("_")[1].split(".")[0]),
        reverse=True
    )
    
    latest_file = sorted_files[0]
    suggestion_id = latest_file.split(".")[0]
    
    # Load the suggestion
    file_path = os.path.join(suggestions_dir, latest_file)
    with open(file_path, "r") as file:
        return suggestion_id, json.load(file)

def backup_file(file_path: str) -> None:
    """Create a backup of a file before modifying it."""
    backup_dir = os.path.join(os.getcwd(), "data", "openevals", "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate backup filename with timestamp
    filename = os.path.basename(file_path)
    backup_path = os.path.join(backup_dir, f"{filename}.{int(time.time())}.bak")
    
    # Copy file content
    with open(file_path, "r") as src, open(backup_path, "w") as dst:
        dst.write(src.read())
