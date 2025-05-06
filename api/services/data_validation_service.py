import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from models.dataset import PipelineRunStatus

class DataValidationService:
    """Service for data validation operations."""
    
    async def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate the data and return validation results."""
        results = {
            "basic_stats": await self._get_basic_stats(df),
            "data_quality": await self._check_data_quality(df),
            "schema_validation": await self._validate_schema(df),
            "business_rules": await self._check_business_rules(df)
        }
        
        # Calculate overall validation score
        quality_score = results["data_quality"]["score"]
        schema_score = results["schema_validation"]["score"]
        rules_score = results["business_rules"]["score"]
        
        results["overall_score"] = (quality_score + schema_score + rules_score) / 3
        
        return results
    
    async def _get_basic_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get basic statistics for each column."""
        stats = {}
        
        for col in df.columns:
            col_stats = {
                "count": len(df),
                "null_count": df[col].isnull().sum(),
                "unique_count": df[col].nunique()
            }
            
            if df[col].dtype in ['int64', 'float64']:
                col_stats.update({
                    "min": df[col].min(),
                    "max": df[col].max(),
                    "mean": df[col].mean(),
                    "median": df[col].median(),
                    "std": df[col].std()
                })
            elif df[col].dtype == 'object':
                col_stats.update({
                    "most_common": df[col].mode().iloc[0],
                    "most_common_count": df[col].value_counts().iloc[0]
                })
                
            stats[col] = col_stats
            
        return stats
    
    async def _check_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check data quality metrics."""
        quality_checks = {
            "completeness": {},
            "consistency": {},
            "accuracy": {},
            "issues": []
        }
        
        # Check completeness
        for col in df.columns:
            null_pct = df[col].isnull().mean()
            quality_checks["completeness"][col] = {
                "null_percentage": null_pct,
                "is_complete": null_pct < 0.1  # Consider >10% nulls as incomplete
            }
            
            if null_pct > 0.1:
                quality_checks["issues"].append({
                    "type": "completeness",
                    "column": col,
                    "message": f"High percentage of null values: {null_pct:.1%}"
                })
        
        # Check consistency
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check for inconsistent string formats
                unique_formats = df[col].dropna().apply(lambda x: str(x).strip()).nunique()
                total_unique = df[col].nunique()
                
                quality_checks["consistency"][col] = {
                    "format_consistency": unique_formats / total_unique if total_unique > 0 else 1.0,
                    "is_consistent": unique_formats / total_unique > 0.9 if total_unique > 0 else True
                }
                
                if unique_formats / total_unique < 0.9 and total_unique > 0:
                    quality_checks["issues"].append({
                        "type": "consistency",
                        "column": col,
                        "message": "Inconsistent string formats detected"
                    })
        
        # Calculate overall quality score
        completeness_score = np.mean([
            check["is_complete"]
            for checks in quality_checks["completeness"].values()
            for check in [checks]
        ])
        
        consistency_score = np.mean([
            check["is_consistent"]
            for checks in quality_checks["consistency"].values()
            for check in [checks]
        ])
        
        quality_checks["score"] = (completeness_score + consistency_score) / 2
        
        return quality_checks
    
    async def _validate_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate the data against expected schema."""
        schema_validation = {
            "column_types": {},
            "required_columns": [],
            "issues": []
        }
        
        # Check column types
        for col in df.columns:
            expected_type = self._get_expected_type(df[col])
            actual_type = str(df[col].dtype)
            
            schema_validation["column_types"][col] = {
                "expected": expected_type,
                "actual": actual_type,
                "is_valid": expected_type == actual_type
            }
            
            if expected_type != actual_type:
                schema_validation["issues"].append({
                    "type": "schema",
                    "column": col,
                    "message": f"Type mismatch: expected {expected_type}, got {actual_type}"
                })
        
        # Calculate schema validation score
        type_score = np.mean([
            check["is_valid"]
            for checks in schema_validation["column_types"].values()
            for check in [checks]
        ])
        
        schema_validation["score"] = type_score
        
        return schema_validation
    
    async def _check_business_rules(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check business rules and constraints."""
        business_rules = {
            "rules": {},
            "issues": []
        }
        
        # Example business rules (customize based on your needs)
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                # Check for negative values in numeric columns
                neg_count = (df[col] < 0).sum()
                business_rules["rules"][f"{col}_non_negative"] = {
                    "check": "non_negative",
                    "violations": neg_count,
                    "is_valid": neg_count == 0
                }
                
                if neg_count > 0:
                    business_rules["issues"].append({
                        "type": "business_rule",
                        "column": col,
                        "message": f"Found {neg_count} negative values"
                    })
                    
            elif df[col].dtype == 'object':
                # Check for empty strings
                empty_count = (df[col].str.strip() == "").sum()
                business_rules["rules"][f"{col}_non_empty"] = {
                    "check": "non_empty",
                    "violations": empty_count,
                    "is_valid": empty_count == 0
                }
                
                if empty_count > 0:
                    business_rules["issues"].append({
                        "type": "business_rule",
                        "column": col,
                        "message": f"Found {empty_count} empty strings"
                    })
        
        # Calculate business rules score
        rule_score = np.mean([
            rule["is_valid"]
            for rules in business_rules["rules"].values()
            for rule in [rules]
        ])
        
        business_rules["score"] = rule_score
        
        return business_rules
    
    def _get_expected_type(self, series: pd.Series) -> str:
        """Determine the expected data type for a series."""
        if series.dtype in ['int64', 'float64']:
            return str(series.dtype)
        elif series.dtype == 'object':
            # Try to convert to numeric
            try:
                pd.to_numeric(series)
                return 'float64'
            except:
                return 'object'
        else:
            return str(series.dtype) 