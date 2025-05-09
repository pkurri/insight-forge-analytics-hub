
import { authService } from '@/api/services/auth/authService';
import { analyticsService } from '@/api/services/analytics/analyticsService';
import { pipelineService } from '@/api/services/pipeline/pipelineService'; 
import { businessRulesService } from '@/api/services/businessRules/businessRulesService';
import { datasourceService } from '@/api/services/datasource/datasourceService';
import { aiService } from '@/api/services/aiService';
import { conversationAnalyticsService } from '@/api/services/analytics/conversationAnalyticsService';

export interface Dataset {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt?: string;
  size?: number;
  format?: string;
  status?: string;
  fileType?: string;
  recordCount?: number;
  columnCount?: number;
  metadata?: Record<string, any>;
}

// Define agent interface
export interface Agent {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
}

// API service aggregator
export const api = {
  auth: authService,
  analytics: analyticsService,
  pipeline: pipelineService,
  businessRules: businessRulesService,
  datasource: datasourceService,
  aiService: aiService,
  
  // Datasets service
  datasets: {
    uploadDataset: async (formData: FormData) => {
      return pipelineService.uploadData(formData);
    },
    
    getDatasets: async () => {
      // Use the pipelineService.getDatasets method
      return pipelineService.getDatasets();
    }
  },
  
  // Analytics methods
  getDatasetAnalytics: async (datasetId: string) => {
    try {
      return await analyticsService.profileDataset(datasetId);
    } catch (error) {
      console.error('Error getting dataset analytics:', error);
      return { success: false, error: 'Failed to fetch dataset analytics' };
    }
  },
  
  getGlobalAnalytics: async () => {
    try {
      // Get first dataset and return its analytics
      const datasets = await pipelineService.getDatasets();
      if (datasets.success && datasets.data && datasets.data.length > 0) {
        return await analyticsService.profileDataset(datasets.data[0].id);
      }
      return { success: false, error: 'No datasets available for analytics' };
    } catch (error) {
      console.error('Error getting global analytics:', error);
      return { success: false, error: 'Failed to fetch global analytics' };
    }
  },
  
  // Dashboard methods
  getDashboardMetrics: async () => {
    try {
      return { 
        success: true, 
        data: {
          totalDatasets: 12,
          processedPipelines: 45,
          aiInteractions: 876,
          datasetChange: 2,
          pipelineChange: 8,
          interactionsChange: 12,
          activityData: [],
          resourceData: [],
          recentActivities: [],
          datasets: []
        }
      };
    } catch (error) {
      console.error('Error getting dashboard metrics:', error);
      return { success: false, error: 'Failed to fetch dashboard metrics' };
    }
  },
  
  getProjectQualityScores: async () => {
    try {
      return { 
        success: true, 
        data: {
          codebase: { average_score: 85, last_evaluation: new Date().toISOString() },
          pipeline: { average_score: 92, last_evaluation: new Date().toISOString() },
          analytics: { average_score: 78, last_evaluation: new Date().toISOString() }
        }
      };
    } catch (error) {
      console.error('Error getting project quality scores:', error);
      return { success: false, error: 'Failed to fetch project quality scores' };
    }
  },
  
  runProjectEvaluation: async () => {
    try {
      return { success: true, data: { status: 'evaluation_started' } };
    } catch (error) {
      console.error('Error running project evaluation:', error);
      return { success: false, error: 'Failed to run project evaluation' };
    }
  },
  
  // Component evaluation
  evaluateRuntimeComponent: async (componentName: string) => {
    try {
      return { 
        success: true, 
        data: { 
          score: 85, 
          suggestions: [
            'Consider adding proper error handling for network requests',
            'Add loading states for better user experience',
            'Implement proper data validation'
          ]
        }
      };
    } catch (error) {
      console.error('Error evaluating component:', error);
      return { success: false, error: 'Failed to evaluate component' };
    }
  },
  
  showComponentSuggestions: async (componentName: string) => {
    console.log(`Showing suggestions for component: ${componentName}`);
    return { success: true };
  },

  // AI Agents
  agents: {
    getAgents: async (): Promise<{ success: boolean, data: Agent[] }> => {
      return { 
        success: true, 
        data: [
          {
            id: 'data-analyst',
            name: 'Data Analyst',
            description: 'Specialized in analyzing datasets and extracting insights',
            capabilities: ['Data analysis', 'Visualization suggestions', 'Anomaly detection']
          },
          {
            id: 'code-assistant',
            name: 'Code Assistant',
            description: 'Helps with coding tasks and pipeline optimization',
            capabilities: ['Code generation', 'Debugging', 'Performance optimization']
          }
        ] 
      };
    }
  }
};

export type { ApiResponse } from '@/api/types';
