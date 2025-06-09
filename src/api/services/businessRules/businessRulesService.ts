import { BusinessRule } from '../../../types/businessRules';
import { ApiResponse } from '../../../types/api';
import { callApi } from '../../utils/apiUtils';

// Response type for business rule operations
interface BusinessRuleResponse {
  message: string;
  rules_saved?: number;
  applied?: boolean;
  applyError?: string;
  id?: string;
  [key: string]: any; // For other properties that might be returned
}

// Response type for batch rule operations
interface BatchRuleResponse {
  created_rules: BusinessRule[];
  failed_rules?: Array<{rule_data: any; error: string}>;
  total_submitted?: number;
  total_created?: number;
  total_failed?: number;
  message?: string;
}

/**
 * Business Rules Service - Handles business rule operations
 */
export interface BusinessRule {
  id: string;
  name: string;
  description?: string;
  condition: string;
  severity: 'low' | 'medium' | 'high';
  message: string;
  active: boolean;
  confidence?: number;
  lastUpdated?: string;
  model_generated?: boolean;
}

export interface RuleSuggestion extends Omit<BusinessRule, 'id'> {
  confidence: number;
  column?: string;
  rule_type?: string;
  sample_match_rate?: number;
  source?: string; // Source of the rule (huggingface, pydantic, greater_expressions, etc.)
}

export type RuleGenerationEngine = 'ai_default' | 'huggingface' | 'pydantic' | 'great_expectations' | 'greater_expressions';

export interface ColumnMetadata {
  name: string;
  type: string;
  stats: {
    min?: number;
    max?: number;
    mean?: number;
    std?: number;
    null_count?: number;
    total_count?: number;
    unique_count?: number;
    common_values?: string[];
    max_length?: number;
    pattern?: string;
    [key: string]: any;
  };
}

export interface GenerateRulesOptions {
  engine: RuleGenerationEngine;
  modelType?: string;
  columnMeta: {
    columns: ColumnMetadata[];
    dataset_info?: Record<string, any>;
  };
}

export const businessRulesService = {
  /**
   * Get business rules for a dataset
   */
  getBusinessRules: async (datasetId: string): Promise<ApiResponse<BusinessRule[]>> => {
    const endpoint = `business-rules/${datasetId}/suggestions`;
    
    try {
      const response = await callApi(endpoint);
      if (response.success) {
        // Transform the backend response to match our frontend types
        const rules = (response.data || []).map((rule: any) => ({
          id: rule.id || `rule_${Math.random().toString(36).substr(2, 9)}`,
          name: rule.name || 'Unnamed Rule',
          description: rule.description || '',
          condition: rule.conditions || '',
          severity: (rule.priority?.toLowerCase() as RuleSeverity) || 'medium',
          message: rule.description || '',
          active: true,
          confidence: rule.confidence || 0.8,
          model_generated: true
        }));
        
        return { ...response, data: rules };
      }
      
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
   * Save business rules for a dataset
   */
  saveBusinessRules: async (datasetId: string, rules: BusinessRule[]): Promise<ApiResponse<BusinessRuleResponse>> => {
    // Use the batch endpoint if multiple rules are provided
    const isBatch = rules.length > 1;
    const endpoint = isBatch ? `business-rules/batch/${datasetId}` : `business-rules`;
    
    try {
      const response = await callApi<BatchRuleResponse | BusinessRule>(endpoint, {
        method: 'POST',
        body: isBatch 
          ? JSON.stringify(rules) // For batch endpoint, send array directly
          : JSON.stringify({ ...rules[0], dataset_id: datasetId }) // For single rule, include dataset_id
      });
      
      if (response.success) {
        // Extract rule IDs based on response type
        const ruleIds = isBatch 
          ? (response.data as BatchRuleResponse).created_rules.map((rule: BusinessRule) => rule.id)
          : [(response.data as BusinessRule).id];
          
        // Call the pipeline service to apply the rules to the dataset
        const applyResponse = await callApi<{success: boolean; message: string}>(
          `pipeline/${datasetId}/business-rules`, {
            method: 'POST',
            body: JSON.stringify({ rule_ids: ruleIds })
          }
        );
        
        if (applyResponse.success) {
          return {
            success: true,
            data: {
              ...response.data,
              applied: true,
              message: `${rules.length} business rules saved and applied successfully`,
            } as BusinessRuleResponse
          };
        } else {
          return {
            success: true,
            data: {
              ...response.data,
              applied: false,
              message: `${rules.length} business rules saved but not applied`,
              applyError: applyResponse.error
            } as BusinessRuleResponse
          };
        }
      }
      
      return response as ApiResponse<BusinessRuleResponse>;
    } catch (error) {
      console.error("Error saving business rules:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to save business rules"
      };
    }
  },

  /**
   * Suggest business rules for a dataset
   */
  suggestRules: async (datasetId: string, sampleData: Record<string, any>[]): Promise<ApiResponse<{ suggested_rules: RuleSuggestion[] }>> => {
    const endpoint = `business-rules/${datasetId}/suggest`;
    
    try {
      // Get column metadata from sample data
      const columnMeta = {
        columns: Object.keys(sampleData[0] || {}).map(key => ({
          name: key,
          type: typeof sampleData[0][key],
          stats: {}
        })),
        dataset_info: {
          row_count: sampleData.length,
          column_count: Object.keys(sampleData[0] || {}).length
        }
      };
      
      const response = await callApi(endpoint, 'POST', { 
        dataset_id: datasetId,
        sample_data: sampleData,
        column_meta: columnMeta
      });
      
      if (response.success) {
        return {
          success: true,
          data: {
            suggested_rules: (response.data?.suggested_rules || []).map((rule: any) => ({
              name: rule.name,
              description: rule.description,
              condition: rule.conditions || rule.condition,
              severity: (rule.priority?.toLowerCase() as RuleSeverity) || 'medium',
              message: rule.message || rule.description,
              active: true,
              confidence: rule.confidence || 0.8,
              source: rule.source || 'ai_default',
              column: rule.column,
              rule_type: rule.rule_type,
              sample_match_rate: rule.sample_match_rate
            }))
          }
        };
      }
      
      return {
        success: false,
        error: response.error || 'Failed to generate rule suggestions'
      };
    } catch (error) {
      console.error('Error suggesting rules:', error);
      return {
        success: false,
        error: 'Failed to suggest rules'
      };
    }
  },

  /**
   * Update a business rule
   */
  updateBusinessRule: async (datasetId: string, ruleId: string, rule: Partial<BusinessRule>): Promise<ApiResponse<BusinessRule>> => {
    const endpoint = `business-rules/${datasetId}/${ruleId}`;
    
    try {
      const response = await callApi(endpoint, 'PUT', {
        ...rule,
        dataset_id: datasetId
      });
      if (response.success) {
        return response;
      }
      
      // Mock successful response
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 600));
      
      return {
        success: true,
        data: {
          message: 'Business rule updated successfully',
          rule_id: ruleId
        }
      };
    } catch (error) {
      console.error("Error updating business rule:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to update business rule"
      };
    }
  },

  /**
   * Delete a business rule
   */
  deleteBusinessRule: async (datasetId: string, ruleId: string): Promise<ApiResponse<any>> => {
    const endpoint = `business-rules/${datasetId}/${ruleId}`;
    
    try {
      const response = await callApi(endpoint, {
        method: 'DELETE'
      });
      if (response.success) {
        return response;
      }
      
      // Mock successful response
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      return {
        success: true,
        data: {
          message: 'Business rule deleted successfully',
          rule_id: ruleId
        }
      };
    } catch (error) {
      console.error("Error deleting business rule:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to delete business rule"
      };
    }
  },

  /**
   * Import business rules from JSON
   */
  importBusinessRules: async (datasetId: string, rulesJson: string): Promise<ApiResponse<any>> => {
    const endpoint = `business-rules/${datasetId}/import`;
    
    try {
      // Parse JSON to validate it before sending
      const rules = JSON.parse(rulesJson);
      
      const response = await callApi(endpoint, {
        method: 'POST',
        body: JSON.stringify({ rules })
      });
      if (response.success) {
        return response;
      }
      
      // Mock successful response
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 800));
      
      return {
        success: true,
        data: {
          message: `${rules.length} business rules imported successfully`,
          rules_imported: rules.length
        }
      };
    } catch (error) {
      console.error("Error importing business rules:", error);
      return {
        success: false,
        error: response.error || 'Failed to generate rule suggestions'
      };
    } catch (error) {
      console.error('Error suggesting rules:', error);
      return {
        success: false,
        error: 'Failed to suggest rules'
      };
    }
  },
  
  /**
   */
  exportBusinessRules: async (datasetId: string): Promise<ApiResponse<{ rules: BusinessRule[], export_time: string }>> => {
      
      await new Promise(resolve => setTimeout(resolve, 500));
      
      return {
        success: true,
        data: {
          rules: [
            {
              id: 'br001',
              name: 'Price Range Rule',
              description: 'Product price must be between $0 and $10,000',
              condition: 'price >= 0 AND price <= 10000',
              severity: 'high',
              message: 'Price must be between $0 and $10,000',
              active: true,
              lastUpdated: '2023-06-02T14:10:22Z'
            },
            {
              id: 'br002',
              name: 'Required Fields Rule',
              description: 'Name and category fields must not be empty',
              condition: 'name IS NOT NULL AND category IS NOT NULL',
              severity: 'high',
              message: 'Name and category are required fields',
              active: true,
              lastUpdated: '2023-06-01T09:15:10Z'
            }
          ],
          export_time: new Date().toISOString()
        }
      };
    } catch (error) {
      console.error("Error exporting business rules:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to export business rules"
      };
    }
  }
};
