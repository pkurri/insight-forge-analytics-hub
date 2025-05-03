import { callApi } from '../../utils/apiUtils';
import { ApiResponse } from '../../api';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
}

export interface ChatCompletionRequest {
  sessionId: string;
  message: string;
  context?: {
    datasetId?: string;
    analysisType?: string;
    parameters?: Record<string, any>;
  };
}

export const chatService = {
  /**
   * Get all chat sessions for the current user
   */
  getChatSessions: async (): Promise<ApiResponse<ChatSession[]>> => {
    try {
      return await callApi('chat/sessions');
    } catch (error) {
      console.error('Error fetching chat sessions:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch chat sessions'
      };
    }
  },

  /**
   * Get a specific chat session by ID
   */
  getChatSession: async (sessionId: string): Promise<ApiResponse<ChatSession>> => {
    try {
      return await callApi(`chat/sessions/${sessionId}`);
    } catch (error) {
      console.error('Error fetching chat session:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch chat session'
      };
    }
  },

  /**
   * Create a new chat session
   */
  createChatSession: async (title: string): Promise<ApiResponse<ChatSession>> => {
    try {
      return await callApi('chat/sessions', {
        method: 'POST',
        body: JSON.stringify({ title })
      });
    } catch (error) {
      console.error('Error creating chat session:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to create chat session'
      };
    }
  },

  /**
   * Send a message and get AI completion
   */
  sendMessage: async (request: ChatCompletionRequest): Promise<ApiResponse<ChatMessage>> => {
    try {
      return await callApi('chat/completion', {
        method: 'POST',
        body: JSON.stringify(request)
      });
    } catch (error) {
      console.error('Error sending message:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to send message'
      };
    }
  },

  /**
   * Delete a chat session
   */
  deleteChatSession: async (sessionId: string): Promise<ApiResponse<void>> => {
    try {
      return await callApi(`chat/sessions/${sessionId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error('Error deleting chat session:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to delete chat session'
      };
    }
  }
};
