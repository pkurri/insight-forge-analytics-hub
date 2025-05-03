import React from "react";
import { FunnelChart, Funnel, Tooltip, LabelList, ResponsiveContainer } from "recharts";

export interface FunnelStage {
  name: string;
  value: number;
}

interface FunnelAnalysisProps {
  stages: FunnelStage[];
}

export default function FunnelAnalysis({ stages }: FunnelAnalysisProps) {
  return (
    <div className="card" style={{ width: 340, height: 320, marginBottom: 24 }}>
      <h3>Funnel Analysis</h3>
      <ResponsiveContainer width="100%" height="80%">
        <FunnelChart width={320} height={240}>
          <Tooltip />
          <Funnel
            dataKey="value"
            data={stages}
            isAnimationActive={false}
          >
            <LabelList dataKey="name" position="right" fill="#374151" />
          </Funnel>
        </FunnelChart>
      </ResponsiveContainer>
    </div>
  );
}
