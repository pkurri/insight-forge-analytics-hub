import React from 'react';
import { Message } from './ChatInterface';
import { Avatar } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Bot, User, ChevronDown, ChevronUp, Lightbulb, Clock, AlertCircle, Copy, ExternalLink, MessageSquare, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Source {
  title?: string;
  snippet?: string;
}

type MessageSource = string | Source;

// Update Message interface to include metadata with proper typing
interface MessageMetadata {
  sources?: MessageSource[];
  insights?: string[];
  confidence?: number;
  isError?: boolean;
  timestamp?: string;
  modelId?: string;
}

// Extend the Message type from ChatInterface to ensure proper typing
declare module './ChatInterface' {
  interface Message {
    metadata?: MessageMetadata;
  }
}

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  expandedMessageIds: string[];
  toggleMessageExpanded: (id: string) => void;
  onMessageAction?: (action: string, messageId: string) => void;
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
  onMessageAction,
}) => {
  return (
    <div className="flex flex-col space-y-6">
      {messages.map((message, index) => {
        const isExpanded = expandedMessageIds.includes(message.id);
        const hasMetadata = message.metadata && (
          message.metadata.sources?.length ||
          message.metadata.insights?.length ||
          message.metadata.confidence
        );
        
        // Check if this is the first message of a sequence from the same sender
        const isFirstInSequence = index === 0 || messages[index - 1].type !== message.type;
        // Check if this is the last message of a sequence from the same sender
        const isLastInSequence = index === messages.length - 1 || messages[index + 1].type !== message.type;
        
        return (
          <div 
            key={message.id}
            className={`group flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} ${!isLastInSequence ? 'mb-1' : ''}`}
          >
            <div 
              className={`flex max-w-[85%] md:max-w-[75%] gap-3 ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              {isLastInSequence && (
                <div className="flex flex-col items-center mt-auto mb-1">
                  <Avatar 
                    className={`h-8 w-8 ${message.type === 'assistant' 
                      ? 'bg-primary/10 ring-1 ring-primary/20' 
                      : 'bg-secondary/90 text-secondary-foreground'} shadow-sm`}
                  >
                    {message.type === 'assistant' ? (
                      <Bot className="h-4 w-4 text-primary" />
                    ) : (
                      <User className="h-4 w-4" />
                    )}
                  </Avatar>
                </div>
              )}
              
              <div className="flex flex-col space-y-1 min-w-0">
                <div 
                  className={`rounded-2xl px-4 py-3 ${message.type === 'assistant' 
                      ? 'bg-card border shadow-sm' 
                      : 'bg-primary text-primary-foreground'} 
                    ${!isFirstInSequence && message.type === 'assistant' ? 'rounded-tl-md' : ''}
                    ${!isFirstInSequence && message.type === 'user' ? 'rounded-tr-md' : ''}
                    ${!isLastInSequence && message.type === 'assistant' ? 'rounded-bl-md' : ''}
                    ${!isLastInSequence && message.type === 'user' ? 'rounded-br-md' : ''}`}
                >
                  {message.metadata?.isError ? (
                    <div className="flex items-center gap-2 text-destructive mb-2 pb-2 border-b border-destructive/10">
                      <AlertCircle className="h-4 w-4" />
                      <span className="font-medium">Error</span>
                    </div>
                  ) : null}
                  
                  <div className="prose-sm dark:prose-invert prose-p:leading-relaxed prose-pre:p-0 prose-pre:rounded-md prose-pre:bg-muted/50 prose-code:text-primary prose-a:text-primary hover:prose-a:text-primary/80 prose-headings:text-foreground">
                    <ReactMarkdown>
                      {message.content}
                    </ReactMarkdown>
                  </div>
                  
                  {message.type === 'assistant' && onMessageAction && (
                    <div className="flex items-center justify-end gap-2 mt-2 pt-1 border-t border-border/30 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-7 w-7 rounded-full hover:bg-primary/10"
                        onClick={() => onMessageAction('copy', message.id)}
                        title="Copy message"
                      >
                        <Copy className="h-3.5 w-3.5 text-muted-foreground" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-7 w-7 rounded-full hover:bg-primary/10"
                        onClick={() => onMessageAction('feedback', message.id)}
                        title="Provide feedback"
                      >
                        <MessageSquare className="h-3.5 w-3.5 text-muted-foreground" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-7 w-7 rounded-full hover:bg-primary/10"
                        onClick={() => onMessageAction('improve', message.id)}
                        title="Improve response"
                      >
                        <Sparkles className="h-3.5 w-3.5 text-muted-foreground" />
                      </Button>
                    </div>
                  )}
                  
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
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
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
                          <div className="space-y-2">
                            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                              <ExternalLink className="h-3 w-3" />
                              <span>Sources:</span>
                            </div>
                            <div className="space-y-2">
                              {message.metadata.sources.map((source, i) => {
                                // Ensure proper type handling for sources
                                if (typeof source === 'string') {
                                  return (
                                    <div key={i} className="text-xs bg-muted/30 p-2.5 rounded-md border border-border/50">
                                      <div className="font-medium">{source}</div>
                                    </div>
                                  );
                                } else {
                                  return (
                                    <div key={i} className="text-xs bg-muted/30 p-2.5 rounded-md border border-border/50">
                                      <div className="font-medium mb-1">{source.title || 'Source'}</div>
                                      {source.snippet && (
                                        <div className="line-clamp-2 text-muted-foreground">{source.snippet}</div>
                                      )}
                                    </div>
                                  );
                                }
                              })}
                            </div>
                          </div>
                        ) : null}
                        
                        {message.metadata?.insights?.length ? (
                          <div className="space-y-2">
                            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                              <Lightbulb className="h-3 w-3 text-amber-500" />
                              <span>Insights:</span>
                            </div>
                            <div className="space-y-1.5 bg-amber-50 dark:bg-amber-950/20 p-2.5 rounded-md border border-amber-100 dark:border-amber-900/30">
                              {message.metadata.insights.map((insight, i) => (
                                <div key={i} className="flex items-start gap-2 text-xs">
                                  <div className="mt-0.5 min-w-[12px]">{i + 1}.</div>
                                  <div>{insight}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : null}
                        
                        {message.metadata?.timestamp && (
                          <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-2">
                            <Clock className="h-3 w-3" />
                            <span>{new Date(message.metadata.timestamp).toLocaleString()}</span>
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
        <div className="flex justify-start animate-pulse">
          <div className="flex flex-row max-w-[80%] gap-3">
            <div className="flex-shrink-0">
              <Avatar className="h-8 w-8 bg-primary/10 ring-1 ring-primary/20 shadow-sm">
                <Bot className="h-4 w-4 text-primary/70" />
              </Avatar>
            </div>
            <div className="space-y-2.5 pt-1 w-full max-w-[350px]">
              <Skeleton className="h-4 w-[85%] rounded-md" />
              <Skeleton className="h-4 w-[70%] rounded-md" />
              <Skeleton className="h-4 w-[40%] rounded-md" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MessageList;
