import React from 'react';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';

export type StepStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface StepProps {
  children: React.ReactNode;
  isActive: boolean;
  isCompleted: boolean;
  description: string;
  icon?: React.ReactNode;
  status: StepStatus;
  onClick?: () => void;
  disabled?: boolean;
}

/**
 * PipelineStep Component
 * 
 * Renders a single step in the pipeline process with appropriate styling based on status.
 */
const PipelineStep: React.FC<StepProps> = ({ 
  children, 
  isActive, 
  isCompleted, 
  description, 
  icon, 
  status, 
  onClick, 
  disabled = false 
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'processing':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
      default:
        return icon;
    }
  };

  return (
    <div 
      onClick={disabled ? undefined : onClick}
      className={`flex items-start gap-4 p-4 rounded-lg transition-all ${onClick && !disabled ? 'cursor-pointer hover:shadow-md' : ''} ${
        isActive ? 'bg-accent shadow-sm' : 
        isCompleted ? 'bg-muted/30' : 
        status === 'failed' ? 'bg-red-50' : 
        'bg-background'
      } border ${isActive ? 'border-primary' : 'border-border'} ${disabled ? 'opacity-60' : ''}`}
    >
      <div className={`flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-full transition-colors ${
        status === 'completed' ? 'bg-green-100 text-green-600' : 
        status === 'failed' ? 'bg-red-100 text-red-600' : 
        status === 'processing' ? 'bg-blue-100 text-blue-600' : 
        isActive ? 'bg-primary/10 text-primary' : 
        'bg-muted text-muted-foreground'
      }`}>
        {getStatusIcon()}
      </div>
      <div className="flex-grow">
        {children}
      </div>
    </div>
  );
};

export default PipelineStep;
