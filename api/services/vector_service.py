
"""
Vector Database Service for AI chat and document retrieval
"""
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import os
from functools import lru_cache

# Import libraries (these should be added to requirements.txt)
try:
    import numpy as np
    import faiss
except ImportError:
    pass  # Handle gracefully in production code

# In-memory vector storage for demo purposes
# In production, this would be a proper vector database (Pinecone, Milvus, etc.)
_vector_storage = {}
_metadata_storage = {}

# FAISS indexes for faster similarity search
_faiss_indexes = {}

"""
AI Implementation Details:
--------------------------
This service implements vector database functionality for AI-powered semantic search.
Vector databases are a critical component in modern AI systems, particularly for:

1. Semantic Search: Finding conceptually similar items beyond exact keyword matches
2. Recommendation Systems: Suggesting related content based on semantic similarity
3. Question Answering: Retrieving relevant context to support AI responses

The implementation uses:
- FAISS (Facebook AI Similarity Search) for efficient vector similarity search
- Sentence embeddings from transformer models to encode text as vectors
- LRU caching to optimize repeated queries
- Asynchronous processing for better performance under load

In production environments, this would connect to a dedicated vector database
service like Pinecone, Weaviate, or Milvus instead of using in-memory storage.
"""

async def store_vector_embeddings(dataset_id: str, record_id: str, 
                                 embedding: List[float], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store vector embeddings for future retrieval.
    
    Args:
        dataset_id: ID of the dataset
        record_id: ID of the specific record
        embedding: Vector embedding (list of floats)
        metadata: Associated metadata
        
    Returns:
        Dict with storage confirmation
        
    AI Implementation:
        This function stores vector embeddings that represent the semantic
        meaning of text or other data. The vectors enable semantic search
        and AI-powered question answering.
    """
    try:
        # Generate unique embedding ID
        embedding_id = f"{dataset_id}:{record_id}:{datetime.now().timestamp()}"
        
        # Initialize storage for this dataset if it doesn't exist
        if dataset_id not in _vector_storage:
            _vector_storage[dataset_id] = []
            _metadata_storage[dataset_id] = {}
        
        # Store the embedding and metadata
        _vector_storage[dataset_id].append((embedding_id, np.array(embedding, dtype=np.float32)))
        _metadata_storage[dataset_id][embedding_id] = {
            "record_id": record_id,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update or rebuild the FAISS index for this dataset
        await _build_or_update_index(dataset_id)
        
        return {
            "success": True,
            "embedding_id": embedding_id,
            "message": "Embedding stored successfully"
        }
    except Exception as e:
        print(f"Error storing vector embedding: {str(e)}")
        raise

async def search_vector_embeddings(dataset_id: str, query_vector: List[float], 
                                  limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for similar vectors in the database.
    
    Args:
        dataset_id: ID of the dataset to search within
        query_vector: Query vector for similarity search
        limit: Number of results to return
        
    Returns:
        List of matching results with metadata
        
    AI Implementation:
        This function performs semantic search using vector similarity.
        It's the core of AI-powered data exploration, allowing users to
        find information based on meaning rather than exact keyword matches.
        
        The FAISS library accelerates vector search performance by using:
        1. Specialized indexing structures (IVF, HNSW)
        2. Efficient distance calculations optimized for CPUs/GPUs
        3. Approximate nearest neighbor algorithms for speed
    """
    try:
        # Check if we have embeddings for this dataset
        if dataset_id not in _vector_storage or not _vector_storage[dataset_id]:
            return []
        
        # Use FAISS index if available for fast search
        if dataset_id in _faiss_indexes:
            embedding_ids = await _search_faiss_index(dataset_id, query_vector, limit)
            
            # Get metadata and format results
            results = []
            for embedding_id, similarity in embedding_ids:
                metadata = _metadata_storage[dataset_id].get(embedding_id, {})
                results.append({
                    "embedding_id": embedding_id,
                    "record_id": metadata.get("record_id"),
                    "similarity": similarity,
                    "metadata": metadata.get("metadata", {})
                })
            return results
            
        # Fallback to simple cosine similarity if FAISS index not available
        query_array = np.array(query_vector, dtype=np.float32)
        
        results = []
        for embedding_id, stored_vector in _vector_storage[dataset_id]:
            # Calculate cosine similarity
            similarity = np.dot(query_array, stored_vector) / (np.linalg.norm(query_array) * np.linalg.norm(stored_vector))
            
            # Get metadata
            metadata = _metadata_storage[dataset_id].get(embedding_id, {})
            
            results.append({
                "embedding_id": embedding_id,
                "record_id": metadata.get("record_id"),
                "similarity": float(similarity),
                "metadata": metadata.get("metadata", {})
            })
        
        # Sort by similarity (highest first) and limit results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]
    
    except Exception as e:
        print(f"Error searching vector embeddings: {str(e)}")
        raise

async def _build_or_update_index(dataset_id: str) -> bool:
    """
    Build or update the FAISS index for a dataset.
    
    Args:
        dataset_id: ID of the dataset
        
    Returns:
        True if successful
        
    Notes:
        FAISS indexes dramatically improve search performance,
        especially for large datasets with millions of vectors.
    """
    if dataset_id not in _vector_storage:
        return False
        
    vectors = [vec for _, vec in _vector_storage[dataset_id]]
    embedding_ids = [id for id, _ in _vector_storage[dataset_id]]
    
    # Skip if no vectors
    if not vectors:
        return False
        
    try:
        # Convert to numpy array
        vectors_np = np.array(vectors, dtype=np.float32)
        
        # Get dimensions
        vector_dim = vectors_np.shape[1]
        
        # Create index - use L2 distance metric
        index = faiss.IndexFlatL2(vector_dim)
        
        # Add vectors to index
        index.add(vectors_np)
        
        # Store index and embedding IDs mapping
        _faiss_indexes[dataset_id] = {
            "index": index,
            "embedding_ids": embedding_ids
        }
        
        return True
    except Exception as e:
        print(f"Error building FAISS index: {str(e)}")
        return False

async def _search_faiss_index(
    dataset_id: str, 
    query_vector: List[float], 
    limit: int = 10
) -> List[Tuple[str, float]]:
    """
    Search the FAISS index for similar vectors.
    
    Args:
        dataset_id: ID of the dataset
        query_vector: Query vector
        limit: Number of results to return
        
    Returns:
        List of tuples with embedding ID and similarity score
    """
    if dataset_id not in _faiss_indexes:
        return []
        
    faiss_data = _faiss_indexes[dataset_id]
    index = faiss_data["index"]
    embedding_ids = faiss_data["embedding_ids"]
    
    # Convert query to numpy array and reshape for FAISS
    query_np = np.array([query_vector], dtype=np.float32)
    
    # Search index
    distances, indices = index.search(query_np, min(limit, len(embedding_ids)))
    
    # Map results to embedding IDs with similarity scores
    # Convert L2 distance to similarity (smaller distance = higher similarity)
    max_distance = np.max(distances) + 1.0  # Avoid division by zero
    results = [
        (embedding_ids[idx], 1.0 - (dist / max_distance))  # Convert to similarity score
        for dist, idx in zip(distances[0], indices[0])
        if idx >= 0 and idx < len(embedding_ids)  # Filter invalid indices
    ]
    
    return results

async def build_vector_index(dataset_id: str, vectors: List[List[float]], 
                            embedding_ids: List[str]) -> bool:
    """
    Build or update a vector index for fast similarity search.
    
    Args:
        dataset_id: ID of the dataset
        vectors: List of vector embeddings
        embedding_ids: IDs corresponding to each vector
        
    Returns:
        True if successful
        
    AI Implementation:
        Vector indexes are crucial for AI-powered search at scale.
        This function builds specialized data structures that enable
        efficient nearest-neighbor search in high-dimensional vector spaces.
    """
    try:
        # Ensure vectors and IDs are matching
        if len(vectors) != len(embedding_ids):
            raise ValueError("Number of vectors and embedding IDs must match")
            
        if not vectors:
            return True
            
        # Convert to numpy array
        vectors_np = np.array(vectors, dtype=np.float32)
        
        # Get dimensions
        vector_dim = vectors_np.shape[1]
        
        # Create index - use L2 distance metric
        index = faiss.IndexFlatL2(vector_dim)
        
        # Add vectors to index
        index.add(vectors_np)
        
        # Store index and embedding IDs mapping
        _faiss_indexes[dataset_id] = {
            "index": index,
            "embedding_ids": embedding_ids
        }
        
        return True
    except Exception as e:
        print(f"Error building vector index: {str(e)}")
        raise

@lru_cache(maxsize=20)
async def get_index_stats(dataset_id: str) -> Dict[str, Any]:
    """
    Get statistics about the vector index for a dataset.
    
    Args:
        dataset_id: ID of the dataset
        
    Returns:
        Dict with index statistics
    """
    stats = {
        "dataset_id": dataset_id,
        "vector_count": 0,
        "has_faiss_index": dataset_id in _faiss_indexes,
        "last_updated": None,
        "dimension": None
    }
    
    if dataset_id in _vector_storage:
        stats["vector_count"] = len(_vector_storage[dataset_id])
        if stats["vector_count"] > 0:
            stats["dimension"] = len(_vector_storage[dataset_id][0][1])
            
    if dataset_id in _metadata_storage and _metadata_storage[dataset_id]:
        # Find most recent timestamp
        timestamps = [
            datetime.fromisoformat(meta.get("timestamp", "2000-01-01T00:00:00"))
            for meta in _metadata_storage[dataset_id].values()
        ]
        if timestamps:
            stats["last_updated"] = max(timestamps).isoformat()
    
    return stats

async def delete_vector_embeddings(dataset_id: str, embedding_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Delete vector embeddings from storage.
    
    Args:
        dataset_id: ID of the dataset
        embedding_ids: Optional list of specific embedding IDs to delete
                       If None, all embeddings for the dataset are deleted
        
    Returns:
        Dict with deletion confirmation
    """
    try:
        if dataset_id not in _vector_storage:
            return {
                "success": False,
                "message": f"Dataset {dataset_id} not found in vector storage"
            }
        
        if embedding_ids is None:
            # Delete all embeddings for this dataset
            _vector_storage.pop(dataset_id, None)
            _metadata_storage.pop(dataset_id, None)
            
            # Remove FAISS index
            if dataset_id in _faiss_indexes:
                _faiss_indexes.pop(dataset_id, None)
            
            return {
                "success": True,
                "message": f"All embeddings for dataset {dataset_id} deleted"
            }
        else:
            # Delete specific embeddings
            retained_vectors = []
            for embedding_id, vector in _vector_storage[dataset_id]:
                if embedding_id not in embedding_ids:
                    retained_vectors.append((embedding_id, vector))
            
            # Update storage
            _vector_storage[dataset_id] = retained_vectors
            
            # Delete metadata
            for embedding_id in embedding_ids:
                _metadata_storage[dataset_id].pop(embedding_id, None)
            
            # Rebuild FAISS index
            if dataset_id in _faiss_indexes:
                await _build_or_update_index(dataset_id)
            
            return {
                "success": True,
                "deleted_count": len(embedding_ids),
                "message": f"Deleted {len(embedding_ids)} embeddings from dataset {dataset_id}"
            }
    
    except Exception as e:
        print(f"Error deleting vector embeddings: {str(e)}")
        raise
