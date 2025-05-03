import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Lightbulb, TrendingUp, TrendingDown, AlertTriangle, Info } from 'lucide-react';

interface Insight {
  id: string;
  title: string;
  description: string;
  type: 'trend' | 'anomaly' | 'correlation' | 'pattern' | 'info';
  severity?: 'low' | 'medium' | 'high';
  timestamp: string;
}

interface InsightsListProps {
  insights: Insight[];
  loading?: boolean;
}

const InsightsList: React.FC<InsightsListProps> = ({ insights, loading = false }) => {
  const getInsightIcon = (type: string, severity?: string) => {
    switch (type) {
      case 'trend':
        return severity === 'high' || severity === 'medium' ? 
          <TrendingUp className="h-5 w-5" /> : 
          <TrendingDown className="h-5 w-5" />;
      case 'anomaly':
        return <AlertTriangle className="h-5 w-5" />;
      case 'correlation':
        return <Lightbulb className="h-5 w-5" />;
      case 'pattern':
        return <TrendingUp className="h-5 w-5" />;
      case 'info':
      default:
        return <Info className="h-5 w-5" />;
    }
  };
  
  const getInsightTypeColor = (type: string) => {
    switch (type) {
      case 'trend':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100';
      case 'anomaly':
        return 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100';
      case 'correlation':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-100';
      case 'pattern':
        return 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100';
      case 'info':
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100';
    }
  };
  
  const getSeverityBadge = (severity?: string) => {
    if (!severity) return null;
    
    switch (severity) {
      case 'high':
        return <Badge variant="destructive">High</Badge>;
      case 'medium':
        return <Badge variant="warning">Medium</Badge>;
      case 'low':
        return <Badge variant="outline">Low</Badge>;
      default:
        return null;
    }
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>AI-Generated Insights</CardTitle>
        <CardDescription>Automatically detected patterns and insights</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex gap-4">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="space-y-2 flex-1">
                  <Skeleton className="h-5 w-full" />
                  <Skeleton className="h-4 w-full" />
                </div>
              </div>
            ))}
          </div>
        ) : insights.length > 0 ? (
          <div className="space-y-6">
            {insights.map((insight) => (
              <div key={insight.id} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`p-2 rounded-full ${getInsightTypeColor(insight.type)}`}>
                      {getInsightIcon(insight.type, insight.severity)}
                    </div>
                    <h3 className="font-medium">{insight.title}</h3>
                  </div>
                  <div className="flex items-center gap-2">
                    {getSeverityBadge(insight.severity)}
                    <span className="text-xs text-muted-foreground">
                      {new Date(insight.timestamp).toLocaleString()}
                    </span>
                  </div>
                </div>
                <p className="pl-10 text-sm text-muted-foreground">{insight.description}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Lightbulb className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No insights available</p>
            <p className="text-xs text-muted-foreground mt-2">Add more data or run analytics to generate insights</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default InsightsList;
