import React from 'react';
import { FileUp, FilterX, CheckCircle2, Activity, BarChart3, Zap, Play } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/api/api';
import { PipelineStep } from '@/api/services/pipeline';

interface StageProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  status: 'completed' | 'in-progress' | 'pending' | 'error';
  isLast?: boolean;
  stepId?: number;
  onRunStep?: (stepId: number) => Promise<void>;
  isRunning?: boolean;
}

const Stage: React.FC<StageProps> = ({ 
  icon, 
  title, 
  description, 
  status, 
  isLast = false,
  stepId,
  onRunStep,
  isRunning = false
}) => {
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
      <div className="ml-4 mt-1 flex-1">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="font-medium">{title}</h3>
            <p className="text-sm text-gray-500">{description}</p>
          </div>
          {stepId && onRunStep && status !== 'completed' && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onRunStep(stepId)}
              disabled={isRunning || status === 'in-progress'}
              className="ml-4"
            >
              {isRunning ? (
                <div className="flex items-center">
                  <div className="animate-spin mr-2">⟳</div>
                  Running...
                </div>
              ) : (
                <div className="flex items-center">
                  <Play size={14} className="mr-2" />
                  Run
                </div>
              )}
            </Button>
          )}
        </div>
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
    stepId?: number;
  }>;
  datasetId?: number;
  onStageUpdate?: () => void;
}

const PipelineStages: React.FC<PipelineStagesProps> = ({ 
  currentStage = 0, 
  stages: customStages,
  datasetId,
  onStageUpdate 
}) => {
  const { toast } = useToast();
  const [runningSteps, setRunningSteps] = React.useState<Set<number>>(new Set());

  const handleRunStep = async (stepId: number) => {
    try {
      setRunningSteps(prev => new Set(prev).add(stepId));
      
      const response = await api.pipelineService.runPipelineStep(stepId);
      
      if (response.success) {
        toast({
          title: "Step started",
          description: "The pipeline step has been initiated successfully.",
        });
        onStageUpdate?.();
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
          stepId={stage.stepId}
          onRunStep={stage.stepId ? handleRunStep : undefined}
          isRunning={stage.stepId ? runningSteps.has(stage.stepId) : false}
        />
      ))}
    </div>
  );
};

export default PipelineStages;
