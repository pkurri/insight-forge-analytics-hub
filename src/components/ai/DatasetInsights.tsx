import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Sparkles, BarChart, FileText, AlertCircle, RefreshCw } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { DatasetSelector } from './DatasetSelector';
import { useToast } from '@/hooks/use-toast';
import { datasetService, taskService } from '@/api/api';
import { Insight, TaskProgress } from '@/api/services/datasets/datasetService';

// Using the Insight interface imported from datasetService

interface Dataset {
  id: string;
  name: string;
  rows: number;
  columns: number;
  lastUpdated: string;
  source?: string;
}

interface DatasetInsightsProps {
  datasets?: Dataset[];
  initialDatasetId?: string;
  className?: string;
}

/**
 * DatasetInsights component that uses RAG and agentic framework to provide insights on datasets
 */
const DatasetInsights: React.FC<DatasetInsightsProps> = ({
  datasets = [],
  initialDatasetId,
  className = '',
}) => {
  const [selectedDataset, setSelectedDataset] = useState<string>(initialDatasetId || '');
  const [insights, setInsights] = useState<Insight[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<string>('all');
  const [generatingInsights, setGeneratingInsights] = useState<boolean>(false);
  const [generationProgress, setGenerationProgress] = useState<number>(0);

  const { toast } = useToast();

  // Fetch insights when dataset changes
  useEffect(() => {
    if (!selectedDataset) return;
    
    const fetchInsights = async () => {
      setIsLoading(true);
      try {
        const response = await datasetService.getInsights(selectedDataset);
        if (response.success && response.data) {
          // The API returns an object with insights array
          setInsights(Array.isArray(response.data.insights) ? response.data.insights : []);
        } else {
          console.error('Failed to fetch insights:', response.error);
          toast({
            title: 'Error',
            description: 'Failed to fetch dataset insights',
            variant: 'destructive'
          });
          setInsights([]);
        }
      } catch (error) {
        console.error('Error fetching insights:', error);
        toast({
          title: 'Error',
          description: 'Failed to connect to insights service',
          variant: 'destructive'
        });
        setInsights([]);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchInsights();
  }, [selectedDataset, toast]);

  // Generate new insights using the RAG and agentic framework
  const handleGenerateInsights = async () => {
    if (!selectedDataset || generatingInsights) return;
    
    setGeneratingInsights(true);
    setGenerationProgress(0);
    
    try {
      // Start the generation process
      const startResponse = await datasetService.generateInsights(selectedDataset, {
        use_agent: true, // Enable agentic capabilities
        insight_types: ['data_quality', 'feature_engineering', 'anomaly', 'correlation'],
      });
      
      if (!startResponse.success || !startResponse.data) {
        throw new Error(startResponse.error || 'Failed to start insight generation');
      }
      
      const { task_id } = startResponse.data;
      
      toast({
        title: 'Generating Insights',
        description: 'Starting insight generation process...',
        variant: 'default'
      });
      
      // Poll for progress
      const pollInterval = setInterval(async () => {
        try {
          const progressResponse = await taskService.getProgress(task_id);
          
          if (progressResponse.success && progressResponse.data) {
            const progressData = progressResponse.data as TaskProgress;
            setGenerationProgress(progressData.progress || 0);
            
            if (progressData.status === 'completed') {
              clearInterval(pollInterval);
              setGeneratingInsights(false);
              
              toast({
                title: 'Success',
                description: 'Insights generation completed successfully',
                variant: 'default'
              });
              
              // Fetch the new insights
              const insightsResponse = await datasetService.getInsights(selectedDataset);
              if (insightsResponse.success && insightsResponse.data) {
                // The API returns an object with insights array
                setInsights(Array.isArray(insightsResponse.data.insights) ? insightsResponse.data.insights : []);
              }
            } else if (progressData.status === 'failed') {
              clearInterval(pollInterval);
              setGeneratingInsights(false);
              
              toast({
                title: 'Error',
                description: `Insight generation failed: ${progressData.error || 'Unknown error'}`,
                variant: 'destructive'
              });
              
              console.error('Insight generation failed:', progressData.error);
            }
          }
        } catch (pollError) {
          console.error('Error polling task progress:', pollError);
        }
      }, 1500);
      
      // Cleanup interval on component unmount
      return () => clearInterval(pollInterval);
    } catch (error) {
      console.error('Error generating insights:', error);
      
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to generate insights',
        variant: 'destructive'
      });
      
      setGeneratingInsights(false);
    }
  };

  // Filter insights based on active tab
  const filteredInsights = insights.filter(insight => {
    if (activeTab === 'all') return true;
    return insight.type === activeTab;
  });

  // Get count by type
  const insightCounts = {
    data_quality: insights.filter(i => i.type === 'data_quality').length,
    feature_engineering: insights.filter(i => i.type === 'feature_engineering').length,
    anomaly: insights.filter(i => i.type === 'anomaly').length,
    correlation: insights.filter(i => i.type === 'correlation').length,
  };

  // Render confidence badge
  const renderConfidenceBadge = (confidence: number) => {
    let color = 'bg-amber-50 text-amber-700 border-amber-200';
    if (confidence >= 0.8) {
      color = 'bg-green-50 text-green-700 border-green-200';
    } else if (confidence < 0.5) {
      color = 'bg-red-50 text-red-700 border-red-200';
    }
    
    return (
      <Badge variant="outline" className={color}>
        {Math.round(confidence * 100)}% confidence
      </Badge>
    );
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Dataset Insights</h3>
        
        <DatasetSelector
          datasets={datasets}
          selectedDataset={selectedDataset}
          onDatasetChange={setSelectedDataset}
          isLoading={isLoading}
          showAllOption={false}
          className="w-[200px]"
        />
      </div>
      
      {selectedDataset ? (
        <>
          <div className="flex justify-between items-center">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid grid-cols-5">
                <TabsTrigger value="all">
                  All ({insights.length})
                </TabsTrigger>
                <TabsTrigger value="data_quality">
                  Quality ({insightCounts.data_quality})
                </TabsTrigger>
                <TabsTrigger value="feature_engineering">
                  Features ({insightCounts.feature_engineering})
                </TabsTrigger>
                <TabsTrigger value="anomaly">
                  Anomalies ({insightCounts.anomaly})
                </TabsTrigger>
                <TabsTrigger value="correlation">
                  Correlations ({insightCounts.correlation})
                </TabsTrigger>
              </TabsList>
            </Tabs>
            
            <Button 
              onClick={handleGenerateInsights} 
              disabled={generatingInsights || !selectedDataset}
              size="sm"
              className="ml-2"
            >
              {generatingInsights ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Generate Insights
                </>
              )}
            </Button>
          </div>
          
          {generatingInsights && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Generating insights...</span>
                <span>{Math.round(generationProgress)}%</span>
              </div>
              <Progress value={generationProgress} className="h-2" />
            </div>
          )}
          
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map(i => (
                <Card key={i}>
                  <CardHeader className="pb-2">
                    <Skeleton className="h-4 w-2/3" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-4 w-full mb-2" />
                    <Skeleton className="h-4 w-5/6" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : filteredInsights.length > 0 ? (
            <div className="space-y-4">
              {filteredInsights.map(insight => (
                <Card key={insight.id}>
                  <CardHeader className="pb-2">
                    <div className="flex justify-between items-start">
                      <CardTitle className="text-base">{insight.title}</CardTitle>
                      {renderConfidenceBadge(insight.confidence)}
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="secondary" className="text-xs">
                        {insight.type === 'data_quality' && 'Data Quality'}
                        {insight.type === 'feature_engineering' && 'Feature Engineering'}
                        {insight.type === 'anomaly' && 'Anomaly'}
                        {insight.type === 'correlation' && 'Correlation'}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {new Date(insight.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm">{insight.description}</p>
                  </CardContent>
                  {insight.metadata && (
                    <CardFooter className="pt-0 text-xs text-muted-foreground">
                      {insight.metadata && 'affected_columns' in insight.metadata && Array.isArray(insight.metadata.affected_columns) && (
                        <div className="flex items-center space-x-1">
                          <FileText className="h-3 w-3" />
                          <span>Affected columns: {(insight.metadata.affected_columns as string[]).join(', ')}</span>
                        </div>
                      )}
                    </CardFooter>
                  )}
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-8">
                <AlertCircle className="h-8 w-8 text-muted-foreground mb-2" />
                <p className="text-muted-foreground text-center">
                  No insights available for this dataset yet.
                </p>
                <Button 
                  onClick={handleGenerateInsights} 
                  disabled={generatingInsights}
                  variant="outline"
                  className="mt-4"
                >
                  <Sparkles className="h-4 w-4 mr-2" />
                  Generate Insights
                </Button>
              </CardContent>
            </Card>
          )}
        </>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-8">
            <BarChart className="h-8 w-8 text-muted-foreground mb-2" />
            <p className="text-muted-foreground text-center">
              Select a dataset to view insights
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export { DatasetInsights };
export type { Dataset, Insight };
