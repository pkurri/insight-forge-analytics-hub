import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { BarChart2, TrendingUp, EyeOff, AlertTriangle } from 'lucide-react';

interface MetricsOverviewProps {
  metrics: {
    totalRows?: number;
    totalColumns?: number;
    missingValuesPercentage?: number;
    outlierPercentage?: number;
    [key: string]: any;
  };
  loading?: boolean;
}

const MetricsOverview: React.FC<MetricsOverviewProps> = ({ metrics, loading = false }) => {
  const metricsData = [
    {
      title: 'Total Records',
      value: metrics.totalRows || 0,
      icon: <BarChart2 className="h-5 w-5" />,
      description: 'Total number of data records'
    },
    {
      title: 'Dimensions',
      value: metrics.totalColumns || 0,
      icon: <TrendingUp className="h-5 w-5" />,
      description: 'Number of data columns/features'
    },
    {
      title: 'Missing Values',
      value: metrics.missingValuesPercentage || 0,
      suffix: '%',
      icon: <EyeOff className="h-5 w-5" />,
      description: 'Percentage of missing data'
    },
    {
      title: 'Outliers',
      value: metrics.outlierPercentage || 0,
      suffix: '%',
      icon: <AlertTriangle className="h-5 w-5" />,
      description: 'Percentage of outlier data points'
    }
  ];
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metricsData.map((metric, index) => (
        <Card key={index}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between space-x-4">
              <div className="flex-1 space-y-1">
                <p className="text-sm font-medium text-muted-foreground">{metric.title}</p>
                {loading ? (
                  <Skeleton className="h-9 w-24" />
                ) : (
                  <div className="flex items-center">
                    <h3 className="text-2xl font-bold tracking-tight">
                      {typeof metric.value === 'number' 
                        ? metric.value.toLocaleString()
                        : metric.value}
                      {metric.suffix}
                    </h3>
                  </div>
                )}
                <p className="text-xs text-muted-foreground">{metric.description}</p>
              </div>
              <div className="p-2 bg-muted rounded-full">
                {metric.icon}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default MetricsOverview;
