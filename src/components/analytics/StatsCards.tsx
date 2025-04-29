import React from "react";
export default function StatsCards({ stats }) {
  if (!stats) return null;
  return (
    <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
      <div className="stat-card">Conversations: {stats.conversations}</div>
      <div className="stat-card">Messages: {stats.messages}</div>
      <div className="stat-card">Evaluations: {stats.evaluations}</div>
      <div className="stat-card">Users: {stats.users}</div>
      <div className="stat-card">Anomalies: {stats.anomalies}</div>
    </div>
  );
}
