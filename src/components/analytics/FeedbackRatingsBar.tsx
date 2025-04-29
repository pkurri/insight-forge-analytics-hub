import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

interface FeedbackRatingsBarProps {
  ratings: { [rating: string]: number };
}

export default function FeedbackRatingsBar({ ratings }: FeedbackRatingsBarProps) {
  if (!ratings) return null;
  const data = Object.entries(ratings).map(([rating, count]) => ({ rating, count }));
  return (
    <div className="card" style={{ width: 400, height: 240, marginBottom: 24 }}>
      <h3>Feedback Ratings Distribution</h3>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <XAxis dataKey="rating" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <CartesianGrid stroke="#eee" />
          <Bar dataKey="count" fill="#6366f1" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
