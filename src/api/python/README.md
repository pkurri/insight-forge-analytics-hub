
# Python Modules for DataForge

This directory contains Python modules that would typically run as microservices or serverless functions to support the DataForge application. In a production deployment, these would be separate services that the frontend communicates with through REST APIs.

## Modules

### Data Profiling Module
Uses ydata-profiling (formerly pandas-profiling) to generate comprehensive data profiles from datasets.

### Anomaly Detection
Uses statistical methods and machine learning to detect anomalies in datasets.

### Schema Validation
Uses Pydantic for schema validation and enforcement.

### Business Rules Engine
Provides capabilities for defining, managing, and enforcing business rules on data.

### AI Assistant with Vector DB
Uses Hugging Face models and vector database for enhanced Q&A capabilities on loaded datasets.

## Installation

The Python backend would typically require:

```bash
pip install fastapi uvicorn pandas numpy ydata-profiling pydantic scikit-learn sentence-transformers langchain faiss-cpu transformers great-expectations huggingface_hub
```

## Deployment

In a production setup, these modules would be deployed as:
- Docker containers
- Cloud Functions (AWS Lambda, Google Cloud Functions)
- Kubernetes pods

## AI Models

The system leverages several Hugging Face models:
- `sentence-transformers/all-MiniLM-L6-v2` for text embeddings
- `facebook/bart-large-mnli` for zero-shot classification
- `google/flan-t5-base` for rule generation
