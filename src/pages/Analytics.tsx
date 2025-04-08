
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { ChartContainer, ChartTooltip } from '@/components/ui/chart';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

const Analytics: React.FC = () => {
  // Sample data for anomaly detection
  const anomalyData = [
    { date: '2025-04-01', anomalies: 24, score: 0.82 },
    { date: '2025-04-02', anomalies: 18, score: 0.76 },
    { date: '2025-04-03', anomalies: 32, score: 0.91 },
    { date: '2025-04-04', anomalies: 15, score: 0.68 },
    { date: '2025-04-05', anomalies: 28, score: 0.85 },
    { date: '2025-04-06', anomalies: 21, score: 0.79 },
    { date: '2025-04-07', anomalies: 12, score: 0.64 },
    { date: '2025-04-08', anomalies: 19, score: 0.77 },
  ];

  // Sample data for data quality issues
  const dataQualityData = [
    { name: 'Missing Values', value: 187 },
    { name: 'Outliers', value: 56 },
    { name: 'Format Errors', value: 43 },
    { name: 'Duplicates', value: 21 },
    { name: 'Type Mismatches', value: 15 },
  ];

  // Sample schema validation results
  const schemaValidations = [
    { field: 'email', type: 'string', format: 'email', valid: true, issues: 0 },
    { field: 'age', type: 'integer', min: 18, max: 120, valid: true, issues: 3 },
    { field: 'income', type: 'number', valid: false, issues: 12 },
    { field: 'address', type: 'string', valid: true, issues: 0 },
    { field: 'purchase_date', type: 'string', format: 'date', valid: false, issues: 8 },
  ];

  const COLORS = ['#4ade80', '#facc15', '#f87171', '#60a5fa', '#a78bfa'];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Data Analytics & Profiling</h1>
      </div>
      
      <Tabs defaultValue="anomalies">
        <TabsList className="mb-4">
          <TabsTrigger value="anomalies">Anomaly Detection</TabsTrigger>
          <TabsTrigger value="quality">Data Quality</TabsTrigger>
          <TabsTrigger value="validation">Schema Validation</TabsTrigger>
        </TabsList>
        
        <TabsContent value="anomalies" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Anomaly Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={anomalyData}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="anomalies" stroke="#8884d8" name="Detected Anomalies" />
                    <Line type="monotone" dataKey="score" stroke="#82ca9d" name="Anomaly Score" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Recent Anomalies</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Count</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {anomalyData.map((row, index) => (
                    <TableRow key={index}>
                      <TableCell>{row.date}</TableCell>
                      <TableCell>{row.anomalies}</TableCell>
                      <TableCell>{row.score.toFixed(2)}</TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded-full text-xs ${row.score > 0.8 ? 'bg-red-100 text-red-800' : row.score > 0.7 ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
                          {row.score > 0.8 ? 'Critical' : row.score > 0.7 ? 'Warning' : 'Normal'}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="quality" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Data Quality Issues</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80 flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
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
            
            <Card>
              <CardHeader>
                <CardTitle>Data Quality Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={dataQualityData}
                      layout="vertical"
                      margin={{ top: 5, right: 30, left: 60, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis dataKey="name" type="category" />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="value" fill="#8884d8" name="Count" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="validation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Pydantic Schema Validation Results</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Field</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Constraints</TableHead>
                    <TableHead>Valid</TableHead>
                    <TableHead>Issues</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {schemaValidations.map((row, index) => (
                    <TableRow key={index}>
                      <TableCell>{row.field}</TableCell>
                      <TableCell>{row.type}</TableCell>
                      <TableCell>
                        {row.format ? `format: ${row.format}` : ''}
                        {row.min !== undefined ? `, min: ${row.min}` : ''}
                        {row.max !== undefined ? `, max: ${row.max}` : ''}
                      </TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded-full text-xs ${row.valid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {row.valid ? 'Valid' : 'Invalid'}
                        </span>
                      </TableCell>
                      <TableCell>{row.issues}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Analytics;
