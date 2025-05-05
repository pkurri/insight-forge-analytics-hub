
import { callApi, ApiCallOptions } from '@/utils/apiUtils';
import { ApiResponse } from '@/api/types';

export interface BusinessRule {
  id: string;
  name: string;
  description?: string;
  condition: string;
  severity: 'low' | 'medium' | 'high';
  datasetId?: string; // For attaching to datasets
  column?: string;
  active: boolean;
  created_at?: string;
  updated_at?: string;
  message?: string;
  confidence?: number;
  model_generated?: boolean;
}

export const businessRulesService = {
  /**
   * Get all business rules
   */
  getAllBusinessRules: async (): Promise<ApiResponse<BusinessRule[]>> => {
    try {
      const options: ApiCallOptions = {
        method: 'GET'
      };
      return await callApi('business-rules', options);
    } catch (error) {
      console.error("Error getting business rules:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to get business rules"
      };
    }
  },

  /**
   * Get business rules for a specific dataset
   */
  getBusinessRules: async (datasetId: string): Promise<ApiResponse<BusinessRule[]>> => {
    try {
      const options: ApiCallOptions = {
        method: 'GET'
      };
      return await callApi(`business-rules/dataset/${datasetId}`, options);
    } catch (error) {
      console.error(`Error getting business rules for dataset ${datasetId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to get business rules"
      };
    }
  },
  
  /**
   * Create a business rule
   */
  createBusinessRule: async (businessRule: Omit<BusinessRule, "id">): Promise<ApiResponse<BusinessRule>> => {
    try {
      const options: ApiCallOptions = {
        method: 'POST',
        body: JSON.stringify(businessRule)
      };
      return await callApi('business-rules', options);
    } catch (error) {
      console.error("Error creating business rule:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to create business rule"
      };
    }
  },
  
  /**
   * Update a business rule
   */
  updateBusinessRule: async (id: string, businessRule: Partial<BusinessRule>): Promise<ApiResponse<BusinessRule>> => {
    try {
      const options: ApiCallOptions = {
        method: 'PUT',
        body: JSON.stringify(businessRule)
      };
      return await callApi(`business-rules/${id}`, options);
    } catch (error) {
      console.error(`Error updating business rule ${id}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to update business rule"
      };
    }
  },
  
  /**
   * Delete a business rule
   */
  deleteBusinessRule: async (id: string): Promise<ApiResponse<void>> => {
    try {
      const options: ApiCallOptions = {
        method: 'DELETE'
      };
      return await callApi(`business-rules/${id}`, options);
    } catch (error) {
      console.error(`Error deleting business rule ${id}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to delete business rule"
      };
    }
  },
  
  /**
   * Save business rules for a dataset (batch save)
   */
  saveBusinessRules: async (datasetId: string, rules: BusinessRule[]): Promise<ApiResponse<any>> => {
    try {
      const options: ApiCallOptions = {
        method: 'POST',
        body: JSON.stringify({ datasetId, rules })
      };
      return await callApi('business-rules/batch', options);
    } catch (error) {
      console.error("Error saving business rules:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to save business rules"
      };
    }
  },
  
  /**
   * Get example business rules based on a schema or dataset
   */
  getExampleRules: async (datasetId: string): Promise<ApiResponse<BusinessRule[]>> => {
    try {
      const options: ApiCallOptions = {
        method: 'GET'
      };
      return await callApi(`business-rules/examples/${datasetId}`, options);
    } catch (error) {
      console.error("Error getting example business rules:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to get example business rules"
      };
    }
  }
};
