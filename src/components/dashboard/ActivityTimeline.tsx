
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface ActivityItem {
  id: string;
  message: string;
  timestamp: string;
  type: 'info' | 'success' | 'warning' | 'error';
}

interface ActivityTimelineProps {
  activities: ActivityItem[];
}

const ActivityTimeline: React.FC<ActivityTimelineProps> = ({ activities }) => {
  const getActivityColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-success';
      case 'warning':
        return 'bg-warning';
      case 'error':
        return 'bg-error';
      case 'info':
      default:
        return 'bg-info';
    }
  };

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activities.map((activity) => (
            <div key={activity.id} className="flex gap-3">
              <div className="flex flex-col items-center">
                <div className={cn("w-3 h-3 rounded-full", getActivityColor(activity.type))} />
                <div className="w-[1px] h-full bg-gray-200" />
              </div>
              <div className="pb-4">
                <p className="text-sm">{activity.message}</p>
                <time className="text-xs text-gray-500">{activity.timestamp}</time>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default ActivityTimeline;
