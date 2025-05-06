import React, { useState, useEffect, useRef } from 'react';
import { SendHorizontal, Search, RefreshCw, AlertCircle, Sparkles, Brain } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useToast } from '@/hooks/use-toast';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { api } from '@/api/api';
import { Message, ChatProps } from '@/types/chat';

/**
 * ChatInterface Component: Provides an AI-powered chat interface for data exploration
 */
export interface ChatInterfaceProps extends ChatProps {}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ datasetId, modelId, agentId }) => {
  const { toast } = useToast();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Hi there! I\'m your AI assistant for data pipeline operations. How can I help you today?',
      timestamp: new Date()
    },
    {
      id: '2',
      type: 'system',
      content: 'I can answer questions about your loaded datasets using vector database technology and AI-powered schema detection.',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeDataset, setActiveDataset] = useState<string>(datasetId || '');
  const [availableDatasets, setAvailableDatasets] = useState<Array<{id: string, name: string}>>([]);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  
  // Fetch available datasets when component mounts
  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const response = await api.datasets.getDatasets();
        if (response.success && response.data) {
          setAvailableDatasets(response.data.map(dataset => ({
            id: dataset.id,
            name: dataset.name
          })));
          if (!activeDataset && response.data.length > 0) {
            setActiveDataset(response.data[0].id);
          }
        }
      } catch (error) {
        console.error('Error fetching datasets:', error);
        setMessages(prev => [...prev, {
          id: `error-${Date.now()}`,
          type: 'system',
          content: 'Failed to load available datasets. Please try again later.',
          metadata: { isError: true },
          timestamp: new Date()
        }]);
      }
    };
    
    fetchDatasets();
  }, [datasetId]);
  
  // Update active dataset when datasetId prop changes
  useEffect(() => {
    if (datasetId) {
      setActiveDataset(datasetId);
    }
  }, [datasetId]);
  
  /**
   * Send a user message to the AI assistant and handle the response
   */
  const handleSendMessage = async () => {
    if (!input.trim() || isProcessing) return;
    
    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: input,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);
    setIsProcessing(true);
    
    try {
      // Mock AI response for now
      setTimeout(() => {
        const aiResponse: Message = {
          id: `assistant-${Date.now()}`,
          type: 'assistant',
          content: `I'm processing your question about "${input}". This is a simulated response as the AI backend is not currently connected.`,
          metadata: {
            confidence: 0.85,
            processing_time: 1.2,
            tokens_used: 150,
            embedding_count: 3
          },
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, aiResponse]);
        setIsTyping(false);
        setIsProcessing(false);
      }, 1500);
    } catch (error) {
      // Handle exception
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        type: 'system',
        content: 'Sorry, there was a problem connecting to the AI service.',
        metadata: { isError: true },
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
      setIsTyping(false);
      setIsProcessing(false);
    }
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  // Scroll to bottom when messages change
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollArea = scrollAreaRef.current;
      scrollArea.scrollTo({ top: scrollArea.scrollHeight, behavior: 'smooth' });
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
                          type: 'assistant',
                          content: 'Hi there! I\'m your AI assistant for data pipeline operations. How can I help you today?',
                          timestamp: new Date()
                        },
                        {
                          id: '2',
                          type: 'system',
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
                message.type === 'user' ? 'justify-end' : 
                message.type === 'system' ? 'justify-center' : 'justify-start'
              }`}>
                <div 
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.type === 'user' 
                      ? 'bg-blue-500 text-white' 
                      : message.type === 'system'
                        ? 'bg-gray-200 text-gray-800'
                        : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {message.type === 'assistant' && (
                    <div className="flex items-center text-blue-600 text-xs mb-1 space-x-1">
                      <Sparkles className="h-3 w-3" />
                      <span>AI Assistant</span>
                    </div>
                  )}
                  
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  
                  {/* Show confidence and sources for AI responses */}
                  {message.type === 'assistant' && message.metadata?.confidence && (
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
            {isTyping && (
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
            className="bg-blue-500 hover:bg-blue-600"
          >
            <SendHorizontal className="h-4 w-4" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
};

export default ChatInterface;
