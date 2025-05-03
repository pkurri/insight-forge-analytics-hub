import { callApi } from '@/api/utils/apiUtils';
import { ApiResponse } from '@/api/types';

export interface ApiConnection {
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

export interface DbConnection {
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

/**
 * Service for managing data source connections (API and Database)
 */
export const datasourceService = {
  /**
   * Get all API connections
   */
  getApiConnections: async (): Promise<ApiResponse> => {
    try {
      return await callApi('/datasource/api', { method: 'GET' });
    } catch (error) {
      console.error('Error fetching API connections:', error);
      return {
        success: false,
        error: 'Failed to fetch API connections',
        data: null
      };
    }
  },

  /**
   * Get all database connections
   */
  getDbConnections: async (): Promise<ApiResponse> => {
    try {
      return await callApi('/datasource/db', { method: 'GET' });
    } catch (error) {
      console.error('Error fetching database connections:', error);
      return {
        success: false,
        error: 'Failed to fetch database connections',
        data: null
      };
    }
  },

  /**
   * Create a new API connection
   */
  createApiConnection: async (connection: Omit<ApiConnection, 'id' | 'createdAt'>): Promise<ApiResponse> => {
    try {
      return await callApi('/datasource/api', { method: 'POST', body: JSON.stringify(connection) });
    } catch (error) {
      console.error('Error creating API connection:', error);
      return {
        success: false,
        error: 'Failed to create API connection',
        data: null
      };
    }
  },

  /**
   * Create a new database connection
   */
  createDbConnection: async (connection: Omit<DbConnection, 'id' | 'createdAt'>): Promise<ApiResponse> => {
    try {
      return await callApi('/datasource/db', { method: 'POST', body: JSON.stringify(connection) });
    } catch (error) {
      console.error('Error creating database connection:', error);
      return {
        success: false,
        error: 'Failed to create database connection',
        data: null
      };
    }
  },

  /**
   * Delete an API connection
   */
  deleteApiConnection: async (id: string): Promise<ApiResponse> => {
    try {
      return await callApi(`/datasource/api/${id}`, { method: 'DELETE' });
    } catch (error) {
      console.error('Error deleting API connection:', error);
      return {
        success: false,
        error: 'Failed to delete API connection',
        data: null
      };
    }
  },

  /**
   * Delete a database connection
   */
  deleteDbConnection: async (id: string): Promise<ApiResponse> => {
    try {
      return await callApi(`/datasource/db/${id}`, { method: 'DELETE' });
    } catch (error) {
      console.error('Error deleting database connection:', error);
      return {
        success: false,
        error: 'Failed to delete database connection',
        data: null
      };
    }
  },

  /**
   * Update an existing API connection
   */
  updateApiConnection: async (id: string, connection: Omit<ApiConnection, 'id' | 'createdAt'>): Promise<ApiResponse> => {
    try {
      return await callApi(`/datasource/api/${id}`, { method: 'PUT', body: JSON.stringify(connection) });
    } catch (error) {
      console.error('Error updating API connection:', error);
      return {
        success: false,
        error: 'Failed to update API connection',
        data: null
      };
    }
  },

  /**
   * Update an existing database connection
   */
  updateDbConnection: async (id: string, connection: Omit<DbConnection, 'id' | 'createdAt'>): Promise<ApiResponse> => {
    try {
      return await callApi(`/datasource/db/${id}`, { method: 'PUT', body: JSON.stringify(connection) });
    } catch (error) {
      console.error('Error updating database connection:', error);
      return {
        success: false,
        error: 'Failed to update database connection',
        data: null
      };
    }
  },

  /**
   * Test an API connection by id
   */
  testApiConnection: async (id: string): Promise<ApiResponse> => {
    try {
      // Fetch the connection first
      const connResp = await callApi(`/datasource/api/${id}`, { method: 'GET' });
      if (!connResp.success || !connResp.data) {
        return { success: false, error: 'API connection not found', data: null };
      }
      return await callApi('/datasource/api/test', { method: 'POST', body: JSON.stringify(connResp.data) });
    } catch (error) {
      console.error('Error testing API connection:', error);
      return {
        success: false,
        error: 'Failed to test API connection',
        data: null
      };
    }
  },

  /**
   * Test a database connection by id
   */
  testDbConnection: async (id: string): Promise<ApiResponse> => {
    try {
      // Fetch the connection first
      const connResp = await callApi(`/datasource/db/${id}`, { method: 'GET' });
      if (!connResp.success || !connResp.data) {
        return { success: false, error: 'DB connection not found', data: null };
      }
      return await callApi('/datasource/db/test', { method: 'POST', body: JSON.stringify(connResp.data) });
    } catch (error) {
      console.error('Error testing database connection:', error);
      return {
        success: false,
        error: 'Failed to test database connection',
        data: null
      };
    }
  }
};
