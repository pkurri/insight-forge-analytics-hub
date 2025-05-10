import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { RefreshCw } from 'lucide-react';
import AnalyticsChart from './AnalyticsChart';
import InsightsList from './InsightsList';
import TrendIndicator from './TrendIndicator';
import MetricSummary from './MetricSummary';
import { api } from '@/api/api';
import { useToast } from '@/hooks/use-toast';

// Not directly used in this file but defines the structure for insights data
// that comes from the API and is passed to InsightsList component
// Commenting out to fix lint warning - this is used by the InsightsList component
/* 
interface Insight {
  id: string;
  title: string;
  description: string;
  impact: number;
  category: string;
  timestamp: string;
}
*/

interface AnalyticsDashboardProps {
  datasetId?: string;
  className?: string;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ datasetId, className }) => {
  const [loading, setLoading] = useState<boolean>(false);
  // Initialize with empty record that satisfies TypeScript requirements
  const [analyticsData, setAnalyticsData] = useState<Record<string, unknown>>({} as Record<string, unknown>);
  // Code quality state - commented out until implemented
  // const [codeQuality, setCodeQuality] = useState<Record<string, unknown> | null>(null);
  const [activeTab, setActiveTab] = useState<string>('overview');
  const { toast } = useToast();

  const loadAnalyticsData = useCallback(async () => {
    setLoading(true);
    try {
      const response = datasetId
        ? await api.getDatasetAnalytics(datasetId)
        : await api.getGlobalAnalytics();

      if (response.success && response.data) {
        // Type assertion to ensure TypeScript knows this is a valid Record<string, unknown>
        setAnalyticsData(response.data as Record<string, unknown>);
      } else {
        toast({
          title: 'Error',
          description: response.error || 'Failed to load analytics data',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Error loading analytics data:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to connect to analytics service',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  }, [datasetId, toast]);

  useEffect(() => {
    loadAnalyticsData();

    // Refresh analytics every 5 minutes
    const interval = setInterval(loadAnalyticsData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadAnalyticsData]);

  const handleRefresh = async () => {
    loadAnalyticsData();
  };

  return (
    <div className={`p-4 space-y-6 ${className}`}>
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Analytics {datasetId ? `for ${analyticsData?.datasetName || 'Dataset'}` : 'Overview'}</h1>
        <div className="flex items-center gap-2">
          {/* Code quality suggestions button - commented out until implemented
            <Button variant="outline" size="sm" onClick={() => api.showComponentSuggestions('AnalyticsDashboard')}>
              View Suggestions
            </Button>
          */}
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={loading}>
            {loading ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
            Refresh
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview" value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid grid-cols-4 mb-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="timeseries">Time Series</TabsTrigger>
          <TabsTrigger value="quality">Data Quality</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <MetricSummary metrics={analyticsData.metrics || {}} loading={loading} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Distribution Overview</CardTitle>
              </CardHeader>
              <CardContent className="h-[300px]">
                {loading ? (
                  <div className="flex justify-center items-center h-full">
                    <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : analyticsData.distributions ? (
                  <AnalyticsChart className="h-full w-full text-muted-foreground" />
                ) : (
                  <div className="flex flex-col items-center justify-center h-full">
                    <div className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">No distribution data available</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Trend Analysis</CardTitle>
              </CardHeader>
              <CardContent className="h-[300px]">
                {loading ? (
                  <div className="flex justify-center items-center h-full">
                    <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : analyticsData.trends ? (
                  <TrendIndicator className="h-full w-full text-muted-foreground" />
                ) : (
                  <div className="flex flex-col items-center justify-center h-full">
                    <div className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">No trend data available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Not currently implemented - will be added in future updates */}
        <TabsContent value="timeseries" className="space-y-4">
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <p className="text-muted-foreground">Time series analysis will be available in a future update</p>
          </div>
        </TabsContent>

        {/* Not currently implemented - will be added in future updates */}
        <TabsContent value="quality" className="space-y-4">
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <p className="text-muted-foreground">Data quality reports will be available in a future update</p>
          </div>
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          <InsightsList insights={Array.isArray(analyticsData.insights) ? analyticsData.insights : []} loading={loading} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AnalyticsDashboard;
