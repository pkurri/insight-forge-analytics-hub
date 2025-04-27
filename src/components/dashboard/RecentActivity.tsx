import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Activity, User, Database, Code, MessageSquare } from 'lucide-react';

interface ActivityItem {
  id: string;
  type: 'dataset' | 'pipeline' | 'ai_chat' | 'code';
  description: string;
  timestamp: string;
  user?: string;
}

interface RecentActivityProps {
  activities: ActivityItem[];
  loading?: boolean;
}

const RecentActivity: React.FC<RecentActivityProps> = ({ activities, loading = false }) => {
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'dataset':
        return <Database className="h-5 w-5" />;
      case 'pipeline':
        return <Activity className="h-5 w-5" />;
      case 'ai_chat':
        return <MessageSquare className="h-5 w-5" />;
      case 'code':
        return <Code className="h-5 w-5" />;
      default:
        return <Activity className="h-5 w-5" />;
    }
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>Latest system activity</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="space-y-2">
                  <Skeleton className="h-4 w-48" />
                  <Skeleton className="h-4 w-24" />
                </div>
              </div>
            ))}
          </div>
        ) : activities.length > 0 ? (
          <div className="space-y-6">
            {activities.map((activity) => (
              <div key={activity.id} className="flex items-start gap-4">
                <div className="bg-muted p-2 rounded-full">
                  {getActivityIcon(activity.type)}
                </div>
                <div className="space-y-1">
                  <p className="text-sm">{activity.description}</p>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    {activity.user && (
                      <div className="flex items-center gap-1">
                        <User className="h-3 w-3" />
                        <span>{activity.user}</span>
                      </div>
                    )}
                    <span>{new Date(activity.timestamp).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Activity className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No recent activity</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default RecentActivity;
