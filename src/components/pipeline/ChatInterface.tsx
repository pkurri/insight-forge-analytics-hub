
import React, { useState, useRef, useEffect } from 'react';
import { SendHorizontal, Bot, RefreshCw, Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Hi there! I\'m your AI assistant for data pipeline operations. How can I help you today?',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  
  const handleSendMessage = () => {
    if (!input.trim()) return;
    
    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: input,
      timestamp: new Date()
    };
    
    setMessages([...messages, userMessage]);
    setInput('');
    setIsTyping(true);
    
    // Simulate AI response after delay
    setTimeout(() => {
      let response = '';
      const normalizedInput = input.toLowerCase();
      
      // Simple pattern matching for responses
      if (normalizedInput.includes('hello') || normalizedInput.includes('hi')) {
        response = 'Hello! How can I assist with your data pipeline today?';
      } else if (normalizedInput.includes('help')) {
        response = 'I can help with data ingestion, cleaning, validation, or analyzing your pipeline status. What would you like to know more about?';
      } else if (normalizedInput.includes('anomaly') || normalizedInput.includes('anomalies')) {
        response = 'Our anomaly detection uses isolation forests and autoencoders to identify outliers in your data. Would you like more details on how it works?';
      } else if (normalizedInput.includes('clean') || normalizedInput.includes('cleaning')) {
        response = 'Our data cleaning process handles missing values, duplicates, and outliers using advanced ML techniques. We use imputation methods like random forest regression for predicting missing values.';
      } else if (normalizedInput.includes('upload') || normalizedInput.includes('format') || normalizedInput.includes('file')) {
        response = 'We support several file formats including CSV, JSON, Excel spreadsheets, and PDFs. For PDFs, we use Hugging Face models like tab-transformer to extract tables accurately.';
      } else if (normalizedInput.includes('validation')) {
        response = 'Data validation ensures your data meets schema and business rule requirements using Pydantic. Our AI can even suggest validation rules based on column names and content.';
      } else if (normalizedInput.includes('research') || normalizedInput.includes('look up')) {
        response = 'I can research information for you. For example, I can check the latest best practices for data validation or look up specific documentation on file parsing techniques.';
      } else {
        response = 'I understand your question about the data pipeline. Let me help you with that aspect of our processing workflow. What specific details would you like to know?';
      }
      
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        type: 'assistant',
        content: response,
        timestamp: new Date()
      };
      
      setMessages(prevMessages => [...prevMessages, assistantMessage]);
      setIsTyping(false);
    }, 1500);
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
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
            <CardTitle className="text-md">AI Assistant</CardTitle>
          </div>
          <div className="flex space-x-1">
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <Search className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-grow p-0 overflow-hidden">
        <ScrollArea className="h-full p-4" ref={scrollAreaRef}>
          <div className="space-y-4">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div 
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.type === 'user' 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <p className="text-sm">{message.content}</p>
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
            placeholder="Ask a question about the data pipeline..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            className="flex-grow"
          />
          <Button 
            onClick={handleSendMessage} 
            disabled={!input.trim()} 
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
