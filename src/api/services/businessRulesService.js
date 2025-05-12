import apiClient from '../utils/apiClient';

/**
 * Business Rules Service
 * 
 * This service provides methods for interacting with the business rules API endpoints.
 */
const businessRulesService = {
  /**
   * Get all business rules for a dataset
   * 
   * @param {string} datasetId - The dataset ID
   * @returns {Promise<Object>} - API response
   */
  async getBusinessRules(datasetId) {
    return apiClient.get('business-rules', { dataset_id: datasetId });
  },

  /**
   * Get a specific business rule by ID
   * 
   * @param {string} ruleId - The rule ID
   * @returns {Promise<Object>} - API response
   */
  async getBusinessRule(ruleId) {
    return apiClient.get(`business-rules/${ruleId}`);
  },

  /**
   * Create a new business rule
   * 
   * @param {Object} ruleData - The rule data
   * @returns {Promise<Object>} - API response
   */
  async createBusinessRule(ruleData) {
    return apiClient.post('business-rules', ruleData);
  },

  /**
   * Update a business rule
   * 
   * @param {string} ruleId - The rule ID
   * @param {Object} ruleData - The updated rule data
   * @returns {Promise<Object>} - API response
   */
  async updateBusinessRule(ruleId, ruleData) {
    return apiClient.put(`business-rules/${ruleId}`, ruleData);
  },

  /**
   * Delete a business rule
   * 
   * @param {string} ruleId - The rule ID
   * @returns {Promise<Object>} - API response
   */
  async deleteBusinessRule(ruleId) {
    return apiClient.delete(`business-rules/${ruleId}`);
  },

  /**
   * Import business rules from JSON
   * 
   * @param {string} datasetId - The dataset ID
   * @param {string} rulesJson - The rules JSON string
   * @returns {Promise<Object>} - API response
   */
  async importBusinessRules(datasetId, rulesJson) {
    return apiClient.post(`business-rules/import/${datasetId}`, { rules_json: rulesJson });
  },

  /**
   * Generate business rules using AI
   * 
   * @param {string} datasetId - The dataset ID
   * @param {Object} columnMeta - Column metadata
   * @param {string} engine - AI engine to use
   * @returns {Promise<Object>} - API response
   */
  async generateBusinessRules(datasetId, columnMeta, engine = 'ai_default') {
    return apiClient.post(`business-rules/generate/${datasetId}`, {
      column_metadata: columnMeta,
      engine
    });
  },

  /**
   * Apply business rules to a dataset
   * 
   * @param {string} datasetId - The dataset ID
   * @param {Array<string>} ruleIds - Rule IDs to apply
   * @returns {Promise<Object>} - API response
   */
  async applyRules(datasetId, ruleIds) {
    return apiClient.post(`pipeline/business-rules/${datasetId}`, { rule_ids: ruleIds });
  },

  /**
   * Test business rules against sample data
   * 
   * @param {string} datasetId - The dataset ID
   * @param {Array<Object>} sampleData - Sample data to test against
   * @param {Array<string>} ruleIds - Rule IDs to test
   * @param {Object} testRule - Optional test rule to evaluate
   * @returns {Promise<Object>} - API response
   */
  async testRulesOnSample(datasetId, sampleData, ruleIds = null, testRule = null) {
    const payload = {
      sample_data: sampleData
    };
    
    if (ruleIds) {
      payload.rule_ids = ruleIds;
    }
    
    if (testRule) {
      payload.test_rule = testRule;
    }
    
    return apiClient.post(`business-rules/test-sample/${datasetId}`, payload);
  },

  /**
   * Get business rule metrics
   * 
   * @param {string} datasetId - The dataset ID
   * @param {string} timePeriod - Time period for metrics
   * @param {Array<string>} ruleIds - Rule IDs to get metrics for
   * @returns {Promise<Object>} - API response
   */
  async getRuleMetrics(datasetId, timePeriod = 'all', ruleIds = null) {
    const params = {
      dataset_id: datasetId,
      time_period: timePeriod
    };
    
    if (ruleIds) {
      params.rule_ids = JSON.stringify(ruleIds);
    }
    
    return apiClient.get('business-rules/metrics', params);
  },

  /**
   * Suggest business rules based on sample data
   * 
   * @param {string} datasetId - The dataset ID
   * @param {Array<Object>} sampleData - Sample data to analyze
   * @param {number} minConfidence - Minimum confidence threshold
   * @returns {Promise<Object>} - API response
   */
  async suggestRules(datasetId, sampleData, minConfidence = 0.7) {
    return apiClient.post(`business-rules/suggest/${datasetId}`, {
      sample_data: sampleData,
      min_confidence: minConfidence
    });
  },

  /**
   * Extract sample data from a dataset
   * 
   * @param {string} datasetId - The dataset ID
   * @param {number} maxRows - Maximum number of rows to extract
   * @returns {Promise<Object>} - API response
   */
  async extractSampleData(datasetId, maxRows = 100) {
    return apiClient.get(`business-rules/extract-sample/${datasetId}`, {
      max_rows: maxRows
    });
  },

  /**
   * Save and apply multiple business rules to a dataset
   * 
   * @param {string} datasetId - The dataset ID
   * @param {Array<Object>} rules - Array of business rule objects to save and apply
   * @returns {Promise<Object>} - API response with created rules and application status
   */
  async saveBusinessRules(datasetId, rules) {
    return apiClient.post(`business-rules/batch/${datasetId}`, { rules });
  }
};

export default businessRulesService;
