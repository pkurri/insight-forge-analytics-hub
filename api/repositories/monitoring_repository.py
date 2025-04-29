
"""
Repository for monitoring metrics and alerts.
"""
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from api.db.connection import get_db_session
from sqlalchemy import text

logger = logging.getLogger(__name__)

class MonitoringRepository:
    """Repository for monitoring metrics and alerts."""
    
    async def record_metric(self, name: str, value: float, unit: Optional[str] = None, 
                         tags: Optional[Dict[str, Any]] = None) -> int:
        """Record a monitoring metric."""
        query = """
        INSERT INTO {settings.DB_SCHEMA}.monitoring_metrics (metric_name, metric_value, metric_unit, tags)
        VALUES (:metric_name, :metric_value, :metric_unit, :tags)
        RETURNING id
        """
        
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text(query),
                    {
                        "metric_name": name,
                        "metric_value": value,
                        "metric_unit": unit,
                        "tags": json.dumps(tags) if tags else None
                    }
                )
                await session.commit()
                row = result.fetchone()
                return row[0] if row else None
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
            where_clauses.append("metric_name = :metric_name")
            params.append({"metric_name": metric_name})
        
        if time_range:
            param_idx = len(params) + 1
            where_clauses.append(f"recorded_at >= CURRENT_TIMESTAMP - INTERVAL '{time_range} minutes'")
        
        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        query = f"""
        SELECT id, metric_name, metric_value, metric_unit, tags, recorded_at
        FROM {settings.DB_SCHEMA}.monitoring_metrics
        {where_clause}
        ORDER BY recorded_at DESC
        LIMIT {limit}
        """
        
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text(query),
                    params
                )
                await session.commit()
                rows = result.fetchall()
                return [dict(row) for row in rows]
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
        FROM {settings.DB_SCHEMA}.monitoring_metrics
        WHERE metric_name = :metric_name 
        AND recorded_at >= CURRENT_TIMESTAMP - INTERVAL '{time_range} minutes'
        GROUP BY time_bucket, metric_unit
        ORDER BY time_bucket DESC
        """
        
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text(query),
                    {
                        "metric_name": metric_name
                    }
                )
                await session.commit()
                rows = result.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching metric aggregates for {metric_name}: {str(e)}")
            raise
    
    async def create_alert(self, name: str, severity: str, message: str, 
                        source: str, tags: Optional[Dict[str, Any]] = None) -> int:
        """Create a new alert."""
        query = """
        INSERT INTO {settings.DB_SCHEMA}.monitoring_alerts (alert_name, severity, message, source, tags)
        VALUES (:alert_name, :severity, :message, :source, :tags)
        RETURNING id
        """
        
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text(query),
                    {
                        "alert_name": name,
                        "severity": severity,
                        "message": message,
                        "source": source,
                        "tags": json.dumps(tags) if tags else None
                    }
                )
                await session.commit()
                row = result.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Error creating alert {name}: {str(e)}")
            raise
    
    async def update_alert_status(self, alert_id: int, status: str) -> bool:
        """Update alert status (active, acknowledged, resolved)."""
        extra_fields = ""
        if status.lower() == 'resolved':
            extra_fields = ", resolved_at = CURRENT_TIMESTAMP"
            
        query = f"""
        UPDATE {settings.DB_SCHEMA}.monitoring_alerts
        SET status = :status{extra_fields}
        WHERE id = :alert_id
        RETURNING id
        """
        
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text(query),
                    {
                        "status": status.lower(),
                        "alert_id": alert_id
                    }
                )
                await session.commit()
                row = result.fetchone()
                return bool(row)
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
            where_clauses.append("status = :status")
            params.append({"status": status.lower()})
        
        if severity:
            where_clauses.append("severity = :severity")
            params.append({"severity": severity})
        
        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        query = f"""
        SELECT id, alert_name, severity, message, source, status, tags, 
               created_at, resolved_at
        FROM {settings.DB_SCHEMA}.monitoring_alerts
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
            async with get_db_session() as session:
                result = await session.execute(
                    text(query),
                    params
                )
                await session.commit()
                rows = result.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching alerts: {str(e)}")
            raise
    
    async def delete_old_metrics(self, older_than_days: int = 30) -> int:
        """Delete metrics older than the specified number of days."""
        query = """
        DELETE FROM {settings.DB_SCHEMA}.monitoring_metrics
        WHERE recorded_at < CURRENT_TIMESTAMP - INTERVAL ':days days'
        """
        
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text(query),
                    {
                        "days": older_than_days
                    }
                )
                await session.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"Error deleting old metrics: {str(e)}")
            raise
