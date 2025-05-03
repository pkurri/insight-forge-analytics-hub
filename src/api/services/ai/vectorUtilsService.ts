/**
 * Vector Utilities Service for AI operations
 * Provides helper functions for vector operations and similarity calculations
 */

/**
 * Calculate cosine similarity between two vectors
 * @param a First vector
 * @param b Second vector
 * @returns Similarity score between -1 and 1 (1 being identical)
 */
export function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length) {
    throw new Error('Vectors must have the same dimensions');
  }
  
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  
  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  
  if (normA === 0 || normB === 0) {
    return 0;
  }
  
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

/**
 * Calculate Euclidean distance between two vectors
 * @param a First vector
 * @param b Second vector
 * @returns Distance value (lower means more similar)
 */
export function euclideanDistance(a: number[], b: number[]): number {
  if (a.length !== b.length) {
    throw new Error('Vectors must have the same dimensions');
  }
  
  let sum = 0;
  
  for (let i = 0; i < a.length; i++) {
    const diff = a[i] - b[i];
    sum += diff * diff;
  }
  
  return Math.sqrt(sum);
}

/**
 * Normalize a vector to unit length
 * @param vector Vector to normalize
 * @returns Normalized vector
 */
export function normalizeVector(vector: number[]): number[] {
  const magnitude = Math.sqrt(vector.reduce((sum, val) => sum + val * val, 0));
  
  if (magnitude === 0) {
    return Array(vector.length).fill(0);
  }
  
  return vector.map(val => val / magnitude);
}

/**
 * Find the top K most similar vectors using cosine similarity
 * @param query Query vector
 * @param vectors Array of vectors to compare against
 * @param k Number of results to return
 * @returns Array of indices and similarity scores
 */
export function findTopKSimilar(
  query: number[], 
  vectors: number[][], 
  k: number
): Array<{index: number, similarity: number}> {
  const similarities = vectors.map((vec, index) => ({
    index,
    similarity: cosineSimilarity(query, vec)
  }));
  
  // Sort by similarity in descending order
  similarities.sort((a, b) => b.similarity - a.similarity);
  
  // Return top k results
  return similarities.slice(0, k);
}

/**
 * Compute the average vector from an array of vectors
 * @param vectors Array of vectors to average
 * @returns Average vector
 */
export function averageVectors(vectors: number[][]): number[] {
  if (vectors.length === 0) {
    throw new Error('Cannot average empty array of vectors');
  }
  
  const dimensions = vectors[0].length;
  const result = Array(dimensions).fill(0);
  
  for (const vector of vectors) {
    if (vector.length !== dimensions) {
      throw new Error('All vectors must have the same dimensions');
    }
    
    for (let i = 0; i < dimensions; i++) {
      result[i] += vector[i];
    }
  }
  
  for (let i = 0; i < dimensions; i++) {
    result[i] /= vectors.length;
  }
  
  return result;
}

/**
 * Compute vector operations like addition, subtraction, etc.
 * @param a First vector
 * @param b Second vector
 * @param operation Operation to perform ('add', 'subtract', 'multiply', 'divide')
 * @returns Result vector
 */
export function vectorOperation(
  a: number[], 
  b: number[], 
  operation: 'add' | 'subtract' | 'multiply' | 'divide'
): number[] {
  if (a.length !== b.length) {
    throw new Error('Vectors must have the same dimensions');
  }
  
  const result = Array(a.length).fill(0);
  
  for (let i = 0; i < a.length; i++) {
    switch (operation) {
      case 'add':
        result[i] = a[i] + b[i];
        break;
      case 'subtract':
        result[i] = a[i] - b[i];
        break;
      case 'multiply':
        result[i] = a[i] * b[i];
        break;
      case 'divide':
        if (b[i] === 0) {
          result[i] = 0; // Avoid division by zero
        } else {
          result[i] = a[i] / b[i];
        }
        break;
    }
  }
  
  return result;
}

/**
 * Dimensionality reduction using Principal Component Analysis (PCA)
 * Simple implementation for visualization purposes
 * @param vectors Array of vectors to reduce
 * @param dimensions Target dimensions
 * @returns Reduced vectors
 */
export function simplePCA(
  vectors: number[][], 
  dimensions: number = 2
): number[][] {
  if (vectors.length === 0) {
    return [];
  }
  
  // This is a very simplified PCA implementation
  // For production use, consider using a proper math library
  
  // 1. Center the data
  const mean = averageVectors(vectors);
  const centeredVectors = vectors.map(vec => 
    vectorOperation(vec, mean, 'subtract')
  );
  
  // 2. For simplicity, we'll just use the first N dimensions
  // In a real implementation, you would compute eigenvectors
  return centeredVectors.map(vec => vec.slice(0, dimensions));
}

/**
 * Create a vector cache with LRU eviction policy
 */
export class VectorCache {
  private cache: Map<string, number[]>;
  private maxSize: number;
  
  constructor(maxSize: number = 1000) {
    this.cache = new Map();
    this.maxSize = maxSize;
  }
  
  /**
   * Get a vector from the cache
   * @param key Cache key
   * @returns Vector if found, undefined otherwise
   */
  get(key: string): number[] | undefined {
    const vector = this.cache.get(key);
    
    if (vector) {
      // Update access order (LRU policy)
      this.cache.delete(key);
      this.cache.set(key, vector);
    }
    
    return vector;
  }
  
  /**
   * Store a vector in the cache
   * @param key Cache key
   * @param vector Vector to store
   */
  set(key: string, vector: number[]): void {
    // Evict oldest entry if cache is full
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    
    this.cache.set(key, vector);
  }
  
  /**
   * Check if a key exists in the cache
   * @param key Cache key
   * @returns True if key exists
   */
  has(key: string): boolean {
    return this.cache.has(key);
  }
  
  /**
   * Remove a key from the cache
   * @param key Cache key
   * @returns True if key was found and removed
   */
  delete(key: string): boolean {
    return this.cache.delete(key);
  }
  
  /**
   * Clear the entire cache
   */
  clear(): void {
    this.cache.clear();
  }
  
  /**
   * Get the current size of the cache
   */
  size(): number {
    return this.cache.size;
  }
  
  /**
   * Find similar vectors in the cache
   * @param queryVector Query vector
   * @param threshold Similarity threshold
   * @param limit Maximum number of results
   * @returns Array of keys and similarity scores
   */
  findSimilar(
    queryVector: number[], 
    threshold: number = 0.7, 
    limit: number = 10
  ): Array<{key: string, similarity: number}> {
    const results: Array<{key: string, similarity: number}> = [];
    
    for (const [key, vector] of this.cache.entries()) {
      const similarity = cosineSimilarity(queryVector, vector);
      
      if (similarity >= threshold) {
        results.push({ key, similarity });
      }
    }
    
    // Sort by similarity in descending order
    results.sort((a, b) => b.similarity - a.similarity);
    
    // Return top results
    return results.slice(0, limit);
  }
}
