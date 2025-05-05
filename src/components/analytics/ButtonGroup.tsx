
import React from "react";
import { cn } from "@/lib/utils";

interface ButtonGroupProps {
  children: React.ReactNode;
  className?: string;
}

export default function ButtonGroup({ children, className }: ButtonGroupProps) {
  return (
    <div className={cn("flex items-center gap-3 mb-4", className)}>
      {children}
    </div>
  );
}
