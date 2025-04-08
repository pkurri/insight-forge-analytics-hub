
import React from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const PipelineAnalytics: React.FC = () => {
  // Sample data for the charts
  const timeSeriesData = [
    { date: '2025-04-01', ingestion: 1200, cleaning: 1000, validation: 800 },
    { date: '2025-04-02', ingestion: 1500, cleaning: 1300, validation: 1100 },
    { date: '2025-04-03', ingestion: 1000, cleaning: 850, validation: 800 },
    { date: '2025-04-04', ingestion: 1800, cleaning: 1600, validation: 1400 },
    { date: '2025-04-05', ingestion: 2000, cleaning: 1800, validation: 1600 },
    { date: '2025-04-06', ingestion: 1700, cleaning: 1500, validation: 1300 },
    { date: '2025-04-07', ingestion: 1900, cleaning: 1700, validation: 1500 },
    { date: '2025-04-08', ingestion: 2200, cleaning: 1900, validation: 1700 },
  ];

  const dataQualityData = [
    { name: 'Clean', value: 85 },
    { name: 'Missing Values', value: 8 },
    { name: 'Errors', value: 4 },
    { name: 'Anomalies', value: 3 },
  ];

  const processingTimeData = [
    { stage: 'Ingestion', time: 12 },
    { stage: 'Cleaning', time: 25 },
    { stage: 'Validation', time: 18 },
    { stage: 'Anomaly Detection', time: 30 },
    { stage: 'Analytics', time: 22 },
  ];

  const COLORS = ['#4ade80', '#facc15', '#f87171', '#60a5fa'];

  return (
    <Tabs defaultValue="overview">
      <TabsList className="mb-4">
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="performance">Performance</TabsTrigger>
        <TabsTrigger value="quality">Data Quality</TabsTrigger>
      </TabsList>
      
      <TabsContent value="overview" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Pipeline Processing Volumes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={timeSeriesData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="ingestion" stroke="#8884d8" name="Data Ingestion" />
                  <Line type="monotone" dataKey="cleaning" stroke="#82ca9d" name="Data Cleaning" />
                  <Line type="monotone" dataKey="validation" stroke="#ffc658" name="Data Validation" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
      
      <TabsContent value="performance" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Average Processing Time by Stage (seconds)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={processingTimeData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="stage" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="time" fill="#8884d8" name="Processing Time (s)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
      
      <TabsContent value="quality" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Data Quality Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80 flex items-center justify-center">
              <ResponsiveContainer width="70%" height="100%">
                <PieChart>
                  <Pie
                    data={dataQualityData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    fill="#8884d8"
                    paddingAngle={5}
                    dataKey="value"
                    label={({name, percent}) => `${name} ${(percent * 100).toFixed(1)}%`}
                  >
                    {dataQualityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
};

export default PipelineAnalytics;
