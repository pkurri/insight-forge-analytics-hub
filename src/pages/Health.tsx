
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { HeartPulse, Activity, Timer, CheckCircle2, XCircle } from "lucide-react";

type ServiceStatus = "operational" | "degraded" | "outage";

interface ServiceHealth {
  name: string;
  status: ServiceStatus;
  uptime: number;
  responseTime: number;
  lastChecked: string;
}

const Health = () => {
  // Sample health check data
  const services: ServiceHealth[] = [
    {
      name: "API Gateway",
      status: "operational",
      uptime: 99.998,
      responseTime: 42,
      lastChecked: "2025-04-08T18:30:00Z"
    },
    {
      name: "Authentication Service",
      status: "operational",
      uptime: 99.995,
      responseTime: 56,
      lastChecked: "2025-04-08T18:30:00Z"
    },
    {
      name: "Database Cluster",
      status: "operational",
      uptime: 99.999,
      responseTime: 12,
      lastChecked: "2025-04-08T18:30:00Z"
    },
    {
      name: "Storage Service",
      status: "degraded",
      uptime: 99.876,
      responseTime: 230,
      lastChecked: "2025-04-08T18:30:00Z"
    },
    {
      name: "Analytics Engine",
      status: "operational",
      uptime: 99.989,
      responseTime: 78,
      lastChecked: "2025-04-08T18:30:00Z"
    },
    {
      name: "Search Index",
      status: "operational",
      uptime: 99.991,
      responseTime: 64,
      lastChecked: "2025-04-08T18:30:00Z"
    },
    {
      name: "Notification Service",
      status: "outage",
      uptime: 98.723,
      responseTime: 500,
      lastChecked: "2025-04-08T18:30:00Z"
    },
    {
      name: "File Processing",
      status: "operational",
      uptime: 99.987,
      responseTime: 112,
      lastChecked: "2025-04-08T18:30:00Z"
    }
  ];

  // Calculate overall system health
  const operationalCount = services.filter(s => s.status === "operational").length;
  const degradedCount = services.filter(s => s.status === "degraded").length;
  const outageCount = services.filter(s => s.status === "outage").length;
  
  const overallStatus = outageCount > 0 ? "outage" 
    : degradedCount > 0 ? "degraded" 
    : "operational";

  const getStatusBadge = (status: ServiceStatus) => {
    switch (status) {
      case "operational":
        return <Badge className="bg-green-500">Operational</Badge>;
      case "degraded":
        return <Badge className="bg-orange-500">Degraded</Badge>;
      case "outage":
        return <Badge variant="destructive">Outage</Badge>;
      default:
        return null;
    }
  };

  const getStatusIcon = (status: ServiceStatus) => {
    switch (status) {
      case "operational":
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case "degraded":
        return <Activity className="h-5 w-5 text-orange-500" />;
      case "outage":
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getResponseTimeColor = (time: number) => {
    if (time < 100) return "text-green-500";
    if (time < 300) return "text-orange-500";
    return "text-red-500";
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <div className="container mx-auto p-4">
      <div className="flex items-center mb-6">
        <HeartPulse className="mr-2 h-6 w-6 text-red-500" />
        <h1 className="text-2xl font-bold">System Health</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center">
            {getStatusIcon(overallStatus)}
            <div className="ml-2">
              {getStatusBadge(overallStatus)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Uptime</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(services.reduce((acc, service) => acc + service.uptime, 0) / services.length).toFixed(3)}%
            </div>
            <p className="text-xs text-muted-foreground">Last 30 days</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round(services.reduce((acc, service) => acc + service.responseTime, 0) / services.length)} ms
            </div>
            <p className="text-xs text-muted-foreground">Across all services</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Services Health</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {services.map((service) => (
              <div key={service.name} className="grid grid-cols-12 gap-4 items-center">
                <div className="col-span-12 sm:col-span-3">
                  <div className="flex items-center">
                    {getStatusIcon(service.status)}
                    <span className="ml-2 font-medium">{service.name}</span>
                  </div>
                </div>
                <div className="col-span-4 sm:col-span-2">
                  {getStatusBadge(service.status)}
                </div>
                <div className="col-span-8 sm:col-span-3">
                  <div className="flex items-center">
                    <Progress value={service.uptime} className="h-2" />
                    <span className="ml-2 text-xs">{service.uptime.toFixed(2)}%</span>
                  </div>
                </div>
                <div className="col-span-6 sm:col-span-2 flex items-center">
                  <Timer className="h-4 w-4 mr-1" />
                  <span className={`text-sm ${getResponseTimeColor(service.responseTime)}`}>
                    {service.responseTime} ms
                  </span>
                </div>
                <div className="col-span-6 sm:col-span-2 text-xs text-muted-foreground">
                  {formatDate(service.lastChecked)}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Health;
