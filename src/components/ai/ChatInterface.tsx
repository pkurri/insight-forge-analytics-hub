import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  SendHorizontal, Bot, RefreshCw, 
  Settings, Loader2, Sparkles
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Textarea } from '@/components/ui/textarea';
import { Rating } from '@/components/ui/rating';
import { useChatHistory } from '@/hooks/useChatHistory';
import { useDatasetContext } from '@/hooks/useDatasetContext';
import { api } from '@/api';
import { useToast } from '@/hooks/use-toast';
import { DatasetSelector } from './DatasetSelector';
import ChatSuggestions, { ChatSuggestion } from './ChatSuggestions';
import { aiAgentService, vectorDatasetService } from '@/api/services/ai';
import { getAllowedModels } from '@/api/services/ai/modelService';
import MessageList from './MessageList';
import ModelSelector from './ModelSelector';

// Define response type interfaces
// Used for AI service responses
interface AIResponse {
  answer?: string;
  text?: string;
  response?: string;
  confidence?: number;
  sources?: string[];
  insights?: string[];
  context?: {
    sources?: string[];
    similarContent?: Array<{
      id: string;
      content: string;
      metadata?: Record<string, unknown>;
      score?: number;
    }>;
    embeddingModel?: string;
    [key: string]: unknown;
  };
}

// Used for providing context to AI responses - used when sending context to AI service
// This interface defines the structure for semantic search results passed to the AI service
export interface SearchContext {
  similarContent: {
    id: string;
    content: string;
    metadata?: Record<string, unknown>;
    score?: number;
  }[];
  embeddingModel: string;
}

export interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: {
    confidence?: number;
    sources?: string[];
    insights?: string[];
    dataset?: string;
    timestamp?: string;
    modelId?: string;
    conversationId?: string;
    isError?: boolean;
    evaluationId?: string;
    evaluationScore?: number;
    improvedResponse?: string;
    [key: string]: unknown; // For any other metadata properties
  };
  timestamp: Date;
}

interface ChatInterfaceProps {
  title?: string;
  subtitle?: string;
  showDatasetSelector?: boolean;
  defaultDataset?: string;
  suggestions?: ChatSuggestion[];
  onMessage?: (message: string, dataset: string, modelId: string) => void;
  processingCallback?: (isProcessing: boolean) => void;
  className?: string;
  selectedModel?: string;
}

/**
 * Enhanced Chat Interface component that connects to Vector DB and Hugging Face models
 * Supports multiple models, dataset selection, and semantic search
 */
const ChatInterface: React.FC<ChatInterfaceProps> = ({
  title = "AI Assistant",
  subtitle = "Vector DB & Hugging Face",
  showDatasetSelector = true,
  defaultDataset = '',
  suggestions = [],
  onMessage,
  processingCallback,
  className = "",
  selectedModel = "",
}) => {
  // Get dataset context if available
  const { activeDataset, setActiveDataset } = useDatasetContext();
  
  // Local state for handling active dataset if context not available
  const [localActiveDataset, setLocalActiveDataset] = useState<string>(defaultDataset || 'all');
  
  // Use the context dataset if available, otherwise use local state
  const currentDataset = activeDataset || localActiveDataset;
  const setCurrentDataset = setActiveDataset || setLocalActiveDataset;
  
  // Chat history hook manages messages and persistence
  const {
    messages,
    addMessage,
    // Fallback for updateMessage if not present in useChatHistory
    updateMessage = () => {},
    clearHistory,
    isLoading: isHistoryLoading,
    // Fallback for conversationId if not present in useChatHistory
    conversationId = ''
  } = useChatHistory(currentDataset) as {
    messages: Message[];
    addMessage: (message: Message) => void;
    updateMessage?: (id: string, message: Message) => void;
    clearHistory: () => void;
    isLoading: boolean;
    conversationId?: string;
  };
  
  // Chat interface state
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  // Store previous inputs for future features (e.g., input history browsing)
  // Currently unused but kept for future implementation
  const [, setInputHistory] = useState<string[]>([]);
  const [expandedMessageIds, setExpandedMessageIds] = useState<string[]>([]);
  
  // OpenEvals state
  // Track the state of message evaluation (currently only used internally)
  const [, setEvaluatingMessage] = useState(false);
  const [showFeedbackDialog, setShowFeedbackDialog] = useState(false);
  const [currentFeedbackMessageId, setCurrentFeedbackMessageId] = useState<string | null>(null);
  const [feedbackRating, setFeedbackRating] = useState(3);
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackImprovementAreas, setFeedbackImprovementAreas] = useState<string[]>([]);
  const [showImprovedResponseDialog, setShowImprovedResponseDialog] = useState(false);
  const [improvedResponse, setImprovedResponse] = useState('');
  
  // Model and dataset selection state
  const [modelId, setModelId] = useState(selectedModel || 'mistral-7b-instruct');
  const [availableModels, setAvailableModels] = useState<Array<{
    id: string;
    name: string;
    provider: string;
    capabilities: string[];
    [key: string]: unknown;
  }>>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  // Embedding models state - these model lists will be used for future model selection features
  // Currently unused but kept for future implementation
  const [, setAllowedEmbeddingModels] = useState<string[]>([]);
  const [, setAllowedTextGenModels] = useState<string[]>([]);
  const [availableDatasets, setAvailableDatasets] = useState<Array<{id: string, name: string, rows: number, columns: number, lastUpdated: string}>>([]);
  const [isLoadingDatasets, setIsLoadingDatasets] = useState(false);
  
  // References and utilities
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  
  // Function to handle model change - needed for TypeScript to recognize the variable
  const onModelChange = (modelId: string) => {
    setModelId(modelId);
  };

  const fetchAllowedModels = useCallback(async () => {
    setIsLoadingModels(true);
    try {
      const response = await getAllowedModels();
      
      if (response.success && response.data) {
        // Set available models
        setAvailableModels(response.data.models || []);
        
        // Set allowed embedding models
        if (response.data.allowed_embedding_models) {
          setAllowedEmbeddingModels(response.data.allowed_embedding_models);
        }
        
        // Set allowed text generation models
        if (response.data.allowed_text_gen_models) {
          setAllowedTextGenModels(response.data.allowed_text_gen_models);
        }
        
        // If no model is selected, select the first one
        if (!modelId && response.data.models && response.data.models.length > 0) {
          setModelId(response.data.models[0].id);
          if (onModelChange) {
            onModelChange(response.data.models[0].id);
          }
        }
      } else {
        console.error('Failed to fetch allowed models:', response.error || 'Unknown error');
        toast({
          title: 'Error',
          description: 'Failed to fetch allowed models',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Error fetching allowed models:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch allowed models',
        variant: 'destructive'
      });
    } finally {
      setIsLoadingModels(false);
    }
  }, [modelId, toast]); // onModelChange is a prop and doesn't need to be in the dependency array

  const fetchDatasets = useCallback(async () => {
    setIsLoadingDatasets(true);
    try {
      // Use the vectorDatasetService to get vectorized datasets
      const response = await vectorDatasetService.getVectorizedDatasets();
      
      if (response.success && response.data) {
        // Convert the response format to match the expected Dataset interface
        const formattedDatasets = response.data.map(dataset => ({
          id: dataset.id,
          name: dataset.name,
          rows: dataset.record_count,
          columns: dataset.column_count,
          lastUpdated: dataset.last_updated,
          // Add embedding model information for display
          source: dataset.embedding_model ? `Model: ${dataset.embedding_model}` : undefined
        }));
        
        setAvailableDatasets(formattedDatasets);
      } else {
        console.error('Failed to fetch vectorized datasets:', response.error || 'Unknown error');
        toast({
          title: 'Error',
          description: 'Failed to fetch vectorized datasets',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Error fetching vectorized datasets:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch vectorized datasets',
        variant: 'destructive'
      });
    } finally {
      setIsLoadingDatasets(false);
    }
  }, [toast]);

  // Update model ID when prop changes
  useEffect(() => {
    if (selectedModel) {
      setModelId(selectedModel);
    }
  }, [selectedModel]);
  
  // Update processing status to parent component if callback provided
  useEffect(() => {
    if (processingCallback) {
      processingCallback(isProcessing);
    }
  }, [isProcessing, processingCallback]);
  
  // Fetch models and datasets on mount
  useEffect(() => {
    fetchAllowedModels();
    fetchDatasets();
  }, [fetchAllowedModels, fetchDatasets]);
  
  // Scroll to bottom when new messages are added
  useEffect(() => {
    if (scrollAreaRef.current && messages.length > 0) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages]);
  
  // Evaluate a response using OpenEvals
  const evaluateResponse = useCallback(async (messageId: string, userQuery: string, assistantResponse: string) => {
    setEvaluatingMessage(true);
    try {
      const result = await aiAgentService.evaluateResponse(
        userQuery,
        assistantResponse,
        conversationId
      );
      
      if (result.success && result.data) {
        // Update message with evaluation results
        const message = messages.find((msg: Message) => msg.id === messageId);
        if (message) {
          updateMessage(messageId, {
            ...message,
            metadata: {
              ...message.metadata,
              evaluationId: result.data.evaluation_id || '',
              evaluationScore: result.data.average_score
            }
          });
        }
      }
    } catch (error) {
      console.error('Error evaluating response:', error);
    } finally {
      setEvaluatingMessage(false);
    }
  }, [messages, updateMessage, conversationId]);

  // Get improved response from OpenEvals - Currently unused but kept for future use
  const getImprovedResponse = useCallback(async (messageId: string) => {
    const message = messages.find((msg: Message) => msg.id === messageId);
    if (!message || message.type !== 'assistant') return;
    
    // Find the user message that preceded this one
    const userMessage = messages.find((msg: Message) => {
      return msg.type === 'user' && new Date(msg.timestamp) < new Date(message.timestamp);
    });
    
    if (!userMessage) return;
    
    try {
      const result = await aiAgentService.getImprovedResponse({
        userQuery: userMessage.content,
        assistantResponse: message.content,
        feedback: 'Please improve this response',
        conversationId: conversationId || ''
      });
      
      if (result.success && result.data) {
        // Update message with improved response
        updateMessage(messageId, {
          ...message,
          metadata: {
            ...message.metadata,
            improvedResponse: result.data.improved_response
          }
        });
        
        toast({
          title: 'Response Improved',
          description: 'We have generated an improved response',
          variant: 'default'
        });
      } else {
        console.error('Failed to get improved response:', result.error || 'Unknown error');
        toast({
          title: 'Error',
          description: 'Failed to get improved response',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Error getting improved response:', error);
      toast({
        title: 'Error',
        description: 'Failed to get improved response',
        variant: 'destructive'
      });
    }
  }, [messages, updateMessage, conversationId, toast]);

  // Handle submitting user feedback
  const submitFeedback = useCallback(async (messageId: string, feedbackType: string, additionalComments?: string) => {
    try {
      // Find the message
      const message = messages.find(msg => msg.id === messageId);
      if (!message) return;
      
      // Submit feedback
      const response = await api.submitFeedback({
        message_id: messageId,
        feedback_type: feedbackType,
        user_comments: additionalComments || '',
        conversation_id: conversationId || '',
        dataset_id: currentDataset === 'all' ? '' : currentDataset
      });
      
      if (response.success) {
        toast({
          title: 'Feedback Submitted',
          description: 'Thank you for your feedback!'
        });
        
        // If it was negative feedback, offer to improve
        if (feedbackType === 'negative' && additionalComments) {
          // Find the user message that preceded this one
          const userMessage = messages.find(msg => {
            return msg.type === 'user' && new Date(msg.timestamp) < new Date(message.timestamp);
          });
          
          if (userMessage) {
            evaluateResponse(messageId, userMessage.content, message.content);
          }
        }
      } else {
        toast({
          title: 'Error',
          description: 'Failed to submit feedback',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
      toast({
        title: 'Error',
        description: 'Failed to submit feedback',
        variant: 'destructive'
      });
    }
  }, [messages, currentDataset, conversationId, toast, evaluateResponse]);

  // Open feedback dialog for a message
  const openFeedbackDialog = (messageId: string) => {
    setCurrentFeedbackMessageId(messageId);
    setShowFeedbackDialog(true);
  };
  
  // Replace current content with improved response
  const applyImprovedResponse = () => {
    if (!currentFeedbackMessageId || !improvedResponse) return;
    
    const message = messages.find(msg => msg.id === currentFeedbackMessageId);
    if (message) {
      updateMessage(currentFeedbackMessageId, {
        ...message,
        content: improvedResponse
      });
    }
    
    setShowImprovedResponseDialog(false);
    setImprovedResponse('');
  };
  
  // Handle sending a message
  const handleSendMessage = useCallback(async () => {
    if (!input.trim() || isProcessing) return;
    
    // Add user message to chat
    const userMessageId = Date.now().toString();
    addMessage({
      id: userMessageId,
      type: 'user',
      content: input,
      timestamp: new Date(),
      metadata: {
        conversationId: conversationId
      }
    });
    
    // Clear input and add to history
    setInputHistory(prev => [input, ...prev].slice(0, 50));
    setInput('');
    
    // Set processing state
    setIsProcessing(true);
    if (processingCallback) {
      processingCallback(true);
    }
    
    try {
      // Use custom handler if provided
      if (onMessage) {
        onMessage(input, currentDataset, modelId);
        setIsProcessing(false);
        if (processingCallback) {
          processingCallback(false);
        }
        return;
      }
      
      // Generate assistant response
      const assistantMessageId = Date.now().toString();
      
      // Add placeholder message while generating
      const placeholderMessage: Message = {
        id: assistantMessageId,
        type: 'assistant',
        content: '...',
        metadata: {
          isLoading: true
        },
        timestamp: new Date()
      };
      
      addMessage(placeholderMessage);
      
      // Get chat history for context
      const chatHistory = messages
        .filter(msg => msg.type !== 'system' && !msg.metadata?.isError)
        .map(msg => ({
          role: msg.type as 'user' | 'assistant',
          content: msg.content
        }));
        
      // Determine if we're using all datasets or a specific one
      const isUsingAllDatasets = currentDataset === 'all';
      
      // Use the AI agent service to get a response
      const response = await aiAgentService.getAgentResponse({
        query: input,
        modelId: modelId,
        // If 'all' is selected, we'll set use_all_datasets to true
        // and leave datasetId undefined
        datasetId: isUsingAllDatasets ? undefined : currentDataset,
        use_all_datasets: isUsingAllDatasets,
        chatHistory: chatHistory,
        context: {}
      });
      
      if (response.success && response.data) {
        // Generate assistant message ID
        const assistantMessageId = Date.now().toString();
        
        // Cast response.data to our AIResponse type
        const aiResponse = response.data as AIResponse;
        
        // Add assistant response
        addMessage({
          id: assistantMessageId,
          type: 'assistant',
          content: aiResponse.answer || aiResponse.text || aiResponse.response,
          metadata: {
            confidence: aiResponse.confidence || 0.9,
            sources: aiResponse.sources || aiResponse.context?.sources,
            insights: aiResponse.insights || [],
            dataset: currentDataset,
            timestamp: new Date().toISOString(),
            modelId: modelId,
            conversationId: conversationId
          },
          timestamp: new Date()
        });
        
        // Auto-evaluate the response quality if we have a conversation ID
        if (conversationId) {
          setTimeout(() => {
            evaluateResponse(
              assistantMessageId,
              input,
              aiResponse.answer || aiResponse.text || aiResponse.response
            );
          }, 1000);
        }
      } else {
        // Add error message
        addMessage({
          id: Date.now().toString(),
          type: 'assistant',
          content: 'Sorry, I encountered an error processing your request. Please try again.',
          metadata: {
            isError: true,
            dataset: currentDataset,
            timestamp: new Date().toISOString()
          },
          timestamp: new Date()
        });
        
        toast({
          title: 'Error',
          description: response.error || 'Failed to get AI response',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      addMessage({
        id: Date.now().toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        metadata: {
          isError: true,
          dataset: currentDataset,
          timestamp: new Date().toISOString()
        },
        timestamp: new Date()
      });
      
      toast({
        title: 'Error',
        description: 'Failed to get AI response',
        variant: 'destructive'
      });
    } finally {
      setIsProcessing(false);
      if (processingCallback) {
        processingCallback(false);
      }
    }
  }, [input, isProcessing, addMessage, conversationId, setInputHistory, currentDataset, modelId, processingCallback, onMessage, evaluateResponse, toast, messages]);
  
  // Apply a suggested question
  const applySuggestion = useCallback((text: string) => {
    setInput(text);
    // Auto-submit if not already processing
    if (!isProcessing) {
      handleSendMessage();
    }
  }, [handleSendMessage, isProcessing]);
  
  // Enhance the existing handleSetDataset with additional functionality
  useEffect(() => {
    // Log the dataset selection for debugging
    console.log(`Dataset selected: ${currentDataset === 'all' ? 'All Datasets' : currentDataset}`);
    
    // Reset suggestions when dataset changes
    setSuggestions([]);
  }, [currentDataset]);
  
  // Handle keyboard shortcuts
  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);
  
  return (
    <>
      {/* User Feedback Dialog */}
      <Dialog open={showFeedbackDialog} onOpenChange={setShowFeedbackDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Provide Feedback</DialogTitle>
            <DialogDescription>
              Help us improve our responses by rating the quality and providing feedback.
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4 space-y-4">
            <div className="flex justify-center py-2">
              <Rating
                value={feedbackRating}
                onValueChange={setFeedbackRating}
              />
            </div>
            
            <div className="space-y-2">
              <h4 className="text-sm font-medium">What could be improved?</h4>
              <div className="flex flex-wrap gap-2">
                {['Accuracy', 'Clarity', 'Relevance', 'Completeness', 'Helpfulness'].map(area => (
                  <Badge
                    key={area}
                    variant={feedbackImprovementAreas.includes(area) ? 'default' : 'outline'}
                    className="cursor-pointer"
                    onClick={() => {
                      setFeedbackImprovementAreas(prev => 
                        prev.includes(area) 
                          ? prev.filter(a => a !== area)
                          : [...prev, area]
                      );
                    }}
                  >
                    {area}
                  </Badge>
                ))}
              </div>
            </div>
            
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Additional comments</h4>
              <Textarea
                placeholder="What would make this response better?"
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowFeedbackDialog(false)}>
              Cancel
            </Button>
            <Button onClick={() => submitFeedback(currentFeedbackMessageId || '', feedbackRating < 3 ? 'negative' : 'positive', feedbackText)}>
              Submit Feedback
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Improved Response Dialog */}
      <Dialog open={showImprovedResponseDialog} onOpenChange={setShowImprovedResponseDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Improved Response</DialogTitle>
            <DialogDescription>
              We've generated an improved version of the response based on feedback and evaluation.
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4 space-y-4">
            <div className="p-4 border rounded-md bg-secondary/20">
              {improvedResponse}
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowImprovedResponseDialog(false)}>
              Cancel
            </Button>
            <Button onClick={applyImprovedResponse}>
              Use This Response
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      <Card className={`flex flex-col h-full ${className}`}>
      <CardHeader className="px-4 py-3 border-b">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">{title}</CardTitle>
            <p className="text-sm text-muted-foreground">{subtitle}</p>
          </div>
          
          <div className="flex items-center space-x-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Settings className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => clearHistory()}>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  <span>Clear History</span>
                </DropdownMenuItem>
                {conversationId && (
                  <>
                    <DropdownMenuItem>
                      <Sparkles className="mr-2 h-4 w-4" />
                      <span>Conversation ID: {conversationId.substring(0, 8)}...</span>
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-2 mt-3">
          {showDatasetSelector && (
            <div className="flex-1">
              <DatasetSelector
                datasets={availableDatasets}
                selectedDataset={currentDataset}
                onDatasetChange={setCurrentDataset}
                isLoading={isLoadingDatasets}
              />
            </div>
          )}
          
          <div className="flex-1">
              <ModelSelector
                models={availableModels}
                selectedModel={modelId}
                onModelChange={setModelId}
                isLoading={isLoadingModels}
              />
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 p-0 overflow-hidden">
        <ScrollArea className="h-full" ref={scrollAreaRef}>
          <div className="p-4">
            <MessageList
              messages={messages}
              isLoading={isHistoryLoading || isProcessing}
              expandedMessageIds={expandedMessageIds}
              toggleMessageExpanded={(id) => setExpandedMessageIds(prev => 
                prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
              )}
              onMessageAction={(action, messageId) => {
                // Handle different message actions
                switch(action) {
                  case 'feedback':
                    openFeedbackDialog(messageId);
                    break;
                  case 'improve':
                    getImprovedResponse(messageId);
                    break;
                  default:
                    console.log(`Unhandled message action: ${action}`);
                }
              }}
            />
            
            {messages.length === 0 && !isHistoryLoading && (
              <div className="flex flex-col items-center justify-center h-[300px] text-center p-4">
                <Bot className="h-12 w-12 mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">How can I help you today?</h3>
                <p className="text-sm text-muted-foreground max-w-md mb-6">
                  Ask me anything about your data or use the suggestions below to get started.
                </p>
                
                {suggestions.length > 0 && (
                  <ChatSuggestions 
                    suggestions={suggestions} 
                    onSuggestionClick={applySuggestion}
                  />
                )}
              </div>
            )}
            
            {isProcessing && (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin mr-2" />
                <span className="text-sm">Generating response...</span>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
      
      <CardFooter className="p-4 border-t">
        <form 
          className="flex w-full items-center space-x-2" 
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
        >
          <Input
            className="flex-1"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={isProcessing}
          />
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  type="submit" 
                  size="icon" 
                  disabled={isProcessing || !input.trim()}
                >
                  {isProcessing ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <SendHorizontal className="h-4 w-4" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Send message</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </form>
      </CardFooter>
    </Card>
    </>
  );
};

export { ChatInterface, ChatSuggestion };
