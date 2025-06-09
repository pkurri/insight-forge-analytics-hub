import { callApi } from '../../utils/apiUtils';

// Type definitions
type RuleSeverity = 'low' | 'medium' | 'high';

// Define the API response type for business rules
type ApiResponse<T = any> = {
  success: boolean;
  data?: T;
  error?: string;
  status?: number;
};

// Response type for business rule operations
interface BusinessRuleResponse {
  message: string;
  rules_saved?: number;
  applied?: boolean;
  applyError?: string;
  id?: string;
  [key: string]: any;
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
 * Business Rule interface
 */
export interface BusinessRule {
  id: string;
  name: string;
  description?: string;
  condition: string;
  severity: RuleSeverity;
  message: string;
  active: boolean;
  confidence?: number;
  lastUpdated?: string;
  model_generated?: boolean;
}

/**
 * Business Rules Service
 * Handles all business rule related operations
 */
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
          message: rule.message || rule.description || '',
          active: rule.active !== false,
          confidence: rule.confidence || 0.8,
          model_generated: rule.model_generated || false,
          lastUpdated: rule.last_updated || rule.lastUpdated
        }));
        
        return { ...response, data: rules };
      }
      
      return response;
    } catch (error) {
      console.error('Error fetching business rules:', error);
      return {
        success: false,
        error: 'Failed to fetch business rules'
      };
    }
  },

  /**
   * Save business rules for a dataset
   */
  saveBusinessRules: async (datasetId: string, rules: BusinessRule[]): Promise<ApiResponse<BusinessRuleResponse>> => {
    const endpoint = `business-rules/${datasetId}/apply`;
    
    try {
      // Transform rules to match backend format
      const rulesToSave = rules.map(rule => ({
        name: rule.name,
        description: rule.description,
        conditions: rule.condition,
        priority: rule.severity,
        message: rule.message,
        active: rule.active !== false
      }));
      
      const response = await callApi(endpoint, 'POST', { 
        dataset_id: datasetId,
        rules: rulesToSave 
      });
      
      if (response.success) {
        return {
          success: true,
          message: response.message || 'Rules applied successfully',
          rules_saved: response.data?.applied_count || rules.length
        };
      }
      
      return {
        success: false,
        error: response.error || 'Failed to apply business rules'
      };
    } catch (error) {
      console.error('Error saving business rules:', error);
      return {
        success: false,
        error: 'Failed to save business rules'
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
        dataset_id: datasetId,
        conditions: rule.condition,
        priority: rule.severity
      });
      
      if (response.success) {
        return {
          success: true,
          data: {
            ...response.data,
            condition: response.data.conditions || '',
            severity: (response.data.priority?.toLowerCase() as RuleSeverity) || 'medium'
          }
        };
      }
      
      return response;
    } catch (error) {
      console.error('Error updating business rule:', error);
      return {
        success: false,
        error: 'Failed to update business rule'
      };
    }
  },

  /**
   * Delete a business rule
   */
  deleteBusinessRule: async (datasetId: string, ruleId: string): Promise<ApiResponse<{ deleted: boolean }>> => {
    const endpoint = `business-rules/${datasetId}/${ruleId}`;
    
    try {
      const response = await callApi(endpoint, 'DELETE');
      return response;
    } catch (error) {
      console.error('Error deleting business rule:', error);
      return {
        success: false,
        error: 'Failed to delete business rule'
      };
    }
  },

  /**
   * Suggest business rules based on sample data
   */
  suggestRules: async (datasetId: string, sampleData: Record<string, any>[]): Promise<ApiResponse<{ suggested_rules: BusinessRule[] }>> => {
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
              id: `suggested_${Math.random().toString(36).substr(2, 9)}`,
              name: rule.name || 'Unnamed Rule',
              description: rule.description || '',
              condition: rule.conditions || rule.condition || '',
              severity: (rule.priority?.toLowerCase() as RuleSeverity) || 'medium',
              message: rule.message || rule.description || '',
              active: true,
              confidence: rule.confidence || 0.8,
              model_generated: true,
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
   * Export business rules for a dataset
   */
  exportBusinessRules: async (datasetId: string): Promise<ApiResponse<{ rules: BusinessRule[], export_time: string }>> => {
    const endpoint = `business-rules/${datasetId}/export`;
    
    try {
      const response = await callApi(endpoint);
      if (response.success) {
        // Transform the exported rules to match our frontend types
        const rules = (response.data?.rules || []).map((rule: any) => ({
          id: rule.id || `rule_${Math.random().toString(36).substr(2, 9)}`,
          name: rule.name || 'Unnamed Rule',
          description: rule.description || '',
          condition: rule.conditions || rule.condition || '',
          severity: (rule.priority?.toLowerCase() as RuleSeverity) || 'medium',
          message: rule.message || rule.description || '',
          active: rule.active !== false,
          confidence: rule.confidence,
          lastUpdated: rule.last_updated || rule.lastUpdated,
          model_generated: rule.model_generated || false
        }));
        
        return {
          success: true,
          data: {
            rules,
            export_time: response.data?.export_time || new Date().toISOString()
          }
        };
      }
      
      return response;
    } catch (error) {
      console.error('Error exporting business rules:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to export business rules'
      };
    }
  }
};

export default businessRulesService;
