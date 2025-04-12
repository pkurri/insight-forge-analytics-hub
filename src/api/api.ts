
/**
 * DataForge API Module
 * 
 * This module provides centralized access to all DataForge API endpoints,
 * including data profiling, anomaly detection, schema validation,
 * and business rules management.
 */

import { analyticsService } from './services/analyticsService';
import { validationService } from './services/validationService';
import { businessRulesService } from './services/businessRulesService';
import { pipelineService } from './services/pipelineService';
import { monitoringService } from './services/monitoringService';
import { aiService } from './services/aiService';
import { datasetService } from './services/datasetService';
import { aiChatService } from './services/ai/aiChatService';

export interface BusinessRule {
  id: string;
  name: string;
  condition: string;
  severity: 'low' | 'medium' | 'high';
  message: string;
  confidence?: number;
  model_generated?: boolean;
}

export interface DatasetSummary {
  id: string;
  name: string;
  recordCount: number;
  columnCount: number;
  createdAt: string;
  updatedAt: string;
  status: 'ready' | 'processing' | 'error';
}

export interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

/**
 * DataForge API client
 */
export const api = {
  // Dataset operations
  getDatasets: datasetService.getDatasets,
  getDataset: datasetService.getDataset,
  runDataQualityChecks: datasetService.runDataQualityChecks,

  // Analytics operations
  profileDataset: analyticsService.fetchDataProfile,
  detectAnomalies: analyticsService.detectAnomalies,
  getDataQuality: analyticsService.getDataQuality,

  // Validation operations
  validateSchema: validationService.validateSchema,
  cleanData: validationService.cleanData,

  // Business rules operations
  getBusinessRules: businessRulesService.getBusinessRules,
  generateBusinessRules: businessRulesService.generateBusinessRules,
  saveBusinessRules: businessRulesService.saveBusinessRules,

  // Pipeline operations
  uploadDataToPipeline: pipelineService.uploadDataToPipeline,
  fetchDataFromExternalApi: pipelineService.fetchDataFromExternalApi,
  fetchDataFromDatabase: pipelineService.fetchDataFromDatabase,
  validateDataInPipeline: pipelineService.validateDataInPipeline,
  transformDataInPipeline: pipelineService.transformDataInPipeline,
  enrichDataInPipeline: pipelineService.enrichDataInPipeline,
  loadDataInPipeline: pipelineService.loadDataInPipeline,
  runDataPipeline: pipelineService.runDataPipeline,

  // Monitoring operations
  getMonitoringMetrics: monitoringService.getMonitoringMetrics,
  getSystemAlerts: monitoringService.getSystemAlerts,
  getSystemLogs: monitoringService.getSystemLogs,

  // AI operations
  askQuestion: aiService.askQuestion,
  getAiAssistantResponse: aiService.getAiAssistantResponse,
  analyzeAnomalies: aiService.analyzeAnomalies,
  
  // AI Chat operations (Vector DB + Hugging Face)
  getChatSuggestions: aiChatService.getChatSuggestions,
  getChatHistory: aiChatService.getChatHistory,
  generateEmbeddings: aiChatService.generateEmbeddings,
  storeChatHistory: aiChatService.storeChatHistory,
  getAvailableModels: aiChatService.getAvailableModels
};
