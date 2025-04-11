
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from api.routes.auth_router import get_current_user_or_api_key
from api.services.monitoring_service import get_metrics, get_alerts, get_logs

router = APIRouter()

@router.get("/metrics", response_model=Dict[str, Any])
async def get_monitoring_metrics(
    time_period: str = Query("24h", description="Time period for metrics (1h, 24h, 7d, 30d)"),
    current_user = Depends(get_current_user_or_api_key)
):
    """Get system monitoring metrics."""
    try:
        metrics = await get_metrics(time_period)
        return {
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat(),
            "time_period": time_period,
            "system_health": "healthy"  # This could be dynamically calculated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")

@router.get("/alerts", response_model=Dict[str, Any])
async def get_system_alerts(
    status: Optional[str] = Query(None, description="Filter by alert status (active, resolved, all)"),
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high)"),
    from_date: Optional[str] = Query(None, description="From date (ISO format)"),
    to_date: Optional[str] = Query(None, description="To date (ISO format)"),
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
        alerts = await get_alerts(
            status=status, 
            severity=severity, 
            from_date=parsed_from_date,
            to_date=parsed_to_date
        )
        
        return {
            "alerts": alerts,
            "count": len(alerts),
            "active_count": sum(1 for alert in alerts if alert.get("status") == "active"),
            "filters_applied": {
                "status": status,
                "severity": severity,
                "from_date": from_date,
                "to_date": to_date
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
                "search": search
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve logs: {str(e)}")
