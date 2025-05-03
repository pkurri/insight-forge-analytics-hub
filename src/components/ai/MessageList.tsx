import React from 'react';
import { Message } from './ChatInterface';
import { Avatar } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Bot, User, ChevronDown, ChevronUp, Lightbulb, Clock, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  expandedMessageIds: string[];
  toggleMessageExpanded: (id: string) => void;
}

/**
 * MessageList component for rendering chat messages
 * Supports markdown, code blocks, and message metadata
 */
const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading,
  expandedMessageIds,
  toggleMessageExpanded,
}) => {
  return (
    <div className="flex flex-col space-y-4 py-4">
      {messages.map((message) => {
        const isExpanded = expandedMessageIds.includes(message.id);
        const hasMetadata = message.metadata && (
          message.metadata.sources?.length ||
          message.metadata.insights?.length ||
          message.metadata.confidence
        );
        
        return (
          <div 
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`flex ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'} max-w-[80%] gap-3`}>
              <Avatar className={`h-8 w-8 mt-0.5 ${message.type === 'assistant' ? 'bg-primary/10' : 'bg-secondary/80'}`}>
                {message.type === 'assistant' ? (
                  <Bot className="h-4 w-4 text-primary" />
                ) : (
                  <User className="h-4 w-4" />
                )}
              </Avatar>
              
              <div className="flex flex-col space-y-1">
                <div 
                  className={`rounded-lg px-4 py-3 ${message.type === 'assistant' 
                    ? 'bg-muted/50 text-foreground' 
                    : 'bg-primary text-primary-foreground'}`}
                >
                  {message.metadata?.isError ? (
                    <div className="flex items-center space-x-2 text-destructive">
                      <AlertCircle className="h-4 w-4" />
                      <span className="font-medium">Error</span>
                    </div>
                  ) : null}
                  
                  <div className="prose-sm dark:prose-invert prose-p:leading-relaxed prose-pre:p-0">
                    <ReactMarkdown>
                      {typeof message.content === 'string' ? message.content : JSON.stringify(message.content)}
                    </ReactMarkdown>
                  </div>
                  
                  {hasMetadata && (
                    <Collapsible
                      open={isExpanded}
                      onOpenChange={() => toggleMessageExpanded(message.id)}
                      className="mt-2 pt-2 border-t border-border/40"
                    >
                      <CollapsibleTrigger className="flex items-center text-xs text-muted-foreground hover:text-foreground transition-colors">
                        {isExpanded ? (
                          <ChevronUp className="h-3 w-3 mr-1" />
                        ) : (
                          <ChevronDown className="h-3 w-3 mr-1" />
                        )}
                        <span>{isExpanded ? 'Hide details' : 'Show details'}</span>
                      </CollapsibleTrigger>
                      
                      <CollapsibleContent className="mt-2 space-y-2">
                        {message.metadata?.confidence !== undefined && (
                          <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                            <span>Confidence:</span>
                            <div className="w-full max-w-[100px] h-2 bg-muted rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-primary"
                                style={{ width: `${message.metadata.confidence * 100}%` }}
                              />
                            </div>
                            <span>{Math.round(message.metadata.confidence * 100)}%</span>
                          </div>
                        )}
                        
                        {message.metadata?.sources?.length ? (
                          <div className="space-y-1">
                            <div className="text-xs text-muted-foreground">Sources:</div>
                            <div className="flex flex-wrap gap-1">
                              {message.metadata.sources.map((source, idx) => (
                                <Badge key={idx} variant="outline" className="text-xs">
                                  {typeof source === 'string' ? source : JSON.stringify(source)}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        ) : null}
                        
                        {message.metadata?.insights?.length ? (
                          <div className="space-y-1">
                            <div className="text-xs text-muted-foreground">Insights:</div>
                            <div className="space-y-1">
                              {message.metadata.insights.map((insight, idx) => (
                                <div key={idx} className="flex items-start space-x-1 text-xs">
                                  <Lightbulb className="h-3 w-3 mt-0.5 text-amber-500" />
                                  <span>{typeof insight === 'string' ? insight : JSON.stringify(insight)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : null}
                        
                        {message.metadata?.timestamp && (
                          <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            <span>{new Date(message.metadata.timestamp).toLocaleTimeString()}</span>
                          </div>
                        )}
                        
                        {message.metadata?.modelId && (
                          <div className="text-xs text-muted-foreground">
                            Model: {message.metadata.modelId}
                          </div>
                        )}
                      </CollapsibleContent>
                    </Collapsible>
                  )}
                </div>
                
                <div className="text-xs text-muted-foreground px-1">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          </div>
        );
      })}
      
      {isLoading && (
        <div className="flex justify-start">
          <div className="flex flex-row max-w-[80%] gap-3">
            <Avatar className="h-8 w-8 mt-0.5 bg-primary/10">
              <Bot className="h-4 w-4 text-primary" />
            </Avatar>
            <div className="space-y-2">
              <Skeleton className="h-4 w-[250px] rounded-md" />
              <Skeleton className="h-4 w-[200px] rounded-md" />
              <Skeleton className="h-4 w-[150px] rounded-md" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MessageList;
