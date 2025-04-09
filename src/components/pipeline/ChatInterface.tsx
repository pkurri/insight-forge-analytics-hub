
import React, { useState, useRef, useEffect } from 'react';
import { SendHorizontal, Bot, RefreshCw, Search, AlertCircle } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { pythonApi } from '@/api/pythonIntegration';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: {
    confidence?: number;
    sources?: string[];
    isError?: boolean;
  };
  timestamp: Date;
}

const ChatInterface: React.FC = () => {
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
      content: 'I can answer questions about your loaded datasets using vector database technology and Hugging Face models.',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeDataset, setActiveDataset] = useState<string>('ds001'); // Default to first dataset
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  
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
      // Send question to Python backend via API
      const response = await pythonApi.askQuestion(activeDataset, input);
      
      if (response.success && response.data) {
        const assistantMessage: Message = {
          id: `assistant-${Date.now()}`,
          type: 'assistant',
          content: response.data.answer,
          metadata: {
            confidence: response.data.confidence,
            sources: response.data.sources
          },
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        // Handle error
        const errorMessage: Message = {
          id: `error-${Date.now()}`,
          type: 'system',
          content: response.error || 'Sorry, I encountered an error processing your question.',
          metadata: { isError: true },
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, errorMessage]);
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
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
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
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);
  
  return (
    <Card className="h-[calc(100vh-16rem)] flex flex-col">
      <CardHeader className="px-4 py-3 border-b">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Avatar className="h-8 w-8 bg-blue-500">
              <Bot className="h-5 w-5 text-white" />
            </Avatar>
            <CardTitle className="text-md">Vector DB AI Assistant</CardTitle>
          </div>
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
                          content: 'I can answer questions about your loaded datasets using vector database technology and Hugging Face models.',
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
                  <p className="text-sm">{message.content}</p>
                  
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
          >
            <SendHorizontal className="h-4 w-4" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
};

export default ChatInterface;
