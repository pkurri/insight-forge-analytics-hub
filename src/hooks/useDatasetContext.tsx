
import { createContext, useContext, useState, useEffect, useMemo, ReactNode } from 'react';
import { api, Dataset } from '@/api/api';

interface DatasetContextType {
  datasets: Dataset[];
  activeDataset: string;
  setActiveDataset: (datasetId: string) => void;
  isLoading: boolean;
  error: string | null;
  refreshDatasets: () => Promise<void>;
}

// Create context without default value (safer)
const DatasetContext = createContext<DatasetContextType | undefined>(undefined);

// Provider component to wrap application and provide dataset context
interface DatasetProviderProps {
  children: ReactNode;
}

export const DatasetProvider = ({ children }: DatasetProviderProps) => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [activeDataset, setActiveDataset] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Function to load available datasets using central API
  const loadDatasets = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Use the centralized api.datasets.getDatasets function
      const response = await api.datasets.getDatasets();
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const contextValue = useMemo(() => ({
    datasets,
    activeDataset,
    setActiveDataset,
    isLoading,
    error,
    refreshDatasets: loadDatasets
  }), [datasets, activeDataset, isLoading, error]);

  return (
    <DatasetContext.Provider value={contextValue}>
      {children}
    </DatasetContext.Provider>
  );
};

// Hook to use dataset context in components (with runtime safety)
export const useDatasetContext = (): DatasetContextType => {
  const context = useContext(DatasetContext);
  if (!context) {
    throw new Error('useDatasetContext must be used within a DatasetProvider');
  }
  return context;
};
