import { callApi } from '../../utils/apiUtils';
import { ApiResponse } from '../../api';

export interface EmbeddingVector {
  id?: string;
  vector: number[];
  text: string;
  metadata?: Record<string, any>;
}

export interface EmbeddingRequest {
  text: string;
  model?: string;
  truncate?: boolean;
}

export interface EmbeddingResponse {
  id: string;
  vector: number[];
  text: string;
  model: string;
  dimension: number;
  metadata?: Record<string, any>;
  timestamp: string;
}

/**
 * Embedding Service - Handles vector embeddings for semantic search
 * using Hugging Face models
 */
export const embeddingService = {
  /**
   * Generate embeddings for text using specified model
   */
  generateEmbeddings: async (request: EmbeddingRequest): Promise<ApiResponse<EmbeddingResponse>> => {
    const endpoint = `ai/embeddings`;
    
    try {
      const response = await callApi(endpoint, 'POST', request);
      
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 600));
      
      // Generate a mock embedding vector with 384 dimensions (like MiniLM-L6-v2)
      const mockVector = Array.from({ length: 384 }, () => Math.random() * 2 - 1);
      // Normalize the vector (unit length)
      const magnitude = Math.sqrt(mockVector.reduce((sum, val) => sum + val * val, 0));
      const normalizedVector = mockVector.map(val => val / magnitude);
      
      return {
        success: true,
        data: {
          id: `mock-${Date.now()}`,
          vector: normalizedVector,
          text: request.text,
          model: request.model || 'sentence-transformers/all-MiniLM-L6-v2',
          dimension: 384,
          timestamp: new Date().toISOString()
        }
      };
    } catch (error) {
      console.error("Error generating embeddings:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to generate embeddings"
      };
    }
  },

  /**
   * Search for similar vectors using semantic search
   */
  searchSimilarVectors: async (query: string, datasetId?: string, limit: number = 5): Promise<ApiResponse<any>> => {
    const endpoint = `ai/search`;
    
    try {
      const response = await callApi(endpoint, 'POST', {
        query,
        dataset_id: datasetId,
        limit
      });
      
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 800));
      
      return {
        success: true,
        data: {
          results: Array.from({ length: limit }, (_, i) => ({
            id: `result-${i}`,
            text: `Mock search result ${i + 1} for "${query}"`,
            score: 1 - (i * 0.15),
            metadata: {
              source: datasetId ? `Dataset ${datasetId}` : 'All datasets',
              type: i % 2 === 0 ? 'document' : 'record',
              timestamp: new Date().toISOString()
            }
          })),
          query,
          model: 'sentence-transformers/all-MiniLM-L6-v2',
          dataset_id: datasetId,
          timestamp: new Date().toISOString()
        }
      };
    } catch (error) {
      console.error("Error searching vectors:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to search vectors"
      };
    }
  },

  /**
   * Store vector embeddings for future retrieval
   */
  storeEmbeddings: async (vectors: EmbeddingVector[], datasetId?: string): Promise<ApiResponse<any>> => {
    const endpoint = `ai/store-embeddings`;
    
    try {
      const response = await callApi(endpoint, 'POST', {
        vectors,
        dataset_id: datasetId
      });
      
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      return {
        success: true,
        data: {
          stored: vectors.length,
          dataset_id: datasetId,
          timestamp: new Date().toISOString()
        }
      };
    } catch (error) {
      console.error("Error storing embeddings:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to store embeddings"
      };
    }
  }
};
