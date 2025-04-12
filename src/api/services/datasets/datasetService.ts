
import { callApi } from '../../utils/apiUtils';
import { ApiResponse, DatasetSummary } from '../../api';

/**
 * Dataset Service - Handles dataset operations
 */
export const datasetService = {
  /**
   * Get list of available datasets
   */
  getDatasets: async (): Promise<ApiResponse<DatasetSummary[]>> => {
    const endpoint = 'datasets';
    
    try {
      const response = await callApi(endpoint);
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      return {
        success: true,
        data: [
          {
            id: 'ds001',
            name: 'Customer Orders',
            rows: 12453,
            columns: 15,
            created_at: '2023-05-15T10:23:45Z',
            updated_at: '2023-06-02T14:10:22Z',
            status: 'active',
            description: 'Customer order data including order items, prices and dates'
          },
          {
            id: 'ds002',
            name: 'Product Inventory',
            rows: 5823,
            columns: 12,
            created_at: '2023-06-10T08:15:30Z',
            updated_at: '2023-06-10T08:15:30Z',
            status: 'active',
            description: 'Product inventory and stock levels'
          },
          {
            id: 'ds003',
            name: 'Sales Transactions',
            rows: 45231,
            columns: 22,
            created_at: '2023-04-22T16:45:12Z',
            updated_at: '2023-06-05T11:30:45Z',
            status: 'active',
            description: 'Sales transaction data across all regions'
          }
        ]
      };
    } catch (error) {
      console.error("Error fetching datasets:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to fetch datasets"
      };
    }
  },

  /**
   * Get detailed information about a dataset
   */
  getDatasetDetails: async (datasetId: string): Promise<ApiResponse<any>> => {
    const endpoint = `datasets/${datasetId}`;
    
    try {
      const response = await callApi(endpoint);
      if (response.success) {
        return response;
      }
      
      // Find the dataset in our mock data
      const datasets = [
        {
          id: 'ds001',
          name: 'Customer Orders',
          rows: 12453,
          columns: 15,
          created_at: '2023-05-15T10:23:45Z',
          updated_at: '2023-06-02T14:10:22Z',
          status: 'active',
          description: 'Customer order data including order items, prices and dates'
        },
        {
          id: 'ds002',
          name: 'Product Inventory',
          rows: 5823,
          columns: 12,
          created_at: '2023-06-10T08:15:30Z',
          updated_at: '2023-06-10T08:15:30Z',
          status: 'active',
          description: 'Product inventory and stock levels'
        },
        {
          id: 'ds003',
          name: 'Sales Transactions',
          rows: 45231,
          columns: 22,
          created_at: '2023-04-22T16:45:12Z',
          updated_at: '2023-06-05T11:30:45Z',
          status: 'active',
          description: 'Sales transaction data across all regions'
        }
      ];
      
      const dataset = datasets.find(ds => ds.id === datasetId);
      
      if (!dataset) {
        return {
          success: false,
          error: `Dataset with ID ${datasetId} not found`
        };
      }
      
      // Generate some sample data based on the dataset
      return {
        success: true,
        data: {
          ...dataset,
          schema: {
            columns: [
              { name: 'id', type: 'string', nullable: false },
              { name: 'name', type: 'string', nullable: false },
              { name: 'category', type: 'string', nullable: true },
              { name: 'price', type: 'number', nullable: false },
              { name: 'quantity', type: 'integer', nullable: false },
              { name: 'created_at', type: 'datetime', nullable: false },
              { name: 'updated_at', type: 'datetime', nullable: true },
            ]
          },
          stats: {
            rowCount: dataset.rows,
            nullValues: Math.floor(dataset.rows * 0.05),
            duplicateRows: Math.floor(dataset.rows * 0.02),
            lastProcessed: new Date().toISOString()
          }
        }
      };
    } catch (error) {
      console.error("Error fetching dataset details:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to fetch dataset details"
      };
    }
  }
};
