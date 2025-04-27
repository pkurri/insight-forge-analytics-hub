
import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { pythonApi } from '@/api/pythonIntegration';
import { useToast } from '@/hooks/use-toast';
import { Loader2 } from 'lucide-react';

interface PipelineAnalyticsProps {
  datasetId?: string;
}

const PipelineAnalytics: React.FC<PipelineAnalyticsProps> = ({ datasetId }) => {
  const [timeSeriesData, setTimeSeriesData] = useState([
    { date: '2025-04-01', ingestion: 1200, cleaning: 1000, validation: 800 },
    { date: '2025-04-02', ingestion: 1500, cleaning: 1300, validation: 1100 },
    { date: '2025-04-03', ingestion: 1000, cleaning: 850, validation: 800 },
    { date: '2025-04-04', ingestion: 1800, cleaning: 1600, validation: 1400 },
    { date: '2025-04-05', ingestion: 2000, cleaning: 1800, validation: 1600 },
    { date: '2025-04-06', ingestion: 1700, cleaning: 1500, validation: 1300 },
    { date: '2025-04-07', ingestion: 1900, cleaning: 1700, validation: 1500 },
    { date: '2025-04-08', ingestion: 2200, cleaning: 1900, validation: 1700 },
  ]);

  const [dataQualityData, setDataQualityData] = useState([
    { name: 'Clean', value: 85 },
    { name: 'Missing Values', value: 8 },
    { name: 'Errors', value: 4 },
    { name: 'Anomalies', value: 3 },
  ]);

  const [processingTimeData, setProcessingTimeData] = useState([
    { stage: 'Ingestion', time: 12 },
    { stage: 'Cleaning', time: 25 },
    { stage: 'Validation', time: 18 },
    { stage: 'Business Rules', time: 15 },
    { stage: 'Anomaly Detection', time: 30 },
    { stage: 'Analytics', time: 22 },
  ]);
  
  const [selectedDataset, setSelectedDataset] = useState<string>(datasetId || '');
  const [availableDatasets, setAvailableDatasets] = useState<Array<{id: string, name: string}>>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const { toast } = useToast();
  
  // Fetch available datasets
  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const response = await fetch('/api/datasets');
        if (response.ok) {
          const data = await response.json();
          setAvailableDatasets(data.datasets || []);
          if (data.datasets?.length > 0 && !selectedDataset) {
            setSelectedDataset(data.datasets[0].id);
          }
        }
      } catch (error) {
        console.error('Error fetching datasets:', error);
      }
    };
    
    fetchDatasets();
  }, []);
  
  // Fetch analytics data when dataset changes
  useEffect(() => {
    if (!selectedDataset) return;
    
    const fetchAnalyticsData = async () => {
      setIsLoading(true);
      try {
        // Fetch data quality metrics
        const qualityResponse = await pythonApi.getDataQuality(selectedDataset);
        if (qualityResponse.success && qualityResponse.data) {
          const { clean_percentage, missing_values_percentage, error_percentage, anomaly_percentage } = qualityResponse.data;
          setDataQualityData([
            { name: 'Clean', value: clean_percentage || 85 },
            { name: 'Missing Values', value: missing_values_percentage || 8 },
            { name: 'Errors', value: error_percentage || 4 },
            { name: 'Anomalies', value: anomaly_percentage || 3 },
          ]);
        }
        
        // Fetch pipeline processing times
        const processingResponse = await pythonApi.getPipelineMetrics(selectedDataset);
        if (processingResponse.success && processingResponse.data) {
          const { stage_metrics } = processingResponse.data;
          if (stage_metrics && Array.isArray(stage_metrics)) {
            setProcessingTimeData(stage_metrics.map(stage => ({
              stage: stage.name,
              time: stage.processing_time_seconds
            })));
          }
        }
        
        // Fetch time series data
        const timeSeriesResponse = await pythonApi.getTimeSeriesMetrics(selectedDataset);
        if (timeSeriesResponse.success && timeSeriesResponse.data) {
          const { time_series } = timeSeriesResponse.data;
          if (time_series && Array.isArray(time_series)) {
            setTimeSeriesData(time_series);
          }
        }
      } catch (error) {
        console.error('Error fetching analytics data:', error);
        toast({
          title: 'Error',
          description: 'Failed to fetch analytics data',
          variant: 'destructive'
        });
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchAnalyticsData();
  }, [selectedDataset]);

  const COLORS = ['#4ade80', '#facc15', '#f87171', '#60a5fa'];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2">Loading analytics data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {availableDatasets.length > 0 && (
        <div className="flex items-center space-x-4">
          <span className="text-sm font-medium">Dataset:</span>
          <Select value={selectedDataset} onValueChange={setSelectedDataset}>
            <SelectTrigger className="w-[240px]">
              <SelectValue placeholder="Select dataset" />
            </SelectTrigger>
            <SelectContent>
              {availableDatasets.map(dataset => (
                <SelectItem key={dataset.id} value={dataset.id}>{dataset.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}
      
      <Tabs defaultValue="overview">
        <TabsList className="mb-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="quality">Data Quality</TabsTrigger>
          <TabsTrigger value="business-rules">Business Rules</TabsTrigger>
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
      
      <TabsContent value="business-rules" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Business Rules Compliance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={[
                    { rule: 'Data Completeness', compliance: 92, violations: 8 },
                    { rule: 'Value Range', compliance: 95, violations: 5 },
                    { rule: 'Format Validation', compliance: 88, violations: 12 },
                    { rule: 'Cross-field Validation', compliance: 90, violations: 10 },
                    { rule: 'Business Logic', compliance: 85, violations: 15 }
                  ]}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="rule" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="compliance" fill="#4ade80" name="Compliance %" />
                  <Bar dataKey="violations" fill="#f87171" name="Violations %" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
    </div>
  );
};

export default PipelineAnalytics;
