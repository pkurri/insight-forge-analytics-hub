import axios from 'axios';
import { API_BASE_URL } from '../../config/constants';

/**
 * Pipeline Service
 * 
 * This service provides methods for interacting with the pipeline API endpoints.
 */
const pipelineService = {
  /**
   * Upload data to the pipeline
   * 
   * @param {Object} uploadData - The upload data
   * @returns {Promise<Object>} - API response
   */
  async uploadData(uploadData) {
    try {
      const formData = new FormData();
      
      // Add file if present
      if (uploadData.file) {
        formData.append('file', uploadData.file);
      }
      
      // Add metadata
      formData.append('name', uploadData.name);
      formData.append('description', uploadData.description || '');
      formData.append('file_type', uploadData.fileType);
      
      // Add API config if present
      if (uploadData.apiConfig) {
        formData.append('api_config', JSON.stringify(uploadData.apiConfig));
      }
      
      // Add DB config if present
      if (uploadData.dbConfig) {
        formData.append('db_config', JSON.stringify(uploadData.dbConfig));
      }
      
      const response = await axios.post(`${API_BASE_URL}/pipeline/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      return response.data;
    } catch (error) {
      console.error('Error uploading data:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to upload data'
      };
    }
  },

  /**
   * Validate data in the pipeline
   * 
   * @param {string} datasetId - The dataset ID
   * @returns {Promise<Object>} - API response
   */
  async validateData(datasetId) {
    try {
      const response = await axios.post(`${API_BASE_URL}/pipeline/validate/${datasetId}`);
      return response.data;
    } catch (error) {
      console.error('Error validating data:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to validate data'
      };
    }
  },

  /**
   * Apply business rules to a dataset in the pipeline
   * 
   * @param {string} datasetId - The dataset ID
   * @param {Array<string>} ruleIds - Rule IDs to apply
   * @returns {Promise<Object>} - API response
   */
  async applyBusinessRules(datasetId, ruleIds) {
    try {
      const response = await axios.post(`${API_BASE_URL}/pipeline/apply-rules/${datasetId}`, {
        rule_ids: ruleIds
      });
      return response.data;
    } catch (error) {
      console.error('Error applying business rules:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to apply business rules'
      };
    }
  },

  /**
   * Transform data in the pipeline
   * 
   * @param {string} datasetId - The dataset ID
   * @param {Object} transformConfig - Transform configuration
   * @returns {Promise<Object>} - API response
   */
  async transformData(datasetId, transformConfig) {
    try {
      const response = await axios.post(`${API_BASE_URL}/pipeline/transform/${datasetId}`, transformConfig);
      return response.data;
    } catch (error) {
      console.error('Error transforming data:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to transform data'
      };
    }
  },

  /**
   * Enrich data in the pipeline
   * 
   * @param {string} datasetId - The dataset ID
   * @param {Object} enrichConfig - Enrichment configuration
   * @returns {Promise<Object>} - API response
   */
  async enrichData(datasetId, enrichConfig) {
    try {
      const response = await axios.post(`${API_BASE_URL}/pipeline/enrich/${datasetId}`, enrichConfig);
      return response.data;
    } catch (error) {
      console.error('Error enriching data:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to enrich data'
      };
    }
  },

  /**
   * Load data to destination in the pipeline
   * 
   * @param {string} datasetId - The dataset ID
   * @param {Object} loadConfig - Load configuration
   * @returns {Promise<Object>} - API response
   */
  async loadData(datasetId, loadConfig) {
    try {
      const response = await axios.post(`${API_BASE_URL}/pipeline/load/${datasetId}`, loadConfig);
      return response.data;
    } catch (error) {
      console.error('Error loading data:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to load data'
      };
    }
  },

  /**
   * Get pipeline status
   * 
   * @param {string} datasetId - The dataset ID
   * @returns {Promise<Object>} - API response
   */
  async getPipelineStatus(datasetId) {
    try {
      const response = await axios.get(`${API_BASE_URL}/pipeline/status/${datasetId}`);
      return response.data;
    } catch (error) {
      console.error('Error getting pipeline status:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to get pipeline status'
      };
    }
  },

  /**
   * Extract sample data from a file
   * 
   * @param {File} file - The file to extract sample data from
   * @param {number} maxRows - Maximum number of rows to extract
   * @returns {Promise<Object>} - API response with sample data
   */
  async extractSampleData(file, maxRows = 100) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('max_rows', maxRows);
      
      const response = await axios.post(`${API_BASE_URL}/pipeline/extract-sample`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      return response.data;
    } catch (error) {
      console.error('Error extracting sample data:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to extract sample data'
      };
    }
  }
};

// Export types for TypeScript support
export const BusinessRule = {};
export const ValidationResult = {};

export default pipelineService;
