
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Anomaly } from "@/api/services/analytics/conversationAnalyticsService";
import { format } from "date-fns";

interface AnomalyTimelineProps {
  anomalies: Anomaly[];
}

export default function AnomalyTimeline({ anomalies }: AnomalyTimelineProps) {
  // Ensure anomalies is an array
  const safeAnomalies = Array.isArray(anomalies) ? anomalies : [];
  
  if (safeAnomalies.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Anomaly Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-40">
            <p className="text-muted-foreground">No anomalies detected</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Anomaly Timeline</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {safeAnomalies.map((anomaly, index) => (
            <div key={index} className="flex items-start gap-3">
              <div className="min-w-fit text-sm text-muted-foreground">
                {anomaly.timestamp && 
                  format(new Date(anomaly.timestamp), "MMM d, h:mm a")}
              </div>
              <div className="flex-1">
                <div className="p-3 bg-red-50 rounded-md border border-red-100">
                  <p className="text-red-800">{anomaly.reason}</p>
                  {anomaly.dataset_id && (
                    <p className="text-xs text-red-600 mt-1">
                      Dataset ID: {anomaly.dataset_id}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
