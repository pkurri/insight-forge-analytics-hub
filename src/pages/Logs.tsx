
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Terminal, Clock, Search, Filter } from "lucide-react";

type LogLevel = "error" | "warn" | "info" | "debug";
type LogEntry = {
  id: string;
  timestamp: string;
  level: LogLevel;
  service: string;
  message: string;
};

const Logs = () => {
  const [filter, setFilter] = useState<string>("");
  const [levelFilter, setLevelFilter] = useState<string>("all");

  // Sample logs data
  const logs: LogEntry[] = [
    {
      id: "log-001",
      timestamp: "2025-04-08T18:23:15.123Z",
      level: "error",
      service: "auth-service",
      message: "Failed to authenticate user: Invalid credentials provided"
    },
    {
      id: "log-002",
      timestamp: "2025-04-08T18:22:45.987Z",
      level: "info",
      service: "data-pipeline",
      message: "Processing batch #28945 completed successfully"
    },
    {
      id: "log-003",
      timestamp: "2025-04-08T18:21:30.546Z",
      level: "warn",
      service: "storage-service",
      message: "Disk usage approaching 80% threshold on node-3"
    },
    {
      id: "log-004",
      timestamp: "2025-04-08T18:20:12.765Z",
      level: "info",
      service: "api-gateway",
      message: "Rate limiting applied to client 192.168.1.105"
    },
    {
      id: "log-005",
      timestamp: "2025-04-08T18:19:55.321Z",
      level: "debug",
      service: "query-engine",
      message: "Query execution plan optimized: reduced complexity from O(n²) to O(n log n)"
    },
    {
      id: "log-006",
      timestamp: "2025-04-08T18:18:42.654Z",
      level: "error",
      service: "database",
      message: "Connection pool exhausted: max connections reached"
    },
    {
      id: "log-007",
      timestamp: "2025-04-08T18:17:30.123Z",
      level: "info",
      service: "scheduler",
      message: "Job #457832 scheduled for execution at 19:00:00"
    },
    {
      id: "log-008",
      timestamp: "2025-04-08T18:16:25.789Z",
      level: "warn",
      service: "cache-service",
      message: "Cache hit ratio dropped below 65%, consider increasing cache size"
    },
    {
      id: "log-009",
      timestamp: "2025-04-08T18:15:10.456Z",
      level: "debug",
      service: "notification-service",
      message: "Template rendering completed in 235ms"
    },
    {
      id: "log-010",
      timestamp: "2025-04-08T18:14:05.321Z",
      level: "info",
      service: "analytics",
      message: "Daily report generation started"
    }
  ];

  // Filter logs based on search input and level filter
  const filteredLogs = logs.filter(log => {
    const matchesSearch = filter === "" || 
      log.message.toLowerCase().includes(filter.toLowerCase()) || 
      log.service.toLowerCase().includes(filter.toLowerCase());
      
    const matchesLevel = levelFilter === "all" || log.level === levelFilter;
    
    return matchesSearch && matchesLevel;
  });
  
  const getLogLevelBadge = (level: LogLevel) => {
    switch (level) {
      case "error":
        return <Badge variant="destructive">ERROR</Badge>;
      case "warn":
        return <Badge className="bg-orange-500">WARN</Badge>;
      case "info":
        return <Badge className="bg-blue-500">INFO</Badge>;
      case "debug":
        return <Badge variant="outline" className="text-gray-500">DEBUG</Badge>;
      default:
        return null;
    }
  };
  
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  return (
    <div className="container mx-auto p-4">
      <div className="flex items-center mb-6">
        <Terminal className="mr-2 h-6 w-6 text-teal-600" />
        <h1 className="text-2xl font-bold">System Logs</h1>
      </div>
      
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex justify-between items-center">
            <span>Log Explorer</span>
            <span className="text-sm font-normal text-muted-foreground">
              Showing {filteredLogs.length} of {logs.length} entries
            </span>
          </CardTitle>
          <div className="flex flex-col sm:flex-row gap-4 pt-2">
            <div className="relative flex-1">
              <Search className="absolute left-2 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search logs..."
                className="pl-8"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={levelFilter} onValueChange={setLevelFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Filter by level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="error">Errors</SelectItem>
                  <SelectItem value="warn">Warnings</SelectItem>
                  <SelectItem value="info">Info</SelectItem>
                  <SelectItem value="debug">Debug</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline">Export Logs</Button>
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px]">
            <div className="space-y-2">
              {filteredLogs.map((log) => (
                <div key={log.id} className="bg-muted p-3 rounded-md">
                  <div className="flex flex-wrap gap-2 items-center mb-1">
                    <div className="flex items-center text-sm text-muted-foreground">
                      <Clock className="mr-1 h-3.5 w-3.5" />
                      {formatTimestamp(log.timestamp)}
                    </div>
                    {getLogLevelBadge(log.level)}
                    <Badge variant="outline" className="bg-background">
                      {log.service}
                    </Badge>
                  </div>
                  <div className="font-mono text-sm whitespace-pre-wrap">
                    {log.message}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
};

export default Logs;
