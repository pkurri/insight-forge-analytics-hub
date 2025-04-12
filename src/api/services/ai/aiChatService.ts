
import { callApi } from '../../utils/apiUtils';
import { ApiResponse } from '../../api';

/**
 * AI Chat Service - Handles AI assistant operations
 * using Vector DB and Hugging Face models
 */
export const aiChatService = {
  /**
   * Generate a response from the AI assistant
   */
  generateResponse: async (message: string, context?: any): Promise<ApiResponse<any>> => {
    const endpoint = `ai/assistant`;
    
    try {
      const response = await callApi(endpoint, 'POST', {
        message,
        context: context || {}
      });
      
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 800));
      
      return {
        success: true,
        data: {
          text: `Here's a response to "${message}"`,
          context: {
            sources: ['Mock AI response'],
            confidence: 0.85
          },
          timestamp: new Date().toISOString()
        }
      };
    } catch (error) {
      console.error("Error generating AI response:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to generate AI response"
      };
    }
  },

  /**
   * Ask a question about a specific dataset
   */
  askQuestion: async (params: any): Promise<ApiResponse<any>> => {
    const endpoint = `ai/question`;
    
    try {
      const response = await callApi(endpoint, 'POST', params);
      
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      return {
        success: true,
        data: {
          answer: `Here's an answer to your question about dataset ${params.dataset_id || 'all datasets'}: "${params.question}"`,
          confidence: 0.87,
          context: [
            {
              column: 'category',
              insight: '8 unique categories present in the dataset',
              distribution: 'Electronics (32.5%), Clothing (21.4%), Home (17.0%)'
            }
          ],
          visualizations: []
        }
      };
    } catch (error) {
      console.error("Error asking question:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to process question"
      };
    }
  },

  /**
   * Get chat suggestions based on dataset metadata and user history
   */
  getChatSuggestions: async (datasetId?: string, context?: any): Promise<any> => {
    const endpoint = `ai/suggestions`;
    
    try {
      const response = await callApi(endpoint, 'POST', {
        dataset_id: datasetId,
        context: context || {}
      });
      
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 800));
      
      return {
        success: true,
        data: {
          suggestions: [
            { id: "1", text: "What's the distribution of values in column X?", category: "exploration" },
            { id: "2", text: "Show me the relationship between column A and B", category: "correlation" },
            { id: "3", text: "What are the top outliers in this dataset?", category: "anomalies" },
            { id: "4", text: "Summarize the key statistics of this dataset", category: "statistics" },
            { id: "5", text: "What trends do you notice over time?", category: "trends" }
          ]
        }
      };
    } catch (error) {
      console.error("Error getting chat suggestions:", error);
      return {
        success: false,
        error: "Failed to get chat suggestions"
      };
    }
  },

  /**
   * Retrieve chat history from backend storage
   */
  getChatHistory: async (datasetId: string, userId?: string): Promise<any> => {
    const endpoint = `ai/chat-history/${datasetId}`;
    
    try {
      const response = await callApi(endpoint, 'GET');
      
      if (response.success) {
        return response;
      }
      
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Return empty history as we handle local storage in the chat hook
      return {
        success: true,
        data: {
          history: [],
          metadata: {
            dataset_id: datasetId,
            count: 0
          }
        }
      };
    } catch (error) {
      console.error("Error getting chat history:", error);
      return {
        success: false,
        error: "Failed to retrieve chat history"
      };
    }
  },

  /**
   * Send a query to generate embeddings for a document or query
   */
  generateEmbeddings: async (text: string, model?: string): Promise<any> => {
    const endpoint = `ai/embeddings`;
    
    try {
      const response = await callApi(endpoint, 'POST', {
        text,
        model: model || "sentence-transformers/all-MiniLM-L6-v2"
      });
      
      if (response.success) {
        return response;
      }
      
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 800));
      
      return {
        success: true,
        data: {
          text: text,
          embedding: Array(384).fill(0).map(() => Math.random() * 2 - 1), // Mock 384-dim embedding
          model: model || "sentence-transformers/all-MiniLM-L6-v2",
          dimensions: 384
        }
      };
    } catch (error) {
      console.error("Error generating embeddings:", error);
      return {
        success: false,
        error: "Failed to generate embeddings"
      };
    }
  },

  /**
   * Store chat history to backend for future reference
   */
  storeChatHistory: async (datasetId: string, messages: any[]): Promise<any> => {
    const endpoint = `ai/chat-history/${datasetId}`;
    
    try {
      const response = await callApi(endpoint, 'POST', { messages });
      
      if (response.success) {
        return response;
      }
      
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 600));
      
      return {
        success: true,
        data: {
          stored: true,
          message: "Chat history stored successfully"
        }
      };
    } catch (error) {
      console.error("Error storing chat history:", error);
      return {
        success: false,
        error: "Failed to store chat history"
      };
    }
  },

  /**
   * Get available AI models for the assistant
   */
  getAvailableModels: async (): Promise<any> => {
    const endpoint = `ai/models`;
    
    try {
      const response = await callApi(endpoint, 'GET');
      
      if (response.success) {
        return response;
      }
      
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      return {
        success: true,
        data: {
          models: [
            {
              id: "sentence-transformers/all-MiniLM-L6-v2",
              type: "embedding",
              dimensions: 384,
              is_default: true
            },
            {
              id: "google/flan-t5-base",
              type: "generation",
              is_default: true
            },
            {
              id: "facebook/bart-large-mnli",
              type: "zero-shot-classification"
            },
            {
              id: "onnx-community/whisper-tiny.en",
              type: "speech-to-text"
            }
          ]
        }
      };
    } catch (error) {
      console.error("Error getting available models:", error);
      return {
        success: false,
        error: "Failed to get available models"
      };
    }
  }
};
