"""
Business Rules Metrics Module

This module provides functionality for tracking and analyzing rule metrics:
- Rule execution statistics
- Violation tracking
- Performance metrics
- Effectiveness analysis
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

async def get_rule_metrics(
    dataset_id: str, 
    time_period: str = "all", 
    rule_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get metrics and performance statistics for rules applied to a dataset.
    
    Args:
        dataset_id: ID of the dataset
        time_period: Time period for metrics (day, week, month, all)
        rule_ids: Optional list of specific rule IDs to get metrics for
        
    Returns:
        Dictionary with rule metrics and statistics
    """
    try:
        # Import here to avoid circular imports
        from api.repositories import business_rules_repository
        
        # Get rules for the dataset
        rules = await business_rules_repository.get_rules_by_dataset(dataset_id)
        
        # Filter by rule_ids if provided
        if rule_ids:
            rules = [r for r in rules if r["id"] in rule_ids]
            
        # Get rule execution history
        execution_history = await business_rules_repository.get_rule_execution_history(
            dataset_id, rule_ids, get_time_range(time_period)
        )
        
        # Calculate metrics
        metrics = calculate_rule_metrics(rules, execution_history)
        
        # Add time series data
        metrics["time_series"] = generate_time_series(execution_history, time_period)
        
        # Add impact analysis
        metrics["impact_analysis"] = analyze_rule_impact(rules, execution_history)
        
        return metrics
    except Exception as e:
        logger.error(f"Error getting rule metrics: {str(e)}")
        return {
            "error": str(e),
            "rules_count": 0,
            "execution_count": 0,
            "time_series": {},
            "rule_metrics": []
        }

def get_time_range(time_period: str) -> Optional[datetime]:
    """
    Get the start time for a given time period.
    
    Args:
        time_period: Time period (day, week, month, all)
        
    Returns:
        Start datetime or None for 'all'
    """
    now = datetime.utcnow()
    
    if time_period == "day":
        return now - timedelta(days=1)
    elif time_period == "week":
        return now - timedelta(weeks=1)
    elif time_period == "month":
        return now - timedelta(days=30)
    else:  # "all"
        return None

def calculate_rule_metrics(
    rules: List[Dict[str, Any]], 
    execution_history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate metrics for rules based on execution history.
    
    Args:
        rules: List of rule dictionaries
        execution_history: List of rule execution history entries
        
    Returns:
        Dictionary with rule metrics
    """
    # Group history by rule_id
    history_by_rule = defaultdict(list)
    for entry in execution_history:
        history_by_rule[entry["rule_id"]].append(entry)
    
    # Calculate metrics for each rule
    rule_metrics = []
    total_executions = 0
    total_violations = 0
    
    for rule in rules:
        rule_id = rule["id"]
        rule_history = history_by_rule.get(rule_id, [])
        
        # Calculate rule-specific metrics
        executions = len(rule_history)
        violations = sum(1 for e in rule_history if not e.get("success", False))
        violation_rate = violations / executions if executions > 0 else 0
        
        # Add to totals
        total_executions += executions
        total_violations += violations
        
        # Calculate trend (positive means improving, negative means deteriorating)
        trend = calculate_trend(rule_history)
        
        rule_metrics.append({
            "rule_id": rule_id,
            "rule_name": rule.get("name", "Unknown"),
            "executions": executions,
            "violations": violations,
            "violation_rate": round(violation_rate, 4),
            "trend": trend,
            "last_executed": max([e.get("timestamp") for e in rule_history], default=None) if rule_history else None
        })
    
    # Sort by violation rate (highest first)
    rule_metrics.sort(key=lambda x: x["violation_rate"], reverse=True)
    
    return {
        "rules_count": len(rules),
        "execution_count": total_executions,
        "violation_count": total_violations,
        "overall_violation_rate": round(total_violations / total_executions, 4) if total_executions > 0 else 0,
        "rule_metrics": rule_metrics
    }

def calculate_trend(history: List[Dict[str, Any]]) -> float:
    """
    Calculate trend in rule violations over time.
    
    Args:
        history: List of rule execution history entries
        
    Returns:
        Trend value (positive means improving, negative means deteriorating)
    """
    if len(history) < 5:
        return 0.0
        
    # Sort by timestamp
    sorted_history = sorted(history, key=lambda x: x.get("timestamp", ""))
    
    # Get success values (1 for success, 0 for failure)
    successes = [1 if e.get("success", False) else 0 for e in sorted_history]
    
    # Calculate trend using simple linear regression
    x = list(range(len(successes)))
    y = successes
    
    # Calculate slope
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(x_i * y_i for x_i, y_i in zip(x, y))
    sum_xx = sum(x_i * x_i for x_i in x)
    
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x) if (n * sum_xx - sum_x * sum_x) != 0 else 0
    
    return round(slope * 10, 2)  # Scale for readability

def generate_time_series(
    execution_history: List[Dict[str, Any]], 
    time_period: str
) -> Dict[str, Any]:
    """
    Generate time series data for rule executions.
    
    Args:
        execution_history: List of rule execution history entries
        time_period: Time period (day, week, month, all)
        
    Returns:
        Dictionary with time series data
    """
    if not execution_history:
        return {"labels": [], "executions": [], "violations": []}
        
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(execution_history)
    
    # Ensure timestamp column exists
    if "timestamp" not in df.columns:
        return {"labels": [], "executions": [], "violations": []}
        
    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # Set frequency based on time period
    if time_period == "day":
        freq = "H"  # Hourly
        format_str = "%H:%M"
    elif time_period == "week":
        freq = "D"  # Daily
        format_str = "%a"
    elif time_period == "month":
        freq = "D"  # Daily
        format_str = "%d"
    else:  # "all"
        freq = "W"  # Weekly
        format_str = "%Y-%m-%d"
    
    # Group by time period
    df["period"] = df["timestamp"].dt.to_period(freq)
    
    # Count executions and violations per period
    grouped = df.groupby("period").agg(
        executions=("rule_id", "count"),
        violations=("success", lambda x: (~x).sum())
    ).reset_index()
    
    # Convert period to string for labels
    grouped["label"] = grouped["period"].dt.to_timestamp().dt.strftime(format_str)
    
    return {
        "labels": grouped["label"].tolist(),
        "executions": grouped["executions"].tolist(),
        "violations": grouped["violations"].tolist()
    }

def analyze_rule_impact(
    rules: List[Dict[str, Any]], 
    execution_history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze the impact of rules on data quality.
    
    Args:
        rules: List of rule dictionaries
        execution_history: List of rule execution history entries
        
    Returns:
        Dictionary with impact analysis
    """
    # Group rules by type
    rules_by_type = defaultdict(list)
    for rule in rules:
        rule_type = rule.get("rule_type", "validation")
        rules_by_type[rule_type].append(rule["id"])
    
    # Calculate impact by rule type
    impact_by_type = {}
    for rule_type, rule_ids in rules_by_type.items():
        # Filter history for these rules
        type_history = [e for e in execution_history if e.get("rule_id") in rule_ids]
        
        # Calculate metrics
        executions = len(type_history)
        violations = sum(1 for e in type_history if not e.get("success", False))
        violation_rate = violations / executions if executions > 0 else 0
        
        impact_by_type[rule_type] = {
            "rules_count": len(rule_ids),
            "executions": executions,
            "violations": violations,
            "violation_rate": round(violation_rate, 4)
        }
    
    # Calculate severity distribution
    severity_counts = defaultdict(int)
    for rule in rules:
        severity = rule.get("severity", "medium")
        severity_counts[severity] += 1
    
    return {
        "impact_by_type": impact_by_type,
        "severity_distribution": dict(severity_counts),
        "top_violated_rules": get_top_violated_rules(rules, execution_history, 5)
    }

def get_top_violated_rules(
    rules: List[Dict[str, Any]], 
    execution_history: List[Dict[str, Any]], 
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Get the top most violated rules.
    
    Args:
        rules: List of rule dictionaries
        execution_history: List of rule execution history entries
        limit: Maximum number of rules to return
        
    Returns:
        List of top violated rules with metrics
    """
    # Create rule lookup
    rule_lookup = {r["id"]: r for r in rules}
    
    # Group history by rule_id
    violations_by_rule = defaultdict(int)
    executions_by_rule = defaultdict(int)
    
    for entry in execution_history:
        rule_id = entry.get("rule_id")
        if not rule_id:
            continue
            
        executions_by_rule[rule_id] += 1
        if not entry.get("success", False):
            violations_by_rule[rule_id] += 1
    
    # Calculate violation rates
    violation_rates = {}
    for rule_id, executions in executions_by_rule.items():
        violations = violations_by_rule.get(rule_id, 0)
        violation_rates[rule_id] = violations / executions if executions > 0 else 0
    
    # Sort by violation rate and get top N
    top_rule_ids = sorted(
        violation_rates.keys(), 
        key=lambda r: violation_rates[r], 
        reverse=True
    )[:limit]
    
    # Build result
    result = []
    for rule_id in top_rule_ids:
        rule = rule_lookup.get(rule_id, {})
        executions = executions_by_rule.get(rule_id, 0)
        violations = violations_by_rule.get(rule_id, 0)
        
        result.append({
            "rule_id": rule_id,
            "rule_name": rule.get("name", "Unknown"),
            "rule_type": rule.get("rule_type", "validation"),
            "severity": rule.get("severity", "medium"),
            "executions": executions,
            "violations": violations,
            "violation_rate": round(violations / executions, 4) if executions > 0 else 0
        })
    
    return result

async def record_rule_execution(
    rule_id: str,
    dataset_id: str,
    success: bool,
    violation_count: int = 0,
    execution_time: float = 0.0,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Record a rule execution event for metrics tracking.
    
    Args:
        rule_id: ID of the rule
        dataset_id: ID of the dataset
        success: Whether the rule execution was successful
        violation_count: Number of violations found
        execution_time: Time taken to execute the rule in seconds
        metadata: Additional metadata about the execution
        
    Returns:
        True if the execution was recorded successfully, False otherwise
    """
    try:
        # Import here to avoid circular imports
        from api.repositories import business_rules_repository
        
        # Create execution record
        execution_record = {
            "rule_id": rule_id,
            "dataset_id": dataset_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": success,
            "violation_count": violation_count,
            "execution_time": execution_time,
            "metadata": metadata or {}
        }
        
        # Record execution
        await business_rules_repository.record_rule_execution(execution_record)
        
        # Update rule statistics
        await update_rule_statistics(rule_id, success, violation_count, execution_time)
        
        return True
    except Exception as e:
        logger.error(f"Error recording rule execution: {str(e)}")
        return False

async def update_rule_statistics(
    rule_id: str,
    success: bool,
    violation_count: int = 0,
    execution_time: float = 0.0
) -> bool:
    """
    Update rule statistics based on execution results.
    
    Args:
        rule_id: ID of the rule
        success: Whether the rule execution was successful
        violation_count: Number of violations found
        execution_time: Time taken to execute the rule in seconds
        
    Returns:
        True if the statistics were updated successfully, False otherwise
    """
    try:
        # Import here to avoid circular imports
        from api.repositories import business_rules_repository
        
        # Get current rule
        rule = await business_rules_repository.get_rule(rule_id)
        if not rule:
            return False
            
        # Update execution count and success rate
        execution_count = rule.get("execution_count", 0) + 1
        success_count = rule.get("success_count", 0) + (1 if success else 0)
        total_violations = rule.get("total_violations", 0) + violation_count
        
        # Calculate new metrics
        success_rate = success_count / execution_count if execution_count > 0 else 0
        avg_execution_time = (
            (rule.get("avg_execution_time", 0) * (execution_count - 1) + execution_time) / execution_count
        ) if execution_count > 0 else 0
        
        # Update rule
        updates = {
            "execution_count": execution_count,
            "success_count": success_count,
            "success_rate": success_rate,
            "total_violations": total_violations,
            "avg_execution_time": avg_execution_time,
            "last_executed": datetime.utcnow().isoformat()
        }
        
        await business_rules_repository.update_rule(rule_id, updates)
        return True
    except Exception as e:
        logger.error(f"Error updating rule statistics: {str(e)}")
        return False
