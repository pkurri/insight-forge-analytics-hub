import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { BarChart, LineChart, PieChart } from '@/components/ui/charts';

interface DashboardChartProps {
  title: string;
  description: string;
  data: any[];
  type: 'bar' | 'line' | 'pie';
  loading?: boolean;
}

const DashboardChart: React.FC<DashboardChartProps> = ({
  title,
  description,
  data,
  type,
  loading = false
}) => {
  const renderChart = () => {
    if (loading) {
      return <Skeleton className="h-[250px] w-full" />;
    }
    
    switch (type) {
      case 'bar':
        return <BarChart data={data} />;  
      case 'line':
        return <LineChart data={data} />;  
      case 'pie':
        return <PieChart data={data} />;  
      default:
        return null;
    }
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {renderChart()}
      </CardContent>
    </Card>
  );
};

export default DashboardChart;
