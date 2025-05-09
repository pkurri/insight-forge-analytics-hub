import os
import json
import logging
import pickle
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

import numpy as np
from fastapi import HTTPException
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory vector database (for demo purposes)
# In production, use a proper vector database like Pinecone, Weaviate, etc.
vector_db = {}

# Vector database file path
VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'vector_db.pkl')

# Ensure data directory exists
os.makedirs(os.path.dirname(VECTOR_DB_PATH), exist_ok=True)

def get_vector_db():
    """
    Get the vector database, loading from disk if available
    """
    global vector_db
    
    # Load from disk if empty and file exists
    if not vector_db and os.path.exists(VECTOR_DB_PATH):
        try:
            with open(VECTOR_DB_PATH, 'rb') as f:
                vector_db = pickle.load(f)
            logger.info(f"Loaded vector database from {VECTOR_DB_PATH} with {len(vector_db)} datasets")
        except Exception as e:
            logger.error(f"Error loading vector database: {str(e)}")
            # Initialize empty if loading fails
            vector_db = {}
    
    return vector_db

def save_vector_db():
    """
    Save the vector database to disk
    """
    try:
        with open(VECTOR_DB_PATH, 'wb') as f:
            pickle.dump(vector_db, f)
        logger.info(f"Saved vector database to {VECTOR_DB_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error saving vector database: {str(e)}")
        return False

async def add_vectors(dataset_id: str, vectors: List[Dict[str, Any]]):
    """
    Add vectors to the database for a specific dataset
    """
    # Initialize the vector database if needed
    db = get_vector_db()
    
    if dataset_id not in db:
        db[dataset_id] = []
    
    # Add timestamp to each vector
    for vector in vectors:
        if "metadata" not in vector:
            vector["metadata"] = {}
        
        vector["metadata"]["added_at"] = datetime.now().isoformat()
    
    db[dataset_id].extend(vectors)
    
    # Save to disk
    save_vector_db()
    
    return {"success": True, "count": len(vectors)}

async def search_similar_vectors(
    query_vector: Union[List[float], np.ndarray], 
    dataset_id: Optional[str] = None, 
    limit: int = 5,
    threshold: float = 0.6
) -> Dict[str, Any]:
    """
    Search for similar vectors in the database
    If dataset_id is None, search across all datasets
    """
    db = get_vector_db()
    
    # Handle empty database
    if not db:
        return {"success": False, "error": "Vector database is empty"}
    
    # If dataset specified but not found
    if dataset_id and dataset_id not in db:
        return {"success": False, "error": f"Dataset {dataset_id} not found"}
    
    # Convert query vector to numpy array if it's a list
    if isinstance(query_vector, list):
        query_np = np.array(query_vector)
    else:
        query_np = query_vector
    
    results = []
    
    # Determine which datasets to search
    datasets_to_search = [dataset_id] if dataset_id else list(db.keys())
    
    # Search each dataset
    for ds_id in datasets_to_search:
        if not db[ds_id]:
            continue
        
        # Extract vectors for batch processing
        vectors = []
        items = []
        
        for item in db[ds_id]:
            if "vector" not in item:
                continue
            
            vectors.append(item["vector"])
            items.append(item)
        
        if not vectors:
            continue
        
        # Convert to numpy array for efficient computation
        vectors_np = np.array(vectors)
        
        # Calculate cosine similarities in batch
        similarities = cosine_similarity([query_np], vectors_np)[0]
        
        # Add results above threshold
        for i, similarity in enumerate(similarities):
            if similarity >= threshold:
                results.append({
                    "content": items[i].get("content", ""),
                    "metadata": {
                        **items[i].get("metadata", {}),
                        "dataset_id": ds_id,
                        "source": items[i].get("metadata", {}).get("source", f"Dataset: {ds_id}")
                    },
                    "similarity": float(similarity)
                })
    
    # Sort by similarity (highest first)
    results.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Return top results
    return {"success": True, "results": results[:limit]}

def delete_vectors(dataset_id: str):
    """
    Delete all vectors for a specific dataset
    """
    db = get_vector_db()
    
    if dataset_id in db:
        count = len(db[dataset_id])
        del db[dataset_id]
        
        # Save changes to disk
        save_vector_db()
        
        return {"success": True, "count": count}
    
    return {"success": False, "error": f"Dataset {dataset_id} not found"}

def get_vector_stats():
    """
    Get statistics about the vector database
    """
    db = get_vector_db()
    
    stats = {
        "total_datasets": len(db),
        "total_vectors": sum(len(vectors) for vectors in db.values()),
        "datasets": {},
        "last_updated": datetime.now().isoformat()
    }
    
    for dataset_id, vectors in db.items():
        # Get the most recent timestamp if available
        latest_timestamp = None
        for vector in vectors:
            if "metadata" in vector and "added_at" in vector["metadata"]:
                timestamp = vector["metadata"]["added_at"]
                if latest_timestamp is None or timestamp > latest_timestamp:
                    latest_timestamp = timestamp
        
        stats["datasets"][dataset_id] = {
            "count": len(vectors),
            "last_updated": latest_timestamp
        }
    
    return {"success": True, "stats": stats}
