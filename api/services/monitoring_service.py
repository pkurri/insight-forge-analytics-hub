
"""
Monitoring service for tracking system metrics, alerts, and logs
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import json
import os
import pandas as pd
import numpy as np
from prometheus_client import Gauge, Counter, Histogram, Summary, generate_latest, REGISTRY

# Setup Prometheus metrics
PIPELINE_RUNS_TOTAL = Counter('pipeline_runs_total', 'Total number of pipeline runs', ['status'])
PIPELINE_PROCESSING_TIME = Histogram('pipeline_processing_time_seconds', 'Time taken to process pipelines', ['pipeline_type'])
API_REQUESTS_TOTAL = Counter('requests_total', 'Total API requests', ['endpoint', 'method', 'status'])
DATASET_SIZE_BYTES = Gauge('dataset_size_bytes', 'Size of datasets in bytes', ['dataset_id'])

# In-memory storage for metrics, alerts and logs (in production this would use a proper database)
_metrics_store = []
_alerts_store = []
_logs_store = []

async def record_metric(name: str, value: float, labels: Dict[str, str] = None):
    """Record a metric value."""
    timestamp = datetime.utcnow()
    
    metric = {
        "name": name,
        "value": value,
        "timestamp": timestamp.isoformat(),
        "labels": labels or {}
    }
    
    _metrics_store.append(metric)
    
    # Update corresponding Prometheus metric if applicable
    if name == "pipeline_runs":
        PIPELINE_RUNS_TOTAL.labels(status=labels.get("status", "unknown")).inc()
    elif name == "pipeline_processing_time":
        PIPELINE_PROCESSING_TIME.labels(pipeline_type=labels.get("pipeline_type", "unknown")).observe(value)
    elif name == "request":
        API_REQUESTS_TOTAL.labels(
            endpoint=labels.get("endpoint", "unknown"),
            method=labels.get("method", "unknown"),
            status=labels.get("status", "unknown")
        ).inc()
    elif name == "dataset_size":
        DATASET_SIZE_BYTES.labels(dataset_id=labels.get("dataset_id", "unknown")).set(value)

async def record_alert(severity: str, message: str, component: str, details: Dict[str, Any] = None):
    """Record a system alert."""
    timestamp = datetime.utcnow()
    
    alert = {
        "id": f"alert-{len(_alerts_store) + 1:03d}",
        "severity": severity,
        "message": message,
        "component": component,
        "timestamp": timestamp.isoformat(),
        "status": "active",
        "details": details or {}
    }
    
    _alerts_store.append(alert)
    
    # Also log the alert as an ERROR log
    await record_log(
        level="ERROR" if severity in ["high", "critical"] else "WARNING",
        component=component,
        message=f"ALERT: {message}",
        details=details
    )
    
    return alert

async def resolve_alert(alert_id: str, resolution_message: str = None):
    """Resolve an active alert."""
    timestamp = datetime.utcnow()
    
    for alert in _alerts_store:
        if alert["id"] == alert_id and alert["status"] == "active":
            alert["status"] = "resolved"
            alert["resolved_at"] = timestamp.isoformat()
            alert["resolution_message"] = resolution_message
            
            # Log the resolution
            await record_log(
                level="INFO",
                component=alert["component"],
                message=f"ALERT RESOLVED: {alert['message']}",
                details={"resolution_message": resolution_message}
            )
            
            return True
    
    return False

async def record_log(level: str, component: str, message: str, details: Dict[str, Any] = None):
    """Record a system log."""
    timestamp = datetime.utcnow()
    
    log = {
        "id": f"log-{len(_logs_store) + 1:03d}",
        "timestamp": timestamp.isoformat(),
        "level": level.upper(),
        "component": component,
        "message": message,
        "details": details or {}
    }
    
    _logs_store.append(log)
    return log

async def get_metrics(time_period: str = "24h") -> List[Dict[str, Any]]:
    """Get system metrics for the specified time period."""
    now = datetime.utcnow()
    
    # Parse time period
    if time_period == "1h":
        from_time = now - timedelta(hours=1)
    elif time_period == "24h":
        from_time = now - timedelta(days=1)
    elif time_period == "7d":
        from_time = now - timedelta(days=7)
    elif time_period == "30d":
        from_time = now - timedelta(days=30)
    else:
        from_time = now - timedelta(days=1)  # Default to 24h
    
    # Filter metrics by time period
    filtered_metrics = []
    for metric in _metrics_store:
        metric_time = datetime.fromisoformat(metric["timestamp"])
        if metric_time >= from_time:
            filtered_metrics.append(metric)
    
    # If no stored metrics, generate sample data
    if not filtered_metrics:
        # For demonstration, generate sample metrics
        metrics = generate_sample_metrics(from_time, now)
        return metrics
    
    # Aggregate metrics by name and calculate statistics
    result = []
    df = pd.DataFrame(filtered_metrics)
    
    for name, group in df.groupby("name"):
        value = group["value"].mean()
        change = None
        
        # Calculate change if we have enough data
        if len(group) > 1:
            first_value = group.iloc[0]["value"]
            last_value = group.iloc[-1]["value"]
            if first_value != 0:
                change_percent = ((last_value - first_value) / first_value) * 100
                change = round(change_percent, 1)
        
        # Extract most common labels for this metric
        labels = {}
        if "labels" in group.columns:
            for idx, row in group.iterrows():
                for k, v in row["labels"].items():
                    if k not in labels:
                        labels[k] = {}
                    if v not in labels[k]:
                        labels[k][v] = 0
                    labels[k][v] += 1
        
        result.append({
            "name": name,
            "value": value,
            "change_percent": change,
            "time_period": time_period,
            "common_labels": {k: max(v.items(), key=lambda x: x[1])[0] for k, v in labels.items()} if labels else {}
        })
    
    return result

async def get_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """Get system alerts filtered by the provided criteria."""
    # If no stored alerts, generate sample data
    if not _alerts_store:
        alerts = generate_sample_alerts()
        _alerts_store.extend(alerts)
    
    # Apply filters
    filtered_alerts = _alerts_store.copy()
    
    if status:
        if status == "active":
            filtered_alerts = [a for a in filtered_alerts if a["status"] == "active"]
        elif status == "resolved":
            filtered_alerts = [a for a in filtered_alerts if a["status"] == "resolved"]
    
    if severity:
        filtered_alerts = [a for a in filtered_alerts if a["severity"] == severity]
    
    if from_date:
        filtered_alerts = [a for a in filtered_alerts if datetime.fromisoformat(a["timestamp"]) >= from_date]
    
    if to_date:
        filtered_alerts = [a for a in filtered_alerts if datetime.fromisoformat(a["timestamp"]) <= to_date]
    
    return sorted(filtered_alerts, key=lambda x: x["timestamp"], reverse=True)

async def get_logs(
    level: Optional[str] = None,
    component: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Tuple[List[Dict[str, Any]], int]:
    """Get system logs filtered by the provided criteria."""
    # If no stored logs, generate sample data
    if not _logs_store:
        logs = generate_sample_logs()
        _logs_store.extend(logs)
    
    # Apply filters
    filtered_logs = _logs_store.copy()
    
    if level:
        filtered_logs = [log for log in filtered_logs if log["level"].upper() == level.upper()]
    
    if component:
        filtered_logs = [log for log in filtered_logs if log["component"] == component]
    
    if from_date:
        filtered_logs = [log for log in filtered_logs if datetime.fromisoformat(log["timestamp"]) >= from_date]
    
    if to_date:
        filtered_logs = [log for log in filtered_logs if datetime.fromisoformat(log["timestamp"]) <= to_date]
    
    if search:
        filtered_logs = [log for log in filtered_logs if search.lower() in log["message"].lower()]
    
    # Sort by timestamp (newest first)
    filtered_logs = sorted(filtered_logs, key=lambda x: x["timestamp"], reverse=True)
    
    # Apply pagination
    total_count = len(filtered_logs)
    paginated_logs = filtered_logs[offset:offset+limit]
    
    return paginated_logs, total_count

def generate_sample_metrics(from_time: datetime, to_time: datetime) -> List[Dict[str, Any]]:
    """Generate sample metrics for demonstration."""
    now = datetime.utcnow()
    
    return [
        {
            "name": "pipeline_jobs_completed",
            "value": 152,
            "time_period": "30d",
            "change_percent": 8.5
        },
        {
            "name": "pipeline_jobs_failed",
            "value": 7,
            "time_period": "30d",
            "change_percent": -12.3
        },
        {
            "name": "average_processing_time",
            "value": 45.3,
            "unit": "seconds",
            "time_period": "30d",
            "change_percent": -5.2
        },
        {
            "name": "data_processed",
            "value": 1.8,
            "unit": "GB",
            "time_period": "30d",
            "change_percent": 22.7
        },
        {
            "name": "api_availability",
            "value": 99.95,
            "unit": "%",
            "time_period": "30d",
            "change_percent": 0.1
        }
    ]

def generate_sample_alerts() -> List[Dict[str, Any]]:
    """Generate sample alerts for demonstration."""
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    
    return [
        {
            "id": "alert-001",
            "severity": "high",
            "message": "Memory usage above 85% threshold",
            "component": "data-processing-service",
            "timestamp": yesterday.isoformat(),
            "status": "resolved",
            "resolved_at": now.isoformat()
        },
        {
            "id": "alert-002",
            "severity": "medium",
            "message": "API response time degradation detected",
            "component": "gateway",
            "timestamp": now.isoformat(),
            "status": "active"
        },
        {
            "id": "alert-003",
            "severity": "low",
            "message": "Non-critical validation errors increasing",
            "component": "data-validation-service",
            "timestamp": now.isoformat(),
            "status": "active",
            "details": {
                "error_rate": "2.8%",
                "threshold": "2.5%",
                "affected_datasets": ["ds-20240410-001", "ds-20240409-005"]
            }
        }
    ]

def generate_sample_logs() -> List[Dict[str, Any]]:
    """Generate sample logs for demonstration."""
    now = datetime.utcnow()
    
    def generate_log_time(minutes_ago: int) -> str:
        return (now - timedelta(minutes=minutes_ago)).isoformat()
    
    return [
        {
            "id": "log-001",
            "timestamp": generate_log_time(5),
            "level": "INFO",
            "component": "pipeline-service",
            "message": "Pipeline processing completed successfully",
            "details": {"pipeline_id": "pipe-2354", "dataset_id": "ds-8723", "duration_ms": 3452}
        },
        {
            "id": "log-002",
            "timestamp": generate_log_time(12),
            "level": "WARNING",
            "component": "data-validation",
            "message": "Data validation found 23 records with quality issues",
            "details": {"dataset_id": "ds-8723", "field": "email", "issue": "invalid format"}
        },
        {
            "id": "log-003",
            "timestamp": generate_log_time(15),
            "level": "ERROR",
            "component": "enrichment-service",
            "message": "Failed to enrich data with external API",
            "details": {"dataset_id": "ds-8720", "service": "geocoding-service", "status_code": 503}
        },
        {
            "id": "log-004",
            "timestamp": generate_log_time(25),
            "level": "INFO",
            "component": "auth-service",
            "message": "User authentication successful",
            "details": {"user_id": "u-2354", "ip_address": "192.168.1.1"}
        },
        {
            "id": "log-005",
            "timestamp": generate_log_time(45),
            "level": "INFO",
            "component": "pipeline-service",
            "message": "Pipeline job scheduled",
            "details": {"pipeline_id": "pipe-2353", "dataset_id": "ds-8722", "scheduled_time": generate_log_time(0)}
        }
    ]
