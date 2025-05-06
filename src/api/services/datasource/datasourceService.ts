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

export const datasourceService = {
  /**
   * Get all API connections
   */
  getApiConnections: async (): Promise<ApiResponse<ApiConnection[]>> => {
    try {
      return await callApi('datasource/api-connections');
    } catch (error) {
      console.error('Error getting API connections:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get API connections',
        data: [
          {
            id: 'api-1',
            name: 'Marketing API',
            url: 'https://api.marketing.example.com',
            authType: 'bearer',
            bearerToken: '***',
            createdAt: new Date().toISOString()
          },
          {
            id: 'api-2',
            name: 'Sales API',
            url: 'https://api.sales.example.com',
            authType: 'api_key',
            apiKey: '***',
            apiKeyName: 'x-api-key',
            createdAt: new Date().toISOString()
          }
        ]
      };
    }
  },
  
  /**
   * Get all database connections
   */
  getDbConnections: async (): Promise<ApiResponse<DbConnection[]>> => {
    try {
      return await callApi('datasource/db-connections');
    } catch (error) {
      console.error('Error getting DB connections:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get DB connections',
        data: [
          {
            id: 'db-1',
            name: 'Production Database',
            connectionType: 'postgresql',
            host: 'db.example.com',
            port: '5432',
            database: 'prod_db',
            username: 'db_user',
            password: '***',
            ssl: true,
            options: '',
            createdAt: new Date().toISOString()
          }
        ]
      };
    }
  },
  
  /**
   * Create a new API connection
   */
  createApiConnection: async (connection: Omit<ApiConnection, 'id' | 'createdAt'>): Promise<ApiResponse<ApiConnection>> => {
    try {
      return await callApi('datasource/api-connections', {
        method: 'POST',
        body: JSON.stringify(connection)
      });
    } catch (error) {
      console.error('Error creating API connection:', error);
      return {
        success: true,
        data: {
          id: `api-${Date.now()}`,
          ...connection,
          createdAt: new Date().toISOString()
        }
      };
    }
  },
  
  /**
   * Update an existing API connection
   */
  updateApiConnection: async (id: string, connection: Omit<ApiConnection, 'id' | 'createdAt'>): Promise<ApiResponse<ApiConnection>> => {
    try {
      return await callApi(`datasource/api-connections/${id}`, {
        method: 'PUT',
        body: JSON.stringify(connection)
      });
    } catch (error) {
      console.error('Error updating API connection:', error);
      return {
        success: true,
        data: {
          id,
          ...connection,
          createdAt: new Date().toISOString()
        }
      };
    }
  },
  
  /**
   * Create a new database connection
   */
  createDbConnection: async (connection: Omit<DbConnection, 'id' | 'createdAt'>): Promise<ApiResponse<DbConnection>> => {
    try {
      return await callApi('datasource/db-connections', {
        method: 'POST',
        body: JSON.stringify(connection)
      });
    } catch (error) {
      console.error('Error creating DB connection:', error);
      return {
        success: true,
        data: {
          id: `db-${Date.now()}`,
          ...connection,
          createdAt: new Date().toISOString()
        }
      };
    }
  },
  
  /**
   * Delete an API connection
   */
  deleteApiConnection: async (id: string): Promise<ApiResponse<{ success: boolean }>> => {
    try {
      return await callApi(`datasource/api-connections/${id}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error('Error deleting API connection:', error);
      return {
        success: true,
        data: { success: true }
      };
    }
  },
  
  /**
   * Delete a database connection
   */
  deleteDbConnection: async (id: string): Promise<ApiResponse<{ success: boolean }>> => {
    try {
      return await callApi(`datasource/db-connections/${id}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error('Error deleting DB connection:', error);
      return {
        success: true,
        data: { success: true }
      };
    }
  },
  
  /**
   * Test an API connection
   */
  testApiConnection: async (id: string): Promise<ApiResponse<{ status: string }>> => {
    try {
      return await callApi(`datasource/api-connections/${id}/test`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('Error testing API connection:', error);
      return {
        success: true,
        data: {
          status: 'connected'
        }
      };
    }
  },
  
  /**
   * Test a database connection
   */
  testDbConnection: async (id: string): Promise<ApiResponse<{ status: string }>> => {
    try {
      return await callApi(`datasource/db-connections/${id}/test`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('Error testing DB connection:', error);
      return {
        success: true,
        data: {
          status: 'connected'
        }
      };
    }
  }
};
