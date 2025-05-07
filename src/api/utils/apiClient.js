/**
 * API Client - Unified API calling mechanism
 * 
 * This module provides a unified way to make API calls to the backend,
 * handling common patterns like error handling, request formatting, etc.
 */

import { callApi } from './apiUtils';

/**
 * Create a form data object from an object
 * @param {Object} data - The data to convert to form data
 * @returns {FormData} - The form data object
 */
const createFormData = (data) => {
  const formData = new FormData();
  
  Object.entries(data).forEach(([key, value]) => {
    // Handle file objects
    if (value instanceof File) {
      formData.append(key, value);
    } 
    // Handle arrays and objects by stringifying them
    else if (typeof value === 'object' && value !== null) {
      formData.append(key, JSON.stringify(value));
    } 
    // Handle primitive values
    else if (value !== undefined && value !== null) {
      formData.append(key, value.toString());
    }
  });
  
  return formData;
};

/**
 * API Client for making standardized API calls
 */
const apiClient = {
  /**
   * Make a GET request
   * @param {string} endpoint - API endpoint
   * @param {Object} params - Query parameters
   * @returns {Promise<Object>} - API response
   */
  async get(endpoint, params = {}) {
    // Convert params to query string
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.append(key, value.toString());
      }
    });
    
    const queryString = queryParams.toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    
    return callApi(url);
  },
  
  /**
   * Make a POST request with JSON data
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request data
   * @returns {Promise<Object>} - API response
   */
  async post(endpoint, data = {}) {
    return callApi(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
  },
  
  /**
   * Make a POST request with form data
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Form data
   * @returns {Promise<Object>} - API response
   */
  async postForm(endpoint, data = {}) {
    const formData = createFormData(data);
    
    return callApi(endpoint, {
      method: 'POST',
      body: formData,
    });
  },
  
  /**
   * Make a PUT request
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request data
   * @returns {Promise<Object>} - API response
   */
  async put(endpoint, data = {}) {
    return callApi(endpoint, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
  },
  
  /**
   * Make a DELETE request
   * @param {string} endpoint - API endpoint
   * @returns {Promise<Object>} - API response
   */
  async delete(endpoint) {
    return callApi(endpoint, {
      method: 'DELETE',
    });
  },
  
  /**
   * Upload a file with additional data
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Data including file and other fields
   * @param {Function} onProgress - Progress callback
   * @returns {Promise<Object>} - API response
   */
  async uploadFile(endpoint, data, onProgress) {
    const formData = createFormData(data);
    
    return callApi(endpoint, {
      method: 'POST',
      body: formData,
      onUploadProgress: onProgress,
    });
  }
};

export default apiClient;
