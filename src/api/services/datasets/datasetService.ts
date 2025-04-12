
import { callApi } from '../../utils/apiUtils';
import { ApiResponse, DatasetSummary } from '../../api';

export const datasetService = {
  /**
   * Get a list of all datasets
   */
  getDatasets: async (): Promise<ApiResponse<DatasetSummary[]>> => {
    const endpoint = 'datasets';
    
    try {
      const response = await callApi(endpoint);
      
      if (response.success) {
        return response;
      }
      
      // Return mock data as fallback
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 800));
      
      return {
        success: true,
        data: [
          {
            id: "ds001",
            name: "Sales Data 2023",
            rows: 5280,
            columns: 12,
            created_at: new Date(2023, 0, 15).toISOString(),
            updated_at: new Date(2023, 6, 10).toISOString(),
            status: "active",
            description: "Annual sales data with customer demographics"
          },
          {
            id: "ds002",
            name: "Customer Feedback",
            rows: 2150,
            columns: 8,
            created_at: new Date(2023, 2, 22).toISOString(),
            updated_at: new Date(2023, 5, 30).toISOString(),
            status: "active",
            description: "Survey responses and NPS scores"
          },
          {
            id: "ds003",
            name: "Inventory Tracking",
            rows: 3720,
            columns: 15,
            created_at: new Date(2023, 3, 10).toISOString(),
            updated_at: new Date(2023, 7, 5).toISOString(),
            status: "pending",
            description: "Warehouse inventory and logistics data"
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
   * Get detailed information about a specific dataset
   */
  getDatasetDetails: async (datasetId: string): Promise<ApiResponse<any>> => {
    const endpoint = `datasets/${datasetId}`;
    
    try {
      const response = await callApi(endpoint);
      
      if (response.success) {
        return response;
      }
      
      // Return mock data as fallback
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Generate mock data based on dataset ID
      const isFirstDataset = datasetId === "ds001";
      
      return {
        success: true,
        data: {
          id: datasetId,
          name: isFirstDataset ? "Sales Data 2023" : "Customer Feedback",
          rows: isFirstDataset ? 5280 : 2150,
          columns: isFirstDataset ? 12 : 8,
          created_at: new Date(2023, isFirstDataset ? 0 : 2, isFirstDataset ? 15 : 22).toISOString(),
          updated_at: new Date(2023, isFirstDataset ? 6 : 5, isFirstDataset ? 10 : 30).toISOString(),
          status: "active",
          description: isFirstDataset 
            ? "Annual sales data with customer demographics" 
            : "Survey responses and NPS scores",
          schema: {
            fields: isFirstDataset 
              ? [
                  { name: "sale_id", type: "string", nullable: false },
                  { name: "date", type: "datetime", nullable: false },
                  { name: "customer_id", type: "string", nullable: false },
                  { name: "product_id", type: "string", nullable: false },
                  { name: "quantity", type: "integer", nullable: false },
                  { name: "unit_price", type: "decimal", nullable: false },
                  { name: "total", type: "decimal", nullable: false }
                ] 
              : [
                  { name: "feedback_id", type: "string", nullable: false },
                  { name: "customer_id", type: "string", nullable: false },
                  { name: "date", type: "datetime", nullable: false },
                  { name: "score", type: "integer", nullable: false },
                  { name: "comment", type: "string", nullable: true },
                  { name: "category", type: "string", nullable: false }
                ]
          },
          sample_data: isFirstDataset 
            ? [
                {
                  sale_id: "S12345",
                  date: "2023-02-15T10:30:00Z",
                  customer_id: "C5001",
                  product_id: "P100",
                  quantity: 2,
                  unit_price: 49.99,
                  total: 99.98
                },
                {
                  sale_id: "S12346",
                  date: "2023-02-15T11:15:00Z",
                  customer_id: "C5002",
                  product_id: "P105",
                  quantity: 1,
                  unit_price: 199.99,
                  total: 199.99
                }
              ] 
            : [
                {
                  feedback_id: "F1001",
                  customer_id: "C5001",
                  date: "2023-03-10T14:22:00Z",
                  score: 9,
                  comment: "Great service, very satisfied!",
                  category: "Support"
                },
                {
                  feedback_id: "F1002",
                  customer_id: "C5010",
                  date: "2023-03-11T09:45:00Z",
                  score: 6,
                  comment: "Product works well but shipping was slow",
                  category: "Logistics"
                }
              ],
          stats: {
            missing_values: isFirstDataset ? 42 : 18,
            outliers: isFirstDataset ? 15 : 7,
            duplicates: isFirstDataset ? 3 : 0
          }
        }
      };
    } catch (error) {
      console.error(`Error fetching dataset details for ${datasetId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to fetch dataset details"
      };
    }
  }
};
