
import time
import logging
from typing import Dict, Any, Optional
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple in-memory cache with optimized data structures
_cache: Dict[str, Dict[str, Any]] = {}

# Cache statistics for performance monitoring
_cache_stats = {
    "hits": 0,
    "misses": 0,
    "evictions": 0,
    "insertions": 0
}

def get_cached_response(key: str) -> Optional[Dict[str, Any]]:
    """
    Get a response from the cache if it exists and is not expired
    
    Args:
        key: The cache key
        
    Returns:
        The cached data if found and valid, otherwise None
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
    
    logger.debug(f"Cache hit for key: {key}")
    return cache_item["data"]

def cache_response(key: str, data: Dict[str, Any], expiry_seconds: int = 3600) -> None:
    """
    Store a response in the cache
    
    Args:
        key: The cache key
        data: The data to cache
        expiry_seconds: How long the cache should be valid for (in seconds)
    """
    now = time.time()
    
    _cache[key] = {
        "data": data,
        "created_at": now,
        "expires_at": now + expiry_seconds,
        "last_accessed": now,
        "access_count": 0
    }
    
    # Record cache insertion for performance monitoring
    _cache_stats["insertions"] += 1
    
    logger.debug(f"Stored in cache: {key} (expires in {expiry_seconds}s)")
    
    # Perform cache cleanup if it's getting large
    if len(_cache) > 1000:  # Arbitrary limit
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
    Get cache performance statistics
    
    Returns:
        Dictionary with cache statistics
    """
    hit_rate = 0
    if _cache_stats["hits"] + _cache_stats["misses"] > 0:
        hit_rate = _cache_stats["hits"] / (_cache_stats["hits"] + _cache_stats["misses"])
    
    return {
        **_cache_stats,
        "size": len(_cache),
        "hit_rate": hit_rate,
        "timestamp": time.time()
    }

def _cleanup_cache() -> int:
    """
    Clean up the cache by removing expired or least recently used items
    
    Returns:
        The number of items removed from the cache
    """
    now = time.time()
    expired_keys = [k for k, v in _cache.items() if v["expires_at"] < now]
    
    # Remove expired items
    for key in expired_keys:
        del _cache[key]
        _cache_stats["evictions"] += 1
    
    # If still too many items, remove least recently accessed
    if len(_cache) > 800:  # Target size
        items = list(_cache.items())
        # Sort by last accessed time
        items.sort(key=lambda x: x[1]["last_accessed"])
        # Remove oldest 20% of items
        items_to_remove = items[:int(len(items) * 0.2)]
        for key, _ in items_to_remove:
            del _cache[key]
            _cache_stats["evictions"] += 1
    
    removed = len(expired_keys) + (len(_cache) - 800 if len(_cache) > 800 else 0)
    logger.info(f"Cache cleanup: removed {removed} items")
    return removed

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
