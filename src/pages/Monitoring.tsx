
import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ResponsiveContainer, LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";
import { Activity, Server, Database, Cpu, HardDrive, Network } from "lucide-react";

const Monitoring = () => {
  // Sample monitoring data
  const performanceData = [
    { time: "00:00", cpu: 42, memory: 65, disk: 25, network: 18 },
    { time: "03:00", cpu: 35, memory: 68, disk: 27, network: 15 },
    { time: "06:00", cpu: 55, memory: 72, disk: 28, network: 22 },
    { time: "09:00", cpu: 75, memory: 85, disk: 30, network: 45 },
    { time: "12:00", cpu: 85, memory: 90, disk: 32, network: 50 },
    { time: "15:00", cpu: 70, memory: 85, disk: 34, network: 35 },
    { time: "18:00", cpu: 65, memory: 80, disk: 36, network: 30 },
    { time: "21:00", cpu: 50, memory: 70, disk: 38, network: 25 },
  ];

  return (
    <div className="container mx-auto p-4">
      <div className="flex items-center mb-6">
        <Activity className="mr-2 h-6 w-6 text-blue-600" />
        <h1 className="text-2xl font-bold">System Monitoring</h1>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
          <TabsTrigger value="network">Network</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center">
                  <Cpu className="h-4 w-4 mr-2 text-blue-500" />
                  CPU Usage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{performanceData[performanceData.length - 1].cpu}%</div>
                <p className="text-xs text-muted-foreground">+2% from last hour</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center">
                  <Server className="h-4 w-4 mr-2 text-green-500" />
                  Memory Usage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{performanceData[performanceData.length - 1].memory}%</div>
                <p className="text-xs text-muted-foreground">-5% from last hour</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center">
                  <HardDrive className="h-4 w-4 mr-2 text-amber-500" />
                  Disk Usage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{performanceData[performanceData.length - 1].disk}%</div>
                <p className="text-xs text-muted-foreground">+2% from yesterday</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center">
                  <Network className="h-4 w-4 mr-2 text-purple-500" />
                  Network Traffic
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{performanceData[performanceData.length - 1].network} MB/s</div>
                <p className="text-xs text-muted-foreground">-10% from peak</p>
              </CardContent>
            </Card>
          </div>
          <Card className="col-span-4">
            <CardHeader>
              <CardTitle>System Performance</CardTitle>
              <CardDescription>24 hour overview of system resources</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={performanceData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="cpu" stroke="#3b82f6" activeDot={{ r: 8 }} name="CPU" />
                  <Line type="monotone" dataKey="memory" stroke="#10b981" name="Memory" />
                  <Line type="monotone" dataKey="disk" stroke="#f59e0b" name="Disk I/O" />
                  <Line type="monotone" dataKey="network" stroke="#8b5cf6" name="Network" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="resources" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Cpu className="mr-2 h-5 w-5 text-blue-500" />
                  CPU Utilization
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="cpu" stroke="#3b82f6" fill="#93c5fd" name="CPU %" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Server className="mr-2 h-5 w-5 text-green-500" />
                  Memory Usage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="memory" stroke="#10b981" fill="#6ee7b7" name="Memory %" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="network" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Network className="mr-2 h-5 w-5 text-purple-500" />
                Network Traffic
              </CardTitle>
              <CardDescription>Incoming and outgoing network activity</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="network" fill="#8b5cf6" name="Network Traffic (MB/s)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Monitoring;
