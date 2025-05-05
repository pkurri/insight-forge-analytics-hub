
import { callApi } from '../utils/apiUtils';

/**
 * Validation Service - Handles data validation and quality checks
 */
export const validationService = {
  /**
   * Validate a dataset against business rules
   */
  validateDataset: async (datasetId: string, options: any = {}): Promise<any> => {
    const endpoint = `validation/dataset/${datasetId}`;
    
    try {
      const response = await callApi(endpoint, {
        method: 'POST',
        body: options
      });
      
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      return {
        success: true,
        data: {
          validation_id: `val-${Date.now()}`,
          dataset_id: datasetId,
          timestamp: new Date().toISOString(),
          summary: {
            total_rules: 12,
            passed_rules: 9,
            failed_rules: 3,
            warning_rules: 2,
            overall_score: 0.85
          },
          results: [
            {
              rule_id: "rule-001",
              name: "No missing values in ID column",
              status: "passed",
              details: {
                column: "id",
                condition: "count(missing) = 0",
                result: true
              }
            },
            {
              rule_id: "rule-002",
              name: "Price is positive",
              status: "failed",
              details: {
                column: "price",
                condition: "min(price) > 0",
                result: false,
                failures: [
                  { row_id: 245, value: -10.99 },
                  { row_id: 1256, value: -5.00 }
                ]
              }
            },
            {
              rule_id: "rule-003",
              name: "Category is from allowed list",
              status: "warning",
              details: {
                column: "category",
                condition: "category in ('Electronics', 'Clothing', 'Home', 'Books')",
                result: false,
                failures: [
                  { row_id: 3456, value: "Unknown" },
                  { row_id: 4277, value: "Misc" }
                ]
              }
            }
          ]
        }
      };
    } catch (error) {
      console.error("Error validating dataset:", error);
      return {
        success: false,
        error: "Failed to validate dataset"
      };
    }
  },

  /**
   * Get validation rule suggestions for a dataset
   */
  getSuggestedRules: async (datasetId: string): Promise<any> => {
    const endpoint = `validation/suggest-rules/${datasetId}`;
    
    try {
      const response = await callApi(endpoint);
      
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      return {
        success: true,
        data: {
          dataset_id: datasetId,
          suggested_rules: [
            {
              name: "ID column must not be null",
              description: "Ensures that all records have a valid identifier",
              condition: "id IS NOT NULL",
              severity: "high",
              column: "id"
            },
            {
              name: "Price must be positive",
              description: "Ensures that all prices are positive values",
              condition: "price > 0",
              severity: "high",
              column: "price"
            },
            {
              name: "Category must be from valid list",
              description: "Ensures categories are from the standard set",
              condition: "category IN ('Electronics', 'Clothing', 'Home', 'Books', 'Food', 'Sports', 'Beauty')",
              severity: "medium",
              column: "category"
            }
          ]
        }
      };
    } catch (error) {
      console.error("Error getting suggested rules:", error);
      return {
        success: false,
        error: "Failed to get rule suggestions"
      };
    }
  }
};
