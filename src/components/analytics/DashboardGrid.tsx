
import React from "react";
import "./DashboardGrid.css";

interface DashboardGridProps {
  children: React.ReactNode;
}

export default function DashboardGrid({ children }: DashboardGridProps) {
  return (
    <div className="dashboard-grid">
      {children}
    </div>
  );
}
