
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

interface PipelineStagesProps {
  currentStage?: number;
  stages?: Array<{
    title: string;
    description: string;
    status: 'completed' | 'in-progress' | 'pending' | 'error';
    icon?: React.ReactNode;
  }>;
}

const PipelineStages: React.FC<PipelineStagesProps> = ({ currentStage = 0, stages: customStages }) => {
  const defaultStages = [
    {
      icon: <FileUp size={18} />,
      title: "Upload",
      description: "Upload data from various sources",
      status: "pending" as const
    },
    {
      icon: <CheckCircle2 size={18} />,
      title: "Validate",
      description: "Ensure data meets schema requirements",
      status: "pending" as const
    },
    {
      icon: <Zap size={18} />,
      title: "Business Rules",
      description: "Apply business logic and validation",
      status: "pending" as const
    },
    {
      icon: <FilterX size={18} />,
      title: "Transform",
      description: "Clean and transform data",
      status: "pending" as const
    },
    {
      icon: <BarChart3 size={18} />,
      title: "Enrich",
      description: "Add derived fields and insights",
      status: "pending" as const
    },
    {
      icon: <Activity size={18} />,
      title: "Load",
      description: "Save processed data to destination",
      status: "pending" as const,
      isLast: true
    }
  ];
  
  const stages = customStages || defaultStages;
  
  // Update status based on current stage
  const stagesWithStatus = stages.map((stage, index) => ({
    ...stage,
    status: index < currentStage ? 'completed' : 
           index === currentStage ? 'in-progress' : 'pending'
  }));

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      {stagesWithStatus.map((stage, idx) => (
        <Stage 
          key={idx} 
          icon={stage.icon} 
          title={stage.title} 
          description={stage.description} 
          status={stage.status} 
          isLast={idx === stagesWithStatus.length - 1}
        />
      ))}
    </div>
  );
};

export default PipelineStages;
