
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Outlet } from 'react-router-dom';
import { DatasetProvider } from '@/hooks/useDatasetContext';
import AiChat from '@/pages/AiChat';
import Dashboard from '@/pages/Dashboard';
import Analytics from '@/pages/Analytics';
import Pipeline from '@/pages/Pipeline';
import NotFound from '@/pages/NotFound';
import Monitoring from '@/pages/Monitoring';
import Alerts from '@/pages/Alerts';
import Health from '@/pages/Health';
import Logs from '@/pages/Logs';
import Login from '@/pages/Login';
import Index from '@/pages/Index';
import Layout from '@/components/layout/Layout';
import { ThemeProvider } from '@/components/theme/ThemeProvider';
import { Toaster } from '@/components/ui/toaster';
import './App.css';

function App() {
  return (
    <ThemeProvider defaultTheme="light" storageKey="vite-ui-theme">
      <DatasetProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Layout children={<Outlet />} />}>
              <Route index element={<Index />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="analytics" element={<Analytics />} />
              <Route path="pipeline" element={<Pipeline />} />
              <Route path="ai-chat" element={<AiChat />} />
              <Route path="monitoring" element={<Monitoring />} />
              <Route path="alerts" element={<Alerts />} />
              <Route path="health" element={<Health />} />
              <Route path="logs" element={<Logs />} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
          <Toaster />
        </Router>
      </DatasetProvider>
    </ThemeProvider>
  );
}

export default App;
