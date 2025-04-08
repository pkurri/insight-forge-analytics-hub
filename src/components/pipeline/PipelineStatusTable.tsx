
import React from 'react';
import { Badge } from '@/components/ui/badge';

interface PipelineJob {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'failed' | 'queued';
  type: string;
  progress: number;
  startTime: string;
  endTime?: string;
}

const PipelineStatusTable: React.FC = () => {
  const pipelineJobs: PipelineJob[] = [
    {
      id: 'job-001',
      name: 'Customer Data Processing',
      status: 'completed',
      type: 'CSV File',
      progress: 100,
      startTime: '2025-04-08 08:30:00',
      endTime: '2025-04-08 08:35:12'
    },
    {
      id: 'job-002',
      name: 'Product Catalog Import',
      status: 'running',
      type: 'JSON API',
      progress: 68,
      startTime: '2025-04-08 09:15:00'
    },
    {
      id: 'job-003',
      name: 'Sales Data Validation',
      status: 'running',
      type: 'Excel File',
      progress: 32,
      startTime: '2025-04-08 09:20:00'
    },
    {
      id: 'job-004',
      name: 'Inventory Analysis',
      status: 'queued',
      type: 'Database',
      progress: 0,
      startTime: '2025-04-08 09:30:00'
    },
    {
      id: 'job-005',
      name: 'Financial Report PDF',
      status: 'failed',
      type: 'PDF Document',
      progress: 45,
      startTime: '2025-04-08 07:45:00',
      endTime: '2025-04-08 07:52:30'
    }
  ];
  
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
                {job.endTime 
                  ? (() => {
                      const start = new Date(job.startTime);
                      const end = new Date(job.endTime);
                      const diffInSeconds = (end.getTime() - start.getTime()) / 1000;
                      return `${diffInSeconds.toFixed(1)}s`;
                    })()
                  : job.status === 'running' 
                    ? 'In progress...' 
                    : '--'
                }
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PipelineStatusTable;
