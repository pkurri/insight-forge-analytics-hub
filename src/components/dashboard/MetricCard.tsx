
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
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon, change, loading = false }) => {
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
            {change > 0 ? (
              <ArrowUp className="h-4 w-4 text-green-500 mr-1" />
            ) : change < 0 ? (
              <ArrowDown className="h-4 w-4 text-red-500 mr-1" />
            ) : null}
            
            <p className={`text-xs ${change > 0 ? 'text-green-500' : change < 0 ? 'text-red-500' : 'text-gray-500'}`}>
              {Math.abs(change)}% from previous period
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default MetricCard;
