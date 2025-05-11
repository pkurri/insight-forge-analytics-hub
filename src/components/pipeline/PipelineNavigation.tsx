import React from 'react';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PipelineNavigationProps {
  currentStep: number;
  completedSteps: number[];
  totalSteps: number;
  onNavigate: (step: number) => void;
  isLoading: boolean;
  onContinue?: () => Promise<void>;
}

/**
 * PipelineNavigation Component
 * 
 * Handles navigation between pipeline steps without triggering unnecessary API calls
 */
const PipelineNavigation: React.FC<PipelineNavigationProps> = ({
  currentStep,
  completedSteps,
  totalSteps,
  onNavigate,
  isLoading,
  onContinue
}) => {
  // Handle going back to previous step
  const handleBack = () => {
    if (currentStep > 0) {
      onNavigate(currentStep - 1);
    }
  };

  // Handle going to next step
  const handleNext = () => {
    // If the next step is already completed, just navigate to it
    if (completedSteps.includes(currentStep + 1)) {
      onNavigate(currentStep + 1);
    } else if (currentStep < totalSteps - 1) {
      // If there's a continue handler (for API calls), use it
      if (onContinue) {
        onContinue();
      } else {
        // Otherwise just navigate to the next step
        onNavigate(currentStep + 1);
      }
    }
  };

  return (
    <div className="flex justify-between mt-6">
      <Button
        variant="outline"
        onClick={handleBack}
        disabled={currentStep === 0 || isLoading}
        className="flex items-center gap-2"
      >
        <ChevronLeft className="h-4 w-4" />
        Back
      </Button>
      
      <Button
        onClick={handleNext}
        disabled={currentStep === totalSteps - 1 || isLoading}
        className="flex items-center gap-2"
      >
        {isLoading ? 'Processing...' : 'Continue'}
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  );
};

export default PipelineNavigation;
