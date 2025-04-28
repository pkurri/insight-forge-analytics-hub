import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  SendHorizontal, Bot, RefreshCw, Search, AlertCircle, 
  Settings, Loader2, ThumbsUp, ThumbsDown, Sparkles, 
  MessageSquareWarning, MessageSquare
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Textarea } from '@/components/ui/textarea';
import { Rating } from '@/components/ui/rating';
import { useChatHistory } from '@/hooks/useChatHistory';
import { useDatasetContext } from '@/hooks/useDatasetContext';
import { api } from '@/api/api';
import { useToast } from '@/hooks/use-toast';

// Import our modular components
import MessageList from './MessageList';
import ModelSelector from './ModelSelector';
import DatasetSelector from './DatasetSelector';
import ChatSuggestions, { ChatSuggestion } from './ChatSuggestions';
// Use all AI services via the central API object
import { AIModel, modelService } from '@/api/services/ai/modelService';
import { embeddingService } from '@/api/services/ai/embeddingService';
import { aiAgentService } from '@/api/services/ai/aiAgentService';

export interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: {
    confidence?: number;
    sources?: string[];
    isError?: boolean;
    dataset?: string;
    timestamp?: string;
    modelId?: string;
    insights?: string[];
    context?: any;
    evaluationId?: string;
    evaluationScore?: number;
    improvedResponse?: string;
    userRating?: number;
    userFeedback?: string;
    conversationId?: string;
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
  const { datasets, activeDataset, setActiveDataset } = useDatasetContext();
  
  // Local state for handling active dataset if context not available
  const [localActiveDataset, setLocalActiveDataset] = useState<string>(defaultDataset || 'all');
  
  // Use the context dataset if available, otherwise use local state
  const currentDataset = activeDataset || localActiveDataset;
  const handleSetDataset = setActiveDataset || setLocalActiveDataset;
  
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
  } = useChatHistory(currentDataset) as any;
  
  // Chat interface state
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [inputHistory, setInputHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [expandedMessageIds, setExpandedMessageIds] = useState<string[]>([]);
  
  // OpenEvals state
  const [evaluatingMessage, setEvaluatingMessage] = useState(false);
  const [improvingMessage, setImprovingMessage] = useState(false);
  const [showFeedbackDialog, setShowFeedbackDialog] = useState(false);
  const [currentFeedbackMessageId, setCurrentFeedbackMessageId] = useState<string | null>(null);
  const [feedbackRating, setFeedbackRating] = useState(3);
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackImprovementAreas, setFeedbackImprovementAreas] = useState<string[]>([]);
  const [showImprovedResponseDialog, setShowImprovedResponseDialog] = useState(false);
  const [improvedResponse, setImprovedResponse] = useState('');
  
  // Model and dataset selection state
  const [modelId, setModelId] = useState(selectedModel || 'mistral-7b-instruct');
  const [availableModels, setAvailableModels] = useState<any[]>([]); // Use type from api.modelService if available
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [availableDatasets, setAvailableDatasets] = useState<Array<{id: string, name: string, rows: number, columns: number, lastUpdated: string}>>([]);
  const [isLoadingDatasets, setIsLoadingDatasets] = useState(false);
  
  // References and utilities
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  
  // Update model ID when prop changes
  useEffect(() => {
    if (selectedModel && selectedModel !== modelId) {
      setModelId(selectedModel);
    }
  }, [selectedModel, modelId]);
  
  // Update processing status to parent component if callback provided
  useEffect(() => {
    if (processingCallback) {
      processingCallback(isProcessing);
    }
  }, [isProcessing, processingCallback]);
  
  // Fetch available models and datasets on mount
  useEffect(() => {
    const fetchModels = async () => {
      setIsLoadingModels(true);
      try {
        const response = await modelService.getAvailableModels('chat');
        if (response.success && response.data) {
          setAvailableModels(response.data);
          // Set default model if none selected
          if (!modelId && response.data.length > 0) {
            setModelId(response.data[0].id);
          }
        }
      } catch (error) {
        console.error('Error fetching models:', error);
        toast({
          title: 'Error',
          description: 'Failed to load AI models',
          variant: 'destructive'
        });
      } finally {
        setIsLoadingModels(false);
      }
    };
    
    const fetchDatasets = async () => {
      setIsLoadingDatasets(true);
      try {
        const response = await api.datasets.getDatasets();
        if (response.success && response.data) {
          const formattedDatasets = response.data.map(ds => ({
            id: ds.id,
            name: ds.name,
            rows: ds.rows,
            columns: ds.columns || 0,
            lastUpdated: ds.updated_at || new Date().toISOString()
          }));
          setAvailableDatasets(formattedDatasets);
        }
      } catch (error) {
        console.error('Error fetching datasets:', error);
      } finally {
        setIsLoadingDatasets(false);
      }
    };
    
    fetchModels();
    fetchDatasets();
  }, [modelId, toast]);

  // Scroll to bottom when messages change
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTo({
        top: scrollAreaRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages, isProcessing]);
  
  // Toggle message expanded state
  const toggleMessageExpanded = useCallback((id: string) => {
    setExpandedMessageIds(prev => 
      prev.includes(id) ? prev.filter(mid => mid !== id) : [...prev, id]
    );
  }, []);
  
  // Evaluate an AI response with OpenEvals
  const evaluateResponse = async (messageId: string, query: string, response: string) => {
    setEvaluatingMessage(true);
    try {
      const result = await aiAgentService.evaluateResponse(
        query,
        response,
        conversationId, // From useChatHistory hook
        messageId
      );
      
      if (result.success && result.data) {
        // Update message with evaluation results
        const message = messages.find(msg => msg.id === messageId);
        if (message) {
          updateMessage(messageId, {
            ...message,
            metadata: {
              ...message.metadata,
              evaluationId: result.data.id,
              evaluationScore: result.data.average_score
            }
          });
        }
        
        // Show toast with result
        let evaluationStatus = 'neutral';
        if (result.data.status === 'excellent') evaluationStatus = 'default';
        else if (['fail', 'error', 'improvement_needed'].includes(result.data.status)) evaluationStatus = 'destructive';
        
        toast({
          title: `Response Quality: ${Math.round(result.data.average_score)}%`,
          description: `Evaluation complete: ${result.data.status}`,
          variant: evaluationStatus as any
        });
      }
    } catch (error) {
      console.error('Error evaluating response:', error);
      toast({
        title: 'Evaluation Error',
        description: error instanceof Error ? error.message : 'Failed to evaluate response',
        variant: 'destructive'
      });
    } finally {
      setEvaluatingMessage(false);
    }
  };
  
  // Get improved response from OpenEvals
  const getImprovedResponse = async (messageId: string) => {
    setImprovingMessage(true);
    try {
      // Find the message and query
      const assistantMessage = messages.find(msg => msg.id === messageId);
      if (!assistantMessage) throw new Error('Message not found');
      
      // Find the user message that preceded this assistant message
      const assistantIndex = messages.findIndex(msg => msg.id === messageId);
      if (assistantIndex <= 0) throw new Error('User query not found');
      
      const userMessage = messages[assistantIndex - 1];
      if (userMessage.type !== 'user') throw new Error('Previous message is not a user query');
      
      // Get improved response
      const result = await aiAgentService.getImprovedResponse(
        userMessage.content,
        assistantMessage.content,
        conversationId,
        assistantMessage.metadata?.evaluationId
      );
      
      if (result.success && result.data) {
        setImprovedResponse(result.data.improved_response);
        setShowImprovedResponseDialog(true);
        
        // Update message with improved response
        updateMessage(messageId, {
          ...assistantMessage,
          metadata: {
            ...assistantMessage.metadata,
            improvedResponse: result.data.improved_response,
            evaluationScore: result.data.improved_evaluation.average_score
          }
        });
        
        toast({
          title: 'Response Improved',
          description: `Quality improvement: +${Math.round(result.data.improvement_delta.average)}%`,
          variant: 'default'
        });
      }
    } catch (error) {
      console.error('Error improving response:', error);
      toast({
        title: 'Improvement Error',
        description: error instanceof Error ? error.message : 'Failed to improve response',
        variant: 'destructive'
      });
    } finally {
      setImprovingMessage(false);
    }
  };
  
  // Handle submitting user feedback
  const submitFeedback = async () => {
    if (!currentFeedbackMessageId) return;
    
    try {
      const result = await aiAgentService.submitUserFeedback(
        conversationId,
        currentFeedbackMessageId,
        {
          rating: feedbackRating,
          feedback_text: feedbackText,
          improvement_areas: feedbackImprovementAreas
        }
      );
      
      if (result.success && result.data) {
        // Update message with feedback
        const message = messages.find(msg => msg.id === currentFeedbackMessageId);
        if (message) {
          updateMessage(currentFeedbackMessageId, {
            ...message,
            metadata: {
              ...message.metadata,
              userRating: feedbackRating,
              userFeedback: feedbackText
            }
          });
        }
        
        // Check if there's an improved response from feedback
        if (result.data.improved_response) {
          setImprovedResponse(result.data.improved_response);
          setShowImprovedResponseDialog(true);
        }
        
        toast({
          title: 'Feedback Submitted',
          description: 'Thank you for your feedback!',
          variant: 'default'
        });
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
      toast({
        title: 'Feedback Error',
        description: error instanceof Error ? error.message : 'Failed to submit feedback',
        variant: 'destructive'
      });
    } finally {
      setShowFeedbackDialog(false);
      setFeedbackRating(3);
      setFeedbackText('');
      setFeedbackImprovementAreas([]);
      setCurrentFeedbackMessageId(null);
    }
  };
  
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
  const handleSendMessage = async () => {
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
    setHistoryIndex(-1);
    
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
      
      // Generate embeddings for semantic search context
      let searchContext = {};
      try {
        const embeddingResponse = await embeddingService.generateEmbeddings({ 
          text: input,
          model: 'sentence-transformers/all-MiniLM-L6-v2'
        });
        
        if (embeddingResponse.success && embeddingResponse.data) {
          // Search for similar content if dataset is selected
          if (currentDataset && currentDataset !== 'all') {
            const searchResponse = await embeddingService.searchSimilarVectors(
              input, 
              currentDataset, 
              3
            );
            
            if (searchResponse.success && searchResponse.data) {
              searchContext = {
                similarContent: searchResponse.data.results,
                embeddingModel: embeddingResponse.data.model
              };
            }
          }
        }
      } catch (error) {
        console.error('Error with embeddings:', error);
        // Continue without embeddings if there's an error
      }
      
      // Call AI service
      const response = await api.getAiAssistantResponse(input, {
        dataset_id: currentDataset === 'all' ? undefined : currentDataset,
        model_id: modelId,
        context: searchContext
      });
      
      if (response.success && response.data) {
        // Generate assistant message ID
        const assistantMessageId = Date.now().toString();
        
        // Add assistant response
        addMessage({
          id: assistantMessageId,
          type: 'assistant',
          content: response.data.answer || response.data.text || response.data.response,
          metadata: {
            confidence: response.data.confidence || 0.9,
            sources: response.data.sources || response.data.context?.sources,
            insights: response.data.insights,
            dataset: currentDataset,
            timestamp: response.data.timestamp,
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
              response.data.answer || response.data.text || response.data.response
            );
          }, 1000);
        }
      } else {
        // Add error message
        addMessage({
          id: Date.now().toString(),
          type: 'assistant',
          content: `I'm sorry, I couldn't process your request. ${response.error || 'Please try again later.'}`,
          metadata: {
            isError: true,
            dataset: currentDataset
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
        content: `I'm sorry, an error occurred while processing your request. Please try again later.`,
        metadata: {
          isError: true,
          dataset: currentDataset
        },
        timestamp: new Date()
      });
      
      toast({
        title: "Connection Error",
        description: error instanceof Error ? error.message : "Failed to connect to AI service",
        variant: "destructive"
      });
    } finally {
      // Reset processing state
      setIsProcessing(false);
      if (processingCallback) {
        processingCallback(false);
      }
    }
  };
  
  // Apply a suggested question
  const applySuggestion = useCallback((text: string) => {
    setInput(text);
    // Optionally auto-send
    // setTimeout(() => handleSendMessage(), 100);
  }, []);
  
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
            <DialogTitle>Rate this response</DialogTitle>
            <DialogDescription>
              Your feedback helps us improve our AI responses.
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
            <Button onClick={submitFeedback}>
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
        
        <div className="flex flex-col sm:flex-row gap-3 mt-3">
          {/* Model Selector */}
          <ModelSelector
            models={availableModels}
            selectedModel={modelId}
            onModelChange={setModelId}
            isLoading={isLoadingModels}
            className="flex-grow"
          />
          
          {/* Dataset Selector */}
          {showDatasetSelector && (
            <DatasetSelector
              datasets={availableDatasets}
              selectedDataset={currentDataset}
              onDatasetChange={handleSetDataset}
              isLoading={isLoadingDatasets}
              className="flex-grow"
            />
          )}
        </div>
      </CardHeader>
      
      <CardContent className="flex-grow p-0 overflow-hidden">
        <ScrollArea className="h-full max-h-[calc(100vh-13rem)]" ref={scrollAreaRef}>
          <div className="p-4">
            {messages.length === 0 && !isHistoryLoading ? (
              <div className="flex flex-col items-center justify-center h-full py-12 text-center">
                <Bot className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">How can I help you?</h3>
                <p className="text-sm text-muted-foreground max-w-md mb-8">
                  Ask me anything about your data. I can analyze trends, explain patterns, and help you explore your datasets.
                </p>
                {suggestions.length > 0 && (
                  <ChatSuggestions 
                    suggestions={suggestions}
                    onSuggestionClick={applySuggestion}
                    layout="grid"
                    className="w-full max-w-lg"
                  />
                )}
              </div>
            ) : (
              <MessageList
                messages={messages}
                isLoading={isProcessing}
                expandedMessageIds={expandedMessageIds}
                toggleMessageExpanded={toggleMessageExpanded}
              />
            )}
          </div>
        </ScrollArea>
      </CardContent>
      <Separator />
      <CardFooter className="p-4 pt-2">
        <form 
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex flex-col w-full space-y-4"
        >
          {suggestions.length > 0 && messages.length > 0 && (
            <ChatSuggestions 
              suggestions={suggestions}
              onSuggestionClick={applySuggestion}
              layout="flow"
              maxSuggestions={4}
            />
          )}
          <div className="flex space-x-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask a question about your data..."
              className="flex-grow"
              disabled={isProcessing}
            />
            <Button 
              type="submit"
              size="icon"
              disabled={!input.trim() || isProcessing}
            >
              {isProcessing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <SendHorizontal className="h-4 w-4" />
              )}
            </Button>
          </div>
        </form>
      </CardFooter>
    </Card>
    </>
  );
};

export default ChatInterface;
