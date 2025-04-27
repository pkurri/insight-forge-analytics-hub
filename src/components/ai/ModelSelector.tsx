import React, { useState, useEffect } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Info } from 'lucide-react';
import { AIModel } from '@/api/services/ai/modelService';

interface ModelSelectorProps {
  models: AIModel[];
  selectedModel: string;
  onModelChange: (modelId: string) => void;
  isLoading?: boolean;
  className?: string;
}

/**
 * ModelSelector component for choosing AI models
 * Supports filtering by model type and provider
 */
const ModelSelector: React.FC<ModelSelectorProps> = ({
  models,
  selectedModel,
  onModelChange,
  isLoading = false,
  className = "",
}) => {
  const [filteredModels, setFilteredModels] = useState<AIModel[]>(models);
  const [selectedType, setSelectedType] = useState<string>('all');

  // Filter models when the type selection changes
  useEffect(() => {
    if (selectedType === 'all') {
      setFilteredModels(models);
    } else {
      setFilteredModels(models.filter(model => model.type === selectedType));
    }
  }, [selectedType, models]);

  // Get the currently selected model object
  const currentModel = models.find(model => model.id === selectedModel);

  return (
    <div className={`flex flex-col space-y-2 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium">AI Model:</span>
          {currentModel && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="inline-flex items-center">
                    <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                  </div>
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  <div className="space-y-2">
                    <p><strong>{currentModel.name}</strong></p>
                    <p className="text-xs">{currentModel.description}</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {currentModel.capabilities.map(cap => (
                        <Badge key={cap} variant="outline" className="text-xs">
                          {cap}
                        </Badge>
                      ))}
                    </div>
                    <p className="text-xs mt-1">
                      Context: {currentModel.contextWindow} tokens | 
                      Max Output: {currentModel.maxTokens} tokens
                    </p>
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
        <div className="flex space-x-1">
          <Badge 
            variant={selectedType === 'all' ? "default" : "outline"}
            className="cursor-pointer text-xs"
            onClick={() => setSelectedType('all')}
          >
            All
          </Badge>
          <Badge 
            variant={selectedType === 'chat' ? "default" : "outline"}
            className="cursor-pointer text-xs"
            onClick={() => setSelectedType('chat')}
          >
            Chat
          </Badge>
          <Badge 
            variant={selectedType === 'embedding' ? "default" : "outline"}
            className="cursor-pointer text-xs"
            onClick={() => setSelectedType('embedding')}
          >
            Embedding
          </Badge>
          <Badge 
            variant={selectedType === 'specialized' ? "default" : "outline"}
            className="cursor-pointer text-xs"
            onClick={() => setSelectedType('specialized')}
          >
            Specialized
          </Badge>
        </div>
      </div>
      
      <Select 
        value={selectedModel} 
        onValueChange={onModelChange}
        disabled={isLoading}
      >
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select AI Model" />
        </SelectTrigger>
        <SelectContent>
          {filteredModels.map(model => (
            <SelectItem key={model.id} value={model.id}>
              <div className="flex items-center justify-between w-full">
                <span>{model.name}</span>
                <Badge variant="outline" className="ml-2 text-xs">
                  {model.provider}
                </Badge>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};

export default ModelSelector;
