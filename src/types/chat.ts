
/**
 * Message interface defining the structure of chat messages
 */
export interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string | any;
  metadata?: {
    confidence?: number;
    sources?: string[];
    isError?: boolean;
    processing_time?: number;
    tokens_used?: number;
    embedding_count?: number;
    timestamp?: Date | string;
    modelId?: string;
    insights?: string[];
  };
  timestamp: Date;
}

export interface ChatProps {
  datasetId?: string;
  modelId?: string;
  agentId?: string;
}
