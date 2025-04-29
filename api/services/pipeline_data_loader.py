
"""
Pipeline Data Loader - Advanced data loading service with AI capabilities

This service handles loading, validating and processing data for the pipeline.
It leverages AI to dynamically detect data types, validate data according to
inferred schemas, and prepare data for storage in vector databases.
"""
import os
import pandas as pd
import numpy as np
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import uuid
from functools import lru_cache

# Import business rules service
from api.services.business_rules_service import BusinessRulesService

# Import local services
from api.services.cache_service import get_cached_response, cache_response
from api.services.ai_schema_service import detect_schema, validate_with_ai_schema

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PipelineDataLoader:
    """
    Advanced data loading service with AI-powered schema detection
    and data validation capabilities.
    
    This class orchestrates:
    1. Loading data from various sources (files, APIs, databases)
    2. AI-powered schema detection and validation
    3. Data preprocessing and cleaning
    4. Preparation for embedding and vector storage
    5. Integration with PostgreSQL and pgvector
    """
    
    def __init__(self):
        """Initialize the data loader with default settings"""
        logger.info("Initializing AI-powered Pipeline Data Loader")
        self.temp_storage = {}
        
        # Initialize business rules service
        self.business_rules_service = BusinessRulesService()
        
        # Configure supported file types and their handlers
        self.file_handlers = {
            "csv": self._load_csv,
            "excel": self._load_excel,
            "json": self._load_json,
            "parquet": self._load_parquet,
            "txt": self._load_text
        }
    
    async def load_file(self, file_path: str, file_type: str = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Load data from a file with AI-powered type inference
        
        Args:
            file_path: Path to the file
            file_type: Type of file (csv, excel, json, etc.)
            options: Additional loading options
            
        Returns:
            Dictionary containing loaded data, stats and automatically inferred schema
        """
        from api.services.openevals_service import openevals_service
        import traceback
        try:
            # Generate a unique dataset ID if not provided
            dataset_id = options.get("dataset_id") if options else None
            if not dataset_id:
                dataset_id = f"ds_{uuid.uuid4().hex[:8]}"
            
            # Check cache first
            cache_key = f"loader:file:{file_path}"
            cached_result = get_cached_response(cache_key)
            if cached_result:
                logger.info(f"Using cached file loading result for {file_path}")
                return cached_result
            
            # Determine file type if not specified
            if not file_type:
                file_type = os.path.splitext(file_path)[1].lower().lstrip('.')
                if not file_type or file_type not in self.file_handlers:
                    file_type = "csv"  # Default
            
            # Default options
            options = options or {}
            
            # Load file using appropriate handler
            if file_type in self.file_handlers:
                try:
                    df, load_stats = await self.file_handlers[file_type](file_path, options)
                except Exception as e:
                    logger.error(f"Error loading file {file_path}: {str(e)}")
                    error_info = {
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "traceback": traceback.format_exc()
                    }
                    # OpenEvals evaluation of error
                    oeval = await openevals_service.evaluate_data_quality(dataset_id, None)
                    return {"success": False, "error": error_info, "openevals_evaluation": oeval}
            else:
                error_msg = f"Unsupported file type: {file_type}"
                logger.error(error_msg)
                error_info = {
                    "error_type": "ValueError",
                    "error_message": error_msg
                }
                oeval = await openevals_service.evaluate_data_quality(dataset_id, None)
                return {"success": False, "error": error_info, "openevals_evaluation": oeval}
            
            # Store in temporary storage
            self.temp_storage[dataset_id] = df
            
            # Use AI to detect schema
            try:
                schema = await detect_schema(dataset_id)
            except Exception as e:
                logger.error(f"Error in schema detection: {str(e)}")
                schema = None
            
            # Validate a sample of the data
            try:
                validation_result = await validate_with_ai_schema(dataset_id, df.head(100))
            except Exception as e:
                logger.error(f"Error in validation: {str(e)}")
                validation_result = {"error": str(e)}
            
            # Calculate basic statistics
            try:
                stats = {
                    "record_count": len(df),
                    "column_count": len(df.columns),
                    "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    "load_time": datetime.now().isoformat(),
                    "missing_values": int(df.isna().sum().sum()),
                    "column_types": {col: str(df[col].dtype) for col in df.columns}
                }
            except Exception as e:
                logger.error(f"Error in stats calculation: {str(e)}")
                stats = {"error": str(e)}
            
            # OpenEvals data quality evaluation
            try:
                openevals_result = await openevals_service.evaluate_data_quality(dataset_id, df)
            except Exception as e:
                logger.error(f"OpenEvals data quality evaluation failed: {str(e)}")
                openevals_result = {"error": str(e)}
            
            # Combine results
            result = {
                "success": True,
                "dataset_id": dataset_id,
                "data_sample": df.head(10).to_dict(orient="records"),
                "stats": {**stats, **load_stats} if load_stats else stats,
                "schema": schema,
                "validation": {
                    "valid_rows": validation_result["stats"]["valid_rows"],
                    "invalid_rows": validation_result["stats"]["invalid_rows"],
                    "error_count": len(validation_result["errors"])
                }
            }
            
            # Cache the result (1 hour)
            cache_response(cache_key, result, 3600)
            
            return result
            
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _load_csv(self, file_path: str, options: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Load data from CSV file with smart inference"""
        options = options or {}
        
        # Try different encodings
        encodings = ["utf-8", "latin1", "iso-8859-1"]
        df = None
        
        for encoding in encodings:
            try:
                # Use pandas with automatic delimiter detection
                df = pd.read_csv(
                    file_path,
                    encoding=encoding,
                    sep=None,  # Auto-detect separator
                    engine="python",
                    **options
                )
                break
            except Exception as e:
                logger.debug(f"Failed to read with encoding {encoding}: {str(e)}")
        
        if df is None:
            raise ValueError("Failed to load CSV file with any encoding")
        
        # Perform automatic type inference
        df = self._infer_column_types(df)
        
        # Calculate stats
        stats = {
            "encoding": encoding,
            "delimiter": pd.read_csv(file_path, encoding=encoding, sep=None, engine="python", nrows=1).iloc[0].name[-1],
            "has_header": True  # Assuming header exists
        }
        
        return df, stats
    
    async def _load_excel(self, file_path: str, options: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Load data from Excel file"""
        options = options or {}
        sheet_name = options.get("sheet_name", 0)
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        df = self._infer_column_types(df)
        
        # Get all sheet names
        xls = pd.ExcelFile(file_path)
        
        stats = {
            "sheets": xls.sheet_names,
            "active_sheet": sheet_name
        }
        
        return df, stats
    
    async def _load_json(self, file_path: str, options: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Load data from JSON file with smart handling of different formats"""
        options = options or {}
        
        # Try to determine if it's an array of objects or a complex structure
        with open(file_path, 'r') as f:
            # Read just enough to determine structure (first 1000 chars)
            start = f.read(1000).strip()
        
        orient = "records"  # default
        if start.startswith('['):
            # Array of objects (most common)
            orient = "records"
        elif start.startswith('{') and '"data"' in start:
            # Object with data property
            orient = "values"
        
        # Load full JSON
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Handle common JSON formats
        if isinstance(data, list):
            # Array of objects
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Object - try to find data array
            for key in ["data", "results", "items", "records"]:
                if key in data and isinstance(data[key], list):
                    df = pd.DataFrame(data[key])
                    break
            else:
                # Fallback - try to convert the object itself
                df = pd.DataFrame([data])
        else:
            raise ValueError("Unsupported JSON structure")
        
        df = self._infer_column_types(df)
        
        stats = {
            "json_structure": "array" if isinstance(data, list) else "object",
            "nested_level": self._calculate_json_nesting(data)
        }
        
        return df, stats
    
    async def _load_parquet(self, file_path: str, options: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Load data from Parquet file"""
        df = pd.read_parquet(file_path)
        
        stats = {
            "compression": "snappy"  # Most common default
        }
        
        return df, stats
    
    async def _load_text(self, file_path: str, options: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Load data from text file with delimiter detection"""
        options = options or {}
        
        # Try to detect structure and create DataFrame
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines()[:100] if line.strip()]
        
        if not lines:
            raise ValueError("Empty file")
        
        # Try common delimiters
        delimiters = [',', '\t', '|', ';', ' ']
        best_delimiter = None
        max_columns = 0
        
        for delimiter in delimiters:
            # Count consistent number of columns
            col_counts = [len(line.split(delimiter)) for line in lines]
            consistent_cols = max(set(col_counts), key=col_counts.count)
            consistent_count = col_counts.count(consistent_cols)
            
            # Keep track of best delimiter
            if consistent_count > 0 and consistent_cols > max_columns:
                max_columns = consistent_cols
                best_delimiter = delimiter
        
        if not best_delimiter:
            # No good delimiter found, treat as single column
            df = pd.DataFrame({"text": lines})
        else:
            # Use detected delimiter
            df = pd.read_csv(file_path, sep=best_delimiter, header=None, engine="python")
            # Try to detect if first row is header
            if df.shape[0] > 1:
                first_row_types = [type(x) for x in df.iloc[0]]
                rest_types = [df.iloc[1:, i].dtype for i in range(df.shape[1])]
                if all(str(t1) != str(t2) for t1, t2 in zip(first_row_types, rest_types)):
                    # First row is probably a header
                    df.columns = df.iloc[0]
                    df = df.iloc[1:]
            
        df = self._infer_column_types(df)
        
        stats = {
            "delimiter": best_delimiter,
            "has_header": first_row_types != rest_types if 'first_row_types' in locals() else False
        }
        
        return df, stats
    
    def _infer_column_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Use advanced type inference to clean DataFrame"""
        for col in df.columns:
            # Skip columns that already have appropriate types
            if df[col].dtype != 'object':
                continue
                
            # Try to convert to datetime
            try:
                pd.to_datetime(df[col], errors='raise')
                df[col] = pd.to_datetime(df[col])
                continue
            except:
                pass
                
            # Try to convert to numeric
            try:
                numeric_values = pd.to_numeric(df[col], errors='coerce')
                # Only convert if most values are valid numbers
                if numeric_values.notna().mean() > 0.8:
                    df[col] = numeric_values
                continue
            except:
                pass
                
            # Check for boolean values
            bool_values = {'true', 'false', 'yes', 'no', 'y', 'n', 't', 'f', '1', '0'}
            if df[col].astype(str).str.lower().isin(bool_values).all():
                df[col] = df[col].astype(str).str.lower().map({
                    'true': True, 'yes': True, 'y': True, 't': True, '1': True,
                    'false': False, 'no': False, 'n': False, 'f': False, '0': False
                })
                
        return df
    
    def _calculate_json_nesting(self, data: Any, current_level: int = 0) -> int:
        """Calculate the maximum nesting level in JSON data"""
        if isinstance(data, dict):
            if not data:
                return current_level
            return max(self._calculate_json_nesting(v, current_level + 1) for v in data.values())
        elif isinstance(data, list):
            if not data:
                return current_level
            return max(self._calculate_json_nesting(item, current_level + 1) for item in data)
        else:
            return current_level
    
    async def apply_business_rules(self, dataset_id: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Apply business rules to the dataset
        
        Args:
            dataset_id: ID of the dataset
            df: DataFrame to validate
            
        Returns:
            Business rules validation results
        """
        try:
            # Get business rules for the dataset
            rules = await self.business_rules_service.get_rules_for_dataset(dataset_id)
            
            if not rules or len(rules) == 0:
                return {
                    "success": True,
                    "message": "No business rules found for this dataset",
                    "rules_applied": 0,
                    "violations": []
                }
            
            # Apply each rule and collect results
            results = []
            for rule in rules:
                # Skip disabled rules
                if not rule.get("active", True):
                    continue
                    
                rule_result = await self.business_rules_service.execute_rule(rule, df)
                results.append({
                    "rule_id": rule.get("id"),
                    "rule_name": rule.get("name"),
                    "passed": rule_result.get("passed", False),
                    "violations": rule_result.get("violations", []),
                    "violation_count": len(rule_result.get("violations", [])),
                    "execution_time": rule_result.get("execution_time")
                })
            
            # Summarize results
            total_rules = len([r for r in rules if r.get("active", True)])
            passed_rules = len([r for r in results if r["passed"]])
            total_violations = sum(r["violation_count"] for r in results)
            
            return {
                "success": True,
                "total_rules": total_rules,
                "passed_rules": passed_rules,
                "failed_rules": total_rules - passed_rules,
                "total_violations": total_violations,
                "rule_results": results
            }
            
        except Exception as e:
            logger.error(f"Error applying business rules for dataset {dataset_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def validate_data(self, dataset_id: str, validation_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate dataset using AI-powered schema detection
        
        Args:
            dataset_id: ID of the dataset
            validation_options: Additional validation options
            
        Returns:
            Validation results
        """
        try:
            validation_options = validation_options or {}
            
            # Get data
            if dataset_id in self.temp_storage:
                df = self.temp_storage[dataset_id]
            else:
                return {
                    "success": False,
                    "error": f"Dataset {dataset_id} not found in storage"
                }
            
            # Use AI to detect schema if not provided
            schema = validation_options.get("schema")
            if not schema:
                schema = await detect_schema(dataset_id)
            
            # Validate against schema
            validation_result = await validate_with_ai_schema(dataset_id, df)
            
            # Apply business rules
            business_rules_result = await self.apply_business_rules(dataset_id, df)
            
            return {
                "success": True,
                "dataset_id": dataset_id,
                "validation_results": validation_result,
                "business_rules_results": business_rules_result,
                "schema": schema
            }
            
        except Exception as e:
            logger.error(f"Error validating data for dataset {dataset_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def prepare_for_vector_db(self, 
                                   dataset_id: str, 
                                   text_columns: List[str] = None, 
                                   embedding_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Prepare dataset for vector database storage
        
        Args:
            dataset_id: ID of the dataset
            text_columns: Columns to use for text embedding
            embedding_options: Additional embedding options
            
        Returns:
            Preparation results including sample embeddings
        """
        try:
            embedding_options = embedding_options or {}
            
            # Get data
            if dataset_id in self.temp_storage:
                df = self.temp_storage[dataset_id]
            else:
                return {
                    "success": False,
                    "error": f"Dataset {dataset_id} not found in storage"
                }
            
            # Auto-detect text columns if not specified
            if not text_columns:
                text_columns = []
                # Look for likely text columns (object type with enough text)
                for col in df.columns:
                    if df[col].dtype == 'object':
                        # Check if column has string values with sufficient length
                        sample = df[col].dropna().astype(str)
                        if len(sample) > 0 and sample.str.len().mean() > 10:
                            text_columns.append(col)
            
            # If still no text columns, use all object columns
            if not text_columns:
                text_columns = [col for col in df.columns if df[col].dtype == 'object']
            
            # Check if we have columns to work with
            if not text_columns:
                return {
                    "success": False,
                    "error": "No suitable text columns found for vector embeddings"
                }
            
            # Generate mock sample embeddings (in real implementation, use a model)
            # In a real app, this would use a transformer model
            sample_size = min(5, len(df))
            sample_df = df.sample(sample_size) if len(df) > 5 else df
            
            sample_results = []
            for _, row in sample_df.iterrows():
                # Combine text from selected columns
                text = " ".join([str(row[col]) for col in text_columns if pd.notna(row[col])])
                
                # In real app, this would be an actual embedding from a model
                # For demonstration, we're creating a mock embedding
                mock_embedding = np.random.randn(384).tolist()  # 384D is common for embeddings
                
                sample_results.append({
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "columns_used": text_columns,
                    "embedding_dimension": len(mock_embedding),
                    "sample_embedding": mock_embedding[:5] + ["..."]  # Show just first few dimensions
                })
            
            return {
                "success": True,
                "dataset_id": dataset_id,
                "preparation_results": {
                    "text_columns": text_columns,
                    "record_count": len(df),
                    "embedding_dimension": 384,  # Common size for sentence embeddings
                    "sample_results": sample_results
                }
            }
        
        except Exception as e:
            logger.error(f"Error preparing vector data for dataset {dataset_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def store_in_pg_vector(self, dataset_id: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Store dataset in PostgreSQL with pgvector extension
        
        Args:
            dataset_id: ID of the dataset
            options: Storage options including connection details
            
        Returns:
            Storage results
        """
        # This is a mock implementation - in a real app, this would connect to PostgreSQL
        try:
            options = options or {}
            
            # Get data
            if dataset_id in self.temp_storage:
                df = self.temp_storage[dataset_id]
            else:
                return {
                    "success": False,
                    "error": f"Dataset {dataset_id} not found in storage"
                }
            
            # Mock database connection and storage
            table_name = options.get("table_name", f"dataset_{dataset_id}")
            
            # In a real implementation, this would:
            # 1. Connect to PostgreSQL
            # 2. Create a table with appropriate schema
            # 3. Store the data
            # 4. Create vector indexes for embedding columns
            
            return {
                "success": True,
                "dataset_id": dataset_id,
                "storage_results": {
                    "database": "postgres",
                    "table": table_name,
                    "records_stored": len(df),
                    "columns_stored": list(df.columns),
                    "vector_indexes": ["embedding_idx"],
                    "storage_time": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error storing in PG Vector for dataset {dataset_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_pipeline_process(self, file_path: str, file_type: str = None) -> Dict[str, Any]:
        """
        Run a complete data pipeline test process
        
        Args:
            file_path: Path to the file to process
            file_type: Type of file (csv, excel, json, etc.)
            
        Returns:
            Complete processing results
        """
        try:
            # Step 1: Load data
            load_result = await self.load_file(file_path, file_type)
            if not load_result["success"]:
                return load_result
            
            dataset_id = load_result["dataset_id"]
            
            # Step 2: Validate data
            validation_result = await self.validate_data(dataset_id)
            if not validation_result["success"]:
                return validation_result
                
            # Step 3: Prepare for vector database
            vector_result = await self.prepare_for_vector_db(dataset_id)
            if not vector_result["success"]:
                return vector_result
                
            # Step 4: Store in PostgreSQL with pgvector
            storage_result = await self.store_in_pg_vector(dataset_id)
            if not storage_result["success"]:
                return storage_result
                
            # Combine all results
            return {
                "success": True,
                "dataset_id": dataset_id,
                "pipeline_test_results": {
                    "loading": load_result,
                    "validation": validation_result["validation_results"]["stats"],
                    "vector_preparation": vector_result["preparation_results"],
                    "storage": storage_result["storage_results"],
                    "completed_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in pipeline test process: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Create singleton instance
pipeline_loader = PipelineDataLoader()

# API function to load data
async def load_data_file(file_path: str, file_type: str = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """Load data from a file with AI-powered schema detection"""
    return await pipeline_loader.load_file(file_path, file_type, options)

# API function to validate data
async def validate_dataset(dataset_id: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """Validate a dataset using AI-powered schema detection"""
    return await pipeline_loader.validate_data(dataset_id, options)

# API function to prepare data for vector database
async def prepare_for_vectors(dataset_id: str, text_columns: List[str] = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """Prepare a dataset for vector database storage"""
    return await pipeline_loader.prepare_for_vector_db(dataset_id, text_columns, options)

# API function to store data in PostgreSQL with pgvector
async def store_in_pgvector(dataset_id: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """Store a dataset in PostgreSQL with pgvector extension"""
    return await pipeline_loader.store_in_pg_vector(dataset_id, options)

# API function to run complete pipeline test
async def test_pipeline(file_path: str, file_type: str = None) -> Dict[str, Any]:
    """Run a complete data pipeline test process"""
    return await pipeline_loader.test_pipeline_process(file_path, file_type)
