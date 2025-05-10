import React, { useState, useEffect, useCallback } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger,
  Button 
} from '@/components/ui';
import { RefreshCw, BarChart2, LineChart, AlertCircle } from 'lucide-react';
import MetricCard from './MetricCard';
import DashboardChart from './DashboardChart';
import DatasetSummary from './DatasetSummary';
import RecentActivity from './RecentActivity';
import { api } from '@/api/api';
import { useToast } from '@/hooks/use-toast';

// Import necessary components for dashboard sections
import SystemAlerts from '@/components/dashboard/SystemAlerts';
import QualityScores from '@/components/dashboard/QualityScores';
// Import but comment out unused components to fix lint warnings
// import PipelineMetrics from './PipelineMetrics';
// import TimeSeriesChart from './TimeSeriesChart';

// Define a more specific type for score data to avoid using 'any'
interface ComponentScore {
  average_score: number;
  details?: Record<string, number>;
  last_updated?: string;
}

interface QualityScore {
  id: string;
  name: string;
  score: number;
  category: string;
  lastUpdated: string;
  average_score?: number;
}

interface QualityScoresData {
  scores: QualityScore[];
  [key: string]: unknown;
}

// Helper functions to simplify the component rendering logic
const getScoreColorClass = (score: ComponentScore | unknown): string => {
  if (score && typeof score === 'object' && 'average_score' in score && 
      typeof score.average_score === 'number') {
    if (score.average_score >= 85) return 'text-green-500';
    if (score.average_score >= 70) return 'text-amber-500';
  }
  return 'text-red-500';
};

const getScoreValue = (score: ComponentScore | unknown): number => {
  if (score && typeof score === 'object' && 'average_score' in score && 
      typeof score.average_score === 'number') {
    return Math.round(score.average_score);
  }
  return 0;
};

interface MetricsData {
  data: unknown[];
  [key: string]: unknown;
}

interface DashboardProps {
  className?: string;
}

const Dashboard: React.FC<DashboardProps> = ({ className }) => {
  const [loading, setLoading] = useState<boolean>(true);
  // Initialize with proper default values to avoid type errors
  const [metrics, setMetrics] = useState<MetricsData>({ data: [] });
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [qualityScores, setQualityScores] = useState<QualityScoresData>({ scores: [] });
  const { toast } = useToast();
  
  // Use useCallback to prevent dependency changes on every render
  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch dashboard metrics
      const metricsResponse = await api.getDashboardMetrics();
      if (metricsResponse.success && metricsResponse.data) {
        // Type assertion to ensure data matches our expected type
        setMetrics(metricsResponse.data as MetricsData);
      } else {
        console.error('Failed to load dashboard metrics:', metricsResponse.error);
        toast({
          title: 'Error',
          description: 'Failed to load dashboard metrics',
          variant: 'destructive'
        });
        // Set default metrics data on error
        setMetrics({ data: [] });
      }
      
      // Fetch project quality scores from OpenEvals
      const qualityResponse = await api.getProjectQualityScores();
      if (qualityResponse.success && qualityResponse.data) {
        // Type assertion to ensure data matches our expected type
        setQualityScores(qualityResponse.data as QualityScoresData);
      } else {
        console.error('Failed to load quality scores:', qualityResponse.error);
        toast({
          title: 'Warning',
          description: 'Failed to load project quality scores',
          variant: 'default'
        });
        // Set default quality scores data on error
        setQualityScores({ scores: [] });
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to connect to monitoring service',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);
  
  useEffect(() => {
    loadDashboardData();
    
    // Refresh dashboard every 5 minutes
    const interval = setInterval(loadDashboardData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadDashboardData]);
  
  const handleRefresh = async () => {
    setLoading(true);
    try {
      const metricsResponse = await api.getDashboardMetrics();
      if (metricsResponse.success && metricsResponse.data) {
        // Type assertion to ensure data matches our expected type
        setMetrics(metricsResponse.data as MetricsData);
      }
      
      const qualityResponse = await api.getProjectQualityScores();
      if (qualityResponse.success && qualityResponse.data) {
        // Type assertion to ensure data matches our expected type
        setQualityScores(qualityResponse.data as QualityScoresData);
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
          value={typeof metrics.totalDatasets === 'number' ? metrics.totalDatasets : 0}
          icon={<BarChart2 className="h-5 w-5" />}
          change={typeof metrics.datasetChange === 'number' ? metrics.datasetChange : undefined}
          loading={loading}
        />
        <MetricCard
          title="Processed Pipelines"
          value={typeof metrics.processedPipelines === 'number' ? metrics.processedPipelines : 0}
          icon={<LineChart className="h-5 w-5" />}
          change={typeof metrics.pipelineChange === 'number' ? metrics.pipelineChange : undefined}
          loading={loading}
        />
        <MetricCard
          title="AI Interactions"
          value={typeof metrics.aiInteractions === 'number' ? metrics.aiInteractions : 0}
          icon={<LineChart className="h-5 w-5" />}
          change={typeof metrics.interactionsChange === 'number' ? metrics.interactionsChange : undefined}
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
              data={Array.isArray(metrics.activityData) ? metrics.activityData : []}
              type="line"
              loading={loading}
            />
            <DashboardChart
              title="Resource Usage"
              description="System resource allocation"
              data={Array.isArray(metrics.resourceData) ? metrics.resourceData : []}
              type="bar"
              loading={loading}
            />
          </div>
          <RecentActivity activities={Array.isArray(metrics.recentActivities) ? metrics.recentActivities : []} loading={loading} />
          <SystemAlerts alerts={Array.isArray(metrics.systemAlerts) ? metrics.systemAlerts : []} />
        </TabsContent>
        
        <TabsContent value="datasets" className="space-y-4">
          <DatasetSummary datasets={Array.isArray(metrics.topDatasets) ? metrics.topDatasets : []} loading={loading} />
        </TabsContent>
        
        <TabsContent value="pipelines" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <DashboardChart
              title="Pipeline Performance"
              description="Execution time by pipeline stage"
              data={Array.isArray(metrics.pipelinePerformance) ? metrics.pipelinePerformance : []}
              type="bar"
              loading={loading}
            />
            <DashboardChart
              title="Success Rate"
              description="Pipeline success vs failures"
              data={Array.isArray(metrics.pipelineSuccess) ? metrics.pipelineSuccess : []}
              type="pie"
              loading={loading}
            />
          </div>
        </TabsContent>
        
        <TabsContent value="quality" className="space-y-4">
          <QualityScores scores={Array.isArray(qualityScores.scores) ? qualityScores.scores : []} />
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
                  {Object.entries(qualityScores).map(([component, score]) => (
                    <div key={component} className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="font-medium">{component}</span>
                        <span className={`text-sm font-bold ${getScoreColorClass(score)}`}>
                          {getScoreValue(score)}%
                        </span>
                      </div>
                      <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
                        <div 
                          className={`h-2 ${score && typeof score === 'object' && 'average_score' in score && typeof score.average_score === 'number' && score.average_score >= 85 ? 'bg-green-500' : score && typeof score === 'object' && 'average_score' in score && typeof score.average_score === 'number' && score.average_score >= 70 ? 'bg-amber-500' : 'bg-red-500'}`}
                          style={{ width: `${score && typeof score === 'object' && 'average_score' in score && typeof score.average_score === 'number' ? score.average_score : 0}%` }}
                        />
                      </div>
                      {score && typeof score === 'object' && 'last_evaluation' in score && score.last_evaluation && (
                        <p className="text-xs text-muted-foreground">Last evaluated: {new Date(String(score.last_evaluation)).toLocaleString()}</p>
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
