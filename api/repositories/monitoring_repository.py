
"""
Repository for monitoring metrics and alerts.
"""
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from utils.db import execute_query, execute_transaction

logger = logging.getLogger(__name__)

class MonitoringRepository:
    """Repository for monitoring metrics and alerts."""
    
    async def record_metric(self, name: str, value: float, unit: Optional[str] = None, 
                         tags: Optional[Dict[str, Any]] = None) -> int:
        """Record a monitoring metric."""
        query = """
        INSERT INTO monitoring_metrics (metric_name, metric_value, metric_unit, tags)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """
        
        try:
            results = await execute_query(
                query, 
                name,
                value, 
                unit,
                json.dumps(tags) if tags else None
            )
            return results[0]['id']
        except Exception as e:
            logger.error(f"Error recording metric {name}: {str(e)}")
            raise
    
    async def get_metrics(self, metric_name: Optional[str] = None, 
                       time_range: Optional[int] = None, 
                       limit: int = 100) -> List[Dict[str, Any]]:
        """Get monitoring metrics with optional filtering."""
        params = []
        where_clauses = []
        
        if metric_name:
            where_clauses.append("metric_name = $1")
            params.append(metric_name)
        
        if time_range:
            param_idx = len(params) + 1
            where_clauses.append(f"recorded_at >= CURRENT_TIMESTAMP - INTERVAL '{time_range} minutes'")
        
        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        query = f"""
        SELECT id, metric_name, metric_value, metric_unit, tags, recorded_at
        FROM monitoring_metrics
        {where_clause}
        ORDER BY recorded_at DESC
        LIMIT {limit}
        """
        
        try:
            results = await execute_query(query, *params)
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error fetching metrics: {str(e)}")
            raise
    
    async def get_metric_aggregates(self, metric_name: str, time_range: int, 
                                 interval: str = '5 minutes',
                                 agg_function: str = 'avg') -> List[Dict[str, Any]]:
        """Get aggregated metrics over time intervals."""
        valid_agg_functions = ['avg', 'min', 'max', 'sum', 'count']
        if agg_function.lower() not in valid_agg_functions:
            agg_function = 'avg'
        
        query = f"""
        SELECT 
            time_bucket('{interval}'::interval, recorded_at) AS time_bucket,
            {agg_function}(metric_value) AS value,
            metric_unit
        FROM monitoring_metrics
        WHERE metric_name = $1 
        AND recorded_at >= CURRENT_TIMESTAMP - INTERVAL '{time_range} minutes'
        GROUP BY time_bucket, metric_unit
        ORDER BY time_bucket DESC
        """
        
        try:
            results = await execute_query(query, metric_name)
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error fetching metric aggregates for {metric_name}: {str(e)}")
            raise
    
    async def create_alert(self, name: str, severity: str, message: str, 
                        source: str, tags: Optional[Dict[str, Any]] = None) -> int:
        """Create a new alert."""
        query = """
        INSERT INTO monitoring_alerts (alert_name, severity, message, source, tags)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """
        
        try:
            results = await execute_query(
                query, 
                name,
                severity, 
                message,
                source,
                json.dumps(tags) if tags else None
            )
            return results[0]['id']
        except Exception as e:
            logger.error(f"Error creating alert {name}: {str(e)}")
            raise
    
    async def update_alert_status(self, alert_id: int, status: str) -> bool:
        """Update alert status (active, acknowledged, resolved)."""
        extra_fields = ""
        if status.lower() == 'resolved':
            extra_fields = ", resolved_at = CURRENT_TIMESTAMP"
            
        query = f"""
        UPDATE monitoring_alerts
        SET status = $1{extra_fields}
        WHERE id = $2
        RETURNING id
        """
        
        try:
            results = await execute_query(query, status.lower(), alert_id)
            return bool(results)
        except Exception as e:
            logger.error(f"Error updating alert {alert_id} status to {status}: {str(e)}")
            raise
    
    async def get_alerts(self, status: Optional[str] = None, 
                      severity: Optional[str] = None, 
                      limit: int = 100) -> List[Dict[str, Any]]:
        """Get alerts with optional filtering."""
        params = []
        where_clauses = []
        
        if status:
            where_clauses.append("status = $1")
            params.append(status.lower())
        
        if severity:
            param_idx = len(params) + 1
            where_clauses.append(f"severity = ${param_idx}")
            params.append(severity.lower())
        
        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        query = f"""
        SELECT id, alert_name, severity, message, source, status, tags, 
               created_at, resolved_at
        FROM monitoring_alerts
        {where_clause}
        ORDER BY 
            CASE WHEN severity = 'critical' THEN 0
                 WHEN severity = 'high' THEN 1
                 WHEN severity = 'medium' THEN 2
                 WHEN severity = 'low' THEN 3
                 ELSE 4
            END,
            created_at DESC
        LIMIT {limit}
        """
        
        try:
            results = await execute_query(query, *params)
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error fetching alerts: {str(e)}")
            raise
    
    async def delete_old_metrics(self, older_than_days: int = 30) -> int:
        """Delete metrics older than the specified number of days."""
        query = """
        DELETE FROM monitoring_metrics
        WHERE recorded_at < CURRENT_TIMESTAMP - INTERVAL '$1 days'
        """
        
        try:
            results = await execute_query(query, older_than_days)
            return len(results) if results else 0
        except Exception as e:
            logger.error(f"Error deleting old metrics: {str(e)}")
            raise
