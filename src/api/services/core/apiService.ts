import { ApiResponse } from '../../api';

/**
 * Core API Service - Handles all API calls to the backend
 * Replaces the monolithic pythonIntegration.ts with a modular approach
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

/**
 * Call the API with proper error handling
 * @param endpoint API endpoint to call
 * @param method HTTP method
 * @param data Request data
 * @returns ApiResponse with data or error
 */
export async function callApi<T = any>(
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  data?: any
): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}/${endpoint.startsWith('/') ? endpoint.substring(1) : endpoint}`;
  
  try {
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    };
    
    if (data) {
      options.body = JSON.stringify(data);
    }
    
    const response = await fetch(url, options);
    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('application/json')) {
      const json = await response.json();
      
      if (response.ok) {
        return {
          success: true,
          data: json.data || json,
          status: response.status,
        };
      } else {
        return {
          success: false,
          error: json.error || json.message || 'Unknown error',
          status: response.status,
        };
      }
    } else {
      const text = await response.text();
      
      if (response.ok) {
        return {
          success: true,
          data: text as unknown as T,
          status: response.status,
        };
      } else {
        return {
          success: false,
          error: text || 'Unknown error',
          status: response.status,
        };
      }
    }
  } catch (error) {
    console.error(`API call to ${url} failed:`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
      status: 0,
    };
  }
}

/**
 * Upload a file to the API
 * @param endpoint API endpoint
 * @param file File to upload
 * @param additionalData Additional form data
 * @returns ApiResponse with data or error
 */
export async function uploadFile<T = any>(
  endpoint: string,
  file: File,
  additionalData?: Record<string, any>
): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}/${endpoint.startsWith('/') ? endpoint.substring(1) : endpoint}`;
  
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, typeof value === 'object' ? JSON.stringify(value) : String(value));
      });
    }
    
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      credentials: 'include',
    });
    
    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('application/json')) {
      const json = await response.json();
      
      if (response.ok) {
        return {
          success: true,
          data: json.data || json,
          status: response.status,
        };
      } else {
        return {
          success: false,
          error: json.error || json.message || 'Unknown error',
          status: response.status,
        };
      }
    } else {
      const text = await response.text();
      
      if (response.ok) {
        return {
          success: true,
          data: text as unknown as T,
          status: response.status,
        };
      } else {
        return {
          success: false,
          error: text || 'Unknown error',
          status: response.status,
        };
      }
    }
  } catch (error) {
    console.error(`File upload to ${url} failed:`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
      status: 0,
    };
  }
}

/**
 * Download a file from the API
 * @param endpoint API endpoint
 * @param filename Filename to save as
 * @param method HTTP method
 * @param data Request data
 * @returns ApiResponse with blob or error
 */
export async function downloadFile(
  endpoint: string,
  filename: string,
  method: 'GET' | 'POST' = 'GET',
  data?: any
): Promise<ApiResponse<Blob>> {
  const url = `${API_BASE_URL}/${endpoint.startsWith('/') ? endpoint.substring(1) : endpoint}`;
  
  try {
    const options: RequestInit = {
      method,
      headers: {},
      credentials: 'include',
    };
    
    if (data) {
      options.headers = {
        'Content-Type': 'application/json',
      };
      options.body = JSON.stringify(data);
    }
    
    const response = await fetch(url, options);
    
    if (response.ok) {
      const blob = await response.blob();
      
      // Create download link
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      return {
        success: true,
        data: blob,
        status: response.status,
      };
    } else {
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        const json = await response.json();
        return {
          success: false,
          error: json.error || json.message || 'Unknown error',
          status: response.status,
        };
      } else {
        const text = await response.text();
        return {
          success: false,
          error: text || 'Unknown error',
          status: response.status,
        };
      }
    }
  } catch (error) {
    console.error(`File download from ${url} failed:`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
      status: 0,
    };
  }
}

/**
 * Create a WebSocket connection to the API
 * @param endpoint WebSocket endpoint
 * @param onMessage Message handler
 * @param onOpen Open handler
 * @param onClose Close handler
 * @param onError Error handler
 * @returns WebSocket instance
 */
export function createWebSocket(
  endpoint: string,
  onMessage: (event: MessageEvent) => void,
  onOpen?: (event: Event) => void,
  onClose?: (event: CloseEvent) => void,
  onError?: (event: Event) => void
): WebSocket {
  const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/${endpoint.startsWith('/') ? endpoint.substring(1) : endpoint}`;
  const socket = new WebSocket(wsUrl);
  
  socket.onmessage = onMessage;
  
  if (onOpen) {
    socket.onopen = onOpen;
  }
  
  if (onClose) {
    socket.onclose = onClose;
  }
  
  if (onError) {
    socket.onerror = onError;
  }
  
  return socket;
}
