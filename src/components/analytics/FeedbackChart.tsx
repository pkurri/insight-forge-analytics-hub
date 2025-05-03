import React from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

export default function FeedbackChart({ feedback }) {
  if (!feedback || !feedback.category_counts) return null;
  const data = Object.entries(feedback.category_counts).map(([name, value]) => ({ name, value }));
  const COLORS = ["#0088FE", "#FF8042", "#00C49F", "#FFBB28", "#d7263d", "#a2d5c6"];
  return (
    <div style={{ width: 350, height: 250, marginBottom: 24 }}>
      <h3>Feedback Categories</h3>
      <ResponsiveContainer>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" outerRadius={80} fill="#8884d8">
            {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
