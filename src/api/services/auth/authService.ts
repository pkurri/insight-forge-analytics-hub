
import { callApi, ApiCallOptions } from '@/utils/apiUtils';
import { ApiResponse } from '@/api/types';

export interface AuthUser {
  id: string;
  username: string;
  role: string;
}

export interface AuthResponseData {
  token: string;
  user: AuthUser;
}

interface AuthResponse extends ApiResponse<AuthResponseData> {}

class AuthService {
  private tokenKey = 'auth_token';
  private userKey = 'user_data';
  
  // Demo user credentials
  private demoUser: AuthUser = {
    id: 'demo-123',
    username: 'demo',
    role: 'viewer'
  };
  private demoToken = 'demo-token-xyz-123';
  private demoPassword = 'demo123';

  async login(username: string, password: string): Promise<AuthResponse> {
    try {
      // Check for demo user first
      if (username === this.demoUser.username && password === this.demoPassword) {
        console.log('Demo login successful');
        // Store demo credentials
        localStorage.setItem(this.tokenKey, this.demoToken);
        localStorage.setItem(this.userKey, JSON.stringify(this.demoUser));
        
        return {
          success: true,
          data: {
            token: this.demoToken,
            user: this.demoUser
          }
        };
      }
      
      // Normal authentication flow
      const options: ApiCallOptions = {
        method: 'POST',
        body: { username, password }
      };
      
      const response = await callApi('/auth/login', options);

      if (response.success && response.data) {
        localStorage.setItem(this.tokenKey, response.data.token);
        localStorage.setItem(this.userKey, JSON.stringify(response.data.user));
      }

      return response as AuthResponse;
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Login failed',
      };
    }
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
    window.location.href = '/login';
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem(this.tokenKey);
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  getUser(): AuthUser | null {
    const userData = localStorage.getItem(this.userKey);
    return userData ? JSON.parse(userData) : null;
  }
}

export const authService = new AuthService();
