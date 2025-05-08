/**
 * API Utilities - Helper functions for API calls
 */

// Base URL for Python API services
const PYTHON_API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api' 
  : 'http://localhost:8000/api';

interface ApiCallOptions extends RequestInit {
  onUploadProgress?: (progressEvent: ProgressEvent) => void;
  params?: Record<string, string | number | boolean>;
}

/**
 * Make an API call to the backend
 */
export const callApi = async (endpoint: string, options: ApiCallOptions = {}): Promise<any> => {
  try {
    const defaultOptions: ApiCallOptions = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    };

    // Merge options, but handle headers separately to avoid overwriting
    const mergedOptions: ApiCallOptions = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...(options.headers || {})
      }
    };

    // Don't set Content-Type for FormData
    if (mergedOptions.body instanceof FormData) {
      delete (mergedOptions.headers as Record<string, string>)['Content-Type'];
    }
    
    // Handle query parameters
    let url = `${PYTHON_API_BASE_URL}/${endpoint}`;
    if (options.params) {
      const queryParams = new URLSearchParams();
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value));
        }
      });
      const queryString = queryParams.toString();
      if (queryString) {
        url += `?${queryString}`;
      }
    }

    const response = await fetch(url, mergedOptions);
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
