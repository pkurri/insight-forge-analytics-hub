"""
Core Business Rules Service Module

This module provides the main BusinessRulesService class with core functionality for:
- Managing business rules (CRUD operations)
- Rule caching
- Service initialization
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid
from cachetools import TTLCache

from config.settings import get_settings
from db.connection import get_db_session

# Import submodules
from services.business_rules.validators import validate_rule_format, validate_rule_condition
from services.business_rules.executors import get_execution_function
from services.business_rules.generators import generate_rules_with_engine
from services.business_rules.metrics import get_rule_metrics, record_rule_execution
from services.business_rules.suggestions import suggest_rules_from_data

settings = get_settings()
logger = logging.getLogger(__name__)

class BusinessRulesService:
    """
    Service for managing and executing business rules.
    
    This class provides the core functionality for business rules management,
    delegating specialized operations to submodules.
    """
    
    def __init__(self):
        """Initialize the service components and caching."""
        # Initialize cache with TTL (5 minutes)
        self.rules_cache = TTLCache(maxsize=100, ttl=300)
        
    async def invalidate_cache(self, dataset_id: Optional[str] = None):
        """
        Invalidate the rules cache for a specific dataset or completely.
        
        Args:
            dataset_id: Optional dataset ID to invalidate cache for
        """
        if dataset_id:
            if dataset_id in self.rules_cache:
                del self.rules_cache[dataset_id]
        else:
            self.rules_cache.clear()
            
    async def load_rules(self, dataset_id: str) -> List[Dict[str, Any]]:
        """
        Load all active rules for a dataset, using cache if available.

        Args:
            dataset_id: ID of the dataset to load rules for
        Returns:
            List of active rules for the dataset
        """
        try:
            # Use cache to avoid redundant DB queries
            if dataset_id in self.rules_cache:
                return self.rules_cache[dataset_id]
                
            # Import here to avoid circular imports
            from repositories import business_rules_repository
            
            # Fetch rules from repository
            rules = await business_rules_repository.get_rules_by_dataset(dataset_id)
            
            # Cache the results
            self.rules_cache[dataset_id] = rules
            return rules
        except Exception as e:
            logger.error(f"Error loading rules: {str(e)}")
            return []
            
    async def get_rules_for_dataset(self, dataset_id: str, rule_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get rules for a dataset, optionally filtered by rule IDs.
        
        Args:
            dataset_id: ID of the dataset
            rule_ids: Optional list of rule IDs to filter by
            
        Returns:
            List of rule dictionaries
        """
        try:
            # Import here to avoid circular imports
            from repositories import business_rules_repository
            
            # Get all rules for the dataset
            rules = await business_rules_repository.get_rules_by_dataset(dataset_id)
            
            # Filter by rule IDs if provided
            if rule_ids:
                rules = [r for r in rules if r["id"] in rule_ids]
                
            # Sort by execution order if available
            rules.sort(key=lambda r: r.get("execution_order", 0))
            
            return rules
        except Exception as e:
            logger.error(f"Error getting rules for dataset {dataset_id}: {str(e)}")
            return []
            
    async def create_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new business rule, validating and enriching the rule as needed.

        Args:
            rule_data: Dictionary containing rule information
        Returns:
            Created rule object
        Raises:
            ValueError: If rule format or condition is invalid
        """
        try:
            # Import here to avoid circular imports
            from repositories import business_rules_repository
            
            # Validate rule format
            if not await validate_rule_format(rule_data):
                raise ValueError("Invalid rule format")

            # Assign a unique rule ID if not provided
            if "id" not in rule_data:
                rule_data["id"] = str(uuid.uuid4())

            # Validate the rule's condition
            if not await validate_rule_condition(rule_data["condition"]):
                raise ValueError("Invalid rule condition")

            # Add timestamps
            now = datetime.utcnow().isoformat()
            rule_data["created_at"] = now
            rule_data["updated_at"] = now

            # Persist rule in the database
            rule = await business_rules_repository.create_rule(rule_data)

            # Update cache
            dataset_id = rule_data["dataset_id"]
            await self.invalidate_cache(dataset_id)
            
            return rule
        except ValueError as e:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error creating rule: {str(e)}")
            raise ValueError(f"Failed to create rule: {str(e)}")
            
    async def create_rules(self, dataset_id: str, rules_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple business rules in a batch operation.
        
        Args:
            dataset_id: ID of the dataset to associate with the rules
            rules_data: List of dictionaries containing rule data
            
        Returns:
            Dict containing information about created rules and any failures
        """
        created_rules = []
        failed_rules = []
        
        for rule_data in rules_data:
            try:
                # Ensure dataset_id is set for each rule
                if "dataset_id" not in rule_data:
                    rule_data["dataset_id"] = dataset_id
                
                # Create the rule
                result = await self.create_rule(rule_data)
                created_rules.append(result)
            except ValueError as e:
                # Track failed rules with their errors
                failed_rules.append({
                    "rule_data": rule_data,
                    "error": str(e)
                })
            except Exception as e:
                logger.error(f"Error creating rule in batch: {str(e)}")
                failed_rules.append({
                    "rule_data": rule_data,
                    "error": str(e)
                })
        
        # Invalidate cache for this dataset to ensure fresh data
        await self.invalidate_cache(dataset_id)
        
        return {
            "success": len(created_rules) > 0,
            "created_rules": created_rules,
            "failed_rules": failed_rules,
            "total_submitted": len(rules_data),
            "total_created": len(created_rules),
            "total_failed": len(failed_rules),
            "dataset_id": dataset_id
        }
            
    async def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing business rule.

        Args:
            rule_id: ID of the rule to update
            updates: Dictionary of fields to update
        Returns:
            Updated rule object
        Raises:
            ValueError: If the updated condition is invalid
        """
        try:
            # Import here to avoid circular imports
            from repositories import business_rules_repository
            
            # Get existing rule
            existing_rule = await business_rules_repository.get_rule(rule_id)
            if not existing_rule:
                raise ValueError(f"Rule with ID {rule_id} not found")
                
            # Validate condition if updated
            if "condition" in updates:
                if not await validate_rule_condition(updates["condition"]):
                    raise ValueError("Invalid rule condition")
                    
            # Add updated timestamp
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            # Update rule in database
            updated_rule = await business_rules_repository.update_rule(rule_id, updates)
            
            # Invalidate cache for this dataset
            await self.invalidate_cache(existing_rule["dataset_id"])
            
            return updated_rule
        except ValueError as e:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error updating rule: {str(e)}")
            raise ValueError(f"Failed to update rule: {str(e)}")
            
    async def delete_rule(self, rule_id: str) -> bool:
        """
        Delete a business rule.
        
        Args:
            rule_id: ID of the rule to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from repositories import business_rules_repository
            
            # Get existing rule to find dataset_id
            existing_rule = await business_rules_repository.get_rule(rule_id)
            if not existing_rule:
                return False
                
            # Delete rule
            result = await business_rules_repository.delete_rule(rule_id)
            
            # Invalidate cache for this dataset
            await self.invalidate_cache(existing_rule["dataset_id"])
            
            return result
        except Exception as e:
            logger.error(f"Error deleting rule: {str(e)}")
            return False
            
    async def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific business rule by ID.

        Args:
            rule_id: ID of the rule to retrieve
        Returns:
            Rule object as a dictionary, or None if not found
        """
        try:
            # Import here to avoid circular imports
            from repositories import business_rules_repository
            
            return await business_rules_repository.get_rule(rule_id)
        except Exception as e:
            logger.error(f"Error getting rule: {str(e)}")
            return None
            
    async def get_rules(self, dataset_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve business rules, optionally filtered by dataset.

        Args:
            dataset_id: Optional ID of the dataset to filter by
        Returns:
            List of rule objects as dictionaries
        """
        try:
            # Import here to avoid circular imports
            from repositories import business_rules_repository
            
            # If dataset_id is provided, use cached version if available
            if dataset_id and dataset_id in self.rules_cache:
                return self.rules_cache[dataset_id]
                
            # Otherwise fetch from database
            rules = await business_rules_repository.get_rules(dataset_id=dataset_id)
            
            # Cache if dataset_id was provided
            if dataset_id:
                self.rules_cache[dataset_id] = rules
                
            return rules
        except Exception as e:
            logger.error(f"Error getting rules: {str(e)}")
            return []
            
    async def import_rules(self, dataset_id: str, rules_json: str) -> Dict[str, Any]:
        """
        Import business rules from a JSON array.

        Args:
            dataset_id: ID of the dataset to import rules for
            rules_json: JSON string containing an array of rule objects
        Returns:
            Dict containing success status, imported/failed counts, and rule details
        """
        try:
            rules = json.loads(rules_json)
            if not isinstance(rules, list):
                raise ValueError("Invalid format: JSON must be an array of rule objects")
                
            imported_rules = []
            failed_rules = []
            
            for rule in rules:
                try:
                    # Add dataset ID and defaults
                    rule["dataset_id"] = dataset_id
                    rule["source"] = rule.get("source", "manual")
                    
                    # Create rule
                    created_rule = await self.create_rule(rule)
                    imported_rules.append(created_rule)
                except Exception as rule_error:
                    failed_rules.append({
                        "rule": rule.get("name", "Unknown"),
                        "error": str(rule_error)
                    })
            
            # Invalidate cache for this dataset
            await self.invalidate_cache(dataset_id)
            
            return {
                "success": len(imported_rules) > 0,
                "imported_count": len(imported_rules),
                "failed_count": len(failed_rules),
                "imported_rules": imported_rules,
                "failed_rules": failed_rules
            }
        except Exception as e:
            logger.error(f"Error importing rules: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "imported_count": 0,
                "failed_count": 0
            }
            
    async def generate_ai_rules(self, dataset_id: str, column_meta: Dict[str, Any], 
                               engine: str = "ai_default", model_type: str = None) -> Dict[str, Any]:
        """
        Generate business rules using different AI engines based on column meta.
        
        Args:
            dataset_id: ID of the dataset to generate rules for
            column_meta: Dictionary containing column information about the dataset
            engine: AI engine to use for rule generation
            model_type: Type of model to use for generation
            
        Returns:
            Dictionary containing generated rules and meta
        """
        try:
            # Delegate to the generators module
            result = await generate_rules_with_engine(
                dataset_id, column_meta, engine, model_type
            )
            
            # If rules were successfully generated and auto-created, invalidate cache
            if result.get("success") and result.get("rules_created", 0) > 0:
                await self.invalidate_cache(dataset_id)
                
            return result
        except Exception as e:
            logger.error(f"Error generating AI rules: {str(e)}")
            return {"success": False, "error": str(e)}
            
    async def get_rule_metrics(self, dataset_id: str, time_period: str = "all", rule_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get metrics and performance statistics for rules applied to a dataset.
        
        Args:
            dataset_id: ID of the dataset
            time_period: Time period for metrics (day, week, month, all)
            rule_ids: Optional list of specific rule IDs to get metrics for
            
        Returns:
            Dictionary with rule metrics and statistics
        """
        return await get_rule_metrics(dataset_id, time_period, rule_ids)
    
    async def suggest_rules_from_data(self, dataset_id: str, sample_data: List[Dict[str, Any]], 
                                    min_confidence: float = 0.7, max_suggestions: int = 10) -> Dict[str, Any]:
        """
        Generate rule suggestions based on sample data patterns.
        
        Args:
            dataset_id: ID of the dataset
            sample_data: Sample data to analyze for rule suggestions
            min_confidence: Minimum confidence threshold for suggestions
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            Dictionary with rule suggestions and metadata
        """
        return await suggest_rules_from_data(dataset_id, sample_data, min_confidence, max_suggestions)
    
    async def record_rule_execution(self, rule_id: str, dataset_id: str, success: bool, 
                                  violation_count: int = 0, execution_time: float = 0.0, 
                                  metadata: Optional[Dict[str, Any]] = None) -> bool:
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
        return await record_rule_execution(rule_id, dataset_id, success, violation_count, execution_time, metadata)
    
    # The apply_rules_to_dataset, validate_data_with_rules, and other execution methods
    # are moved to the executors.py module and imported from there
    
    # Import and re-export those methods for backward compatibility
    from services.business_rules.executors import (
        apply_rules_to_dataset, 
        apply_rule, 
        validate_data_with_rules,
        update_rule_stats
    )
