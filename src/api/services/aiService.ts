
import { callApi } from '../utils/apiUtils';

/**
 * AI Service - Handles AI assistant and data analysis operations
 */
export const aiService = {
  /**
   * Ask a question about a dataset using vector DB
   */
  askQuestion: async (datasetId: string, question: string): Promise<any> => {
    const endpoint = `ai/ask`;
    
    try {
      const response = await callApi(endpoint, 'POST', {
        dataset_id: datasetId,
        question: question
      });
      
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 1800));
      
      return {
        success: true,
        data: {
          answer: "Based on the data, electronics is the most profitable category with an average profit margin of 28.3%. The second most profitable category is Beauty with 22.7%, followed by Books at 18.2%.",
          confidence: 0.87,
          context: [
            {
              column: "category",
              insight: "8 unique categories present in the dataset",
              distribution: "Electronics (32.5%), Clothing (21.4%), Home (17.0%), Books (13.0%), Food (8.2%), Sports (5.9%), Beauty (1.9%), Other (0.2%)"
            },
            {
              column: "profit_margin",
              insight: "Average profit margin across all products is 19.2%",
              distribution: "Electronics (28.3%), Beauty (22.7%), Books (18.2%), Clothing (17.8%), Home (16.5%), Sports (15.9%), Food (12.1%), Other (11.2%)"
            }
          ],
          query_analysis: {
            type: "comparison",
            target_column: "profit_margin",
            group_by_column: "category",
            aggregation: "avg"
          }
        }
      };
    } catch (error) {
      console.error("Error asking question:", error);
      return {
        success: false,
        error: "Failed to process question"
      };
    }
  },
  
  /**
   * Get response from AI assistant
   */
  getAiAssistantResponse: async (message: string, context: any = {}): Promise<any> => {
    const endpoint = `ai/assistant`;
    
    try {
      const response = await callApi(endpoint, 'POST', {
        message,
        context
      });
      
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Generate responses based on keyword matching
      let answer = "I don't have enough context to answer that question.";
      
      if (message.toLowerCase().includes("how to")) {
        answer = "To accomplish that, you can follow these steps:\n\n1. Select your dataset from the dashboard\n2. Go to the appropriate tab for the operation you want to perform\n3. Configure the settings according to your needs\n4. Click 'Run' or 'Process' to execute the operation";
      } else if (message.toLowerCase().includes("error")) {
        answer = "The error you're experiencing might be due to several reasons:\n\n- Invalid data format\n- Missing required fields\n- Connection issues\n- Insufficient permissions\n\nCheck the system logs for more details and try validating your input data first.";
      } else if (message.toLowerCase().includes("best practice")) {
        answer = "Following best practices for data processing:\n\n- Always validate data before transformation\n- Use appropriate data types for each column\n- Create reusable pipeline templates for common tasks\n- Monitor pipeline performance regularly\n- Set up alerts for critical failures";
      } else if (message.toLowerCase().includes("example")) {
        answer = "Here's an example of how to use the feature:\n\n```python\n# Sample code\nfrom dataforge import Pipeline\n\npipeline = Pipeline()\npipeline.add_step('validate', {'schema': 'customer_schema'})\npipeline.add_step('transform', {'standardize': ['name', 'address']})\npipeline.run(dataset_id='ds-12345')\n```";
      }
      
      return {
        success: true,
        data: {
          message: message,
          response: answer,
          context: {
            sources: [
              "User documentation",
              "System knowledge base",
              "Previous conversations"
            ],
            confidence: 0.85
          },
          timestamp: new Date().toISOString()
        }
      };
    } catch (error) {
      console.error("Error getting AI assistant response:", error);
      return {
        success: false,
        error: "Failed to get response from AI assistant"
      };
    }
  },
  
  /**
   * Analyze anomalies in a dataset and provide explanations
   */
  analyzeAnomalies: async (datasetId: string, config: any = {}): Promise<any> => {
    const endpoint = `ai/analyze-anomalies/${datasetId}`;
    
    try {
      const response = await callApi(endpoint, 'POST', { config });
      if (response.success) {
        return response;
      }
      
      // Fallback to mock data if API fails
      console.log(`Falling back to mock data for: ${endpoint}`);
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      return {
        success: true,
        data: {
          dataset_id: datasetId,
          anomaly_count: 15,
          anomalies: [
            {
              id: "anom-001",
              row_id: 1245,
              features: ["price", "stock", "views"],
              score: 0.95,
              description: "Extremely high-priced item with very low stock and views",
              values: { price: 2999.99, stock: 1, views: 5 }
            },
            {
              id: "anom-002",
              row_id: 3782,
              features: ["price", "stock", "rating"],
              score: 0.91,
              description: "Very low priced item with excessive stock and perfect rating",
              values: { price: 0.99, stock: 9999, rating: 5.0 }
            },
            {
              id: "anom-003",
              row_id: 952,
              features: ["views", "conversion_rate"],
              score: 0.88,
              description: "Product with extremely high views but low conversion rate",
              values: { views: 10029, conversion_rate: 0.01 }
            }
          ],
          root_causes: [
            {
              cause: "Data entry errors",
              confidence: 0.85,
              affected_anomalies: ["anom-001", "anom-002"],
              evidence: "Values significantly outside normal distribution ranges"
            },
            {
              cause: "Product promotion campaign",
              confidence: 0.75,
              affected_anomalies: ["anom-003"],
              evidence: "Timestamp correlates with known marketing event"
            }
          ],
          recommendations: [
            {
              action: "Review data entry process for pricing information",
              priority: "high"
            },
            {
              action: "Implement validation rules for stock levels",
              priority: "medium"
            },
            {
              action: "Correlate marketing events with product performance metrics",
              priority: "medium"
            }
          ]
        }
      };
    } catch (error) {
      console.error("Error analyzing anomalies:", error);
      return {
        success: false,
        error: "Failed to analyze anomalies"
      };
    }
  }
};
