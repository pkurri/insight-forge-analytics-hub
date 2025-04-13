
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

# Import cache service for performance optimization
from api.services.cache_service import get_cached_response, cache_response

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
4. Neural Information Retrieval: Using embeddings for more natural search experiences
5. Cross-modal Retrieval: Finding connections between different data types

The implementation uses:
- FAISS (Facebook AI Similarity Search) for efficient vector similarity search
- Sentence embeddings from transformer models to encode text as vectors
- LRU caching to optimize repeated queries
- Asynchronous processing for better performance under load
- Optimized indexing structures for fast retrieval even with millions of vectors

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
        
    Vector Database Theory:
        Vector embeddings transform high-dimensional semantic meaning into
        numerical arrays that can be efficiently compared and searched.
        These embeddings capture the "essence" of content, allowing for
        similarity comparisons based on meaning rather than exact matches.
    """
    try:
        # Generate unique embedding ID
        embedding_id = f"{dataset_id}:{record_id}:{datetime.now().timestamp()}"
        
        # Check cache first
        cache_key = f"vector:store:{dataset_id}:{record_id}"
        cached_response = get_cached_response(cache_key)
        if cached_response:
            return cached_response
        
        # Initialize storage for this dataset if it doesn't exist
        if dataset_id not in _vector_storage:
            _vector_storage[dataset_id] = []
            _metadata_storage[dataset_id] = {}
        
        # Store the embedding and metadata
        _vector_storage[dataset_id].append((embedding_id, np.array(embedding, dtype=np.float32)))
        _metadata_storage[dataset_id][embedding_id] = {
            "record_id": record_id,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat(),
            "vector_stats": {
                "dimension": len(embedding),
                "l2_norm": float(np.linalg.norm(embedding)),
                "min_value": float(min(embedding)),
                "max_value": float(max(embedding))
            }
        }
        
        # Update or rebuild the FAISS index for this dataset
        await _build_or_update_index(dataset_id)
        
        result = {
            "success": True,
            "embedding_id": embedding_id,
            "message": "Embedding stored successfully"
        }
        
        # Cache the response
        cache_response(cache_key, result, 3600)
        
        return result
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
        
    Vector Search Theory:
        Vector similarity search works by measuring the "distance" between
        vectors in high-dimensional space. Common similarity metrics include:
        - Cosine similarity: Measures angle between vectors (direction similarity)
        - L2/Euclidean distance: Measures straight-line distance
        - Dot product: Combines magnitude and direction
        
        For efficient searching at scale, nearest neighbor algorithms use
        techniques like space partitioning, quantization, and graph-based
        indexing to avoid exhaustive comparisons.
    """
    try:
        # Check if we have embeddings for this dataset
        if dataset_id not in _vector_storage or not _vector_storage[dataset_id]:
            return []
        
        # Check cache for identical query
        query_hash = f"vector:search:{dataset_id}:{hash(str(query_vector))}:{limit}"
        cached_result = get_cached_response(query_hash)
        if cached_result:
            return cached_result
        
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
                    "metadata": metadata.get("metadata", {}),
                    "vector_stats": metadata.get("vector_stats", {})
                })
                
            # Cache results
            cache_response(query_hash, results, 1800)  # 30 minutes
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
                "metadata": metadata.get("metadata", {}),
                "vector_stats": metadata.get("vector_stats", {})
            })
        
        # Sort by similarity (highest first) and limit results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:limit]
        
        # Cache results
        cache_response(query_hash, results, 1800)  # 30 minutes
        
        return results
    
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
        
    AI Implementation:
        This function builds specialized index structures that support
        efficient similarity search in high-dimensional vector spaces.
        These indexes are critical for AI applications that need to
        search through large collections of embeddings quickly.
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
        vector_count = vectors_np.shape[0]
        
        # Choose appropriate index type based on dataset size
        if vector_count < 10000:
            # For small datasets, use exact search (FlatL2)
            index = faiss.IndexFlatL2(vector_dim)
        else:
            # For larger datasets, use approximate nearest neighbor search
            # IVF (Inverted File Index) with 4*sqrt(n) clusters
            n_clusters = min(4 * int(vector_count ** 0.5), vector_count // 10)
            n_clusters = max(n_clusters, 10)  # At least 10 clusters
            
            quantizer = faiss.IndexFlatL2(vector_dim)
            index = faiss.IndexIVFFlat(quantizer, vector_dim, n_clusters, faiss.METRIC_L2)
            
            # Train the index
            index.train(vectors_np)
        
        # Add vectors to index
        index.add(vectors_np)
        
        # Store index and embedding IDs mapping
        _faiss_indexes[dataset_id] = {
            "index": index,
            "embedding_ids": embedding_ids,
            "created_at": datetime.now().isoformat(),
            "vector_count": vector_count,
            "vector_dim": vector_dim
        }
        
        return True
    except Exception as e:
        print(f"Error building FAISS index: {str(e)}")
        return False

async def _search_faiss_index(
    dataset_id: str, 
    query_vector: List[float], 
    limit: int = 10,
    nprobe: int = None
) -> List[Tuple[str, float]]:
    """
    Search the FAISS index for similar vectors.
    
    Args:
        dataset_id: ID of the dataset
        query_vector: Query vector
        limit: Number of results to return
        nprobe: Number of clusters to visit (for IVF indexes)
        
    Returns:
        List of tuples with embedding ID and similarity score
        
    AI Implementation:
        This function executes the vector similarity search at the core of
        many AI retrieval systems. It uses optimized algorithms to efficiently
        find the closest vectors in high-dimensional space.
    """
    if dataset_id not in _faiss_indexes:
        return []
        
    faiss_data = _faiss_indexes[dataset_id]
    index = faiss_data["index"]
    embedding_ids = faiss_data["embedding_ids"]
    
    # Set nprobe dynamically if using IVF index
    if isinstance(index, faiss.IndexIVFFlat) and nprobe is None:
        # A higher nprobe means more accurate results but slower search
        # Dynamically scale based on dataset size
        vector_count = len(embedding_ids)
        if vector_count < 10000:
            nprobe = min(10, vector_count // 10)
        elif vector_count < 100000:
            nprobe = min(20, vector_count // 20)
        else:
            nprobe = min(40, vector_count // 50)
        
        index.nprobe = nprobe
    
    # Convert query to numpy array and reshape for FAISS
    query_np = np.array([query_vector], dtype=np.float32)
    
    # Search index
    distances, indices = index.search(query_np, min(limit, len(embedding_ids)))
    
    # Map results to embedding IDs with similarity scores
    # Convert L2 distance to similarity (smaller distance = higher similarity)
    max_distance = float(np.max(distances)) + 1.0  # Avoid division by zero
    results = [
        (embedding_ids[idx], 1.0 - (float(dist) / max_distance))  # Convert to similarity score
        for dist, idx in zip(distances[0], indices[0])
        if idx >= 0 and idx < len(embedding_ids)  # Filter invalid indices
    ]
    
    return results

async def build_vector_index(dataset_id: str, vectors: List[List[float]], 
                            embedding_ids: List[str]) -> Dict[str, Any]:
    """
    Build or update a vector index for fast similarity search.
    
    Args:
        dataset_id: ID of the dataset
        vectors: List of vector embeddings
        embedding_ids: IDs corresponding to each vector
        
    Returns:
        Dict with index statistics
        
    AI Implementation:
        Vector indexes are crucial for AI-powered search at scale.
        This function builds specialized data structures that enable
        efficient nearest-neighbor search in high-dimensional vector spaces.
    """
    try:
        # Check cache
        cache_key = f"vector:index_build:{dataset_id}:{len(vectors)}"
        cached_result = get_cached_response(cache_key)
        if cached_result:
            return cached_result
        
        # Ensure vectors and IDs are matching
        if len(vectors) != len(embedding_ids):
            raise ValueError("Number of vectors and embedding IDs must match")
            
        if not vectors:
            return {
                "success": True,
                "dataset_id": dataset_id,
                "message": "No vectors to index",
                "index_stats": {
                    "vector_count": 0,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        # Convert to numpy array
        vectors_np = np.array(vectors, dtype=np.float32)
        
        # Get dimensions
        vector_dim = vectors_np.shape[1]
        vector_count = vectors_np.shape[0]
        
        # Choose appropriate index type based on dataset size
        if vector_count < 10000:
            # For small datasets, use exact search
            index = faiss.IndexFlatL2(vector_dim)
        else:
            # For larger datasets, use approximate nearest neighbor search
            n_clusters = min(4 * int(vector_count ** 0.5), vector_count // 10)
            n_clusters = max(n_clusters, 10)  # At least 10 clusters
            
            quantizer = faiss.IndexFlatL2(vector_dim)
            index = faiss.IndexIVFFlat(quantizer, vector_dim, n_clusters, faiss.METRIC_L2)
            
            # Train the index
            index.train(vectors_np)
        
        # Add vectors to index
        index.add(vectors_np)
        
        # Store index and embedding IDs mapping
        _faiss_indexes[dataset_id] = {
            "index": index,
            "embedding_ids": embedding_ids,
            "created_at": datetime.now().isoformat(),
            "vector_count": vector_count,
            "vector_dim": vector_dim
        }
        
        # Prepare response
        result = {
            "success": True,
            "dataset_id": dataset_id,
            "message": f"Vector index built successfully with {vector_count} vectors",
            "index_stats": {
                "vector_count": vector_count,
                "vector_dimension": vector_dim,
                "index_type": type(index).__name__,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Cache for future use (12 hours)
        cache_response(cache_key, result, 43200)
        
        return result
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
        
    AI Implementation:
        Monitoring vector indexes is important for understanding and
        optimizing AI retrieval system performance.
    """
    # Check cache
    cache_key = f"vector:stats:{dataset_id}"
    cached_result = get_cached_response(cache_key)
    if cached_result:
        return cached_result
    
    stats = {
        "dataset_id": dataset_id,
        "vector_count": 0,
        "has_faiss_index": dataset_id in _faiss_indexes,
        "last_updated": None,
        "dimension": None,
        "vector_quality_metrics": {
            "avg_norm": None,
            "min_norm": None,
            "max_norm": None,
            "avg_distance": None
        }
    }
    
    if dataset_id in _vector_storage:
        vectors = [vec for _, vec in _vector_storage[dataset_id]]
        stats["vector_count"] = len(vectors)
        
        if stats["vector_count"] > 0:
            # Calculate basic stats
            stats["dimension"] = len(vectors[0])
            
            # Calculate vector quality metrics
            if stats["vector_count"] > 1:
                norms = [np.linalg.norm(vec) for vec in vectors]
                stats["vector_quality_metrics"]["avg_norm"] = float(np.mean(norms))
                stats["vector_quality_metrics"]["min_norm"] = float(np.min(norms))
                stats["vector_quality_metrics"]["max_norm"] = float(np.max(norms))
                
                # Calculate average distance between vectors (sample if many vectors)
                if stats["vector_count"] <= 100:
                    all_pairs = [(i, j) for i in range(len(vectors)) for j in range(i+1, len(vectors))]
                    distances = [np.linalg.norm(vectors[i] - vectors[j]) for i, j in all_pairs]
                    stats["vector_quality_metrics"]["avg_distance"] = float(np.mean(distances))
                else:
                    # Sample some pairs for large datasets
                    import random
                    sample_size = min(1000, stats["vector_count"] * 2)
                    sample_pairs = [(random.randint(0, stats["vector_count"]-1), 
                                    random.randint(0, stats["vector_count"]-1)) 
                                   for _ in range(sample_size)]
                    sample_pairs = [(i, j) for i, j in sample_pairs if i != j]
                    distances = [np.linalg.norm(vectors[i] - vectors[j]) for i, j in sample_pairs]
                    stats["vector_quality_metrics"]["avg_distance"] = float(np.mean(distances))
            
    if dataset_id in _metadata_storage and _metadata_storage[dataset_id]:
        # Find most recent timestamp
        timestamps = [
            datetime.fromisoformat(meta.get("timestamp", "2000-01-01T00:00:00"))
            for meta in _metadata_storage[dataset_id].values()
        ]
        if timestamps:
            stats["last_updated"] = max(timestamps).isoformat()
    
    # Add FAISS index details if available
    if dataset_id in _faiss_indexes:
        faiss_data = _faiss_indexes[dataset_id]
        stats["faiss_index"] = {
            "type": type(faiss_data["index"]).__name__,
            "created_at": faiss_data.get("created_at"),
            "vector_count": faiss_data.get("vector_count", stats["vector_count"]),
            "vector_dim": faiss_data.get("vector_dim", stats["dimension"])
        }
        
        # Add IVF-specific details if applicable
        if isinstance(faiss_data["index"], faiss.IndexIVFFlat):
            stats["faiss_index"]["ivf_details"] = {
                "nlist": faiss_data["index"].nlist,  # Number of clusters
                "nprobe": faiss_data["index"].nprobe  # Number of clusters to visit during search
            }
    
    # Cache for 30 minutes
    cache_response(cache_key, stats, 1800)
    
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

async def get_nearest_neighbors_graph(dataset_id: str, k: int = 5) -> Dict[str, Any]:
    """
    Generate a nearest neighbors graph for the vectors in a dataset.
    
    Args:
        dataset_id: ID of the dataset
        k: Number of neighbors to find for each vector
        
    Returns:
        Dict with graph data
        
    AI Implementation:
        Nearest neighbor graphs are useful for:
        1. Visualizing vector relationships
        2. Understanding data clustering
        3. Detecting outliers
        4. Building recommendation systems
    """
    try:
        # Check cache
        cache_key = f"vector:graph:{dataset_id}:{k}"
        cached_result = get_cached_response(cache_key)
        if cached_result:
            return cached_result
        
        if dataset_id not in _vector_storage or not _vector_storage[dataset_id]:
            return {
                "success": False,
                "message": f"No vectors found for dataset {dataset_id}"
            }
        
        # Get vectors and their IDs
        vector_pairs = _vector_storage[dataset_id]
        embedding_ids = [id for id, _ in vector_pairs]
        vectors = np.array([vec for _, vec in vector_pairs], dtype=np.float32)
        
        # Calculate nearest neighbors
        index = faiss.IndexFlatL2(vectors.shape[1])
        index.add(vectors)
        
        # Search for k+1 neighbors (the first neighbor is the vector itself)
        distances, indices = index.search(vectors, k+1)
        
        # Build graph structure
        graph = {
            "nodes": [],
            "edges": []
        }
        
        # Add nodes
        for i, embedding_id in enumerate(embedding_ids):
            metadata = _metadata_storage[dataset_id].get(embedding_id, {})
            record_id = metadata.get("record_id", f"record_{i}")
            
            node = {
                "id": embedding_id,
                "record_id": record_id,
                "metadata": metadata.get("metadata", {})
            }
            
            graph["nodes"].append(node)
        
        # Add edges (skip first neighbor which is self)
        for i, neighbors in enumerate(indices):
            source_id = embedding_ids[i]
            
            for j in range(1, len(neighbors)):
                neighbor_idx = neighbors[j]
                
                # Skip invalid indices
                if neighbor_idx < 0 or neighbor_idx >= len(embedding_ids):
                    continue
                    
                target_id = embedding_ids[neighbor_idx]
                distance = float(distances[i, j])
                
                edge = {
                    "source": source_id,
                    "target": target_id,
                    "distance": distance,
                    "similarity": 1.0 / (1.0 + distance)  # Convert distance to similarity
                }
                
                graph["edges"].append(edge)
        
        result = {
            "success": True,
            "dataset_id": dataset_id,
            "graph": graph,
            "stats": {
                "node_count": len(graph["nodes"]),
                "edge_count": len(graph["edges"]),
                "k_neighbors": k
            }
        }
        
        # Cache for 1 hour
        cache_response(cache_key, result, 3600)
        
        return result
        
    except Exception as e:
        print(f"Error generating nearest neighbors graph: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
