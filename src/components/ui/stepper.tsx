
import React, { useState } from 'react';
import { cn } from '@/utils/utils';
import { CircleCheckBig, CircleDashed, Check } from 'lucide-react';

interface StepProps {
  children: React.ReactNode;
  description?: string;
  icon?: React.ReactNode;
  isActive?: boolean;
  isCompleted?: boolean;
  onClick?: () => void;
  clickable?: boolean;
}

interface StepperProps {
  currentStep: number;
  orientation?: 'horizontal' | 'vertical';
  children: React.ReactNode;
  onStepClick?: (stepIndex: number) => void;
  clickableSteps?: boolean;
  error?: string;
}

export const Step = ({ 
  children, 
  description, 
  icon, 
  isActive, 
  isCompleted,
  onClick,
  clickable = false
}: StepProps) => {
  return (
    <div 
      className={cn(
        "flex flex-col items-center",
        clickable && !isActive && "cursor-pointer hover:opacity-80"
      )}
      onClick={clickable && onClick ? onClick : undefined}
    >
      {children}
      {description && <span className="text-xs mt-1 text-muted-foreground">{description}</span>}
    </div>
  );
};

export const Stepper = ({ 
  currentStep, 
  orientation = 'horizontal', 
  children, 
  onStepClick,
  clickableSteps = false,
  error
}: StepperProps) => {
  const steps = React.Children.toArray(children);

  const handleStepClick = (index: number) => {
    if (onStepClick && clickableSteps && (index < currentStep || index === currentStep + 1)) {
      onStepClick(index);
    }
  };

  const renderHorizontalStepper = () => {
    return (
      <div className="flex justify-between items-center w-full">
        {steps.map((step, index) => {
          const isActive = index === currentStep;
          const isCompleted = index < currentStep;
          const isClickable = clickableSteps && (index < currentStep || index === currentStep + 1);

          return (
            <React.Fragment key={index}>
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center border-2 text-xs font-semibold transition-all',
                    isActive
                      ? 'border-primary bg-primary text-primary-foreground'
                      : isCompleted
                      ? 'border-primary text-primary-foreground bg-primary'
                      : 'border-muted-foreground text-muted-foreground',
                    isClickable && 'cursor-pointer hover:opacity-80',
                    error && isActive && 'border-destructive bg-destructive text-destructive-foreground'
                  )}
                  onClick={() => handleStepClick(index)}
                >
                  {isCompleted && React.isValidElement(
                    (step as React.ReactElement<StepProps>).props.icon
                  ) ? (
                    (step as React.ReactElement<StepProps>).props.icon
                  ) : (
                    isCompleted ? <Check className="h-4 w-4" /> : index + 1
                  )}
                </div>
                <div className={cn(
                  'mt-2 text-center',
                  isActive ? 'text-primary font-medium' : 
                  isCompleted ? 'text-primary' : 'text-muted-foreground',
                  error && isActive && 'text-destructive'
                )}>
                  {React.cloneElement(step as React.ReactElement, {
                    isActive,
                    isCompleted,
                    onClick: () => handleStepClick(index),
                    clickable: isClickable
                  })}
                </div>
              </div>
              
              {/* Connector line between steps */}
              {index < steps.length - 1 && (
                <div className={cn(
                  'flex-1 h-0.5 mx-2',
                  index < currentStep ? 'bg-primary' : 'bg-muted-foreground/30'
                )} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    );
  };

  const renderVerticalStepper = () => {
    return (
      <div className="flex flex-col space-y-8 w-full">
        {steps.map((step, index) => {
          const isActive = index === currentStep;
          const isCompleted = index < currentStep;
          const isClickable = clickableSteps && (index < currentStep || index === currentStep + 1);

          return (
            <div key={index} className="flex items-start">
              <div className="flex flex-col items-center mr-4">
                <div
                  className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center border-2 text-xs font-semibold transition-all',
                    isActive
                      ? 'border-primary bg-primary text-primary-foreground'
                      : isCompleted
                      ? 'border-primary text-primary-foreground bg-primary'
                      : 'border-muted-foreground text-muted-foreground',
                    isClickable && 'cursor-pointer hover:opacity-80',
                    error && isActive && 'border-destructive bg-destructive text-destructive-foreground'
                  )}
                  onClick={() => handleStepClick(index)}
                >
                  {isCompleted && React.isValidElement(
                    (step as React.ReactElement<StepProps>).props.icon
                  ) ? (
                    (step as React.ReactElement<StepProps>).props.icon
                  ) : (
                    isCompleted ? <Check className="h-4 w-4" /> : index + 1
                  )}
                </div>
                
                {/* Connector line between steps */}
                {index < steps.length - 1 && (
                  <div className={cn(
                    'w-0.5 flex-1 my-2',
                    index < currentStep ? 'bg-primary' : 'bg-muted-foreground/30'
                  )} />
                )}
              </div>
              
              <div className={cn(
                'pt-1',
                isActive ? 'text-primary font-medium' : 
                isCompleted ? 'text-primary' : 'text-muted-foreground',
                error && isActive && 'text-destructive'
              )}>
                {React.cloneElement(step as React.ReactElement, {
                  isActive,
                  isCompleted,
                  onClick: () => handleStepClick(index),
                  clickable: isClickable
                })}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  // Display error message if provided
  const errorMessage = error ? (
    <div className="mt-2 text-sm text-destructive">{error}</div>
  ) : null;

  return (
    <div className={cn('w-full', orientation === 'vertical' ? 'flex' : '')}>
      {orientation === 'horizontal' ? renderHorizontalStepper() : renderVerticalStepper()}
      {errorMessage}
    </div>
  );
};
