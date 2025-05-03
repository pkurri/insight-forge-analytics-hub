/**
 * AI Cache Service
 * Provides caching capabilities for AI responses and embeddings
 * with support for model-specific and dataset-aware caching
 */

interface CacheOptions {
  ttl?: number;  // Time to live in milliseconds
  modelId?: string;
  datasetId?: string;
  maxSize?: number;
}

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
  modelId?: string;
  datasetId?: string;
}

interface CacheStats {
  hits: number;
  misses: number;
  size: number;
  maxSize: number;
}

/**
 * LRU Cache implementation with TTL support
 * Supports model-specific and dataset-aware caching
 */
export class AICache<T = any> {
  private cache: Map<string, CacheEntry<T>>;
  private maxSize: number;
  private defaultTTL: number;
  private stats: CacheStats;
  
  /**
   * Create a new cache instance
   * @param maxSize Maximum number of entries
   * @param defaultTTL Default time to live in milliseconds
   */
  constructor(maxSize: number = 1000, defaultTTL: number = 3600000) { // Default 1 hour TTL
    this.cache = new Map();
    this.maxSize = maxSize;
    this.defaultTTL = defaultTTL;
    this.stats = {
      hits: 0,
      misses: 0,
      size: 0,
      maxSize
    };
  }
  
  /**
   * Generate a cache key based on input and options
   * @param input Input string or object
   * @param options Cache options
   * @returns Cache key
   */
  private generateKey(input: string | Record<string, any>, options?: CacheOptions): string {
    const inputStr = typeof input === 'string' ? input : JSON.stringify(input);
    const modelPart = options?.modelId ? `:model=${options.modelId}` : '';
    const datasetPart = options?.datasetId ? `:dataset=${options.datasetId}` : '';
    
    return `${inputStr}${modelPart}${datasetPart}`;
  }
  
  /**
   * Check if an entry is expired
   * @param entry Cache entry
   * @returns True if expired
   */
  private isExpired(entry: CacheEntry<T>): boolean {
    const now = Date.now();
    return now - entry.timestamp > entry.ttl;
  }
  
  /**
   * Get a value from the cache
   * @param key Cache key or input to generate key from
   * @param options Cache options
   * @returns Cached value or undefined if not found or expired
   */
  get(key: string | Record<string, any>, options?: CacheOptions): T | undefined {
    const cacheKey = typeof key === 'string' ? key : this.generateKey(key, options);
    const entry = this.cache.get(cacheKey);
    
    if (!entry) {
      this.stats.misses++;
      return undefined;
    }
    
    // Check if entry is expired
    if (this.isExpired(entry)) {
      this.cache.delete(cacheKey);
      this.stats.misses++;
      this.stats.size = this.cache.size;
      return undefined;
    }
    
    // Update access order (LRU policy)
    this.cache.delete(cacheKey);
    this.cache.set(cacheKey, entry);
    this.stats.hits++;
    
    return entry.data;
  }
  
  /**
   * Set a value in the cache
   * @param key Cache key or input to generate key from
   * @param value Value to cache
   * @param options Cache options
   */
  set(key: string | Record<string, any>, value: T, options?: CacheOptions): void {
    const cacheKey = typeof key === 'string' ? key : this.generateKey(key, options);
    
    // Evict oldest entry if cache is full
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    
    // Create cache entry
    const entry: CacheEntry<T> = {
      data: value,
      timestamp: Date.now(),
      ttl: options?.ttl || this.defaultTTL,
      modelId: options?.modelId,
      datasetId: options?.datasetId
    };
    
    this.cache.set(cacheKey, entry);
    this.stats.size = this.cache.size;
  }
  
  /**
   * Check if a key exists in the cache
   * @param key Cache key or input to generate key from
   * @param options Cache options
   * @returns True if key exists and is not expired
   */
  has(key: string | Record<string, any>, options?: CacheOptions): boolean {
    const cacheKey = typeof key === 'string' ? key : this.generateKey(key, options);
    const entry = this.cache.get(cacheKey);
    
    if (!entry) {
      return false;
    }
    
    // Check if entry is expired
    if (this.isExpired(entry)) {
      this.cache.delete(cacheKey);
      this.stats.size = this.cache.size;
      return false;
    }
    
    return true;
  }
  
  /**
   * Delete a key from the cache
   * @param key Cache key or input to generate key from
   * @param options Cache options
   * @returns True if key was found and deleted
   */
  delete(key: string | Record<string, any>, options?: CacheOptions): boolean {
    const cacheKey = typeof key === 'string' ? key : this.generateKey(key, options);
    const result = this.cache.delete(cacheKey);
    this.stats.size = this.cache.size;
    return result;
  }
  
  /**
   * Clear all entries from the cache
   */
  clear(): void {
    this.cache.clear();
    this.stats.size = 0;
  }
  
  /**
   * Clear all entries for a specific model
   * @param modelId Model ID
   */
  clearByModel(modelId: string): void {
    for (const [key, entry] of this.cache.entries()) {
      if (entry.modelId === modelId) {
        this.cache.delete(key);
      }
    }
    this.stats.size = this.cache.size;
  }
  
  /**
   * Clear all entries for a specific dataset
   * @param datasetId Dataset ID
   */
  clearByDataset(datasetId: string): void {
    for (const [key, entry] of this.cache.entries()) {
      if (entry.datasetId === datasetId) {
        this.cache.delete(key);
      }
    }
    this.stats.size = this.cache.size;
  }
  
  /**
   * Get cache statistics
   * @returns Cache statistics
   */
  getStats(): CacheStats {
    return { ...this.stats };
  }
  
  /**
   * Get all keys in the cache
   * @returns Array of cache keys
   */
  keys(): string[] {
    return Array.from(this.cache.keys());
  }
  
  /**
   * Get the current size of the cache
   * @returns Number of entries in the cache
   */
  size(): number {
    return this.cache.size;
  }
}

// Create singleton instances for different types of caches
export const responseCache = new AICache<any>(500, 3600000); // 1 hour TTL for responses
export const embeddingCache = new AICache<number[]>(1000, 86400000); // 24 hour TTL for embeddings
export const datasetCache = new AICache<any>(100, 300000); // 5 minutes TTL for dataset metadata

// Export a default cacheService object with all caches
const cacheService = {
  response: responseCache,
  embedding: embeddingCache,
  dataset: datasetCache
};

export default cacheService;
