import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Collapse,
  Alert,
  Paper,
  Grid
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Delete as DeleteIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

/**
 * RulePreview component to display selected rules and their potential impacts
 * 
 * @param {Object} props Component properties
 * @param {Array} props.rules List of rule objects to preview
 * @param {function} props.onRemoveRule Callback when a rule is removed
 * @param {Object} props.impactAnalysis Impact analysis data (optional)
 * @param {boolean} props.showActions Whether to show action buttons
 * @param {function} props.onApplyRules Callback when "Apply Rules" is clicked
 */
const RulePreview = ({
  rules = [],
  onRemoveRule,
  impactAnalysis = null,
  showActions = true,
  onApplyRules
}) => {
  const theme = useTheme();
  const [expandedRules, setExpandedRules] = useState({});

  // Toggle rule expansion
  const toggleRuleExpansion = (ruleId) => {
    setExpandedRules(prev => ({
      ...prev,
      [ruleId]: !prev[ruleId]
    }));
  };

  // Get severity icon
  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'high':
        return <ErrorIcon color="error" />;
      case 'medium':
        return <WarningIcon color="warning" />;
      case 'low':
        return <InfoIcon color="info" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  // Group rules by type
  const rulesByType = rules.reduce((acc, rule) => {
    const type = rule.rule_type || 'validation';
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(rule);
    return acc;
  }, {});

  // Render impact analysis
  const renderImpactAnalysis = () => {
    if (!impactAnalysis) return null;

    return (
      <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Estimated Impact
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={6} md={3}>
            <Box textAlign="center" p={1}>
              <Typography variant="h4" color="primary">
                {impactAnalysis.totalRecords}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Records
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} md={3}>
            <Box textAlign="center" p={1}>
              <Typography variant="h4" color="success.main">
                {impactAnalysis.passingRecords}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Passing Records
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} md={3}>
            <Box textAlign="center" p={1}>
              <Typography variant="h4" color="error.main">
                {impactAnalysis.failingRecords}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Failing Records
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} md={3}>
            <Box textAlign="center" p={1}>
              <Typography variant="h4" color={impactAnalysis.impactPercentage > 20 ? "error.main" : "warning.main"}>
                {impactAnalysis.impactPercentage}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Impact Rate
              </Typography>
            </Box>
          </Grid>
        </Grid>
        
        {impactAnalysis.impactPercentage > 20 && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            High impact detected. These rules will filter out a significant portion of your data.
          </Alert>
        )}
      </Paper>
    );
  };

  // Render rule card
  const renderRuleCard = (rule) => {
    const isExpanded = !!expandedRules[rule.id];
    
    return (
      <Card key={rule.id} variant="outlined" sx={{ mb: 1 }}>
        <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box display="flex" alignItems="center">
              <ListItemIcon sx={{ minWidth: 32 }}>
                {getSeverityIcon(rule.severity)}
              </ListItemIcon>
              <Typography variant="body1">
                {rule.name}
              </Typography>
            </Box>
            <Box>
              <IconButton 
                size="small" 
                onClick={() => toggleRuleExpansion(rule.id)}
                aria-expanded={isExpanded}
                aria-label="show more"
              >
                {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
              {onRemoveRule && (
                <IconButton 
                  size="small" 
                  onClick={() => onRemoveRule(rule.id)}
                  aria-label="remove rule"
                >
                  <DeleteIcon />
                </IconButton>
              )}
            </Box>
          </Box>
          
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <Box mt={1}>
              {rule.description && (
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {rule.description}
                </Typography>
              )}
              
              <Box display="flex" flexWrap="wrap" gap={0.5} mt={1}>
                <Chip 
                  size="small" 
                  label={rule.rule_type || 'validation'} 
                  color="primary" 
                  variant="outlined" 
                />
                <Chip 
                  size="small" 
                  label={rule.source || 'manual'} 
                  color="secondary" 
                  variant="outlined" 
                />
                {rule.tags && rule.tags.map(tag => (
                  <Chip 
                    key={tag} 
                    size="small" 
                    label={tag} 
                    variant="outlined" 
                  />
                ))}
              </Box>
              
              {rule.condition && (
                <Box mt={1}>
                  <Typography variant="caption" color="text.secondary">
                    Condition:
                  </Typography>
                  <Typography variant="body2" sx={{ 
                    fontFamily: 'monospace', 
                    backgroundColor: 'rgba(0, 0, 0, 0.04)',
                    p: 1,
                    borderRadius: 1,
                    overflowX: 'auto'
                  }}>
                    {rule.condition}
                  </Typography>
                </Box>
              )}
            </Box>
          </Collapse>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Selected Rules ({rules.length})
      </Typography>
      
      {renderImpactAnalysis()}
      
      {rules.length === 0 ? (
        <Typography color="text.secondary">
          No rules selected. Select rules to preview their impact.
        </Typography>
      ) : (
        <Box>
          {Object.entries(rulesByType).map(([type, typeRules]) => (
            <Box key={type} mb={3}>
              <Typography variant="subtitle1" gutterBottom>
                {type.charAt(0).toUpperCase() + type.slice(1)} Rules ({typeRules.length})
              </Typography>
              <List disablePadding>
                {typeRules.map(renderRuleCard)}
              </List>
            </Box>
          ))}
          
          {showActions && (
            <Box mt={3} display="flex" justifyContent="flex-end">
              <Button 
                variant="contained" 
                color="primary" 
                onClick={onApplyRules}
                disabled={rules.length === 0}
              >
                Apply Selected Rules
              </Button>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
};

export default RulePreview;
