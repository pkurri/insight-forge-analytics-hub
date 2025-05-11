import React from 'react';
import { ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';

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
      <button
        className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 flex items-center"
        onClick={handleBack}
        disabled={currentStep === 0 || isLoading}
      >
        <ChevronLeft className="mr-2 h-4 w-4" />
        Back
      </button>
      
      <button
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center"
        onClick={handleNext}
        disabled={currentStep === totalSteps - 1 || isLoading}
      >
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Processing...
          </>
        ) : (
          <>
            <ChevronRight className="mr-2 h-4 w-4" />
            Continue
          </>
        )}
      </button>
    </div>
  );
};

export default PipelineNavigation;
