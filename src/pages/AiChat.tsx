
import React, { useState, useEffect } from 'react';
import ChatInterface from '@/components/ai/ChatInterface';
import ModelSelector from '@/components/ai/ModelSelector';
import { api } from '@/api/api';
import { useDatasetContext } from '@/hooks/useDatasetContext';
import DatasetSelector from '@/components/ai/DatasetSelector';
import { DatasetProvider } from '@/hooks/useDatasetContext';

interface Agent {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
}

// Define dummy AI models for display purposes
const aiModels = [
  {
    id: 'gpt-4',
    name: 'GPT-4',
    description: 'Advanced language model for complex tasks',
    provider: 'OpenAI',
    type: 'chat',
    capabilities: ['Text generation', 'Context understanding', 'Complex reasoning'],
    contextWindow: 8192,
    maxTokens: 4096
  },
  {
    id: 'gpt-3.5-turbo',
    name: 'GPT-3.5 Turbo',
    description: 'Fast and efficient language model',
    provider: 'OpenAI',
    type: 'chat',
    capabilities: ['Text generation', 'Context understanding'],
    contextWindow: 4096,
    maxTokens: 2048
  }
];

// Create a wrapper component with DatasetProvider
const AiChatWithProvider: React.FC = () => {
  return (
    <DatasetProvider>
      <AiChatContent />
    </DatasetProvider>
  );
};

// Actual content of the AiChat page
const AiChatContent: React.FC = () => {
  const [selectedModel, setSelectedModel] = useState<string>('gpt-4');
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const { activeDataset, datasets } = useDatasetContext();
  
  useEffect(() => {
    const loadAgents = async () => {
      setLoading(true);
      try {
        // Fetch available AI agents
        const response = await api.agents.getAgents();
        if (response.success && response.data) {
          setAgents(response.data);
          if (response.data.length > 0) {
            setSelectedAgentId(response.data[0].id);
          }
        }
      } catch (error) {
        console.error('Error loading AI agents:', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadAgents();
  }, []);
  
  const handleModelChange = (model: string) => {
    setSelectedModel(model);
  };
  
  const handleDatasetChange = (datasetId: string) => {
    // This function would be passed to DatasetSelector
    // but we're using the context's activeDataset instead
    console.log('Dataset selected:', datasetId);
  };
  
  // Convert context datasets to format expected by DatasetSelector
  const formattedDatasets = datasets.map(dataset => ({
    id: dataset.id,
    name: dataset.name,
    rows: dataset.recordCount || 0,
    columns: dataset.columnCount || 0,
    lastUpdated: dataset.updatedAt,
    source: 'Local'
  }));
  
  return (
    <div className="container mx-auto p-4">
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold">AI Assistant</h1>
          <div className="flex items-center gap-4">
            <ModelSelector 
              selectedModel={selectedModel} 
              onModelChange={handleModelChange}
              models={aiModels}
              isLoading={loading}
            />
            <DatasetSelector 
              datasets={formattedDatasets}
              selectedDataset={activeDataset}
              onDatasetChange={handleDatasetChange}
              isLoading={loading}
            />
          </div>
        </div>
        
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-3 hidden md:block">
            <div className="bg-card rounded-lg p-4">
              <h2 className="text-xl font-semibold mb-4">Dataset Info</h2>
              {activeDataset ? (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground">Selected Dataset</h3>
                    <p className="text-base">{datasets.find(d => d.id === activeDataset)?.name || activeDataset}</p>
                  </div>
                  
                  <button 
                    className="bg-primary text-primary-foreground hover:bg-primary/90 w-full py-2 rounded-md text-sm"
                    onClick={() => api.aiService.analyzeAnomalies(activeDataset)}
                  >
                    Analyze Dataset
                  </button>
                </div>
              ) : (
                <p className="text-muted-foreground">No dataset selected</p>
              )}
            </div>
          </div>
          
          <div className="col-span-12 md:col-span-9">
            <ChatInterface 
              datasetId={activeDataset} 
              modelId={selectedModel}
              agentId={selectedAgentId || undefined}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// Export the wrapper component as the default export
export default AiChatWithProvider;
