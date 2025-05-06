
import { callApi } from '../../utils/apiUtils';
import { ApiResponse } from '../../api';

interface PipelineRunStage {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  start_time?: string;
  end_time?: string;
  details?: Record<string, any>;
}

interface PipelineRun {
  id: string;
  dataset_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  current_stage: string;
  progress: number;
  created_at: string;
  updated_at: string;
  stages: PipelineRunStage[];
}

export interface Dataset {
  id: string;
  name: string;
  description?: string;
  fileType: string;
  status: string;
  recordCount: number;
  columnCount: number;
  createdAt: string;
  updatedAt: string;
  metadata?: Record<string, any>;
}

export const pipelineService = {
  /**
   * Upload data to create a new pipeline
   */
  uploadData: async (formData: FormData, config?: { onUploadProgress?: (progressEvent: any) => void }): Promise<ApiResponse<any>> => {
    try {
      return await callApi('pipeline/upload', {
        method: 'POST',
        body: formData,
        config
      });
    } catch (error) {
      console.error('Error uploading data:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to upload data'
      };
    }
  },

  /**
   * Get available datasets
   */
  getDatasets: async (): Promise<ApiResponse<Dataset[]>> => {
    try {
      return await callApi('datasets');
    } catch (error) {
      console.error('Error fetching datasets:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch datasets',
        data: []
      };
    }
  },

  /**
   * Apply business rules to a dataset
   */
  applyBusinessRules: async (datasetId: string, options?: any): Promise<ApiResponse<any>> => {
    try {
      return await callApi(`pipeline/${datasetId}/apply-rules`, {
        method: 'POST',
        body: JSON.stringify(options || {})
      });
    } catch (error) {
      console.error('Error applying business rules:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to apply business rules'
      };
    }
  },

  /**
   * Get pipeline runs for a specific dataset
   */
  getPipelineRuns: async (datasetId: string): Promise<ApiResponse<PipelineRun[]>> => {
    try {
      return await callApi(`pipeline/runs/${datasetId}`);
    } catch (error) {
      console.error('Error fetching pipeline runs:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch pipeline runs',
        data: []
      };
    }
  },

  /**
   * Get business rules for a dataset
   */
  getBusinessRules: async (datasetId: string): Promise<ApiResponse<any>> => {
    try {
      return await callApi(`datasets/${datasetId}/rules`);
    } catch (error) {
      console.error('Error fetching business rules:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch business rules'
      };
    }
  },

  /**
   * Create a business rule for a dataset
   */
  createBusinessRule: async (datasetId: string, rule: any): Promise<ApiResponse<any>> => {
    try {
      return await callApi(`datasets/${datasetId}/rules`, {
        method: 'POST',
        body: JSON.stringify(rule)
      });
    } catch (error) {
      console.error('Error creating business rule:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to create business rule'
      };
    }
  },

  /**
   * Get business rules validation results for a dataset
   */
  getBusinessRulesResults: async (datasetId: string): Promise<ApiResponse<any>> => {
    try {
      return await callApi(`datasets/${datasetId}/rules/results`);
    } catch (error) {
      console.error('Error fetching business rules results:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch business rules results'
      };
    }
  }
};
