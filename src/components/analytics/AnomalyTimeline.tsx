import React from "react";

export default function AnomalyTimeline({ anomalies }) {
  if (!anomalies || anomalies.length === 0)
    return <div>No anomalies detected.</div>;
  return (
    <div style={{ marginBottom: 24 }}>
      <h3>Anomaly Events</h3>
      <ul style={{ maxHeight: 180, overflowY: "auto", paddingLeft: 16 }}>
        {anomalies.map((a, i) => (
          <li key={i} style={{ marginBottom: 6 }}>
            <b>{a.timestamp}:</b> {a.reason} (dataset: {a.dataset_id})
          </li>
        ))}
      </ul>
    </div>
  );
}
