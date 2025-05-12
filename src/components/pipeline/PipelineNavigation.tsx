import React from 'react';
import { ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface PipelineNavigationProps {
  currentStep: number;
  completedSteps: number[];
  totalSteps: number;
  onNavigate: (step: number) => void;
  isLoading: boolean;
  onContinue?: () => Promise<void>;
}

const PipelineNavigation: React.FC<PipelineNavigationProps> = ({
  currentStep,
  completedSteps,
  totalSteps,
  onNavigate,
  isLoading,
  onContinue
}) => {
  const handleBack = () => {
    if (currentStep > 0) {
      onNavigate(currentStep - 1);
    }
  };

  const handleNext = async () => {
    if (completedSteps.includes(currentStep + 1)) {
      onNavigate(currentStep + 1);
    } else if (currentStep < totalSteps - 1) {
      if (onContinue) {
        await onContinue();
      } else {
        onNavigate(currentStep + 1);
      }
    }
  };

  return (
    <div className="flex justify-between mt-6">
      <Button
        variant="outline"
        size="sm"
        className="flex items-center gap-2 transition-all"
        onClick={handleBack}
        disabled={currentStep === 0 || isLoading}
      >
        <ChevronLeft className="h-4 w-4" />
        Back
      </Button>
      
      <Button
        variant="default"
        size="sm"
        className="bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2 transition-all"
        onClick={handleNext}
        disabled={currentStep === totalSteps - 1 || isLoading}
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Processing...
          </>
        ) : (
          <>
            Continue
            <ChevronRight className="h-4 w-4" />
          </>
        )}
      </Button>
    </div>
  );
};

export default PipelineNavigation;
