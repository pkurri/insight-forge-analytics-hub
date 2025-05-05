
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { authService } from '@/api/services/auth/authService';
import Layout from './components/layout/Layout';
import Index from './pages/Index';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import Pipeline from './pages/Pipeline';
import Monitoring from './pages/Monitoring';
import Alerts from './pages/Alerts';
import Logs from './pages/Logs';
import Health from './pages/Health';
import AiChat from './pages/AiChat';
import NotFound from './pages/NotFound';
import Login from './pages/Login';
import { ThemeProvider } from './components/theme/ThemeProvider';
import { Toaster } from '@/components/ui/toaster';
import { AnalyticsFunctions } from './components/analytics/AnalyticsFunctions';
import { conversationAnalyticsService } from "./api/services/analytics/conversationAnalyticsService";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const location = useLocation();
  const isAuthenticated = authService.isAuthenticated();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

function ConversationAnalyticsDashboard() {
  const [stats, setStats] = React.useState({});
  const [feedback, setFeedback] = React.useState({});
  const [volume, setVolume] = React.useState({});
  const [anomalies, setAnomalies] = React.useState([]);
  const [commonFeedback, setCommonFeedback] = React.useState([]);
  const [ratings, setRatings] = React.useState({});
  const [activeUsers, setActiveUsers] = React.useState({});
  const [cohort, setCohort] = React.useState({ cohorts: [], periods: [] });
  const [firstResponseTime, setFirstResponseTime] = React.useState({ avgTime: 0 });
  const [lengthDist, setLengthDist] = React.useState([]);
  const [funnel, setFunnel] = React.useState([]);
  const [userSegmentation, setUserSegmentation] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      conversationAnalyticsService.getMemoryStats(),
      conversationAnalyticsService.getFeedbackSummary(),
      conversationAnalyticsService.getMessageVolumeOverTime('D'),
      conversationAnalyticsService.getAnomalyReport(),
      conversationAnalyticsService.getMostCommonFeedback(5),
      conversationAnalyticsService.getFeedbackRatingsHistogram(),
      conversationAnalyticsService.getActiveUsersOverTime('D'),
      conversationAnalyticsService.getCohortAnalysis(),
      conversationAnalyticsService.getFirstResponseTime(),
      conversationAnalyticsService.getConversationLengthDistribution(),
      conversationAnalyticsService.getFunnelAnalysis(),
      conversationAnalyticsService.getUserSegmentation(),
    ])
      .then(([
        statsRes,
        feedbackRes,
        volumeRes,
        anomaliesRes,
        commonFeedbackRes,
        ratingsRes,
        activeUsersRes,
        cohortRes,
        firstResponseTimeRes,
        lengthDistRes,
        funnelRes,
        userSegmentationRes
      ]) => {
        setStats(statsRes);
        setFeedback(feedbackRes);
        setVolume(volumeRes);
        setAnomalies(anomaliesRes);
        setCommonFeedback(commonFeedbackRes);
        setRatings(ratingsRes);
        setActiveUsers(activeUsersRes);
        setCohort(cohortRes);
        setFirstResponseTime(firstResponseTimeRes);
        setLengthDist(lengthDistRes);
        setFunnel(funnelRes);
        setUserSegmentation(userSegmentationRes);
      })
      .catch((e) => {
        setError("Failed to load analytics data");
        console.error(e);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: 32 }}>
      <AnalyticsFunctions
        stats={stats}
        feedback={feedback}
        volume={volume}
        anomalies={anomalies}
        commonFeedback={commonFeedback}
        ratings={ratings}
        activeUsers={activeUsers}
        cohort={cohort}
        firstResponseTime={firstResponseTime}
        lengthDist={lengthDist}
        funnel={funnel}
        userSegmentation={userSegmentation}
        loading={loading}
        error={error}
      />
    </div>
  );
}

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="dataforge-theme">
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <ConversationAnalyticsDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Layout>
                  <Analytics />
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
                  <Pipeline />
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
