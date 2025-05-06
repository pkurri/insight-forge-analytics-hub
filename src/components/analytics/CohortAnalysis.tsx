
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface CohortAnalysisProps {
  cohortData: Array<{
    cohort: string;
    retention: number[];
  }>;
  periods: string[];
}

export default function CohortAnalysis({ cohortData, periods }: CohortAnalysisProps) {
  // Ensure cohortData is an array
  const safeData = Array.isArray(cohortData) ? cohortData : [];
  const safePeriods = Array.isArray(periods) ? periods : [];
  
  if (safeData.length === 0 || safePeriods.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Cohort Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-40">
            <p className="text-muted-foreground">No cohort data available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cohort Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="p-2 text-left border">Cohort</th>
                {safePeriods.map((period, i) => (
                  <th key={i} className="p-2 text-center border">
                    {period}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {safeData.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  <td className="p-2 font-medium border">{row.cohort}</td>
                  {row.retention.map((value, colIndex) => (
                    <td 
                      key={colIndex} 
                      className="p-2 text-center border"
                      style={{
                        backgroundColor: `rgba(99, 102, 241, ${value / 100})`,
                      }}
                    >
                      {value}%
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
