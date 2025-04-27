import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { RefreshCw, FileSpreadsheet, BarChart2, LineChart } from 'lucide-react';
import MetricsOverview from './MetricsOverview';
import InsightsList from './InsightsList';
import DataQualityReport from './DataQualityReport';
import TimeSeriesAnalysis from './TimeSeriesAnalysis';
import { api } from '@/api/api';

interface AnalyticsDashboardProps {
  datasetId?: string;
  className?: string;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ datasetId, className }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [analyticsData, setAnalyticsData] = useState<any>({});
  const [codeQuality, setCodeQuality] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<string>('overview');
  
  useEffect(() => {
    loadAnalyticsData();
    
    // Check component code quality using OpenEvals
    const checkComponentQuality = async () => {
      try {
        const result = await api.evaluateRuntimeComponent('AnalyticsDashboard');
        if (result.success) {
          setCodeQuality(result.data);
          
          // If quality is below threshold, show suggestions for improvement
          if (result.data.score < 80) {
            console.log('Component quality below threshold:', result.data.suggestions);
          }
        }
      } catch (error) {
        console.error('Error evaluating component quality:', error);
      }
    };
    
    checkComponentQuality();
  }, [datasetId]);
  
  const loadAnalyticsData = async () => {
    setLoading(true);
    try {
      const response = datasetId 
        ? await api.getDatasetAnalytics(datasetId)
        : await api.getGlobalAnalytics();
        
      if (response.success) {
        setAnalyticsData(response.data);
      }
    } catch (error) {
      console.error('Error loading analytics data:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleRefresh = () => {
    loadAnalyticsData();
  };
  
  return (
    <div className={`p-4 space-y-6 ${className}`}>
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Analytics {datasetId ? `for ${analyticsData?.datasetName || 'Dataset'}` : 'Overview'}</h1>
        <div className="flex items-center gap-2">
          {codeQuality && codeQuality.score < 80 && (
            <Button variant="outline" size="sm" onClick={() => api.showComponentSuggestions('AnalyticsDashboard')}>
              View Suggestions
            </Button>
          )}
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
          <MetricsOverview metrics={analyticsData.metrics || {}} loading={loading} />
          
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
                  <BarChart2 className="h-full w-full text-muted-foreground" />
                ) : (
                  <div className="flex flex-col items-center justify-center h-full">
                    <FileSpreadsheet className="h-12 w-12 text-muted-foreground mb-4" />
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
                  <LineChart className="h-full w-full text-muted-foreground" />
                ) : (
                  <div className="flex flex-col items-center justify-center h-full">
                    <FileSpreadsheet className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">No trend data available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="timeseries" className="space-y-4">
          <TimeSeriesAnalysis 
            timeSeriesData={analyticsData.timeSeries || []} 
            loading={loading} 
          />
        </TabsContent>
        
        <TabsContent value="quality" className="space-y-4">
          <DataQualityReport 
            qualityData={analyticsData.qualityReport || {}} 
            loading={loading} 
          />
        </TabsContent>
        
        <TabsContent value="insights" className="space-y-4">
          <InsightsList 
            insights={analyticsData.insights || []} 
            loading={loading} 
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AnalyticsDashboard;
