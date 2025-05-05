
import React from "react";
import { cn } from "@/lib/utils";

interface QualityScoreProps {
  value: number;
  maxValue?: number;
  showLabel?: boolean;
  className?: string;
}

export default function QualityScore({ 
  value, 
  maxValue = 10, 
  showLabel = true, 
  className 
}: QualityScoreProps) {
  const percentage = (value / maxValue) * 100;
  
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
      <div className="flex items-center justify-between">
        {showLabel && (
          <span className={cn("text-sm font-medium", getTextClass())}>
            Quality Score: {value}/{maxValue}
          </span>
        )}
      </div>
      <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
        <div 
          className={cn("h-full rounded-full transition-all", getColorClass())} 
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
