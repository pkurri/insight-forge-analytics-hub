import axios from 'axios';
import { API_BASE_URL } from '../../config/constants';

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
    try {
      const response = await axios.get(`${API_BASE_URL}/business-rules?dataset_id=${datasetId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching business rules:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch business rules'
      };
    }
  },

  /**
   * Get a specific business rule by ID
   * 
   * @param {string} ruleId - The rule ID
   * @returns {Promise<Object>} - API response
   */
  async getBusinessRule(ruleId) {
    try {
      const response = await axios.get(`${API_BASE_URL}/business-rules/${ruleId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching business rule:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch business rule'
      };
    }
  },

  /**
   * Create a new business rule
   * 
   * @param {Object} ruleData - The rule data
   * @returns {Promise<Object>} - API response
   */
  async createBusinessRule(ruleData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/business-rules`, ruleData);
      return response.data;
    } catch (error) {
      console.error('Error creating business rule:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to create business rule'
      };
    }
  },

  /**
   * Update a business rule
   * 
   * @param {string} ruleId - The rule ID
   * @param {Object} ruleData - The updated rule data
   * @returns {Promise<Object>} - API response
   */
  async updateBusinessRule(ruleId, ruleData) {
    try {
      const response = await axios.put(`${API_BASE_URL}/business-rules/${ruleId}`, ruleData);
      return response.data;
    } catch (error) {
      console.error('Error updating business rule:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to update business rule'
      };
    }
  },

  /**
   * Delete a business rule
   * 
   * @param {string} ruleId - The rule ID
   * @returns {Promise<Object>} - API response
   */
  async deleteBusinessRule(ruleId) {
    try {
      const response = await axios.delete(`${API_BASE_URL}/business-rules/${ruleId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting business rule:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to delete business rule'
      };
    }
  },

  /**
   * Import business rules from JSON
   * 
   * @param {string} datasetId - The dataset ID
   * @param {string} rulesJson - The rules JSON string
   * @returns {Promise<Object>} - API response
   */
  async importBusinessRules(datasetId, rulesJson) {
    try {
      const response = await axios.post(`${API_BASE_URL}/business-rules/import/${datasetId}`, {
        rules_json: rulesJson
      });
      return response.data;
    } catch (error) {
      console.error('Error importing business rules:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to import business rules'
      };
    }
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
    try {
      const response = await axios.post(`${API_BASE_URL}/business-rules/generate/${datasetId}?engine=${engine}`, columnMeta);
      return response.data;
    } catch (error) {
      console.error('Error generating business rules:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to generate business rules'
      };
    }
  },

  /**
   * Apply business rules to a dataset
   * 
   * @param {string} datasetId - The dataset ID
   * @param {Array<string>} ruleIds - Rule IDs to apply
   * @returns {Promise<Object>} - API response
   */
  async applyRules(datasetId, ruleIds) {
    try {
      const response = await axios.post(`${API_BASE_URL}/business-rules/apply/${datasetId}?rule_ids=${ruleIds.join(',')}`, {});
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
   * Test business rules against sample data
   * 
   * @param {string} datasetId - The dataset ID
   * @param {Array<Object>} sampleData - Sample data to test against
   * @param {Array<string>} ruleIds - Rule IDs to test
   * @param {Object} testRule - Optional test rule to evaluate
   * @returns {Promise<Object>} - API response
   */
  async testRulesOnSample(datasetId, sampleData, ruleIds = null, testRule = null) {
    try {
      const queryParams = ruleIds ? `?rule_ids=${ruleIds.join(',')}` : '';
      const response = await axios.post(`${API_BASE_URL}/business-rules/test-sample/${datasetId}${queryParams}`, {
        sample_data: sampleData,
        test_rule: testRule
      });
      return response.data;
    } catch (error) {
      console.error('Error testing business rules:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to test business rules'
      };
    }
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
    try {
      let url = `${API_BASE_URL}/business-rules/metrics/${datasetId}?time_period=${timePeriod}`;
      if (ruleIds) {
        url += `&rule_ids=${ruleIds.join(',')}`;
      }
      const response = await axios.get(url);
      return response.data;
    } catch (error) {
      console.error('Error fetching rule metrics:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch rule metrics'
      };
    }
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
    try {
      const response = await axios.post(`${API_BASE_URL}/business-rules/suggest/${datasetId}?min_confidence=${minConfidence}`, {
        sample_data: sampleData
      });
      return response.data;
    } catch (error) {
      console.error('Error suggesting business rules:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to suggest business rules'
      };
    }
  },

  /**
   * Extract sample data from a dataset
   * 
   * @param {string} datasetId - The dataset ID
   * @param {number} maxRows - Maximum number of rows to extract
   * @returns {Promise<Object>} - API response
   */
  async extractSampleData(datasetId, maxRows = 100) {
    try {
      const response = await axios.post(`${API_BASE_URL}/business-rules/extract-sample/${datasetId}?max_rows=${maxRows}`);
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

export default businessRulesService;
