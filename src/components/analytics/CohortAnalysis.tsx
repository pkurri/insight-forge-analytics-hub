import React from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export interface CohortDataPoint {
  cohort: string;
  retention: number[]; // Retention percent for each time period (e.g., day/week)
}

interface CohortAnalysisProps {
  cohortData: CohortDataPoint[];
  periods: string[];
}

export default function CohortAnalysis({ cohortData, periods }: CohortAnalysisProps) {
  // Transform cohortData into chart-friendly format
  const chartData = periods.map((period, i) => {
    const row: any = { period };
    cohortData.forEach(cohort => {
      row[cohort.cohort] = cohort.retention[i] ?? 0;
    });
    return row;
  });
  return (
    <div className="card" style={{ width: 700, height: 320, marginBottom: 24 }}>
      <h3>Cohort Retention Analysis</h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <XAxis dataKey="period" />
          <YAxis domain={[0, 100]} tickFormatter={v => `${v}%`} />
          <Tooltip />
          <CartesianGrid stroke="#eee" />
          {cohortData.map((cohort, idx) => (
            <Line
              key={cohort.cohort}
              type="monotone"
              dataKey={cohort.cohort}
              stroke={`hsl(${(idx * 55) % 360},70%,50%)`}
              strokeWidth={2}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
