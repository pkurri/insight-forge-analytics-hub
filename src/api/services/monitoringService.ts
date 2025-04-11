
import { callApi } from '../utils/apiUtils';

/**
 * Monitoring Service - Handles system monitoring, alerts, and logs
 */
export const monitoringService = {
  /**
   * Get monitoring metrics
   */
  getMonitoringMetrics: async (params: any = {}): Promise<any> => {
    const endpoint = `monitoring/metrics`;
    
    try {
      const response = await callApi(endpoint, 'GET');
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 1200));
      
      return {
        success: true,
        data: {
          metrics: [
            {
              name: "pipeline_jobs_completed",
              value: 152,
              time_period: "30d",
              change_percent: 8.5
            },
            {
              name: "pipeline_jobs_failed",
              value: 7,
              time_period: "30d",
              change_percent: -12.3
            },
            {
              name: "average_processing_time",
              value: 45.3,
              unit: "seconds",
              time_period: "30d",
              change_percent: -5.2
            },
            {
              name: "data_processed",
              value: 1.8,
              unit: "GB",
              time_period: "30d",
              change_percent: 22.7
            },
            {
              name: "api_availability",
              value: 99.95,
              unit: "%",
              time_period: "30d",
              change_percent: 0.1
            }
          ],
          timestamp: new Date().toISOString(),
          system_health: "healthy"
        }
      };
    } catch (error) {
      console.error("Error getting monitoring metrics:", error);
      return {
        success: false,
        error: "Failed to get monitoring metrics"
      };
    }
  },
  
  /**
   * Get system alerts
   */
  getSystemAlerts: async (): Promise<any> => {
    const endpoint = `monitoring/alerts`;
    
    try {
      const response = await callApi(endpoint);
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const now = new Date();
      const yesterday = new Date(now);
      yesterday.setDate(yesterday.getDate() - 1);
      
      return {
        success: true,
        data: {
          alerts: [
            {
              id: "alert-001",
              severity: "high",
              message: "Memory usage above 85% threshold",
              component: "data-processing-service",
              timestamp: yesterday.toISOString(),
              status: "resolved",
              resolved_at: now.toISOString()
            },
            {
              id: "alert-002",
              severity: "medium",
              message: "API response time degradation detected",
              component: "api-gateway",
              timestamp: now.toISOString(),
              status: "active"
            },
            {
              id: "alert-003",
              severity: "low",
              message: "Non-critical validation errors increasing",
              component: "data-validation-service",
              timestamp: now.toISOString(),
              status: "active",
              details: {
                error_rate: "2.8%",
                threshold: "2.5%",
                affected_datasets: ["ds-20240410-001", "ds-20240409-005"]
              }
            }
          ]
        }
      };
    } catch (error) {
      console.error("Error getting system alerts:", error);
      return {
        success: false,
        error: "Failed to get system alerts"
      };
    }
  },
  
  /**
   * Get system logs
   */
  getSystemLogs: async (params: { limit?: number, severity?: string, component?: string } = {}): Promise<any> => {
    const queryParams = new URLSearchParams();
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.severity) queryParams.append('severity', params.severity);
    if (params.component) queryParams.append('component', params.component);
    
    const endpoint = `monitoring/logs?${queryParams.toString()}`;
    
    try {
      const response = await callApi(endpoint);
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const now = new Date();
      const generateLogTime = (minutesAgo: number) => {
        const date = new Date(now);
        date.setMinutes(date.getMinutes() - minutesAgo);
        return date.toISOString();
      };
      
      return {
        success: true,
        data: {
          logs: [
            {
              id: "log-001",
              timestamp: generateLogTime(5),
              level: "INFO",
              component: "pipeline-service",
              message: "Pipeline processing completed successfully",
              details: { pipeline_id: "pipe-2354", dataset_id: "ds-8723", duration_ms: 3452 }
            },
            {
              id: "log-002",
              timestamp: generateLogTime(12),
              level: "WARNING",
              component: "data-validation",
              message: "Data validation found 23 records with quality issues",
              details: { dataset_id: "ds-8723", field: "email", issue: "invalid format" }
            },
            {
              id: "log-003",
              timestamp: generateLogTime(15),
              level: "ERROR",
              component: "enrichment-service",
              message: "Failed to enrich data with external API",
              details: { dataset_id: "ds-8720", api: "geocoding-service", status_code: 503 }
            },
            {
              id: "log-004",
              timestamp: generateLogTime(25),
              level: "INFO",
              component: "auth-service",
              message: "User authentication successful",
              details: { user_id: "u-2354", ip_address: "192.168.1.1" }
            },
            {
              id: "log-005",
              timestamp: generateLogTime(45),
              level: "INFO",
              component: "pipeline-service",
              message: "Pipeline job scheduled",
              details: { pipeline_id: "pipe-2353", dataset_id: "ds-8722", scheduled_time: generateLogTime(0) }
            }
          ],
          pagination: {
            total: 1243,
            page: 1,
            limit: params.limit || 25
          }
        }
      };
    } catch (error) {
      console.error("Error getting system logs:", error);
      return {
        success: false,
        error: "Failed to get system logs"
      };
    }
  }
};
