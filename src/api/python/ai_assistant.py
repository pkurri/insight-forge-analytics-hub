
"""
AI Assistant Module with Vector DB Integration

This module provides AI assistant capabilities with vector database integration
for answering questions about loaded datasets.

In a production environment, this would be deployed as an API endpoint or microservice.
"""

import pandas as pd
import numpy as np
import json
import os
import logging
from typing import Dict, List, Any, Union, Optional
from datetime import datetime

# Vector DB and embedding imports
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    logging.error("Required packages not installed. Please install sentence-transformers, faiss-cpu, transformers, and langchain.")
    raise

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIAssistant:
    """Class for providing AI assistant capabilities with vector DB"""
    
    def __init__(self):
        """Initialize the AI assistant"""
        self.embedding_model = None
        self.vector_index = None
        self.qa_model = None
        self.zero_shot_model = None
        self.dataset_info = {}
        self.document_chunks = []
        self.embeddings = None
        logger.info("AIAssistant initialized")
    
    def load_models(self):
        """Load required models"""
        try:
            # Load embedding model
            logger.info("Loading embedding model...")
            self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            
            # Load QA model
            logger.info("Loading QA model...")
            self.qa_model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")
            self.qa_tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
            
            # Load zero-shot classification model
            logger.info("Loading zero-shot classification model...")
            self.zero_shot_model = pipeline("zero-shot-classification", 
                                            model="facebook/bart-large-mnli")
            
            return {
                "success": True,
                "message": "Models loaded successfully"
            }
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _chunk_dataframe(self, df: pd.DataFrame, chunk_size: int = 100) -> List[str]:
        """
        Convert dataframe to text chunks for vector storage
        
        Args:
            df: Pandas DataFrame to process
            chunk_size: Number of rows per chunk
            
        Returns:
            List of text chunks
        """
        chunks = []
        total_rows = len(df)
        
        # Create a text description of the dataframe schema
        column_descriptions = []
        for col in df.columns:
            dtype = df[col].dtype
            sample_values = df[col].dropna().sample(min(3, len(df[col].dropna()))).tolist()
            sample_str = ", ".join([str(x) for x in sample_values])
            column_descriptions.append(f"- {col} ({dtype}): Example values: {sample_str}")
        
        schema_text = "Dataset Schema:\n" + "\n".join(column_descriptions)
        chunks.append(schema_text)
        
        # Create chunks of rows
        for i in range(0, total_rows, chunk_size):
            end_idx = min(i + chunk_size, total_rows)
            chunk_df = df.iloc[i:end_idx]
            
            # Convert chunk to text
            chunk_text = f"Rows {i} to {end_idx-1}:\n"
            chunk_text += chunk_df.to_string()
            chunks.append(chunk_text)
        
        # Create summary statistics
        stats_text = "Dataset Statistics:\n"
        
        # Numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            stats_text += "Numeric columns summary statistics:\n"
            stats_text += df[numeric_cols].describe().to_string()
            
        # Categorical columns
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(cat_cols) > 0:
            stats_text += "\n\nCategorical columns summary:\n"
            for col in cat_cols:
                stats_text += f"\n{col} value counts:\n"
                stats_text += df[col].value_counts().head(5).to_string()
        
        chunks.append(stats_text)
        
        return chunks
    
    def load_dataset(self, df: pd.DataFrame, dataset_id: str, dataset_name: str) -> Dict[str, Any]:
        """
        Load a dataset into the assistant's vector database
        
        Args:
            df: Pandas DataFrame to load
            dataset_id: Unique identifier for the dataset
            dataset_name: Human-readable name for the dataset
            
        Returns:
            Dict with load status and info
        """
        try:
            logger.info(f"Loading dataset {dataset_name} (ID: {dataset_id})")
            
            # Store dataset info
            self.dataset_info = {
                "id": dataset_id,
                "name": dataset_name,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "loaded_at": datetime.now().isoformat()
            }
            
            # Chunk the dataframe into text segments
            chunks = self._chunk_dataframe(df)
            self.document_chunks = chunks
            
            # Create text splitter for further processing if needed
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            
            # Further split large chunks if needed
            processed_chunks = []
            for chunk in chunks:
                if len(chunk) > 1000:
                    sub_chunks = text_splitter.split_text(chunk)
                    processed_chunks.extend(sub_chunks)
                else:
                    processed_chunks.append(chunk)
            
            # Generate embeddings
            if self.embedding_model is None:
                self.load_models()
                
            embeddings = self.embedding_model.encode(processed_chunks)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.vector_index = faiss.IndexFlatL2(dimension)
            self.vector_index.add(embeddings)
            self.embeddings = embeddings
            self.document_chunks = processed_chunks
            
            return {
                "success": True,
                "message": f"Dataset {dataset_name} loaded successfully",
                "chunks": len(processed_chunks),
                "vector_dimension": dimension
            }
            
        except Exception as e:
            logger.error(f"Error loading dataset: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def suggest_business_rules(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Use Hugging Face models to suggest business rules based on data patterns
        
        Args:
            df: Pandas DataFrame to analyze
            
        Returns:
            Dict with generated business rules suggestions
        """
        try:
            if self.zero_shot_model is None:
                self.load_models()
                
            rules = []
            rule_id = 1
            
            # Analyze each column
            for column in df.columns:
                column_data = df[column]
                dtype = column_data.dtype
                column_name = str(column)
                
                # Define potential rule types based on data type
                if pd.api.types.is_numeric_dtype(dtype):
                    rule_types = ["range validation", "outlier detection", "non-negative check"]
                    
                    # Range validation
                    min_val = column_data.min()
                    max_val = column_data.max()
                    rules.append({
                        "id": f"R{rule_id}",
                        "name": f"{column_name} Range Check",
                        "condition": f"data['{column_name}'] >= {min_val} and data['{column_name}'] <= {max_val}",
                        "severity": "high",
                        "message": f"{column_name} must be between {min_val} and {max_val}",
                        "confidence": 0.95,
                        "model_generated": True
                    })
                    rule_id += 1
                    
                    # Check if column likely needs to be non-negative
                    if min_val >= 0 and column_name.lower() in ['price', 'quantity', 'amount', 'count', 'age']:
                        rules.append({
                            "id": f"R{rule_id}",
                            "name": f"{column_name} Non-Negative Check",
                            "condition": f"data['{column_name}'] >= 0",
                            "severity": "high",
                            "message": f"{column_name} must be non-negative",
                            "confidence": 0.9,
                            "model_generated": True
                        })
                        rule_id += 1
                
                elif pd.api.types.is_string_dtype(dtype):
                    # Check for email pattern
                    if column_name.lower() in ['email', 'e-mail', 'email_address']:
                        rules.append({
                            "id": f"R{rule_id}",
                            "name": f"{column_name} Email Format",
                            "condition": f"re.match(r'^[\\w.-]+@[\\w.-]+\\.[a-zA-Z]{{2,}}$', str(data['{column_name}']))",
                            "severity": "high", 
                            "message": f"{column_name} must be a valid email format",
                            "confidence": 0.85,
                            "model_generated": True
                        })
                        rule_id += 1
                    
                    # Check for categorical data
                    unique_values = column_data.nunique()
                    if unique_values <= 10:  # Likely a categorical column
                        values = column_data.dropna().unique().tolist()
                        values_str = ", ".join([f"'{str(v)}'" for v in values])
                        rules.append({
                            "id": f"R{rule_id}",
                            "name": f"{column_name} Valid Values",
                            "condition": f"str(data['{column_name}']) in [{values_str}]",
                            "severity": "medium",
                            "message": f"{column_name} must be one of the allowed values",
                            "confidence": 0.8,
                            "model_generated": True
                        })
                        rule_id += 1
                        
                # Use zero-shot classification to identify type of column
                if len(column_data.dropna()) > 0:
                    sample_values = [str(x) for x in column_data.dropna().sample(min(5, len(column_data.dropna()))).tolist()]
                    sample_text = f"Column name: {column_name}. Sample values: {', '.join(sample_values)}"
                    
                    column_types = [
                        "personal identifier", "date", "monetary value", "geographic location",
                        "percentage", "scientific measurement", "product identifier", "age"
                    ]
                    
                    classification = self.zero_shot_model(sample_text, column_types)
                    top_label = classification['labels'][0]
                    confidence = classification['scores'][0]
                    
                    # Generate rules based on column type prediction
                    if top_label == "personal identifier" and confidence > 0.7:
                        rules.append({
                            "id": f"R{rule_id}",
                            "name": f"{column_name} Personal ID Format",
                            "condition": f"len(str(data['{column_name}'])) >= 4",
                            "severity": "high",
                            "message": f"{column_name} must be a valid identifier",
                            "confidence": confidence,
                            "model_generated": True
                        })
                        rule_id += 1
                    
                    elif top_label == "date" and confidence > 0.7:
                        rules.append({
                            "id": f"R{rule_id}",
                            "name": f"{column_name} Date Range",
                            "condition": f"pd.to_datetime(data['{column_name}']) <= pd.Timestamp.now()",
                            "severity": "medium",
                            "message": f"{column_name} cannot be in the future",
                            "confidence": confidence,
                            "model_generated": True
                        })
                        rule_id += 1
            
            return {
                "success": True,
                "rules_generated": len(rules),
                "rules": rules,
                "model_info": "Generated using Hugging Face zero-shot classification"
            }
            
        except Exception as e:
            logger.error(f"Error generating business rules: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def answer_question(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Answer questions about the loaded dataset using vector search and LLM
        
        Args:
            question: Question to answer
            top_k: Number of relevant chunks to retrieve
            
        Returns:
            Dict with answer and relevant context
        """
        try:
            if not self.vector_index:
                return {
                    "success": False,
                    "error": "No dataset loaded. Please load a dataset first."
                }
                
            if self.embedding_model is None or self.qa_model is None:
                self.load_models()
            
            # Embed the question
            question_embedding = self.embedding_model.encode([question])
            
            # Search for relevant chunks
            distances, indices = self.vector_index.search(question_embedding, top_k)
            
            # Retrieve relevant chunks
            relevant_chunks = [self.document_chunks[i] for i in indices[0]]
            
            # Prepare context for QA model
            context = "\n\n".join(relevant_chunks)
            
            # Ask QA model
            inputs = self.qa_tokenizer(
                f"Answer the following question based on this context: {context}\n\nQuestion: {question}", 
                return_tensors="pt", 
                max_length=1024, 
                truncation=True
            )
            
            # Generate answer
            output = self.qa_model.generate(
                inputs["input_ids"],
                max_length=150,
                num_beams=4,
                early_stopping=True
            )
            
            answer = self.qa_tokenizer.decode(output[0], skip_special_tokens=True)
            
            return {
                "success": True,
                "question": question,
                "answer": answer,
                "dataset": self.dataset_info.get("name", "Unknown"),
                "relevant_context_count": len(relevant_chunks),
                "confidence": 1.0 - float(distances[0][0]) / 10.0  # Rough confidence estimate
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Example usage (would be called via API endpoint in production)
if __name__ == "__main__":
    # Create sample data
    data = pd.DataFrame({
        'customer_id': ['C001', 'C002', 'C003', 'C004'],
        'name': ['Alice Smith', 'Bob Johnson', 'Charlie Brown', 'Diana Miller'],
        'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com', 'diana@example.com'],
        'age': [32, 45, 22, 38],
        'purchase_amount': [125.50, 89.99, 245.00, 55.25],
        'purchase_date': ['2023-01-15', '2023-01-22', '2023-02-05', '2023-02-10']
    })
    
    # Initialize AI assistant
    assistant = AIAssistant()
    assistant.load_models()
    
    # Load dataset
    assistant.load_dataset(data, "sample-001", "Customer Orders")
    
    # Generate business rules
    rules = assistant.suggest_business_rules(data)
    print(f"Generated {rules['rules_generated']} rules")
    
    # Answer a question
    answer = assistant.answer_question("What's the average purchase amount?")
    print(f"Q: What's the average purchase amount?")
    print(f"A: {answer['answer']}")
