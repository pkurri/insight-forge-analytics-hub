import apiClient from '../utils/apiClient';

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
    return apiClient.uploadFile('pipeline/upload', {
      file: uploadData.file,
      name: uploadData.name,
      description: uploadData.description || '',
      file_type: uploadData.fileType,
      api_config: uploadData.apiConfig,
      db_config: uploadData.dbConfig,
      user_id: uploadData.userId || 1 // Default to user 1 if not provided
    });
  },

  /**
   * Validate data in the pipeline
   * 
   * @param {string} datasetId - The dataset ID
   * @returns {Promise<Object>} - API response
   */
  async validateData(datasetId) {
    return apiClient.post(`pipeline/step/${datasetId}/validate`);
  },

  /**
   * Apply business rules to a dataset in the pipeline
   * 
   * @param {string} datasetId - The dataset ID
   * @param {Array<string>} ruleIds - Rule IDs to apply
   * @returns {Promise<Object>} - API response
   */
  async applyBusinessRules(datasetId, ruleIds) {
    return apiClient.post(`pipeline/business-rules/${datasetId}`, { rule_ids: ruleIds });
  },

  /**
   * Transform data in the pipeline
   * 
   * @param {string} datasetId - The dataset ID
   * @param {Object} transformConfig - Transform configuration
   * @returns {Promise<Object>} - API response
   */
  async transformData(datasetId, transformConfig = {}) {
    return apiClient.post(`pipeline/transform/${datasetId}`, transformConfig);
  },

  /**
   * Enrich data in the pipeline
   * 
   * @param {string} datasetId - The dataset ID
   * @param {Object} enrichConfig - Enrichment configuration
   * @returns {Promise<Object>} - API response
   */
  async enrichData(datasetId, enrichConfig = {}) {
    return apiClient.post(`pipeline/enrich/${datasetId}`, enrichConfig);
  },

  /**
   * Load data to vector database in the pipeline
   * 
   * @param {string} datasetId - The dataset ID
   * @param {Object} loadConfig - Load configuration with options like chunk_size and overlap
   * @returns {Promise<Object>} - API response
   */
  async loadData(datasetId, loadConfig = {}) {
    return apiClient.post(`pipeline/load_data/${datasetId}`, loadConfig);
  },

  /**
   * Get pipeline status
   * 
   * @param {string} datasetId - The dataset ID
   * @returns {Promise<Object>} - API response
   */
  async getPipelineStatus(datasetId) {
    return apiClient.get(`pipeline/runs/${datasetId}`);
  },

  /**
   * Extract sample data from a file
   * 
   * @param {File} file - The file to extract sample data from
   * @param {number} maxRows - Maximum number of rows to extract
   * @returns {Promise<Object>} - API response with sample data
   */
  async extractSampleData(file, maxRows = 100) {
    return apiClient.uploadFile('pipeline/extract-sample', {
      file,
      max_rows: maxRows
    });
  },
  
  /**
   * Get sample data from a dataset
   * 
   * @param {string} datasetId - The dataset ID
   * @param {number} maxRows - Maximum number of rows to extract
   * @returns {Promise<Object>} - API response with sample data
   */
  async getSampleData(datasetId, maxRows = 100) {
    return apiClient.get(`pipeline/sample/${datasetId}`, { max_rows: maxRows });
  },
  
  /**
   * Run a specific pipeline step
   * 
   * @param {string} datasetId - The dataset ID
   * @param {string} stepType - The step type (validate, transform, enrich, load)
   * @returns {Promise<Object>} - API response
   */
  async runPipelineStep(datasetId, stepType) {
    return apiClient.post(`pipeline/step/${datasetId}/${stepType}`);
  }
};

// Export types for TypeScript support
export const BusinessRule = {};
export const ValidationResult = {};

export default pipelineService;
