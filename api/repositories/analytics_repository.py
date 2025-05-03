
"""
Repository for analytics data operations.
"""
import json
import logging
from typing import Dict, List, Any, Optional
import numpy as np
from datetime import datetime

from utils.db import execute_query, execute_transaction

logger = logging.getLogger(__name__)

class AnalyticsRepository:
    """Repository for analytics data operations."""
    
    async def get_data_profile(self, dataset_id: int) -> Optional[Dict[str, Any]]:
        """Get the latest data profile for a dataset."""
        query = """
        SELECT summary, detailed_profile
        FROM data_profiles
        WHERE dataset_id = $1
        ORDER BY profile_date DESC
        LIMIT 1
        """
        
        try:
            results = await execute_query(query, dataset_id)
            if results:
                return {
                    "summary": results[0]['summary'],
                    "detailed_profile": results[0]['detailed_profile']
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching data profile for dataset {dataset_id}: {str(e)}")
            raise
    
    async def save_data_profile(self, dataset_id: int, summary: Dict[str, Any], 
                              detailed_profile: Optional[Dict[str, Any]] = None) -> int:
        """Save a new data profile for a dataset."""
        query = """
        INSERT INTO data_profiles (dataset_id, summary, detailed_profile)
        VALUES ($1, $2, $3)
        RETURNING id
        """
        
        try:
            results = await execute_query(
                query, 
                dataset_id, 
                json.dumps(summary), 
                json.dumps(detailed_profile) if detailed_profile else None
            )
            return results[0]['id']
        except Exception as e:
            logger.error(f"Error saving data profile for dataset {dataset_id}: {str(e)}")
            raise
    
    async def get_anomaly_detection_results(self, dataset_id: int) -> List[Dict[str, Any]]:
        """Get anomaly detection results for a dataset."""
        query = """
        SELECT detection_method, detection_date, anomaly_count, anomaly_types,
               detected_anomalies, method_specific_params
        FROM anomaly_detections
        WHERE dataset_id = $1
        ORDER BY detection_date DESC
        LIMIT 10
        """
        
        try:
            results = await execute_query(query, dataset_id)
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error fetching anomaly detection results for dataset {dataset_id}: {str(e)}")
            raise
    
    async def save_anomaly_detection_results(self, dataset_id: int, method: str, 
                                          anomaly_count: int, anomaly_types: Dict[str, Any],
                                          detected_anomalies: List[Dict[str, Any]], 
                                          method_specific_params: Dict[str, Any]) -> int:
        """Save anomaly detection results."""
        query = """
        INSERT INTO anomaly_detections (
            dataset_id, detection_method, anomaly_count, 
            anomaly_types, detected_anomalies, method_specific_params
        )
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
        """
        
        try:
            results = await execute_query(
                query, 
                dataset_id, 
                method, 
                anomaly_count, 
                json.dumps(anomaly_types), 
                json.dumps(detected_anomalies),
                json.dumps(method_specific_params)
            )
            return results[0]['id']
        except Exception as e:
            logger.error(f"Error saving anomaly detection results for dataset {dataset_id}: {str(e)}")
            raise
    
    async def save_vector_embeddings(self, dataset_id: int, record_id: str, 
                                  embedding: List[float], metadata: Dict[str, Any]) -> int:
        """Save vector embeddings for a dataset record."""
        query = """
        INSERT INTO dataset_embeddings (dataset_id, record_id, embedding, metadata)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """
        
        try:
            results = await execute_query(
                query, 
                dataset_id, 
                record_id, 
                embedding, 
                json.dumps(metadata)
            )
            return results[0]['id']
        except Exception as e:
            logger.error(f"Error saving vector embedding for record {record_id} in dataset {dataset_id}: {str(e)}")
            raise
    
    async def vector_search(self, dataset_id: int, query_vector: List[float], 
                         limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar records using vector similarity."""
        query = """
        SELECT record_id, metadata, 
               1 - (embedding <=> $1) AS similarity
        FROM dataset_embeddings
        WHERE dataset_id = $2
        ORDER BY similarity DESC
        LIMIT $3
        """
        
        try:
            results = await execute_query(query, query_vector, dataset_id, limit)
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error performing vector search for dataset {dataset_id}: {str(e)}")
            raise
    
    async def get_system_config(self, key: str) -> Optional[Dict[str, Any]]:
        """Get system configuration value."""
        query = """
        SELECT value, description, updated_at
        FROM system_config
        WHERE key = $1
        """
        
        try:
            results = await execute_query(query, key)
            if results:
                return dict(results[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching system config for key {key}: {str(e)}")
            raise
    
    async def update_system_config(self, key: str, value: Dict[str, Any], 
                                description: Optional[str] = None, updated_by: Optional[str] = None) -> bool:
        """Update system configuration."""
        query = """
        INSERT INTO system_config (key, value, description, updated_by, updated_at)
        VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
        ON CONFLICT (key) 
        DO UPDATE SET
            value = EXCLUDED.value,
            description = COALESCE(EXCLUDED.description, system_config.description),
            updated_by = EXCLUDED.updated_by,
            updated_at = CURRENT_TIMESTAMP
        RETURNING key
        """
        
        try:
            results = await execute_query(
                query, 
                key, 
                json.dumps(value), 
                description, 
                updated_by
            )
            return bool(results)
        except Exception as e:
            logger.error(f"Error updating system config for key {key}: {str(e)}")
            raise
    
    async def log_audit_event(self, action: str, entity_type: str, entity_id: Optional[str] = None,
                           user_id: Optional[int] = None, details: Optional[Dict[str, Any]] = None,
                           ip_address: Optional[str] = None) -> int:
        """Log an audit event."""
        query = """
        INSERT INTO audit_logs (action, entity_type, entity_id, user_id, details, ip_address)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
        """
        
        try:
            results = await execute_query(
                query, 
                action, 
                entity_type, 
                entity_id, 
                user_id, 
                json.dumps(details) if details else None,
                ip_address
            )
            return results[0]['id']
        except Exception as e:
            logger.error(f"Error logging audit event {action} on {entity_type}: {str(e)}")
            raise
