import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export interface ConversationLengthBin {
  bin: string; // e.g. "1-5", "6-10", etc.
  count: number;
}

interface ConversationLengthChartProps {
  data: ConversationLengthBin[];
}

export default function ConversationLengthChart({ data }: ConversationLengthChartProps) {
  return (
    <div className="card" style={{ width: 340, height: 320, marginBottom: 24 }}>
      <h3>Conversation Length Distribution</h3>
      <ResponsiveContainer width="100%" height="80%">
        <BarChart data={data}>
          <XAxis dataKey="bin" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <CartesianGrid stroke="#eee" />
          <Bar dataKey="count" fill="#6366f1" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
