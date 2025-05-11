// Define API response interface locally
interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  status?: number;
}

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

  // Local implementation of callApi function
  private async callApi<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
    const url = `${baseUrl}${endpoint}`;
    
    const token = this.getToken();
    const headers = new Headers(options.headers);
    
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    
    // Handle body properly for TypeScript
    const requestOptions = { ...options };
    
    if (requestOptions.body && typeof requestOptions.body === 'object' && !(requestOptions.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
      requestOptions.body = JSON.stringify(requestOptions.body);
    }
    
    // Use our modified options with headers
    const fetchOptions = {
      ...requestOptions,
      headers
    };
    
    try {
      const response = await fetch(url, fetchOptions);
      
      const data = await response.json();
      return {
        success: response.ok,
        data: response.ok ? data : undefined,
        error: !response.ok ? data.error || 'An error occurred' : undefined,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'API request failed',
        status: 500
      };
    }
  }

  async login(username: string, password: string): Promise<AuthResponse> {
    try {
      const response = await this.callApi<AuthResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
        headers: {
          'Content-Type': 'application/json'
        }
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
