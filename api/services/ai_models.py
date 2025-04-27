import pandas as pd
from typing import Dict, Any, List
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

class AIModelService:
    def __init__(self):
        # Initialize models
        self.text_cleaner = pipeline("text-classification", model="cleanlab/cleantext-small")
        self.data_validator = pipeline("text-classification", model="facebook/bart-large-mnli")
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()

    async def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean data using AI models for text and numerical data."""
        cleaned_df = df.copy()

        for column in df.columns:
            if df[column].dtype == 'object':  # Text data
                # Clean text data using the model
                cleaned_values = []
                for text in df[column].fillna(''):
                    result = self.text_cleaner(str(text))[0]
                    cleaned_text = result['label'] if result['score'] > 0.8 else text
                    cleaned_values.append(cleaned_text)
                cleaned_df[column] = cleaned_values
            else:  # Numerical data
                # Handle missing values and outliers
                cleaned_df[column] = cleaned_df[column].fillna(cleaned_df[column].median())

        return cleaned_df

    async def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate data using AI models."""
        validation_results = {
            'column_validations': {},
            'overall_quality_score': 0.0,
            'issues_detected': []
        }

        for column in df.columns:
            column_stats = {
                'valid_entries': 0,
                'invalid_entries': 0,
                'confidence_score': 0.0
            }

            if df[column].dtype == 'object':
                # Validate text data using NLI model
                for text in df[column].fillna(''):
                    result = self.data_validator(
                        f"This is valid data: {text}",
                        candidate_labels=["valid", "invalid"]
                    )[0]
                    
                    if result['labels'][0] == 'valid' and result['scores'][0] > 0.7:
                        column_stats['valid_entries'] += 1
                    else:
                        column_stats['invalid_entries'] += 1
                        validation_results['issues_detected'].append({
                            'column': column,
                            'value': text,
                            'issue': 'Potentially invalid data'
                        })

            else:  # Numerical data
                # Basic statistical validation
                z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
                column_stats['valid_entries'] = (z_scores <= 3).sum()
                column_stats['invalid_entries'] = (z_scores > 3).sum()

            total_entries = column_stats['valid_entries'] + column_stats['invalid_entries']
            column_stats['confidence_score'] = column_stats['valid_entries'] / total_entries
            validation_results['column_validations'][column] = column_stats

        # Calculate overall quality score
        validation_results['overall_quality_score'] = np.mean([
            stats['confidence_score'] 
            for stats in validation_results['column_validations'].values()
        ])

        return validation_results

    async def analyze_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate analytics insights using AI models."""
        analytics_results = {
            'column_profiles': {},
            'correlations': {},
            'key_insights': []
        }

        # Generate column profiles
        for column in df.columns:
            if df[column].dtype == 'object':
                # Generate embeddings for text data
                embeddings = self.sentence_model.encode(df[column].fillna('').astype(str).tolist())
                analytics_results['column_profiles'][column] = {
                    'data_type': 'text',
                    'unique_values': df[column].nunique(),
                    'semantic_clusters': self._cluster_embeddings(embeddings)
                }
            else:
                analytics_results['column_profiles'][column] = {
                    'data_type': 'numerical',
                    'mean': df[column].mean(),
                    'median': df[column].median(),
                    'std': df[column].std(),
                    'distribution': self._analyze_distribution(df[column])
                }

        # Calculate correlations for numerical columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            analytics_results['correlations'] = corr_matrix.to_dict()

        return analytics_results

    async def detect_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalies in the dataset using AI models."""
        anomaly_results = {
            'anomalies': [],
            'anomaly_scores': {},
            'summary': {}
        }

        # Prepare numerical data for anomaly detection
        numeric_data = df.select_dtypes(include=[np.number])
        if not numeric_data.empty:
            scaled_data = self.scaler.fit_transform(numeric_data)
            anomaly_scores = self.anomaly_detector.fit_predict(scaled_data)
            
            # Record anomalies
            anomaly_indices = np.where(anomaly_scores == -1)[0]
            for idx in anomaly_indices:
                anomaly_results['anomalies'].append({
                    'row_index': idx,
                    'values': df.iloc[idx].to_dict(),
                    'anomaly_type': 'statistical_outlier'
                })

            # Calculate anomaly scores for each column
            for col in numeric_data.columns:
                col_scores = self.anomaly_detector.score_samples(
                    scaled_data[:, numeric_data.columns.get_loc(col)].reshape(-1, 1)
                )
                anomaly_results['anomaly_scores'][col] = col_scores.tolist()

        # Text anomaly detection using embeddings
        text_cols = df.select_dtypes(include=['object']).columns
        for col in text_cols:
            embeddings = self.sentence_model.encode(df[col].fillna('').astype(str).tolist())
            text_anomaly_scores = self.anomaly_detector.fit_predict(embeddings)
            text_anomaly_indices = np.where(text_anomaly_scores == -1)[0]
            
            for idx in text_anomaly_indices:
                anomaly_results['anomalies'].append({
                    'row_index': idx,
                    'column': col,
                    'value': df[col].iloc[idx],
                    'anomaly_type': 'semantic_outlier'
                })

        # Generate summary
        anomaly_results['summary'] = {
            'total_anomalies': len(anomaly_results['anomalies']),
            'anomaly_percentage': len(anomaly_results['anomalies']) / len(df) * 100,
            'affected_columns': list(set([a.get('column') for a in anomaly_results['anomalies']]))
        }

        return anomaly_results

    def _cluster_embeddings(self, embeddings: np.ndarray, n_clusters: int = 3) -> List[Dict[str, Any]]:
        """Helper method to cluster embeddings."""
        from sklearn.cluster import KMeans
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(embeddings)
        
        return [{
            'cluster_id': int(i),
            'size': int((clusters == i).sum()),
            'center': kmeans.cluster_centers_[i].tolist()
        } for i in range(n_clusters)]

    def _analyze_distribution(self, series: pd.Series) -> Dict[str, Any]:
        """Helper method to analyze numerical distributions."""
        return {
            'skewness': float(series.skew()),
            'kurtosis': float(series.kurtosis()),
            'quartiles': series.quantile([0.25, 0.5, 0.75]).to_dict()
        }
