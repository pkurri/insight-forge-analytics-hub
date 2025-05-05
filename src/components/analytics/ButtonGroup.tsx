
import React from "react";
import { cn } from "@/lib/utils";

interface ButtonGroupProps {
  children: React.ReactNode;
  className?: string;
  orientation?: "horizontal" | "vertical";
  spacing?: "tight" | "normal" | "loose";
}

export default function ButtonGroup({ 
  children, 
  className,
  orientation = "horizontal",
  spacing = "normal" 
}: ButtonGroupProps) {
  const spacingClass = {
    tight: "gap-1",
    normal: "gap-3",
    loose: "gap-4"
  };

  const orientationClass = {
    horizontal: "flex items-center",
    vertical: "flex flex-col items-start"
  };
  
  return (
    <div className={cn(
      orientationClass[orientation], 
      spacingClass[spacing], 
      "mb-4", 
      className
    )}>
      {children}
    </div>
  );
}
