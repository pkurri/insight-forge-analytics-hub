
"""
Analytics Router Module

This module defines API routes for data analytics and monitoring.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request, BackgroundTasks
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import logging

from api.models.dataset import Dataset, BusinessRule, BusinessRuleCreate
from api.repositories.dataset_repository import get_dataset_repository
from api.repositories.analytics_repository import AnalyticsRepository
from api.repositories.business_rules_repository import BusinessRulesRepository
from api.repositories.monitoring_repository import MonitoringRepository
from api.services.analytics_service import (
    get_data_profile, 
    detect_anomalies,
    query_vector_database,
    create_vector_embeddings
)
from api.services.business_rules_service import (
    get_rules,
    create_rule,
    update_rule,
    delete_rule,
    validate_rules,
    generate_rules
)
from api.routes.auth_router import get_current_user_or_api_key

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize repositories
analytics_repo = AnalyticsRepository()
business_rules_repo = BusinessRulesRepository()
monitoring_repo = MonitoringRepository()

# Request/Response models
class AnomalyDetectionConfig(BaseModel):
    method: str = "isolation_forest"
    params: Dict[str, Any] = Field(default_factory=dict)

class VectorQueryRequest(BaseModel):
    query: str

class BusinessRuleUpdateRequest(BaseModel):
    name: Optional[str] = None
    condition: Optional[str] = None
    severity: Optional[str] = None
    message: Optional[str] = None
    is_active: Optional[bool] = None

class RuleGenerationOptions(BaseModel):
    cross_column_rules: bool = True
    generate_pattern_rules: bool = True
    max_rules_per_column: int = 3

class MonitoringMetricRequest(BaseModel):
    name: str
    value: float
    unit: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None

class AlertRequest(BaseModel):
    name: str
    severity: str
    message: str
    source: str
    tags: Optional[Dict[str, Any]] = None

class AlertStatusUpdate(BaseModel):
    status: str

@router.get("/{dataset_id}/profile")
async def profile_dataset(
    dataset_id: int,
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Generate and return data profile for a dataset."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Get data profile
    profile_data = await get_data_profile(dataset_id)
    return profile_data

@router.post("/{dataset_id}/anomalies")
async def detect_dataset_anomalies(
    dataset_id: int,
    config: AnomalyDetectionConfig = Body(...),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Detect and return anomalies in a dataset."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Detect anomalies
    anomalies = await detect_anomalies(dataset_id, config.dict())
    return anomalies

@router.post("/{dataset_id}/vectorize")
async def vectorize_dataset(
    dataset_id: int,
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Create vector embeddings for a dataset and store in vector database."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Create vector embeddings
    result = await create_vector_embeddings(dataset_id)
    return result

@router.post("/{dataset_id}/query")
async def query_dataset(
    dataset_id: int,
    request: VectorQueryRequest,
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Query a dataset using natural language and vector search."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Query vector database
    results = await query_vector_database(dataset_id, request.query)
    return results

@router.get("/{dataset_id}/rules")
async def get_dataset_rules(
    dataset_id: int,
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Get all business rules for a dataset."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Get rules
    result = await get_rules(dataset_id)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/{dataset_id}/rules")
async def create_dataset_rule(
    dataset_id: int,
    rule: BusinessRuleCreate,
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Create a new business rule for a dataset."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Ensure rule is for the specified dataset
    if rule.dataset_id != dataset_id:
        rule.dataset_id = dataset_id
    
    # Create rule
    result = await create_rule(rule)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.put("/rules/{rule_id}")
async def update_dataset_rule(
    rule_id: int,
    rule_update: BusinessRuleUpdateRequest,
    current_user = Depends(get_current_user_or_api_key)
):
    """Update an existing business rule."""
    # First, get the rule to check ownership
    rule = await business_rules_repo.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule with ID {rule_id} not found")
    
    # Get the dataset to check access
    dataset_repo = get_dataset_repository()
    dataset = await dataset_repo.get_dataset(rule["dataset_id"])
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to modify this rule")
    
    # Update rule
    result = await update_rule(rule_id, rule_update.dict(exclude_unset=True))
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.delete("/rules/{rule_id}")
async def delete_dataset_rule(
    rule_id: int,
    current_user = Depends(get_current_user_or_api_key)
):
    """Delete a business rule."""
    # First, get the rule to check ownership
    rule = await business_rules_repo.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule with ID {rule_id} not found")
    
    # Get the dataset to check access
    dataset_repo = get_dataset_repository()
    dataset = await dataset_repo.get_dataset(rule["dataset_id"])
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this rule")
    
    # Delete rule
    result = await delete_rule(rule_id)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/{dataset_id}/rules/validate")
async def validate_dataset_rules(
    dataset_id: int,
    rule_ids: List[int] = Body(None),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Validate business rules against a dataset."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Validate rules
    result = await validate_rules(dataset_id, rule_ids)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/{dataset_id}/rules/generate")
async def generate_dataset_rules(
    dataset_id: int,
    options: RuleGenerationOptions = Body(...),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Generate business rules for a dataset based on data patterns."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Generate rules
    result = await generate_rules(dataset_id, options.dict())
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

# Monitoring endpoints
@router.post("/monitoring/metrics")
async def record_metric(
    metric: MonitoringMetricRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user_or_api_key)
):
    """Record a monitoring metric."""
    # Record metric asynchronously to not block the response
    async def record_metric_task():
        try:
            await monitoring_repo.record_metric(
                name=metric.name,
                value=metric.value,
                unit=metric.unit,
                tags=metric.tags
            )
        except Exception as e:
            logger.error(f"Failed to record metric: {str(e)}")
    
    background_tasks.add_task(record_metric_task)
    
    return {"success": True, "message": "Metric recorded"}

@router.get("/monitoring/metrics")
async def get_metrics(
    metric_name: Optional[str] = None,
    time_range: Optional[int] = None,
    limit: int = Query(100, ge=1, le=1000),
    current_user = Depends(get_current_user_or_api_key)
):
    """Get monitoring metrics with optional filtering."""
    try:
        metrics = await monitoring_repo.get_metrics(
            metric_name=metric_name,
            time_range=time_range,
            limit=limit
        )
        return {"success": True, "metrics": metrics}
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@router.get("/monitoring/metrics/aggregates")
async def get_metric_aggregates(
    metric_name: str,
    time_range: int = Query(60, description="Time range in minutes"),
    interval: str = Query("5 minutes", description="Aggregation interval"),
    agg_function: str = Query("avg", description="Aggregation function (avg, min, max, sum, count)"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Get aggregated metrics over time intervals."""
    try:
        aggregates = await monitoring_repo.get_metric_aggregates(
            metric_name=metric_name,
            time_range=time_range,
            interval=interval,
            agg_function=agg_function
        )
        return {"success": True, "aggregates": aggregates}
    except Exception as e:
        logger.error(f"Failed to get metric aggregates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metric aggregates: {str(e)}")

@router.post("/monitoring/alerts")
async def create_alert(
    alert: AlertRequest,
    current_user = Depends(get_current_user_or_api_key)
):
    """Create a new monitoring alert."""
    try:
        alert_id = await monitoring_repo.create_alert(
            name=alert.name,
            severity=alert.severity,
            message=alert.message,
            source=alert.source,
            tags=alert.tags
        )
        return {"success": True, "alert_id": alert_id}
    except Exception as e:
        logger.error(f"Failed to create alert: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")

@router.put("/monitoring/alerts/{alert_id}/status")
async def update_alert_status(
    alert_id: int,
    status_update: AlertStatusUpdate,
    current_user = Depends(get_current_user_or_api_key)
):
    """Update alert status (active, acknowledged, resolved)."""
    try:
        success = await monitoring_repo.update_alert_status(
            alert_id=alert_id,
            status=status_update.status
        )
        if not success:
            raise HTTPException(status_code=404, detail=f"Alert with ID {alert_id} not found")
        return {"success": True, "message": f"Alert status updated to {status_update.status}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update alert status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update alert status: {str(e)}")

@router.get("/monitoring/alerts")
async def get_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    current_user = Depends(get_current_user_or_api_key)
):
    """Get monitoring alerts with optional filtering."""
    try:
        alerts = await monitoring_repo.get_alerts(
            status=status,
            severity=severity,
            limit=limit
        )
        return {"success": True, "alerts": alerts}
    except Exception as e:
        logger.error(f"Failed to get alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")
