
import { callApi, ApiCallOptions } from '@/utils/apiUtils';
import { ApiResponse, DataSource } from '@/api/types';

interface ApiConnection {
  id: string;
  name: string;
  url: string;
  authType: string;
  username?: string;
  password?: string;
  apiKey?: string;
  apiKeyName?: string;
  bearerToken?: string;
  headers?: string;
  createdAt: string;
}

interface DbConnection {
  id: string;
  name: string;
  connectionType: string;
  host: string;
  port: string;
  database: string;
  username?: string;
  password?: string;
  ssl: boolean;
  options?: string;
  createdAt: string;
}

export const datasourceService = {
  /**
   * Get all data sources
   */
  getDataSources: async (): Promise<ApiResponse<DataSource[]>> => {
    try {
      const options: ApiCallOptions = {
        method: 'GET'
      };
      return await callApi('datasources', options);
    } catch (error) {
      console.error("Error getting data sources:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to get data sources"
      };
    }
  },
  
  /**
   * Get a data source by ID
   */
  getDataSource: async (id: string): Promise<ApiResponse<DataSource>> => {
    try {
      const options: ApiCallOptions = {
        method: 'GET'
      };
      return await callApi(`datasources/${id}`, options);
    } catch (error) {
      console.error(`Error getting data source ${id}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to get data source"
      };
    }
  },
  
  /**
   * Create a new data source
   */
  createDataSource: async (dataSource: Omit<DataSource, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<DataSource>> => {
    try {
      const options: ApiCallOptions = {
        method: 'POST',
        body: JSON.stringify(dataSource)
      };
      return await callApi('datasources', options);
    } catch (error) {
      console.error("Error creating data source:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to create data source"
      };
    }
  },
  
  /**
   * Update a data source
   */
  updateDataSource: async (id: string, dataSource: Partial<DataSource>): Promise<ApiResponse<DataSource>> => {
    try {
      const options: ApiCallOptions = {
        method: 'PUT',
        body: JSON.stringify(dataSource)
      };
      return await callApi(`datasources/${id}`, options);
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
      const options: ApiCallOptions = {
        method: 'DELETE'
      };
      return await callApi(`datasources/${id}`, options);
    } catch (error) {
      console.error(`Error deleting data source ${id}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to delete data source"
      };
    }
  },
  
  /**
   * Test a connection to a data source
   */
  testConnection: async (id: string): Promise<ApiResponse<{ status: string }>> => {
    try {
      const options: ApiCallOptions = {
        method: 'POST'
      };
      return await callApi(`datasources/${id}/test`, options);
    } catch (error) {
      console.error(`Error testing connection for data source ${id}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to test connection"
      };
    }
  },
  
  /**
   * Get all API connections
   */
  getApiConnections: async (): Promise<ApiResponse<ApiConnection[]>> => {
    try {
      const options: ApiCallOptions = {
        method: 'GET'
      };
      return await callApi('datasources/api-connections', options);
    } catch (error) {
      console.error("Error getting API connections:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to get API connections"
      };
    }
  },
  
  /**
   * Get all database connections
   */
  getDbConnections: async (): Promise<ApiResponse<DbConnection[]>> => {
    try {
      const options: ApiCallOptions = {
        method: 'GET'
      };
      return await callApi('datasources/db-connections', options);
    } catch (error) {
      console.error("Error getting database connections:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to get database connections"
      };
    }
  },
  
  /**
   * Create an API connection
   */
  createApiConnection: async (connection: Omit<ApiConnection, 'id' | 'createdAt'>): Promise<ApiResponse<ApiConnection>> => {
    try {
      const options: ApiCallOptions = {
        method: 'POST',
        body: JSON.stringify(connection)
      };
      return await callApi('datasources/api-connections', options);
    } catch (error) {
      console.error("Error creating API connection:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to create API connection"
      };
    }
  },
  
  /**
   * Update an API connection
   */
  updateApiConnection: async (id: string, connection: Partial<ApiConnection>): Promise<ApiResponse<ApiConnection>> => {
    try {
      const options: ApiCallOptions = {
        method: 'PUT',
        body: JSON.stringify(connection)
      };
      return await callApi(`datasources/api-connections/${id}`, options);
    } catch (error) {
      console.error(`Error updating API connection ${id}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to update API connection"
      };
    }
  },
  
  /**
   * Create a database connection
   */
  createDbConnection: async (connection: Omit<DbConnection, 'id' | 'createdAt'>): Promise<ApiResponse<DbConnection>> => {
    try {
      const options: ApiCallOptions = {
        method: 'POST',
        body: JSON.stringify(connection)
      };
      return await callApi('datasources/db-connections', options);
    } catch (error) {
      console.error("Error creating database connection:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to create database connection"
      };
    }
  },
  
  /**
   * Delete an API connection
   */
  deleteApiConnection: async (id: string): Promise<ApiResponse<void>> => {
    try {
      const options: ApiCallOptions = {
        method: 'DELETE'
      };
      return await callApi(`datasources/api-connections/${id}`, options);
    } catch (error) {
      console.error(`Error deleting API connection ${id}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to delete API connection"
      };
    }
  },
  
  /**
   * Delete a database connection
   */
  deleteDbConnection: async (id: string): Promise<ApiResponse<void>> => {
    try {
      const options: ApiCallOptions = {
        method: 'DELETE'
      };
      return await callApi(`datasources/db-connections/${id}`, options);
    } catch (error) {
      console.error(`Error deleting database connection ${id}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to delete database connection"
      };
    }
  },
  
  /**
   * Test an API connection
   */
  testApiConnection: async (id: string): Promise<ApiResponse<{ status: string }>> => {
    try {
      const options: ApiCallOptions = {
        method: 'POST'
      };
      return await callApi(`datasources/api-connections/${id}/test`, options);
    } catch (error) {
      console.error(`Error testing API connection ${id}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to test API connection"
      };
    }
  },
  
  /**
   * Test a database connection
   */
  testDbConnection: async (id: string): Promise<ApiResponse<{ status: string }>> => {
    try {
      const options: ApiCallOptions = {
        method: 'POST'
      };
      return await callApi(`datasources/db-connections/${id}/test`, options);
    } catch (error) {
      console.error(`Error testing database connection ${id}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to test database connection"
      };
    }
  }
};
