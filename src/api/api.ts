
import { authService } from '@/api/services/auth/authService';
import { analyticsService } from '@/api/services/analyticsService';
import { pipelineService } from '@/api/services/pipeline/pipelineService'; 
import { businessRulesService } from '@/api/services/businessRules/businessRulesService';

// API service aggregator
export const api = {
  auth: authService,
  analytics: analyticsService,
  pipeline: pipelineService,
  businessRules: businessRulesService,
  
  // Add datasets service for improved readability
  datasets: {
    uploadDataset: async (formData: FormData) => {
      return pipelineService.uploadData(formData);
    }
  }
};

export type { ApiResponse } from '@/api/types';
