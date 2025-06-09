
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MessageSquare } from 'lucide-react';
import PipelineStages from '@/components/pipeline/PipelineStages';
import PipelineUploadForm from '@/components/pipeline/PipelineUploadForm';
import PipelineStatusTable from '@/components/pipeline/PipelineStatusTable';
import PipelineAnalytics from '@/components/pipeline/PipelineAnalytics';
import ChatInterface from '@/components/pipeline/ChatInterface';
import BusinessRules from '@/components/pipeline/BusinessRules';
import DataSourceConfig from '@/components/pipeline/DataSourceConfig';
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger 
} from '@/components/ui/tooltip';
import { usePipeline } from '@/contexts/PipelineContext';

const Pipeline: React.FC = () => {
  const { 
    isChatOpen, 
    toggleChat, 
    activeTab, 
    setActiveTab,
    currentDataset,
    setCurrentDataset,
    pipelineStatus,
    setPipelineStatus,
    businessRules,
    updateBusinessRules
  } = usePipeline();
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Data Pipeline</h1>
          <p className="text-muted-foreground">
            Manage and monitor your data processing workflow
          </p>
        </div>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button 
                onClick={toggleChat}
                variant="outline"
                className="flex items-center gap-2"
              >
                <span className={`w-2 h-2 rounded-full ${isChatOpen ? 'bg-green-500' : 'bg-blue-500'}`}></span>
                <MessageSquare className="h-4 w-4 mr-1" />
                {isChatOpen ? 'Hide AI Assistant' : 'Open AI Assistant'}
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>AI-powered data pipeline assistant</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-3">
          <CardHeader className="pb-3">
            <CardTitle>Pipeline Workflow</CardTitle>
          </CardHeader>
          <CardContent>
            <PipelineStages />
          </CardContent>
        </Card>
      </div>

      <div className={`grid gap-6 ${isChatOpen ? 'md:grid-cols-3' : 'md:grid-cols-1'}`}>
        <div className={isChatOpen ? 'md:col-span-2' : 'md:col-span-1'}>
          <Tabs 
            value={activeTab} 
            onValueChange={setActiveTab}
            className="w-full"
          >
            <TabsList className="grid grid-cols-5 mb-4">
              <TabsTrigger value="upload">Upload Data</TabsTrigger>
              <TabsTrigger value="datasources">Data Sources</TabsTrigger>
              <TabsTrigger value="status">Pipeline Status</TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
              <TabsTrigger value="rules">Business Rules</TabsTrigger>
            </TabsList>
            
            <TabsContent value="upload" className="mt-0">
              <Card>
                <CardHeader>
                  <CardTitle>Data Upload</CardTitle>
                </CardHeader>
                <CardContent>
                  <PipelineUploadForm 
                    onUploadSuccess={(dataset) => {
                      setCurrentDataset(dataset);
                      setPipelineStatus('completed');
                      setActiveTab('analytics');
                    }}
                  />
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="datasources" className="mt-0">
              <DataSourceConfig />
            </TabsContent>
            
            <TabsContent value="status" className="mt-0">
              <Card>
                <CardHeader>
                  <CardTitle>Pipeline Status</CardTitle>
                </CardHeader>
                <CardContent>
                  <PipelineStatusTable />
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="analytics" className="mt-0">
              <Card>
                <CardHeader>
                  <CardTitle>Data Analytics</CardTitle>
                </CardHeader>
                <CardContent>
                  <PipelineAnalytics />
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="rules" className="mt-0">
              <BusinessRules 
                rules={businessRules}
                onRulesUpdate={updateBusinessRules}
                dataset={currentDataset}
                datasetId={currentDataset?.id}
              />
            </TabsContent>
          </Tabs>
        </div>
        
        {isChatOpen && (
          <div className="md:col-span-1">
            <Card className="h-full border-primary/20">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <MessageSquare className="h-4 w-4" />
                  AI Assistant
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
<ChatInterface 
                  context={{
                    currentDataset,
                    pipelineStatus,
                    activeTab,
                    businessRules
                  }}
                />
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default Pipeline;
