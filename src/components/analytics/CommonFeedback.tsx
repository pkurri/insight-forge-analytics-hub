
import React from "react";

interface CommonFeedbackProps {
  feedbacks: string[];
}

export default function CommonFeedback({ feedbacks }: CommonFeedbackProps) {
  // Ensure feedbacks is an array before mapping
  const feedbackArray = Array.isArray(feedbacks) ? feedbacks : [];
  
  if (feedbackArray.length === 0) {
    return <div className="text-muted-foreground">No common feedback yet.</div>;
  }
  
  return (
    <div className="card space-y-2">
      <h3 className="text-lg font-medium">Most Common Feedback</h3>
      <div className="flex flex-wrap gap-2">
        {feedbackArray.map((feedback, index) => (
          <span 
            key={index} 
            className="bg-indigo-100 text-indigo-800 rounded-xl px-3 py-1 text-sm"
          >
            {feedback}
          </span>
        ))}
      </div>
    </div>
  );
}
