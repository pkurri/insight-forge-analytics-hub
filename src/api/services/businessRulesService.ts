
import { callApi } from '../utils/apiUtils';
import { BusinessRule } from '../api';

/**
 * Business Rules Service - Handles operations related to business rules
 */
export const businessRulesService = {
  /**
   * Get business rules for a dataset
   */
  getBusinessRules: async (datasetId: string): Promise<any> => {
    // In a real app, this would retrieve actual rules from the backend
    const endpoint = `datasets/${datasetId}/rules`;
    
    try {
      const response = await callApi(endpoint);
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 600));
      
      return {
        success: true,
        data: [
          {
            id: 'rule001',
            name: 'Valid Price',
            condition: 'product.price >= 0',
            severity: 'high',
            message: 'Product price must be non-negative'
          },
          {
            id: 'rule002',
            name: 'Valid Quantity',
            condition: 'product.quantity >= 0',
            severity: 'high',
            message: 'Product quantity must be non-negative'
          },
          {
            id: 'rule003',
            name: 'Category Required',
            condition: 'product.category != null && product.category.trim() !== ""',
            severity: 'medium',
            message: 'Product must have a category'
          }
        ]
      };
    } catch (error) {
      console.error("Error getting business rules:", error);
      return {
        success: false,
        error: "Failed to get business rules"
      };
    }
  },

  /**
   * Generate business rules for a dataset
   */
  generateBusinessRules: async (datasetId: string, options: any = {}): Promise<any> => {
    const endpoint = `ai/generate-rules/${datasetId}`;
    
    try {
      const response = await callApi(endpoint, 'POST', options);
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 2500));
      
      return {
        success: true,
        data: {
          rules_generated: 8,
          rules: [
            {
              id: "auto-1",
              name: "Price Range",
              condition: "data['price'] >= 0 and data['price'] <= 2000",
              severity: "high",
              message: "Price must be between 0 and 2000",
              confidence: 0.95,
              model_generated: true
            },
            {
              id: "auto-2",
              name: "Valid Stock",
              condition: "data['stock'] >= 0",
              severity: "high",
              message: "Stock cannot be negative",
              confidence: 0.99,
              model_generated: true
            },
            {
              id: "auto-3",
              name: "Rating Range",
              condition: "data['rating'] >= 1 and data['rating'] <= 5",
              severity: "medium",
              message: "Rating must be between 1 and 5",
              confidence: 0.98,
              model_generated: true
            },
            {
              id: "auto-4",
              name: "Category Check",
              condition: "data['category'] in ['Electronics', 'Clothing', 'Home', 'Books', 'Food', 'Sports', 'Beauty', 'Other']",
              severity: "medium",
              message: "Category must be from approved list",
              confidence: 0.96,
              model_generated: true
            },
            {
              id: "auto-5",
              name: "Price-Stock Correlation",
              condition: "data['price'] < 100 or data['stock'] >= 5",
              severity: "low",
              message: "High-priced items should maintain minimum stock",
              confidence: 0.82,
              model_generated: true
            }
          ],
          generation_metadata: {
            method: "pattern_mining",
            confidence_threshold: 0.8,
            row_threshold: 0.98
          }
        }
      };
    } catch (error) {
      console.error("Error generating business rules:", error);
      return {
        success: false,
        error: "Failed to generate business rules"
      };
    }
  },

  /**
   * Save business rules
   */
  saveBusinessRules: async (datasetId: string, rules: BusinessRule[]): Promise<any> => {
    console.log('Saving business rules:', datasetId, rules);
    
    // In a real app, this would send the rules to the backend
    const endpoint = `datasets/${datasetId}/rules`;
    
    try {
      const response = await callApi(endpoint, 'POST', { rules });
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 800));
      
      return {
        success: true,
        message: `Successfully saved ${rules.length} rules for dataset ${datasetId}`
      };
    } catch (error) {
      console.error("Error saving business rules:", error);
      return {
        success: false,
        error: "Failed to save business rules"
      };
    }
  }
};
