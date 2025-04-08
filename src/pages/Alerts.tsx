
import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BellRing, Clock, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

const Alerts = () => {
  // Sample alert data
  const alerts = [
    {
      id: 1,
      title: "CPU Usage Spike",
      description: "Server CPU usage exceeded 90% threshold",
      severity: "high",
      timestamp: "2025-04-08T10:23:15Z",
    },
    {
      id: 2,
      title: "Memory Warning",
      description: "Low memory available on data processing node",
      severity: "medium",
      timestamp: "2025-04-08T09:45:22Z",
    },
    {
      id: 3,
      title: "Disk Space Alert",
      description: "Storage capacity reached 85% on primary database",
      severity: "medium",
      timestamp: "2025-04-08T08:12:05Z",
    },
    {
      id: 4,
      title: "API Response Time",
      description: "External API response time exceeding SLA",
      severity: "low",
      timestamp: "2025-04-08T07:30:19Z",
    },
    {
      id: 5,
      title: "Failed Authentication Attempts",
      description: "Multiple failed login attempts detected",
      severity: "high",
      timestamp: "2025-04-08T06:55:41Z",
    },
  ];

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "high":
        return <Badge variant="destructive" className="ml-2">Critical</Badge>;
      case "medium":
        return <Badge variant="default" className="bg-orange-500 ml-2">Warning</Badge>;
      case "low":
        return <Badge variant="outline" className="ml-2">Info</Badge>;
      default:
        return null;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <div className="container mx-auto p-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Alert Management</h1>
        <Badge className="bg-blue-600">
          {alerts.length} Active Alerts
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="col-span-1 lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="mr-2 h-5 w-5 text-red-500" />
              Recent Alerts
            </CardTitle>
            <CardDescription>View and manage system alerts</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px] pr-4">
              {alerts.map((alert) => (
                <div key={alert.id} className="mb-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <h3 className="font-medium">{alert.title}</h3>
                      {getSeverityBadge(alert.severity)}
                    </div>
                    <div className="flex items-center text-sm text-muted-foreground">
                      <Clock className="mr-1 h-4 w-4" />
                      {formatDate(alert.timestamp)}
                    </div>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{alert.description}</p>
                  <Separator className="mt-3" />
                </div>
              ))}
            </ScrollArea>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BellRing className="mr-2 h-5 w-5" />
              Alert Summary
            </CardTitle>
            <CardDescription>Current alert status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Critical Alerts</span>
                <Badge variant="destructive">{alerts.filter(a => a.severity === "high").length}</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Warning Alerts</span>
                <Badge className="bg-orange-500">{alerts.filter(a => a.severity === "medium").length}</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Info Alerts</span>
                <Badge variant="outline">{alerts.filter(a => a.severity === "low").length}</Badge>
              </div>
              <Separator />
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Total Alerts</span>
                <Badge className="bg-blue-600">{alerts.length}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Alerts;
