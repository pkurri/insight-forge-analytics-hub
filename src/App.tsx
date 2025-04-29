
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
import StatsCards from "./components/analytics/StatsCards";
import FeedbackChart from "./components/analytics/FeedbackChart";
import MessageVolumeChart from "./components/analytics/MessageVolumeChart";
import AnomalyTimeline from "./components/analytics/AnomalyTimeline";
import CommonFeedback from "./components/analytics/CommonFeedback";
import FeedbackRatingsBar from "./components/analytics/FeedbackRatingsBar";
import ActiveUsersChart from "./components/analytics/ActiveUsersChart";
import DashboardGrid from "./components/analytics/DashboardGrid";
import CohortAnalysis from "./components/analytics/CohortAnalysis";
import FirstResponseTime from "./components/analytics/FirstResponseTime";
import ConversationLengthChart from "./components/analytics/ConversationLengthChart";
import FunnelAnalysis from "./components/analytics/FunnelAnalysis";
import UserSegmentationChart from "./components/analytics/UserSegmentationChart";
import ExportMenu from "./components/analytics/ExportMenu";
import PrintMenu from "./components/analytics/PrintMenu";
import PdfExportMenu from "./components/analytics/PdfExportMenu";

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


import { conversationAnalyticsService, Stats, Feedback, Volume, Anomaly } from "./api/services/analytics/conversationAnalyticsService";

function ConversationAnalyticsDashboard() {
  const [stats, setStats] = React.useState<Stats>({});
  const [feedback, setFeedback] = React.useState<Feedback>({});
  const [volume, setVolume] = React.useState<Volume>({});
  const [anomalies, setAnomalies] = React.useState<Anomaly[]>([]);
  const [commonFeedback, setCommonFeedback] = React.useState<string[]>([]);
  const [ratings, setRatings] = React.useState<Record<string, number>>({});
  const [activeUsers, setActiveUsers] = React.useState<Record<string, number>>({});
  const [cohort, setCohort] = React.useState<{ cohorts: any[]; periods: string[] }>({ cohorts: [], periods: [] });
  const [firstResponseTime, setFirstResponseTime] = React.useState<{ avgTime: number; medianTime?: number }>({ avgTime: 0 });
  const [lengthDist, setLengthDist] = React.useState<any[]>([]);
  const [funnel, setFunnel] = React.useState<any[]>([]);
  const [userSegmentation, setUserSegmentation] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

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

  // Prepare data for CSV export
  const volumeCsv = Object.entries(volume).map(([date, count]) => ({ date, count }));
  const activeUsersCsv = Object.entries(activeUsers).map(([date, count]) => ({ date, count }));
  const ratingsCsv = Object.entries(ratings).map(([rating, count]) => ({ rating, count }));

  if (loading) return <div>Loading analytics...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: 32 }}>
      <h1 style={{ marginBottom: 32 }}>Conversation Analytics Dashboard</h1>
      <PdfExportMenu />
      <PrintMenu />
      <ExportMenu csvData={volumeCsv} fileName="message_volume" />
      <ExportMenu csvData={activeUsersCsv} fileName="active_users" />
      <ExportMenu csvData={ratingsCsv} fileName="feedback_ratings" />
      <DashboardGrid>
        <StatsCards stats={stats} />
        <FeedbackChart feedback={feedback} />
        <FeedbackRatingsBar ratings={ratings} />
        <CommonFeedback feedbacks={commonFeedback} />
        <MessageVolumeChart volume={volume} />
        <ActiveUsersChart activeUsers={activeUsers} />
        <CohortAnalysis cohortData={cohort.cohorts} periods={cohort.periods} />
        <FirstResponseTime avgTime={firstResponseTime.avgTime} medianTime={firstResponseTime.medianTime} />
        <ConversationLengthChart data={lengthDist} />
        <UserSegmentationChart data={userSegmentation} />
        <FunnelAnalysis stages={funnel} />
        <AnomalyTimeline anomalies={anomalies} />
      </DashboardGrid>
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
