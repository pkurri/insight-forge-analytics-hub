
import React from 'react';
import { cn } from '@/utils/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, AlertCircle, XCircle } from 'lucide-react';

type Status = 'operational' | 'warning' | 'error';

interface StatusCardProps {
  title: string;
  description: string;
  status: Status;
  lastUpdated?: string;
}

const StatusCard: React.FC<StatusCardProps> = ({
  title,
  description,
  status,
  lastUpdated,
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'operational':
        return <CheckCircle className="h-5 w-5 text-success" />;
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-warning" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-error" />;
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'operational':
        return 'bg-green-50 border-green-200';
      case 'warning':
        return 'bg-amber-50 border-amber-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      default:
        return '';
    }
  };

  return (
    <Card className={cn("border shadow-sm", getStatusColor())}>
      <CardHeader className="pb-2">
        <div className="flex justify-between">
          <CardTitle className="text-lg">{title}</CardTitle>
          {getStatusIcon()}
        </div>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {lastUpdated && (
          <p className="text-xs text-gray-500">Last updated: {lastUpdated}</p>
        )}
      </CardContent>
    </Card>
  );
};

export default StatusCard;
