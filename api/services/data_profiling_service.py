import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from models.dataset import PipelineRunStatus

class DataProfilingService:
    """Service for data profiling operations."""
    
    async def profile_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate a comprehensive data profile."""
        profile = {
            "overview": await self._get_overview(df),
            "columns": await self._profile_columns(df),
            "correlations": await self._get_correlations(df),
            "patterns": await self._detect_patterns(df)
        }
        
        return profile
    
    async def _get_overview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get an overview of the dataset."""
        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "memory_usage": df.memory_usage(deep=True).sum(),
            "duplicate_rows": len(df) - len(df.drop_duplicates()),
            "missing_values": df.isnull().sum().sum(),
            "missing_percentage": (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        }
    
    async def _profile_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Profile each column in the dataset."""
        column_profiles = {}
        
        for col in df.columns:
            profile = {
                "type": str(df[col].dtype),
                "missing_values": df[col].isnull().sum(),
                "missing_percentage": (df[col].isnull().sum() / len(df)) * 100,
                "unique_values": df[col].nunique(),
                "unique_percentage": (df[col].nunique() / len(df)) * 100
            }
            
            if df[col].dtype in ['int64', 'float64']:
                profile.update({
                    "min": df[col].min(),
                    "max": df[col].max(),
                    "mean": df[col].mean(),
                    "median": df[col].median(),
                    "std": df[col].std(),
                    "skew": df[col].skew(),
                    "kurtosis": df[col].kurtosis(),
                    "zeros": (df[col] == 0).sum(),
                    "negatives": (df[col] < 0).sum()
                })
                
                # Add quartiles
                q1, q2, q3 = df[col].quantile([0.25, 0.5, 0.75])
                profile.update({
                    "q1": q1,
                    "q2": q2,
                    "q3": q3,
                    "iqr": q3 - q1
                })
                
            elif df[col].dtype == 'object':
                profile.update({
                    "most_common": df[col].mode().iloc[0],
                    "most_common_count": df[col].value_counts().iloc[0],
                    "most_common_percentage": (df[col].value_counts().iloc[0] / len(df)) * 100,
                    "empty_strings": (df[col].str.strip() == "").sum(),
                    "whitespace": (df[col].str.strip() != df[col]).sum(),
                    "avg_length": df[col].str.len().mean()
                })
                
                # Add value distribution
                value_counts = df[col].value_counts()
                profile["value_distribution"] = {
                    "top_5": value_counts.head(5).to_dict(),
                    "bottom_5": value_counts.tail(5).to_dict()
                }
            
            column_profiles[col] = profile
            
        return column_profiles
    
    async def _get_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate correlations between numeric columns."""
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        
        if len(numeric_cols) < 2:
            return {"message": "Not enough numeric columns for correlation analysis"}
            
        # Calculate Pearson correlation
        pearson_corr = df[numeric_cols].corr(method='pearson')
        
        # Calculate Spearman correlation
        spearman_corr = df[numeric_cols].corr(method='spearman')
        
        # Find highly correlated pairs
        high_corr_pairs = []
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                col1, col2 = numeric_cols[i], numeric_cols[j]
                pearson = pearson_corr.loc[col1, col2]
                spearman = spearman_corr.loc[col1, col2]
                
                if abs(pearson) > 0.7 or abs(spearman) > 0.7:
                    high_corr_pairs.append({
                        "columns": [col1, col2],
                        "pearson": pearson,
                        "spearman": spearman
                    })
        
        return {
            "pearson": pearson_corr.to_dict(),
            "spearman": spearman_corr.to_dict(),
            "high_correlations": high_corr_pairs
        }
    
    async def _detect_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect patterns in the data."""
        patterns = {
            "numeric_patterns": {},
            "categorical_patterns": {},
            "temporal_patterns": {}
        }
        
        # Detect numeric patterns
        for col in df.select_dtypes(include=['int64', 'float64']).columns:
            numeric_patterns = {}
            
            # Check for uniform distribution
            hist, _ = np.histogram(df[col].dropna(), bins=10)
            uniformity = np.std(hist) / np.mean(hist)
            numeric_patterns["uniformity"] = {
                "score": 1 - min(uniformity, 1),
                "is_uniform": uniformity < 0.5
            }
            
            # Check for normal distribution
            skew = df[col].skew()
            kurtosis = df[col].kurtosis()
            numeric_patterns["normality"] = {
                "skew": skew,
                "kurtosis": kurtosis,
                "is_normal": abs(skew) < 0.5 and abs(kurtosis) < 0.5
            }
            
            patterns["numeric_patterns"][col] = numeric_patterns
        
        # Detect categorical patterns
        for col in df.select_dtypes(include=['object']).columns:
            categorical_patterns = {}
            
            # Check for cardinality
            unique_ratio = df[col].nunique() / len(df)
            categorical_patterns["cardinality"] = {
                "unique_ratio": unique_ratio,
                "is_high_cardinality": unique_ratio > 0.5
            }
            
            # Check for value distribution
            value_counts = df[col].value_counts(normalize=True)
            entropy = -np.sum(value_counts * np.log2(value_counts))
            categorical_patterns["distribution"] = {
                "entropy": entropy,
                "max_entropy": np.log2(len(value_counts)),
                "is_balanced": entropy > np.log2(len(value_counts)) * 0.8
            }
            
            patterns["categorical_patterns"][col] = categorical_patterns
        
        # Detect temporal patterns
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    # Try to convert to datetime
                    pd.to_datetime(df[col])
                    temporal_patterns = {}
                    
                    # Check for gaps
                    dates = pd.to_datetime(df[col])
                    date_diff = dates.diff()
                    temporal_patterns["gaps"] = {
                        "min_gap": date_diff.min(),
                        "max_gap": date_diff.max(),
                        "avg_gap": date_diff.mean(),
                        "has_gaps": date_diff.std() > date_diff.mean()
                    }
                    
                    # Check for seasonality
                    if len(dates) > 365:
                        monthly_counts = dates.dt.month.value_counts()
                        seasonality = monthly_counts.std() / monthly_counts.mean()
                        temporal_patterns["seasonality"] = {
                            "score": seasonality,
                            "has_seasonality": seasonality > 0.5
                        }
                    
                    patterns["temporal_patterns"][col] = temporal_patterns
                except:
                    continue
        
        return patterns 