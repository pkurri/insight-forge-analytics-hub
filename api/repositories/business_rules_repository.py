
"""
Repository for business rules operations.
"""
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from api.db.connection import get_db_session
from sqlalchemy import text
from api.models.dataset import BusinessRule, BusinessRuleCreate, BusinessRuleSeverity

logger = logging.getLogger(__name__)

class BusinessRulesRepository:
    """Repository for business rules operations."""
    
    async def get_rules(self, dataset_id: int) -> List[Dict[str, Any]]:
        """Get all business rules for a dataset."""
        query = text(f"""
            SELECT id, dataset_metadata, condition, severity, message, is_active,
                   model_generated, confidence, created_at, updated_at
            FROM {DB_SCHEMA}.business_rules
            WHERE dataset_id = :dataset_id
            ORDER BY created_at DESC
            """)
        
        try:
            results = await execute_query(query, dataset_id)
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error fetching business rules for dataset {dataset_id}: {str(e)}")
            raise
    
    async def get_rule(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific business rule by ID."""
        query = text(f"""
            SELECT id, dataset_metadata, condition, severity, message, is_active,
                   model_generated, confidence, created_at, updated_at
            FROM {DB_SCHEMA}.business_rules
            WHERE id = :rule_id
            """)
        
        try:
            results = await execute_query(query, rule_id)
            return dict(results[0]) if results else None
        except Exception as e:
            logger.error(f"Error fetching business rule {rule_id}: {str(e)}")
            raise
    
    async def create_rule(self, rule: BusinessRuleCreate) -> Dict[str, Any]:
        """Create a new business rule."""
        query = text(f"""
            INSERT INTO {DB_SCHEMA}.business_rules (
                dataset_metadata, condition, severity, message, 
                model_generated, confidence
            )
            VALUES (:dataset_metadata, :condition, :severity, :message, 
                     :model_generated, :confidence)
            RETURNING id, dataset_metadata, condition, severity, message, is_active,
                      model_generated, confidence, created_at, updated_at
            """)
        
        try:
            results = await execute_query(
                query, 
                dataset_metadata=rule.dataset_metadata,
                condition=rule.condition,
                severity=rule.severity,
                message=rule.message,
                model_generated=rule.model_generated,
                confidence=rule.confidence
            )
            return dict(results[0])
        except Exception as e:
            logger.error(f"Error creating business rule for dataset {rule.dataset_id}: {str(e)}")
            raise
    
    async def update_rule(self, rule_id: int, rule_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing business rule."""
        # Build dynamic update query based on provided fields
        update_fields = []
        params = {'rule_id': rule_id}  # First parameter is the rule ID
        
        # Build SET clause dynamically
        for field, value in rule_data.items():
            if field in ['dataset_metadata', 'condition', 'severity', 'message', 'is_active', 'confidence']:
                update_fields.append(f"{field} = :{field}")
                params[field] = value
        
        # Add updated_at field
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        if not update_fields:
            logger.warning(f"No valid fields to update for rule {rule_id}")
            return await self.get_rule(rule_id)
        
        query = text(f"""
            UPDATE {DB_SCHEMA}.business_rules
            SET {", ".join(update_fields)}
            WHERE id = :rule_id
            RETURNING id, dataset_metadata, condition, severity, message, is_active,
                      model_generated, confidence, created_at, updated_at
            """)
        
        try:
            results = await execute_query(query, **params)
            return dict(results[0]) if results else None
        except Exception as e:
            logger.error(f"Error updating business rule {rule_id}: {str(e)}")
            raise
    
    async def delete_rule(self, rule_id: int) -> bool:
        """Delete a business rule."""
        query = text(f"""
            DELETE FROM {DB_SCHEMA}.business_rules
            WHERE id = :rule_id
            RETURNING id
            """)
        
        try:
            results = await execute_query(query, rule_id)
            return bool(results)
        except Exception as e:
            logger.error(f"Error deleting business rule {rule_id}: {str(e)}")
            raise
    
    async def save_rule_validation(self, rule_id: int, dataset_id: int, 
                                violations_count: int, violations: List[Dict[str, Any]]) -> int:
        """Save validation results for a business rule."""
        query = """
        INSERT INTO rule_validations (
            rule_id, dataset_id, violations_count, violations
        )
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """
        
        try:
            results = await execute_query(
                query, 
                rule_id,
                dataset_id,
                violations_count,
                json.dumps(violations)
            )
            return results[0]['id']
        except Exception as e:
            logger.error(f"Error saving rule validation for rule {rule_id}, dataset {dataset_id}: {str(e)}")
            raise
    
    async def get_rule_validations(self, dataset_id: int, rule_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get validation results for rules applied to a dataset."""
        params = [dataset_id]
        
        if rule_id is not None:
            query = """
            SELECT rv.id, rv.rule_id, rv.violations_count, rv.validation_date,
                   br.dataset_metadata as rule_dataset_metadata, br.severity
            FROM rule_validations rv
            JOIN business_rules br ON rv.rule_id = br.id
            WHERE rv.dataset_id = $1 AND rv.rule_id = $2
            ORDER BY rv.validation_date DESC
            """
            params.append(rule_id)
        else:
            query = """
            SELECT rv.id, rv.rule_id, rv.violations_count, rv.validation_date,
                   br.dataset_metadata as rule_dataset_metadata, br.severity
            FROM rule_validations rv
            JOIN business_rules br ON rv.rule_id = br.id
            WHERE rv.dataset_id = $1
            ORDER BY rv.validation_date DESC
            """
        
        try:
            results = await execute_query(query, *params)
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error fetching rule validations for dataset {dataset_id}: {str(e)}")
            raise
    
    async def bulk_create_rules(self, rules: List[BusinessRuleCreate]) -> List[Dict[str, Any]]:
        """Create multiple business rules in a transaction."""
        if not rules:
            return []
        
        # Prepare batch of queries for transaction
        queries = []
        for rule in rules:
            query = """
            INSERT INTO business_rules (
                dataset_metadata, condition, severity, message, 
                model_generated, confidence
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, dataset_metadata, condition, severity, message, is_active,
                      model_generated, confidence, created_at, updated_at
            """
            params = (
                rule.dataset_metadata,
                rule.condition,
                rule.severity,
                rule.message,
                rule.model_generated,
                rule.confidence
            )
            queries.append((query, params))
        
        try:
            results = await execute_transaction(queries)
            return [dict(row[0]) for row in results if row]
        except Exception as e:
            logger.error(f"Error bulk creating business rules: {str(e)}")
            raise
