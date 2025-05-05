
import React from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Info, AlertCircle, TrendingUp } from 'lucide-react';

interface Insight {
  id: string;
  title: string;
  description: string;
  type: 'info' | 'anomaly' | 'trend';
  importance: 'low' | 'medium' | 'high';
}

interface InsightsListProps {
  insights: Insight[];
  loading?: boolean;
  className?: string;
}

// Map insight types to icons
const getInsightIcon = (type: Insight['type']) => {
  switch (type) {
    case 'anomaly':
      return <AlertCircle className="h-4 w-4" />;
    case 'trend':
      return <TrendingUp className="h-4 w-4" />;
    case 'info':
    default:
      return <Info className="h-4 w-4" />;
  }
};

// Map insight importance to alert variants
const getAlertVariant = (type: Insight['type'], importance: Insight['importance']) => {
  if (type === 'anomaly' && importance === 'high') {
    return 'destructive';
  }
  if (type === 'trend') {
    return 'default';
  }
  return 'default';
};

const InsightsList: React.FC<InsightsListProps> = ({ 
  insights,
  loading = false,
  className = ''
}) => {
  if (loading) {
    return <p className={`text-sm text-muted-foreground ${className}`}>Loading insights...</p>;
  }

  if (!insights || insights.length === 0) {
    return <p className={`text-sm text-muted-foreground ${className}`}>No insights available.</p>;
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {insights.map((insight) => (
        <Alert 
          key={insight.id} 
          variant={getAlertVariant(insight.type, insight.importance)}
        >
          {getInsightIcon(insight.type)}
          <AlertTitle>{insight.title}</AlertTitle>
          <AlertDescription>{insight.description}</AlertDescription>
        </Alert>
      ))}
    </div>
  );
};

export default InsightsList;
