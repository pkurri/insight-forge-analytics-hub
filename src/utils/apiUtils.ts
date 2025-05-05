
/**
 * API Utilities - Helper functions for API calls
 */

// Base URL for Python API services
const PYTHON_API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api' 
  : 'http://localhost:8000/api';

/**
 * API call options interface
 */
export interface ApiCallOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: any;
  headers?: Record<string, string>;
  onUploadProgress?: (progressEvent: any) => void;
}

/**
 * Make an API call to the backend
 */
export const callApi = async (endpoint: string, options: ApiCallOptions = {}): Promise<any> => {
  try {
    const { method = 'GET', body, headers = {}, onUploadProgress } = options;

    const requestOptions: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
    };

    if (body) {
      requestOptions.body = JSON.stringify(body);
    }

    const response = await fetch(`${PYTHON_API_BASE_URL}/${endpoint}`, requestOptions);
    const data = await response.json();

    return {
      success: response.ok,
      data: response.ok ? data : null,
      error: !response.ok ? data.detail || 'API request failed' : null
    };
  } catch (error) {
    console.error(`API error (${endpoint}):`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'An unexpected error occurred'
    };
  }
};
