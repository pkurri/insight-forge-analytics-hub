import React, { useEffect, useState } from "react";
import axios from "axios";
import StatsCards from "./components/StatsCards";
import FeedbackChart from "./components/FeedbackChart";
import MessageVolumeChart from "./components/MessageVolumeChart";
import AnomalyTimeline from "./components/AnomalyTimeline";

const API_BASE = "http://localhost:8000/conversation-analytics";

function App() {
  const [stats, setStats] = useState({});
  const [feedback, setFeedback] = useState({});
  const [volume, setVolume] = useState({});
  const [anomalies, setAnomalies] = useState([]);

  useEffect(() => {
    axios.get(`${API_BASE}/memory-stats`).then(r => setStats(r.data));
    axios.get(`${API_BASE}/feedback-summary`).then(r => setFeedback(r.data));
    axios.get(`${API_BASE}/message-volume-over-time?freq=D`).then(r => setVolume(r.data));
    axios.get(`${API_BASE}/anomaly-report`).then(r => setAnomalies(r.data));
  }, []);

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: 32 }}>
      <h1 style={{ marginBottom: 32 }}>Conversation Analytics Dashboard</h1>
      <StatsCards stats={stats} />
      <FeedbackChart feedback={feedback} />
      <MessageVolumeChart volume={volume} />
      <AnomalyTimeline anomalies={anomalies} />
    </div>
  );
}

export default App;
