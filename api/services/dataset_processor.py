import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from fastapi import HTTPException

# Import vector service for embedding generation
from .vector_service import VectorService, add_vectors, get_vector_db
from .ai_agent_service import generate_embeddings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dataset storage path
DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'datasets')

# Ensure datasets directory exists
os.makedirs(DATASET_PATH, exist_ok=True)

# Dataset dataset_metadata
dataset_dataset_metadata = {}
METADATA_PATH = os.path.join(DATASET_PATH, 'dataset_metadata.json')

# Initialize vector service
vector_service = VectorService()

# Load dataset_metadata if exists
def load_dataset_metadata():
    """Load dataset dataset_metadata from disk"""
    global dataset_dataset_metadata
    
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, 'r') as f:
                dataset_dataset_metadata = json.load(f)
            logger.info(f"Loaded dataset dataset_metadata with {len(dataset_dataset_metadata)} datasets")
        except Exception as e:
            logger.error(f"Error loading dataset dataset_metadata: {str(e)}")
            dataset_dataset_metadata = {}

# Save dataset_metadata
def save_dataset_metadata():
    """Save dataset dataset_metadata to disk"""
    try:
        with open(METADATA_PATH, 'w') as f:
            json.dump(dataset_dataset_metadata, f, indent=2)
        logger.info(f"Saved dataset dataset_metadata")
        return True
    except Exception as e:
        logger.error(f"Error saving dataset dataset_metadata: {str(e)}")
        return False

# Initialize dataset_metadata
load_dataset_metadata()

async def process_dataset(dataset_id: str, file_path: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Process a dataset after pipeline processing and prepare it for AI analysis
    - Loads the dataset
    - Extracts schema and statistics
    - Generates embeddings for vectorization
    - Updates dataset_metadata
    
    Args:
        dataset_id: Unique identifier for the dataset
        file_path: Path to the processed dataset file
        options: Processing options
        
    Returns:
        Processed dataset information
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Dataset file not found: {file_path}")
        
        # Determine file type and load dataset
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.json'):
            df = pd.read_json(file_path)
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_path}")
        
        # Get basic dataset information
        rows, columns = df.shape
        column_names = df.columns.tolist()
        
        # Calculate basic statistics
        statistics = {
            "numeric_columns": {},
            "categorical_columns": {},
            "text_columns": {},
            "temporal_columns": {}
        }
        
        # Analyze columns
        for col in column_names:
            # Skip if column is all null
            if df[col].isna().all():
                continue
                
            # Check data type and calculate appropriate statistics
            if pd.api.types.is_numeric_dtype(df[col]):
                statistics["numeric_columns"][col] = {
                    "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                    "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                    "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                    "median": float(df[col].median()) if not pd.isna(df[col].median()) else None,
                    "std": float(df[col].std()) if not pd.isna(df[col].std()) else None,
                    "nulls": int(df[col].isna().sum()),
                    "nulls_percent": float(df[col].isna().mean() * 100)
                }
            elif pd.api.types.is_string_dtype(df[col]):
                # Check if it's a categorical or text column
                unique_values = df[col].nunique()
                unique_ratio = unique_values / rows if rows > 0 else 0
                
                if unique_ratio < 0.2 and unique_values < 100:  # Likely categorical
                    value_counts = df[col].value_counts().head(20).to_dict()
                    statistics["categorical_columns"][col] = {
                        "unique_values": int(unique_values),
                        "most_common": value_counts,
                        "nulls": int(df[col].isna().sum()),
                        "nulls_percent": float(df[col].isna().mean() * 100)
                    }
                else:  # Likely text
                    # Calculate average text length
                    text_lengths = df[col].astype(str).str.len()
                    statistics["text_columns"][col] = {
                        "avg_length": float(text_lengths.mean()) if not pd.isna(text_lengths.mean()) else 0,
                        "max_length": int(text_lengths.max()) if not pd.isna(text_lengths.max()) else 0,
                        "min_length": int(text_lengths.min()) if not pd.isna(text_lengths.min()) else 0,
                        "nulls": int(df[col].isna().sum()),
                        "nulls_percent": float(df[col].isna().mean() * 100)
                    }
            elif pd.api.types.is_datetime64_dtype(df[col]):
                statistics["temporal_columns"][col] = {
                    "min": df[col].min().isoformat() if not pd.isna(df[col].min()) else None,
                    "max": df[col].max().isoformat() if not pd.isna(df[col].max()) else None,
                    "nulls": int(df[col].isna().sum()),
                    "nulls_percent": float(df[col].isna().mean() * 100)
                }
        
        # Generate dataset summary
        summary = f"Dataset '{dataset_id}' with {rows} rows and {columns} columns. "
        summary += f"Columns include: {', '.join(column_names[:10])}"
        if len(column_names) > 10:
            summary += f" and {len(column_names) - 10} more."
            
        # Create dataset description for vectorization
        column_descriptions = []
        for col in column_names:
            if col in statistics["numeric_columns"]:
                stats = statistics["numeric_columns"][col]
                col_desc = f"Column '{col}' is numeric with range from {stats['min']} to {stats['max']}, mean {stats['mean']:.2f}."
                column_descriptions.append(col_desc)
            elif col in statistics["categorical_columns"]:
                stats = statistics["categorical_columns"][col]
                top_cats = list(stats["most_common"].keys())[:5]
                col_desc = f"Column '{col}' is categorical with {stats['unique_values']} unique values including {', '.join(top_cats)}."
                column_descriptions.append(col_desc)
            elif col in statistics["text_columns"]:
                stats = statistics["text_columns"][col]
                col_desc = f"Column '{col}' contains text with average length {stats['avg_length']:.1f} characters."
                column_descriptions.append(col_desc)
            elif col in statistics["temporal_columns"]:
                stats = statistics["temporal_columns"][col]
                col_desc = f"Column '{col}' contains dates/times from {stats['min']} to {stats['max']}."
                column_descriptions.append(col_desc)
                
        # Save dataset information to dataset_metadata
        dataset_dataset_metadata[dataset_id] = {
            "id": dataset_id,
            "file_path": file_path,
            "rows": rows,
            "columns": columns,
            "column_names": column_names,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "summary": summary,
            "statistics": statistics
        }
        
        # Save dataset_metadata
        save_dataset_metadata()
        
        # Generate embeddings for the dataset description
        dataset_texts = [
            {"content": summary, "dataset_metadata": {"type": "summary", "dataset_id": dataset_id, "source": f"Dataset: {dataset_id}"}},
        ]
        
        # Add column descriptions
        for desc in column_descriptions:
            dataset_texts.append({
                "content": desc,
                "dataset_metadata": {"type": "column_description", "dataset_id": dataset_id, "source": f"Dataset: {dataset_id}"}
            })
            
        # Add sample data (first few rows)
        sample_rows = min(5, rows)
        if sample_rows > 0:
            sample_data = df.head(sample_rows).to_dict(orient='records')
            for i, row in enumerate(sample_data):
                # Convert to string representation
                row_str = ", ".join([f"{col}: {val}" for col, val in row.items()])
                dataset_texts.append({
                    "content": f"Sample data row {i+1}: {row_str}",
                    "dataset_metadata": {"type": "sample_data", "dataset_id": dataset_id, "row": i, "source": f"Dataset: {dataset_id}"}
                })
        
        # Generate embeddings for each text
        vectors_to_add = []
        for item in dataset_texts:
            try:
                # Generate embedding
                embedding_result = await generate_embeddings(item["content"])
                
                # Add to vectors if successful
                if embedding_result["success"] and "embeddings" in embedding_result:
                    vectors_to_add.append({
                        "content": item["content"],
                        "vector": embedding_result["embeddings"],
                        "dataset_metadata": item["dataset_metadata"]
                    })
            except Exception as e:
                logger.error(f"Error generating embedding for dataset text: {str(e)}")
        
        # Add vectors to database
        if vectors_to_add:
            await add_vectors(dataset_id, vectors_to_add)
            
        # Extract data patterns and insights (simple version)
        patterns = extract_data_patterns(df)
        
        return {
            "success": True,
            "dataset_id": dataset_id,
            "rows": rows,
            "columns": columns,
            "summary": summary,
            "vectors_added": len(vectors_to_add),
            "patterns": patterns
        }
    
    except Exception as e:
        logger.error(f"Error processing dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process dataset: {str(e)}")

def extract_data_patterns(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Extract patterns and insights from the dataset
    """
    patterns = []
    
    try:
        # Check for missing values
        missing_vals = df.isna().sum()
        cols_with_missing = missing_vals[missing_vals > 0]
        if not cols_with_missing.empty:
            for col, count in cols_with_missing.items():
                percent = (count / len(df)) * 100
                if percent > 5:  # Only report if more than 5% missing
                    patterns.append({
                        "type": "missing_values",
                        "column": col,
                        "count": int(count),
                        "percent": float(percent),
                        "description": f"Column '{col}' has {percent:.1f}% missing values"
                    })
        
        # Check for outliers in numeric columns
        for col in df.select_dtypes(include=[np.number]).columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col]
            
            if len(outliers) > 0 and len(outliers) < len(df) * 0.1:  # Less than 10% are outliers
                patterns.append({
                    "type": "outliers",
                    "column": col,
                    "count": len(outliers),
                    "percent": float((len(outliers) / len(df)) * 100),
                    "description": f"Column '{col}' has {len(outliers)} outliers ({(len(outliers) / len(df) * 100):.1f}%)"
                })
        
        # Check for correlations between numeric columns
        if len(df.select_dtypes(include=[np.number]).columns) >= 2:
            corr_matrix = df.select_dtypes(include=[np.number]).corr()
            # Get the strongest correlations (ignoring self-correlations)
            strong_corrs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    corr = corr_matrix.iloc[i, j]
                    if abs(corr) > 0.7:  # Strong correlation threshold
                        strong_corrs.append((col1, col2, corr))
            
            # Add top correlations
            for col1, col2, corr in sorted(strong_corrs, key=lambda x: abs(x[2]), reverse=True)[:5]:
                corr_type = "positive" if corr > 0 else "negative"
                patterns.append({
                    "type": "correlation",
                    "columns": [col1, col2],
                    "correlation": float(corr),
                    "description": f"Strong {corr_type} correlation ({corr:.2f}) between '{col1}' and '{col2}'"
                })
    
    except Exception as e:
        logger.error(f"Error extracting data patterns: {str(e)}")
    
    return patterns

async def get_datasets() -> List[Dict[str, Any]]:
    """
    Get list of all datasets with dataset_metadata
    """
    datasets = []
    
    for dataset_id, dataset_metadata in dataset_dataset_metadata.items():
        datasets.append({
            "id": dataset_id,
            "name": dataset_metadata.get("name", dataset_id),
            "rows": dataset_metadata.get("rows", 0),
            "columns": dataset_metadata.get("columns", 0),
            "updated_at": dataset_metadata.get("updated_at"),
            "summary": dataset_metadata.get("summary", "")
        })
    
    return datasets

async def get_dataset(dataset_id: str) -> Dict[str, Any]:
    """
    Get dataset_metadata for a specific dataset
    """
    if dataset_id not in dataset_dataset_metadata:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    
    return dataset_dataset_metadata[dataset_id]

async def delete_dataset(dataset_id: str) -> Dict[str, Any]:
    """
    Delete a dataset and its vectorized data
    """
    try:
        if dataset_id not in dataset_dataset_metadata:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
        
        # Get file path
        file_path = dataset_dataset_metadata[dataset_id].get("file_path")
        
        # Remove from dataset_metadata
        del dataset_dataset_metadata[dataset_id]
        save_dataset_metadata()
        
        # Delete vector data
        from .vector_service import delete_vectors
        delete_result = delete_vectors(dataset_id)
        
        # Delete file if exists
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            
        return {
            "success": True,
            "message": f"Dataset {dataset_id} deleted",
            "vectors_deleted": delete_result.get("count", 0) if delete_result.get("success", False) else 0
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete dataset: {str(e)}")

async def get_dataset_metadataset(dataset_id: str) -> Optional[Dict[str, Any]]:
    """
    Get dataset metadataset information.
    
    Args:
        dataset_id: ID of the dataset
        
    Returns:
        Dict containing dataset information or None if not found
    """
    try:
        from api.repositories import dataset_repository
        repo = dataset_repository.DatasetRepository()
        return await repo.get_dataset(dataset_id)
    except Exception as e:
        logger.error(f"Error getting dataset metadataset: {str(e)}")
        return None

async def process_dataset_metadataset(dataset_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process dataset metadataset metadata.
    
    Args:
        dataset_id: ID of the dataset
        metadata: Dataset metadata to process
        
    Returns:
        Dict containing processed metadata
    """
    try:
        from api.repositories import dataset_repository
        repo = dataset_repository.DatasetRepository()
        
        # Process metadata
        processed_metadata = {
            "dataset_id": dataset_id,
            "metadata": metadata,
            "processed_at": pd.Timestamp.now().isoformat()
        }
        
        # Store processed metadata
        await repo.update_dataset_status(dataset_id, "PROCESSED", processed_metadata)
        
        return processed_metadata
    except Exception as e:
        logger.error(f"Error processing dataset metadataset: {str(e)}")
        return {
            "dataset_id": dataset_id,
            "error": str(e)
        }
