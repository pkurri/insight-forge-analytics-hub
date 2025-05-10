from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime
import uuid

from api.services.ai_service import analyze_dataset_with_rag
from api.services.pipeline_service import PipelineService
from api.repositories.dataset_repository import DatasetRepository
from api.repositories.suggestions_repository import SuggestionsRepository
from models.suggestion import SuggestionModel, SuggestionType, SuggestionStatus

router = APIRouter(prefix="/api/datasets", tags=["insights"])
logger = logging.getLogger(__name__)

# Dictionary to store background tasks progress
task_progress = {}

@router.get("/{dataset_id}/insights")
async def get_dataset_insights(dataset_id: int):
    """
    Get insights for a specific dataset
    """
    try:
        # Initialize repositories
        suggestions_repo = SuggestionsRepository()
        await suggestions_repo.initialize()
        
        # Get suggestions for the dataset
        suggestions = await suggestions_repo.get_suggestions_by_dataset(dataset_id)
        
        # Convert to insights format
        insights = []
        for suggestion in suggestions:
            insight_type = "data_quality"
            if suggestion.type == SuggestionType.FEATURE_ENGINEERING:
                insight_type = "feature_engineering"
            elif suggestion.type == SuggestionType.ANOMALY:
                insight_type = "anomaly"
            elif suggestion.type == SuggestionType.CORRELATION:
                insight_type = "correlation"
            
            insights.append({
                "id": suggestion.id,
                "title": suggestion.title,
                "description": suggestion.description,
                "type": insight_type,
                "confidence": suggestion.confidence_score,
                "metadata": suggestion.metadata,
                "created_at": suggestion.created_at.isoformat() if suggestion.created_at else datetime.utcnow().isoformat()
            })
        
        return {"success": True, "insights": insights}
    except Exception as e:
        logger.error(f"Error getting dataset insights: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")

@router.post("/{dataset_id}/generate-insights")
async def generate_dataset_insights(
    dataset_id: int, 
    background_tasks: BackgroundTasks,
    request_data: Dict[str, Any] = {}
):
    """
    Generate insights for a dataset using RAG and agentic framework
    """
    try:
        # Create a task ID
        task_id = str(uuid.uuid4())
        task_progress[task_id] = {"progress": 0, "status": "pending"}
        
        # Start background task
        background_tasks.add_task(
            generate_insights_task, 
            task_id, 
            dataset_id, 
            request_data.get("use_agent", True),
            request_data.get("insight_types", ["data_quality", "feature_engineering", "anomaly", "correlation"])
        )
        
        return {"success": True, "task_id": task_id}
    except Exception as e:
        logger.error(f"Error starting insight generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start insight generation: {str(e)}")

@router.get("/tasks/{task_id}/progress")
async def get_task_progress(task_id: str):
    """
    Get the progress of an insight generation task
    """
    if task_id not in task_progress:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task_progress[task_id]

async def generate_insights_task(
    task_id: str, 
    dataset_id: int, 
    use_agent: bool = True,
    insight_types: List[str] = ["data_quality", "feature_engineering", "anomaly", "correlation"]
):
    """
    Background task to generate insights for a dataset
    """
    try:
        # Update task status
        task_progress[task_id] = {"progress": 5, "status": "running"}
        
        # Initialize repositories and services
        dataset_repo = DatasetRepository()
        suggestions_repo = SuggestionsRepository()
        pipeline_service = PipelineService()
        
        # Get dataset metadata and profile
        task_progress[task_id]["progress"] = 10
        metadata = await dataset_repo.get_dataset_metadata(dataset_id) or {}
        profile = await dataset_repo.get_dataset_profile(dataset_id) or {}
        
        # Generate insights based on the dataset profile
        task_progress[task_id]["progress"] = 20
        
        # Initialize suggestions list
        suggestions = []
        
        # Generate data quality insights if requested
        if "data_quality" in insight_types:
            task_progress[task_id]["progress"] = 30
            quality_insights = await generate_data_quality_insights(dataset_id, profile, use_agent)
            suggestions.extend(quality_insights)
        
        # Generate feature engineering insights if requested
        if "feature_engineering" in insight_types:
            task_progress[task_id]["progress"] = 50
            feature_insights = await generate_feature_engineering_insights(dataset_id, metadata, profile, use_agent)
            suggestions.extend(feature_insights)
        
        # Generate anomaly insights if requested
        if "anomaly" in insight_types:
            task_progress[task_id]["progress"] = 70
            anomaly_insights = await generate_anomaly_insights(dataset_id, profile, use_agent)
            suggestions.extend(anomaly_insights)
        
        # Generate correlation insights if requested
        if "correlation" in insight_types:
            task_progress[task_id]["progress"] = 85
            correlation_insights = await generate_correlation_insights(dataset_id, profile, use_agent)
            suggestions.extend(correlation_insights)
        
        # Save suggestions to database
        task_progress[task_id]["progress"] = 95
        for suggestion in suggestions:
            await suggestions_repo.create_suggestion(suggestion)
        
        # Update task status
        task_progress[task_id] = {"progress": 100, "status": "completed"}
        
        # Clean up task after 1 hour
        await asyncio.sleep(3600)
        if task_id in task_progress:
            del task_progress[task_id]
            
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        task_progress[task_id] = {"progress": 0, "status": "failed", "error": str(e)}

async def generate_data_quality_insights(dataset_id: int, profile: Dict[str, Any], use_agent: bool) -> List[SuggestionModel]:
    """Generate data quality insights using RAG and agentic framework"""
    suggestions = []
    
    try:
        # Use RAG to analyze data quality issues
        quality_query = "What are the main data quality issues in this dataset?"
        rag_result = await analyze_dataset_with_rag(dataset_id, quality_query, use_agent)
        
        if rag_result.get("success") and rag_result.get("analysis"):
            analysis = rag_result["analysis"]
            confidence = analysis.get("confidence", 0.7)
            
            # Create suggestion from analysis
            suggestions.append(SuggestionModel(
                dataset_id=dataset_id,
                title="Data Quality Analysis",
                description=analysis.get("analysis", ""),
                type=SuggestionType.DATA_QUALITY,
                status=SuggestionStatus.GENERATED,
                confidence_score=confidence,
                metadata={
                    "source": "rag_analysis",
                    "processing_time": analysis.get("processing_time", 0),
                    "affected_columns": profile.get("quality_metrics", {}).get("columns_with_issues", [])
                }
            ))
        
        # Add specific quality suggestions based on profile
        quality_metrics = profile.get("quality_metrics", {})
        
        # Missing values suggestion
        if quality_metrics.get("missing_values_percentage", 0) > 5:
            missing_cols = quality_metrics.get("columns_with_missing_values", [])
            suggestions.append(SuggestionModel(
                dataset_id=dataset_id,
                title="Address Missing Values",
                description=f"Your dataset has {quality_metrics.get('missing_values_percentage')}% missing values, primarily in columns: {', '.join(missing_cols[:3])}.",
                type=SuggestionType.DATA_QUALITY,
                status=SuggestionStatus.GENERATED,
                confidence_score=0.9,
                metadata={"affected_columns": missing_cols}
            ))
        
        # Duplicate rows suggestion
        if quality_metrics.get("duplicate_rows_count", 0) > 0:
            suggestions.append(SuggestionModel(
                dataset_id=dataset_id,
                title="Remove Duplicate Rows",
                description=f"Found {quality_metrics.get('duplicate_rows_count')} duplicate rows in your dataset.",
                type=SuggestionType.DATA_QUALITY,
                status=SuggestionStatus.GENERATED,
                confidence_score=0.95,
                metadata={}
            ))
        
        # Outlier suggestion
        if quality_metrics.get("outlier_columns", []):
            outlier_cols = quality_metrics.get("outlier_columns", [])
            suggestions.append(SuggestionModel(
                dataset_id=dataset_id,
                title="Handle Outliers",
                description=f"Detected outliers in {len(outlier_cols)} columns that may affect your analysis.",
                type=SuggestionType.DATA_QUALITY,
                status=SuggestionStatus.GENERATED,
                confidence_score=0.8,
                metadata={"affected_columns": outlier_cols}
            ))
    
    except Exception as e:
        logger.error(f"Error generating data quality insights: {str(e)}")
    
    return suggestions

async def generate_feature_engineering_insights(dataset_id: int, metadata: Dict[str, Any], profile: Dict[str, Any], use_agent: bool) -> List[SuggestionModel]:
    """Generate feature engineering insights using RAG and agentic framework"""
    suggestions = []
    
    try:
        # Use RAG to analyze potential feature engineering opportunities
        feature_query = "What feature engineering opportunities exist in this dataset?"
        rag_result = await analyze_dataset_with_rag(dataset_id, feature_query, use_agent)
        
        if rag_result.get("success") and rag_result.get("analysis"):
            analysis = rag_result["analysis"]
            confidence = analysis.get("confidence", 0.7)
            
            # Create suggestion from analysis
            suggestions.append(SuggestionModel(
                dataset_id=dataset_id,
                title="Feature Engineering Opportunities",
                description=analysis.get("analysis", ""),
                type=SuggestionType.FEATURE_ENGINEERING,
                status=SuggestionStatus.GENERATED,
                confidence_score=confidence,
                metadata={
                    "source": "rag_analysis",
                    "processing_time": analysis.get("processing_time", 0)
                }
            ))
        
        # Add specific feature engineering suggestions based on column types
        column_types = metadata.get("column_types", {})
        date_columns = [col for col, type in column_types.items() if type == "datetime"]
        
        # Date feature extraction
        if date_columns:
            suggestions.append(SuggestionModel(
                dataset_id=dataset_id,
                title="Extract Date Features",
                description=f"Extract year, month, day, and day of week from date columns: {', '.join(date_columns[:3])}.",
                type=SuggestionType.FEATURE_ENGINEERING,
                status=SuggestionStatus.GENERATED,
                confidence_score=0.85,
                metadata={"affected_columns": date_columns}
            ))
        
        # Text column processing
        text_columns = [col for col, type in column_types.items() if type == "text" or type == "string"]
        if text_columns:
            suggestions.append(SuggestionModel(
                dataset_id=dataset_id,
                title="Text Feature Extraction",
                description=f"Extract features from text columns like word count, character count, and sentiment.",
                type=SuggestionType.FEATURE_ENGINEERING,
                status=SuggestionStatus.GENERATED,
                confidence_score=0.75,
                metadata={"affected_columns": text_columns}
            ))
        
        # Numeric column normalization
        numeric_columns = [col for col, type in column_types.items() if type == "numeric" or type == "integer" or type == "float"]
        if numeric_columns:
            suggestions.append(SuggestionModel(
                dataset_id=dataset_id,
                title="Normalize Numeric Features",
                description=f"Normalize numeric columns to improve model performance.",
                type=SuggestionType.FEATURE_ENGINEERING,
                status=SuggestionStatus.GENERATED,
                confidence_score=0.8,
                metadata={"affected_columns": numeric_columns}
            ))
    
    except Exception as e:
        logger.error(f"Error generating feature engineering insights: {str(e)}")
    
    return suggestions

async def generate_anomaly_insights(dataset_id: int, profile: Dict[str, Any], use_agent: bool) -> List[SuggestionModel]:
    """Generate anomaly insights using RAG and agentic framework"""
    suggestions = []
    
    try:
        # Use RAG to analyze anomalies
        anomaly_query = "What anomalies or unusual patterns exist in this dataset?"
        rag_result = await analyze_dataset_with_rag(dataset_id, anomaly_query, use_agent)
        
        if rag_result.get("success") and rag_result.get("analysis"):
            analysis = rag_result["analysis"]
            confidence = analysis.get("confidence", 0.7)
            
            # Create suggestion from analysis
            suggestions.append(SuggestionModel(
                dataset_id=dataset_id,
                title="Anomaly Detection Results",
                description=analysis.get("analysis", ""),
                type=SuggestionType.ANOMALY,
                status=SuggestionStatus.GENERATED,
                confidence_score=confidence,
                metadata={
                    "source": "rag_analysis",
                    "processing_time": analysis.get("processing_time", 0)
                }
            ))
        
        # Add specific anomaly suggestions based on profile
        anomaly_metrics = profile.get("anomaly_metrics", {})
        
        if anomaly_metrics.get("detected_anomalies", []):
            anomalies = anomaly_metrics.get("detected_anomalies", [])
            for anomaly in anomalies[:3]:  # Limit to top 3 anomalies
                suggestions.append(SuggestionModel(
                    dataset_id=dataset_id,
                    title=f"Anomaly: {anomaly.get('type', 'Unknown')}",
                    description=anomaly.get("description", "Unusual pattern detected in the dataset."),
                    type=SuggestionType.ANOMALY,
                    status=SuggestionStatus.GENERATED,
                    confidence_score=anomaly.get("confidence", 0.7),
                    metadata={
                        "affected_columns": anomaly.get("columns", []),
                        "row_indices": anomaly.get("row_indices", [])[:10]  # Limit to first 10 indices
                    }
                ))
    
    except Exception as e:
        logger.error(f"Error generating anomaly insights: {str(e)}")
    
    return suggestions

async def generate_correlation_insights(dataset_id: int, profile: Dict[str, Any], use_agent: bool) -> List[SuggestionModel]:
    """Generate correlation insights using RAG and agentic framework"""
    suggestions = []
    
    try:
        # Use RAG to analyze correlations
        correlation_query = "What are the key correlations and relationships in this dataset?"
        rag_result = await analyze_dataset_with_rag(dataset_id, correlation_query, use_agent)
        
        if rag_result.get("success") and rag_result.get("analysis"):
            analysis = rag_result["analysis"]
            confidence = analysis.get("confidence", 0.7)
            
            # Create suggestion from analysis
            suggestions.append(SuggestionModel(
                dataset_id=dataset_id,
                title="Correlation Analysis",
                description=analysis.get("analysis", ""),
                type=SuggestionType.CORRELATION,
                status=SuggestionStatus.GENERATED,
                confidence_score=confidence,
                metadata={
                    "source": "rag_analysis",
                    "processing_time": analysis.get("processing_time", 0)
                }
            ))
        
        # Add specific correlation suggestions based on profile
        correlation_matrix = profile.get("correlation_matrix", {})
        
        # Strong positive correlations
        strong_positive = []
        for col1, correlations in correlation_matrix.items():
            for col2, value in correlations.items():
                if col1 != col2 and value > 0.7:
                    strong_positive.append((col1, col2, value))
        
        if strong_positive:
            # Sort by correlation strength
            strong_positive.sort(key=lambda x: x[2], reverse=True)
            
            # Create suggestion for top correlations
            top_correlations = strong_positive[:5]  # Limit to top 5
            description = "Strong positive correlations found:\n"
            for col1, col2, value in top_correlations:
                description += f"- {col1} and {col2}: {value:.2f}\n"
            
            suggestions.append(SuggestionModel(
                dataset_id=dataset_id,
                title="Strong Positive Correlations",
                description=description,
                type=SuggestionType.CORRELATION,
                status=SuggestionStatus.GENERATED,
                confidence_score=0.9,
                metadata={
                    "correlations": [{"col1": c1, "col2": c2, "value": v} for c1, c2, v in top_correlations]
                }
            ))
        
        # Strong negative correlations
        strong_negative = []
        for col1, correlations in correlation_matrix.items():
            for col2, value in correlations.items():
                if col1 != col2 and value < -0.7:
                    strong_negative.append((col1, col2, value))
        
        if strong_negative:
            # Sort by correlation strength (most negative first)
            strong_negative.sort(key=lambda x: x[2])
            
            # Create suggestion for top negative correlations
            top_correlations = strong_negative[:5]  # Limit to top 5
            description = "Strong negative correlations found:\n"
            for col1, col2, value in top_correlations:
                description += f"- {col1} and {col2}: {value:.2f}\n"
            
            suggestions.append(SuggestionModel(
                dataset_id=dataset_id,
                title="Strong Negative Correlations",
                description=description,
                type=SuggestionType.CORRELATION,
                status=SuggestionStatus.GENERATED,
                confidence_score=0.9,
                metadata={
                    "correlations": [{"col1": c1, "col2": c2, "value": v} for c1, c2, v in top_correlations]
                }
            ))
    
    except Exception as e:
        logger.error(f"Error generating correlation insights: {str(e)}")
    
    return suggestions
