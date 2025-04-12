
import React, { useState, useEffect } from 'react';
import ChatInterface from '@/components/ai/ChatInterface';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DatasetProvider } from '@/hooks/useDatasetContext';
import { api } from '@/api/api';
import { ChatSuggestion } from '@/components/ai/ChatInterface';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const AiChat: React.FC = () => {
  const [suggestions, setSuggestions] = useState<ChatSuggestion[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  
  // Load initial chat suggestions
  useEffect(() => {
    const loadSuggestions = async () => {
      setIsLoadingSuggestions(true);
      
      try {
        // Call AI service to get suggested questions
        const response = await api.getAiAssistantResponse("Generate 5 common data analysis questions", {
          type: "suggestion_generation"
        });
        
        if (response.success && response.data) {
          // Parse suggestions from response
          const suggestions: ChatSuggestion[] = [
            { id: "1", text: "What's the distribution of values in column X?", category: "exploration" },
            { id: "2", text: "Show me the relationship between column A and B", category: "correlation" },
            { id: "3", text: "What are the top outliers in this dataset?", category: "anomalies" },
            { id: "4", text: "Summarize the key statistics of this dataset", category: "statistics" },
            { id: "5", text: "What trends do you notice over time?", category: "trends" }
          ];
          
          setSuggestions(suggestions);
        }
      } catch (error) {
        console.error("Failed to load suggestions:", error);
      } finally {
        setIsLoadingSuggestions(false);
      }
    };
    
    loadSuggestions();
  }, []);
  
  return (
    <DatasetProvider>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">AI Data Assistant</h1>
          <p className="text-muted-foreground">
            Explore your data with natural language using vector DB and Hugging Face models
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-4">
          {/* Left sidebar with info */}
          <Card className="md:col-span-1">
            <CardHeader>
              <CardTitle>AI Assistant Features</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-medium">Vector Database</h3>
                <p className="text-sm text-muted-foreground">Ask questions about your data using semantic search</p>
              </div>
              
              <div>
                <h3 className="font-medium">Hugging Face Integration</h3>
                <p className="text-sm text-muted-foreground">Powered by state-of-the-art language models</p>
              </div>
              
              <div>
                <h3 className="font-medium">Chat Categories</h3>
                <div className="flex flex-wrap gap-2 mt-2">
                  <Badge variant="outline">Exploration</Badge>
                  <Badge variant="outline">Analysis</Badge>
                  <Badge variant="outline">Statistics</Badge>
                  <Badge variant="outline">Predictions</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* Main chat interface */}
          <div className="md:col-span-3">
            <Tabs defaultValue="chat" className="w-full">
              <TabsList className="grid grid-cols-3 mb-4">
                <TabsTrigger value="chat">Chat Assistant</TabsTrigger>
                <TabsTrigger value="history">Chat History</TabsTrigger>
                <TabsTrigger value="settings">Settings</TabsTrigger>
              </TabsList>
              
              <TabsContent value="chat" className="mt-0">
                <ChatInterface 
                  title="Data Exploration Assistant"
                  subtitle="Ask questions about your datasets"
                  showDatasetSelector={true}
                  suggestions={suggestions}
                />
              </TabsContent>
              
              <TabsContent value="history" className="mt-0">
                <Card>
                  <CardHeader>
                    <CardTitle>Chat History</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground">
                      View and manage your past conversations across datasets.
                      This feature uses local storage to save your chat history.
                    </p>
                    {/* Chat history management UI can be added here */}
                  </CardContent>
                </Card>
              </TabsContent>
              
              <TabsContent value="settings" className="mt-0">
                <Card>
                  <CardHeader>
                    <CardTitle>AI Assistant Settings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground">
                      Configure your AI assistant preferences and model settings.
                    </p>
                    {/* Settings UI can be added here */}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </DatasetProvider>
  );
};

export default AiChat;
