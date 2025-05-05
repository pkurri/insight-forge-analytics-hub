
import React from "react";
import { cn } from "@/lib/utils";

interface QualityScoreProps {
  value: number;
  maxValue?: number;
  showLabel?: boolean;
  className?: string;
  labelClassName?: string;
  showPercentage?: boolean;
}

export default function QualityScore({ 
  value, 
  maxValue = 10, 
  showLabel = true,
  showPercentage = false,
  className,
  labelClassName
}: QualityScoreProps) {
  const percentage = (value / maxValue) * 100;
  const roundedPercentage = Math.round(percentage);
  
  const getColorClass = () => {
    if (percentage >= 80) return "bg-green-500";
    if (percentage >= 60) return "bg-yellow-500";
    if (percentage >= 40) return "bg-orange-500";
    return "bg-red-500";
  };
  
  const getTextClass = () => {
    if (percentage >= 80) return "text-green-700";
    if (percentage >= 60) return "text-yellow-700";
    if (percentage >= 40) return "text-orange-700";
    return "text-red-700";
  };

  return (
    <div className={cn("flex flex-col gap-1", className)}>
      {showLabel && (
        <div className="flex items-center justify-between">
          <span className={cn("text-sm font-medium", getTextClass(), labelClassName)}>
            Quality Score: {value}/{maxValue}
            {showPercentage && ` (${roundedPercentage}%)`}
          </span>
        </div>
      )}
      <div 
        className="h-2 w-full bg-gray-200 rounded-full overflow-hidden"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={roundedPercentage}
        aria-label={`Quality score: ${value} out of ${maxValue}`}
      >
        <div 
          className={cn("h-full rounded-full transition-all", getColorClass())} 
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
