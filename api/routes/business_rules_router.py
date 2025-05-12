"""Business Rules Router Module

This module provides API endpoints for managing business rules, including:
- Creating, updating, and deleting rules
- Importing and exporting rules
- Generating rules using AI
- Applying rules to datasets
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from typing import List, Dict, Any, Optional
import json

from api.models.business_rule import BusinessRule, BusinessRuleCreate, BusinessRuleUpdate, RuleValidationResult
from api.models.responses import StandardResponse, PaginatedResponse
from api.services.business_rules import business_rules_service
from api.services.business_rules.core import BusinessRulesService
from api.dependencies.auth import get_current_user
from api.dependencies.services import get_business_rules_service
from api.services.pipeline_service import pipeline_service

router = APIRouter(
    prefix="/business-rules",
    tags=["business-rules"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=PaginatedResponse[BusinessRule])
async def get_rules(
    dataset_id: Optional[str] = Query(None, description="Filter rules by dataset ID"),
    rule_type: Optional[str] = Query(None, description="Filter rules by type (validation, transformation, enrichment)"),
    severity: Optional[str] = Query(None, description="Filter rules by severity (low, medium, high)"),
    source: Optional[str] = Query(None, description="Filter rules by source (manual, ai, great_expectations, etc.)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    rules_service: BusinessRulesService = Depends(get_business_rules_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a list of business rules with optional filtering.
    """
    try:
        # Get rules from service
        rules = await rules_service.get_rules(dataset_id)
        
        # Apply filters
        if rule_type:
            rules = [r for r in rules if r.get("rule_type") == rule_type]
        if severity:
            rules = [r for r in rules if r.get("severity") == severity]
        if source:
            rules = [r for r in rules if r.get("source") == source]
            
        # Paginate results
        total = len(rules)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_rules = rules[start_idx:end_idx]
        
        return PaginatedResponse(
            success=True,
            data=paginated_rules,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving rules: {str(e)}")

@router.get("/{rule_id}", response_model=StandardResponse[BusinessRule])
async def get_rule(
    rule_id: str = Path(..., description="ID of the rule to retrieve"),
    rules_service: BusinessRulesService = Depends(get_business_rules_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a specific business rule by ID.
    """
    try:
        rule = await rules_service.get_rule(rule_id)
        if not rule:
            return StandardResponse(success=False, error=f"Rule with ID {rule_id} not found")
        return StandardResponse(success=True, data=rule)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving rule: {str(e)}")

@router.post("/", response_model=StandardResponse[BusinessRule])
async def create_rule(
    rule_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new business rule.
    """
    try:
        created_rule = await business_rules_service.create_rule(rule_data)
        return StandardResponse(success=True, data=created_rule)
    except ValueError as e:
        return StandardResponse(success=False, error=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating rule: {str(e)}")

@router.post("/batch", response_model=StandardResponse[List[BusinessRule]])
async def create_rules(
    rules_data: List[Dict[str, Any]],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create multiple business rules in a single request.
    
    This endpoint allows for bulk creation of business rules, which is more efficient
    than making multiple individual requests when creating several rules at once.
    """
    try:
        created_rules = []
        failed_rules = []
        
        for rule_data in rules_data:
            try:
                created_rule = await business_rules_service.create_rule(rule_data)
                created_rules.append(created_rule)
            except ValueError as e:
                # Track failed rules with their errors
                failed_rules.append({
                    "rule_data": rule_data,
                    "error": str(e)
                })
        
        # Return information about successful and failed creations
        result = {
            "created_rules": created_rules,
            "failed_rules": failed_rules,
            "total_submitted": len(rules_data),
            "total_created": len(created_rules),
            "total_failed": len(failed_rules)
        }
        
        # Consider the operation successful if at least one rule was created
        success = len(created_rules) > 0
        
        return StandardResponse(
            success=success,
            data=result,
            error=None if success else "Some or all rules failed to create"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating rules: {str(e)}")


@router.put("/{rule_id}", response_model=StandardResponse[BusinessRule])
async def update_rule(
    rule_id: str = Path(..., description="ID of the rule to update"),
    rule_update: BusinessRuleUpdate = Body(...),
    rules_service: BusinessRulesService = Depends(get_business_rules_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update an existing business rule.
    """
    try:
        # Check if rule exists
        existing_rule = await rules_service.get_rule(rule_id)
        if not existing_rule:
            return StandardResponse(success=False, error=f"Rule with ID {rule_id} not found")
            
        # Update rule
        updated_rule = await rules_service.update_rule(rule_id, rule_update.dict(exclude_unset=True))
        return StandardResponse(success=True, data=updated_rule)
    except ValueError as e:
        return StandardResponse(success=False, error=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating rule: {str(e)}")

@router.delete("/{rule_id}", response_model=StandardResponse[bool])
async def delete_rule(
    rule_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a business rule.
    """
    try:
        # Check if rule exists
        existing_rule = await rules_service.get_rule(rule_id)
        if not existing_rule:
            return StandardResponse(success=False, error=f"Rule with ID {rule_id} not found")
            
        # Delete rule
        result = await rules_service.delete_rule(rule_id)
        return StandardResponse(success=result, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting rule: {str(e)}")

@router.post("/import/{dataset_id}", response_model=StandardResponse[Dict[str, Any]])
async def import_rules(
    dataset_id: str = Path(..., description="ID of the dataset to import rules for"),
    rules_json: str = Body(..., embed=True),
    rules_service: BusinessRulesService = Depends(get_business_rules_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Import business rules from JSON.
    """
    try:
        result = await rules_service.import_rules(dataset_id, rules_json)
        return StandardResponse(success=result["success"], data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing rules: {str(e)}")

@router.post("/generate/{dataset_id}", response_model=StandardResponse[Dict[str, Any]])
async def generate_rules(
    dataset_id: str = Path(..., description="ID of the dataset to generate rules for"),
    column_meta: Dict[str, Any] = Body(...),
    engine: str = Query("ai_default", description="AI engine to use for rule generation"),
    model_type: Optional[str] = Query(None, description="Type of model to use for generation"),
    rules_service: BusinessRulesService = Depends(get_business_rules_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate business rules using AI.
    """
    try:
        result = await rules_service.generate_ai_rules(dataset_id, column_meta, engine, model_type)
        return StandardResponse(success="error" not in result, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating rules: {str(e)}")

@router.post("/apply/{dataset_id}", response_model=StandardResponse[RuleValidationResult])
async def apply_rules(
    dataset_id: str = Path(..., description="ID of the dataset to apply rules to"),
    data: List[Dict[str, Any]] = Body(...),
    rule_ids: Optional[List[str]] = Query(None, description="IDs of specific rules to apply"),
    rules_service: BusinessRulesService = Depends(get_business_rules_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Apply business rules to data.
    """
    try:
        result = await rules_service.apply_rules_to_dataset(dataset_id, data, rule_ids)
        return StandardResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying rules: {str(e)}")

@router.post("/validate/{dataset_id}", response_model=StandardResponse[Dict[str, Any]])
async def validate_data(
    dataset_id: str = Path(..., description="ID of the dataset to validate data for"),
    data: List[Dict[str, Any]] = Body(...),
    rule_ids: Optional[List[str]] = Query(None, description="IDs of specific rules to apply"),
    rules_service: BusinessRulesService = Depends(get_business_rules_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Validate data against business rules before vectorization.
    """
    try:
        result = await rules_service.validate_data_with_rules(dataset_id, data, rule_ids)
        return StandardResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating data: {str(e)}")

@router.post("/test-sample/{dataset_id}", response_model=StandardResponse[Dict[str, Any]])
async def test_rules_on_sample(
    dataset_id: str = Path(..., description="ID of the dataset"),
    sample_data: List[Dict[str, Any]] = Body(..., description="Sample data to test rules against"),
    rule_ids: Optional[List[str]] = Query(None, description="Specific rules to test, if None all active rules will be used"),
    test_rule: Optional[Dict[str, Any]] = Body(None, description="Optional test rule to evaluate"),
    confidence_threshold: float = Query(0.8, ge=0.0, le=1.0, description="Minimum confidence threshold for rule suggestions"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Test business rules against sample data and provide validation results and suggestions.
    
    This endpoint allows testing rules against a sample of data before applying them to the full dataset.
    It returns validation results and may suggest new rules based on data patterns.
    
    If a test_rule is provided, it will be evaluated against the sample data without being saved to the database.
    This is useful for testing new rules before creating them.
    """
    try:
        # Validate sample data against existing rules
        validation_results = await business_rules_service.validate_data_with_rules(
            dataset_id, 
            sample_data, 
            rule_ids,
            include_rule_suggestions=True,
            confidence_threshold=confidence_threshold
        )
        
        # Calculate potential impact metrics
        total_records = len(sample_data)
        filtered_records = len(validation_results.get("filtered_data", []))
        impact_percentage = ((total_records - filtered_records) / total_records * 100) if total_records > 0 else 0
        
        # Add impact metrics to response
        validation_results["impact_metrics"] = {
            "total_records": total_records,
            "records_passing_validation": filtered_records,
            "records_failing_validation": total_records - filtered_records,
            "impact_percentage": round(impact_percentage, 2),
            "estimated_full_dataset_impact": validation_results.get("estimated_impact", {})
        }
        
        return StandardResponse(success=True, data=validation_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing rules on sample data: {str(e)}")

@router.post("/suggest/{dataset_id}", response_model=StandardResponse[Dict[str, Any]])
async def suggest_business_rules(
    dataset_id: str = Path(..., description="ID of the dataset to suggest rules for"),
    sample_data: List[Dict[str, Any]] = Body(..., description="Sample data to analyze for rule suggestions"),
    min_confidence: float = Query(0.7, ge=0.0, le=1.0, description="Minimum confidence threshold for suggestions"),
    max_suggestions: int = Query(10, ge=1, le=50, description="Maximum number of suggestions to return"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Suggest business rules based on sample data patterns.
    
    This endpoint analyzes sample data and suggests potential business rules
    based on patterns, data types, and statistical analysis. The suggestions
    can be used as a starting point for creating new rules.
    """
    try:
        suggestions = await business_rules_service.suggest_rules_from_data(
            dataset_id, 
            sample_data, 
            min_confidence, 
            max_suggestions
        )
        return StandardResponse(success=True, data=suggestions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error suggesting rules: {str(e)}")

@router.get("/metrics/{dataset_id}", response_model=StandardResponse[Dict[str, Any]])
async def get_rule_metrics(
    dataset_id: str = Path(..., description="ID of the dataset"),
    time_period: str = Query("all", description="Time period for metrics (day, week, month, all)"),
    rule_ids: Optional[List[str]] = Query(None, description="Specific rules to get metrics for"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get metrics and performance statistics for rules applied to a dataset.
    
    This endpoint provides insights into rule effectiveness, violation rates,
    and impact on data quality over time.
    """
    try:
        metrics = await business_rules_service.get_rule_metrics(dataset_id, time_period, rule_ids)
        return StandardResponse(success=True, data=metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving rule metrics: {str(e)}")

@router.post("/extract-sample/{dataset_id}", response_model=StandardResponse[Dict[str, Any]])
async def extract_sample_data(
    dataset_id: str = Path(..., description="ID of the dataset"),
    max_rows: int = Query(100, ge=1, le=1000, description="Maximum number of rows to extract"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Extract a sample of data from a dataset for rule testing and preview.
    
    This endpoint extracts a sample of data from the dataset file for use in rule testing
    and data preview. It returns the sample data along with basic metadata.
    """
    try:
        # Get dataset metadata
        dataset = await pipeline_service.dataset_repo.get_dataset(dataset_id)
        if not dataset:
            return StandardResponse(success=False, error=f"Dataset with ID {dataset_id} not found")
        
        # Extract sample data
        file_path = dataset.get("file_path")
        file_type = dataset.get("file_type")
        
        if not file_path or not file_type:
            return StandardResponse(success=False, error="Dataset missing file path or file type information")
        
        result = await pipeline_service.extract_sample_data(file_path, file_type, max_rows)
        return StandardResponse(success=result.get("success", False), data=result)
        
    except Exception as e:
        return StandardResponse(success=False, error=f"Error extracting sample data: {str(e)}")

@router.post("/suggest/{dataset_id}", response_model=StandardResponse[Dict[str, Any]])
async def suggest_rules(
    dataset_id: str = Path(..., description="ID of the dataset"),
    sample_data: List[Dict[str, Any]] = Body(..., description="Sample data to analyze for rule suggestions"),
    min_confidence: float = Query(0.7, ge=0.0, le=1.0, description="Minimum confidence threshold for suggestions"),
    max_suggestions: int = Query(10, ge=1, le=50, description="Maximum number of suggestions to return"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate rule suggestions based on sample data patterns.
    
    This endpoint analyzes sample data to suggest data quality rules that might
    be relevant for the dataset, using pattern recognition and statistical analysis.
    """
    try:
        suggestions = await business_rules_service.suggest_rules_from_data(
            dataset_id,
            sample_data,
            min_confidence=min_confidence,
            max_suggestions=max_suggestions
        )
        return StandardResponse(success=True, data=suggestions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating rule suggestions: {str(e)}")
