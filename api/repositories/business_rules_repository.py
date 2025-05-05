
"""
Repository for business rules operations.
"""
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from api.db.connection import get_db_session
from sqlalchemy import text
from api.models.business_rule import BusinessRule, BusinessRuleCreate, BusinessRuleUpdate, DatasetRule
from api.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class BusinessRulesRepository:
    """Repository for business rules operations."""
    
    async def get_rules(self, dataset_id: Optional[str] = None, rule_type: Optional[str] = None, 
                      severity: Optional[str] = None, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get business rules with optional filtering."""
        async with get_db_session() as session:
            # Build query with optional filters
            conditions = []
            params = {}
            
            if dataset_id:
                conditions.append("dataset_id = :dataset_id")
                params["dataset_id"] = dataset_id
            
            if rule_type:
                conditions.append("rule_type = :rule_type")
                params["rule_type"] = rule_type
                
            if severity:
                conditions.append("severity = :severity")
                params["severity"] = severity
                
            if source:
                conditions.append("source = :source")
                params["source"] = source
                
            # Build WHERE clause if conditions exist
            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
                
            query = text(f"""
                SELECT * FROM {settings.DB_SCHEMA}.business_rules
                {where_clause}
                ORDER BY priority DESC, created_at DESC
                """)
                
            try:
                result = await session.execute(query, params)
                return [dict(row) for row in result]
            except Exception as e:
                logger.error(f"Error fetching business rules: {str(e)}")
                return []
    
    async def get_rules_by_dataset(self, dataset_id: str) -> List[Dict[str, Any]]:
        """Get all business rules for a dataset."""
        async with get_db_session() as session:
            query = text(f"""
                SELECT * FROM {settings.DB_SCHEMA}.business_rules
                WHERE dataset_id = :dataset_id
                ORDER BY priority DESC, created_at DESC
                """)
            
            try:
                result = await session.execute(query, {"dataset_id": dataset_id})
                return [dict(row) for row in result]
            except Exception as e:
                logger.error(f"Error fetching business rules for dataset {dataset_id}: {str(e)}")
                return []
    
    async def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific business rule by ID."""
        async with get_db_session() as session:
            query = text(f"""
                SELECT * FROM {settings.DB_SCHEMA}.business_rules
                WHERE id = :rule_id
                """)
            
            try:
                result = await session.execute(query, {"rule_id": rule_id})
                row = result.first()
                return dict(row) if row else None
            except Exception as e:
                logger.error(f"Error fetching business rule {rule_id}: {str(e)}")
                return None
    
    async def create_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new business rule."""
        async with get_db_session() as session:
            # Prepare fields and values for insertion
            fields = []
            values = []
            params = {}
            
            for key, value in rule_data.items():
                # Skip id if it's in the data (will be auto-generated)
                if key != 'id':
                    fields.append(key)
                    values.append(f":{key}")
                    params[key] = value
            
            # Add created_at and updated_at timestamps
            now = datetime.utcnow().isoformat()
            if 'created_at' not in fields:
                fields.append('created_at')
                values.append(":created_at")
                params['created_at'] = now
            if 'updated_at' not in fields:
                fields.append('updated_at')
                values.append(":updated_at")
                params['updated_at'] = now
            
            # Build and execute query
            query = text(f"""
                INSERT INTO {settings.DB_SCHEMA}.business_rules (
                    {', '.join(fields)}
                )
                VALUES (
                    {', '.join(values)}
                )
                RETURNING *
                """)
            
            try:
                result = await session.execute(query, params)
                await session.commit()
                return dict(result.first())
            except Exception as e:
                await session.rollback()
                logger.error(f"Error creating business rule: {str(e)}")
                raise
    
    async def update_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing business rule."""
        async with get_db_session() as session:
            # Build dynamic update query based on provided fields
            update_fields = []
            params = {'rule_id': rule_id}  # First parameter is the rule ID
            
            # Build SET clause dynamically
            for field, value in rule_data.items():
                # Skip id field since it's the primary key
                if field != 'id':
                    update_fields.append(f"{field} = :{field}")
                    params[field] = value
            
            # Add updated_at field
            update_fields.append("updated_at = :updated_at")
            params['updated_at'] = datetime.utcnow().isoformat()
            
            if not update_fields:
                logger.warning(f"No valid fields to update for rule {rule_id}")
                return await self.get_rule(rule_id)
            
            query = text(f"""
                UPDATE {settings.DB_SCHEMA}.business_rules
                SET {', '.join(update_fields)}
                WHERE id = :rule_id
                RETURNING *
                """)
            
            try:
                result = await session.execute(query, params)
                await session.commit()
                row = result.first()
                return dict(row) if row else None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating business rule {rule_id}: {str(e)}")
                raise
    
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a business rule."""
        async with get_db_session() as session:
            query = text(f"""
                DELETE FROM {settings.DB_SCHEMA}.business_rules
                WHERE id = :rule_id
                RETURNING id
                """)
            
            try:
                result = await session.execute(query, {"rule_id": rule_id})
                await session.commit()
                return bool(result.first())
            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting business rule {rule_id}: {str(e)}")
                raise
    
    async def save_rule_validation(self, rule_id: str, dataset_id: str, 
                                violations_count: int, violations: List[Dict[str, Any]]) -> str:
        """Save validation results for a business rule."""
        async with get_db_session() as session:
            query = text(f"""
            INSERT INTO {settings.DB_SCHEMA}.rule_validations (
                rule_id, dataset_id, violations_count, violations, validation_date
            )
            VALUES (
                :rule_id, :dataset_id, :violations_count, :violations, :validation_date
            )
            RETURNING id
            """)
            
            try:
                result = await session.execute(
                    query, 
                    {
                        "rule_id": rule_id,
                        "dataset_id": dataset_id,
                        "violations_count": violations_count,
                        "violations": json.dumps(violations),
                        "validation_date": datetime.utcnow().isoformat()
                    }
                )
                await session.commit()
                return result.first()[0]
            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving rule validation for rule {rule_id}, dataset {dataset_id}: {str(e)}")
                raise
    
    async def get_rule_validations(self, dataset_id: str, rule_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get validation results for rules applied to a dataset."""
        async with get_db_session() as session:
            params = {"dataset_id": dataset_id}
            
            if rule_id is not None:
                query = text(f"""
                SELECT rv.id, rv.rule_id, rv.violations_count, rv.validation_date, rv.violations,
                       br.name as rule_name, br.description as rule_description, br.severity, br.rule_type
                FROM {settings.DB_SCHEMA}.rule_validations rv
                JOIN {settings.DB_SCHEMA}.business_rules br ON rv.rule_id = br.id
                WHERE rv.dataset_id = :dataset_id AND rv.rule_id = :rule_id
                ORDER BY rv.validation_date DESC
                """)
                params["rule_id"] = rule_id
            else:
                query = text(f"""
                SELECT rv.id, rv.rule_id, rv.violations_count, rv.validation_date, rv.violations,
                       br.name as rule_name, br.description as rule_description, br.severity, br.rule_type
                FROM {settings.DB_SCHEMA}.rule_validations rv
                JOIN {settings.DB_SCHEMA}.business_rules br ON rv.rule_id = br.id
                WHERE rv.dataset_id = :dataset_id
                ORDER BY rv.validation_date DESC
                """)
            
            try:
                result = await session.execute(query, params)
                return [dict(row) for row in result]
            except Exception as e:
                logger.error(f"Error fetching rule validations for dataset {dataset_id}: {str(e)}")
                return []
    
    async def bulk_create_rules(self, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple business rules in a transaction."""
        if not rules:
            return []
        
        created_rules = []
        async with get_db_session() as session:
            try:
                # Start transaction
                for rule_data in rules:
                    # Prepare fields and values for insertion
                    fields = []
                    values = []
                    params = {}
                    
                    for key, value in rule_data.items():
                        # Skip id if it's in the data (will be auto-generated)
                        if key != 'id':
                            fields.append(key)
                            values.append(f":{key}_{len(created_rules)}")
                            params[f"{key}_{len(created_rules)}"] = value
                    
                    # Add created_at and updated_at timestamps
                    now = datetime.utcnow().isoformat()
                    if 'created_at' not in fields:
                        fields.append('created_at')
                        values.append(f":created_at_{len(created_rules)}")
                        params[f"created_at_{len(created_rules)}"] = now
                    if 'updated_at' not in fields:
                        fields.append('updated_at')
                        values.append(f":updated_at_{len(created_rules)}")
                        params[f"updated_at_{len(created_rules)}"] = now
                    
                    # Build and execute query
                    query = text(f"""
                        INSERT INTO {settings.DB_SCHEMA}.business_rules (
                            {', '.join(fields)}
                        )
                        VALUES (
                            {', '.join(values)}
                        )
                        RETURNING *
                        """)
                    
                    result = await session.execute(query, params)
                    created_rules.append(dict(result.first()))
                
                # Commit transaction
                await session.commit()
                return created_rules
            except Exception as e:
                await session.rollback()
                logger.error(f"Error bulk creating business rules: {str(e)}")
                raise
