import api from './api';

interface LoginResponse {
  success: boolean;
  token?: string;
  error?: string;
}

interface UserData {
  username: string;
  role: string;
  is_admin: boolean;
}

export const authService = {
  async login(username: string, password: string): Promise<LoginResponse> {
    try {
      // For admin/admin credentials, return a mock successful response
      if (username === 'admin' && password === 'admin') {
        const mockToken = 'mock-jwt-token-for-admin';
        const userData: UserData = {
          username: 'admin',
          role: 'admin',
          is_admin: true
        };

        // Store token in localStorage for API requests
        localStorage.setItem('apiToken', mockToken);
        
        // Set default authorization header for all future requests
        api.defaults.headers.common['Authorization'] = `Bearer ${mockToken}`;

        return {
          success: true,
          token: mockToken
        };
      }

      return {
        success: false,
        error: 'Invalid credentials'
      };
    } catch (error) {
      return {
        success: false,
        error: 'An error occurred during login'
      };
    }
  },

  async logout(): Promise<void> {
    // Remove token from localStorage
    localStorage.removeItem('apiToken');
    
    // Remove authorization header
    delete api.defaults.headers.common['Authorization'];
  },

  getToken(): string | null {
    return localStorage.getItem('apiToken');
  },

  isAuthenticated(): boolean {
    return !!this.getToken();
  }
}; 