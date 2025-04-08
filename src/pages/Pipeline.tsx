
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import PipelineStages from '@/components/pipeline/PipelineStages';
import PipelineUploadForm from '@/components/pipeline/PipelineUploadForm';
import PipelineStatusTable from '@/components/pipeline/PipelineStatusTable';
import PipelineAnalytics from '@/components/pipeline/PipelineAnalytics';
import ChatInterface from '@/components/pipeline/ChatInterface';

const Pipeline: React.FC = () => {
  const [isChatOpen, setIsChatOpen] = useState(false);
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Data Pipeline</h1>
          <p className="text-muted-foreground">
            Manage and monitor your data processing workflow
          </p>
        </div>
        <Button 
          onClick={() => setIsChatOpen(!isChatOpen)}
          variant="outline"
          className="flex items-center gap-2"
        >
          <span className={`w-2 h-2 rounded-full ${isChatOpen ? 'bg-green-500' : 'bg-blue-500'}`}></span>
          {isChatOpen ? 'Hide AI Assistant' : 'Open AI Assistant'}
        </Button>
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
          <Tabs defaultValue="upload" className="w-full">
            <TabsList className="grid grid-cols-4 mb-4">
              <TabsTrigger value="upload">Upload Data</TabsTrigger>
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
                  <PipelineUploadForm />
                </CardContent>
              </Card>
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
              <Card>
                <CardHeader>
                  <CardTitle>Business Rules</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center p-8">
                    <h3 className="text-lg font-medium">Business Rules Engine</h3>
                    <p className="text-muted-foreground mt-2">
                      Configure and manage business rules for automated data processing
                    </p>
                    <Button className="mt-4">Manage Rules</Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
        
        {isChatOpen && (
          <div className="md:col-span-1">
            <ChatInterface />
          </div>
        )}
      </div>
    </div>
  );
};

export default Pipeline;
