
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from api.routes.auth_router import get_current_user_or_api_key
from api.services.monitoring_service import get_metrics, get_alerts, get_logs

router = APIRouter()

@router.get("/metrics", response_model=Dict[str, Any])
async def get_monitoring_metrics(
    time_period: str = Query("24h", description="Time period for metrics (1h, 24h, 7d, 30d)"),
    metrics: Optional[List[str]] = Query(None, description="Specific metrics to retrieve"),
    dataset_id: Optional[str] = Query(None, description="Filter metrics by dataset ID"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Get system monitoring metrics."""
    try:
        metrics_data = await get_metrics(
            time_period=time_period,
            metrics_filter=metrics,
            dataset_id=dataset_id
        )
        
        return {
            "metrics": metrics_data,
            "timestamp": datetime.utcnow().isoformat(),
            "time_period": time_period,
            "system_health": "healthy",  # This could be dynamically calculated
            "filters_applied": {
                "metrics": metrics,
                "dataset_id": dataset_id
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")

@router.get("/alerts", response_model=Dict[str, Any])
async def get_system_alerts(
    status: Optional[str] = Query(None, description="Filter by alert status (active, resolved, all)"),
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high)"),
    from_date: Optional[str] = Query(None, description="From date (ISO format)"),
    to_date: Optional[str] = Query(None, description="To date (ISO format)"),
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    component: Optional[str] = Query(None, description="Filter by component"),
    limit: int = Query(50, description="Maximum number of alerts to return"),
    offset: int = Query(0, description="Offset for pagination"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Get system alerts."""
    try:
        # Parse dates if provided
        parsed_from_date = None
        parsed_to_date = None
        
        if from_date:
            try:
                parsed_from_date = datetime.fromisoformat(from_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid from_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
        
        if to_date:
            try:
                parsed_to_date = datetime.fromisoformat(to_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid to_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
        
        # Get alerts with filters
        alerts, total_count = await get_alerts(
            status=status, 
            severity=severity, 
            from_date=parsed_from_date,
            to_date=parsed_to_date,
            dataset_id=dataset_id,
            component=component,
            limit=limit,
            offset=offset
        )
        
        return {
            "alerts": alerts,
            "count": len(alerts),
            "total_count": total_count,
            "active_count": sum(1 for alert in alerts if alert.get("status") == "active"),
            "pagination": {
                "limit": limit,
                "offset": offset,
                "next_offset": offset + limit if offset + limit < total_count else None,
                "previous_offset": max(0, offset - limit) if offset > 0 else None,
                "total": total_count
            },
            "filters_applied": {
                "status": status,
                "severity": severity,
                "from_date": from_date,
                "to_date": to_date,
                "dataset_id": dataset_id,
                "component": component
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve alerts: {str(e)}")

@router.get("/logs", response_model=Dict[str, Any])
async def get_system_logs(
    level: Optional[str] = Query(None, description="Filter by log level (INFO, WARNING, ERROR, DEBUG)"),
    component: Optional[str] = Query(None, description="Filter by component"),
    from_date: Optional[str] = Query(None, description="From date (ISO format)"),
    to_date: Optional[str] = Query(None, description="To date (ISO format)"),
    search: Optional[str] = Query(None, description="Search in log message"),
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    limit: int = Query(100, description="Maximum number of logs to return"),
    offset: int = Query(0, description="Offset for pagination"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Get system logs."""
    try:
        # Parse dates if provided
        parsed_from_date = None
        parsed_to_date = None
        
        if from_date:
            try:
                parsed_from_date = datetime.fromisoformat(from_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid from_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
        
        if to_date:
            try:
                parsed_to_date = datetime.fromisoformat(to_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid to_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
        
        # Get logs with filters
        logs, total_count = await get_logs(
            level=level,
            component=component,
            from_date=parsed_from_date,
            to_date=parsed_to_date,
            search=search,
            dataset_id=dataset_id,
            limit=limit,
            offset=offset
        )
        
        return {
            "logs": logs,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "next_offset": offset + limit if offset + limit < total_count else None,
                "previous_offset": max(0, offset - limit) if offset > 0 else None
            },
            "filters_applied": {
                "level": level,
                "component": component,
                "from_date": from_date,
                "to_date": to_date,
                "search": search,
                "dataset_id": dataset_id
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve logs: {str(e)}")

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_metrics(
    time_period: str = Query("24h", description="Time period for metrics (1h, 24h, 7d, 30d)"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Get dashboard summary metrics."""
    try:
        # This would fetch metrics from a real monitoring service
        # For now, return mock data
        metrics = await get_metrics(time_period)
        
        # Get recent alerts
        recent_alerts, _ = await get_alerts(
            status="active", 
            limit=5,
            offset=0
        )
        
        # Get recent logs
        recent_logs, _ = await get_logs(
            level="ERROR",
            limit=5,
            offset=0
        )
        
        # Construct dashboard data
        return {
            "summary": {
                "processed_today": 24832,
                "success_rate": 98.7,
                "data_sources": 12,
                "storage_used": "1.2 TB",
                "active_alerts": sum(1 for alert in recent_alerts if alert.get("status") == "active"),
                "error_logs_today": sum(1 for log in recent_logs if log.get("timestamp", "").startswith(datetime.utcnow().strftime("%Y-%m-%d")))
            },
            "pipeline_status": {
                "ingestion": "operational",
                "cleaning": "operational",
                "validation": "warning",
                "anomaly": "operational",
                "storage": "operational"
            },
            "recent_alerts": recent_alerts,
            "recent_logs": recent_logs,
            "system_health": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "time_period": time_period
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dashboard metrics: {str(e)}")

@router.post("/acknowledge-alert/{alert_id}", response_model=Dict[str, Any])
async def acknowledge_alert(
    alert_id: str,
    notes: Optional[str] = Body(None, description="Optional notes about acknowledgment"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Acknowledge an alert."""
    try:
        # This would update the alert status in a real system
        # For now, return a success response
        return {
            "success": True,
            "alert_id": alert_id,
            "status": "acknowledged",
            "acknowledged_by": current_user.username,
            "acknowledged_at": datetime.utcnow().isoformat(),
            "notes": notes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")

@router.post("/resolve-alert/{alert_id}", response_model=Dict[str, Any])
async def resolve_alert(
    alert_id: str,
    resolution: str = Body(..., description="Description of how the alert was resolved"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Mark an alert as resolved."""
    try:
        # This would update the alert status in a real system
        # For now, return a success response
        return {
            "success": True,
            "alert_id": alert_id,
            "status": "resolved",
            "resolved_by": current_user.username,
            "resolved_at": datetime.utcnow().isoformat(),
            "resolution": resolution
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")
