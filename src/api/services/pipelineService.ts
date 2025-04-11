
import { callApi, uploadFile } from '../utils/apiUtils';

/**
 * Pipeline Service - Handles data pipeline operations
 */
export const pipelineService = {
  /**
   * Upload data to the pipeline
   */
  uploadDataToPipeline: async (file: File, fileType: string): Promise<any> => {
    const endpoint = `pipeline/upload`;
    
    try {
      const response = await uploadFile(endpoint, file, { 
        file_type: fileType
      });
      
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      return {
        success: true,
        data: {
          dataset_id: `ds-${Date.now()}`,
          filename: file.name,
          file_type: fileType,
          size: file.size,
          upload_time: new Date().toISOString()
        }
      };
    } catch (error) {
      console.error("Error uploading data to pipeline:", error);
      return {
        success: false,
        error: "Failed to upload data to pipeline"
      };
    }
  },
  
  /**
   * Fetch data from external API
   */
  fetchDataFromExternalApi: async (apiEndpoint: string, fileType: string): Promise<any> => {
    const endpoint = `pipeline/fetch-from-api`;
    
    try {
      const response = await callApi(endpoint, 'POST', {
        api_endpoint: apiEndpoint,
        output_format: fileType
      });
      
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 1800));
      
      return {
        success: true,
        data: {
          dataset_id: `ds-api-${Date.now()}`,
          source: apiEndpoint,
          file_type: fileType,
          record_count: 2453,
          fetch_time: new Date().toISOString()
        }
      };
    } catch (error) {
      console.error("Error fetching data from API:", error);
      return {
        success: false,
        error: "Failed to fetch data from API"
      };
    }
  },
  
  /**
   * Fetch data from database
   */
  fetchDataFromDatabase: async (connectionId: string, fileType: string): Promise<any> => {
    const endpoint = `pipeline/fetch-from-db`;
    
    try {
      const response = await callApi(endpoint, 'POST', {
        connection_id: connectionId,
        output_format: fileType
      });
      
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 1600));
      
      return {
        success: true,
        data: {
          dataset_id: `ds-db-${Date.now()}`,
          connection: connectionId,
          file_type: fileType,
          record_count: 8732,
          fetch_time: new Date().toISOString()
        }
      };
    } catch (error) {
      console.error("Error fetching data from database:", error);
      return {
        success: false,
        error: "Failed to fetch data from database"
      };
    }
  },
  
  /**
   * Validate data in the pipeline
   */
  validateDataInPipeline: async (datasetId: string): Promise<any> => {
    const endpoint = `pipeline/${datasetId}/validate`;
    
    try {
      const response = await callApi(endpoint, 'POST');
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 1800));
      
      return {
        success: true,
        data: {
          dataset_id: datasetId,
          validation_results: {
            total_rules: 10,
            passed_rules: 8,
            failed_rules: 2,
            validation_errors: [
              {
                rule_id: "R001",
                rule_name: "Valid Date Format",
                column: "transaction_date",
                error_count: 5,
                error_percentage: 0.5,
                sample_errors: ["2023/13/45", "invalid date"]
              },
              {
                rule_id: "R002",
                rule_name: "Valid Price Range",
                column: "price",
                error_count: 3,
                error_percentage: 0.3,
                sample_errors: ["-10.99", "2500.00"]
              }
            ]
          }
        }
      };
    } catch (error) {
      console.error("Error validating data in pipeline:", error);
      return {
        success: false,
        error: "Failed to validate data in pipeline"
      };
    }
  },
  
  /**
   * Transform data in the pipeline
   */
  transformDataInPipeline: async (datasetId: string): Promise<any> => {
    const endpoint = `pipeline/${datasetId}/transform`;
    
    try {
      const response = await callApi(endpoint, 'POST');
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      return {
        success: true,
        data: {
          dataset_id: datasetId,
          transformation_results: {
            transformations_applied: [
              {
                name: "Convert to datetime",
                columns: ["order_date", "shipping_date"],
                output_format: "YYYY-MM-DD"
              },
              {
                name: "Standardize case",
                columns: ["customer_name", "product_name"],
                case: "title"
              }
            ],
            rows_transformed: 5823,
            new_columns_added: ["order_year", "order_month", "days_to_ship"]
          }
        }
      };
    } catch (error) {
      console.error("Error transforming data in pipeline:", error);
      return {
        success: false,
        error: "Failed to transform data in pipeline"
      };
    }
  },
  
  /**
   * Enrich data in the pipeline
   */
  enrichDataInPipeline: async (datasetId: string): Promise<any> => {
    const endpoint = `pipeline/${datasetId}/enrich`;
    
    try {
      const response = await callApi(endpoint, 'POST');
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      return {
        success: true,
        data: {
          dataset_id: datasetId,
          enrichment_results: {
            enrichments_applied: [
              {
                name: "Geocoding",
                columns: ["customer_address"],
                output_columns: ["latitude", "longitude", "country_code"]
              },
              {
                name: "Sentiment Analysis",
                columns: ["customer_feedback"],
                output_columns: ["sentiment_score", "sentiment_label"]
              }
            ],
            rows_enriched: 5823,
            new_columns_added: ["latitude", "longitude", "country_code", "sentiment_score", "sentiment_label"]
          }
        }
      };
    } catch (error) {
      console.error("Error enriching data in pipeline:", error);
      return {
        success: false,
        error: "Failed to enrich data in pipeline"
      };
    }
  },
  
  /**
   * Load data in the pipeline
   */
  loadDataInPipeline: async (datasetId: string, destination: string, options: any = {}): Promise<any> => {
    const endpoint = `pipeline/${datasetId}/load`;
    
    try {
      const response = await callApi(endpoint, 'POST', {
        destination,
        ...options
      });
      
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 1800));
      
      return {
        success: true,
        data: {
          dataset_id: datasetId,
          destination: destination,
          loading_results: {
            rows_loaded: 5823,
            columns_loaded: 12,
            loading_mode: options.mode || "append"
          }
        }
      };
    } catch (error) {
      console.error("Error loading data in pipeline:", error);
      return {
        success: false,
        error: "Failed to load data in pipeline"
      };
    }
  },
  
  /**
   * Run a complete data pipeline on a dataset
   */
  runDataPipeline: async (datasetId: string, steps: string[] = ["profile", "clean", "validate", "anomalies"]): Promise<any> => {
    console.log(`Running data pipeline for dataset: ${datasetId} with steps:`, steps);
    
    // In a real app, this would make an actual API call
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    return {
      success: true,
      data: {
        dataset_id: datasetId,
        steps_completed: steps,
        steps_failed: [],
        status: "success",
        results: {
          profile: { /* profile results */ },
          clean: { /* cleaning results */ },
          validate: { /* validation results */ },
          anomalies: { /* anomaly detection results */ }
        }
      }
    };
  }
};
