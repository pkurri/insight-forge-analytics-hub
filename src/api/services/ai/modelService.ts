import { callApi } from '../../utils/apiUtils';
import { ApiResponse } from '../../api';

export interface AIModel {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  contextWindow: number;
  maxTokens: number;
  provider: 'huggingface' | 'openai' | 'anthropic' | 'custom';
  type: 'chat' | 'embedding' | 'specialized';
}

/**
 * Model Service - Handles AI model operations
 * with focus on Hugging Face models for agentic AI
 */
export const modelService = {
  /**
   * Get available AI models for the assistant
   */
  getAvailableModels: async (modelType?: string): Promise<ApiResponse<AIModel[]>> => {
    const endpoint = `ai/models${modelType ? `?model_type=${modelType}` : ''}`;
    
    try {
      const response = await callApi(endpoint);
      
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      return {
        success: true,
        data: [
          {
            id: "mistral-7b-instruct",
            name: "Mistral 7B Instruct",
            description: "Excellent instruction-following capabilities",
            capabilities: ["chat", "reasoning", "planning"],
            contextWindow: 8192,
            maxTokens: 2048,
            provider: "huggingface",
            type: "chat"
          },
          {
            id: "llama-3-8b",
            name: "Llama 3 8B",
            description: "Strong reasoning and planning abilities",
            capabilities: ["chat", "reasoning", "planning", "code"],
            contextWindow: 8192,
            maxTokens: 2048,
            provider: "huggingface",
            type: "chat"
          },
          {
            id: "falcon-40b-instruct",
            name: "Falcon 40B Instruct",
            description: "Good for complex reasoning tasks",
            capabilities: ["chat", "reasoning", "planning"],
            contextWindow: 4096,
            maxTokens: 1024,
            provider: "huggingface",
            type: "chat"
          },
          {
            id: "sentence-transformers/all-MiniLM-L6-v2",
            name: "MiniLM L6 v2",
            description: "Lightweight, general-purpose embeddings",
            capabilities: ["embeddings", "search"],
            contextWindow: 512,
            maxTokens: 512,
            provider: "huggingface",
            type: "embedding"
          },
          {
            id: "BAAI/bge-large-en-v1.5",
            name: "BGE Large v1.5",
            description: "State-of-the-art for retrieval tasks",
            capabilities: ["embeddings", "search", "retrieval"],
            contextWindow: 512,
            maxTokens: 512,
            provider: "huggingface",
            type: "embedding"
          },
          {
            id: "intfloat/e5-large-v2",
            name: "E5 Large v2",
            description: "Excellent for question-answering",
            capabilities: ["embeddings", "qa"],
            contextWindow: 512,
            maxTokens: 512,
            provider: "huggingface",
            type: "embedding"
          },
          {
            id: "Salesforce/blip2-opt-2.7b",
            name: "BLIP2 OPT 2.7B",
            description: "For image understanding",
            capabilities: ["vision", "image-to-text"],
            contextWindow: 1024,
            maxTokens: 512,
            provider: "huggingface",
            type: "specialized"
          },
          {
            id: "facebook/bart-large-xsum",
            name: "BART Large XSum",
            description: "For summarization",
            capabilities: ["summarization"],
            contextWindow: 1024,
            maxTokens: 512,
            provider: "huggingface",
            type: "specialized"
          },
          {
            id: "deepset/roberta-base-squad2",
            name: "RoBERTa Base SQuAD2",
            description: "For extractive QA",
            capabilities: ["qa", "extraction"],
            contextWindow: 512,
            maxTokens: 512,
            provider: "huggingface",
            type: "specialized"
          }
        ]
      };
    } catch (error) {
      console.error("Error fetching models:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to fetch models"
      };
    }
  },

  /**
   * Get model details by ID
   */
  getModelById: async (modelId: string): Promise<ApiResponse<AIModel>> => {
    const endpoint = `ai/models/${modelId}`;
    
    try {
      const response = await callApi(endpoint);
      
      if (response.success) {
        return response;
      }
      
      // Fallback to getting all models and filtering
      const allModelsResponse = await modelService.getAvailableModels();
      if (allModelsResponse.success && allModelsResponse.data) {
        const model = allModelsResponse.data.find(m => m.id === modelId);
        if (model) {
          return {
            success: true,
            data: model
          };
        }
      }
      
      return {
        success: false,
        error: `Model with ID ${modelId} not found`
      };
    } catch (error) {
      console.error(`Error fetching model ${modelId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : `Failed to fetch model ${modelId}`
      };
    }
  }
};
