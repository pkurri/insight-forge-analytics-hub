import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { RefreshCw, LineChart, TrendingUp, AlertTriangle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

interface TimeSeriesDataPoint {
  timestamp: string;
  value: number;
  [key: string]: any;
}

interface TimeSeriesAnalysisProps {
  timeSeriesData: {
    series?: Record<string, TimeSeriesDataPoint[]>;
    anomalies?: Record<string, Array<{timestamp: string; expected: number; actual: number; score: number}>>;
    trends?: Record<string, Array<{start: string; end: string; slope: number; confidence: number}>>;
  };
  loading?: boolean;
}

const TimeSeriesAnalysis: React.FC<TimeSeriesAnalysisProps> = ({ timeSeriesData, loading = false }) => {
  const [selectedSeries, setSelectedSeries] = useState<string>('');
  const [timeRange, setTimeRange] = useState<string>('7d');
  
  // Get available series names
  const seriesNames = timeSeriesData.series ? Object.keys(timeSeriesData.series) : [];
  
  // Set default selected series if none is selected
  React.useEffect(() => {
    if (seriesNames.length > 0 && !selectedSeries) {
      setSelectedSeries(seriesNames[0]);
    }
  }, [seriesNames, selectedSeries]);
  
  const renderTimeSeriesChart = () => {
    if (loading) {
      return <Skeleton className="h-[300px] w-full" />;
    }
    
    if (!timeSeriesData.series || !selectedSeries || !timeSeriesData.series[selectedSeries]) {
      return (
        <div className="flex flex-col items-center justify-center h-[300px]">
          <LineChart className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-muted-foreground">No time series data available</p>
        </div>
      );
    }
    
    // Would render actual chart here with chart library
    return (
      <div className="h-[300px] flex items-center justify-center">
        <LineChart className="h-full w-full text-muted-foreground" />
      </div>
    );
  };
  
  const renderAnomalies = () => {
    if (loading) {
      return <Skeleton className="h-[200px] w-full" />;
    }
    
    if (!timeSeriesData.anomalies || !selectedSeries || !timeSeriesData.anomalies[selectedSeries] || timeSeriesData.anomalies[selectedSeries].length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-[200px]">
          <AlertTriangle className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-muted-foreground">No anomalies detected</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-4">
        {timeSeriesData.anomalies[selectedSeries].map((anomaly, index) => (
          <div key={index} className="flex items-center justify-between p-3 border rounded-md">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              <div>
                <p className="font-medium">Anomaly Detected</p>
                <p className="text-sm text-muted-foreground">
                  {new Date(anomaly.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="font-medium">Expected: {anomaly.expected.toFixed(2)}</p>
              <p className="font-medium">Actual: {anomaly.actual.toFixed(2)}</p>
              <p className="text-xs text-muted-foreground">Confidence: {(anomaly.score * 100).toFixed(1)}%</p>
            </div>
          </div>
        ))}
      </div>
    );
  };
  
  const renderTrends = () => {
    if (loading) {
      return <Skeleton className="h-[200px] w-full" />;
    }
    
    if (!timeSeriesData.trends || !selectedSeries || !timeSeriesData.trends[selectedSeries] || timeSeriesData.trends[selectedSeries].length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-[200px]">
          <TrendingUp className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-muted-foreground">No trends detected</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-4">
        {timeSeriesData.trends[selectedSeries].map((trend, index) => (
          <div key={index} className="flex items-center justify-between p-3 border rounded-md">
            <div className="flex items-center gap-3">
              <TrendingUp className={`h-5 w-5 ${trend.slope > 0 ? 'text-green-500' : 'text-red-500'}`} />
              <div>
                <p className="font-medium">{trend.slope > 0 ? 'Upward' : 'Downward'} Trend</p>
                <p className="text-sm text-muted-foreground">
                  {new Date(trend.start).toLocaleDateString()} - {new Date(trend.end).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="font-medium">Slope: {trend.slope.toFixed(4)}</p>
              <p className="text-xs text-muted-foreground">Confidence: {(trend.confidence * 100).toFixed(1)}%</p>
            </div>
          </div>
        ))}
      </div>
    );
  };
  
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Time Series Analysis</CardTitle>
              <CardDescription>Analyze temporal patterns in your data</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Select value={selectedSeries} onValueChange={setSelectedSeries}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Select metric" />
                </SelectTrigger>
                <SelectContent>
                  {seriesNames.map((name) => (
                    <SelectItem key={name} value={name}>{name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Select value={timeRange} onValueChange={setTimeRange}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="Time range" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1d">1 Day</SelectItem>
                  <SelectItem value="7d">7 Days</SelectItem>
                  <SelectItem value="30d">30 Days</SelectItem>
                  <SelectItem value="90d">90 Days</SelectItem>
                  <SelectItem value="1y">1 Year</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {renderTimeSeriesChart()}
        </CardContent>
      </Card>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Anomaly Detection</CardTitle>
            <CardDescription>Automatically detected anomalies in the selected metric</CardDescription>
          </CardHeader>
          <CardContent>
            {renderAnomalies()}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Trend Analysis</CardTitle>
            <CardDescription>Identified trends and patterns</CardDescription>
          </CardHeader>
          <CardContent>
            {renderTrends()}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TimeSeriesAnalysis;
