import React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, CheckCircle, AlertTriangle, Info, HelpCircle } from 'lucide-react';

interface RuleStatus {
  status: 'success' | 'error' | 'warning' | 'info' | 'in_progress';
  message?: string;
  total?: number;
  passed?: number;
  failed?: number;
  skipped?: number;
}

interface RuleStatusIndicatorProps {
  status: RuleStatus;
  showDetails?: boolean;
  className?: string;
}

/**
 * RuleStatusIndicator component to display the status of rule execution
 */
const RuleStatusIndicator: React.FC<RuleStatusIndicatorProps> = ({
  status,
  showDetails = true,
  className = ''
}) => {
  // Get status color
  const getStatusColor = () => {
    switch (status.status) {
      case 'success':
        return 'text-success';
      case 'error':
        return 'text-destructive';
      case 'warning':
        return 'text-warning';
      case 'info':
        return 'text-info';
      case 'in_progress':
        return 'text-primary';
      default:
        return 'text-muted-foreground';
    }
  };

  // Get status icon
  const getStatusIcon = () => {
    switch (status.status) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-success" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-destructive" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-warning" />;
      case 'info':
        return <Info className="h-5 w-5 text-info" />;
      case 'in_progress':
        return <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary" />;
      default:
        return <HelpCircle className="h-5 w-5 text-muted-foreground" />;
    }
  };

  // Get status text
  const getStatusText = () => {
    switch (status.status) {
      case 'success':
        return 'All Rules Passed';
      case 'error':
        return 'Rules Failed';
      case 'warning':
        return 'Rules Warning';
      case 'info':
        return 'Rules Info';
      case 'in_progress':
        return 'Rules Processing';
      default:
        return 'Unknown Status';
    }
  };

  return (
    <Card className={className}>
      <CardHeader className="p-4">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <CardTitle className={`text-base ${getStatusColor()}`}>
            {getStatusText()}
          </CardTitle>
        </div>
        {status.message && (
          <CardDescription className="mt-2">
            {status.message}
          </CardDescription>
        )}
      </CardHeader>

      {showDetails && (status.total !== undefined || status.passed !== undefined || 
        status.failed !== undefined || status.skipped !== undefined) && (
        <CardContent className="p-4 pt-0">
          <div className="flex flex-wrap gap-2">
            {status.total !== undefined && (
              <Badge variant="outline" className="gap-1">
                Total: {status.total}
              </Badge>
            )}
            {status.passed !== undefined && (
              <Badge variant="outline" className="gap-1 text-success">
                <CheckCircle className="h-3 w-3" />
                Passed: {status.passed}
              </Badge>
            )}
            {status.failed !== undefined && (
              <Badge variant="outline" className="gap-1 text-destructive">
                <AlertCircle className="h-3 w-3" />
                Failed: {status.failed}
              </Badge>
            )}
            {status.skipped !== undefined && (
              <Badge variant="outline" className="gap-1 text-muted-foreground">
                <HelpCircle className="h-3 w-3" />
                Skipped: {status.skipped}
              </Badge>
            )}
          </div>

          {status.failed && status.failed > 0 && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {status.failed} rule{status.failed !== 1 ? 's' : ''} failed validation
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      )}
    </Card>
  );
};

export default RuleStatusIndicator; 