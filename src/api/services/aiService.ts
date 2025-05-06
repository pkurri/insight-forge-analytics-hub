
import { callApi, ApiCallOptions } from '@/utils/apiUtils';
import { ApiResponse } from '@/api/types';

interface ChatRequest {
  message: string;
  context?: {
    dataset_id?: string;
    model_id?: string;
    agent_type?: string;
    context?: any;
  };
}

export const aiService = {
  /**
   * Ask a question about a dataset
   */
  askQuestion: async (datasetId: string, question: string): Promise<ApiResponse<any>> => {
    try {
      const options: ApiCallOptions = {
        method: 'POST',
        body: JSON.stringify({
          dataset_id: datasetId,
          question
        })
      };
      
      return await callApi('ai/ask-question', options);
    } catch (error) {
      console.error("Error asking question:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to ask question"
      };
    }
  },
  
  /**
   * Get response from AI assistant based on a message and context
   */
  getAiAssistantResponse: async (
    message: string, 
    context?: { 
      dataset_id?: string;
      model_id?: string;
      agent_type?: string;
      context?: any;
    }
  ): Promise<ApiResponse<any>> => {
    try {
      const options: ApiCallOptions = {
        method: 'POST',
        body: JSON.stringify({
          message,
          ...context
        })
      };
      
      return await callApi('ai/assistant', options);
    } catch (error) {
      console.error("Error getting AI response:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to get AI response"
      };
    }
  },
  
  /**
   * Analyze anomalies in a dataset
   */
  analyzeAnomalies: async (
    datasetId: string, 
    config?: any
  ): Promise<ApiResponse<any>> => {
    try {
      const options: ApiCallOptions = {
        method: 'POST',
        body: JSON.stringify({
          dataset_id: datasetId,
          config
        })
      };
      
      return await callApi('ai/analyze-anomalies', options);
    } catch (error) {
      console.error("Error analyzing anomalies:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to analyze anomalies"
      };
    }
  },
  
  /**
   * Analyze a dataset using AI
   */
  analyzeDataset: async (
    datasetId: string,
    options?: any
  ): Promise<ApiResponse<any>> => {
    try {
      const apiOptions: ApiCallOptions = {
        method: 'POST',
        body: JSON.stringify({
          dataset_id: datasetId,
          options
        })
      };
      
      return await callApi('ai/analyze-dataset', apiOptions);
    } catch (error) {
      console.error("Error analyzing dataset:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to analyze dataset"
      };
    }
  }
};
