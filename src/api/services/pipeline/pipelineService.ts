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
    metadata?: any;
  }[];
  pipeline_metadata?: any;
}

export interface PipelineStep {
  name: string;
  type: string;
  config: any;
  order: number;
}

export const pipelineService = {
  /**
   * Run a dynamic pipeline with user-specified steps
   */
  runDynamicPipeline: async (
    datasetId: string,
    steps: PipelineStep[]
  ): Promise<ApiResponse<any>> => {
    const endpoint = `pipeline/dynamic/run`;
    try {
      const response = await callApi(endpoint, {
        method: 'POST',
        body: JSON.stringify({
          dataset_id: datasetId,
          steps
        })
      });
      return response;
    } catch (error) {
      console.error("Error running dynamic pipeline:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to run dynamic pipeline'
      };
    }
  },

  /**
   * Get OpenEvals evaluations for pipeline steps
   */
  getPipelineStepEvaluations: async (
    datasetId: string,
    stepName: string
  ): Promise<ApiResponse<any>> => {
    const endpoint = `pipeline/evaluations/${datasetId}/${stepName}`;
    try {
      const response = await callApi(endpoint);
      return response;
    } catch (error) {
      console.error("Error getting pipeline step evaluations:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get pipeline step evaluations'
      };
    }
  },

  /**
   * Retry a failed pipeline step
   */
  retryPipelineStep: async (
    datasetId: string,
    stepName: string
  ): Promise<ApiResponse<any>> => {
    const endpoint = `pipeline/steps/${stepName}/retry`;
    try {
      const response = await callApi(endpoint, {
        method: 'POST',
        body: JSON.stringify({ dataset_id: datasetId })
      });
      return response;
    } catch (error) {
      console.error("Error retrying pipeline step:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to retry pipeline step'
      };
    }
  },

  /**
   * Resume a paused pipeline run
   */
  resumePipelineRun: async (
    pipelineId: string
  ): Promise<ApiResponse<any>> => {
    const endpoint = `pipeline/${pipelineId}/resume`;
    try {
      const response = await callApi(endpoint, {
        method: 'POST'
      });
      return response;
    } catch (error) {
      console.error("Error resuming pipeline run:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to resume pipeline run'
      };
    }
  },

  /**
   * Override business rules for a dataset and log the override action
   */
  overrideBusinessRules: async (
    datasetId: string,
    data: { reason?: string; user?: string; violations?: any[] }
  ): Promise<ApiResponse<any>> => {
    const endpoint = `pipeline/${datasetId}/business-rules/override`;
    try {
      const response = await callApi(endpoint, {
        method: 'POST',
        body: JSON.stringify(data)
      });
      return response;
    } catch (error) {
      console.error("Error overriding business rules:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to override business rules'
      };
    }
  },

  /**
   * Upload data to the pipeline
   */
  uploadData: async (formData: FormData, config?: { onUploadProgress?: (progressEvent: any) => void }): Promise<ApiResponse<any>> => {
    const endpoint = 'pipeline/upload';
    try {
      const response = await callApi(endpoint, {
        method: 'POST',
        body: formData,
        onUploadProgress: config?.onUploadProgress
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
  },

  /**
   * Validate data structure and integrity
   */
  validateData: async (datasetId: string): Promise<ApiResponse<any>> => {
    const endpoint = `pipeline/step/${datasetId}/validate`;
    try {
      const response = await callApi(endpoint, {
        method: 'POST'
      });
      return response;
    } catch (error) {
      console.error("Error validating data:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  /**
   * Get sample data from a dataset
   */
  getSampleData: async (datasetId: string, maxRows: number = 100): Promise<ApiResponse<any>> => {
    const endpoint = `pipeline/sample/${datasetId}`;
    try {
      const response = await callApi(endpoint, {
        method: 'GET',
        params: { max_rows: maxRows }
      });
      return response;
    } catch (error) {
      console.error("Error getting sample data:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },
};
