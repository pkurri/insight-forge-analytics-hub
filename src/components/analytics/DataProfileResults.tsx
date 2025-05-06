
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/api/api';

interface DataProfile {
  columns: {
    name: string;
    type: string;
    missing: number;
    unique: number;
    min?: number | string;
    max?: number | string;
    mean?: number;
    median?: number;
    stdDev?: number;
    topValues?: Array<{value: any, count: number}>;
  }[];
  rowCount: number;
  missingCells: number;
}

export default function DataProfileResults() {
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const [profile, setProfile] = useState<DataProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Get the first dataset to profile if no dataset ID is specified
    const getFirstDataset = async () => {
      try {
        const datasetsResponse = await api.datasets.getDatasets();
        if (datasetsResponse.success && datasetsResponse.data && datasetsResponse.data.length > 0) {
          setDatasetId(datasetsResponse.data[0].id);
        }
      } catch (error) {
        console.error('Error fetching datasets:', error);
        setError('Failed to fetch datasets');
      }
    };

    getFirstDataset();
  }, []);

  useEffect(() => {
    if (datasetId) {
      fetchDataProfile(datasetId);
    }
  }, [datasetId]);

  const fetchDataProfile = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      // Use the analytics service to fetch the profile
      const response = await api.analytics.fetchDataProfile(id);
      if (response.success && response.data) {
        setProfile(response.data);
      } else {
        setError(response.error || 'Failed to fetch data profile');
      }
    } catch (error) {
      console.error('Error fetching data profile:', error);
      setError('An error occurred while fetching the data profile');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center p-10">Loading data profile...</div>;
  }

  if (error) {
    return <div className="text-center text-red-500 p-10">{error}</div>;
  }

  if (!profile) {
    return <div className="text-center p-10">No data profile available</div>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Data Profile Results</h2>
      
      <Card>
        <CardHeader>
          <CardTitle>Dataset Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-sm text-gray-500">Total Rows</div>
              <div className="text-2xl font-bold">{profile.rowCount.toLocaleString()}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-sm text-gray-500">Total Columns</div>
              <div className="text-2xl font-bold">{profile.columns.length}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-sm text-gray-500">Missing Values</div>
              <div className="text-2xl font-bold">{profile.missingCells.toLocaleString()}</div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Column Profiles</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-gray-50">
                  <th className="p-2 text-left border">Column</th>
                  <th className="p-2 text-left border">Type</th>
                  <th className="p-2 text-left border">Missing</th>
                  <th className="p-2 text-left border">Unique</th>
                  <th className="p-2 text-left border">Range/Values</th>
                </tr>
              </thead>
              <tbody>
                {profile.columns.map((column, index) => (
                  <tr key={index} className={index % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                    <td className="p-2 border font-medium">{column.name}</td>
                    <td className="p-2 border">{column.type}</td>
                    <td className="p-2 border">{column.missing} ({((column.missing / profile.rowCount) * 100).toFixed(1)}%)</td>
                    <td className="p-2 border">{column.unique} ({((column.unique / profile.rowCount) * 100).toFixed(1)}%)</td>
                    <td className="p-2 border">
                      {column.min !== undefined && column.max !== undefined ? 
                        `${column.min} to ${column.max}` : 
                        column.topValues ? 
                          column.topValues.slice(0, 3).map(v => `${v.value} (${v.count})`).join(', ') :
                          'N/A'
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
