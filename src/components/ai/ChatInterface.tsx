import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Loader2, Send, Bot, User, Sparkles, Info, AlertCircle } from 'lucide-react';
import { api } from '@/api/api';
import { ChatSuggestion } from '@/api/types';
import ReactMarkdown from 'react-markdown';
import { useDatasetContext } from '@/hooks/useDatasetContext';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    sources?: string[];
    confidence?: number;
    model?: string;
    processing_time?: number;
  };
}

interface ChatInterfaceProps {
  title?: string;
  subtitle?: string;
  showDatasetSelector?: boolean;
  suggestions?: ChatSuggestion[];
  defaultDataset?: string;
  selectedModel?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  title = 'AI Assistant',
  subtitle = 'Ask me anything about your data',
  showDatasetSelector = false,
  suggestions = [],
  defaultDataset,
  selectedModel = 'default'
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<string | undefined>(defaultDataset);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const { datasets } = useDatasetContext();

  // Initial system message
  useEffect(() => {
    setMessages([
      {
        id: 'system-1',
        role: 'system',
        content: 'Hello! I\'m your AI data assistant. How can I help you analyze your data today?',
        timestamp: new Date(),
      }
    ]);
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus input on load
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Prepare chat history for context
      const chatHistory = messages
        .filter(msg => msg.role !== 'system')
        .map(msg => ({
          role: msg.role,
          content: msg.content
        }));

      // Call AI service
      const response = await api.getAiAssistantResponse(input.trim(), {
        dataset_id: selectedDataset,
        model_id: selectedModel,
        chat_history: chatHistory,
        context: {
          system_prompt_addition: selectedDataset 
            ? `The user is currently working with dataset ID: ${selectedDataset}.` 
            : undefined
        }
      });

      if (response.success && response.data) {
        const aiMessage: Message = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: response.data.response || response.data.answer || "I'm not sure how to respond to that.",
          timestamp: new Date(),
          metadata: {
            sources: response.data.context?.sources || [],
            confidence: response.data.context?.confidence || 0.8,
            model: selectedModel,
            processing_time: response.data.processing_time
          }
        };

        setMessages(prev => [...prev, aiMessage]);
      } else {
        // Handle error
        const errorMessage: Message = {
          id: `assistant-error-${Date.now()}`,
          role: 'assistant',
          content: "I'm sorry, I encountered an error processing your request. Please try again later.",
          timestamp: new Date(),
        };

        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error("Error in AI response:", error);
      
      // Add error message
      const errorMessage: Message = {
        id: `assistant-error-${Date.now()}`,
        role: 'assistant',
        content: "I'm sorry, I encountered an unexpected error. Please try again later.",
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      // Focus back on input after response
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)] min-h-[500px] border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b bg-card flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        </div>
        
        {showDatasetSelector && (
          <Select
            value={selectedDataset}
            onValueChange={setSelectedDataset}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select dataset" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={undefined}>All Datasets</SelectItem>
              {datasets.map(dataset => (
                <SelectItem key={dataset.id} value={dataset.id}>
                  {dataset.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`flex gap-3 max-w-[80%] ${
                  message.role === 'user'
                    ? 'flex-row-reverse'
                    : 'flex-row'
                }`}
              >
                <Avatar className={message.role === 'user' ? 'bg-primary' : 'bg-muted'}>
                  <AvatarFallback>
                    {message.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <div
                    className={`rounded-lg p-4 ${
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    <ReactMarkdown className="prose dark:prose-invert max-w-none">
                      {message.content}
                    </ReactMarkdown>
                  </div>
                  <div className="flex items-center mt-1 space-x-2">
                    <span className="text-xs text-muted-foreground">
                      {formatTimestamp(message.timestamp)}
                    </span>
                    
                    {message.metadata?.sources && message.metadata.sources.length > 0 && (
                      <Badge variant="outline" className="text-xs">
                        <Info className="h-3 w-3 mr-1" />
                        {message.metadata.sources.length} sources
                      </Badge>
                    )}
                    
                    {message.metadata?.confidence && (
                      <Badge 
                        variant={message.metadata.confidence > 0.8 ? "default" : "outline"} 
                        className="text-xs"
                      >
                        <Sparkles className="h-3 w-3 mr-1" />
                        {Math.round(message.metadata.confidence * 100)}% confidence
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Suggestions */}
      {suggestions && suggestions.length > 0 && (
        <div className="p-2 border-t">
          <p className="text-xs text-muted-foreground mb-2">Suggested questions:</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.slice(0, 3).map((suggestion) => (
              <Button
                key={suggestion.id}
                variant="outline"
                size="sm"
                className="text-xs"
                onClick={() => handleSuggestionClick(suggestion.text)}
              >
                {suggestion.text}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <Textarea
            ref={inputRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your data..."
            className="min-h-[60px] resize-none"
            disabled={isLoading}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!input.trim() || isLoading}
            className="shrink-0"
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
        <div className="mt-2 text-xs text-muted-foreground flex items-center">
          <Bot className="h-3 w-3 mr-1" />
          <span>
            {selectedModel !== 'default' ? `Using ${selectedModel} model` : 'AI-powered assistant'}
            {selectedDataset ? ` • Dataset: ${selectedDataset}` : ''}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
