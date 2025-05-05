
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowDown, ArrowUp } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

export interface MetricCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  change?: number;
  loading?: boolean;
  trend?: 'up' | 'down' | 'none';
  trendText?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  icon, 
  change, 
  loading = false,
  trend,
  trendText
}) => {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-24" />
        ) : (
          <div className="text-2xl font-bold">{value}</div>
        )}
        
        {change !== undefined && !loading && (
          <div className="flex items-center pt-1">
            {trend === 'up' || (change > 0 && !trend) ? (
              <ArrowUp className="h-4 w-4 text-green-500 mr-1" />
            ) : trend === 'down' || (change < 0 && !trend) ? (
              <ArrowDown className="h-4 w-4 text-red-500 mr-1" />
            ) : null}
            
            <p className={`text-xs ${
              trend === 'up' || (change > 0 && !trend) 
                ? 'text-green-500' 
                : trend === 'down' || (change < 0 && !trend) 
                  ? 'text-red-500' 
                  : 'text-gray-500'
            }`}>
              {Math.abs(change || 0)}% {trendText || 'from previous period'}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default MetricCard;
