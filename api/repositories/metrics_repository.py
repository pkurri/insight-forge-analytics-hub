"""
Metrics Repository Module

This module provides data access functions for storing and retrieving business rule metrics.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from api.config.settings import get_settings
from api.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)
settings = get_settings()

class MetricsRepository(BaseRepository):
    """Repository for business rule metrics."""
    
    async def store_rule_execution_metrics(self, metrics_data: Dict[str, Any]) -> bool:
        """
        Store rule execution metrics.
        
        Args:
            metrics_data: Dictionary containing metrics data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add metadata
            metrics_data["created_at"] = datetime.utcnow().isoformat()
            
            # Store in database
            query = """
                INSERT INTO rule_execution_metrics (
                    rule_id,
                    dataset_id,
                    success,
                    violation_count,
                    execution_time,
                    timestamp,
                    meta,
                    created_at
                ) VALUES (
                    :rule_id,
                    :dataset_id,
                    :success,
                    :violation_count,
                    :execution_time,
                    :timestamp,
                    :meta,
                    :created_at
                )
            """
            
            await self.execute(query, metrics_data)
            return True
        except Exception as e:
            logger.error(f"Error storing rule execution metrics: {str(e)}")
            return False
            
    async def get_rule_execution_metrics(
        self,
        rule_id: str,
        time_range: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get rule execution metrics.
        
        Args:
            rule_id: ID of the rule
            time_range: Optional time range to filter by (e.g., "1d", "7d", "30d")
            
        Returns:
            List of metrics dictionaries
        """
        try:
            # Build query
            query = """
                SELECT *
                FROM rule_execution_metrics
                WHERE rule_id = :rule_id
            """
            params = {"rule_id": rule_id}
            
            # Add time range filter if specified
            if time_range:
                days = int(time_range[:-1])  # Extract number from "1d", "7d", etc.
                query += " AND timestamp >= :start_time"
                params["start_time"] = (datetime.utcnow() - timedelta(days=days)).isoformat()
                
            query += " ORDER BY timestamp DESC"
            
            # Execute query
            result = await self.fetch_all(query, params)
            
            # Convert to list of dicts
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Error getting rule execution metrics: {str(e)}")
            return []
            
    async def get_dataset_rule_metrics(
        self,
        dataset_id: str,
        time_range: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get metrics for all rules in a dataset.
        
        Args:
            dataset_id: ID of the dataset
            time_range: Optional time range to filter by
            
        Returns:
            List of metrics dictionaries
        """
        try:
            # Build query
            query = """
                SELECT *
                FROM rule_execution_metrics
                WHERE dataset_id = :dataset_id
            """
            params = {"dataset_id": dataset_id}
            
            # Add time range filter if specified
            if time_range:
                days = int(time_range[:-1])
                query += " AND timestamp >= :start_time"
                params["start_time"] = (datetime.utcnow() - timedelta(days=days)).isoformat()
                
            query += " ORDER BY timestamp DESC"
            
            # Execute query
            result = await self.fetch_all(query, params)
            
            # Convert to list of dicts
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Error getting dataset rule metrics: {str(e)}")
            return []
            
    async def store_rule_generation_metrics(self, metrics_data: Dict[str, Any]) -> bool:
        """
        Store rule generation metrics.
        
        Args:
            metrics_data: Dictionary containing metrics data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add metadata
            metrics_data["created_at"] = datetime.utcnow().isoformat()
            
            # Store in database
            query = """
                INSERT INTO rule_generation_metrics (
                    dataset_id,
                    engine,
                    rule_count,
                    success,
                    timestamp,
                    meta,
                    created_at
                ) VALUES (
                    :dataset_id,
                    :engine,
                    :rule_count,
                    :success,
                    :timestamp,
                    :meta,
                    :created_at
                )
            """
            
            await self.execute(query, metrics_data)
            return True
        except Exception as e:
            logger.error(f"Error storing rule generation metrics: {str(e)}")
            return False
            
    async def get_rule_generation_metrics(
        self,
        dataset_id: str,
        time_range: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get rule generation metrics.
        
        Args:
            dataset_id: ID of the dataset
            time_range: Optional time range to filter by
            
        Returns:
            List of metrics dictionaries
        """
        try:
            # Build query
            query = """
                SELECT *
                FROM rule_generation_metrics
                WHERE dataset_id = :dataset_id
            """
            params = {"dataset_id": dataset_id}
            
            # Add time range filter if specified
            if time_range:
                days = int(time_range[:-1])
                query += " AND timestamp >= :start_time"
                params["start_time"] = (datetime.utcnow() - timedelta(days=days)).isoformat()
                
            query += " ORDER BY timestamp DESC"
            
            # Execute query
            result = await self.fetch_all(query, params)
            
            # Convert to list of dicts
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Error getting rule generation metrics: {str(e)}")
            return []
            
    async def cleanup_old_metrics(self, retention_days: Optional[int] = None) -> bool:
        """
        Clean up old metrics data.
        
        Args:
            retention_days: Number of days to retain metrics for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Use configured retention period if not specified
            if retention_days is None:
                retention_days = settings.MONITORING_METRICS_RETENTION_DAYS
                
            # Calculate cutoff date
            cutoff_date = (datetime.utcnow() - timedelta(days=retention_days)).isoformat()
            
            # Delete old execution metrics
            exec_query = """
                DELETE FROM rule_execution_metrics
                WHERE timestamp < :cutoff_date
            """
            await self.execute(exec_query, {"cutoff_date": cutoff_date})
            
            # Delete old generation metrics
            gen_query = """
                DELETE FROM rule_generation_metrics
                WHERE timestamp < :cutoff_date
            """
            await self.execute(gen_query, {"cutoff_date": cutoff_date})
            
            return True
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {str(e)}")
            return False 