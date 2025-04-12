
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
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
import { ThemeProvider } from './components/theme/ThemeProvider';
import { Toaster } from '@/components/ui/toaster';

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="dataforge-theme">
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/pipeline" element={<Pipeline />} />
            <Route path="/monitoring" element={<Monitoring />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/health" element={<Health />} />
            <Route path="/ai-chat" element={<AiChat />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Layout>
        <Toaster />
      </Router>
    </ThemeProvider>
  );
}

export default App;
