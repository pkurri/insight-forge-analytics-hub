import api from './api';

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface PipelineStep {
  id: number;
  name: string;
  status: 'completed' | 'in-progress' | 'pending' | 'error';
  type: string;
  params?: Record<string, any>;
}

export interface PipelineStatus {
  id: string;
  status: 'running' | 'completed' | 'failed' | 'queued' | 'pending';
  current_stage: string;
  progress: number;
  created_at: string;
  updated_at: string;
  steps: PipelineStep[];
}

export const pipelineService = {
  getPipelineRuns: async (datasetId: string): Promise<ApiResponse<PipelineStatus[]>> => {
    try {
      const response = await api.get(`/pipeline/runs?dataset_id=${datasetId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch pipeline runs'
      };
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

  // ... rest of existing code ...
}; 