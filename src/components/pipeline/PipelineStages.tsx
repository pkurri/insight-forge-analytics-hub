import React from 'react';
import { FileUp, CheckCircle2, Activity, Play, Info, Sparkles, HardDrive, Filter, ArrowRight, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

type StageStatus = 'completed' | 'in-progress' | 'pending' | 'error';

interface StageProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  status: StageStatus;
  stepId?: number;
  onRunStep?: (stepId: number) => Promise<void>;
  isRunning?: boolean;
  onClick?: () => void;
  isActive?: boolean;
  details?: string;
}

const Stage: React.FC<StageProps> = ({ 
  icon, 
  title, 
  description, 
  status, 
  stepId,
  onRunStep,
  isRunning = false,
  onClick,
  isActive = false,
  details
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-600 border-green-500';
      case 'in-progress': return 'bg-blue-100 text-blue-600 border-blue-500';
      case 'error': return 'bg-red-100 text-red-600 border-red-500';
      default: return 'bg-gray-100 text-gray-500 border-gray-300';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'in-progress': return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
      case 'error': return <Activity className="h-5 w-5 text-red-500" />;
      default: return icon;
    }
  };

  return (
    <div 
      onClick={onClick}
      className={cn(
        "flex items-start p-4 rounded-lg border transition-all", 
        onClick && "cursor-pointer hover:shadow-md",
        isActive ? "bg-accent shadow-sm border-primary" : 
        status === 'completed' ? "bg-muted/30" : 
        status === 'error' ? "bg-red-50" : 
        "bg-background"
      )}
    >
      <div className={cn("flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-full", getStatusColor())}>
        {getStatusIcon()}
      </div>
      <div className="ml-4 flex-1">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-medium">{title}</h3>
              {isActive && <Badge variant="outline" className="ml-1">Current</Badge>}
              {status === 'completed' && <Badge className="ml-1 bg-green-500">Completed</Badge>}
              {status === 'in-progress' && <Badge variant="outline" className="ml-1 animate-pulse">Processing</Badge>}
              {status === 'error' && <Badge variant="destructive" className="ml-1">Failed</Badge>}
            </div>
            <p className="text-sm text-muted-foreground mt-1">{description}</p>
            {details && isActive && <p className="text-xs text-muted-foreground mt-2 bg-muted/50 p-2 rounded">{details}</p>}
          </div>
          {stepId && onRunStep && status !== 'completed' && (
            <Button
              variant={status === 'error' ? "destructive" : "outline"}
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onRunStep(stepId);
              }}
              disabled={isRunning || status === 'in-progress'}
              className="ml-4"
            >
              {isRunning ? (
                <div className="flex items-center">
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Running...
                </div>
              ) : (
                <div className="flex items-center">
                  {status === 'error' ? (
                    <>
                      <ArrowRight size={14} className="mr-2" />
                      Retry
                    </>
                  ) : (
                    <>
                      <Play size={14} className="mr-2" />
                      Run
                    </>
                  )}
                </div>
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

interface StageDefinition {
  icon: React.ReactNode;
  title: string;
  description: string;
  status: StageStatus;
  stepId?: number;
  isLast?: boolean;
  details?: string;
}

interface PipelineStagesProps {
  currentStage?: number;
  stages?: StageDefinition[];
  onStageUpdate?: () => void;
}

const PipelineStages: React.FC<PipelineStagesProps> = ({ 
  currentStage = 0, 
  stages: customStages,
  onStageUpdate 
}) => {
  const { toast } = useToast();
  const [runningSteps, setRunningSteps] = React.useState<Set<number>>(new Set());

  const handleRunStep = async (stepId: number) => {
    try {
      setRunningSteps(prev => new Set(prev).add(stepId));
      
      // Mock API call for now
      await new Promise(resolve => setTimeout(resolve, 1500));
      const response = { success: true };
      
      if (response.success) {
        toast({
          title: "Step started",
          description: "The pipeline step has been initiated successfully.",
        });
        onStageUpdate?.();
      } else {
        throw new Error("Failed to start pipeline step");
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

  const defaultStages: StageDefinition[] = [
    {
      icon: <FileUp size={18} />,
      title: "Upload",
      description: "Upload data from various sources",
      status: "pending",
      details: "Upload your data from a local file, API, or database connection"
    },
    {
      icon: <CheckCircle2 size={18} />,
      title: "Validate",
      description: "Ensure data meets schema requirements",
      status: "pending",
      details: "Verify data schema, types, and basic integrity checks"
    },
    {
      icon: <Filter size={18} />,
      title: "Business Rules",
      description: "Apply business logic and validation",
      status: "pending",
      details: "Apply custom business rules and data quality constraints"
    },
    {
      icon: <Sparkles size={18} />,
      title: "Transform",
      description: "Clean and transform data",
      status: "pending",
      details: "Transform data structure and format for analysis"
    },
    {
      icon: <Info size={18} />,
      title: "Enrich",
      description: "Add derived fields and insights",
      status: "pending",
      details: "Add derived fields, external data, and enrich your dataset"
    },
    {
      icon: <HardDrive size={18} />,
      title: "Load",
      description: "Save processed data to destination",
      status: "pending",
      isLast: true,
      details: "Load processed data to your target destination"
    }
  ];
  
  const stages = customStages || defaultStages;
  
  // Update status based on current stage
  const stagesWithStatus = stages.map((stage, index) => ({
    ...stage,
    status: index < currentStage ? 'completed' as StageStatus : 
           index === currentStage ? 'in-progress' as StageStatus : 'pending' as StageStatus
  }));

  // Calculate overall progress percentage
  const calculateProgress = () => {
    const totalSteps = stagesWithStatus.length;
    const completedSteps = stagesWithStatus.filter(step => step.status === 'completed').length;
    return (completedSteps / totalSteps) * 100;
  };

  return (
    <Card className="shadow-sm border-muted">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-center">
          <CardTitle>Pipeline Progress</CardTitle>
          <Badge className={calculateProgress() === 100 ? "bg-green-500" : ""}>
            {Math.round(calculateProgress())}% Complete
          </Badge>
        </div>
        <Progress value={calculateProgress()} className="h-2 mt-2" />
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {stagesWithStatus.map((stage, idx) => (
            <Stage 
              key={idx} 
              icon={stage.icon} 
              title={stage.title} 
              description={stage.description} 
              status={stage.status} 
              stepId={stage.stepId}
              onRunStep={stage.stepId ? handleRunStep : undefined}
              isRunning={stage.stepId ? runningSteps.has(stage.stepId) : false}
              isActive={idx === currentStage}
              details={stage.details}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default PipelineStages;
