
import React from 'react';
import { FileUp, FilterX, CheckCircle2, Activity, BarChart3, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StageProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  status: 'completed' | 'in-progress' | 'pending' | 'error';
  isLast?: boolean;
}

const Stage: React.FC<StageProps> = ({ icon, title, description, status, isLast = false }) => {
  const getStatusColor = () => {
    switch (status) {
      case 'completed': return 'bg-green-500 text-white border-green-500';
      case 'in-progress': return 'bg-blue-500 text-white border-blue-500 animate-pulse';
      case 'error': return 'bg-red-500 text-white border-red-500';
      default: return 'bg-gray-200 text-gray-500 border-gray-300';
    }
  };

  return (
    <div className="flex items-start">
      <div className={cn("flex flex-col items-center")}>
        <div className={cn("w-10 h-10 rounded-full flex items-center justify-center border-2", getStatusColor())}>
          {icon}
        </div>
        {!isLast && <div className="w-0.5 h-16 bg-gray-300 mt-2"></div>}
      </div>
      <div className="ml-4 mt-1">
        <h3 className="font-medium">{title}</h3>
        <p className="text-sm text-gray-500">{description}</p>
      </div>
    </div>
  );
};

const PipelineStages: React.FC = () => {
  const stages = [
    {
      icon: <FileUp size={18} />,
      title: "Data Injection",
      description: "Upload and parse data from various formats",
      status: "completed" as const
    },
    {
      icon: <FilterX size={18} />,
      title: "Data Cleaning",
      description: "Handle missing values, duplicates, and outliers",
      status: "completed" as const
    },
    {
      icon: <CheckCircle2 size={18} />,
      title: "Data Validation",
      description: "Ensure data meets schema requirements",
      status: "in-progress" as const
    },
    {
      icon: <Activity size={18} />,
      title: "Anomaly Detection",
      description: "Identify unusual patterns in data",
      status: "pending" as const
    },
    {
      icon: <BarChart3 size={18} />,
      title: "Analytics",
      description: "Generate insights and predictions",
      status: "pending" as const
    },
    {
      icon: <Zap size={18} />,
      title: "Business Rules",
      description: "Apply and suggest business logic",
      status: "pending" as const,
      isLast: true
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      {stages.map((stage, idx) => (
        <Stage 
          key={idx} 
          icon={stage.icon} 
          title={stage.title} 
          description={stage.description} 
          status={stage.status} 
          isLast={stage.isLast}
        />
      ))}
    </div>
  );
};

export default PipelineStages;
