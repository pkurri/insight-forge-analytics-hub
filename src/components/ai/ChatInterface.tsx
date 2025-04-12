
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  SendHorizontal, Bot, RefreshCw, Search, AlertCircle, ArrowUp, 
  Clock, XCircle, Settings, Lightbulb, ChevronDown, ChevronUp 
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';
import { useChatHistory } from '@/hooks/useChatHistory';
import { useDatasetContext } from '@/hooks/useDatasetContext';
import { api } from '@/api/api';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';

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
  };
  timestamp: Date;
}

export interface ChatSuggestion {
  id: string;
  text: string;
  category?: string;
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
 * Reusable Chat Interface component that connects to Vector DB and Hugging Face models
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
    setMessages,
    addMessage,
    clearHistory,
    isLoading: isHistoryLoading
  } = useChatHistory(currentDataset);
  
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [inputHistory, setInputHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [modelId, setModelId] = useState(selectedModel);
  const [expandedMessageIds, setExpandedMessageIds] = useState<string[]>([]);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  
  // Toggle insight expansion
  const toggleInsightExpansion = (messageId: string) => {
    setExpandedMessageIds(prev => 
      prev.includes(messageId) 
        ? prev.filter(id => id !== messageId) 
        : [...prev, messageId]
    );
  };

  // Check if insights are expanded for a message
  const isInsightExpanded = (messageId: string) => {
    return expandedMessageIds.includes(messageId);
  };
  
  // Update model selection when prop changes
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
  
  /**
   * Handle sending a message to the AI assistant
   */
  const handleSendMessage = async () => {
    if (!input.trim() || isProcessing) return;
    
    // Add user message to display
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: input,
      timestamp: new Date()
    };
    
    // Add to input history for up/down arrow navigation
    setInputHistory(prev => [...prev, input]);
    setHistoryIndex(-1);
    
    // Add message to chat history
    addMessage(userMessage);
    
    // Clear input and show typing indicator
    setInput('');
    setIsTyping(true);
    setIsProcessing(true);
    
    try {
      // If external handler is provided, use it
      if (onMessage) {
        onMessage(input, currentDataset, modelId);
      } else {
        // Otherwise use default API call
        const response = await api.askQuestion(currentDataset, input, {
          modelId: modelId
        });
        
        if (response.success && response.data) {
          const insights = response.data.context?.map((ctx: any) => {
            if (ctx.insight) return ctx.insight;
            if (ctx.analysis) return `Analysis: ${ctx.analysis}`;
            if (ctx.distribution) return `Distribution: ${ctx.distribution}`;
            return null;
          }).filter(Boolean);
          
          const assistantMessage: Message = {
            id: `assistant-${Date.now()}`,
            type: 'assistant',
            content: response.data.answer,
            metadata: {
              confidence: response.data.confidence,
              sources: response.data.context?.map((ctx: any) => ctx.column || ctx.analysis),
              dataset: currentDataset,
              timestamp: new Date().toISOString(),
              modelId: modelId,
              insights: insights || [],
              context: response.data.context || []
            },
            timestamp: new Date()
          };
          
          addMessage(assistantMessage);
        } else {
          // Handle error response
          const errorMessage: Message = {
            id: `error-${Date.now()}`,
            type: 'system',
            content: response.error || 'Sorry, I encountered an error processing your question.',
            metadata: { isError: true },
            timestamp: new Date()
          };
          
          addMessage(errorMessage);
          
          toast({
            title: "Error processing request",
            description: response.error || "An unexpected error occurred",
            variant: "destructive"
          });
        }
      }
    } catch (error) {
      // Handle exception
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        type: 'system',
        content: 'Sorry, there was a problem connecting to the AI service.',
        metadata: { isError: true },
        timestamp: new Date()
      };
      
      addMessage(errorMessage);
      
      toast({
        title: "Connection Error",
        description: "Failed to connect to AI service",
        variant: "destructive"
      });
    } finally {
      setIsTyping(false);
      setIsProcessing(false);
    }
  };
  
  /**
   * Handle keyboard shortcuts for the chat interface
   */
  const handleKeyPress = (e: React.KeyboardEvent) => {
    // Send message on Enter (without shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
    
    // Navigate input history with up/down arrows
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (historyIndex < inputHistory.length - 1) {
        const newIndex = historyIndex + 1;
        setHistoryIndex(newIndex);
        setInput(inputHistory[inputHistory.length - 1 - newIndex]);
      }
    }
    
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1;
        setHistoryIndex(newIndex);
        setInput(inputHistory[inputHistory.length - 1 - newIndex]);
      } else if (historyIndex === 0) {
        setHistoryIndex(-1);
        setInput('');
      }
    }
  };
  
  /**
   * Apply a suggested message to the input field
   */
  const applySuggestion = useCallback((suggestion: string) => {
    setInput(suggestion);
  }, []);
  
  /**
   * Reset the chat conversation
   */
  const handleResetChat = useCallback(() => {
    // Add welcome message
    const welcomeMessage: Message = {
      id: '1',
      type: 'assistant',
      content: `Hi there! I'm your AI assistant for data operations. How can I help you today?`,
      timestamp: new Date()
    };
    
    const systemMessage: Message = {
      id: '2',
      type: 'system',
      content: 'I can answer questions about your loaded datasets using vector database technology and Hugging Face models.',
      timestamp: new Date()
    };
    
    clearHistory();
    setMessages([welcomeMessage, systemMessage]);
    
    toast({
      title: "Chat Reset",
      description: "The conversation has been reset",
    });
  }, [clearHistory, setMessages, toast]);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages, expandedMessageIds]);
  
  // Initialize chat with welcome message if empty
  useEffect(() => {
    if (messages.length === 0 && !isHistoryLoading) {
      handleResetChat();
    }
  }, [messages.length, handleResetChat, isHistoryLoading]);
  
  return (
    <Card className={`h-[calc(100vh-16rem)] flex flex-col ${className} max-h-[calc(100dvh-16rem)]`}>
      <CardHeader className="px-4 py-3 border-b">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Avatar className="h-8 w-8 bg-blue-500">
              <Bot className="h-5 w-5 text-white" />
            </Avatar>
            <div>
              <CardTitle className="text-md">{title}</CardTitle>
              <p className="text-xs text-muted-foreground">{subtitle}</p>
            </div>
          </div>
          <div className="flex space-x-1">
            {/* Dataset selector */}
            {showDatasetSelector && datasets && datasets.length > 0 && (
              <Select 
                value={currentDataset}
                onValueChange={handleSetDataset}
              >
                <SelectTrigger className="text-sm border rounded px-2 py-1 mr-2 w-40 md:w-48">
                  <SelectValue placeholder="Select dataset" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Datasets</SelectItem>
                  {datasets.map(dataset => (
                    <SelectItem key={dataset.id} value={dataset.id}>
                      {dataset.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <Search className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Search conversation</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-8 w-8"
                    onClick={handleResetChat}
                    disabled={isProcessing}
                  >
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Reset conversation</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            
            {/* Model selector dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Settings className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem className="text-xs text-muted-foreground" disabled>
                  Current model: {modelId.split('/').pop() || modelId}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>
      
      {/* Suggestions area */}
      {suggestions && suggestions.length > 0 && (
        <div className="px-4 py-2 border-b flex gap-2 overflow-x-auto">
          {suggestions.map(suggestion => (
            <Badge 
              key={suggestion.id} 
              variant="outline" 
              className="cursor-pointer hover:bg-muted whitespace-nowrap"
              onClick={() => applySuggestion(suggestion.text)}
            >
              {suggestion.text}
            </Badge>
          ))}
        </div>
      )}
      
      <CardContent className="flex-grow p-0 overflow-hidden">
        <ScrollArea className="h-full p-4" ref={scrollAreaRef}>
          <div className="space-y-4">
            {isHistoryLoading ? (
              // Loading skeleton
              <>
                <div className="flex justify-start">
                  <Skeleton className="h-16 w-3/4 rounded-lg" />
                </div>
                <div className="flex justify-end">
                  <Skeleton className="h-12 w-2/3 rounded-lg" />
                </div>
                <div className="flex justify-start">
                  <Skeleton className="h-24 w-4/5 rounded-lg" />
                </div>
              </>
            ) : (
              // Actual messages
              messages.map((message) => (
                <div key={message.id} className={`flex ${
                  message.type === 'user' ? 'justify-end' : 
                  message.type === 'system' ? 'justify-center' : 'justify-start'
                }`}>
                  <div 
                    className={`max-w-[90%] sm:max-w-[85%] md:max-w-[80%] rounded-lg p-3 ${
                      message.type === 'user' 
                        ? 'bg-primary text-primary-foreground' 
                        : message.type === 'system'
                          ? 'bg-muted text-foreground' 
                          : 'bg-accent text-accent-foreground'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    
                    {/* Show AI Insights for assistant responses */}
                    {message.type === 'assistant' && message.metadata?.insights && message.metadata.insights.length > 0 && (
                      <Collapsible
                        className="w-full mt-2 border-t border-border pt-1"
                        open={isInsightExpanded(message.id)}
                        onOpenChange={() => toggleInsightExpansion(message.id)}
                      >
                        <div className="flex items-center justify-between">
                          <p className="text-xs flex items-center gap-1 text-muted-foreground">
                            <Lightbulb className="h-3 w-3" />
                            <span>AI Insights</span>
                          </p>
                          <CollapsibleTrigger asChild>
                            <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                              {isInsightExpanded(message.id) ? (
                                <ChevronUp className="h-3 w-3" />
                              ) : (
                                <ChevronDown className="h-3 w-3" />
                              )}
                            </Button>
                          </CollapsibleTrigger>
                        </div>
                        <CollapsibleContent className="mt-2">
                          <div className="pl-4 border-l-2 border-muted space-y-1">
                            {message.metadata.insights.map((insight, index) => (
                              <p key={index} className="text-xs">
                                • {insight}
                              </p>
                            ))}
                          </div>
                        </CollapsibleContent>
                      </Collapsible>
                    )}
                    
                    {/* Show confidence and sources for AI responses */}
                    {message.type === 'assistant' && message.metadata?.confidence && (
                      <div className="mt-2 text-xs text-muted-foreground border-t border-border pt-1">
                        <div className="flex items-center">
                          <span>Confidence: {Math.round(message.metadata.confidence * 100)}%</span>
                          {message.metadata.confidence < 0.7 && (
                            <AlertCircle className="h-3 w-3 ml-1 text-amber-500" />
                          )}
                        </div>
                        
                        {message.metadata.sources && message.metadata.sources.length > 0 && (
                          <div className="mt-1">
                            <span>Sources: {message.metadata.sources.join(", ")}</span>
                          </div>
                        )}
                      </div>
                    )}
                    
                    <div className="flex justify-between items-center mt-1">
                      <p className="text-xs opacity-70">
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                      
                      {/* Show dataset if available */}
                      {message.metadata?.dataset && message.metadata.dataset !== "all" && (
                        <Badge variant="outline" className="text-xs">
                          {message.metadata.dataset}
                        </Badge>
                      )}
                      
                      {/* Show model if available */}
                      {message.metadata?.modelId && (
                        <Badge variant="outline" className="text-xs ml-1">
                          {message.metadata.modelId.split('/').pop() || 'AI'}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-accent text-accent-foreground rounded-lg p-3">
                  <div className="flex space-x-1">
                    <div className="h-2 w-2 bg-current rounded-full animate-bounce"></div>
                    <div className="h-2 w-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="h-2 w-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
      
      <Separator />
      
      <CardFooter className="p-3">
        <div className="flex w-full items-center space-x-2">
          <Input
            placeholder="Ask me about your dataset..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            className="flex-grow"
            disabled={isProcessing}
          />
          <Button 
            onClick={handleSendMessage} 
            disabled={!input.trim() || isProcessing} 
            size="icon"
          >
            <SendHorizontal className="h-4 w-4" />
          </Button>
        </div>
        
        {/* Input history indicator */}
        {historyIndex !== -1 && (
          <div className="absolute right-16 bottom-5 text-xs text-muted-foreground flex items-center">
            <Clock className="h-3 w-3 mr-1" />
            <span>{historyIndex + 1}/{inputHistory.length}</span>
          </div>
        )}
      </CardFooter>
    </Card>
  );
};

export default ChatInterface;
