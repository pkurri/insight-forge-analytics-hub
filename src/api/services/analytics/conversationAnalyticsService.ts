import { callApi } from '../../utils/apiUtils';

export interface Stats {
  conversations?: number;
  messages?: number;
  evaluations?: number;
  users?: number;
  anomalies?: number;
}
export interface Feedback {
  category_counts?: Record<string, number>;
}
export interface Volume {
  [date: string]: number;
}
export interface Anomaly {
  timestamp: string;
  reason: string;
  dataset_id?: string | number;
}

const BASE = '/conversation-analytics';

export interface FeedbackRatingsHistogram {
  [rating: string]: number;
}
export interface ActiveUsersOverTime {
  [date: string]: number;
}

export interface CohortDataPoint {
  cohort: string;
  retention: number[];
}
export interface CohortAnalysisResult {
  cohorts: CohortDataPoint[];
  periods: string[];
}
export interface FirstResponseTimeResult {
  avgTime: number;
  medianTime?: number;
}

export interface ConversationLengthBin {
  bin: string;
  count: number;
}

export interface FunnelStage {
  name: string;
  value: number;
}

export interface UserSegment {
  segment: string;
  count: number;
}

export const conversationAnalyticsService = {
  getMemoryStats(): Promise<Stats> {
    return callApi(`${BASE}/memory-stats`);
  },
  getFeedbackSummary(): Promise<Feedback> {
    return callApi(`${BASE}/feedback-summary`);
  },
  getMessageVolumeOverTime(freq: 'D' | 'H' = 'D'): Promise<Volume> {
    return callApi(`${BASE}/message-volume-over-time?freq=${freq}`);
  },
  getAnomalyReport(): Promise<Anomaly[]> {
    return callApi(`${BASE}/anomaly-report`);
  },
  getMostCommonFeedback(n = 3): Promise<string[]> {
    return callApi(`${BASE}/common-feedback?n=${n}`);
  },
  getFeedbackRatingsHistogram(): Promise<FeedbackRatingsHistogram> {
    return callApi(`${BASE}/feedback-ratings-histogram`);
  },
  getActiveUsersOverTime(freq: 'D' | 'H' = 'D'): Promise<ActiveUsersOverTime> {
    return callApi(`${BASE}/active-users-over-time?freq=${freq}`);
  },
  getCohortAnalysis(): Promise<CohortAnalysisResult> {
    return callApi(`${BASE}/cohort-analysis`);
  },
  getFirstResponseTime(): Promise<{ avgTime: number; medianTime: number }> {
    return callApi(`${BASE}/first-response-time`);
  },
  getConversationLengthDistribution(): Promise<{ bin: string; count: number }[]> {
    return callApi(`${BASE}/conversation-length-distribution`);
  },
  getFunnelAnalysis(): Promise<{ name: string; value: number }[]> {
    return callApi(`${BASE}/funnel-analysis`);
  },
  getUserSegmentation(): Promise<{ segment: string; count: number }[]> {
    return callApi(`${BASE}/user-segmentation`);
  },
};
