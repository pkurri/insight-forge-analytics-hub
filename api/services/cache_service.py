import os
import json
import logging
import pickle
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache file path
CACHE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cache.pkl')

# Ensure data directory exists
os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)

# In-memory cache
cache = {}

# Default TTL (time to live) in seconds
DEFAULT_TTL = 3600  # 1 hour

# Maximum cache size
MAX_CACHE_SIZE = 1000

# Cache statistics
cache_stats = {
    "hits": 0,
    "misses": 0,
    "size": 0,
    "evictions": 0,
    "last_cleaned": datetime.now().isoformat()
}

def load_cache():
    """
    Load cache from disk if available
    """
    global cache, cache_stats
    
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'rb') as f:
                data = pickle.load(f)
                cache = data.get("cache", {})
                cache_stats = data.get("stats", cache_stats)
            logger.info(f"Loaded cache from {CACHE_PATH} with {len(cache)} entries")
        except Exception as e:
            logger.error(f"Error loading cache: {str(e)}")
            # Initialize empty if loading fails
            cache = {}
            cache_stats = {
                "hits": 0,
                "misses": 0,
                "size": 0,
                "evictions": 0,
                "last_cleaned": datetime.now().isoformat()
            }

def save_cache():
    """
    Save cache to disk
    """
    try:
        with open(CACHE_PATH, 'wb') as f:
            pickle.dump({"cache": cache, "stats": cache_stats}, f)
        logger.info(f"Saved cache to {CACHE_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error saving cache: {str(e)}")
        return False

def get_cache(key: str) -> Optional[Any]:
    """
    Get a value from the cache
    """
    global cache_stats
    
    # Load cache if empty
    if not cache:
        load_cache()
    
    if key in cache:
        entry = cache[key]
        
        # Check if entry is expired
        if "expires_at" in entry and datetime.fromisoformat(entry["expires_at"]) < datetime.now():
            # Remove expired entry
            del cache[key]
            cache_stats["size"] = len(cache)
            cache_stats["misses"] += 1
            return None
        
        # Update access time (for LRU eviction)
        entry["last_accessed"] = datetime.now().isoformat()
        cache[key] = entry
        
        cache_stats["hits"] += 1
        return entry["value"]
    
    cache_stats["misses"] += 1
    return None

def set_cache(key: str, value: Any, ttl: int = DEFAULT_TTL, model_id: Optional[str] = None, dataset_id: Optional[str] = None):
    """
    Set a value in the cache with optional model and dataset tags
    """
    global cache, cache_stats
    
    # Load cache if empty
    if not cache:
        load_cache()
    
    # Check if cache is full
    if len(cache) >= MAX_CACHE_SIZE:
        # Evict least recently used entry
        evict_lru_entry()
    
    # Calculate expiration time
    expires_at = (datetime.now() + timedelta(seconds=ttl)).isoformat()
    
    # Create cache entry
    entry = {
        "value": value,
        "created_at": datetime.now().isoformat(),
        "last_accessed": datetime.now().isoformat(),
        "expires_at": expires_at,
        "ttl": ttl
    }
    
    # Add optional tags
    if model_id:
        entry["model_id"] = model_id
    
    if dataset_id:
        entry["dataset_id"] = dataset_id
    
    # Store in cache
    cache[key] = entry
    cache_stats["size"] = len(cache)
    
    # Periodically save cache to disk (every 100 entries)
    if cache_stats["size"] % 100 == 0:
        save_cache()
    
    return True

def evict_lru_entry():
    """
    Evict the least recently used cache entry
    """
    global cache, cache_stats
    
    if not cache:
        return
    
    # Find least recently accessed entry
    lru_key = None
    lru_time = None
    
    for key, entry in cache.items():
        last_accessed = datetime.fromisoformat(entry["last_accessed"])
        
        if lru_time is None or last_accessed < lru_time:
            lru_key = key
            lru_time = last_accessed
    
    # Remove entry
    if lru_key:
        del cache[lru_key]
        cache_stats["evictions"] += 1
        cache_stats["size"] = len(cache)

def clear_cache():
    """
    Clear the entire cache
    """
    global cache, cache_stats
    
    cache = {}
    cache_stats["size"] = 0
    cache_stats["last_cleaned"] = datetime.now().isoformat()
    
    # Save empty cache
    save_cache()
    
    return True

def clear_expired_entries():
    """
    Clear all expired entries from the cache
    """
    global cache, cache_stats
    
    # Load cache if empty
    if not cache:
        load_cache()
    
    now = datetime.now()
    expired_keys = []
    
    for key, entry in cache.items():
        if "expires_at" in entry and datetime.fromisoformat(entry["expires_at"]) < now:
            expired_keys.append(key)
    
    # Remove expired entries
    for key in expired_keys:
        del cache[key]
    
    cache_stats["size"] = len(cache)
    cache_stats["last_cleaned"] = now.isoformat()
    
    # Save cache if entries were removed
    if expired_keys:
        save_cache()
    
    return len(expired_keys)

def clear_by_model(model_id: str):
    """
    Clear all cache entries for a specific model
    """
    global cache, cache_stats
    
    # Load cache if empty
    if not cache:
        load_cache()
    
    keys_to_remove = []
    
    for key, entry in cache.items():
        if entry.get("model_id") == model_id:
            keys_to_remove.append(key)
    
    # Remove entries
    for key in keys_to_remove:
        del cache[key]
    
    cache_stats["size"] = len(cache)
    
    # Save cache if entries were removed
    if keys_to_remove:
        save_cache()
    
    return len(keys_to_remove)

def clear_by_dataset(dataset_id: str):
    """
    Clear all cache entries for a specific dataset
    """
    global cache, cache_stats
    
    # Load cache if empty
    if not cache:
        load_cache()
    
    keys_to_remove = []
    
    for key, entry in cache.items():
        if entry.get("dataset_id") == dataset_id:
            keys_to_remove.append(key)
    
    # Remove entries
    for key in keys_to_remove:
        del cache[key]
    
    cache_stats["size"] = len(cache)
    
    # Save cache if entries were removed
    if keys_to_remove:
        save_cache()
    
    return len(keys_to_remove)

def get_cache_stats():
    """
    Get cache statistics
    """
    global cache_stats
    
    # Update size
    cache_stats["size"] = len(cache)
    
    return {
        "success": True,
        "stats": cache_stats
    }
