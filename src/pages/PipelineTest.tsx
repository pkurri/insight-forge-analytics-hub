import React, { useState } from 'react';
import Layout from '@/components/layout/Layout';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle, 
  CardDescription 
} from '@/components/ui';
import PipelineStages from '@/components/pipeline/PipelineStages';
import { Button } from '@/components/ui/button';
import { Database, FileText, ArrowRight, RotateCw } from 'lucide-react';

const testDatasets = [
  {
    id: 'sales-data',
    name: 'Sales Data 2024',
    description: 'Quarterly sales data for all regions',
    size: '1.2MB',
    format: 'CSV',
    columns: 12,
    rows: 5000
  },
  {
    id: 'customer-data',
    name: 'Customer Database',
    description: 'Customer information and purchase history',
    size: '3.4MB',
    format: 'JSON',
    columns: 24,
    rows: 8500
  },
  {
    id: 'inventory-data',
    name: 'Inventory Tracking',
    description: 'Current inventory levels and locations',
    size: '0.8MB',
    format: 'Excel',
    columns: 8,
    rows: 1200
  }
];

const PipelineTest: React.FC = () => {
  const [expandedStage, setExpandedStage] = useState(0);
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  
  return (
    <Layout>
      <div className="container mx-auto py-8">
        <h1 className="text-3xl font-bold mb-8">Pipeline Process Test</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <Card className="col-span-1 lg:col-span-2">
            <CardHeader>
              <CardTitle>Pipeline Workflow</CardTitle>
              <CardDescription>
                Test the data pipeline visualization with sample data
              </CardDescription>
            </CardHeader>
            <CardContent>
              <PipelineStages expandedStage={expandedStage} />
              
              <div className="flex justify-between mt-6">
                <Button 
                  variant="outline" 
                  onClick={() => setExpandedStage(Math.max(0, expandedStage - 1))}
                  disabled={expandedStage === 0}
                >
                  Previous Stage
                </Button>
                <Button 
                  onClick={() => setExpandedStage(Math.min(5, expandedStage + 1))}
                  disabled={expandedStage === 5}
                >
                  Next Stage <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Test Datasets</CardTitle>
              <CardDescription>
                Select a dataset to visualize in the pipeline
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {testDatasets.map(dataset => (
                  <div 
                    key={dataset.id}
                    className={`p-4 border rounded-md cursor-pointer transition-colors ${
                      selectedDataset === dataset.id 
                        ? 'bg-blue-50 border-blue-300' 
                        : 'hover:bg-slate-50 border-slate-200'
                    }`}
                    onClick={() => setSelectedDataset(dataset.id)}
                  >
                    <div className="flex items-start">
                      <div className="mr-3 mt-1">
                        {dataset.format === 'CSV' && <FileText className="h-5 w-5 text-emerald-500" />}
                        {dataset.format === 'JSON' && <Database className="h-5 w-5 text-blue-500" />}
                        {dataset.format === 'Excel' && <FileText className="h-5 w-5 text-green-500" />}
                      </div>
                      <div>
                        <h3 className="font-medium">{dataset.name}</h3>
                        <p className="text-sm text-muted-foreground">{dataset.description}</p>
                        <div className="flex gap-3 mt-2 text-xs text-muted-foreground">
                          <span>{dataset.format}</span>
                          <span>{dataset.size}</span>
                          <span>{dataset.rows.toLocaleString()} rows</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                
                <Button 
                  variant="outline" 
                  className="w-full mt-4"
                  onClick={() => {
                    setSelectedDataset(null);
                    setExpandedStage(0);
                  }}
                >
                  <RotateCw className="h-4 w-4 mr-2" />
                  Reset Test
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
        
        <div className="grid grid-cols-1 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Test Results</CardTitle>
              <CardDescription>
                Information about the pipeline process
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 bg-slate-50 rounded-md">
                  <h3 className="font-medium mb-2">Selected Dataset</h3>
                  {selectedDataset ? (
                    <div>
                      <p>
                        <span className="font-medium">Name:</span>{' '}
                        {testDatasets.find(d => d.id === selectedDataset)?.name}
                      </p>
                      <p>
                        <span className="font-medium">Format:</span>{' '}
                        {testDatasets.find(d => d.id === selectedDataset)?.format}
                      </p>
                      <p>
                        <span className="font-medium">Size:</span>{' '}
                        {testDatasets.find(d => d.id === selectedDataset)?.size}
                      </p>
                      <p>
                        <span className="font-medium">Rows:</span>{' '}
                        {testDatasets.find(d => d.id === selectedDataset)?.rows.toLocaleString()}
                      </p>
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No dataset selected</p>
                  )}
                </div>
                
                <div className="p-4 bg-slate-50 rounded-md">
                  <h3 className="font-medium mb-2">Current Pipeline Stage</h3>
                  <p>
                    <span className="font-medium">Stage:</span>{' '}
                    {expandedStage === 0 && 'Upload'}
                    {expandedStage === 1 && 'Validate'}
                    {expandedStage === 2 && 'Business Rules'}
                    {expandedStage === 3 && 'Transform'}
                    {expandedStage === 4 && 'Enrich'}
                    {expandedStage === 5 && 'Load'}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {expandedStage === 0 && 'Data ingestion from various sources'}
                    {expandedStage === 1 && 'Validation of data schema and quality'}
                    {expandedStage === 2 && 'Application of business rules and logic'}
                    {expandedStage === 3 && 'Data transformation and cleaning'}
                    {expandedStage === 4 && 'Data enrichment with derived fields'}
                    {expandedStage === 5 && 'Loading data to destination systems'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
};

export default PipelineTest;
