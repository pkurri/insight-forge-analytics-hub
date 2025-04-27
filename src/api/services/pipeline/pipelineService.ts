import { callApi } from '../../utils/apiUtils';
import { ApiResponse } from '../../api';

export interface PipelineStatus {
  id: string;
  dataset_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  current_stage: string;
  progress: number;
  error?: string;
  created_at: string;
  updated_at: string;
  stages: {
    name: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    start_time?: string;
    end_time?: string;
    error?: string;
  }[];
}

export const pipelineService = {
  /**
   * Upload data to the pipeline
   */
  uploadData: async (formData: FormData): Promise<ApiResponse<any>> => {
    const endpoint = 'pipeline/upload';
    
    try {
      const response = await callApi(endpoint, {
        method: 'POST',
        body: formData
      });
      return response;
    } catch (error) {
      console.error("Error uploading data:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to upload data"
      };
    }
  },
  
  /**
   * Apply business rules to a dataset
   */
  applyBusinessRules: async (datasetId: string, options: any = {}): Promise<ApiResponse<any>> => {
    const endpoint = `pipeline/${datasetId}/business-rules`;
    
    try {
      const response = await callApi(endpoint, {
        method: 'POST',
        body: JSON.stringify(options)
      });
      return response;
    } catch (error) {
      console.error("Error applying business rules:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to apply business rules"
      };
    }
  },

  /**
   * Get pipeline status
   */
  getPipelineStatus: async (pipelineId: string): Promise<ApiResponse<PipelineStatus>> => {
    const endpoint = `pipeline/status/${pipelineId}`;
    
    try {
      const response = await callApi(endpoint);
      return response;
    } catch (error) {
      console.error("Error getting pipeline status:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to get pipeline status"
      };
    }
  },

  /**
   * Get pipeline runs for a dataset
   */
  getPipelineRuns: async (datasetId: string): Promise<ApiResponse<PipelineStatus[]>> => {
    const endpoint = `pipeline/runs/${datasetId}`;
    
    try {
      const response = await callApi(endpoint);
      return response;
    } catch (error) {
      console.error("Error getting pipeline runs:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to get pipeline runs"
      };
    }
  },

  /**
   * Configure pipeline stages
   */
  configurePipeline: async (datasetId: string, config: any): Promise<ApiResponse<any>> => {
    const endpoint = `pipeline/configure/${datasetId}`;
    
    try {
      const response = await callApi(endpoint, {
        method: 'POST',
        body: JSON.stringify(config)
      });
      return response;
    } catch (error) {
      console.error("Error configuring pipeline:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to configure pipeline"
      };
    }
  },

  /**
   * Run a specific pipeline stage
   */
  runPipelineStage: async (
    datasetId: string,
    stage: string,
    params?: any
  ): Promise<ApiResponse<any>> => {
    const endpoint = `pipeline/steps/${stage}/run`;
    
    try {
      const response = await callApi(endpoint, {
        method: 'POST',
        body: JSON.stringify({
          dataset_id: datasetId,
          params
        })
      });
      return response;
    } catch (error) {
      console.error("Error running pipeline stage:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to run pipeline stage"
      };
    }
  },

  /**
   * Get pipeline stage results
   */
  getPipelineStageResults: async (
    datasetId: string,
    stage: string
  ): Promise<ApiResponse<any>> => {
    const endpoint = `pipeline/results/${datasetId}/${stage}`;
    
    try {
      const response = await callApi(endpoint);
      return response;
    } catch (error) {
      console.error(`Error getting ${stage} results:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : `Failed to get ${stage} results`
      };
    }
  },
  
  /**
   * Get business rules validation results
   */
  getBusinessRulesResults: async (datasetId: string): Promise<ApiResponse<any>> => {
    const endpoint = `pipeline/results/${datasetId}/business-rules`;
    
    try {
      const response = await callApi(endpoint);
      return response;
    } catch (error) {
      console.error("Error getting business rules results:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to get business rules results"
      };
    }
  }
};
