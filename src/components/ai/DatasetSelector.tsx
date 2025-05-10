import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Database, Globe } from 'lucide-react';

export interface Dataset {
  id: string;
  name: string;
  rows: number;
  columns: number;
  lastUpdated: string;
  source?: string;
}

interface DatasetSelectorProps {
  datasets: Dataset[];
  selectedDataset: string;
  onDatasetChange: (datasetId: string) => void;
  isLoading?: boolean;
  showAllOption?: boolean;
  className?: string;
}

/**
 * DatasetSelector component for choosing which dataset to use
 * Supports selecting a specific dataset or all datasets
 */
const DatasetSelector: React.FC<DatasetSelectorProps> = ({
  datasets,
  selectedDataset,
  onDatasetChange,
  isLoading = false,
  showAllOption = true,
  className = "",
}) => {
  // Get the currently selected dataset object
  const currentDataset = datasets.find(dataset => dataset.id === selectedDataset);
  
  return (
    <div className={`flex flex-col space-y-2 ${className}`}>
      <div className="flex items-center space-x-2">
        <span className="text-sm font-medium">Dataset:</span>
        {currentDataset && (
          <Badge variant="outline" className="text-xs">
            {currentDataset.rows.toLocaleString()} rows
          </Badge>
        )}
      </div>
      
      <Select 
        value={selectedDataset} 
        onValueChange={onDatasetChange}
        disabled={isLoading}
      >
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select Dataset" />
        </SelectTrigger>
        <SelectContent>
          {showAllOption && (
            <SelectItem value="all">
              <div className="flex items-center space-x-2">
                <Globe className="h-4 w-4" />
                <span>All Datasets</span>
              </div>
            </SelectItem>
          )}
          
          {datasets.map(dataset => (
            <SelectItem key={dataset.id} value={dataset.id}>
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center space-x-2">
                  <Database className="h-4 w-4" />
                  <span>{dataset.name}</span>
                </div>
                <Badge variant="outline" className="ml-2 text-xs">
                  {dataset.rows.toLocaleString()} rows
                </Badge>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};

export { DatasetSelector };
export type { Dataset };
