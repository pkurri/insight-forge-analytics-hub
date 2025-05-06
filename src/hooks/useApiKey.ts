import { useState, useEffect } from 'react';

export const useApiKey = () => {
  const [apiKey, setApiKey] = useState<string | null>(null);

  useEffect(() => {
    // Load API key from localStorage on mount
    const storedApiKey = localStorage.getItem('apiKey');
    if (storedApiKey) {
      setApiKey(storedApiKey);
    }
  }, []);

  const saveApiKey = (key: string) => {
    localStorage.setItem('apiKey', key);
    setApiKey(key);
  };

  const removeApiKey = () => {
    localStorage.removeItem('apiKey');
    setApiKey(null);
  };

  return {
    apiKey,
    saveApiKey,
    removeApiKey,
  };
}; 