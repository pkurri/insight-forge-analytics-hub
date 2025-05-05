
import { callApi } from '../../../utils/apiUtils';
import { DataSource, ApiResponse } from '../../../api/types';

/**
 * Data Source Service - Handles operations related to data sources
 */
export const datasourceService = {
  /**
   * Get all available data sources
   */
  getDataSources: async (): Promise<ApiResponse<DataSource[]>> => {
    try {
      const response = await callApi('datasources');
      return response;
    } catch (error) {
      console.error("Error fetching data sources:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to fetch data sources"
      };
    }
  },

  /**
   * Get a specific data source by ID
   */
  getDataSource: async (id: string): Promise<ApiResponse<DataSource>> => {
    try {
      const response = await callApi(`datasources/${id}`);
      return response;
    } catch (error) {
      console.error(`Error fetching data source ${id}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to fetch data source"
      };
    }
  },

  /**
   * Create a new data source
   */
  createDataSource: async (dataSource: Omit<DataSource, 'id'>): Promise<ApiResponse<DataSource>> => {
    try {
      const response = await callApi('datasources', {
        method: 'POST',
        body: dataSource
      });
      return response;
    } catch (error) {
      console.error("Error creating data source:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to create data source"
      };
    }
  },

  /**
   * Update an existing data source
   */
  updateDataSource: async (id: string, dataSource: Partial<DataSource>): Promise<ApiResponse<DataSource>> => {
    try {
      const response = await callApi(`datasources/${id}`, {
        method: 'PUT',
        body: dataSource
      });
      return response;
    } catch (error) {
      console.error(`Error updating data source ${id}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to update data source"
      };
    }
  },

  /**
   * Delete a data source
   */
  deleteDataSource: async (id: string): Promise<ApiResponse<void>> => {
    try {
      const response = await callApi(`datasources/${id}`, {
        method: 'DELETE'
      });
      return response;
    } catch (error) {
      console.error(`Error deleting data source ${id}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to delete data source"
      };
    }
  },

  /**
   * Test connection to a data source
   */
  testConnection: async (dataSource: Partial<DataSource>): Promise<ApiResponse<{ connectable: boolean }>> => {
    try {
      const response = await callApi('datasources/test-connection', {
        method: 'POST',
        body: dataSource
      });
      return response;
    } catch (error) {
      console.error("Error testing data source connection:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to test data source connection"
      };
    }
  }
};
