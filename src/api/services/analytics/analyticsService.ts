
import { callApi } from '../../utils/apiUtils';
import { ApiResponse } from '../../api';

export interface DataCleaningOptions {
  method: 'scikit-learn' | 'ai-model';
  operations: Array<{
    type: 'cleaning' | 'validation' | 'analytics' | 'anomalies';
    config: Record<string, any>;
  }>;
}

export interface BusinessRule {
  name: string;
  condition: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  message?: string;
}

export interface DataQualityMetrics {
  completeness: number;
  validity: number;
  accuracy: number;
  consistency: number;
  uniqueness: number;
  details: Array<{
    check: string;
    status: 'passed' | 'warning' | 'failed';
    score: number;
  }>;
}

export interface DatasetStatistics {
  rowCount: number;
  columnCount: number;
  nullPercentage: number;
  duplicatePercentage: number;
  columns: Array<{
    name: string;
    type: string;
    uniqueValues: number;
    nullCount: number;
    statistics: Record<string, any>;
  }>;
}

export interface DatasetAnomaly {
  column: string;
  type: string;
  count: number;
  examples: any[];
}

export interface BusinessRuleValidation {
  passed: BusinessRule[];
  failed: BusinessRule[];
  warnings: BusinessRule[];
}

export interface AnalyticsResult {
  datasetId: string;
  metrics: {
    quality: DataQualityMetrics;
    statistics: DatasetStatistics;
    anomalies?: DatasetAnomaly[];
  };
  businessRules: BusinessRuleValidation;
}

/**
 * Analytics Service - Handles data analytics operations
 */
export interface TimeSeriesMetric {
  date: string;
  ingestion: number;
  cleaning: number;
  validation: number;
  [key: string]: string | number; // Allow additional metrics
}

export interface PipelineStageMetric {
  stage: string;
  time: number;
  count?: number;
  success_rate?: number;
}

export interface BusinessRuleComplianceMetric {
  rule: string;
  compliance: number;
  violations: number;
}

export const analyticsService = {
  /**
   * Process a dataset using the specified cleaning method and operations
   */
  processDataset: async (datasetId: string, options: DataCleaningOptions): Promise<ApiResponse<AnalyticsResult>> => {
    try {
      return await callApi(`analytics/process/${datasetId}`, {
        method: 'POST',
        body: JSON.stringify(options)
      });
    } catch (error) {
      console.error('Error processing dataset:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to process dataset'
      };
    }
  },

  /**
   * Get data quality metrics for a dataset
   */
  getDataQuality: async (datasetId: string): Promise<ApiResponse<DataQualityMetrics>> => {
    try {
      return await callApi(`analytics/quality/${datasetId}`);
    } catch (error) {
      console.error('Error getting data quality:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get data quality metrics'
      };
    }
  },

  /**
   * Profile a dataset to get its statistics and characteristics
   */
  profileDataset: async (datasetId: string): Promise<ApiResponse<DatasetStatistics>> => {
    try {
      return await callApi(`analytics/profile/${datasetId}`);
    } catch (error) {
      console.error("Error profiling dataset:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to profile dataset"
      };
    }
  },
  
  /**
   * Detect anomalies in a dataset
   */
  detectAnomalies: async (datasetId: string): Promise<ApiResponse<DatasetAnomaly[]>> => {
    try {
      return await callApi(`analytics/anomalies/${datasetId}`);
    } catch (error) {
      console.error('Error detecting anomalies:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to detect anomalies'
      };
    }
  },

  /**
   * Get business rules validation results
   */
  validateBusinessRules: async (datasetId: string): Promise<ApiResponse<BusinessRuleValidation>> => {
    try {
      return await callApi(`analytics/rules/${datasetId}`);
    } catch (error) {
      console.error('Error validating business rules:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to validate business rules'
      };
    }
  },

  /**
   * Store dataset in vector database
   */
  storeInVectorDB: async (datasetId: string): Promise<ApiResponse<void>> => {
    try {
      return await callApi(`analytics/vectorize/${datasetId}`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('Error storing in vector DB:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to store in vector database'
      };
    }
  },

  /**
   * Get time series metrics for pipeline processing volumes
   */
  getTimeSeriesMetrics: async (datasetId: string): Promise<ApiResponse<{time_series: TimeSeriesMetric[]}>> => {
    try {
      return await callApi(`analytics/timeseries/${datasetId}`);
    } catch (error) {
      console.error('Error getting time series metrics:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get time series metrics',
        data: {
          time_series: [
            { date: '2025-04-01', ingestion: 1200, cleaning: 1000, validation: 800 },
            { date: '2025-04-02', ingestion: 1500, cleaning: 1300, validation: 1100 },
            { date: '2025-04-03', ingestion: 1000, cleaning: 850, validation: 800 },
            { date: '2025-04-04', ingestion: 1800, cleaning: 1600, validation: 1400 },
            { date: '2025-04-05', ingestion: 2000, cleaning: 1800, validation: 1600 },
            { date: '2025-04-06', ingestion: 1700, cleaning: 1500, validation: 1300 },
            { date: '2025-04-07', ingestion: 1900, cleaning: 1700, validation: 1500 },
          ]
        }
      };
    }
  },

  /**
   * Get pipeline stage metrics (processing time, success rate, etc.)
   */
  getPipelineMetrics: async (datasetId: string): Promise<ApiResponse<{stage_metrics: PipelineStageMetric[]}>> => {
    try {
      return await callApi(`analytics/pipeline/metrics/${datasetId}`);
    } catch (error) {
      console.error('Error getting pipeline metrics:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get pipeline metrics',
        data: {
          stage_metrics: [
            { stage: 'Ingestion', time: 12 },
            { stage: 'Cleaning', time: 25 },
            { stage: 'Validation', time: 18 },
            { stage: 'Business Rules', time: 15 },
            { stage: 'Anomaly Detection', time: 30 },
            { stage: 'Analytics', time: 22 },
          ]
        }
      };
    }
  },

  /**
   * Get business rules compliance metrics
   */
  getBusinessRulesCompliance: async (datasetId: string): Promise<ApiResponse<{rules_compliance: BusinessRuleComplianceMetric[]}>> => {
    try {
      return await callApi(`analytics/business-rules/compliance/${datasetId}`);
    } catch (error) {
      console.error('Error getting business rules compliance:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get business rules compliance',
        data: {
          rules_compliance: [
            { rule: 'Data Completeness', compliance: 92, violations: 8 },
            { rule: 'Value Range', compliance: 95, violations: 5 },
            { rule: 'Format Validation', compliance: 88, violations: 12 },
            { rule: 'Cross-field Validation', compliance: 90, violations: 10 },
            { rule: 'Business Logic', compliance: 85, violations: 15 }
          ]
        }
      };
    }
  }
};
