import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { RefreshCw, BarChart2, LineChart, PieChart, AlertCircle } from 'lucide-react';
import MetricCard from './MetricCard';
import DashboardChart from './DashboardChart';
import DatasetSummary from './DatasetSummary';
import RecentActivity from './RecentActivity';
import { api } from '@/api/api';

interface DashboardProps {
  className?: string;
}

const Dashboard: React.FC<DashboardProps> = ({ className }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [metrics, setMetrics] = useState<any>({});
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [qualityScores, setQualityScores] = useState<any>({});
  
  useEffect(() => {
    // Load dashboard metrics
    const loadDashboardData = async () => {
      setLoading(true);
      try {
        // Fetch dashboard metrics
        const metricsResponse = await api.getDashboardMetrics();
        if (metricsResponse.success) {
          setMetrics(metricsResponse.data);
        }
        
        // Fetch project quality scores
        const qualityResponse = await api.getProjectQualityScores();
        if (qualityResponse.success) {
          setQualityScores(qualityResponse.data);
        }
      } catch (error) {
        console.error('Error loading dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadDashboardData();
    
    // Refresh dashboard every 5 minutes
    const interval = setInterval(loadDashboardData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);
  
  const handleRefresh = async () => {
    setLoading(true);
    try {
      const metricsResponse = await api.getDashboardMetrics();
      if (metricsResponse.success) {
        setMetrics(metricsResponse.data);
      }
      
      const qualityResponse = await api.getProjectQualityScores();
      if (qualityResponse.success) {
        setQualityScores(qualityResponse.data);
      }
    } catch (error) {
      console.error('Error refreshing dashboard:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className={`p-4 space-y-6 ${className}`}>
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Button variant="outline" size="sm" onClick={handleRefresh} disabled={loading}>
          {loading ? (
            <RefreshCw className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <RefreshCw className="h-4 w-4 mr-2" />
          )}
          Refresh
        </Button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard 
          title="Total Datasets" 
          value={metrics.totalDatasets || 0} 
          icon={<BarChart2 className="h-5 w-5" />}
          change={metrics.datasetChange}
          loading={loading}
        />
        <MetricCard 
          title="Processed Pipelines" 
          value={metrics.processedPipelines || 0} 
          icon={<LineChart className="h-5 w-5" />}
          change={metrics.pipelineChange}
          loading={loading}
        />
        <MetricCard 
          title="AI Interactions" 
          value={metrics.aiInteractions || 0} 
          icon={<PieChart className="h-5 w-5" />}
          change={metrics.interactionsChange}
          loading={loading}
        />
      </div>
      
      <Tabs defaultValue="overview" value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid grid-cols-4 mb-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="datasets">Datasets</TabsTrigger>
          <TabsTrigger value="pipelines">Pipelines</TabsTrigger>
          <TabsTrigger value="quality">Quality</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <DashboardChart 
              title="Activity Overview" 
              description="User activity over time"
              data={metrics.activityData || []}
              type="line"
              loading={loading}
            />
            <DashboardChart 
              title="Resource Usage" 
              description="System resource allocation"
              data={metrics.resourceData || []}
              type="bar"
              loading={loading}
            />
          </div>
          <RecentActivity activities={metrics.recentActivities || []} loading={loading} />
        </TabsContent>
        
        <TabsContent value="datasets" className="space-y-4">
          <DatasetSummary datasets={metrics.datasets || []} loading={loading} />
        </TabsContent>
        
        <TabsContent value="pipelines" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <DashboardChart 
              title="Pipeline Performance" 
              description="Execution time by pipeline stage"
              data={metrics.pipelinePerformance || []}
              type="bar"
              loading={loading}
            />
            <DashboardChart 
              title="Success Rate" 
              description="Pipeline success vs failures"
              data={metrics.pipelineSuccess || []}
              type="pie"
              loading={loading}
            />
          </div>
        </TabsContent>
        
        <TabsContent value="quality" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Code Quality Scores
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => api.runProjectEvaluation()}
                  disabled={loading}
                >
                  Run Evaluation
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center py-8">
                  <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : Object.keys(qualityScores).length > 0 ? (
                <div className="space-y-4">
                  {Object.entries(qualityScores).map(([component, score]: [string, any]) => (
                    <div key={component} className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="font-medium">{component}</span>
                        <span className={`text-sm font-bold ${Number(score.average_score) >= 85 ? 'text-green-500' : Number(score.average_score) >= 70 ? 'text-amber-500' : 'text-red-500'}`}>
                          {Math.round(Number(score.average_score))}%
                        </span>
                      </div>
                      <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
                        <div 
                          className={`h-2 ${Number(score.average_score) >= 85 ? 'bg-green-500' : Number(score.average_score) >= 70 ? 'bg-amber-500' : 'bg-red-500'}`}
                          style={{ width: `${score.average_score}%` }}
                        />
                      </div>
                      {score.last_evaluation && (
                        <p className="text-xs text-muted-foreground">Last evaluated: {new Date(score.last_evaluation).toLocaleString()}</p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">No quality evaluations available.</p>
                  <p className="text-sm text-muted-foreground mt-2">Run an evaluation to see code quality metrics.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Dashboard;
