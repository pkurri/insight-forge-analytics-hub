
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowUpIcon, ArrowDownIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  change?: number;
  trend?: 'up' | 'down' | 'neutral';
  trendText?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  icon,
  change,
  trend,
  trendText,
}) => {
  const renderTrend = () => {
    if (!trend || trend === 'neutral') return null;
    
    const isPositive = trend === 'up';
    const trendClass = isPositive ? 'text-success' : 'text-error';
    const TrendIcon = isPositive ? ArrowUpIcon : ArrowDownIcon;
    
    return (
      <div className={cn("flex items-center text-sm font-medium", trendClass)}>
        <TrendIcon className="h-4 w-4 mr-1" />
        <span>{change}%</span>
        {trendText && <span className="ml-1 text-gray-500">{trendText}</span>}
      </div>
    );
  };

  return (
    <Card className="shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="h-8 w-8 rounded-md bg-primary/10 p-1.5 text-primary">
          {icon}
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {renderTrend()}
      </CardContent>
    </Card>
  );
};

export default MetricCard;
