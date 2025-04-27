import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Eye, FileSpreadsheet, Database, RefreshCw } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { useNavigate } from 'react-router-dom';

interface Dataset {
  id: string;
  name: string;
  rows: number;
  columns: number;
  lastUpdated: string;
  status: 'active' | 'processing' | 'error';
  quality?: number;
}

interface DatasetSummaryProps {
  datasets: Dataset[];
  loading?: boolean;
}

const DatasetSummary: React.FC<DatasetSummaryProps> = ({ datasets, loading = false }) => {
  const navigate = useNavigate();
  
  const renderStatus = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-500 text-white">Active</Badge>;
      case 'processing':
        return <Badge className="bg-yellow-500 text-white">Processing</Badge>;
      case 'error':
        return <Badge className="bg-red-500 text-white">Error</Badge>;
      default:
        return <Badge className="border border-gray-300">{status}</Badge>;
    }
  };
  
  const handleViewDataset = (id: string) => {
    navigate(`/datasets/${id}`);
  };
  
  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>Dataset Summary</CardTitle>
            <CardDescription>Overview of available datasets</CardDescription>
          </div>
          <Button className="border border-gray-300 py-1 px-3 text-sm rounded-md" onClick={() => navigate('/datasets')}>
            View All
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : datasets.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Quality</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {datasets.map((dataset) => (
                <TableRow key={dataset.id}>
                  <TableCell className="font-medium">{dataset.name}</TableCell>
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="text-xs text-muted-foreground">{dataset.rows.toLocaleString()} rows</span>
                      <span className="text-xs text-muted-foreground">{dataset.columns} columns</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {dataset.quality ? (
                      <div className="flex items-center">
                        <div className="w-16 h-2 bg-secondary rounded-full overflow-hidden mr-2">
                          <div 
                            className={`h-2 ${dataset.quality >= 85 ? 'bg-green-500' : dataset.quality >= 70 ? 'bg-amber-500' : 'bg-red-500'}`}
                            style={{ width: `${dataset.quality}%` }}
                          />
                        </div>
                        <span className="text-xs">{dataset.quality}%</span>
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground">N/A</span>
                    )}
                  </TableCell>
                  <TableCell>{renderStatus(dataset.status)}</TableCell>
                  <TableCell className="text-right">
                    <Button className="bg-transparent p-1 rounded-full hover:bg-gray-100" onClick={() => handleViewDataset(dataset.id)}>
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <div className="flex flex-col items-center justify-center py-8">
            <Database className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No datasets available</p>
            <Button className="border border-gray-300 py-1 px-3 text-sm rounded-md mt-4" onClick={() => navigate('/datasets/new')}>
              <FileSpreadsheet className="h-4 w-4 mr-2" />
              Upload Dataset
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DatasetSummary;
