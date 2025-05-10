import { callApi } from '../../utils/apiUtils';
import { ApiResponse } from '../../api';

export interface TaskProgress {
  progress: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  error?: string;
}

export const taskService = {
  /**
   * Get the progress of a task
   */
  getProgress: async (taskId: string): Promise<ApiResponse<TaskProgress>> => {
    try {
      return await callApi<TaskProgress>(`tasks/${taskId}/progress`);
    } catch (error) {
      console.error('Error fetching task progress:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch task progress'
      };
    }
  },

  /**
   * Cancel a running task
   */
  cancelTask: async (taskId: string): Promise<ApiResponse<void>> => {
    try {
      return await callApi<void>(`tasks/${taskId}/cancel`, 'POST', {});
    } catch (error) {
      console.error('Error canceling task:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to cancel task'
      };
    }
  }
};
