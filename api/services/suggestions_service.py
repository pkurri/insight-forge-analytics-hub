"""
Suggestions Service Module

This module provides functionality for generating and managing suggestions
based on data analysis, transformations, and enrichment.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from models.suggestion import SuggestionModel, SuggestionType, SuggestionStatus
from repositories.suggestions_repository import suggestions_repository
from services.data_profiling_service import DataProfilingService
from services.vector_service import vector_service

logger = logging.getLogger(__name__)

class SuggestionsService:
    """Service for generating and managing suggestions."""
    
    def __init__(self):
        """Initialize the suggestions service."""
        self.profiling_service = DataProfilingService()
        
    async def generate_data_quality_suggestions(
        self, 
        df: pd.DataFrame, 
        dataset_id: int
    ) -> List[SuggestionModel]:
        """
        Generate data quality suggestions based on data profiling.
        
        Args:
            df: DataFrame to analyze
            dataset_id: ID of the dataset
            
        Returns:
            List of generated suggestions
        """
        suggestions = []
        
        # Get data profile
        profile = await self.profiling_service.profile_data(df)
        
        # Check for missing values
        if profile["overview"]["missing_percentage"] > 5:
            # Suggest imputation for columns with high missing values
            for col_name, col_profile in profile["columns"].items():
                if col_profile.get("missing_percentage", 0) > 10:
                    if col_profile["type"] in ['int64', 'float64']:
                        suggestions.append(SuggestionModel(
                            dataset_id=dataset_id,
                            type=SuggestionType.DATA_QUALITY,
                            title=f"Impute missing values in {col_name}",
                            description=f"Column {col_name} has {col_profile['missing_percentage']:.2f}% missing values. Consider imputing with median.",
                            content={
                                "column": col_name,
                                "action": "impute",
                                "method": "median",
                                "missing_percentage": col_profile["missing_percentage"]
                            },
                            confidence_score=0.8
                        ))
                    elif col_profile["type"] == 'object':
                        suggestions.append(SuggestionModel(
                            dataset_id=dataset_id,
                            type=SuggestionType.DATA_QUALITY,
                            title=f"Impute missing values in {col_name}",
                            description=f"Column {col_name} has {col_profile['missing_percentage']:.2f}% missing values. Consider imputing with mode.",
                            content={
                                "column": col_name,
                                "action": "impute",
                                "method": "mode",
                                "missing_percentage": col_profile["missing_percentage"]
                            },
                            confidence_score=0.8
                        ))
        
        # Check for outliers in numeric columns
        for col_name, col_profile in profile["columns"].items():
            if col_profile["type"] in ['int64', 'float64']:
                if "q1" in col_profile and "q3" in col_profile:
                    iqr = col_profile["iqr"]
                    lower_bound = col_profile["q1"] - 1.5 * iqr
                    upper_bound = col_profile["q3"] + 1.5 * iqr
                    
                    outliers_count = ((df[col_name] < lower_bound) | (df[col_name] > upper_bound)).sum()
                    outliers_percentage = (outliers_count / len(df)) * 100
                    
                    if outliers_percentage > 1:
                        suggestions.append(SuggestionModel(
                            dataset_id=dataset_id,
                            type=SuggestionType.DATA_QUALITY,
                            title=f"Handle outliers in {col_name}",
                            description=f"Column {col_name} has {outliers_percentage:.2f}% outliers. Consider capping or removing them.",
                            content={
                                "column": col_name,
                                "action": "handle_outliers",
                                "method": "cap",
                                "lower_bound": float(lower_bound),
                                "upper_bound": float(upper_bound),
                                "outliers_percentage": float(outliers_percentage)
                            },
                            confidence_score=0.75
                        ))
        
        # Check for high cardinality categorical columns
        for col_name, col_profile in profile["columns"].items():
            if col_profile["type"] == 'object':
                if col_profile.get("unique_percentage", 0) > 50 and col_profile.get("unique_values", 0) > 100:
                    suggestions.append(SuggestionModel(
                        dataset_id=dataset_id,
                        type=SuggestionType.DATA_QUALITY,
                        title=f"High cardinality in {col_name}",
                        description=f"Column {col_name} has high cardinality ({col_profile['unique_values']} unique values). Consider grouping less frequent values.",
                        content={
                            "column": col_name,
                            "action": "reduce_cardinality",
                            "method": "group_rare",
                            "threshold": 0.01,
                            "unique_values": col_profile["unique_values"]
                        },
                        confidence_score=0.7
                    ))
        
        return suggestions
    
    async def generate_transformation_suggestions(
        self, 
        df: pd.DataFrame, 
        dataset_id: int
    ) -> List[SuggestionModel]:
        """
        Generate transformation suggestions based on data analysis.
        
        Args:
            df: DataFrame to analyze
            dataset_id: ID of the dataset
            
        Returns:
            List of generated suggestions
        """
        suggestions = []
        
        # Get data profile
        profile = await self.profiling_service.profile_data(df)
        
        # Suggest normalization for skewed numeric columns
        for col_name, col_profile in profile["columns"].items():
            if col_profile["type"] in ['int64', 'float64']:
                # Check for skewness
                if "skew" in col_profile and abs(col_profile["skew"]) > 1:
                    if col_profile["skew"] > 0:  # Right-skewed
                        suggestions.append(SuggestionModel(
                            dataset_id=dataset_id,
                            type=SuggestionType.TRANSFORMATION,
                            title=f"Apply log transformation to {col_name}",
                            description=f"Column {col_name} is right-skewed (skew={col_profile['skew']:.2f}). Consider applying log transformation.",
                            content={
                                "column": col_name,
                                "action": "transform",
                                "method": "log",
                                "skew": float(col_profile["skew"])
                            },
                            confidence_score=0.75
                        ))
                    else:  # Left-skewed
                        suggestions.append(SuggestionModel(
                            dataset_id=dataset_id,
                            type=SuggestionType.TRANSFORMATION,
                            title=f"Apply power transformation to {col_name}",
                            description=f"Column {col_name} is left-skewed (skew={col_profile['skew']:.2f}). Consider applying power transformation.",
                            content={
                                "column": col_name,
                                "action": "transform",
                                "method": "power",
                                "power": 2,
                                "skew": float(col_profile["skew"])
                            },
                            confidence_score=0.75
                        ))
        
        # Suggest encoding for categorical columns
        for col_name, col_profile in profile["columns"].items():
            if col_profile["type"] == 'object':
                if col_profile.get("unique_values", 0) < 10:  # Low cardinality
                    suggestions.append(SuggestionModel(
                        dataset_id=dataset_id,
                        type=SuggestionType.TRANSFORMATION,
                        title=f"One-hot encode {col_name}",
                        description=f"Column {col_name} is categorical with {col_profile['unique_values']} unique values. Consider one-hot encoding.",
                        content={
                            "column": col_name,
                            "action": "encode",
                            "method": "onehot",
                            "unique_values": col_profile["unique_values"]
                        },
                        confidence_score=0.8
                    ))
                else:  # High cardinality
                    suggestions.append(SuggestionModel(
                        dataset_id=dataset_id,
                        type=SuggestionType.TRANSFORMATION,
                        title=f"Target encode {col_name}",
                        description=f"Column {col_name} is categorical with high cardinality ({col_profile['unique_values']} unique values). Consider target encoding.",
                        content={
                            "column": col_name,
                            "action": "encode",
                            "method": "target",
                            "unique_values": col_profile["unique_values"]
                        },
                        confidence_score=0.7
                    ))
        
        # Suggest scaling for numeric columns
        numeric_columns = [col for col, profile in profile["columns"].items() 
                          if profile["type"] in ['int64', 'float64']]
        
        if len(numeric_columns) >= 2:
            suggestions.append(SuggestionModel(
                dataset_id=dataset_id,
                type=SuggestionType.TRANSFORMATION,
                title="Standardize numeric columns",
                description=f"Standardize {len(numeric_columns)} numeric columns to have zero mean and unit variance.",
                content={
                    "columns": numeric_columns,
                    "action": "scale",
                    "method": "standard"
                },
                confidence_score=0.85
            ))
        
        return suggestions
    
    async def generate_enrichment_suggestions(
        self, 
        df: pd.DataFrame, 
        dataset_id: int
    ) -> List[SuggestionModel]:
        """
        Generate enrichment suggestions based on data analysis.
        
        Args:
            df: DataFrame to analyze
            dataset_id: ID of the dataset
            
        Returns:
            List of generated suggestions
        """
        suggestions = []
        
        # Get data profile
        profile = await self.profiling_service.profile_data(df)
        
        # Suggest derived features based on correlations
        if "correlations" in profile and "high_correlations" in profile["correlations"]:
            for corr in profile["correlations"]["high_correlations"]:
                col1, col2 = corr["columns"]
                pearson = corr["pearson"]
                
                if abs(pearson) > 0.8:  # Strong correlation
                    suggestions.append(SuggestionModel(
                        dataset_id=dataset_id,
                        type=SuggestionType.ENRICHMENT,
                        title=f"Create interaction feature from {col1} and {col2}",
                        description=f"Columns {col1} and {col2} are highly correlated (r={pearson:.2f}). Consider creating an interaction feature.",
                        content={
                            "columns": [col1, col2],
                            "action": "create_feature",
                            "method": "interaction",
                            "correlation": float(pearson)
                        },
                        confidence_score=0.75
                    ))
        
        # Suggest date-based features for datetime columns
        for col_name in df.columns:
            try:
                if pd.api.types.is_datetime64_any_dtype(df[col_name]) or pd.to_datetime(df[col_name], errors='coerce').notna().all():
                    suggestions.append(SuggestionModel(
                        dataset_id=dataset_id,
                        type=SuggestionType.ENRICHMENT,
                        title=f"Extract date features from {col_name}",
                        description=f"Column {col_name} contains datetime values. Consider extracting year, month, day, day of week, etc.",
                        content={
                            "column": col_name,
                            "action": "extract_date_features",
                            "features": ["year", "month", "day", "day_of_week", "quarter"]
                        },
                        confidence_score=0.9
                    ))
            except:
                pass
        
        # Suggest text-based features for string columns with reasonable length
        for col_name, col_profile in profile["columns"].items():
            if col_profile["type"] == 'object':
                if "avg_length" in col_profile and col_profile["avg_length"] > 10:
                    suggestions.append(SuggestionModel(
                        dataset_id=dataset_id,
                        type=SuggestionType.ENRICHMENT,
                        title=f"Extract text features from {col_name}",
                        description=f"Column {col_name} contains text data with average length {col_profile['avg_length']:.1f}. Consider extracting text features.",
                        content={
                            "column": col_name,
                            "action": "extract_text_features",
                            "features": ["char_count", "word_count", "sentence_count", "sentiment"]
                        },
                        confidence_score=0.7
                    ))
        
        return suggestions
    
    async def generate_visualization_suggestions(
        self, 
        df: pd.DataFrame, 
        dataset_id: int
    ) -> List[SuggestionModel]:
        """
        Generate visualization suggestions based on data analysis.
        
        Args:
            df: DataFrame to analyze
            dataset_id: ID of the dataset
            
        Returns:
            List of generated suggestions
        """
        suggestions = []
        
        # Get data profile
        profile = await self.profiling_service.profile_data(df)
        
        # Suggest distribution plots for numeric columns
        numeric_columns = [col for col, profile in profile["columns"].items() 
                          if profile["type"] in ['int64', 'float64']]
        
        if numeric_columns:
            suggestions.append(SuggestionModel(
                dataset_id=dataset_id,
                type=SuggestionType.VISUALIZATION,
                title="Distribution plots for numeric columns",
                description=f"Create distribution plots (histogram, boxplot) for {len(numeric_columns)} numeric columns.",
                content={
                    "columns": numeric_columns,
                    "plot_type": "distribution",
                    "variants": ["histogram", "boxplot", "violin"]
                },
                confidence_score=0.9
            ))
        
        # Suggest correlation heatmap for numeric columns
        if len(numeric_columns) >= 3:
            suggestions.append(SuggestionModel(
                dataset_id=dataset_id,
                type=SuggestionType.VISUALIZATION,
                title="Correlation heatmap",
                description="Create a correlation heatmap to visualize relationships between numeric columns.",
                content={
                    "columns": numeric_columns,
                    "plot_type": "heatmap",
                    "correlation_method": "pearson"
                },
                confidence_score=0.85
            ))
        
        # Suggest bar plots for categorical columns
        categorical_columns = [col for col, profile in profile["columns"].items() 
                              if profile["type"] == 'object' and profile.get("unique_values", 0) < 20]
        
        for col in categorical_columns:
            suggestions.append(SuggestionModel(
                dataset_id=dataset_id,
                type=SuggestionType.VISUALIZATION,
                title=f"Bar plot for {col}",
                description=f"Create a bar plot to visualize the distribution of values in categorical column {col}.",
                content={
                    "column": col,
                    "plot_type": "bar",
                    "orientation": "vertical",
                    "sort": "frequency"
                },
                confidence_score=0.8
            ))
        
        # Suggest scatter plots for highly correlated pairs
        if "correlations" in profile and "high_correlations" in profile["correlations"]:
            for i, corr in enumerate(profile["correlations"]["high_correlations"][:3]):  # Limit to top 3
                col1, col2 = corr["columns"]
                pearson = corr["pearson"]
                
                suggestions.append(SuggestionModel(
                    dataset_id=dataset_id,
                    type=SuggestionType.VISUALIZATION,
                    title=f"Scatter plot: {col1} vs {col2}",
                    description=f"Create a scatter plot to visualize the relationship between {col1} and {col2} (correlation: {pearson:.2f}).",
                    content={
                        "columns": [col1, col2],
                        "plot_type": "scatter",
                        "correlation": float(pearson),
                        "add_trendline": True
                    },
                    confidence_score=0.8
                ))
        
        return suggestions
    
    async def generate_all_suggestions(
        self, 
        df: pd.DataFrame, 
        dataset_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Generate all types of suggestions for a dataset.
        
        Args:
            df: DataFrame to analyze
            dataset_id: ID of the dataset
            db: Database session
            
        Returns:
            Dictionary with generated suggestions and metadata
        """
        all_suggestions = []
        
        # Generate data quality suggestions
        quality_suggestions = await self.generate_data_quality_suggestions(df, dataset_id)
        all_suggestions.extend(quality_suggestions)
        
        # Generate transformation suggestions
        transformation_suggestions = await self.generate_transformation_suggestions(df, dataset_id)
        all_suggestions.extend(transformation_suggestions)
        
        # Generate enrichment suggestions
        enrichment_suggestions = await self.generate_enrichment_suggestions(df, dataset_id)
        all_suggestions.extend(enrichment_suggestions)
        
        # Generate visualization suggestions
        visualization_suggestions = await self.generate_visualization_suggestions(df, dataset_id)
        all_suggestions.extend(visualization_suggestions)
        
        # Save suggestions to database
        if all_suggestions:
            db_suggestions = await suggestions_repository.create_suggestions_batch(db, all_suggestions)
            
            return {
                "success": True,
                "suggestions_count": len(db_suggestions),
                "suggestions_by_type": {
                    "data_quality": len(quality_suggestions),
                    "transformation": len(transformation_suggestions),
                    "enrichment": len(enrichment_suggestions),
                    "visualization": len(visualization_suggestions)
                }
            }
        
        return {
            "success": False,
            "message": "No suggestions generated"
        }
    
    async def update_suggestion_status(
        self,
        db: AsyncSession,
        suggestion_id: int,
        status: SuggestionStatus,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update the status of a suggestion.
        
        Args:
            db: Database session
            suggestion_id: ID of the suggestion to update
            status: New status
            user_id: Optional user ID who selected the suggestion
            
        Returns:
            Dictionary with update result
        """
        updated_suggestion = await suggestions_repository.update_suggestion_status(
            db, suggestion_id, status, user_id
        )
        
        if updated_suggestion:
            return {
                "success": True,
                "suggestion_id": updated_suggestion.id,
                "status": updated_suggestion.status.value
            }
        
        return {
            "success": False,
            "message": f"Suggestion with ID {suggestion_id} not found"
        }
    
    async def get_suggestions_by_dataset(
        self,
        db: AsyncSession,
        dataset_id: int,
        status: Optional[SuggestionStatus] = None,
        suggestion_type: Optional[SuggestionType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get suggestions for a specific dataset with optional filters.
        
        Args:
            db: Database session
            dataset_id: Dataset ID to filter by
            status: Optional status filter
            suggestion_type: Optional suggestion type filter
            limit: Maximum number of suggestions to return
            offset: Offset for pagination
            
        Returns:
            List of suggestions as dictionaries
        """
        suggestions = await suggestions_repository.get_suggestions_by_dataset(
            db, dataset_id, status, suggestion_type, limit, offset
        )
        
        return [
            {
                "id": s.id,
                "dataset_id": s.dataset_id,
                "type": s.type.value,
                "title": s.title,
                "description": s.description,
                "content": s.content,
                "status": s.status.value,
                "confidence_score": s.confidence_score,
                "metadata": s.metadata,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
                "selected_at": s.selected_at.isoformat() if s.selected_at else None,
                "user_id": s.user_id
            }
            for s in suggestions
        ]


# Create singleton instance
suggestions_service = SuggestionsService()
