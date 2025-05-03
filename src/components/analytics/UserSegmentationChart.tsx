import React from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

export interface UserSegment {
  segment: string;
  count: number;
}

interface UserSegmentationChartProps {
  data: UserSegment[];
  title?: string;
}

const COLORS = ["#6366f1", "#10b981", "#f59e42", "#ef4444", "#a21caf", "#0ea5e9", "#fbbf24", "#6d28d9", "#64748b"];

export default function UserSegmentationChart({ data, title = "User Segmentation" }: UserSegmentationChartProps) {
  return (
    <div className="card" style={{ width: 340, height: 320, marginBottom: 24 }}>
      <h3>{title}</h3>
      <ResponsiveContainer width="100%" height="80%">
        <PieChart>
          <Pie data={data} dataKey="count" nameKey="segment" cx="50%" cy="50%" outerRadius={80} label>
            {data.map((entry, idx) => (
              <Cell key={`cell-${idx}`} fill={COLORS[idx % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
