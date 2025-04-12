
import { useState, useEffect, useCallback } from 'react';
import { Message } from '@/components/ai/ChatInterface';

/**
 * Hook to manage chat history with local storage persistence
 * @param datasetId - Current dataset ID for scoped history
 * @returns Object containing messages and methods to manage them
 */
export const useChatHistory = (datasetId: string) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Storage key is scoped to dataset ID
  const storageKey = useCallback(() => `chat_history_${datasetId}`, [datasetId]);
  
  // Load messages from local storage on mount or dataset change
  useEffect(() => {
    setIsLoading(true);
    
    const loadMessages = async () => {
      try {
        // Get saved messages from local storage
        const savedMessages = localStorage.getItem(storageKey());
        
        if (savedMessages) {
          // Parse saved messages and convert string timestamps back to Date objects
          const parsedMessages = JSON.parse(savedMessages);
          const messagesWithDates = parsedMessages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }));
          
          setMessages(messagesWithDates);
        } else {
          // No saved messages found
          setMessages([]);
        }
      } catch (error) {
        console.error('Error loading chat history:', error);
        setMessages([]);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadMessages();
  }, [datasetId, storageKey]);
  
  // Save messages to local storage whenever they change
  useEffect(() => {
    if (messages.length > 0 && !isLoading) {
      localStorage.setItem(storageKey(), JSON.stringify(messages));
    }
  }, [messages, isLoading, storageKey]);
  
  /**
   * Add a new message to the chat history
   */
  const addMessage = useCallback((newMessage: Message) => {
    setMessages(prevMessages => [...prevMessages, newMessage]);
  }, []);
  
  /**
   * Clear all messages from chat history
   */
  const clearHistory = useCallback(() => {
    setMessages([]);
    localStorage.removeItem(storageKey());
  }, [storageKey]);
  
  return {
    messages,
    setMessages,
    addMessage,
    clearHistory,
    isLoading
  };
};
