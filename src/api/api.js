import businessRulesService from './services/businessRulesService';
import pipelineService from './services/pipelineService';

/**
 * API Module
 * 
 * This module exports all API services for use in the frontend components.
 */
export const api = {
  businessRules: businessRulesService,
  pipeline: pipelineService
  // Add other services here as needed
};

export default api;
