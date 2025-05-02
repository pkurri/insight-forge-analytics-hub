import { callApi } from '../utils/apiUtils';
import { ApiResponse } from '../api';
import type { BusinessRule } from './businessRules/businessRulesService';

/**
 * OpenEvals Service - Handles AI-based business rule generation
 */
export type AIRuleEngine = 'huggingface' | 'pydantic' | 'great_expectations' | 'ai_default';

export const openevalsService = {
  /**
   * Generate business rules using AI for a dataset, with selectable engine
   */
  generateBusinessRules: async (
    datasetId: string,
    engine: AIRuleEngine = 'ai_default'
  ): Promise<ApiResponse<BusinessRule[]>> => {
    const endpoint = `business-rules/generate/${datasetId}`;
    try {
      const response = await callApi(endpoint, {
        method: 'POST',
        body: JSON.stringify({ engine })
      });
      if (response.success) {
        return {
          success: true,
          data: response.data?.rules || response.data,
        };
      }
      return response;
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to generate business rules',
      };
    }
  }
};

export default openevalsService;
