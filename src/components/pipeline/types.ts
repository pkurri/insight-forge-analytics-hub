import { ReactNode } from 'react';
import { StepStatus } from './PipelineStep';

/**
 * Data source types for the pipeline
 */
export type DataSource = 'local' | 'api' | 'database';

/**
 * File types supported by the pipeline
 */
export type FileType = 'csv' | 'json' | 'excel' | 'parquet';

/**
 * API configuration for API data source
 */
export interface ApiConfig {
  url: string;
  method: 'GET' | 'POST';
  headers?: Record<string, string>;
  body?: string;
}

/**
 * Database configuration for database data source
 */
export interface DatabaseConfig {
  type: 'postgresql' | 'mysql' | 'sqlserver' | 'oracle';
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  query: string;
}

/**
 * Validation result from the validation step
 */
export interface ValidationResult {
  success: boolean;
  errors?: string[];
  warnings?: string[];
  data?: any;
}

/**
 * Business rule model
 */
export interface BusinessRule {
  id: string;
  name: string;
  description: string;
  type: string;
  severity: string;
  condition: string;
  action?: string;
}

/**
 * Pipeline step model
 */
export interface PipelineStep {
  name: string;
  status: StepStatus;
  description: string;
  icon: ReactNode;
  details: string;
}

/**
 * Stage loading state for pipeline steps
 */
export interface StageLoading {
  validate: boolean;
  rules: boolean;
  transform: boolean;
  enrich: boolean;
  load: boolean;
}

/**
 * Props for the PipelineUploadForm component
 */
export interface PipelineUploadFormProps {
  onUploadComplete?: (datasetId: string) => void;
}
