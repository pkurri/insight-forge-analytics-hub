
export interface DataSource {
  id: string;
  name: string;
  type: string;
  connection_string?: string;
  credentials?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
  status?: 'active' | 'inactive' | 'error';
}

export interface BusinessRule {
  id: string;
  name: string;
  description?: string;
  condition: string;
  severity: 'low' | 'medium' | 'high';
  datasetId?: string; // For attaching to datasets
  column?: string;
  active: boolean;
  created_at?: string;
  updated_at?: string;
  message?: string;
  confidence?: number;
  model_generated?: boolean;
}

export interface PipelineStatus {
  current_stage: string;
  progress: number;
  status: 'running' | 'completed' | 'failed';
  statusMessage?: string; // Added for message property
}

// ChatSuggestion type for AI Chat
export interface ChatSuggestion {
  id: string;
  text: string;
  category: string;
}

// Adding ApiResponse interface to centralize API response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  status?: number;
}
