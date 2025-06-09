
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { authService } from '@/api/services/auth/authService';
import Layout from './components/layout/Layout';
import Index from './pages/Index';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import Pipeline from './pages/Pipeline';
import PipelineTest from './pages/PipelineTest';
import Monitoring from './pages/Monitoring';
import Alerts from './pages/Alerts';
import Logs from './pages/Logs';
import Health from './pages/Health';
import AiChat from './pages/AiChat';
import NotFound from './pages/NotFound';
import Login from './pages/Login';
import { ThemeProvider } from './components/theme/ThemeProvider';
import { Toaster } from '@/components/ui/toaster';
import { PipelineProvider } from '@/contexts/PipelineContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const location = useLocation();
  // Use a React state to track authentication status
  const [isAuthenticated] = React.useState(authService.isAuthenticated());

  if (!isAuthenticated) {
    // Use replace prop to prevent adding to history stack
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="dataforge-theme">
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout>
                  <Index />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <ProtectedRoute>
                <Layout>
                  <Analytics />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/pipeline"
            element={
              <ProtectedRoute>
                <Layout>
                  <PipelineProvider>
                    <Pipeline />
                  </PipelineProvider>
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/pipeline-test"
            element={
              <ProtectedRoute>
                <Layout>
                  <PipelineProvider>
                    <PipelineTest />
                  </PipelineProvider>
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/monitoring"
            element={
              <ProtectedRoute>
                <Layout>
                  <Monitoring />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/alerts"
            element={
              <ProtectedRoute>
                <Layout>
                  <Alerts />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/logs"
            element={
              <ProtectedRoute>
                <Layout>
                  <Logs />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/health"
            element={
              <ProtectedRoute>
                <Layout>
                  <Health />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/ai-chat"
            element={
              <ProtectedRoute>
                <Layout>
                  <AiChat />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
        <Toaster />
      </Router>
    </ThemeProvider>
  );
}

export default App;
