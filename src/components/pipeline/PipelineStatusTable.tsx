import React, { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { api } from '@/api/api';
import { useToast } from '@/hooks/use-toast';
import { Loader2, Play, RefreshCw, CheckCircle, XCircle, Clock, AlertTriangle, ArrowRight, Info } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

interface PipelineJob {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'failed' | 'queued' | 'pending';
  type: string;
  progress: number;
  startTime: string;
  endTime?: string;
  steps?: {
    id: number;
    name: string;
    status: string;
  }[];
  businessRulesStatus?: {
    total: number;
    passed: number;
    failed: number;
  };
}

interface PipelineStatusTableProps {
  datasetId?: string;
}

const PipelineStatusTable: React.FC<PipelineStatusTableProps> = ({ datasetId }) => {
  const [pipelineJobs, setPipelineJobs] = useState<PipelineJob[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [runningSteps, setRunningSteps] = useState<Set<number>>(new Set());
  const { toast } = useToast();
  
  useEffect(() => {
    if (datasetId) {
      fetchPipelineRuns(datasetId);
    }
  }, [datasetId]);
  
  const fetchPipelineRuns = async (datasetId: string) => {
    setIsLoading(true);
    try {
      const response = await api.pipelineService.getPipelineRuns(datasetId);
      
      if (response.success && response.data) {
        // Transform pipeline data to match our component's format
        const jobs: PipelineJob[] = response.data.map((run: any) => {
          // Find business rules stage if it exists
          const businessRulesStage = run.steps.find((step: any) => 
            step.name.toLowerCase().includes('business') || 
            step.name.toLowerCase().includes('rule')
          );
          
          return {
            id: run.id,
            name: `Pipeline Run ${run.id.substring(0, 8)}`,
            status: run.status,
            type: run.current_stage,
            progress: run.progress,
            startTime: run.created_at,
            endTime: run.updated_at,
            steps: run.steps,
            businessRulesStatus: businessRulesStage ? {
              total: 0, // These would come from the actual API response
              passed: 0,
              failed: 0
            } : undefined
          };
        });
        
        setPipelineJobs(jobs);
      } else {
        toast({
          title: "Failed to fetch pipeline runs",
          description: response.error || "An error occurred while fetching pipeline runs",
          variant: "destructive"
        });
        // Fall back to mock data if API fails
        setPipelineJobs([
          {
            id: 'job-001',
            name: 'Customer Data Processing',
            status: 'completed',
            type: 'CSV File',
            progress: 100,
            startTime: '2025-04-08 08:30:00',
            endTime: '2025-04-08 08:35:12',
            businessRulesStatus: {
              total: 10,
              passed: 8,
              failed: 2
            }
          },
          {
            id: 'job-002',
            name: 'Product Catalog Import',
            status: 'running',
            type: 'JSON API',
            progress: 68,
            startTime: '2025-04-08 09:15:00'
          }
        ]);
      }
    } catch (error) {
      console.error("Error fetching pipeline runs:", error);
      toast({
        title: "Error",
        description: "Failed to fetch pipeline runs",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunStep = async (stepId: number) => {
    try {
      setRunningSteps(prev => new Set(prev).add(stepId));
      
      // Call the API to run the pipeline step
      const response = await api.pipelineService.runPipelineStage(datasetId || '', String(stepId));
      
      if (response.success) {
        toast({
          title: "Step started",
          description: "The pipeline step has been initiated successfully.",
        });
        // Refresh the pipeline runs after a short delay
        setTimeout(() => {
          datasetId && fetchPipelineRuns(datasetId);
        }, 1000);
      } else {
        throw new Error(response.error || "Failed to start pipeline step");
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to start pipeline step",
        variant: "destructive",
      });
    } finally {
      setRunningSteps(prev => {
        const next = new Set(prev);
        next.delete(stepId);
        return next;
      });
    }
  };
  
  const getStatusBadge = (status: PipelineJob['status']) => {
    switch (status) {
      case 'running':
        return (
          <div className="flex items-center gap-1">
            <Loader2 className="h-3 w-3 animate-spin text-blue-500" />
            <Badge className="bg-blue-500">Running</Badge>
          </div>
        );
      case 'completed':
        return (
          <div className="flex items-center gap-1">
            <CheckCircle className="h-3 w-3 text-green-500" />
            <Badge className="bg-green-500">Completed</Badge>
          </div>
        );
      case 'failed':
        return (
          <div className="flex items-center gap-1">
            <XCircle className="h-3 w-3 text-red-500" />
            <Badge className="bg-red-500">Failed</Badge>
          </div>
        );
      case 'queued':
        return (
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3 text-yellow-500" />
            <Badge className="bg-yellow-500">Queued</Badge>
          </div>
        );
      case 'pending':
        return (
          <div className="flex items-center gap-1">
            <AlertTriangle className="h-3 w-3 text-gray-500" />
            <Badge className="bg-gray-500">Pending</Badge>
          </div>
        );
      default:
        return <Badge>Unknown</Badge>;
    }
  };

  const getProgressBar = (progress: number) => {
    return (
      <div className="flex items-center gap-2">
        <Progress 
          value={progress} 
          className={cn(
            "h-2", 
            progress === 100 ? "bg-green-100" : 
            progress > 0 ? "bg-blue-100" : "bg-gray-100"
          )}
        />
        <span className="text-xs font-medium">{Math.round(progress)}%</span>
      </div>
    );
  };

  if (isLoading) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center p-8">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-2">Loading pipeline data...</span>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card className="w-full shadow-sm border-muted">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-center">
          <CardTitle>Pipeline Runs</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => datasetId && fetchPipelineRuns(datasetId)}
            disabled={isLoading}
            className="h-8"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
        <CardDescription>View and manage your data processing pipeline runs</CardDescription>
      </CardHeader>
      <CardContent>
        {pipelineJobs.length === 0 ? (
          <div className="text-center py-8 bg-muted/20 rounded-md">
            <Info className="h-12 w-12 text-muted-foreground mx-auto mb-3 opacity-50" />
            <p className="text-muted-foreground">No pipeline jobs found</p>
            <p className="text-xs text-muted-foreground mt-1">Start a new pipeline run to see results here</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b">
                <tr>
                  <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider py-3">Job</th>
                  <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider py-3">Status</th>
                  <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider py-3">Type</th>
                  <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider py-3 w-[200px]">Progress</th>
                  <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider py-3">Time</th>
                  <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {pipelineJobs.map((job) => (
                  <tr key={job.id} className="hover:bg-muted/20 transition-colors">
                    <td className="py-4">
                      <div className="text-sm font-medium">{job.name}</div>
                      {job.businessRulesStatus && (
                        <div className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                          <span className={job.businessRulesStatus.failed > 0 ? "text-red-500" : "text-green-500"}>
                            Rules: {job.businessRulesStatus.passed}/{job.businessRulesStatus.total} passed
                          </span>
                          {job.businessRulesStatus.failed > 0 && (
                            <Badge variant="destructive" className="text-[10px] h-4">
                              {job.businessRulesStatus.failed} failed
                            </Badge>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="py-4">
                      {getStatusBadge(job.status)}
                    </td>
                    <td className="py-4 text-sm text-muted-foreground">
                      {job.type}
                    </td>
                    <td className="py-4 w-[200px]">
                      {getProgressBar(job.progress)}
                    </td>
                    <td className="py-4 text-sm text-muted-foreground">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger className="text-left">
                            <div>{new Date(job.startTime).toLocaleDateString()}</div>
                            <div className="text-xs">{job.endTime ? `Completed: ${new Date(job.endTime).toLocaleTimeString()}` : 'Running...'}</div>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Started: {new Date(job.startTime).toLocaleString()}</p>
                            {job.endTime && <p>Ended: {new Date(job.endTime).toLocaleString()}</p>}
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </td>
                    <td className="py-4">
                      <div className="flex flex-wrap gap-2">
                        {job.steps && job.steps.map((step, index) => (
                          <Button
                            key={`${job.id}-step-${index}`}
                            variant={step.status === 'failed' ? "destructive" : "outline"}
                            size="sm"
                            onClick={() => step.id && handleRunStep(step.id)}
                            disabled={runningSteps.has(step.id || 0) || job.status === 'running' || step.status === 'completed'}
                            className="h-7 text-xs"
                          >
                            {runningSteps.has(step.id || 0) ? (
                              <>
                                <Loader2 className="h-3 w-3 animate-spin mr-1" />
                                Running...
                              </>
                            ) : step.status === 'failed' ? (
                              <>
                                <ArrowRight className="h-3 w-3 mr-1" />
                                Retry {step.name}
                              </>
                            ) : (
                              <>
                                <Play className="h-3 w-3 mr-1" />
                                Run {step.name}
                              </>
                            )}
                          </Button>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default PipelineStatusTable;
