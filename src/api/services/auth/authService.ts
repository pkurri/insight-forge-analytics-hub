
import { callApi, ApiCallOptions } from '@/utils/apiUtils';

export interface AuthUser {
  id: string;
  username: string;
  role: string;
}

export interface AuthResponseData {
  token: string;
  user: AuthUser;
}

interface AuthResponse {
  success: boolean;
  data?: AuthResponseData;
  error?: string;
}

class AuthService {
  private tokenKey = 'auth_token';
  private userKey = 'user_data';

  async login(username: string, password: string): Promise<AuthResponse> {
    try {
      const options: ApiCallOptions = {
        method: 'POST',
        body: { username, password }
      };
      
      const response = await callApi('/auth/login', options);

      if (response.success && response.data) {
        localStorage.setItem(this.tokenKey, response.data.token);
        localStorage.setItem(this.userKey, JSON.stringify(response.data.user));
      }

      return response;
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
