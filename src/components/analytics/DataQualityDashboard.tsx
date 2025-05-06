import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { api } from '@/api/api';

interface DataQualityMetrics {
  score: number;
  completeness: number;
  accuracy: number;
  consistency: number;
  timeliness: number;
  schemaCompliance: number;
}

export default function DataQualityDashboard() {
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<DataQualityMetrics>({
    score: 0,
    completeness: 0,
    accuracy: 0,
    consistency: 0,
    timeliness: 0,
    schemaCompliance: 0
  });
  const [loading, setLoading] = useState(false);
  const [cleaning, setCleaning] = useState(false);

  useEffect(() => {
    // Get the first dataset to analyze if no dataset ID is specified
    const getFirstDataset = async () => {
      try {
        const datasetsResponse = await api.datasets.getDatasets();
        if (datasetsResponse.success && datasetsResponse.data && datasetsResponse.data.length > 0) {
          setDatasetId(datasetsResponse.data[0].id);
        }
      } catch (error) {
        console.error('Error fetching datasets:', error);
      }
    };

    getFirstDataset();
  }, []);

  useEffect(() => {
    if (datasetId) {
      fetchDataQuality(datasetId);
    }
  }, [datasetId]);

  const fetchDataQuality = async (id: string) => {
    setLoading(true);
    try {
      const response = await api.analytics.getDataQuality(id);
      if (response.success && response.data) {
        // Update with actual data quality metrics
        setMetrics({
          score: response.data.score || 0,
          completeness: response.data.completeness || 0,
          accuracy: response.data.accuracy || 0,
          consistency: response.data.consistency || 0,
          timeliness: response.data.timeliness || 0,
          schemaCompliance: response.data.schemaCompliance || 0
        });
      }
    } catch (error) {
      console.error('Error fetching data quality metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCleanData = async () => {
    if (!datasetId) return;
    
    setCleaning(true);
    try {
      // Call the cleanData method from the analytics service
      await api.analytics.cleanData(datasetId);
      
      // Refetch data quality after cleaning
      await fetchDataQuality(datasetId);
    } catch (error) {
      console.error('Error cleaning data:', error);
    } finally {
      setCleaning(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-amber-600';
    return 'text-red-600';
  };

  const getProgressColor = (value: number) => {
    if (value >= 80) return 'bg-green-500';
    if (value >= 60) return 'bg-amber-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Data Quality Dashboard</h2>
        <Button onClick={handleCleanData} disabled={cleaning || !datasetId}>
          {cleaning ? 'Cleaning...' : 'Clean Data'}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Overall Quality Score</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center items-center h-40">
            <div className="text-7xl font-bold text-center">
              <span className={getScoreColor(metrics.score)}>{metrics.score}</span>
              <span className="text-2xl font-normal text-gray-400">/100</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Completeness</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Score</span>
                <span className={getScoreColor(metrics.completeness)}>{metrics.completeness}%</span>
              </div>
              <Progress value={metrics.completeness} className={getProgressColor(metrics.completeness)} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Accuracy</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Score</span>
                <span className={getScoreColor(metrics.accuracy)}>{metrics.accuracy}%</span>
              </div>
              <Progress value={metrics.accuracy} className={getProgressColor(metrics.accuracy)} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Consistency</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Score</span>
                <span className={getScoreColor(metrics.consistency)}>{metrics.consistency}%</span>
              </div>
              <Progress value={metrics.consistency} className={getProgressColor(metrics.consistency)} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Schema Compliance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Score</span>
                <span className={getScoreColor(metrics.schemaCompliance)}>{metrics.schemaCompliance}%</span>
              </div>
              <Progress value={metrics.schemaCompliance} className={getProgressColor(metrics.schemaCompliance)} />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
