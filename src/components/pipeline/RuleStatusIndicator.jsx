import React from 'react';
import {
  Box,
  Chip,
  CircularProgress,
  Typography,
  Tooltip
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  HourglassEmpty as HourglassEmptyIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

/**
 * RuleStatusIndicator component to display the status of rule application
 * 
 * @param {Object} props Component properties
 * @param {'idle' | 'pending' | 'processing' | 'success' | 'failed' | 'warning'} props.status Current status
 * @param {string} [props.message] Optional message to display
 * @param {number} [props.progress] Optional progress value (0-100) for processing state
 * @param {string} [props.size='medium'] Size of the indicator ('small' or 'medium')
 */
const RuleStatusIndicator = ({ 
  status = 'idle', 
  message,
  progress,
  size = 'medium'
}) => {
  const theme = useTheme();

  const getStatusProps = () => {
    switch (status) {
      case 'pending':
        return {
          icon: <HourglassEmptyIcon fontSize={size === 'small' ? 'small' : 'inherit'} />,
          color: 'info',
          label: message || 'Pending',
          variant: 'outlined'
        };
      case 'processing':
        return {
          icon: (
            <CircularProgress 
              size={size === 'small' ? 16 : 20} 
              variant={progress !== undefined ? 'determinate' : 'indeterminate'} 
              value={progress}
              color="inherit" // Inherits color from Chip
            />
          ),
          color: 'primary',
          label: message || (progress !== undefined ? `Processing... ${progress}%` : 'Processing...'),
          variant: 'outlined'
        };
      case 'success':
        return {
          icon: <CheckCircleIcon fontSize={size === 'small' ? 'small' : 'inherit'} />,
          color: 'success',
          label: message || 'Completed Successfully',
          variant: 'filled'
        };
      case 'failed':
        return {
          icon: <ErrorIcon fontSize={size === 'small' ? 'small' : 'inherit'} />,
          color: 'error',
          label: message || 'Failed',
          variant: 'filled'
        };
      case 'warning':
        return {
          icon: <WarningIcon fontSize={size === 'small' ? 'small' : 'inherit'} />,
          color: 'warning',
          label: message || 'Completed with Warnings',
          variant: 'filled'
        };
      case 'idle':
      default:
        return {
          icon: <InfoIcon fontSize={size === 'small' ? 'small' : 'inherit'} />,
          color: 'default',
          label: message || 'Idle',
          variant: 'outlined'
        };
    }
  };

  const statusProps = getStatusProps();

  const indicator = (
    <Chip
      icon={statusProps.icon}
      label={statusProps.label}
      color={statusProps.color}
      variant={statusProps.variant}
      size={size}
      sx={{ 
        fontWeight: 500,
        ...(status === 'processing' && { // Ensure progress color matches chip
          '& .MuiCircularProgress-root': {
            color: theme.palette[statusProps.color]?.main || theme.palette.text.primary,
          }
        })
      }}
    />
  );

  // If status is failed or warning and there's a detailed message, wrap in tooltip
  if ((status === 'failed' || status === 'warning') && message && message !== statusProps.label) {
    return (
      <Tooltip title={message} arrow>
        {indicator}
      </Tooltip>
    );
  } 

  return indicator;
};

export default RuleStatusIndicator;
