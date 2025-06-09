import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

interface PipelineState {
  currentDataset: any | null;
  pipelineStatus: 'idle' | 'processing' | 'completed' | 'error';
  pipelineData: any;
  activeTab: string;
  isChatOpen: boolean;
  businessRules: any[];
}

interface PipelineContextType extends PipelineState {
  setCurrentDataset: (dataset: any) => void;
  setPipelineStatus: (status: PipelineState['pipelineStatus']) => void;
  setPipelineData: (data: any) => void;
  setActiveTab: (tab: string) => void;
  toggleChat: () => void;
  updateBusinessRules: (rules: any[]) => void;
  clearPipeline: () => void;
}

const PipelineContext = createContext<PipelineContextType | undefined>(undefined);

// Custom hook to use localStorage with state
function usePersistedState<T>(
  key: string,
  initialValue: T,
  listenToStorageChanges: boolean = true
): [T, (value: T | ((val: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      if (typeof window === 'undefined') return initialValue;
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((val: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        if (typeof window !== 'undefined') {
          window.localStorage.setItem(key, JSON.stringify(valueToStore));
        }
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  useEffect(() => {
    if (!listenToStorageChanges) return;

    const handleStorageChange = (event: StorageEvent) => {
      if (event.key === key && event.newValue) {
        try {
          const newValue = JSON.parse(event.newValue);
          if (JSON.stringify(storedValue) !== JSON.stringify(newValue)) {
            setStoredValue(newValue);
          }
        } catch (error) {
          console.warn(`Error parsing storage event for key "${key}":`, error);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key, storedValue, listenToStorageChanges]);

  return [storedValue, setValue];
}

export const PipelineProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = usePersistedState<PipelineState>('pipelineState', {
    currentDataset: null,
    pipelineStatus: 'idle',
    pipelineData: {},
    activeTab: 'upload',
    isChatOpen: false,
    businessRules: [],
  });

  const updateState = useCallback((updates: Partial<PipelineState>) => {
    setState(prev => ({
      ...prev,
      ...updates,
    }));
  }, [setState]);

  const contextValue = {
    ...state,
    setCurrentDataset: (dataset: any) => updateState({ currentDataset: dataset }),
    setPipelineStatus: (status: PipelineState['pipelineStatus']) => updateState({ pipelineStatus: status }),
    setPipelineData: (data: any) => updateState({ pipelineData: data }),
    setActiveTab: (activeTab: string) => updateState({ activeTab }),
    toggleChat: () => updateState({ isChatOpen: !state.isChatOpen }),
    updateBusinessRules: (businessRules: any[]) => updateState({ businessRules }),
    clearPipeline: () => updateState({
      currentDataset: null,
      pipelineStatus: 'idle',
      pipelineData: {},
      activeTab: 'upload',
      businessRules: [],
    }),
  };

  return (
    <PipelineContext.Provider value={contextValue}>
      {children}
    </PipelineContext.Provider>
  );
};

export const usePipeline = (): PipelineContextType => {
  const context = useContext(PipelineContext);
  if (context === undefined) {
    throw new Error('usePipeline must be used within a PipelineProvider');
  }
  return context;
};

export default PipelineContext;
