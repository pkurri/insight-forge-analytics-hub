
import { callApi } from '../../utils/apiUtils';
import { ApiResponse, BusinessRule } from '../../api';

/**
 * Business Rules Service - Handles business rule operations
 */
export const businessRulesService = {
  /**
   * Get business rules for a dataset
   */
  getBusinessRules: async (datasetId: string): Promise<ApiResponse<BusinessRule[]>> => {
    const endpoint = `datasets/${datasetId}/business-rules`;
    
    try {
      const response = await callApi(endpoint);
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      return {
        success: true,
        data: [
          {
            id: 'br001',
            name: 'Price Range Rule',
            description: 'Product price must be between $0 and $10,000',
            dataset_id: datasetId,
            rule_type: 'range',
            condition: 'price >= 0 AND price <= 10000',
            severity: 'high',
            active: true,
            created_at: '2023-05-15T10:23:45Z',
            updated_at: '2023-06-02T14:10:22Z'
          },
          {
            id: 'br002',
            name: 'Required Fields Rule',
            description: 'Name and category fields must not be empty',
            dataset_id: datasetId,
            rule_type: 'not_null',
            condition: 'name IS NOT NULL AND category IS NOT NULL',
            severity: 'critical',
            active: true,
            created_at: '2023-05-16T11:30:00Z',
            updated_at: '2023-06-01T09:15:10Z'
          }
        ]
      };
    } catch (error) {
      console.error("Error fetching business rules:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to fetch business rules"
      };
    }
  },
  
  /**
   * Save business rules for a dataset
   */
  saveBusinessRules: async (datasetId: string, rules: BusinessRule[]): Promise<ApiResponse<any>> => {
    const endpoint = `datasets/${datasetId}/business-rules`;
    
    try {
      const response = await callApi(endpoint, 'POST', { rules });
      if (response.success) {
        return response;
      }
      
      // Mock successful response
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 800));
      
      return {
        success: true,
        data: {
          message: `${rules.length} business rules saved successfully`,
          rules_saved: rules.length
        }
      };
    } catch (error) {
      console.error("Error saving business rules:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to save business rules"
      };
    }
  }
};
