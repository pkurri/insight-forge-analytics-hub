"""
Business Rules Manager Module

This module provides functions for managing business rules, including CRUD operations
and rule organization.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from services.business_rules.validators import validate_rule_structure, validate_rule_condition
from services.business_rules.executors import execute_rule
from services.business_rules.generators import generate_rules_with_engine

logger = logging.getLogger(__name__)

class RuleManager:
    """Class for managing business rules."""
    
    def __init__(self, db_session):
        """Initialize the rule manager.
        
        Args:
            db_session: Database session for rule operations
        """
        self.db = db_session
        
    async def create_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new business rule.
        
        Args:
            rule_data: Dictionary containing rule data
            
        Returns:
            Dict containing the created rule or error information
        """
        try:
            # Validate rule structure and condition
            if not validate_rule_structure(rule_data):
                return {"success": False, "error": "Invalid rule structure"}
            if not validate_rule_condition(rule_data["condition"]):
                return {"success": False, "error": "Invalid rule condition"}
                
            # Add metadata
            rule_data["created_at"] = datetime.utcnow()
            rule_data["updated_at"] = datetime.utcnow()
            
            # Store in database
            rule_id = await self.db.rules.insert_one(rule_data)
            rule_data["_id"] = rule_id
            
            return {"success": True, "rule": rule_data}
        except Exception as e:
            logger.error(f"Error creating rule: {str(e)}")
            return {"success": False, "error": str(e)}
            
    async def get_rule(self, rule_id: str) -> Dict[str, Any]:
        """Get a business rule by ID.
        
        Args:
            rule_id: ID of the rule to retrieve
            
        Returns:
            Dict containing the rule or error information
        """
        try:
            rule = await self.db.rules.find_one({"_id": rule_id})
            if not rule:
                return {"success": False, "error": "Rule not found"}
            return {"success": True, "rule": rule}
        except Exception as e:
            logger.error(f"Error getting rule: {str(e)}")
            return {"success": False, "error": str(e)}
            
    async def update_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing business rule.
        
        Args:
            rule_id: ID of the rule to update
            rule_data: Dictionary containing updated rule data
            
        Returns:
            Dict containing the updated rule or error information
        """
        try:
            # Validate rule structure and condition
            if not validate_rule_structure(rule_data):
                return {"success": False, "error": "Invalid rule structure"}
            if not validate_rule_condition(rule_data["condition"]):
                return {"success": False, "error": "Invalid rule condition"}
                
            # Add metadata
            rule_data["updated_at"] = datetime.utcnow()
            
            # Update in database
            result = await self.db.rules.update_one(
                {"_id": rule_id},
                {"$set": rule_data}
            )
            
            if result.modified_count == 0:
                return {"success": False, "error": "Rule not found"}
                
            return {"success": True, "rule": rule_data}
        except Exception as e:
            logger.error(f"Error updating rule: {str(e)}")
            return {"success": False, "error": str(e)}
            
    async def delete_rule(self, rule_id: str) -> Dict[str, Any]:
        """Delete a business rule.
        
        Args:
            rule_id: ID of the rule to delete
            
        Returns:
            Dict containing success status or error information
        """
        try:
            result = await self.db.rules.delete_one({"_id": rule_id})
            if result.deleted_count == 0:
                return {"success": False, "error": "Rule not found"}
            return {"success": True}
        except Exception as e:
            logger.error(f"Error deleting rule: {str(e)}")
            return {"success": False, "error": str(e)}
            
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
        try:
            # Build filter
            filter_dict = {}
            if dataset_id:
                filter_dict["dataset_id"] = dataset_id
            if source:
                filter_dict["source"] = source
            if severity:
                filter_dict["severity"] = severity
                
            # Get total count
            total = await self.db.rules.count_documents(filter_dict)
            
            # Get rules
            rules = await self.db.rules.find(filter_dict).skip(offset).limit(limit).to_list(length=limit)
            
            return {
                "success": True,
                "rules": rules,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        except Exception as e:
            logger.error(f"Error listing rules: {str(e)}")
            return {"success": False, "error": str(e)}
            
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
        try:
            # Generate rules
            result = await generate_rules_with_engine(
                dataset_id,
                column_meta,
                engine,
                model_type
            )
            
            if not result.get("success", True):
                return result
                
            # Validate and store generated rules
            rules_created = []
            for rule in result["rules"]:
                rule["dataset_id"] = dataset_id
                create_result = await self.create_rule(rule)
                if create_result["success"]:
                    rules_created.append(create_result["rule"])
                    
            return {
                "success": True,
                "rules": rules_created,
                "meta": result.get("meta", {})
            }
        except Exception as e:
            logger.error(f"Error generating rules: {str(e)}")
            return {"success": False, "error": str(e)}
            
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
        try:
            # Get rules to execute
            filter_dict = {"dataset_id": dataset_id}
            if rule_ids:
                filter_dict["_id"] = {"$in": rule_ids}
            rules = await self.db.rules.find(filter_dict).to_list(length=None)
            
            if not rules:
                return {"success": False, "error": "No rules found"}
                
            # Execute rules
            results = []
            for rule in rules:
                result = await execute_rule(rule, data)
                results.append(result)
                
            return {
                "success": True,
                "results": results,
                "total_rules": len(rules),
                "passed_rules": sum(1 for r in results if r["status"] == "passed"),
                "failed_rules": sum(1 for r in results if r["status"] == "failed"),
                "error_rules": sum(1 for r in results if r["status"] == "error")
            }
        except Exception as e:
            logger.error(f"Error executing rules: {str(e)}")
            return {"success": False, "error": str(e)} 