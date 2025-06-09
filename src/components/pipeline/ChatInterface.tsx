import React, { useState, useRef, useEffect } from 'react';
import { Send, Search, RefreshCw, Sparkles, AlertCircle, Brain } from 'lucide-react'; // Added Brain icon
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { ScrollArea } from '../ui/scroll-area';
import { Input } from '../ui/input';
import { Separator } from '@/components/ui/separator';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Avatar } from '@/components/ui/avatar';
import { CardFooter } from '@/components/ui/card';

/**
 * Message interface defining the structure of chat messages
 * 
 * AI usage: The message type and metadata structure supports
 * AI-generated responses with confidence scores and source attribution
 */
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: ChatMessageMetadata;
}

interface ChatMessageMetadata {
  confidence?: number;
  sources?: string[];
  isError?: boolean;
  processing_time?: number;
  tokens_used?: number;
  embedding_count?: number;
  used_agent?: string;
  context_count?: number;
  context_sample?: Array<{ text: string; similarity: number }>;
  isThinking?: boolean;
}

/**
 * ChatInterface Component: Provides an AI-powered chat interface for data exploration
 * 
 * AI Implementation:
 * - Connects to a backend AI service through the pythonApi.askQuestion method
 * - Uses vectorized data representations for semantic search capabilities
 * - Presents AI confidence scores and source attributions for transparency
 * - Handles AI errors gracefully with fallbacks
 */
interface ChatContext {
  currentDataset?: any; // Consider defining a proper type for dataset
  pipelineStatus?: 'idle' | 'processing' | 'completed' | 'error';
  activeTab?: string;
  businessRules?: any[]; // Consider defining a proper type for business rules
}

interface ChatInterfaceProps {
  datasetId?: string;
  context?: ChatContext;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ datasetId, context = {} }) => {
  // Use context to enhance the chat experience
  const systemMessage = React.useMemo(() => {
    if (!context) return '';
    
    let message = 'Current context:\n';
    if (context.currentDataset) {
      message += `- Dataset: ${context.currentDataset.name || 'Unnamed dataset'}\n`;
    }
    if (context.pipelineStatus) {
      message += `- Pipeline Status: ${context.pipelineStatus}\n`;
    }
    if (context.activeTab) {
      message += `- Active Tab: ${context.activeTab}\n`;
    }
    if (context.businessRules?.length) {
      message += `- Active Business Rules: ${context.businessRules.length}\n`;
    }
    
    return message;
  }, [context]);
  
  // Update system message when context changes
  useEffect(() => {
    if (systemMessage) {
      setMessages(prev => [
        {
          id: 'system-context',
          role: 'system',
          content: systemMessage,
          timestamp: new Date()
        },
        ...prev.filter(msg => msg.id !== 'system-context')
      ]);
    }
  }, [systemMessage]);
  
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hi there! I\'m your AI assistant for data pipeline operations. How can I help you today?',
      timestamp: new Date()
    },
    {
      id: '2',
      role: 'system',
      content: 'I can answer questions about your loaded datasets using vector database technology and AI-powered schema detection.',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeDataset, setActiveDataset] = useState<string>(datasetId || '');
  const [availableDatasets, setAvailableDatasets] = useState<Array<{id: string, name: string}>>([]);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (datasetId) {
      setActiveDataset(datasetId);
      // In a real app, you would fetch available datasets here
      const fetchDatasets = async () => {
        try {
          // Simulate fetching datasets
          setAvailableDatasets([
            { id: '1', name: 'Sales Data' },
            { id: '2', name: 'Customer Data' },
          ]);
        } catch (err) {
          console.error('Error fetching datasets:', err);
          setMessages(prev => [...prev, {
            id: `error-${Date.now()}`,
            role: 'system',
            content: 'Failed to load available datasets. Please try again later.',
            metadata: { isError: true },
            timestamp: new Date()
          }]);
        }
      };
      
      fetchDatasets();
    }
  }, [datasetId, activeDataset]);
  
  /**
   * Send a user message to the AI assistant and handle the response
   *
   * 1. User question is captured and sent to the backend
   * 2. Backend vector DB retrieves relevant context from datasets
   * 3. AI model generates an answer based on retrieved context
   * 4. Response with confidence scores and metadata is displayed
   */
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    
    try {
      // Here you would typically call your API to get a response
      // For now, we'll simulate a response
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const botMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `I received your message: "${input}"`,
        timestamp: new Date(),
        metadata: {
          processing_time: 500,
          tokens_used: 20
        },
      };
      
      setMessages(prev => [...prev, botMessage]);
      
      // Simulate API response handling
      try {
        const mockData = {
          success: true,
          text: `I received your message: "${input}"`,
          confidence: 0.8,
          processing_time: 500,
          tokens_used: 20
        };
        
        if (mockData.success) {
          // Add AI response
          const aiMessage: ChatMessage = {
            id: Date.now().toString(),
            role: 'assistant',
            content: mockData.text || 'I found some information that might help.',
            metadata: {
              confidence: mockData.confidence || 0.8,
              processing_time: mockData.processing_time,
              tokens_used: mockData.tokens_used
            },
            timestamp: new Date()
          };
          
          setMessages(prev => [...prev, aiMessage]);
        } else {
          // Handle error in response
          const errorMessage: ChatMessage = {
            id: `error-${Date.now()}`,
            role: 'system',
            content: 'Sorry, I encountered an issue while processing your request.',
            metadata: { isError: true },
            timestamp: new Date()
          };
          setMessages(prev => [...prev, errorMessage]);
        }
      } catch (err) {
        console.error('Error processing message:', err);
        const errorMessage: ChatMessage = {
          id: `error-${Date.now()}`,
          role: 'system',
          content: err instanceof Error ? err.message : 'An unexpected error occurred. Please try again.',
          metadata: { isError: true },
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Error processing message:', error);
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'system',
        content: error instanceof Error ? error.message : 'An unexpected error occurred. Please try again.',
        metadata: { isError: true },
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Scroll to bottom when messages change
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);
  
  return (
    <Card className="h-[calc(100vh-16rem)] flex flex-col">
      <CardHeader className="px-4 py-3 border-b">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Avatar className="h-8 w-8 bg-blue-500">
              <Brain className="h-5 w-5 text-white" />
            </Avatar>
            <CardTitle className="text-md">Vector DB AI Assistant</CardTitle>
          </div>
          {availableDatasets.length > 0 && (
            <Select value={activeDataset} onValueChange={setActiveDataset}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Select dataset" />
              </SelectTrigger>
              <SelectContent>
                {availableDatasets.map(dataset => (
                  <SelectItem key={dataset.id} value={dataset.id}>{dataset.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <div className="flex space-x-1">
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
                    onClick={() => {
                      setMessages([
                        {
                          id: '1',
                          role: 'assistant',
                          content: 'Hi there! I\'m your AI assistant for data pipeline operations. How can I help you today?',
                          timestamp: new Date()
                        },
                        {
                          id: '2',
                          role: 'system',
                          content: 'I can answer questions about your loaded datasets using vector database technology and AI-powered schema detection.',
                          timestamp: new Date()
                        }
                      ]);
                    }}
                  >
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Reset conversation</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-grow p-0 overflow-hidden">
        <ScrollArea className="h-full p-4" ref={scrollAreaRef}>
          <div className="space-y-4">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${
                message.role === 'user' ? 'justify-end' : 
                message.role === 'system' ? 'justify-center' : 'justify-start'
              }`}>
                <div 
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.role === 'user' 
                      ? 'bg-blue-500 text-white' 
                      : message.role === 'system'
                        ? 'bg-gray-200 text-gray-800'
                        : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {message.role === 'assistant' && (
                    <div className="flex items-center text-blue-600 text-xs mb-1 space-x-1">
                      <Sparkles className="h-3 w-3" />
                      <span>AI Assistant</span>
                    </div>
                  )}
                  
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  
                  {/* Show confidence and sources for AI responses */}
                  {message.role === 'assistant' && message.metadata?.confidence && (
                    <div className="mt-2 text-xs text-gray-500 border-t border-gray-200 pt-1">
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
                      
                      {message.metadata.processing_time && (
                        <div className="mt-1 text-xs text-gray-400">
                          <span>Processing time: {message.metadata.processing_time.toFixed(2)}s</span>
                          {message.metadata.tokens_used && (
                            <span className="ml-2">• Tokens: {message.metadata.tokens_used}</span>
                          )}
                          {message.metadata.embedding_count && (
                            <span className="ml-2">• Embeddings: {message.metadata.embedding_count}</span>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                  
                  <p className="text-xs mt-1 opacity-70">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-800 rounded-lg p-3">
                  <div className="flex space-x-1">
                    <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
      
      <Separator />
      
      <CardFooter className="p-3">
        <form onSubmit={handleSendMessage}>
          <div className="flex w-full items-center space-x-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              className="flex-1"
              disabled={isLoading}
            />
            <Button type="submit" size="icon" disabled={isLoading}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </form>
      </CardFooter>
    </Card>
  );
};

export default ChatInterface;
