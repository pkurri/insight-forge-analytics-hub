
import { callApi } from '../../utils/apiUtils';
import { ApiResponse, BusinessRule } from '../../types';

export const businessRulesService = {
  /**
   * Get all business rules
   */
  getBusinessRules: async (datasetId?: string): Promise<ApiResponse<BusinessRule[]>> => {
    const endpoint = datasetId 
      ? `datasets/${datasetId}/rules` 
      : 'business-rules';
    
    try {
      const response = await callApi(endpoint);
      return response;
    } catch (error) {
      console.error("Error fetching business rules:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to fetch business rules"
      };
    }
  },
  
  /**
   * Create a new business rule
   */
  createBusinessRule: async (rule: Partial<BusinessRule>, datasetId?: string): Promise<ApiResponse<BusinessRule>> => {
    const endpoint = datasetId 
      ? `datasets/${datasetId}/rules` 
      : 'business-rules';
    
    try {
      const response = await callApi(endpoint, {
        method: 'POST',
        body: JSON.stringify(rule)
      });
      return response;
    } catch (error) {
      console.error("Error creating business rule:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to create business rule"
      };
    }
  },
  
  /**
   * Update an existing business rule
   */
  updateBusinessRule: async (ruleId: string, rule: Partial<BusinessRule>): Promise<ApiResponse<BusinessRule>> => {
    const endpoint = `business-rules/${ruleId}`;
    
    try {
      const response = await callApi(endpoint, {
        method: 'PUT',
        body: JSON.stringify(rule)
      });
      return response;
    } catch (error) {
      console.error(`Error updating business rule ${ruleId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to update business rule"
      };
    }
  },
  
  /**
   * Delete a business rule
   */
  deleteBusinessRule: async (ruleId: string): Promise<ApiResponse<void>> => {
    const endpoint = `business-rules/${ruleId}`;
    
    try {
      const response = await callApi(endpoint, {
        method: 'DELETE'
      });
      return response;
    } catch (error) {
      console.error(`Error deleting business rule ${ruleId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to delete business rule"
      };
    }
  },
  
  /**
   * Generate business rules for a dataset
   */
  generateBusinessRules: async (datasetId: string): Promise<ApiResponse<BusinessRule[]>> => {
    const endpoint = `datasets/${datasetId}/generate-rules`;
    
    try {
      const response = await callApi(endpoint, {
        method: 'POST'
      });
      return response;
    } catch (error) {
      console.error(`Error generating business rules for dataset ${datasetId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to generate business rules"
      };
    }
  },
  
  /**
   * Apply business rules to a dataset
   */
  applyBusinessRules: async (datasetId: string, ruleIds?: string[]): Promise<ApiResponse<any>> => {
    const endpoint = `datasets/${datasetId}/apply-rules`;
    
    try {
      const response = await callApi(endpoint, {
        method: 'POST',
        body: ruleIds ? JSON.stringify({ rule_ids: ruleIds }) : undefined
      });
      return response;
    } catch (error) {
      console.error(`Error applying business rules to dataset ${datasetId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to apply business rules"
      };
    }
  },
  
  /**
   * Get rule validation results for a dataset
   */
  getRuleValidationResults: async (datasetId: string): Promise<ApiResponse<any>> => {
    const endpoint = `datasets/${datasetId}/rule-validations`;
    
    try {
      const response = await callApi(endpoint);
      return response;
    } catch (error) {
      console.error(`Error fetching rule validation results for dataset ${datasetId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to fetch rule validation results"
      };
    }
  }
};
