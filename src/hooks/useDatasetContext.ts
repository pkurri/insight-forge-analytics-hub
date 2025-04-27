import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from '@/api/api';

interface Dataset {
  id: string;
  name: string;
  rows: number;
  columns: number;
  lastUpdated: string;
}

interface DatasetContextType {
  datasets: Dataset[];
  isLoading: boolean;
  error: string | null;
  activeDataset: string;
  setActiveDataset: (datasetId: string) => void;
  refreshDatasets: () => Promise<void>;
}

// Create context with default values
const DatasetContext = createContext<DatasetContextType>({
  datasets: [],
  isLoading: false,
  error: null,
  activeDataset: 'all',
  setActiveDataset: () => {},
  refreshDatasets: async () => {}
});

interface DatasetProviderProps {
  children: ReactNode;
  initialDatasetId?: string;
}

/**
 * Provider component that wraps app and makes dataset context available
 */
export const DatasetProvider: React.FC<DatasetProviderProps> = ({ 
  children,
  initialDatasetId = 'all'
}) => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeDataset, setActiveDataset] = useState(initialDatasetId);
  
  // Load datasets on mount
  const fetchDatasets = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.datasets.getDatasets();
      
      if (response.success && response.data) {
        const formattedDatasets = response.data.map(ds => ({
          id: ds.id,
          name: ds.name,
          rows: ds.rows,
          columns: ds.columns || 0,
          lastUpdated: ds.updated_at || new Date().toISOString()
        }));
        
        setDatasets(formattedDatasets);
      } else {
        setError(response.error || 'Failed to load datasets');
      }
    } catch (err) {
      console.error('Error fetching datasets:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Initial fetch
  useEffect(() => {
    fetchDatasets();
  }, []);
  
  // Refresh datasets function for external components
  const refreshDatasets = async () => {
    await fetchDatasets();
  };
  
  const value = {
    datasets,
    isLoading,
    error,
    activeDataset,
    setActiveDataset,
    refreshDatasets
  };
  
  return (
    <DatasetContext.Provider value={value}>
      {children}
    </DatasetContext.Provider>
  );
};

/**
 * Hook to use the dataset context
 */
export const useDatasetContext = () => {
  const context = useContext(DatasetContext);
  
  if (context === undefined) {
    throw new Error('useDatasetContext must be used within a DatasetProvider');
  }
  
  return context;
};
