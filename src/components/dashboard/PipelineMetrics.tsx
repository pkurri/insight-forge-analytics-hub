import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface PipelineMetric {
  name: string;
  value: number;
  status?: 'success' | 'error' | 'warning' | 'info';
  [key: string]: string | number | undefined;
}

interface PipelineMetricsProps {
  data: PipelineMetric[];
  title?: string;
  description?: string;
  loading?: boolean;
}

const PipelineMetrics: React.FC<PipelineMetricsProps> = ({
  data,
  title = "Pipeline Metrics",
  description = "Performance metrics by pipeline stage",
  loading = false
}) => {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent className="h-80">
          <div className="flex items-center justify-center h-full">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        </CardContent>
      </Card>
    );
  }

  // Custom colors based on status
  const getBarFill = (entry: PipelineMetric) => {
    switch (entry.status) {
      case 'success':
        return 'var(--success)';
      case 'error':
        return 'var(--destructive)';
      case 'warning':
        return 'var(--warning)';
      default:
        return 'var(--primary)';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </CardHeader>
      <CardContent className="h-80">
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar 
                dataKey="value" 
                fill="var(--primary)" 
                radius={[4, 4, 0, 0]}
                // Custom fill based on status
                fill={(entry) => getBarFill(entry as PipelineMetric)}
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex flex-col items-center justify-center h-full">
            <p className="text-muted-foreground">No pipeline metrics available</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default PipelineMetrics;
