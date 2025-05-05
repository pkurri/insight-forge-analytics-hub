"""
Business Rules Service Module

This module provides the main service interface for business rules functionality.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.business_rules.manager import RuleManager
from services.business_rules.validators import (
    validate_rule_structure,
    validate_rule_condition,
    validate_execution_result,
    validate_dataset_for_rules
)
from services.business_rules.executors import execute_rule
from services.business_rules.generators import generate_rules_with_engine

logger = logging.getLogger(__name__)

class BusinessRulesService:
    """Service class for business rules functionality."""
    
    def __init__(self, db_session):
        """Initialize the business rules service.
        
        Args:
            db_session: Database session for rule operations
        """
        self.rule_manager = RuleManager(db_session)
        
    async def create_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new business rule.
        
        Args:
            rule_data: Dictionary containing rule data
            
        Returns:
            Dict containing the created rule or error information
        """
        return await self.rule_manager.create_rule(rule_data)
        
    async def get_rule(self, rule_id: str) -> Dict[str, Any]:
        """Get a business rule by ID.
        
        Args:
            rule_id: ID of the rule to retrieve
            
        Returns:
            Dict containing the rule or error information
        """
        return await self.rule_manager.get_rule(rule_id)
        
    async def update_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing business rule.
        
        Args:
            rule_id: ID of the rule to update
            rule_data: Dictionary containing updated rule data
            
        Returns:
            Dict containing the updated rule or error information
        """
        return await self.rule_manager.update_rule(rule_id, rule_data)
        
    async def delete_rule(self, rule_id: str) -> Dict[str, Any]:
        """Delete a business rule.
        
        Args:
            rule_id: ID of the rule to delete
            
        Returns:
            Dict containing success status or error information
        """
        return await self.rule_manager.delete_rule(rule_id)
        
    async def list_rules(
        self,
        dataset_id: Optional[str] = None,
        source: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List business rules with optional filtering.
        
        Args:
            dataset_id: Optional dataset ID to filter by
            source: Optional source to filter by
            severity: Optional severity to filter by
            limit: Maximum number of rules to return
            offset: Number of rules to skip
            
        Returns:
            Dict containing list of rules and total count
        """
        return await self.rule_manager.list_rules(
            dataset_id,
            source,
            severity,
            limit,
            offset
        )
        
    async def generate_rules(
        self,
        dataset_id: str,
        column_meta: Dict[str, Any],
        engine: str = "ai_default",
        model_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate business rules using the specified engine.
        
        Args:
            dataset_id: ID of the dataset to generate rules for
            column_meta: Dictionary containing column information
            engine: Engine to use for rule generation
            model_type: Optional model type to use
            
        Returns:
            Dict containing generated rules or error information
        """
        return await self.rule_manager.generate_rules(
            dataset_id,
            column_meta,
            engine,
            model_type
        )
        
    async def execute_rules(
        self,
        dataset_id: str,
        data: Any,
        rule_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute business rules on a dataset.
        
        Args:
            dataset_id: ID of the dataset to execute rules on
            data: Data to execute rules against
            rule_ids: Optional list of rule IDs to execute
            
        Returns:
            Dict containing execution results
        """
        return await self.rule_manager.execute_rules(
            dataset_id,
            data,
            rule_ids
        )
        
    async def validate_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a business rule.
        
        Args:
            rule: The rule to validate
            
        Returns:
            Dict containing validation results
        """
        try:
            structure_valid = validate_rule_structure(rule)
            condition_valid = validate_rule_condition(rule["condition"])
            
            return {
                "success": True,
                "valid": structure_valid and condition_valid,
                "structure_valid": structure_valid,
                "condition_valid": condition_valid
            }
        except Exception as e:
            logger.error(f"Error validating rule: {str(e)}")
            return {"success": False, "error": str(e)}
            
    async def validate_execution_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a rule execution result.
        
        Args:
            result: The execution result to validate
            
        Returns:
            Dict containing validation results
        """
        try:
            valid = validate_execution_result(result)
            return {"success": True, "valid": valid}
        except Exception as e:
            logger.error(f"Error validating execution result: {str(e)}")
            return {"success": False, "error": str(e)}
            
    async def validate_dataset_for_rules(
        self,
        dataset: Any,
        rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate that a dataset has all required columns for the given rules.
        
        Args:
            dataset: The dataset to validate
            rules: List of rules to check against
            
        Returns:
            Dict containing validation results
        """
        try:
            valid = validate_dataset_for_rules(dataset, rules)
            return {"success": True, "valid": valid}
        except Exception as e:
            logger.error(f"Error validating dataset for rules: {str(e)}")
            return {"success": False, "error": str(e)}