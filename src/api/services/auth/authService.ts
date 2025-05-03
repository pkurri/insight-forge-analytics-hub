import { callApi } from '@/api/api';

interface AuthResponse {
  success: boolean;
  data?: {
    token: string;
    user: {
      id: string;
      username: string;
      role: string;
    };
  };
  error?: string;
}

class AuthService {
  private tokenKey = 'auth_token';
  private userKey = 'user_data';

  async login(username: string, password: string): Promise<AuthResponse> {
    try {
      const response = await callApi<AuthResponse>('/auth/login', {
        method: 'POST',
        body: { username, password },
      });

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

  getUser(): { id: string; username: string; role: string } | null {
    const userData = localStorage.getItem(this.userKey);
    return userData ? JSON.parse(userData) : null;
  }
}

export const authService = new AuthService();
