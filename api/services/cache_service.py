import os
import json
import logging
import pickle
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        # Cache file path
        self.CACHE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cache.pkl')
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.CACHE_PATH), exist_ok=True)
        
        # In-memory cache
        self.cache = {}
        
        # Default TTL (time to live) in seconds
        self.DEFAULT_TTL = 3600  # 1 hour
        
        # Maximum cache size
        self.MAX_CACHE_SIZE = 1000
        
        # Cache statistics
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "size": 0,
            "evictions": 0,
            "last_cleaned": datetime.now().isoformat()
        }
        
        # Load cache on initialization
        self.load_cache()

    def load_cache(self):
        """Load cache from disk if available"""
        if os.path.exists(self.CACHE_PATH):
            try:
                with open(self.CACHE_PATH, 'rb') as f:
                    data = pickle.load(f)
                    self.cache = data.get("cache", {})
                    self.cache_stats = data.get("stats", self.cache_stats)
                logger.info(f"Loaded cache from {self.CACHE_PATH} with {len(self.cache)} entries")
            except Exception as e:
                logger.error(f"Error loading cache: {str(e)}")
                # Initialize empty if loading fails
                self.cache = {}
                self.cache_stats = {
                    "hits": 0,
                    "misses": 0,
                    "size": 0,
                    "evictions": 0,
                    "last_cleaned": datetime.now().isoformat()
                }

    def save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.CACHE_PATH, 'wb') as f:
                pickle.dump({"cache": self.cache, "stats": self.cache_stats}, f)
            logger.info(f"Saved cache to {self.CACHE_PATH}")
            return True
        except Exception as e:
            logger.error(f"Error saving cache: {str(e)}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache"""
        if key in self.cache:
            entry = self.cache[key]
            
            # Check if entry is expired
            if "expires_at" in entry and datetime.fromisoformat(entry["expires_at"]) < datetime.now():
                # Remove expired entry
                del self.cache[key]
                self.cache_stats["size"] = len(self.cache)
                self.cache_stats["misses"] += 1
                return None
            
            # Update access time (for LRU eviction)
            entry["last_accessed"] = datetime.now().isoformat()
            self.cache[key] = entry
            
            self.cache_stats["hits"] += 1
            return entry["value"]
        
        self.cache_stats["misses"] += 1
        return None

    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL, model_id: Optional[str] = None, dataset_id: Optional[str] = None):
        """Set a value in the cache with optional model and dataset tags"""
        # Check if cache is full
        if len(self.cache) >= self.MAX_CACHE_SIZE:
            # Evict least recently used entry
            self.evict_lru_entry()
        
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
        self.cache[key] = entry
        self.cache_stats["size"] = len(self.cache)
        
        # Periodically save cache to disk (every 100 entries)
        if self.cache_stats["size"] % 100 == 0:
            self.save_cache()
        
        return True

    def evict_lru_entry(self):
        """Evict the least recently used cache entry"""
        if not self.cache:
            return
        
        # Find least recently accessed entry
        lru_key = None
        lru_time = None
        
        for key, entry in self.cache.items():
            last_accessed = datetime.fromisoformat(entry["last_accessed"])
            
            if lru_time is None or last_accessed < lru_time:
                lru_key = key
                lru_time = last_accessed
        
        # Remove entry
        if lru_key:
            del self.cache[lru_key]
            self.cache_stats["evictions"] += 1
            self.cache_stats["size"] = len(self.cache)

    def clear(self):
        """Clear the entire cache"""
        self.cache = {}
        self.cache_stats["size"] = 0
        self.cache_stats["last_cleaned"] = datetime.now().isoformat()
        
        # Save empty cache
        self.save_cache()
        
        return True

    def clear_expired(self):
        """Clear all expired entries from the cache"""
        now = datetime.now()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if "expires_at" in entry and datetime.fromisoformat(entry["expires_at"]) < now:
                expired_keys.append(key)
        
        # Remove expired entries
        for key in expired_keys:
            del self.cache[key]
        
        self.cache_stats["size"] = len(self.cache)
        self.cache_stats["last_cleaned"] = now.isoformat()
        
        # Save cache if entries were removed
        if expired_keys:
            self.save_cache()
        
        return len(expired_keys)

    def clear_by_model(self, model_id: str):
        """Clear all cache entries for a specific model"""
        keys_to_remove = []
        
        for key, entry in self.cache.items():
            if entry.get("model_id") == model_id:
                keys_to_remove.append(key)
        
        # Remove entries
        for key in keys_to_remove:
            del self.cache[key]
        
        self.cache_stats["size"] = len(self.cache)
        
        # Save cache if entries were removed
        if keys_to_remove:
            self.save_cache()
        
        return len(keys_to_remove)

    def clear_by_dataset(self, dataset_id: str):
        """Clear all cache entries for a specific dataset"""
        keys_to_remove = []
        
        for key, entry in self.cache.items():
            if entry.get("dataset_id") == dataset_id:
                keys_to_remove.append(key)
        
        # Remove entries
        for key in keys_to_remove:
            del self.cache[key]
        
        self.cache_stats["size"] = len(self.cache)
        
        # Save cache if entries were removed
        if keys_to_remove:
            self.save_cache()
        
        return len(keys_to_remove)

    def get_stats(self):
        """Get cache statistics"""
        # Update size
        self.cache_stats["size"] = len(self.cache)
        
        return {
            "success": True,
            "stats": self.cache_stats
        }

# Create a singleton instance
cache_service = CacheService()

# Export the singleton instance
__all__ = ['cache_service']
