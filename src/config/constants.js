/**
 * Application Constants
 * 
 * This file contains constants used throughout the application.
 */

// API Base URL - Change this based on environment
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Other constants
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
export const SUPPORTED_FILE_TYPES = ['.csv', '.json', '.xlsx', '.xls', '.parquet'];

// Business Rules constants
export const RULE_TYPES = [
  { value: 'validation', label: 'Validation' },
  { value: 'transformation', label: 'Transformation' },
  { value: 'enrichment', label: 'Enrichment' }
];

export const RULE_SEVERITIES = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' }
];

export const RULE_SOURCES = [
  { value: 'manual', label: 'Manual' },
  { value: 'ai', label: 'AI Generated' },
  { value: 'imported', label: 'Imported' }
];
