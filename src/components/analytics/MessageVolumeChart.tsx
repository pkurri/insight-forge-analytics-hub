import React from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

export default function MessageVolumeChart({ volume }) {
  if (!volume) return null;
  const data = Object.entries(volume).map(([date, count]) => ({ date, count }));
  return (
    <div style={{ width: 600, height: 300, marginBottom: 24 }}>
      <h3>Message Volume Over Time</h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey="date" tick={{ fontSize: 12 }} angle={-30} textAnchor="end" height={60} interval={0} />
          <YAxis />
          <Tooltip />
          <CartesianGrid stroke="#eee" />
          <Line type="monotone" dataKey="count" stroke="#8884d8" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
