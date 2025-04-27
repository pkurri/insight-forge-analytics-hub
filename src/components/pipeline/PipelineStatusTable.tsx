
import React, { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { pipelineService } from '@/api/services/pipeline/pipelineService';
import { useToast } from '@/hooks/use-toast';
import { Loader2 } from 'lucide-react';

interface PipelineJob {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'failed' | 'queued';
  type: string;
  progress: number;
  startTime: string;
  endTime?: string;
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
  const { toast } = useToast();
  
  useEffect(() => {
    if (datasetId) {
      fetchPipelineRuns(datasetId);
    }
  }, [datasetId]);
  
  const fetchPipelineRuns = async (datasetId: string) => {
    setIsLoading(true);
    try {
      const response = await pipelineService.getPipelineRuns(datasetId);
      
      if (response.success && response.data) {
        // Transform pipeline data to match our component's format
        const jobs: PipelineJob[] = response.data.map(run => {
          // Find business rules stage if it exists
          const businessRulesStage = run.stages.find(stage => 
            stage.name.toLowerCase().includes('business') || 
            stage.name.toLowerCase().includes('rule')
          );
          
          return {
            id: run.id,
            name: `Pipeline Run ${run.id.substring(0, 8)}`,
            status: run.status,
            type: run.current_stage,
            progress: run.progress,
            startTime: run.created_at,
            endTime: run.updated_at,
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
  
  const getStatusBadge = (status: PipelineJob['status']) => {
    switch (status) {
      case 'running':
        return <Badge className="bg-blue-500">Running</Badge>;
      case 'completed':
        return <Badge className="bg-green-500">Completed</Badge>;
      case 'failed':
        return <Badge className="bg-red-500">Failed</Badge>;
      case 'queued':
        return <Badge className="bg-yellow-500">Queued</Badge>;
      default:
        return <Badge>Unknown</Badge>;
    }
  };

  const getProgressBar = (progress: number) => {
    return (
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${
            progress === 100 ? 'bg-green-500' : 
            progress > 0 ? 'bg-blue-500' : 'bg-gray-300'
          }`}
          style={{ width: `${progress}%` }}
        ></div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2">Loading pipeline data...</span>
      </div>
    );
  }
  
  return (
    <div className="overflow-x-auto">
      <table className="w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Job</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Progress</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Time</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Business Rules</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {pipelineJobs.map((job) => (
            <tr key={job.id}>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="font-medium text-gray-900">{job.name}</div>
                <div className="text-sm text-gray-500">{job.id}</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {getStatusBadge(job.status)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {job.type}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <div className="w-full mr-2">
                    {getProgressBar(job.progress)}
                  </div>
                  <span className="text-xs text-gray-500">{job.progress}%</span>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {job.startTime}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {job.endTime ? 
                  new Date(new Date(job.endTime) - new Date(job.startTime)).toISOString().substr(11, 8) : 
                  'In progress'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                {job.businessRulesStatus ? (
                  <div className="flex flex-col">
                    <span className="font-medium">{job.businessRulesStatus.passed} / {job.businessRulesStatus.total} passed</span>
                    {job.businessRulesStatus.failed > 0 && (
                      <span className="text-red-500 text-xs mt-1">{job.businessRulesStatus.failed} rules failed</span>
                    )}
                  </div>
                ) : (
                  <span className="text-gray-400">Not available</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PipelineStatusTable;
