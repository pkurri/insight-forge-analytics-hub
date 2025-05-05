
import { callApi } from '../../../utils/apiUtils';
import { BusinessRule } from '../../../api/types';

/**
 * Business Rules Service - Handles CRUD operations for business rules
 */
export const businessRulesService = {
  /**
   * Get all business rules
   */
  getAllBusinessRules: async (): Promise<any> => {
    try {
      const response = await callApi('business-rules');
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
   * Get business rules for a specific dataset
   */
  getDatasetBusinessRules: async (datasetId: string): Promise<any> => {
    try {
      const response = await callApi(`datasets/${datasetId}/business-rules`);
      return response;
    } catch (error) {
      console.error(`Error fetching business rules for dataset ${datasetId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to fetch dataset business rules"
      };
    }
  },

  /**
   * Create a new business rule
   */
  createBusinessRule: async (businessRule: Omit<BusinessRule, 'id'>): Promise<any> => {
    try {
      const response = await callApi('business-rules', {
        method: 'POST',
        body: businessRule
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
  updateBusinessRule: async (id: string, businessRule: Partial<BusinessRule>): Promise<any> => {
    try {
      const response = await callApi(`business-rules/${id}`, {
        method: 'PUT',
        body: businessRule
      });
      return response;
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
  deleteBusinessRule: async (id: string): Promise<any> => {
    try {
      const response = await callApi(`business-rules/${id}`, {
        method: 'DELETE'
      });
      return response;
    } catch (error) {
      console.error(`Error deleting business rule ${id}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to delete business rule"
      };
    }
  },

  /**
   * Generate example business rules
   */
  getExampleRules: async (): Promise<any> => {
    // These are hardcoded examples
    return {
      success: true,
      data: [
        {
          id: "example-1",
          name: "Email Format Validation",
          description: "Validates that all email addresses match standard format",
          condition: "REGEXP_MATCH(email, '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$')",
          severity: "high",
          column: "email",
          active: true,
          created_at: new Date().toISOString()
        },
        {
          id: "example-2",
          name: "Price Range Check",
          description: "Ensures all prices fall within acceptable range",
          condition: "price >= 0 AND price <= 10000",
          severity: "medium",
          column: "price",
          active: true,
          created_at: new Date().toISOString()
        },
        {
          id: "example-3",
          name: "Date Format Check",
          description: "Validates date format is YYYY-MM-DD",
          condition: "REGEXP_MATCH(date_field, '^[0-9]{4}-[0-9]{2}-[0-9]{2}$')",
          severity: "medium",
          column: "date_field",
          active: true,
          created_at: new Date().toISOString()
        }
      ]
    };
  }
};
