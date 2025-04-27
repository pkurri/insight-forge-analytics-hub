
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
    create_vector_embeddings,
    clean_dataset,
    process_dataset
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
class DataCleaningConfig(BaseModel):
    method: str = "scikit-learn"
    operations: List[Dict[str, Any]] = Field(default_factory=list)

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

@router.post("/{dataset_id}/process")
async def process_dataset_data(
    dataset_id: int,
    config: DataCleaningConfig = Body(...),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Process a dataset using specified cleaning method and operations."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Process dataset
    result = await process_dataset(dataset_id, config.dict())
    return result

@router.post("/{dataset_id}/clean")
async def clean_dataset_data(
    dataset_id: int,
    config: DataCleaningConfig = Body(...),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Clean a dataset using specified cleaning method and operations."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Clean dataset
    result = await clean_dataset(dataset_id, config.dict())
    return result

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

# Dataset analytics endpoints

@router.get("/dataset/{dataset_id}")
async def get_dataset_analytics(dataset_id: int, current_user = Depends(get_current_user_or_api_key)):
    """Get comprehensive analytics for a specific dataset."""
    try:
        # In a real implementation, we would fetch actual analytics from a service or database
        # For now, let's generate sample data
        import random
        from datetime import datetime, timedelta
        
        # Generate sample metrics
        metrics = {
            "totalRows": random.randint(10000, 100000),
            "totalColumns": random.randint(10, 30),
            "missingValuesPercentage": round(random.uniform(0, 20), 2),
            "outlierPercentage": round(random.uniform(0, 10), 2),
            "dataTypes": {
                "numeric": random.randint(3, 10),
                "categorical": random.randint(2, 8),
                "temporal": random.randint(1, 3),
                "text": random.randint(0, 5)
            },
            "processingTime": random.randint(5, 120)
        }
        
        # Generate time series data (last 30 days)
        now = datetime.now()
        time_series = {}
        series_names = ["metric_a", "metric_b", "revenue", "users"]
        
        for series in series_names:
            points = []
            base_value = random.randint(100, 1000)
            
            for i in range(30):
                day = now - timedelta(days=i)
                # Add some randomness to create trends and patterns
                value = base_value + random.randint(-50, 100) + (i * random.randint(-5, 10))
                if value < 0:
                    value = random.randint(10, 50)
                    
                points.append({
                    "timestamp": day.isoformat(),
                    "value": value
                })
            
            # Sort by timestamp (oldest first)
            points.sort(key=lambda x: x["timestamp"])
            time_series[series] = points
        
        # Generate anomalies
        anomalies = {}
        for series in series_names:
            anomaly_count = random.randint(0, 3)
            anomalies[series] = []
            
            for _ in range(anomaly_count):
                # Pick a random point
                point_idx = random.randint(0, len(time_series[series]) - 1)
                point = time_series[series][point_idx]
                
                # Create anomaly
                expected = point["value"] * random.uniform(0.7, 1.3)
                anomalies[series].append({
                    "timestamp": point["timestamp"],
                    "expected": expected,
                    "actual": point["value"],
                    "score": random.uniform(0.7, 0.99)
                })
        
        # Generate trends
        trends = {}
        for series in series_names:
            trend_count = random.randint(0, 2)
            trends[series] = []
            
            for _ in range(trend_count):
                # Create start and end points for trend
                start_idx = random.randint(0, len(time_series[series]) // 2)
                end_idx = random.randint(start_idx + 5, len(time_series[series]) - 1)
                
                start_point = time_series[series][start_idx]
                end_point = time_series[series][end_idx]
                
                # Calculate slope
                if end_idx > start_idx:
                    slope = (end_point["value"] - start_point["value"]) / (end_idx - start_idx)
                else:
                    slope = 0
                
                trends[series].append({
                    "start": start_point["timestamp"],
                    "end": end_point["timestamp"],
                    "slope": slope,
                    "confidence": random.uniform(0.7, 0.95)
                })
        
        # Generate data quality report
        columns = []
        column_names = ["id", "name", "date", "category", "amount", "status", "description",
                       "location", "user_id", "rating", "timestamp"]
        data_types = ["integer", "string", "date", "string", "float", "string", "text",
                     "string", "integer", "float", "timestamp"]
        
        for i, (name, data_type) in enumerate(zip(column_names[:metrics["totalColumns"]], data_types[:metrics["totalColumns"]])):
            completeness = random.randint(50, 100)
            columns.append({
                "name": name,
                "dataType": data_type,
                "completeness": completeness,
                "uniqueness": random.randint(50, 100) if data_type != "text" else None,
                "validFormat": random.randint(50, 100) if data_type in ["date", "timestamp", "integer", "float"] else None,
                "issues": ["Missing values"] if completeness < 80 else []
            })
        
        quality_report = {
            "columns": columns,
            "overallScore": random.randint(60, 95)
        }
        
        # Generate insights
        insights = []
        insight_types = ["trend", "anomaly", "correlation", "pattern", "info"]
        severity_levels = ["high", "medium", "low", None]
        
        insight_templates = [
            "Significant {direction} trend detected in {metric} over {timeframe}",
            "Anomaly detected in {metric} with deviation of {percent}%",
            "Strong correlation ({coef}) found between {metric1} and {metric2}",
            "Recurring pattern identified in {metric} with {percent}% consistency",
            "Distribution of {metric} shows {characteristic} characteristics"
        ]
        
        for i in range(random.randint(3, 8)):
            insight_type = random.choice(insight_types)
            template_idx = min(insight_types.index(insight_type), len(insight_templates) - 1)
            
            metric = random.choice(series_names)
            direction = "upward" if random.random() > 0.5 else "downward"
            timeframe = random.choice(["past week", "past month", "Q1", "recent period"])
            percent = random.randint(10, 40)
            coef = round(random.uniform(0.7, 0.95), 2)
            metric2 = random.choice([m for m in series_names if m != metric])
            characteristic = random.choice(["normal", "bimodal", "skewed", "long-tailed"])
            
            template = insight_templates[template_idx]
            description = template.format(
                direction=direction,
                metric=metric,
                timeframe=timeframe,
                percent=percent,
                coef=coef,
                metric1=metric,
                metric2=metric2,
                characteristic=characteristic
            )
            
            insights.append({
                "id": f"insight-{i+1}",
                "title": description.split(".")[0],
                "description": description,
                "type": insight_type,
                "severity": random.choice(severity_levels) if insight_type in ["anomaly", "trend"] else None,
                "timestamp": (now - timedelta(days=random.randint(0, 7))).isoformat()
            })
        
        # Combine all analytics data
        analytics_data = {
            "datasetName": f"Dataset {dataset_id}",
            "metrics": metrics,
            "timeSeries": time_series,
            "anomalies": anomalies,
            "trends": trends,
            "qualityReport": quality_report,
            "insights": insights
        }
        
        return {
            "success": True,
            "data": analytics_data
        }
        
    except Exception as e:
        logging.error(f"Error getting dataset analytics: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to retrieve analytics for dataset {dataset_id}"
        }

@router.get("/global")
async def get_global_analytics(current_user = Depends(get_current_user_or_api_key)):
    """Get global analytics across all datasets."""
    try:
        # In a real implementation, we would aggregate analytics from multiple datasets
        # For now, let's generate sample global data similar to dataset analytics but with aggregated metrics
        import random
        from datetime import datetime, timedelta
        
        # Generate global metrics
        metrics = {
            "totalDatasets": random.randint(5, 20),
            "totalRecords": random.randint(100000, 1000000),
            "avgQualityScore": round(random.uniform(70, 95), 1),
            "dataTypes": {
                "numeric": random.randint(10, 30),
                "categorical": random.randint(8, 20),
                "temporal": random.randint(3, 10),
                "text": random.randint(5, 15)
            },
            "processingTimeAvg": random.randint(20, 200)
        }
        
        # Use the same time series generation logic as in dataset analytics
        # but with different base values to represent global aggregates
        now = datetime.now()
        time_series = {}
        series_names = ["total_users", "active_datasets", "global_revenue", "system_load"]
        
        for series in series_names:
            points = []
            base_value = random.randint(500, 5000)
            
            for i in range(30):
                day = now - timedelta(days=i)
                # Add some randomness to create trends and patterns
                value = base_value + random.randint(-200, 400) + (i * random.randint(-10, 20))
                if value < 0:
                    value = random.randint(50, 200)
                    
                points.append({
                    "timestamp": day.isoformat(),
                    "value": value
                })
            
            # Sort by timestamp (oldest first)
            points.sort(key=lambda x: x["timestamp"])
            time_series[series] = points
        
        # Generate anomalies and trends similar to dataset analytics
        # but pertaining to global metrics
        anomalies = {}
        trends = {}
        for series in series_names:
            # Generate anomalies
            anomaly_count = random.randint(0, 3)
            anomalies[series] = []
            
            for _ in range(anomaly_count):
                point_idx = random.randint(0, len(time_series[series]) - 1)
                point = time_series[series][point_idx]
                
                expected = point["value"] * random.uniform(0.7, 1.3)
                anomalies[series].append({
                    "timestamp": point["timestamp"],
                    "expected": expected,
                    "actual": point["value"],
                    "score": random.uniform(0.7, 0.99)
                })
            
            # Generate trends
            trend_count = random.randint(0, 2)
            trends[series] = []
            
            for _ in range(trend_count):
                start_idx = random.randint(0, len(time_series[series]) // 2)
                end_idx = random.randint(start_idx + 5, len(time_series[series]) - 1)
                
                start_point = time_series[series][start_idx]
                end_point = time_series[series][end_idx]
                
                if end_idx > start_idx:
                    slope = (end_point["value"] - start_point["value"]) / (end_idx - start_idx)
                else:
                    slope = 0
                
                trends[series].append({
                    "start": start_point["timestamp"],
                    "end": end_point["timestamp"],
                    "slope": slope,
                    "confidence": random.uniform(0.7, 0.95)
                })
        
        # Generate insights similar to dataset analytics but focused on global patterns
        insights = []
        insight_types = ["trend", "anomaly", "correlation", "pattern", "info"]
        severity_levels = ["high", "medium", "low", None]
        
        insight_templates = [
            "Global {direction} trend detected in {metric} across all datasets over {timeframe}",
            "System-wide anomaly detected in {metric} with deviation of {percent}%",
            "Strong correlation ({coef}) found between {metric1} and {metric2} across datasets",
            "Recurring pattern identified in global {metric} with {percent}% consistency",
            "Distribution of {metric} across all datasets shows {characteristic} characteristics"
        ]
        
        for i in range(random.randint(3, 8)):
            insight_type = random.choice(insight_types)
            template_idx = min(insight_types.index(insight_type), len(insight_templates) - 1)
            
            metric = random.choice(series_names)
            direction = "upward" if random.random() > 0.5 else "downward"
            timeframe = random.choice(["past week", "past month", "Q1", "recent period"])
            percent = random.randint(10, 40)
            coef = round(random.uniform(0.7, 0.95), 2)
            metric2 = random.choice([m for m in series_names if m != metric])
            characteristic = random.choice(["normal", "bimodal", "skewed", "long-tailed"])
            
            template = insight_templates[template_idx]
            description = template.format(
                direction=direction,
                metric=metric,
                timeframe=timeframe,
                percent=percent,
                coef=coef,
                metric1=metric,
                metric2=metric2,
                characteristic=characteristic
            )
            
            insights.append({
                "id": f"global-insight-{i+1}",
                "title": description.split(".")[0],
                "description": description,
                "type": insight_type,
                "severity": random.choice(severity_levels) if insight_type in ["anomaly", "trend"] else None,
                "timestamp": (now - timedelta(days=random.randint(0, 7))).isoformat()
            })
        
        # Combine all global analytics data
        analytics_data = {
            "metrics": metrics,
            "timeSeries": time_series,
            "anomalies": anomalies,
            "trends": trends,
            "insights": insights
        }
        
        return {
            "success": True,
            "data": analytics_data
        }
        
    except Exception as e:
        logging.error(f"Error getting global analytics: {str(e)}")
        return {
            "success": False,
            "error": "Failed to retrieve global analytics"
        }

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
