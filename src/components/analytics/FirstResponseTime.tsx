import React from "react";

interface FirstResponseTimeProps {
  avgTime: number; // in seconds
  medianTime?: number;
}

export default function FirstResponseTime({ avgTime, medianTime }: FirstResponseTimeProps) {
  return (
    <div className="card" style={{ width: 340, marginBottom: 24 }}>
      <h3>Time to First Response</h3>
      <div style={{ fontSize: 24, fontWeight: 600, color: '#10b981' }}>{Math.round(avgTime)}s</div>
      {medianTime !== undefined && (
        <div style={{ fontSize: 14, color: '#6b7280' }}>Median: {Math.round(medianTime)}s</div>
      )}
    </div>
  );
}
