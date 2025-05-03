
import { callApi } from '../../utils/apiUtils';
import { ApiResponse } from '../../api';

export interface SimilaritySearchParams {
  query_embedding?: number[];
  query_text?: string;
  limit?: number;
}

export interface Dataset {
  id: number;
  name: string;
  description?: string;
  fileType: string;
  status: string;
  recordCount: number;
  columnCount: number;
  createdAt: string;
  updatedAt: string;
  metadata?: Record<string, any>;
  embedding?: number[];
}

export const datasetService = {
  /**
   * Get a list of all datasets
   */
  getDatasets: async (): Promise<ApiResponse<Dataset[]>> => {
    try {
      return await callApi('datasets');
    } catch (error) {
      console.error('Error fetching datasets:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch datasets'
      };
    }
  },

  /**
   * Get detailed information about a specific dataset
   */
  getDatasetDetails: async (datasetId: string): Promise<ApiResponse<Dataset>> => {
    try {
      return await callApi(`datasets/${datasetId}`);
    } catch (error) {
      console.error('Error fetching dataset details:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch dataset details'
      };
    }
  },

  /**
   * Search for similar datasets using vector similarity
   */
  searchSimilarDatasets: async (params: SimilaritySearchParams): Promise<ApiResponse<Dataset[]>> => {
    try {
      return await callApi('datasets/search', {
        method: 'POST',
        body: JSON.stringify(params)
      });
    } catch (error) {
      console.error('Error searching similar datasets:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to search datasets'
      };
    }
  },

  /**
   * Get dataset embedding vector
   */
  getDatasetEmbedding: async (datasetId: string): Promise<ApiResponse<{ embedding: number[] }>> => {
    try {
      return await callApi(`datasets/${datasetId}/embedding`);
    } catch (error) {
      console.error('Error fetching dataset embedding:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch dataset embedding'
      };
    }
  },

  /**
   * Upload a new dataset
   */
  uploadDataset: async (formData: FormData): Promise<ApiResponse<Dataset>> => {
    try {
      return await callApi('datasets/upload', {
        method: 'POST',
        body: formData
      });
    } catch (error) {
      console.error('Error uploading dataset:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to upload dataset'
      };
    }
  },

  /**
   * Update an existing dataset
   */
  updateDataset: async (datasetId: string, data: Partial<Dataset>): Promise<ApiResponse<Dataset>> => {
    try {
      return await callApi(`datasets/${datasetId}`, {
        method: 'PUT',
        body: JSON.stringify(data)
      });
    } catch (error) {
      console.error('Error updating dataset:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update dataset'
      };
    }
  },

  /**
   * Delete a dataset
   */
  deleteDataset: async (datasetId: string): Promise<ApiResponse<void>> => {
    try {
      return await callApi(`datasets/${datasetId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error('Error deleting dataset:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to delete dataset'
      };
    }
  }
};
