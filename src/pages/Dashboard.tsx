
import React from 'react';
import { ArrowUpDown, FileText, Server, Database, CheckCircle2 } from 'lucide-react';

import MetricCard from '@/components/dashboard/MetricCard';
import StatusCard from '@/components/dashboard/StatusCard';
import PipelineFlow from '@/components/dashboard/PipelineFlow';
import ActivityTimeline from '@/components/dashboard/ActivityTimeline';

const Dashboard: React.FC = () => {
  // Pipeline Nodes
  const pipelineNodes = [
    { id: 'ingestion', name: 'Data Ingestion', status: 'operational' as const },
    { id: 'cleaning', name: 'Data Cleaning', status: 'operational' as const },
    { id: 'validation', name: 'Data Validation', status: 'warning' as const },
    { id: 'anomaly', name: 'Anomaly Detection', status: 'operational' as const },
    { id: 'storage', name: 'Data Storage', status: 'operational' as const },
  ];

  // Pipeline Connections
  const pipelineConnections = [
    { source: 'ingestion', target: 'cleaning', status: 'active' as const },
    { source: 'cleaning', target: 'validation', status: 'active' as const },
    { source: 'validation', target: 'anomaly', status: 'warning' as const },
    { source: 'anomaly', target: 'storage', status: 'active' as const },
  ];

  // Activity Timeline
  const activities = [
    {
      id: '1',
      message: 'Data validation warning: Schema mismatch in sales_data table',
      timestamp: '15 minutes ago',
      type: 'warning' as const,
    },
    {
      id: '2',
      message: 'Scheduled analytics report generated successfully',
      timestamp: '1 hour ago',
      type: 'success' as const,
    },
    {
      id: '3',
      message: 'New data source added: Marketing Campaign Results',
      timestamp: '3 hours ago',
      type: 'info' as const,
    },
    {
      id: '4',
      message: 'System backup completed',
      timestamp: '5 hours ago',
      type: 'success' as const,
    },
    {
      id: '5',
      message: 'Failed to connect to external API endpoint',
      timestamp: 'Yesterday, 20:45',
      type: 'error' as const,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of your data pipeline and analytics system
        </p>
      </div>

      {/* Metrics Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Processed Today"
          value="24,832"
          icon={<ArrowUpDown />}
          change={12}
          trend="up"
          trendText="from yesterday"
        />
        <MetricCard
          title="Success Rate"
          value="98.7%"
          icon={<CheckCircle2 />}
          change={1.2}
          trend="up"
          trendText="from last week"
        />
        <MetricCard
          title="Data Sources"
          value="12"
          icon={<Database />}
          change={2}
          trend="up"
          trendText="new this month"
        />
        <MetricCard
          title="Storage Used"
          value="1.2 TB"
          icon={<Server />}
          change={5}
          trend="up"
          trendText="from last month"
        />
      </div>

      {/* Pipeline Flow */}
      <PipelineFlow nodes={pipelineNodes} connections={pipelineConnections} />

      {/* Status Cards and Activity */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">System Status</h2>
          <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-2">
            <StatusCard
              title="Ingestion Agent"
              description="Processing new data sources"
              status="operational"
              lastUpdated="5 min ago"
            />
            <StatusCard
              title="Cleaning Agent"
              description="Handling data normalization"
              status="operational"
              lastUpdated="7 min ago"
            />
            <StatusCard
              title="Validation Agent"
              description="Schema validation running"
              status="warning"
              lastUpdated="10 min ago"
            />
            <StatusCard
              title="Anomaly Agent"
              description="Detecting irregular patterns"
              status="operational"
              lastUpdated="12 min ago"
            />
            <StatusCard
              title="Storage Agent"
              description="Managing data storage and retrieval"
              status="operational"
              lastUpdated="15 min ago"
            />
            <StatusCard
              title="API Service"
              description="Handling external requests"
              status="operational"
              lastUpdated="3 min ago"
            />
          </div>
        </div>
        
        <ActivityTimeline activities={activities} />
      </div>
    </div>
  );
};

export default Dashboard;
