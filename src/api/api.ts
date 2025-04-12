
import { aiChatService } from './services/ai/aiChatService';
import { datasetService } from './services/datasets/datasetService';
import { userService } from './services/user/userService';
import { analyticsService } from './services/analytics/analyticsService';
import { businessRulesService } from './services/businessRules/businessRulesService';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  status?: number;
}

export interface DatasetSummary {
  id: string;
  name: string;
  rows: number;
  columns: number;
  created_at: string;
  updated_at: string;
  status: 'active' | 'pending' | 'error';
  description?: string;
}

export interface BusinessRule {
  id: string;
  name: string;
  description: string;
  dataset_id: string;
  rule_type: string;
  condition: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  active: boolean;
  created_at: string;
  updated_at: string;
}

// API utilities
export const api = {
  // Dataset operations
  getDatasets: async (): Promise<ApiResponse<DatasetSummary[]>> => {
    return datasetService.getDatasets();
  },
  
  getDatasetDetails: async (id: string): Promise<ApiResponse> => {
    return datasetService.getDatasetDetails(id);
  },
  
  // AI Assistant operations
  getAiAssistantResponse: async (message: string, context?: any): Promise<ApiResponse> => {
    // Integrate with backend API
    try {
      return aiChatService.generateResponse(message, context);
    } catch (error) {
      console.error("Error in AI assistant response:", error);
      return {
        success: false,
        error: "Failed to get AI response"
      };
    }
  },
  
  // Ask question about dataset(s)
  askQuestion: async (datasetId: string, question: string, options?: any): Promise<ApiResponse> => {
    try {
      // If datasetId is 'all', send request to analyze all datasets
      const params = {
        dataset_id: datasetId === 'all' ? undefined : datasetId,
        question,
        ...options
      };
      
      return aiChatService.askQuestion(params);
    } catch (error) {
      console.error("Error asking question:", error);
      return {
        success: false,
        error: "Failed to process question"
      };
    }
  },
  
  // Get available AI models
  getAvailableModels: async (): Promise<ApiResponse> => {
    try {
      return aiChatService.getAvailableModels();
    } catch (error) {
      console.error("Error getting AI models:", error);
      return {
        success: false,
        error: "Failed to get available models"
      };
    }
  },
  
  // Get chat history
  getChatHistory: async (datasetId: string): Promise<ApiResponse> => {
    try {
      return aiChatService.getChatHistory(datasetId);
    } catch (error) {
      console.error("Error getting chat history:", error);
      return {
        success: false,
        error: "Failed to retrieve chat history"
      };
    }
  },
  
  // User and authentication operations
  getCurrentUser: async (): Promise<ApiResponse> => {
    return userService.getCurrentUser();
  },
  
  // Analytics operations
  getDataQuality: async (datasetId: string): Promise<ApiResponse> => {
    return analyticsService.getDataQuality(datasetId);
  },
  
  profileDataset: async (datasetId: string): Promise<ApiResponse> => {
    return analyticsService.profileDataset(datasetId);
  },
  
  cleanData: async (datasetId: string, options: any): Promise<ApiResponse> => {
    return analyticsService.cleanData(datasetId, options);
  },
  
  // Business Rules operations
  saveBusinessRules: async (datasetId: string, rules: any[]): Promise<ApiResponse> => {
    return businessRulesService.saveBusinessRules(datasetId, rules);
  }
};
