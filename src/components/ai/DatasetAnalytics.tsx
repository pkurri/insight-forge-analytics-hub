import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DatasetSelector } from './DatasetSelector';
import { DatasetInsights } from './DatasetInsights';
import ChatInterface from '../pipeline/ChatInterface';
import { MessageSquare, Sparkles } from 'lucide-react';

interface Dataset {
  id: string;
  name: string;
  rows: number;
  columns: number;
  lastUpdated: string;
  source?: string;
}

interface DatasetAnalyticsProps {
  initialDatasetId?: string;
  className?: string;
}

/**
 * DatasetAnalytics component that combines dataset selection, insights, and chat
 * Uses RAG and agentic framework for AI-powered analytics
 */
const DatasetAnalytics: React.FC<DatasetAnalyticsProps> = ({
  initialDatasetId,
  className = '',
}) => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<string>(initialDatasetId || '');
  const [activeTab, setActiveTab] = useState<string>('insights');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Fetch available datasets
  useEffect(() => {
    const fetchDatasets = async () => {
      setIsLoading(true);
      try {
        const response = await fetch('/api/datasets');
        if (response.ok) {
          const data = await response.json();
          setDatasets(data.datasets || []);
          
          // Select first dataset if none is selected
          if (!selectedDataset && data.datasets?.length > 0) {
            setSelectedDataset(data.datasets[0].id);
          }
        } else {
          console.error('Failed to fetch datasets');
        }
      } catch (error) {
        console.error('Error fetching datasets:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchDatasets();
  }, []);

  const handleDatasetChange = (datasetId: string) => {
    setSelectedDataset(datasetId);
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">Dataset Analytics</h2>
        
        <DatasetSelector
          datasets={datasets}
          selectedDataset={selectedDataset}
          onDatasetChange={handleDatasetChange}
          isLoading={isLoading}
          showAllOption={false}
          className="w-[250px]"
        />
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid grid-cols-2">
          <TabsTrigger value="insights" className="flex items-center">
            <Sparkles className="h-4 w-4 mr-2" />
            Insights
          </TabsTrigger>
          <TabsTrigger value="chat" className="flex items-center">
            <MessageSquare className="h-4 w-4 mr-2" />
            AI Chat
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="insights" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Dataset Insights</CardTitle>
              <CardDescription>
                AI-generated insights and suggestions for your dataset
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DatasetInsights 
                datasets={datasets} 
                initialDatasetId={selectedDataset} 
              />
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="chat" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>AI Chat Assistant</CardTitle>
              <CardDescription>
                Ask questions about your data using natural language
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ChatInterface datasetId={selectedDataset} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export { DatasetAnalytics };
export type { Dataset };
