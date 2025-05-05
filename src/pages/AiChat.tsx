import React, { useState, useEffect } from 'react';
import ChatInterface from '@/components/ai/ChatInterface';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DatasetProvider } from '@/hooks/useDatasetContext';
import { api } from '@/api/api';
import { ChatSuggestion } from '@/api/types';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';

// Interface for AI Model selection
interface AIModel {
  id: string;
  type: string;
  dimensions?: number;
  is_default?: boolean;
}

const AiChat: React.FC = () => {
  const [suggestions, setSuggestions] = useState<ChatSuggestion[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<string>("all"); // 'all' or specific dataset ID
  const [availableModels, setAvailableModels] = useState<AIModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>(""); // Model ID
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  
  // Load available models
  useEffect(() => {
    const loadModels = async () => {
      setIsLoadingModels(true);
      
      try {
        // Using aiAgentService to get models
        const response = await api.models.getAvailableModels();
        if (response.success && response.data && response.data.models) {
          setAvailableModels(response.data.models);
          
          // Set default model
          const defaultModel = response.data.models.find((model: AIModel) => model.is_default && model.type === "generation");
          if (defaultModel) {
            setSelectedModel(defaultModel.id);
          } else if (response.data.models.length > 0) {
            setSelectedModel(response.data.models[0].id);
          }
        }
      } catch (error) {
        console.error("Failed to load AI models:", error);
      } finally {
        setIsLoadingModels(false);
      }
    };
    
    loadModels();
  }, []);
  
  // Load initial chat suggestions
  useEffect(() => {
    const loadSuggestions = async () => {
      setIsLoadingSuggestions(true);
      
      try {
        // Call AI service to get suggested questions for the selected dataset
        const datasetParam = selectedDataset !== "all" ? selectedDataset : undefined;
        const response = await api.getAiAssistantResponse("Generate chat suggestions", {
          dataset_id: datasetParam,
          model_id: selectedModel,
          agent_type: "suggestion_generation",
          context: {}
        });
        
        if (response.success && response.data) {
          // Parse suggestions from response
          setSuggestions([
            { id: "1", text: "What's the distribution of values in column X?", category: "exploration" },
            { id: "2", text: "Show me the relationship between column A and B", category: "correlation" },
            { id: "3", text: "What are the top outliers in this dataset?", category: "anomalies" },
            { id: "4", text: "Summarize the key statistics of this dataset", category: "statistics" },
            { id: "5", text: "What trends do you notice over time?", category: "trends" }
          ]);
        }
      } catch (error) {
        console.error("Failed to load suggestions:", error);
      } finally {
        setIsLoadingSuggestions(false);
      }
    };
    
    loadSuggestions();
  }, [selectedDataset, selectedModel]);
  
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
          {/* Left sidebar with info and settings */}
          <Card className="md:col-span-1">
            <CardHeader>
              <CardTitle>Settings & Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-medium mb-2">Dataset Selection</h3>
                <Select
                  value={selectedDataset}
                  onValueChange={setSelectedDataset}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select dataset" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Datasets</SelectItem>
                    {/* Dataset items will be loaded dynamically */}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <h3 className="font-medium mb-2">Model Selection</h3>
                {isLoadingModels ? (
                  <Skeleton className="h-10 w-full" />
                ) : (
                  <Select
                    value={selectedModel}
                    onValueChange={setSelectedModel}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select AI model" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableModels
                        .filter(model => model.type === "generation")
                        .map(model => (
                          <SelectItem key={model.id} value={model.id}>
                            {model.id.split('/').pop() || model.id}
                          </SelectItem>
                        ))
                      }
                    </SelectContent>
                  </Select>
                )}
              </div>
              
              <div>
                <h3 className="font-medium">Technologies</h3>
                <p className="text-sm text-muted-foreground">Ask questions about your data using semantic search</p>
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
                <TabsTrigger value="settings">Advanced Settings</TabsTrigger>
              </TabsList>
              
              <TabsContent value="chat" className="mt-0">
                <ChatInterface 
                  title="Data Exploration Assistant"
                  subtitle="Ask questions about your datasets"
                  showDatasetSelector={true}
                  suggestions={suggestions}
                  defaultDataset={selectedDataset !== "all" ? selectedDataset : undefined}
                  selectedModel={selectedModel}
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
                    <CardTitle>AI Assistant Advanced Settings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground mb-4">
                      Configure your AI assistant preferences and model settings.
                    </p>
                    
                    <div className="space-y-4">
                      <div>
                        <h3 className="text-sm font-medium mb-2">Response Length</h3>
                        <Select defaultValue="medium">
                          <SelectTrigger>
                            <SelectValue placeholder="Response length" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="short">Short</SelectItem>
                            <SelectItem value="medium">Medium</SelectItem>
                            <SelectItem value="long">Long</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      
                      <div>
                        <h3 className="text-sm font-medium mb-2">Temperature</h3>
                        <Select defaultValue="balanced">
                          <SelectTrigger>
                            <SelectValue placeholder="Creativity level" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="precise">Precise (0.2)</SelectItem>
                            <SelectItem value="balanced">Balanced (0.7)</SelectItem>
                            <SelectItem value="creative">Creative (1.0)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      
                      <div>
                        <h3 className="text-sm font-medium mb-2">Embedding Model</h3>
                        <Select defaultValue={availableModels.find(model => model.type === "embedding")?.id || ""}>
                          <SelectTrigger>
                            <SelectValue placeholder="Embedding model" />
                          </SelectTrigger>
                          <SelectContent>
                            {availableModels
                              .filter(model => model.type === "embedding")
                              .map(model => (
                                <SelectItem key={model.id} value={model.id}>
                                  {model.id.split('/').pop() || model.id}
                                </SelectItem>
                              ))
                            }
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
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
