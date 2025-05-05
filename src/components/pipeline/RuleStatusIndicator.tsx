import React from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  Tooltip,
  IconButton,
  Chip
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Help as HelpIcon
} from '@mui/icons-material';

interface RuleStatus {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  inProgress: boolean;
  error?: string;
}

interface RuleStatusIndicatorProps {
  status: RuleStatus;
  onHelpClick?: () => void;
}

/**
 * RuleStatusIndicator component to display the status of rule execution
 */
const RuleStatusIndicator: React.FC<RuleStatusIndicatorProps> = ({
  status,
  onHelpClick
}) => {
  const getStatusColor = () => {
    if (status.error) return 'error';
    if (status.failed > 0) return 'warning';
    if (status.passed === status.total) return 'success';
    return 'info';
  };

  const getStatusIcon = () => {
    if (status.error) return <ErrorIcon color="error" />;
    if (status.failed > 0) return <WarningIcon color="warning" />;
    if (status.passed === status.total) return <CheckCircleIcon color="success" />;
    return <InfoIcon color="info" />;
  };

  const getStatusText = () => {
    if (status.error) return 'Error';
    if (status.inProgress) return 'In Progress';
    if (status.failed > 0) return 'Warnings';
    if (status.passed === status.total) return 'All Passed';
    return 'Incomplete';
  };

  return (
    <Box display="flex" alignItems="center" gap={2}>
      {status.inProgress ? (
        <CircularProgress size={24} />
      ) : (
        getStatusIcon()
      )}

      <Box>
        <Typography variant="body1" color={getStatusColor()}>
          {getStatusText()}
        </Typography>
        
        <Box display="flex" gap={1} mt={0.5}>
          <Chip
            size="small"
            label={`Total: ${status.total}`}
            variant="outlined"
          />
          <Chip
            size="small"
            label={`Passed: ${status.passed}`}
            color="success"
            variant="outlined"
          />
          <Chip
            size="small"
            label={`Failed: ${status.failed}`}
            color="error"
            variant="outlined"
          />
          {status.skipped > 0 && (
            <Chip
              size="small"
              label={`Skipped: ${status.skipped}`}
              color="default"
              variant="outlined"
            />
          )}
        </Box>
      </Box>

      {onHelpClick && (
        <Tooltip title="View detailed status">
          <IconButton size="small" onClick={onHelpClick}>
            <HelpIcon />
          </IconButton>
        </Tooltip>
      )}
    </Box>
  );
};

export default RuleStatusIndicator; 