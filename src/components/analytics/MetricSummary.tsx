import React from 'react';
import { Card } from '@/components/ui/card';
import { ArrowUpRight, ArrowDownRight, ArrowRight } from 'lucide-react';

interface MetricSummaryProps {
  metrics: Record<string, unknown>;
  loading?: boolean;
}

const MetricSummary: React.FC<MetricSummaryProps> = ({ metrics, loading = false }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="p-4">
            <div className="h-4 w-1/3 bg-muted rounded animate-pulse mb-2" />
            <div className="h-8 w-1/2 bg-muted rounded animate-pulse mb-2" />
            <div className="h-4 w-2/3 bg-muted rounded animate-pulse" />
          </Card>
        ))}
      </div>
    );
  }

  // Extract key metrics or use defaults
  const keyMetrics = [
    {
      name: 'Accuracy',
      value: typeof metrics.accuracy === 'number' ? metrics.accuracy : 0,
      change: typeof metrics.accuracyChange === 'number' ? metrics.accuracyChange : 0,
      unit: '%',
      description: 'Model prediction accuracy'
    },
    {
      name: 'Processing Time',
      value: typeof metrics.processingTime === 'number' ? metrics.processingTime : 0,
      change: typeof metrics.processingTimeChange === 'number' ? metrics.processingTimeChange : 0,
      unit: 'ms',
      description: 'Average processing time'
    },
    {
      name: 'Data Quality',
      value: typeof metrics.dataQuality === 'number' ? metrics.dataQuality : 0,
      change: typeof metrics.dataQualityChange === 'number' ? metrics.dataQualityChange : 0,
      unit: '%',
      description: 'Overall data quality score'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {keyMetrics.map((metric) => (
        <Card key={metric.name} className="p-4">
          <div className="flex flex-col">
            <div className="text-sm text-muted-foreground">{metric.name}</div>
            <div className="text-2xl font-bold mt-1">
              {metric.value}
              {metric.unit}
            </div>
            <div className="flex items-center mt-1">
              {metric.change > 0 ? (
                <div className="flex items-center text-green-500 text-sm">
                  <ArrowUpRight className="h-3 w-3 mr-1" />
                  <span>+{metric.change}{metric.unit}</span>
                </div>
              ) : metric.change < 0 ? (
                <div className="flex items-center text-red-500 text-sm">
                  <ArrowDownRight className="h-3 w-3 mr-1" />
                  <span>{metric.change}{metric.unit}</span>
                </div>
              ) : (
                <div className="flex items-center text-muted-foreground text-sm">
                  <ArrowRight className="h-3 w-3 mr-1" />
                  <span>No change</span>
                </div>
              )}
              <span className="text-xs text-muted-foreground ml-2">vs last period</span>
            </div>
            <div className="text-xs text-muted-foreground mt-2">{metric.description}</div>
          </div>
        </Card>
      ))}
    </div>
  );
};

export default MetricSummary;
