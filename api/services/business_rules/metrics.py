"""
Business Rules Metrics Module

This module provides functions for tracking and recording business rule execution metrics.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

from api.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

async def record_rule_execution(
    rule_id: str,
    dataset_id: str,
    success: bool,
    violation_count: int,
    execution_time: float,
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Record metrics for a rule execution.
    
    Args:
        rule_id: ID of the executed rule
        dataset_id: ID of the dataset
        success: Whether the rule execution was successful
        violation_count: Number of violations found
        execution_time: Time taken to execute the rule
        meta: Optional metadata about the execution
        
    Returns:
        Dict containing recording status
    """
    try:
        # Import here to avoid circular imports
        from api.repositories import metrics_repository
        
        # Prepare metrics data
        metrics_data = {
            "rule_id": rule_id,
            "dataset_id": dataset_id,
            "success": success,
            "violation_count": violation_count,
            "execution_time": execution_time,
            "timestamp": datetime.utcnow().isoformat(),
            "meta": meta or {}
        }
        
        # Store metrics
        await metrics_repository.store_rule_execution_metrics(metrics_data)
        
        return {
            "success": True,
            "metrics": metrics_data
        }
    except Exception as e:
        logger.error(f"Error recording rule execution metrics: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def get_rule_execution_stats(
    rule_id: str,
    time_range: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get execution statistics for a rule.
    
    Args:
        rule_id: ID of the rule
        time_range: Optional time range to filter by (e.g., "1d", "7d", "30d")
        
    Returns:
        Dict containing execution statistics
    """
    try:
        # Import here to avoid circular imports
        from api.repositories import metrics_repository
        
        # Get metrics
        metrics = await metrics_repository.get_rule_execution_metrics(
            rule_id,
            time_range
        )
        
        if not metrics:
            return {
                "success": True,
                "stats": {
                    "total_executions": 0,
                    "success_rate": 0,
                    "avg_execution_time": 0,
                    "total_violations": 0
                }
            }
            
        # Calculate statistics
        total_executions = len(metrics)
        success_count = sum(1 for m in metrics if m["success"])
        success_rate = success_count / total_executions if total_executions > 0 else 0
        avg_execution_time = sum(m["execution_time"] for m in metrics) / total_executions if total_executions > 0 else 0
        total_violations = sum(m["violation_count"] for m in metrics)
        
        return {
            "success": True,
            "stats": {
                "total_executions": total_executions,
                "success_rate": success_rate,
                "avg_execution_time": avg_execution_time,
                "total_violations": total_violations
            }
        }
    except Exception as e:
        logger.error(f"Error getting rule execution stats: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def get_dataset_rule_stats(
    dataset_id: str,
    time_range: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get execution statistics for all rules in a dataset.
    
    Args:
        dataset_id: ID of the dataset
        time_range: Optional time range to filter by
        
    Returns:
        Dict containing dataset rule statistics
    """
    try:
        # Import here to avoid circular imports
        from api.repositories import metrics_repository
        
        # Get metrics
        metrics = await metrics_repository.get_dataset_rule_metrics(
            dataset_id,
            time_range
        )
        
        if not metrics:
            return {
                "success": True,
                "stats": {
                    "total_rules": 0,
                    "total_executions": 0,
                    "avg_success_rate": 0,
                    "total_violations": 0
                }
            }
            
        # Calculate statistics
        total_rules = len(set(m["rule_id"] for m in metrics))
        total_executions = len(metrics)
        success_count = sum(1 for m in metrics if m["success"])
        avg_success_rate = success_count / total_executions if total_executions > 0 else 0
        total_violations = sum(m["violation_count"] for m in metrics)
        
        # Calculate per-rule statistics
        rule_stats = {}
        for rule_id in set(m["rule_id"] for m in metrics):
            rule_metrics = [m for m in metrics if m["rule_id"] == rule_id]
            rule_executions = len(rule_metrics)
            rule_success = sum(1 for m in rule_metrics if m["success"])
            rule_success_rate = rule_success / rule_executions if rule_executions > 0 else 0
            rule_violations = sum(m["violation_count"] for m in rule_metrics)
            
            rule_stats[rule_id] = {
                "executions": rule_executions,
                "success_rate": rule_success_rate,
                "violations": rule_violations
            }
            
        return {
            "success": True,
            "stats": {
                "total_rules": total_rules,
                "total_executions": total_executions,
                "avg_success_rate": avg_success_rate,
                "total_violations": total_violations,
                "rule_stats": rule_stats
            }
        }
    except Exception as e:
        logger.error(f"Error getting dataset rule stats: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def record_rule_generation(
    dataset_id: str,
    engine: str,
    rule_count: int,
    success: bool,
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Record metrics for rule generation.
    
    Args:
        dataset_id: ID of the dataset
        engine: Engine used for generation
        rule_count: Number of rules generated
        success: Whether generation was successful
        meta: Optional metadata about the generation
        
    Returns:
        Dict containing recording status
    """
    try:
        # Import here to avoid circular imports
        from api.repositories import metrics_repository
        
        # Prepare metrics data
        metrics_data = {
            "dataset_id": dataset_id,
            "engine": engine,
            "rule_count": rule_count,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "meta": meta or {}
        }
        
        # Store metrics
        await metrics_repository.store_rule_generation_metrics(metrics_data)
        
        return {
            "success": True,
            "metrics": metrics_data
        }
    except Exception as e:
        logger.error(f"Error recording rule generation metrics: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
