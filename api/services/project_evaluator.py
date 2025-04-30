"""Project-wide OpenEvals evaluator.

This service applies OpenEvals to entire project codebase, including UI and API components.
"""

import os
import glob
import json
import time
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum

# Import OpenEvals config and service
from ..config.openevals_config import openevals_config, ComponentType, EvaluationCategory
from .openevals_service import openevals_service, EvalType, EvalStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectEvaluator:
    """Service for evaluating the entire project codebase."""
    
    def __init__(self):
        """Initialize project evaluator."""
        self.project_root = openevals_config.project_root
        self.evaluation_history = {}
        self.component_scores = {}
        self.last_full_evaluation = None
        
        # Create logs directory if it doesn't exist
        self.logs_path = os.path.join(self.project_root, "logs", "project_evaluations")
        os.makedirs(self.logs_path, exist_ok=True)
    
    def _resolve_file_patterns(self, patterns: List[str]) -> List[str]:
        """Resolve glob patterns to actual file paths."""
        resolved_files = []
        for pattern in patterns:
            full_pattern = os.path.join(self.project_root, pattern)
            files = glob.glob(full_pattern, recursive=True)
            resolved_files.extend(files)
        return list(set(resolved_files))  # Remove duplicates
    
    def _get_component_files(self, component_type: ComponentType) -> List[str]:
        """Get all files for a specific component type."""
        patterns = openevals_config.get_file_patterns(component_type)
        return self._resolve_file_patterns(patterns)
    
    def _get_file_content(self, file_path: str) -> str:
        """Read file content from path."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return ""
    
    def _determine_file_type(self, file_path: str) -> str:
        """Determine file type based on extension."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".py"]:
            return "python"
        elif ext in [".js", ".jsx", ".ts", ".tsx"]:
            return "javascript"
        elif ext in [".css", ".scss", ".sass"]:
            return "css"
        elif ext in [".html", ".htm"]:
            return "html"
        elif ext in [".json"]:
            return "json"
        elif ext in [".md", ".markdown"]:
            return "markdown"
        elif ext in [".yml", ".yaml"]:
            return "yaml"
        else:
            return "text"
    
    async def evaluate_file(self, file_path: str, categories: List[EvaluationCategory]) -> Dict[str, Any]:
        """Evaluate a single file against specified categories."""
        file_content = self._get_file_content(file_path)
        if not file_content:
            return {
                "file": file_path,
                "status": EvalStatus.ERROR,
                "scores": {},
                "average_score": 0,
                "error": "Could not read file content"
            }
        
        rel_path = os.path.relpath(file_path, self.project_root)
        file_type = self._determine_file_type(file_path)
        
        # Prepare evaluation prompt
        categories_str = ", ".join([cat.value for cat in categories])
        evaluation_prompt = f"""Evaluate the following {file_type} code for quality in these categories: {categories_str}.

File path: {rel_path}

Code content:
```{file_type}
{file_content[:20000]}  # Limiting to 20K chars to avoid token limits
```

For each category, provide a score from 0-100 and brief explanation.
Format your response as:

Category: Score
Explanation

Category: Score
Explanation

Provide specific improvement suggestions for any category scoring below threshold.
"""
        
        try:
            # Get evaluation from OpenEvals service
            start_time = time.time()
            result = await openevals_service._get_ai_evaluation(evaluation_prompt)
            scores = openevals_service._extract_scores(result)
            
            # Calculate average score
            if scores:
                avg_score = sum(scores.values()) / len(scores)
            else:
                avg_score = 0
            
            # Extract improvement suggestions
            suggestions = []
            for line in result.split("\n"):
                if "suggestion" in line.lower() or "improve" in line.lower() or "should" in line.lower():
                    suggestions.append(line.strip())
            
            # Determine overall status based on thresholds
            status = EvalStatus.PASS
            for category in categories:
                threshold = openevals_config.get_category_threshold(category)
                category_score = scores.get(category.value, 0)
                if category_score < threshold:
                    status = EvalStatus.FAIL
                    break
            
            return {
                "file": rel_path,
                "status": status,
                "scores": scores,
                "average_score": avg_score,
                "suggestions": suggestions,
                "execution_time": time.time() - start_time
            }
        
        except Exception as e:
            logger.error(f"Error evaluating file {rel_path}: {e}")
            return {
                "file": rel_path,
                "status": EvalStatus.ERROR,
                "scores": {},
                "average_score": 0,
                "error": str(e)
            }
    
    async def evaluate_component(self, component_type: ComponentType) -> Dict[str, Any]:
        """Evaluate all files for a specific component type."""
        eval_id = f"{component_type}_{datetime.datetime.now().isoformat()}"
        files = self._get_component_files(component_type)
        categories = openevals_config.get_component_criteria(component_type)
        
        if not files:
            logger.warning(f"No files found for component type {component_type}")
            return {
                "id": eval_id,
                "component_type": component_type,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": EvalStatus.ERROR,
                "error": "No files found for this component type",
                "files_evaluated": 0,
                "average_score": 0,
                "category_scores": {},
                "dataset_metadata": {}
            }
        
        logger.info(f"Evaluating {len(files)} files for component {component_type}")
        
        # Evaluate each file
        file_evaluations = []
        for file_path in files:
            file_eval = await self.evaluate_file(file_path, categories)
            file_evaluations.append(file_eval)
        
        # Aggregate scores by category
        category_scores = {}
        for cat in categories:
            cat_scores = [eval["scores"].get(cat.value, 0) for eval in file_evaluations if eval["scores"]]
            if cat_scores:
                category_scores[cat.value] = sum(cat_scores) / len(cat_scores)
        
        # Calculate component average score
        if category_scores:
            component_avg = sum(category_scores.values()) / len(category_scores)
        else:
            component_avg = 0
        
        # Determine overall status
        status = EvalStatus.PASS
        for cat in categories:
            threshold = openevals_config.get_category_threshold(cat)
            if category_scores.get(cat.value, 0) < threshold:
                status = EvalStatus.FAIL
                break
        
        # Count files by status
        status_counts = {}
        for eval in file_evaluations:
            status_counts[eval["status"]] = status_counts.get(eval["status"], 0) + 1
        
        result = {
            "id": eval_id,
            "component_type": component_type,
            "timestamp": datetime.datetime.now().isoformat(),
            "status": status,
            "files_evaluated": len(file_evaluations),
            "average_score": component_avg,
            "category_scores": category_scores,
            "status_counts": status_counts,
            "file_evaluations": file_evaluations,
            "dataset_metadata": {}
        }
        
        # Store evaluation result
        self.evaluation_history[eval_id] = result
        self.component_scores[component_type] = {
            "average_score": component_avg,
            "category_scores": category_scores,
            "last_evaluation": datetime.datetime.now().isoformat(),
            "dataset_metadata": {}
        }
        
        # Save to log file
        self._save_evaluation_log(result)
        
        return result
    
    async def evaluate_all(self) -> Dict[str, Any]:
        """Evaluate all components in the project."""
        start_time = time.time()
        eval_id = f"full_evaluation_{datetime.datetime.now().isoformat()}"
        
        all_components = openevals_config.get_all_component_types()
        component_evaluations = {}
        overall_scores = {}
        
        for component_type in all_components:
            logger.info(f"Evaluating component type: {component_type}")
            eval_result = await self.evaluate_component(component_type)
            component_evaluations[component_type] = eval_result
            overall_scores[component_type] = eval_result["average_score"]
        
        # Calculate project-wide average
        if overall_scores:
            project_avg = sum(overall_scores.values()) / len(overall_scores)
        else:
            project_avg = 0
        
        # Determine overall status
        failing_components = [c for c, e in component_evaluations.items() if e["status"] == EvalStatus.FAIL]
        status = EvalStatus.PASS if not failing_components else EvalStatus.FAIL
        
        result = {
            "id": eval_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "status": status,
            "average_score": project_avg,
            "component_scores": overall_scores,
            "failing_components": failing_components,
            "execution_time": time.time() - start_time,
            "component_evaluations": component_evaluations,
            "pipeline_metadata": {}
        }
        
        self.last_full_evaluation = result
        self._save_evaluation_log(result, is_full=True)
        
        return result
    
    def _save_evaluation_log(self, evaluation: Dict[str, Any], is_full: bool = False) -> None:
        """Save evaluation log to file."""
        try:
            prefix = "full" if is_full else evaluation.get("component_type", "component")
            filename = f"{prefix}_eval_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path = os.path.join(self.logs_path, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(evaluation, f, indent=2)
                
            logger.info(f"Saved evaluation log to {file_path}")
        except Exception as e:
            logger.error(f"Error saving evaluation log: {e}")
    
    def get_component_scores(self) -> Dict[str, Any]:
        """Get latest scores for all components."""
        return self.component_scores
    
    def get_last_full_evaluation(self) -> Optional[Dict[str, Any]]:
        """Get results of the last full project evaluation."""
        return self.last_full_evaluation
    
    def get_evaluation_history(self, component_type: Optional[ComponentType] = None) -> List[Dict[str, Any]]:
        """Get evaluation history, optionally filtered by component type."""
        if component_type:
            return [eval for eval in self.evaluation_history.values() 
                    if eval.get("component_type") == component_type]
        return list(self.evaluation_history.values())
    
    async def generate_improvement_plan(self, evaluation_id: str) -> Dict[str, Any]:
        """Generate improvement plan based on evaluation results."""
        evaluation = self.evaluation_history.get(evaluation_id)
        if not evaluation:
            return {"error": "Evaluation not found"}
        
        # If it's a component evaluation
        if "component_type" in evaluation:
            component_type = evaluation["component_type"]
            categories = openevals_config.get_component_criteria(ComponentType(component_type))
            failing_categories = []
            
            for cat in categories:
                threshold = openevals_config.get_category_threshold(cat)
                score = evaluation["category_scores"].get(cat.value, 0)
                if score < threshold:
                    failing_categories.append({
                        "category": cat.value,
                        "score": score,
                        "threshold": threshold,
                        "gap": threshold - score
                    })
            
            # Collect low-scoring files with their suggestions
            problematic_files = []
            for file_eval in evaluation["file_evaluations"]:
                if file_eval["status"] != EvalStatus.PASS:
                    problematic_files.append({
                        "file": file_eval["file"],
                        "score": file_eval["average_score"],
                        "suggestions": file_eval.get("suggestions", [])
                    })
            
            # Sort by score (ascending)
            problematic_files.sort(key=lambda x: x["score"])
            
            return {
                "evaluation_id": evaluation_id,
                "component_type": component_type,
                "failing_categories": failing_categories,
                "problematic_files": problematic_files[:10],  # Top 10 worst files
                "improvement_priority": "high" if evaluation["status"] == EvalStatus.FAIL else "medium"
            }
        
        # If it's a full project evaluation
        else:
            component_priorities = []
            for component, score in evaluation["component_scores"].items():
                threshold = 85  # Default threshold for components
                if score < threshold:
                    component_priorities.append({
                        "component": component,
                        "score": score,
                        "threshold": threshold,
                        "gap": threshold - score
                    })
            
            # Sort by gap (descending)
            component_priorities.sort(key=lambda x: x["gap"], reverse=True)
            
            return {
                "evaluation_id": evaluation_id,
                "failing_components": evaluation.get("failing_components", []),
                "component_priorities": component_priorities,
                "improvement_priority": "high" if evaluation["status"] == EvalStatus.FAIL else "medium"
            }

# Create singleton instance
project_evaluator = ProjectEvaluator()
