
"""
Anomaly Detection Module

This module provides functionality for detecting anomalies in datasets
using statistical methods and machine learning techniques including
isolation forests, autoencoders, and vector database comparison.

In a production environment, this would be deployed as an API endpoint or microservice.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from typing import Dict, List, Any, Union, Optional
import logging
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing deep learning libraries for autoencoders
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    logger.warning("PyTorch not available. Autoencoder-based detection will be disabled.")
    TORCH_AVAILABLE = False

# Try importing vector DB libraries
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    VECTOR_DB_AVAILABLE = True
except ImportError:
    logger.warning("FAISS or sentence-transformers not available. Vector DB comparison will be disabled.")
    VECTOR_DB_AVAILABLE = False

class Autoencoder(nn.Module):
    """Autoencoder neural network for anomaly detection"""
    def __init__(self, input_dim, encoding_dim=10):
        super(Autoencoder, self).__init__()
        
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, encoding_dim),
            nn.ReLU()
        )
        
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Linear(128, input_dim),
            nn.Sigmoid()  # Output in [0,1]
        )
        
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

class AnomalyDetector:
    """Class for detecting anomalies in datasets"""
    
    def __init__(self, method: str = "isolation_forest", params: Optional[Dict[str, Any]] = None):
        """
        Initialize the anomaly detector
        
        Args:
            method: The anomaly detection method to use
                ("isolation_forest", "lof", "z_score", "iqr", "autoencoder", "vector_comparison")
            params: Parameters specific to the detection method
        """
        self.method = method
        self.params = params or {}
        self.model = None
        self.vector_index = None
        self.embedding_model = None
        logger.info(f"AnomalyDetector initialized with method: {method}")
    
    def fit(self, data: pd.DataFrame, columns: Optional[List[str]] = None):
        """
        Fit the anomaly detection model to the data
        
        Args:
            data: Pandas DataFrame containing the dataset
            columns: List of column names to use for fitting
                     (if None, all numeric columns are used)
        """
        # Select columns for analysis
        if columns is None:
            # Select only numeric columns
            numeric_columns = data.select_dtypes(include=np.number).columns.tolist()
            analysis_data = data[numeric_columns]
            logger.info(f"Auto-selected {len(numeric_columns)} numeric columns for fitting")
        else:
            analysis_data = data[columns]
            logger.info(f"Using {len(columns)} specified columns for fitting")
        
        # Fill missing values for algorithm processing
        analysis_data = analysis_data.fillna(analysis_data.mean())
        
        # Fit the appropriate model
        if self.method == "isolation_forest":
            n_estimators = self.params.get('n_estimators', 100)
            contamination = self.params.get('contamination', 'auto')
            random_state = self.params.get('random_state', 42)
            
            self.model = IsolationForest(
                n_estimators=n_estimators,
                contamination=contamination,
                random_state=random_state
            )
            self.model.fit(analysis_data)
            logger.info("Isolation forest model fitted")
            
        elif self.method == "autoencoder" and TORCH_AVAILABLE:
            self._fit_autoencoder(analysis_data)
            logger.info("Autoencoder model fitted")
            
        elif self.method == "vector_comparison" and VECTOR_DB_AVAILABLE:
            self._fit_vector_db(analysis_data)
            logger.info("Vector database created for comparison")
            
        return self
    
    def _fit_autoencoder(self, data: pd.DataFrame):
        """Fit an autoencoder model to the data"""
        # Normalize data to [0,1]
        min_vals = data.min()
        max_vals = data.max()
        normalized_data = (data - min_vals) / (max_vals - min_vals)
        
        # Convert to PyTorch tensors
        X_tensor = torch.FloatTensor(normalized_data.values)
        
        # Get parameters
        batch_size = self.params.get('batch_size', 64)
        epochs = self.params.get('epochs', 50)
        learning_rate = self.params.get('learning_rate', 0.001)
        encoding_dim = self.params.get('encoding_dim', 10)
        
        # Create data loader
        dataset = TensorDataset(X_tensor, X_tensor)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # Create and train the autoencoder
        input_dim = data.shape[1]
        self.model = Autoencoder(input_dim, encoding_dim)
        self.scaler = {"min": min_vals, "max": max_vals}
        
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()
        
        # Training loop
        self.model.train()
        for epoch in range(epochs):
            total_loss = 0
            for batch_X, batch_y in dataloader:
                # Forward pass
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_X)
                
                # Backward pass and optimize
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            avg_loss = total_loss / len(dataloader)
            if epoch % 10 == 0:
                logger.debug(f"Epoch {epoch}: Avg Loss = {avg_loss:.6f}")
        
        # Switch to evaluation mode
        self.model.eval()
        
        # Compute reconstruction error distribution for thresholding
        with torch.no_grad():
            reconstructions = self.model(X_tensor)
            mse = torch.mean(torch.pow(X_tensor - reconstructions, 2), dim=1)
            self.threshold = torch.quantile(mse, 0.95).item()  # 95th percentile as anomaly threshold
        
        logger.info(f"Autoencoder trained. Anomaly threshold set to {self.threshold:.6f}")
    
    def _fit_vector_db(self, data: pd.DataFrame):
        """Fit a vector database for data comparison"""
        # Load embedding model
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # Convert dataframe to text for embedding
        text_representations = []
        for _, row in data.iterrows():
            text_repr = " ".join([f"{col}: {val}" for col, val in row.items()])
            text_representations.append(text_repr)
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(text_representations)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.vector_index = faiss.IndexFlatL2(dimension)
        self.vector_index.add(embeddings)
        
        # Store reference data statistics
        self.ref_data_stats = {
            "mean": data.mean().to_dict(),
            "std": data.std().to_dict(),
            "min": data.min().to_dict(),
            "max": data.max().to_dict(),
            "count": len(data)
        }
        
        logger.info(f"Vector database created with {len(data)} entries")
        
    def detect(self, data: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Detect anomalies in the dataset
        
        Args:
            data: Pandas DataFrame containing the dataset
            columns: List of column names to check for anomalies 
                     (if None, all numeric columns are used)
                     
        Returns:
            Dictionary with anomaly detection results
        """
        # Select columns for analysis
        if columns is None:
            # Select only numeric columns
            numeric_columns = data.select_dtypes(include=np.number).columns.tolist()
            analysis_data = data[numeric_columns]
            logger.info(f"Auto-selected {len(numeric_columns)} numeric columns for analysis")
        else:
            analysis_data = data[columns]
            logger.info(f"Using {len(columns)} specified columns for analysis")
        
        # Fill missing values for algorithm processing
        analysis_data = analysis_data.fillna(analysis_data.mean())
        
        # Run the appropriate detection method
        if self.method == "isolation_forest":
            return self._isolation_forest(analysis_data, data)
        elif self.method == "lof":
            return self._local_outlier_factor(analysis_data, data)
        elif self.method == "z_score":
            return self._z_score(analysis_data, data)
        elif self.method == "iqr":
            return self._iqr_method(analysis_data, data)
        elif self.method == "autoencoder" and TORCH_AVAILABLE and self.model is not None:
            return self._autoencoder_detect(analysis_data, data)
        elif self.method == "vector_comparison" and VECTOR_DB_AVAILABLE and self.vector_index is not None:
            return self._vector_db_detect(analysis_data, data)
        else:
            error_msg = f"Unknown or unavailable method: {self.method}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def _isolation_forest(self, analysis_data: pd.DataFrame, 
                         original_data: pd.DataFrame) -> Dict[str, Any]:
        """Use Isolation Forest algorithm to detect anomalies"""
        # ... keep existing code (isolation forest implementation)
    
    def _local_outlier_factor(self, analysis_data: pd.DataFrame, 
                             original_data: pd.DataFrame) -> Dict[str, Any]:
        """Use Local Outlier Factor algorithm to detect anomalies"""
        # ... keep existing code (LOF implementation)
    
    def _z_score(self, analysis_data: pd.DataFrame, 
                original_data: pd.DataFrame) -> Dict[str, Any]:
        """Use Z-score method to detect anomalies"""
        # ... keep existing code (Z-score implementation)
    
    def _iqr_method(self, analysis_data: pd.DataFrame, 
                   original_data: pd.DataFrame) -> Dict[str, Any]:
        """Use IQR (Interquartile Range) method to detect anomalies"""
        # ... keep existing code (IQR method implementation)
    
    def _autoencoder_detect(self, analysis_data: pd.DataFrame, 
                           original_data: pd.DataFrame) -> Dict[str, Any]:
        """Use trained autoencoder to detect anomalies"""
        try:
            # Normalize data using the same scaler as during training
            min_vals = self.scaler["min"]
            max_vals = self.scaler["max"]
            
            normalized_data = analysis_data.copy()
            for col in normalized_data.columns:
                if col in min_vals and col in max_vals:
                    normalized_data[col] = (normalized_data[col] - min_vals[col]) / (max_vals[col] - min_vals[col])
            
            # Convert to tensor
            X_tensor = torch.FloatTensor(normalized_data.values)
            
            # Get reconstructions and compute errors
            with torch.no_grad():
                reconstructions = self.model(X_tensor)
                mse = torch.mean(torch.pow(X_tensor - reconstructions, 2), dim=1).numpy()
            
            # Find anomalies using the threshold
            anomaly_indices = np.where(mse > self.threshold)[0]
            
            return self._format_results(original_data, anomaly_indices, mse, 
                                      analysis_data.columns.tolist(),
                                      method_details={
                                          "reconstruction_errors": mse.tolist(),
                                          "threshold": self.threshold
                                      })
            
        except Exception as e:
            logger.error(f"Error in autoencoder detection: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _vector_db_detect(self, analysis_data: pd.DataFrame, 
                         original_data: pd.DataFrame) -> Dict[str, Any]:
        """Use vector database comparison to detect anomalies"""
        try:
            # Convert new data to text representations
            text_representations = []
            for _, row in analysis_data.iterrows():
                text_repr = " ".join([f"{col}: {val}" for col, val in row.items()])
                text_representations.append(text_repr)
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(text_representations)
            
            # Search for nearest neighbors
            k = min(5, self.vector_index.ntotal)  # Number of neighbors to retrieve
            distances, _ = self.vector_index.search(embeddings, k)
            
            # Average distance to k nearest neighbors as anomaly score
            anomaly_scores = np.mean(distances, axis=1)
            
            # Use quartiles to determine threshold
            q3 = np.quantile(anomaly_scores, 0.75)
            iqr = np.quantile(anomaly_scores, 0.75) - np.quantile(anomaly_scores, 0.25)
            threshold = q3 + 1.5 * iqr
            
            # Find anomalies
            anomaly_indices = np.where(anomaly_scores > threshold)[0]
            
            # Also check for statistical deviations from reference data
            stat_anomalies = set()
            for idx, row in analysis_data.iterrows():
                for col in row.index:
                    if col in self.ref_data_stats["mean"] and col in self.ref_data_stats["std"]:
                        mean = self.ref_data_stats["mean"][col]
                        std = max(self.ref_data_stats["std"][col], 1e-5)  # Avoid division by zero
                        z_score = abs((row[col] - mean) / std)
                        if z_score > 3:  # More than 3 standard deviations
                            stat_anomalies.add(idx)
            
            # Combine vector-based and statistical anomalies
            combined_anomalies = set(anomaly_indices) | stat_anomalies
            anomaly_indices = np.array(list(combined_anomalies))
            
            return self._format_results(original_data, anomaly_indices, anomaly_scores, 
                                      analysis_data.columns.tolist(),
                                      method_details={
                                          "vector_distances": distances.tolist(),
                                          "threshold": threshold,
                                          "reference_data_size": self.vector_index.ntotal
                                      })
            
        except Exception as e:
            logger.error(f"Error in vector DB comparison: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _format_results(self, original_data: pd.DataFrame, 
                       anomaly_indices: np.ndarray,
                       anomaly_scores: np.ndarray,
                       analyzed_columns: List[str],
                       method_details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Format the results of anomaly detection"""
        try:
            # Extract anomaly data
            total_rows = len(original_data)
            anomaly_count = len(anomaly_indices)
            
            # Create detailed anomaly information
            anomalies = []
            for idx in anomaly_indices:
                if idx < len(original_data):  # Ensure index is valid
                    anomaly_record = {
                        "index": int(idx),
                        "score": float(anomaly_scores[idx]),
                        "values": {}
                    }
                    
                    # Add values for analyzed columns
                    for col in analyzed_columns:
                        try:
                            val = original_data.iloc[idx][col]
                            # Convert numpy types to Python native types
                            if isinstance(val, (np.integer, np.floating)):
                                val = val.item()
                            anomaly_record["values"][col] = val
                        except:
                            anomaly_record["values"][col] = None
                    
                    anomalies.append(anomaly_record)
            
            # Sort anomalies by score (highest first)
            anomalies = sorted(anomalies, key=lambda x: x["score"], reverse=True)
            
            result = {
                "success": True,
                "summary": {
                    "total_rows": total_rows,
                    "anomaly_count": anomaly_count,
                    "anomaly_percentage": (anomaly_count / total_rows * 100) if total_rows > 0 else 0,
                    "analyzed_columns": analyzed_columns,
                    "detection_method": self.method,
                    "detection_time": datetime.now().isoformat()
                },
                "anomalies": anomalies[:100],  # Limit to top 100 anomalies
                "method_specific": method_details if method_details else {}
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error formatting results: {str(e)}")
            return {"success": False, "error": str(e)}

# Example usage (would be called via API endpoint in production)
if __name__ == "__main__":
    import json
    
    # Create sample data with outliers
    np.random.seed(42)
    normal_data = np.random.normal(0, 1, (1000, 4))
    
    # Add some outliers
    outliers = np.random.uniform(10, 20, (20, 4))
    combined_data = np.vstack([normal_data, outliers])
    
    # Create DataFrame
    df = pd.DataFrame(
        combined_data, 
        columns=["feature1", "feature2", "feature3", "feature4"]
    )
    
    # Example 1: Isolation Forest
    detector1 = AnomalyDetector(method="isolation_forest")
    results1 = detector1.detect(df)
    
    # Example 2: Autoencoder (if PyTorch is available)
    if TORCH_AVAILABLE:
        detector2 = AnomalyDetector(method="autoencoder", params={"epochs": 20})
        detector2.fit(df[:800])  # Train on first 800 rows
        results2 = detector2.detect(df[800:])  # Test on last 200 rows
    
    # Example 3: Vector comparison (if FAISS is available)
    if VECTOR_DB_AVAILABLE:
        detector3 = AnomalyDetector(method="vector_comparison")
        detector3.fit(df[:800])  # Reference data
        results3 = detector3.detect(df[800:])  # New data to check
