"""
Data Enrichment Service Module

This module provides functionality for enriching datasets with external data,
derived fields, and advanced transformations.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional
import aiohttp
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class DataEnrichmentService:
    """Service for data enrichment operations."""
    
    async def enrich_data(self, df: pd.DataFrame, enrichment_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Enrich data with external sources, derived fields, and advanced transformations.
        
        Args:
            df: DataFrame to enrich
            enrichment_config: Configuration for enrichment operations
            
        Returns:
            Dictionary with enriched DataFrame and metadata
        """
        if enrichment_config is None:
            enrichment_config = {}
            
        enriched_df = df.copy()
        applied_enrichments = []
        
        # Apply derived fields
        if enrichment_config.get("derived_fields"):
            enriched_df, derived_fields = await self._add_derived_fields(
                enriched_df, 
                enrichment_config["derived_fields"]
            )
            applied_enrichments.extend(derived_fields)
            
        # Apply external data enrichment
        if enrichment_config.get("external_data"):
            enriched_df, external_enrichments = await self._add_external_data(
                enriched_df,
                enrichment_config["external_data"]
            )
            applied_enrichments.extend(external_enrichments)
            
        # Apply advanced transformations
        if enrichment_config.get("advanced_transformations"):
            enriched_df, advanced_transformations = await self._apply_advanced_transformations(
                enriched_df,
                enrichment_config["advanced_transformations"]
            )
            applied_enrichments.extend(advanced_transformations)
            
        return {
            "enriched_df": enriched_df,
            "enrichments_applied": applied_enrichments,
            "original_columns": list(df.columns),
            "new_columns": [col for col in enriched_df.columns if col not in df.columns],
            "rows_before": len(df),
            "rows_after": len(enriched_df)
        }
    
    async def _add_derived_fields(self, df: pd.DataFrame, derived_fields_config: List[Dict[str, Any]]) -> tuple:
        """
        Add derived fields to the DataFrame based on existing columns.
        
        Args:
            df: DataFrame to enrich
            derived_fields_config: Configuration for derived fields
            
        Returns:
            Tuple of (enriched DataFrame, list of applied enrichments)
        """
        enriched_df = df.copy()
        applied_enrichments = []
        
        for field_config in derived_fields_config:
            field_name = field_config.get("name")
            field_type = field_config.get("type")
            source_columns = field_config.get("source_columns", [])
            
            try:
                if field_type == "concatenate":
                    # Concatenate multiple columns
                    separator = field_config.get("separator", " ")
                    enriched_df[field_name] = enriched_df[source_columns].astype(str).agg(separator.join, axis=1)
                    
                elif field_type == "arithmetic":
                    # Arithmetic operation on columns
                    operation = field_config.get("operation")
                    if operation == "add":
                        enriched_df[field_name] = enriched_df[source_columns[0]] + enriched_df[source_columns[1]]
                    elif operation == "subtract":
                        enriched_df[field_name] = enriched_df[source_columns[0]] - enriched_df[source_columns[1]]
                    elif operation == "multiply":
                        enriched_df[field_name] = enriched_df[source_columns[0]] * enriched_df[source_columns[1]]
                    elif operation == "divide":
                        enriched_df[field_name] = enriched_df[source_columns[0]] / enriched_df[source_columns[1]]
                        
                elif field_type == "date_diff":
                    # Calculate difference between two date columns
                    unit = field_config.get("unit", "days")
                    enriched_df[field_name] = (
                        pd.to_datetime(enriched_df[source_columns[0]]) - 
                        pd.to_datetime(enriched_df[source_columns[1]])
                    )
                    if unit == "days":
                        enriched_df[field_name] = enriched_df[field_name].dt.days
                    elif unit == "hours":
                        enriched_df[field_name] = enriched_df[field_name].dt.total_seconds() / 3600
                        
                elif field_type == "conditional":
                    # Apply conditional logic
                    condition = field_config.get("condition")
                    true_value = field_config.get("true_value")
                    false_value = field_config.get("false_value")
                    
                    # Use eval to apply the condition (with safety checks)
                    condition_str = condition
                    for col in source_columns:
                        condition_str = condition_str.replace(col, f"enriched_df['{col}']")
                        
                    mask = eval(condition_str)
                    enriched_df[field_name] = np.where(mask, true_value, false_value)
                
                applied_enrichments.append({
                    "type": "derived_field",
                    "name": field_name,
                    "field_type": field_type,
                    "source_columns": source_columns
                })
                
            except Exception as e:
                logger.error(f"Error creating derived field {field_name}: {str(e)}")
                
        return enriched_df, applied_enrichments
    
    async def _add_external_data(self, df: pd.DataFrame, external_data_config: List[Dict[str, Any]]) -> tuple:
        """
        Enrich DataFrame with external data sources.
        
        Args:
            df: DataFrame to enrich
            external_data_config: Configuration for external data sources
            
        Returns:
            Tuple of (enriched DataFrame, list of applied enrichments)
        """
        enriched_df = df.copy()
        applied_enrichments = []
        
        for source_config in external_data_config:
            source_type = source_config.get("type")
            source_name = source_config.get("name")
            join_column = source_config.get("join_column")
            
            try:
                if source_type == "api":
                    # Enrich with API data
                    api_url = source_config.get("url")
                    method = source_config.get("method", "GET")
                    headers = source_config.get("headers", {})
                    
                    # Get unique values to query
                    unique_values = enriched_df[join_column].unique().tolist()
                    
                    # Create a mapping of values to API responses
                    value_to_data = {}
                    
                    async with aiohttp.ClientSession() as session:
                        for value in unique_values:
                            url = api_url.replace("{value}", str(value))
                            
                            async with session.request(method, url, headers=headers) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    value_to_data[value] = data
                    
                    # Add new columns based on API response
                    for field in source_config.get("fields", []):
                        field_name = field.get("name")
                        json_path = field.get("json_path")
                        
                        def extract_value(row):
                            value = row[join_column]
                            if value in value_to_data:
                                # Navigate JSON path
                                data = value_to_data[value]
                                for key in json_path.split('.'):
                                    if isinstance(data, dict) and key in data:
                                        data = data[key]
                                    else:
                                        return None
                                return data
                            return None
                        
                        enriched_df[field_name] = enriched_df.apply(extract_value, axis=1)
                
                elif source_type == "database":
                    # For demonstration purposes, we'll simulate a database lookup
                    # In a real implementation, this would connect to an actual database
                    
                    # Simulate database data
                    db_data = {
                        "customer_id": [1, 2, 3, 4, 5],
                        "customer_segment": ["Premium", "Standard", "Premium", "Basic", "Standard"],
                        "lifetime_value": [1200, 450, 980, 120, 350]
                    }
                    
                    db_df = pd.DataFrame(db_data)
                    
                    # Join with the main DataFrame
                    enriched_df = pd.merge(
                        enriched_df,
                        db_df,
                        left_on=join_column,
                        right_on=source_config.get("db_column", join_column),
                        how="left"
                    )
                
                applied_enrichments.append({
                    "type": "external_data",
                    "name": source_name,
                    "source_type": source_type,
                    "join_column": join_column
                })
                
            except Exception as e:
                logger.error(f"Error enriching with external data {source_name}: {str(e)}")
                
        return enriched_df, applied_enrichments
    
    async def _apply_advanced_transformations(self, df: pd.DataFrame, transformation_config: List[Dict[str, Any]]) -> tuple:
        """
        Apply advanced transformations to the DataFrame.
        
        Args:
            df: DataFrame to transform
            transformation_config: Configuration for advanced transformations
            
        Returns:
            Tuple of (transformed DataFrame, list of applied transformations)
        """
        transformed_df = df.copy()
        applied_transformations = []
        
        for transform_config in transformation_config:
            transform_type = transform_config.get("type")
            transform_name = transform_config.get("name")
            columns = transform_config.get("columns", [])
            
            try:
                if transform_type == "binning":
                    # Bin numeric values into categories
                    for column in columns:
                        bins = transform_config.get("bins", 5)
                        labels = transform_config.get("labels")
                        
                        if isinstance(bins, int):
                            # Create equal-width bins
                            transformed_df[f"{column}_binned"] = pd.cut(
                                transformed_df[column], 
                                bins=bins, 
                                labels=labels
                            )
                        else:
                            # Use custom bin edges
                            transformed_df[f"{column}_binned"] = pd.cut(
                                transformed_df[column], 
                                bins=bins, 
                                labels=labels
                            )
                
                elif transform_type == "one_hot_encoding":
                    # One-hot encode categorical columns
                    for column in columns:
                        one_hot = pd.get_dummies(
                            transformed_df[column], 
                            prefix=column,
                            prefix_sep="_"
                        )
                        transformed_df = pd.concat([transformed_df, one_hot], axis=1)
                
                elif transform_type == "text_extraction":
                    # Extract patterns from text
                    for column in columns:
                        pattern = transform_config.get("pattern")
                        output_column = transform_config.get("output_column", f"{column}_extracted")
                        
                        transformed_df[output_column] = transformed_df[column].str.extract(pattern)
                
                elif transform_type == "date_extraction":
                    # Extract components from dates
                    for column in columns:
                        components = transform_config.get("components", ["year", "month", "day"])
                        
                        # Convert to datetime if not already
                        if not pd.api.types.is_datetime64_any_dtype(transformed_df[column]):
                            transformed_df[f"{column}_dt"] = pd.to_datetime(transformed_df[column])
                        else:
                            transformed_df[f"{column}_dt"] = transformed_df[column]
                        
                        # Extract components
                        if "year" in components:
                            transformed_df[f"{column}_year"] = transformed_df[f"{column}_dt"].dt.year
                        if "month" in components:
                            transformed_df[f"{column}_month"] = transformed_df[f"{column}_dt"].dt.month
                        if "day" in components:
                            transformed_df[f"{column}_day"] = transformed_df[f"{column}_dt"].dt.day
                        if "weekday" in components:
                            transformed_df[f"{column}_weekday"] = transformed_df[f"{column}_dt"].dt.weekday
                        if "quarter" in components:
                            transformed_df[f"{column}_quarter"] = transformed_df[f"{column}_dt"].dt.quarter
                            
                        # Remove temporary column
                        if f"{column}_dt" != column:
                            transformed_df = transformed_df.drop(columns=[f"{column}_dt"])
                
                applied_transformations.append({
                    "type": "advanced_transformation",
                    "name": transform_name,
                    "transform_type": transform_type,
                    "columns": columns
                })
                
            except Exception as e:
                logger.error(f"Error applying transformation {transform_name}: {str(e)}")
                
        return transformed_df, applied_transformations

# Create a singleton instance
data_enrichment_service = DataEnrichmentService()
