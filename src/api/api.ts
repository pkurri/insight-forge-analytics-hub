// Core AI services
import { modelService } from './services/ai/modelService';
import { embeddingService } from './services/ai/embeddingService';
import { aiAgentService } from './services/ai/aiAgentService';
import { businessRulesService } from './services/businessRules/businessRulesService';
import { aiService } from './services/aiService';

// Analytics and monitoring services
import { analyticsService } from './services/analyticsService';
import { monitoringService } from './services/monitoringService';

// Data validation and processing services
import { validationService } from './services/validationService';
import { datasetService } from './services/datasets/datasetService';
import { taskService } from './services/tasks/taskService';
import { pipelineService } from './services/pipeline/pipelineService';
import { datasourceService } from './services/datasource/datasourceService';

// Export all services for use throughout the application
export { 
  modelService, 
  embeddingService, 
  aiAgentService, 
  businessRulesService, 
  aiService, 
  analyticsService, 
  monitoringService, 
  validationService, 
  datasetService, 
  taskService,
  pipelineService,
  datasourceService
};

/**
 * API Response interface
 * Generic interface used for all API responses
 */
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  status?: number;
}

/**
 * Dataset interface
 * Basic dataset information returned by the API
 */
export interface Dataset {
  id: string;
  name: string;
  rows: number;
  columns?: number;
  updated_at?: string;
  description?: string;
  tags?: string[];
}

/**
 * Call API utility function
 * @param endpoint API endpoint to call
 * @param method HTTP method
 * @param data Request data
 * @returns Promise with API response
 */
/**
 * Core API utility function used by all services
 */
export async function callApi<T = unknown>(
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  data?: unknown
): Promise<ApiResponse<T>> {
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
  const url = `${apiUrl}/${endpoint.startsWith('/') ? endpoint.substring(1) : endpoint}`;
  
  try {
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    };
    
    if (data) {
      options.body = JSON.stringify(data);
    }
    
    const response = await fetch(url, options);
    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('application/json')) {
      const json = await response.json();
      
      if (response.ok) {
        return {
          success: true,
          data: json.data || json,
          status: response.status,
        };
      } else {
        return {
          success: false,
          error: json.error || json.message || 'Unknown error',
          status: response.status,
        };
      }
    } else {
      const text = await response.text();
      
      if (response.ok) {
        return {
          success: true,
          data: text as unknown as T,
          status: response.status,
        };
      } else {
        return {
          success: false,
          error: text || 'Unknown error',
          status: response.status,
        };
      }
    }
  } catch (error) {
    console.error(`API call to ${url} failed:`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
      status: 0,
    };
  }
}

/**
 * Dataset API functions
 */
const datasets = {
  /**
   * Get all datasets
   * @returns Promise with datasets
   */
  getDatasets: async (): Promise<ApiResponse<Dataset[]>> => {
    return callApi<Dataset[]>('datasets');
  },
  
  /**
   * Get a specific dataset
   * @param id Dataset ID
   * @returns Promise with dataset
   */
  getDataset: async (id: string): Promise<ApiResponse<Dataset>> => {
    return callApi<Dataset>(`datasets/${id}`);
  },
  
  /**
   * Get insights for a specific dataset
   * @param id Dataset ID
   * @returns Promise with insights
   */
  getInsights: async (id: string): Promise<ApiResponse<{ insights: Array<Record<string, unknown>> }>> => {
    return callApi<{ insights: Array<Record<string, unknown>> }>(`datasets/${id}/insights`);
  },
  
  /**
   * Generate new insights for a dataset
   * @param id Dataset ID
   * @param options Generation options
   * @returns Promise with task ID
   */
  generateInsights: async (id: string, options: Record<string, unknown> = {}): Promise<ApiResponse<{task_id: string}>> => {
    return callApi<{task_id: string}>(`datasets/${id}/generate-insights`, 'POST', options);
  },
  
  /**
   * Upload a dataset
   * @param file Dataset file
   * @param name Dataset name
   * @returns Promise with upload result
   */
  uploadDataset: async (file: File, name: string): Promise<ApiResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    
    const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
    const url = `${apiUrl}/datasets/upload`;
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });
      
      const json = await response.json();
      
      if (response.ok) {
        return {
          success: true,
          data: json.data || json,
          status: response.status,
        };
      } else {
        return {
          success: false,
          error: json.error || json.message || 'Unknown error',
          status: response.status,
        };
      }
    } catch (error) {
      console.error('Dataset upload failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
        status: 0,
      };
    }
  },
  
  /**
   * Delete a dataset
   * @param id Dataset ID
   * @returns Promise with delete result
   */
  deleteDataset: async (id: string): Promise<ApiResponse> => {
    return callApi(`datasets/${id}`, 'DELETE');
  },
  
  /**
   * Delete a business rule
   * @param datasetId Dataset ID
   * @param ruleId Business rule ID
   * @returns Promise with delete result
   */
  deleteBusinessRule: async (datasetId: string, ruleId: string): Promise<ApiResponse> => {
    return callApi(`datasets/${datasetId}/business-rules/${ruleId}`, 'DELETE');
  },
};

/**
 * AI Assistant API functions
 */
const getAiAssistantResponse = async (
  query: string,
  options?: {
    dataset_id?: string;
    model_id?: string;
    agent_type?: string;
    context?: Record<string, unknown>;
  }
): Promise<ApiResponse<{ response: string; sources?: Array<Record<string, unknown>> }>> => {
  const request = {
    query,
    modelId: options?.model_id,
    agentType: options?.agent_type || 'data_analyst',
    datasetId: options?.dataset_id,
    context: options?.context
  };
  
  return aiAgentService.getAgentResponse(request);
};

/**
 * Export API functions
 */

export const api = {
  aiService,
  analyticsService,
  monitoringService,
  validationService,
  datasourceService,
  modelService,
  embeddingService,
  aiAgentService,
  businessRulesService,
  pipelineService,
  callApi,
  datasets,
  getAiAssistantResponse,
  models: modelService,
  embeddings: embeddingService,
  agents: aiAgentService,
  pipeline: pipelineService,
  datasource: datasourceService,
  datasetService,
  taskService,
  businessRules: businessRulesService,
  
  // Dashboard API
  getDashboardMetrics: async (): Promise<ApiResponse> => {
    return callApi('dashboard/metrics');
  },
  
  // Analytics API
  getDatasetAnalytics: async (datasetId: string): Promise<ApiResponse> => {
    return callApi(`analytics/dataset/${datasetId}`);
  },
  
  getGlobalAnalytics: async (): Promise<ApiResponse> => {
    return callApi('analytics/global');
  },
  
  // Project Evaluation API
  getProjectQualityScores: async (): Promise<ApiResponse> => {
    return callApi('project-eval/scores');
  },
  
  runProjectEvaluation: async (): Promise<ApiResponse> => {
    return callApi('project-eval/all', 'POST');
  },
  
  // OpenEvals Runtime Code Quality API
  evaluateRuntimeComponent: async (componentName: string): Promise<ApiResponse> => {
    return callApi('openevals/runtime/evaluate', 'POST', { component_name: componentName });
  },
  
  showComponentSuggestions: async (componentName: string): Promise<ApiResponse> => {
    return callApi('openevals/runtime/suggestions', 'POST', { component_name: componentName });
  },
  
  applyComponentSuggestions: async (componentName: string, suggestionId: string): Promise<ApiResponse> => {
    return callApi('openevals/runtime/apply', 'POST', { 
      component_name: componentName,
      suggestion_id: suggestionId
    });
  }
};
