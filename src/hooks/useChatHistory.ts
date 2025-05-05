
import { useState, useEffect } from 'react';
import { Message } from '@/components/ai/ChatInterface';

export const useChatHistory = (chatId: string) => {
  const [history, setHistory] = useState<Message[]>([]);
  
  useEffect(() => {
    // Load chat history from local storage
    const loadHistory = () => {
      const storedHistory = localStorage.getItem(`chat_history_${chatId}`);
      if (storedHistory) {
        try {
          const parsedHistory = JSON.parse(storedHistory);
          // Convert string dates back to Date objects
          const processedHistory = parsedHistory.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }));
          setHistory(processedHistory);
        } catch (e) {
          console.error('Failed to parse chat history:', e);
        }
      }
    };
    
    loadHistory();
  }, [chatId]);
  
  const saveMessage = (message: Message) => {
    const newHistory = [...history, message];
    setHistory(newHistory);
    
    // Save to localStorage
    try {
      localStorage.setItem(`chat_history_${chatId}`, JSON.stringify(newHistory));
    } catch (e) {
      console.error('Failed to save chat history:', e);
    }
  };
  
  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem(`chat_history_${chatId}`);
  };
  
  return { history, saveMessage, clearHistory };
};
