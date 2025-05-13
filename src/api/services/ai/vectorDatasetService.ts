import { ApiResponse } from '../../api';
import { callApi } from '../../utils/apiUtils';

/**
 * Vector Dataset Service
 * Provides integration with the backend vector database system
 */

// Types
export interface VectorizedDataset {
  id: string;
  name: string;
  record_count: number;
  column_count: number;
  vectorized: boolean;
  embedding_model?: string;
  last_updated: string;
}

/**
 * Get a list of datasets that have been vectorized and can be used for semantic search
 * @returns Promise with vectorized datasets
 */
export const getVectorizedDatasets = async (): Promise<ApiResponse<VectorizedDataset[]>> => {
  try {
    const response = await callApi('ai/vectorized-datasets');
    
    return response;
  } catch (error) {
    console.error('Error fetching vectorized datasets:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
};

// Export the service
export const vectorDatasetService = {
  getVectorizedDatasets
};
