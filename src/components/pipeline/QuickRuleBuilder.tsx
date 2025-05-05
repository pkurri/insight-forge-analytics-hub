import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Chip,
  Alert,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Help as HelpIcon
} from '@mui/icons-material';

interface Rule {
  id: string;
  name: string;
  description?: string;
  severity: 'high' | 'medium' | 'low';
  rule_type?: string;
  source?: string;
  tags?: string[];
  condition?: string;
}

interface QuickRuleBuilderProps {
  onAddRule: (rule: Rule) => void;
  onCancel?: () => void;
}

/**
 * QuickRuleBuilder component for rapidly creating simple validation rules
 */
const QuickRuleBuilder: React.FC<QuickRuleBuilderProps> = ({
  onAddRule,
  onCancel
}) => {
  const [rule, setRule] = useState<Partial<Rule>>({
    name: '',
    description: '',
    severity: 'medium',
    rule_type: 'validation',
    source: 'quick_builder',
    tags: [],
    condition: ''
  });

  const [error, setError] = useState<string | null>(null);

  const handleChange = (field: keyof Rule, value: any) => {
    setRule(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleAddRule = () => {
    if (!rule.name) {
      setError('Rule name is required');
      return;
    }

    if (!rule.condition) {
      setError('Rule condition is required');
      return;
    }

    onAddRule({
      id: `rule_${Date.now()}`,
      name: rule.name,
      description: rule.description,
      severity: rule.severity as 'high' | 'medium' | 'low',
      rule_type: rule.rule_type,
      source: rule.source,
      tags: rule.tags,
      condition: rule.condition
    });

    // Reset form
    setRule({
      name: '',
      description: '',
      severity: 'medium',
      rule_type: 'validation',
      source: 'quick_builder',
      tags: [],
      condition: ''
    });
    setError(null);
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    }
  };

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">
          Quick Rule Builder
        </Typography>
        <Tooltip title="Create simple validation rules quickly">
          <IconButton size="small">
            <HelpIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box display="flex" flexDirection="column" gap={2}>
        <TextField
          label="Rule Name"
          fullWidth
          value={rule.name}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleChange('name', e.target.value)}
          required
          error={!!error && !rule.name}
          helperText={error && !rule.name ? 'Rule name is required' : ''}
        />

        <TextField
          label="Description"
          fullWidth
          multiline
          rows={2}
          value={rule.description}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleChange('description', e.target.value)}
        />

        <Box display="flex" gap={2}>
          <FormControl fullWidth>
            <InputLabel>Severity</InputLabel>
            <Select
              value={rule.severity}
              label="Severity"
              onChange={(e: SelectChangeEvent) => handleChange('severity', e.target.value)}
            >
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="low">Low</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Rule Type</InputLabel>
            <Select
              value={rule.rule_type}
              label="Rule Type"
              onChange={(e: SelectChangeEvent) => handleChange('rule_type', e.target.value)}
            >
              <MenuItem value="validation">Validation</MenuItem>
              <MenuItem value="transformation">Transformation</MenuItem>
              <MenuItem value="enrichment">Enrichment</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <TextField
          label="Tags"
          fullWidth
          value={rule.tags?.join(', ')}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => 
            handleChange('tags', e.target.value.split(',').map((tag: string) => tag.trim()))
          }
          helperText="Comma-separated tags"
        />

        <TextField
          label="Condition"
          fullWidth
          multiline
          rows={3}
          value={rule.condition}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleChange('condition', e.target.value)}
          required
          error={!!error && !rule.condition}
          helperText={
            error && !rule.condition 
              ? 'Rule condition is required' 
              : 'Enter the rule condition in SQL-like syntax'
          }
        />

        <Box display="flex" justifyContent="flex-end" gap={1}>
          {onCancel && (
            <Button
              variant="outlined"
              onClick={handleCancel}
              startIcon={<DeleteIcon />}
            >
              Cancel
            </Button>
          )}
          <Button
            variant="contained"
            onClick={handleAddRule}
            startIcon={<AddIcon />}
          >
            Add Rule
          </Button>
        </Box>
      </Box>
    </Paper>
  );
};

export default QuickRuleBuilder; 