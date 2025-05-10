import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, AlertTriangle, Info } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface Alert {
  id: string;
  title: string;
  message: string;
  severity: 'critical' | 'warning' | 'info';
  timestamp: string;
}

interface SystemAlertsProps {
  alerts: Alert[];
  loading?: boolean;
}

const SystemAlerts: React.FC<SystemAlertsProps> = ({ alerts, loading = false }) => {
  if (loading) {
    return (
      <Card className="col-span-1">
        <CardHeader>
          <CardTitle>System Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center py-8">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          System Alerts
          {alerts.length > 0 && (
            <Badge variant={alerts.some(a => a.severity === 'critical') ? 'destructive' : 'outline'}>
              {alerts.length} {alerts.length === 1 ? 'Alert' : 'Alerts'}
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Info className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No system alerts</p>
            <p className="text-sm text-muted-foreground mt-2">All systems operating normally</p>
          </div>
        ) : (
          <div className="space-y-4">
            {alerts.map((alert) => (
              <div 
                key={alert.id} 
                className={`p-4 rounded-md flex items-start gap-3 ${
                  alert.severity === 'critical' 
                    ? 'bg-destructive/10 border border-destructive/20' 
                    : alert.severity === 'warning' 
                      ? 'bg-amber-500/10 border border-amber-500/20' 
                      : 'bg-secondary border border-border'
                }`}
              >
                {alert.severity === 'critical' ? (
                  <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
                ) : alert.severity === 'warning' ? (
                  <AlertTriangle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
                ) : (
                  <Info className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                )}
                <div className="space-y-1">
                  <div className="font-medium">{alert.title}</div>
                  <p className="text-sm text-muted-foreground">{alert.message}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(alert.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default SystemAlerts;
