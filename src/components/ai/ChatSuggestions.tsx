import React from 'react';
import { Button } from '@/components/ui/button';
import { Search, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export interface ChatSuggestion {
  id: string;
  text: string;
  category?: string;
}

interface ChatSuggestionsProps {
  suggestions: ChatSuggestion[];
  onSuggestionClick: (text: string) => void;
  layout?: 'grid' | 'flow' | 'list';
  maxSuggestions?: number;
  className?: string;
}

/**
 * ChatSuggestions component for displaying suggested queries
 * Supports different layouts and categories
 */
const ChatSuggestions: React.FC<ChatSuggestionsProps> = ({
  suggestions,
  onSuggestionClick,
  layout = 'grid',
  maxSuggestions = 6,
  className = '',
}) => {
  if (!suggestions || suggestions.length === 0) {
    return null;
  }

  // Limit the number of suggestions shown
  const limitedSuggestions = suggestions.slice(0, maxSuggestions);
  
  // Group suggestions by category if they have categories
  const hasCategories = suggestions.some(s => s.category);
  const groupedSuggestions = hasCategories 
    ? limitedSuggestions.reduce((acc, suggestion) => {
        const category = suggestion.category || 'General';
        if (!acc[category]) {
          acc[category] = [];
        }
        acc[category].push(suggestion);
        return acc;
      }, {} as Record<string, ChatSuggestion[]>)
    : { 'Suggestions': limitedSuggestions };

  if (layout === 'flow') {
    return (
      <div className={`flex flex-wrap gap-2 ${className}`}>
        {limitedSuggestions.map(suggestion => (
          <Badge 
            key={suggestion.id} 
            variant="outline" 
            className="cursor-pointer hover:bg-muted whitespace-nowrap py-1.5"
            onClick={() => onSuggestionClick(suggestion.text)}
          >
            {suggestion.text}
          </Badge>
        ))}
      </div>
    );
  }
  
  if (layout === 'list') {
    return (
      <div className={`space-y-1.5 ${className}`}>
        {Object.entries(groupedSuggestions).map(([category, categorySuggestions]) => (
          <div key={category} className="space-y-1">
            {hasCategories && (
              <div className="text-xs font-medium text-muted-foreground">{category}</div>
            )}
            <div className="space-y-1">
              {categorySuggestions.map(suggestion => (
                <Button
                  key={suggestion.id}
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-left h-auto py-1.5 px-2"
                  onClick={() => onSuggestionClick(suggestion.text)}
                >
                  <Search className="h-3 w-3 mr-2 flex-shrink-0" />
                  <span className="truncate">{suggestion.text}</span>
                </Button>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }
  
  // Default grid layout
  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 gap-2 ${className}`}>
      {Object.entries(groupedSuggestions).map(([category, categorySuggestions]) => (
        <React.Fragment key={category}>
          {hasCategories && (
            <div className="col-span-full text-xs font-medium text-muted-foreground mb-1">{category}</div>
          )}
          {categorySuggestions.map(suggestion => (
            <Button
              key={suggestion.id}
              variant="outline"
              className="justify-start text-left h-auto py-2"
              onClick={() => onSuggestionClick(suggestion.text)}
            >
              <Sparkles className="h-3.5 w-3.5 mr-2 flex-shrink-0 text-primary" />
              <span className="truncate">{suggestion.text}</span>
            </Button>
          ))}
        </React.Fragment>
      ))}
    </div>
  );
};

export default ChatSuggestions;
