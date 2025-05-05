
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { authService } from '@/api/services/auth/authService';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await authService.login(username, password);
      if (response.success) {
        toast({
          title: "Login successful",
          description: "Welcome to Data Forge Analytics",
        });
        navigate('/dashboard');
      } else {
        throw new Error(response.error || 'Login failed');
      }
    } catch (error) {
      toast({
        title: "Login failed",
        description: error instanceof Error ? error.message : "Invalid credentials",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setIsLoading(true);
    
    try {
      // Use demo credentials
      const response = await authService.login('demo', 'demo123');
      if (response.success) {
        toast({
          title: "Demo login successful",
          description: "Welcome to Data Forge Analytics demo account",
        });
        navigate('/dashboard');
      } else {
        throw new Error(response.error || 'Demo login failed');
      }
    } catch (error) {
      toast({
        title: "Demo login failed",
        description: error instanceof Error ? error.message : "Unable to access demo account",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-r from-blue-600 to-indigo-800">
      <div className="absolute inset-0 bg-black opacity-50" />
      <div className="absolute inset-0 bg-[url('/data-analytics-bg.jpg')] bg-cover bg-center mix-blend-overlay" />
      
      <Card className="w-full max-w-md p-8 space-y-6 relative z-10 bg-white/90 backdrop-blur-sm">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-gray-900">Data Forge Analytics</h1>
          <p className="text-gray-500">Sign in to your account</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="username" className="text-sm font-medium text-gray-700">
              Username
            </label>
            <Input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder="Enter your username"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium text-gray-700">
              Password
            </label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter your password"
            />
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? "Signing in..." : "Sign in"}
          </Button>
        </form>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-white/90 px-2 text-muted-foreground">
              Or continue with
            </span>
          </div>
        </div>

        <Button
          type="button"
          variant="outline"
          className="w-full"
          onClick={handleDemoLogin}
          disabled={isLoading}
        >
          Demo Account Access
        </Button>

        <p className="text-xs text-center text-muted-foreground">
          Demo credentials: username <span className="font-semibold">demo</span> / password <span className="font-semibold">demo123</span>
        </p>
      </Card>
    </div>
  );
};

export default Login;
