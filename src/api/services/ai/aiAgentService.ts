
import { callApi, ApiCallOptions } from '@/utils/apiUtils';

/**
 * AI Agent Service
 * Provides integration with the backend AI agent system
 */

// Types
export interface AIAgent {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface ChatContext {
  systemPromptAddition?: string;
  similarContent?: any[];
  embeddingModel?: string;
  [key: string]: any;
}

export interface ChatRequest {
  query: string;
  modelId?: string;
  agentType?: string;
  datasetId?: string;
  chatHistory?: ChatMessage[];
  context?: ChatContext;
}

export interface ChatResponse {
  answer: string;
  model: string;
  agent: string;
  timestamp: string;
  confidence: number;
  insights: string[];
  sources: string[];
}

export interface StreamingChatResponse {
  type: 'chunk' | 'context' | 'complete' | 'error';
  content: string | any;
  done?: boolean;
}

export interface SuggestionsRequest {
  datasetId?: string;
  category?: string;
}

export interface ChatSuggestion {
  text: string;
  category: string;
}

export interface EvaluationScore {
  [key: string]: number;
}

export interface EvaluationResult {
  id: string;
  type: string;
  timestamp: string;
  query?: string;
  response?: string;
  scores: EvaluationScore;
  average_score: number;
  explanation: string;
  status: string;
  improvement_suggestions?: string[];
}

export interface ImprovedResponseResult {
  success: boolean;
  original_response: string;
  improved_response: string;
  original_evaluation: EvaluationResult;
  improved_evaluation: EvaluationResult;
  improvement_delta: {
    average: number;
    scores: EvaluationScore;
  };
}

export interface UserFeedback {
  rating: number;  // 1-5 scale
  feedback_text?: string;
  improvement_areas?: string[];
  tags?: string[];
}

export interface FeedbackResult {
  success: boolean;
  evaluation_id?: string;
  status?: string;
  improved_response?: string;
  message?: string;
  error?: string;
}

/**
 * Get available AI agents
 * @returns Promise with available agents
 */
async function getAvailableAgents() {
  try {
    return await callApi('ai/agents');
  } catch (error) {
    console.error('Error fetching AI agents:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to fetch AI agents',
      status: 0
    };
  }
}

/**
 * Get a response from an AI agent
 * @param request Chat request parameters
 * @returns Promise with chat response
 */
async function getAgentResponse(request: ChatRequest) {
  try {
    return await callApi('ai/chat', { method: 'POST', body: request });
  } catch (error) {
    console.error('Error getting AI response:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get AI response',
      status: 0
    };
  }
}

/**
 * Get a streaming response from an AI agent
 * @param request Chat request parameters
 * @param onChunk Callback for each chunk of the response
 * @param onComplete Callback when streaming is complete
 * @param onError Callback when an error occurs
 * @returns Promise that resolves when streaming is complete
 */
async function getStreamingResponse(
  request: ChatRequest,
  onChunk: (chunk: string) => void,
  onComplete?: (metadata: any) => void,
  onError?: (error: string) => void
): Promise<void> {
  try {
    // Create URL with API endpoint
    const apiUrl = `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/ai/chat/stream`;
    
    // Make fetch request
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `Server responded with status: ${response.status}`);
    }
    
    // Create event source from response
    const reader = response.body?.getReader();
    
    if (!reader) {
      throw new Error('Failed to get response reader');
    }
    
    // Process chunks
    const decoder = new TextDecoder();
    let buffer = '';
    
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        break;
      }
      
      // Decode chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });
      
      // Process complete SSE messages
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.slice(6);
          
          try {
            const data = JSON.parse(jsonStr) as StreamingChatResponse;
            
            if (data.type === 'error') {
              if (onError) {
                onError(typeof data.content === 'string' ? data.content : 'Unknown error');
              }
              return;
            }
            
            if (data.type === 'chunk') {
              onChunk(data.content as string);
              
              if (data.done && onComplete) {
                onComplete({});
              }
            } else if (data.type === 'complete' && onComplete) {
              onComplete(data.content);
            }
          } catch (e) {
            console.error('Error parsing SSE message:', e);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error in streaming response:', error);
    if (onError) {
      onError(error instanceof Error ? error.message : 'Unknown error');
    }
  }
}

/**
 * Get chat suggestions
 * @param request Suggestions request parameters
 * @returns Promise with chat suggestions
 */
async function getChatSuggestions(request: SuggestionsRequest) {
  try {
    return await callApi('ai/suggestions', { method: 'POST', body: request });
  } catch (error) {
    console.error('Error fetching chat suggestions:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to fetch chat suggestions',
      status: 0
    };
  }
}

/**
 * Evaluate an AI agent's response
 * @param query User query that prompted the response
 * @param response AI generated response to evaluate
 * @param conversationId ID of the conversation (optional)
 * @param messageId ID of the message being evaluated (optional)
 * @param facts List of facts to validate against (optional)
 * @returns Promise with evaluation results
 */
async function evaluateResponse(
  query: string,
  response: string,
  conversationId?: string,
  messageId?: string,
  facts?: any[]
) {
  try {
    return await callApi('ai/evaluate', { 
      method: 'POST', 
      body: {
        query,
        response,
        conversation_id: conversationId,
        message_id: messageId,
        facts
      }
    });
  } catch (error) {
    console.error('Error evaluating response:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to evaluate response',
      status: 0
    };
  }
}

/**
 * Get an improved response based on evaluation feedback
 * @param query User query that prompted the response
 * @param initialResponse Original AI response to improve
 * @param conversationId ID of the conversation (optional)
 * @param evaluationId ID of an existing evaluation (optional)
 * @returns Promise with improved response results
 */
async function getImprovedResponse(
  query: string,
  initialResponse: string,
  conversationId?: string,
  evaluationId?: string
) {
  try {
    return await callApi('ai/improve-response', {
      method: 'POST',
      body: {
        query,
        initial_response: initialResponse,
        conversation_id: conversationId,
        evaluation_id: evaluationId
      }
    });
  } catch (error) {
    console.error('Error getting improved response:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get improved response',
      status: 0
    };
  }
}

/**
 * Submit user feedback for a chat message
 * @param conversationId ID of the conversation
 * @param messageId ID of the message receiving feedback
 * @param feedback User feedback data
 * @returns Promise with feedback processing results
 */
async function submitUserFeedback(
  conversationId: string,
  messageId: string,
  feedback: UserFeedback
) {
  try {
    return await callApi('ai/user-feedback', {
      method: 'POST',
      body: {
        conversation_id: conversationId,
        message_id: messageId,
        rating: feedback.rating,
        feedback_text: feedback.feedback_text,
        improvement_areas: feedback.improvement_areas,
        tags: feedback.tags
      }
    });
  } catch (error) {
    console.error('Error submitting user feedback:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to submit feedback',
      status: 0
    };
  }
}

/**
 * Evaluate insights generated from a conversation
 * @param conversationId ID of the conversation
 * @param insights List of insights to evaluate
 * @returns Promise with evaluation results
 */
async function evaluateInsights(
  conversationId: string,
  insights: string[]
) {
  try {
    return await callApi('ai/evaluate-insights', {
      method: 'POST',
      body: {
        conversation_id: conversationId,
        insights
      }
    });
  } catch (error) {
    console.error('Error evaluating insights:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to evaluate insights',
      status: 0
    };
  }
}

// Export the service
export const aiAgentService = {
  getAvailableAgents,
  getAgentResponse,
  getStreamingResponse,
  getChatSuggestions,
  evaluateResponse,
  getImprovedResponse,
  submitUserFeedback,
  evaluateInsights
};

export default aiAgentService;
