import React from "react";

interface CommonFeedbackProps {
  feedbacks: string[];
}

export default function CommonFeedback({ feedbacks }: CommonFeedbackProps) {
  if (!feedbacks || feedbacks.length === 0) return <div>No common feedback yet.</div>;
  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <h3>Most Common Feedback</h3>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {feedbacks.map((f, i) => (
          <span key={i} style={{ background: "#e0e7ff", borderRadius: 12, padding: "4px 12px", fontSize: 14 }}>{f}</span>
        ))}
      </div>
    </div>
  );
}
