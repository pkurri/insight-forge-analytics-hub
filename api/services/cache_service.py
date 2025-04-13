
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from functools import lru_cache
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced in-memory cache with optimized data structures for AI workloads
_cache: Dict[str, Dict[str, Any]] = {}

# Cache statistics for performance monitoring and optimization
_cache_stats = {
    "hits": 0,
    "misses": 0,
    "evictions": 0,
    "insertions": 0,
    "ai_model_hits": 0,  # AI-specific hits
    "vector_hits": 0,    # Vector-specific hits
    "schema_hits": 0     # Schema-specific hits
}

# Cache configuration
_cache_config = {
    "max_size": 10000,           # Maximum number of items in cache
    "cleanup_threshold": 8000,    # Threshold to trigger cleanup
    "default_ttl": 3600,         # Default TTL in seconds (1 hour)
    "vector_ttl": 7200,          # TTL for vector embeddings (2 hours)
    "schema_ttl": 86400,         # TTL for detected schemas (24 hours)
    "ai_model_ttl": 43200,       # TTL for AI model outputs (12 hours)
    "min_access_for_keep": 2     # Minimum access count to keep during cleanup
}

"""
AI-Optimized Cache Implementation

This cache system is specifically optimized for AI workloads in data pipelines:

1. Smart Caching Strategy: Differentiates between expensive AI operations 
   (like vector embeddings, schema detection) and regular data
   
2. Performance Monitoring: Tracks fine-grained statistics to optimize 
   AI system performance
   
3. Intelligent Eviction: Uses AI-aware eviction policies that prioritize
   keeping frequently accessed and computationally expensive results
   
4. TTL-based Expiry: Different expiration times for different types of
   cached content based on their computational cost and volatility
"""

def get_cached_response(key: str) -> Optional[Dict[str, Any]]:
    """
    Get a response from the cache if it exists and is not expired
    
    Args:
        key: The cache key
        
    Returns:
        The cached data if found and valid, otherwise None
        
    Notes:
        For AI operations, this reduces computational load by avoiding
        expensive recalculations and model inferences
    """
    if key not in _cache:
        _cache_stats["misses"] += 1
        return None
    
    cache_item = _cache[key]
    
    # Check if expired
    if cache_item["expires_at"] < time.time():
        # Expired, remove from cache
        del _cache[key]
        _cache_stats["evictions"] += 1
        return None
    
    # Update access stats
    _cache[key]["access_count"] += 1
    _cache[key]["last_accessed"] = time.time()
    
    # Record cache hit for performance monitoring
    _cache_stats["hits"] += 1
    
    # Track AI-specific hits
    if key.startswith("vector:"):
        _cache_stats["vector_hits"] += 1
    elif key.startswith("schema_detection:"):
        _cache_stats["schema_hits"] += 1
    elif key.startswith("ai_model:"):
        _cache_stats["ai_model_hits"] += 1
    
    logger.debug(f"Cache hit for key: {key}")
    return cache_item["data"]

def cache_response(key: str, data: Dict[str, Any], expiry_seconds: Optional[int] = None) -> None:
    """
    Store a response in the cache with AI-aware TTL selection
    
    Args:
        key: The cache key
        data: The data to cache
        expiry_seconds: How long the cache should be valid for (in seconds)
                        If None, a default is selected based on key type
    """
    now = time.time()
    
    # Determine appropriate TTL if not specified
    if expiry_seconds is None:
        if key.startswith("vector:"):
            expiry_seconds = _cache_config["vector_ttl"]
        elif key.startswith("schema_detection:"):
            expiry_seconds = _cache_config["schema_ttl"]
        elif key.startswith("ai_model:"):
            expiry_seconds = _cache_config["ai_model_ttl"]
        else:
            expiry_seconds = _cache_config["default_ttl"]
    
    _cache[key] = {
        "data": data,
        "created_at": now,
        "expires_at": now + expiry_seconds,
        "last_accessed": now,
        "access_count": 0,
        "key_type": _determine_key_type(key),
        "size_estimate": _estimate_size(data)
    }
    
    # Record cache insertion for performance monitoring
    _cache_stats["insertions"] += 1
    
    logger.debug(f"Stored in cache: {key} (expires in {expiry_seconds}s)")
    
    # Perform cache cleanup if it's getting large
    if len(_cache) > _cache_config["cleanup_threshold"]:
        _cleanup_cache()

def invalidate_cache(key: str) -> bool:
    """
    Remove a specific item from the cache
    
    Args:
        key: The cache key to remove
        
    Returns:
        True if the item was in the cache and removed, False otherwise
    """
    if key in _cache:
        del _cache[key]
        logger.debug(f"Invalidated cache key: {key}")
        return True
    return False

def invalidate_by_prefix(prefix: str) -> int:
    """
    Remove all cache items with keys starting with the given prefix
    
    Args:
        prefix: The prefix to match
        
    Returns:
        Number of items removed
    """
    keys_to_remove = [k for k in _cache.keys() if k.startswith(prefix)]
    count = len(keys_to_remove)
    
    for key in keys_to_remove:
        del _cache[key]
    
    logger.info(f"Invalidated {count} cache items with prefix: {prefix}")
    return count

def clear_cache() -> int:
    """
    Clear the entire cache
    
    Returns:
        The number of items that were in the cache
    """
    count = len(_cache)
    _cache.clear()
    
    # Reset statistics when cache is cleared
    for key in _cache_stats:
        _cache_stats[key] = 0
        
    logger.info(f"Cleared {count} items from cache")
    return count

def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache performance statistics with AI-specific metrics
    
    Returns:
        Dictionary with cache statistics
    """
    hit_rate = 0
    if _cache_stats["hits"] + _cache_stats["misses"] > 0:
        hit_rate = _cache_stats["hits"] / (_cache_stats["hits"] + _cache_stats["misses"])
    
    # Calculate AI-specific hit rates
    ai_hits = _cache_stats["vector_hits"] + _cache_stats["schema_hits"] + _cache_stats["ai_model_hits"]
    
    # Estimate memory usage
    memory_usage = sum(_cache[key].get("size_estimate", 1000) for key in _cache)
    
    # Count by type
    type_counts = {
        "vector": sum(1 for k, v in _cache.items() if v.get("key_type") == "vector"),
        "schema": sum(1 for k, v in _cache.items() if v.get("key_type") == "schema"),
        "ai_model": sum(1 for k, v in _cache.items() if v.get("key_type") == "ai_model"),
        "other": sum(1 for k, v in _cache.items() if v.get("key_type") == "other")
    }
    
    return {
        **_cache_stats,
        "size": len(_cache),
        "hit_rate": hit_rate,
        "ai_hit_rate": ai_hits / _cache_stats["hits"] if _cache_stats["hits"] > 0 else 0,
        "memory_usage_bytes": memory_usage,
        "type_counts": type_counts,
        "config": _cache_config,
        "timestamp": time.time()
    }

def update_cache_config(config_updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update cache configuration parameters
    
    Args:
        config_updates: Dictionary of configuration parameters to update
        
    Returns:
        Updated configuration dictionary
    """
    global _cache_config
    
    for key, value in config_updates.items():
        if key in _cache_config:
            _cache_config[key] = value
    
    logger.info(f"Updated cache configuration: {config_updates}")
    return _cache_config

def _cleanup_cache() -> int:
    """
    Clean up the cache using an AI-aware strategy that prioritizes keeping:
    1. Computationally expensive results (vectors, models)
    2. Frequently accessed items
    3. Recently accessed items
    
    Returns:
        The number of items removed from the cache
    """
    now = time.time()
    expired_keys = [k for k, v in _cache.items() if v["expires_at"] < now]
    
    # Remove expired items
    for key in expired_keys:
        del _cache[key]
        _cache_stats["evictions"] += 1
    
    # If still too many items, use a more sophisticated eviction policy
    if len(_cache) > _cache_config["cleanup_threshold"]:
        # Get all items sorted by priority score (lower = more likely to be removed)
        items = list(_cache.items())
        
        # Calculate priority scores
        for i, (key, value) in enumerate(items):
            # Base score
            score = 0
            
            # Add score based on access count (frequently used items are valuable)
            access_count = value["access_count"]
            score += min(access_count * 10, 100)  # Cap at 100
            
            # Add score based on recency (recently used items are valuable)
            recency = now - value["last_accessed"]
            recency_score = max(0, 100 - (recency / 60))  # Higher score for more recent access, max 100
            score += recency_score
            
            # Add score based on type (AI operations are more expensive to recompute)
            key_type = value.get("key_type", "other")
            type_scores = {
                "vector": 100,   # Very expensive
                "schema": 80,    # Expensive
                "ai_model": 60,  # Moderately expensive
                "other": 0       # Standard
            }
            score += type_scores.get(key_type, 0)
            
            # Store the score
            items[i] = (key, value, score)
        
        # Sort by score (ascending)
        items.sort(key=lambda x: x[2])
        
        # Remove lowest scoring items to reach target size
        target_size = _cache_config["max_size"] * 0.8  # Reduce to 80% of max
        items_to_remove = items[:int(len(items) - target_size)]
        
        for key, _, _ in items_to_remove:
            # Don't remove items with high access count even if low score
            if _cache[key]["access_count"] >= _cache_config["min_access_for_keep"]:
                continue
                
            del _cache[key]
            _cache_stats["evictions"] += 1
    
    removed = len(expired_keys) + (len(_cache) - _cache_config["cleanup_threshold"] if len(_cache) > _cache_config["cleanup_threshold"] else 0)
    logger.info(f"Cache cleanup: removed {removed} items")
    return removed

def _determine_key_type(key: str) -> str:
    """Determine the type of cache key for AI-aware TTL and eviction"""
    if key.startswith("vector:"):
        return "vector"
    elif key.startswith("schema_detection:"):
        return "schema"
    elif key.startswith("ai_model:"):
        return "ai_model"
    else:
        return "other"

def _estimate_size(data: Dict[str, Any]) -> int:
    """Estimate the memory size of cached data in bytes"""
    try:
        # Convert to JSON string and get byte size
        return len(json.dumps(data).encode('utf-8'))
    except:
        # Fallback if data is not JSON serializable
        return 1000  # Default estimate

# Helper function for dataset service - uses LRU cache for frequently accessed data
@lru_cache(maxsize=100)
async def get_all_dataset_ids():
    """Mock function to get all dataset IDs - would be replaced with actual DB call"""
    # This would be replaced with actual database query
    return ["ds001", "ds002", "ds003"]

@lru_cache(maxsize=100)
async def get_dataset_columns(dataset_id: str):
    """Mock function to get columns for a dataset - would be replaced with actual DB call"""
    # This would be replaced with actual database query
    columns_map = {
        "ds001": ["name", "age", "salary", "department"],
        "ds002": ["product_id", "price", "quantity", "date"],
        "ds003": ["customer_id", "order_date", "total_value", "items"]
    }
    return columns_map.get(dataset_id, [])
