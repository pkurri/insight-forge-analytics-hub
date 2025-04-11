
/**
 * API Utilities - Helper functions for API calls
 */

// Base URL for Python API services
const PYTHON_API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api' 
  : 'http://localhost:8000/api';

/**
 * Make an API call to the backend
 */
export const callApi = async (endpoint: string, method: string = 'GET', body?: any): Promise<any> => {
  try {
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(`${PYTHON_API_BASE_URL}/${endpoint}`, options);
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

/**
 * Upload a file to the backend
 */
export const uploadFile = async (endpoint: string, file: File, params: Record<string, string> = {}): Promise<any> => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    // Add any additional parameters
    Object.entries(params).forEach(([key, value]) => {
      formData.append(key, value);
    });

    const response = await fetch(`${PYTHON_API_BASE_URL}/${endpoint}`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    return {
      success: response.ok,
      data: response.ok ? data : null,
      error: !response.ok ? data.detail || 'File upload failed' : null
    };
  } catch (error) {
    console.error(`Upload error (${endpoint}):`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'An unexpected error occurred during upload'
    };
  }
};
