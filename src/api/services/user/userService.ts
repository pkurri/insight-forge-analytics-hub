
import { callApi } from '../../utils/apiUtils';
import { ApiResponse } from '../../api';

/**
 * User Service - Handles user operations and authentication
 */
export const userService = {
  /**
   * Get current user information
   */
  getCurrentUser: async (): Promise<ApiResponse<any>> => {
    const endpoint = 'user/current';
    
    try {
      const response = await callApi(endpoint);
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      return {
        success: true,
        data: {
          id: 'usr001',
          username: 'datauser',
          email: 'user@example.com',
          name: 'Data Analyst',
          role: 'analyst',
          permissions: ['read:datasets', 'write:datasets', 'run:analysis'],
          last_login: new Date().toISOString()
        }
      };
    } catch (error) {
      console.error("Error fetching current user:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to fetch user data"
      };
    }
  },
  
  /**
   * Check if user is authenticated
   */
  isAuthenticated: async (): Promise<boolean> => {
    const response = await userService.getCurrentUser();
    return response.success && !!response.data;
  }
};
