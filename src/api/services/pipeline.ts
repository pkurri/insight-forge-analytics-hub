import { callApi } from '../utils/apiUtils';
import { ApiResponse } from '../api';

export type FileType = 'csv' | 'json' | 'excel' | 'parquet';
export type SourceType = 'file' | 'api' | 'database';
export type DatasetStatus = 'pending' | 'processing' | 'completed' | 'error';

export interface ApiConfig {
    url: string;
    method: string;
    headers?: Record<string, string>;
    body?: any;
}

export interface DatabaseConfig {
    type: string;
    host: string;
    port: number;
    database: string;
    username: string;
    password: string;
    query: string;
}

export interface UploadData {
    file?: File;
    fileType?: FileType;
    apiConfig?: ApiConfig;
    dbConfig?: DatabaseConfig;
    name?: string;
    description?: string;
}

export interface Dataset {
    id: number;
    name: string;
    description?: string;
    fileType: FileType;
    sourceType: SourceType;
    sourceInfo?: Record<string, any>;
    status: DatasetStatus;
    error?: string;
    rowCount?: number;
    columnCount?: number;
    columns?: Array<{
        name: string;
        dataType: string;
        nullable: boolean;
    }>;
    filePath?: string;
    cleaningMetadata?: Record<string, any>;
    validationResults?: Record<string, any>;
    profileData?: Record<string, any>;
    anomalies?: Record<string, any>;
    createdAt: string;
    updatedAt: string;
}

export interface PipelineStep {
    id: number;
    type: string;
    status: string;
    config?: Record<string, any>;
    result?: Record<string, any>;
    error?: string;
    startedAt?: string;
    completedAt?: string;
}

export interface PipelineRun {
    id: number;
    datasetId: number;
    status: string;
    steps: PipelineStep[];
    startedAt: string;
    completedAt?: string;
    error?: string;
}

class PipelineService {
    async uploadData(data: UploadData): Promise<ApiResponse<Dataset>> {
        const formData = new FormData();
        
        if (data.file) {
            formData.append('file', data.file);
        }
        if (data.fileType) {
            formData.append('file_type', data.fileType);
        }
        if (data.apiConfig) {
            formData.append('api_config', JSON.stringify(data.apiConfig));
        }
        if (data.dbConfig) {
            formData.append('db_config', JSON.stringify(data.dbConfig));
        }
        if (data.name) {
            formData.append('name', data.name);
        }
        if (data.description) {
            formData.append('description', data.description);
        }
        
        return callApi('pipeline/upload', {
            method: 'POST',
            body: formData
        });
    }
    
    async getDataset(datasetId: number): Promise<ApiResponse<Dataset>> {
        return callApi(`pipeline/datasets/${datasetId}`, {
            method: 'GET'
        });
    }
    
    async listDatasets(
        sourceType?: SourceType,
        skip: number = 0,
        limit: number = 100
    ): Promise<ApiResponse<Dataset[]>> {
        const params = new URLSearchParams();
        if (sourceType) {
            params.append('source_type', sourceType);
        }
        params.append('skip', skip.toString());
        params.append('limit', limit.toString());
        
        return callApi(`pipeline/datasets?${params.toString()}`, {
            method: 'GET'
        });
    }
    
    async runPipelineStep(
        datasetId: number,
        stepType: string,
        config?: Record<string, any>
    ): Promise<ApiResponse<PipelineStep>> {
        return callApi(`pipeline/datasets/${datasetId}/steps`, {
            method: 'POST',
            body: JSON.stringify({
                type: stepType,
                config
            })
        });
    }
    
    async getPipelineRun(runId: number): Promise<ApiResponse<PipelineRun>> {
        return callApi(`pipeline/runs/${runId}`, {
            method: 'GET'
        });
    }
    
    async deleteDataset(datasetId: number): Promise<ApiResponse<void>> {
        return callApi(`pipeline/datasets/${datasetId}`, {
            method: 'DELETE'
        });
    }
}

export const pipelineService = new PipelineService(); 