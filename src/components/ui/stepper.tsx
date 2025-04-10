
import React from 'react';
import { cn } from '@/lib/utils';
import { CircleCheckBig, CircleDashed } from 'lucide-react';

interface StepProps {
  children: React.ReactNode;
  description?: string;
  icon?: React.ReactNode;
  isActive?: boolean;
  isCompleted?: boolean;
}

interface StepperProps {
  currentStep: number;
  orientation?: 'horizontal' | 'vertical';
  children: React.ReactNode;
}

export const Step = ({ children, description, icon, isActive, isCompleted }: StepProps) => {
  return (
    <div className="flex flex-col items-center">
      {children}
      {description && <span className="text-xs mt-1 text-muted-foreground">{description}</span>}
    </div>
  );
};

export const Stepper = ({ currentStep, orientation = 'horizontal', children }: StepperProps) => {
  const steps = React.Children.toArray(children);

  const renderHorizontalStepper = () => {
    return (
      <div className="flex justify-between items-center w-full">
        {steps.map((step, index) => {
          const isActive = index === currentStep;
          const isCompleted = index < currentStep;

          return (
            <React.Fragment key={index}>
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center border-2 text-xs font-semibold',
                    isActive
                      ? 'border-primary bg-primary text-primary-foreground'
                      : isCompleted
                      ? 'border-primary text-primary-foreground bg-primary'
                      : 'border-muted-foreground text-muted-foreground'
                  )}
                >
                  {isCompleted && React.isValidElement(
                    (step as React.ReactElement<StepProps>).props.icon
                  ) ? (
                    (step as React.ReactElement<StepProps>).props.icon
                  ) : (
                    isCompleted ? <CircleCheckBig className="h-4 w-4" /> : index + 1
                  )}
                </div>
                <div className={cn(
                  'mt-2 text-center',
                  isActive ? 'text-primary font-medium' : 
                  isCompleted ? 'text-primary' : 'text-muted-foreground'
                )}>
                  {React.cloneElement(step as React.ReactElement, {
                    isActive,
                    isCompleted,
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

          return (
            <div key={index} className="flex items-start">
              <div className="flex flex-col items-center mr-4">
                <div
                  className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center border-2 text-xs font-semibold',
                    isActive
                      ? 'border-primary bg-primary text-primary-foreground'
                      : isCompleted
                      ? 'border-primary text-primary-foreground bg-primary'
                      : 'border-muted-foreground text-muted-foreground'
                  )}
                >
                  {isCompleted && React.isValidElement(
                    (step as React.ReactElement<StepProps>).props.icon
                  ) ? (
                    (step as React.ReactElement<StepProps>).props.icon
                  ) : (
                    isCompleted ? <CircleCheckBig className="h-4 w-4" /> : index + 1
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
                isCompleted ? 'text-primary' : 'text-muted-foreground'
              )}>
                {React.cloneElement(step as React.ReactElement, {
                  isActive,
                  isCompleted,
                })}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className={cn('w-full', orientation === 'vertical' ? 'flex' : '')}>
      {orientation === 'horizontal' ? renderHorizontalStepper() : renderVerticalStepper()}
    </div>
  );
};
