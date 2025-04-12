
import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '@/api/api';
import { DatasetSummary } from '@/api/api';

interface DatasetContextType {
  datasets: DatasetSummary[];
  activeDataset: string;
  setActiveDataset: (datasetId: string) => void;
  isLoading: boolean;
  error: string | null;
  refreshDatasets: () => Promise<void>;
}

// Create context with default values
const DatasetContext = createContext<DatasetContextType>({
  datasets: [],
  activeDataset: '',
  setActiveDataset: () => {},
  isLoading: false,
  error: null,
  refreshDatasets: async () => {},
});

/**
 * Provider component to wrap application and provide dataset context
 */
export const DatasetProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [activeDataset, setActiveDataset] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Function to load available datasets
  const loadDatasets = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.getDatasets();
      
      if (response.success && response.data) {
        setDatasets(response.data);
        
        // Set active dataset to first one if none is selected
        if (!activeDataset && response.data.length > 0) {
          setActiveDataset(response.data[0].id);
        }
      } else {
        setError('Failed to load datasets');
      }
    } catch (err) {
      setError('Error loading datasets');
      console.error('Error loading datasets:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Load datasets on mount
  useEffect(() => {
    loadDatasets();
  }, []);

  const value = {
    datasets,
    activeDataset,
    setActiveDataset,
    isLoading,
    error,
    refreshDatasets: loadDatasets
  };

  return (
    <DatasetContext.Provider value={value}>
      {children}
    </DatasetContext.Provider>
  );
};

/**
 * Hook to use dataset context in components
 */
export const useDatasetContext = () => {
  return useContext(DatasetContext);
};
