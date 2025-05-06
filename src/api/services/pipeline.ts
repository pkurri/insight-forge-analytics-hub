import api from './api';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface PipelineStep {
  id: number;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
}

export interface PipelineStatus {
  id: number;
  dataset_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  steps: PipelineStep[];
  created_at: string;
  updated_at: string;
}

export interface BusinessRule {
  id: number;
  name: string;
  description: string;
  condition: string;
  severity: 'warning' | 'error';
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  rule_results: {
    rule_id: number;
    passed: boolean;
    message: string;
  }[];
}

export interface PipelineService {
  runDynamicPipeline: (datasetId: string, steps: PipelineStep[]) => Promise<ApiResponse<any>>;
  getPipelineStepEvaluations: (datasetId: string, stepName: string) => Promise<ApiResponse<any>>;
  getPipelineEvaluations: (datasetId: string) => Promise<ApiResponse<any>>;
  getPipelineStatus: (runId: string) => Promise<ApiResponse<any>>;
  retryFailedSteps: (runId: string) => Promise<ApiResponse<any>>;
  resumePipeline: (runId: string) => Promise<ApiResponse<any>>;
  getPipelineRun: (runId: string) => Promise<ApiResponse<any>>;
  listPipelineRuns: (datasetId?: string) => Promise<ApiResponse<any>>;
  uploadData: (file: File, fileType: string, name: string, description: string) => Promise<ApiResponse<{ dataset_id: string }>>;
  fetchFromApi: (apiEndpoint: string, outputFormat: string, authConfig?: any) => Promise<ApiResponse<any>>;
  fetchFromDatabase: (connectionId: string, query?: string, tableName?: string, outputFormat?: string) => Promise<ApiResponse<any>>;
  validateData: (datasetId: string) => Promise<ApiResponse<ValidationResult>>;
  applyBusinessRules: (datasetId: string, rules: BusinessRule[]) => Promise<ApiResponse<ValidationResult>>;
  transformData: (datasetId: string) => Promise<ApiResponse<any>>;
  enrichData: (datasetId: string) => Promise<ApiResponse<any>>;
  loadData: (datasetId: string) => Promise<ApiResponse<any>>;
  getPipelineRuns: (datasetId: string) => Promise<ApiResponse<PipelineStatus[]>>;
  runPipelineStep: (stepId: number) => Promise<ApiResponse<any>>;
}

export const pipelineService = {
  getPipelineRuns: async (datasetId: string): Promise<ApiResponse<PipelineStatus[]>> => {
    try {
      const response = await api.get(`/api/pipeline/${datasetId}/runs`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Failed to get pipeline runs' };
    }
  },

  runPipelineStep: async (stepId: number): Promise<ApiResponse<any>> => {
    try {
      const response = await api.post(`/pipeline/steps/${stepId}/run`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to run pipeline step'
      };
    }
  },

  uploadData: async (file: File, fileType: string, name: string, description: string): Promise<ApiResponse<{ dataset_id: string }>> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', fileType);
    formData.append('name', name);
    formData.append('description', description);
    
    try {
      const response = await api.post('/api/pipeline/upload', formData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Failed to upload file' };
    }
  },

  validateData: async (datasetId: string): Promise<ApiResponse<ValidationResult>> => {
    try {
      const response = await api.post(`/api/pipeline/${datasetId}/validate`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Failed to validate data' };
    }
  },

  applyBusinessRules: async (datasetId: string, rules: BusinessRule[]): Promise<ApiResponse<ValidationResult>> => {
    try {
      const response = await api.post(`/api/pipeline/${datasetId}/business-rules`, { rules });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Failed to apply business rules' };
    }
  },

  transformData: async (datasetId: string): Promise<ApiResponse<any>> => {
    try {
      const response = await api.post(`/api/pipeline/${datasetId}/transform`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Failed to transform data' };
    }
  },

  enrichData: async (datasetId: string): Promise<ApiResponse<any>> => {
    try {
      const response = await api.post(`/api/pipeline/${datasetId}/enrich`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Failed to enrich data' };
    }
  },

  loadData: async (datasetId: string): Promise<ApiResponse<any>> => {
    try {
      const response = await api.post(`/api/pipeline/${datasetId}/load`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Failed to load data' };
    }
  },

  getPipelineStatus: async (datasetId: string): Promise<ApiResponse<PipelineStatus>> => {
    try {
      const response = await api.get(`/api/pipeline/${datasetId}/status`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Failed to get pipeline status' };
    }
  },

  getPipelineStepEvaluations: async (datasetId: string): Promise<ApiResponse<any>> => {
    try {
      const response = await api.get(`/api/pipeline/${datasetId}/evaluations`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Failed to get pipeline evaluations' };
    }
  }
}; 