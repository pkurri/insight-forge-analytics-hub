import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Divider,
  Chip,
  IconButton,
  Grid,
  Paper,
  Alert
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Code as CodeIcon,
  Check as CheckIcon
} from '@mui/icons-material';
import axios from 'axios';
import { API_BASE_URL } from '../../config/constants'; // Adjust the path as needed

/**
 * QuickRuleBuilder component for simple rule creation during the upload process
 * 
 * @param {Object} props Component properties
 * @param {string} props.datasetId The dataset ID
 * @param {function} props.onRuleCreated Callback when a rule is created
 * @param {function} props.onCancel Callback when cancel is clicked
 * @param {Object} props.sampleData Sample data for rule testing (optional)
 * @param {Array} props.suggestedRules Suggested rules based on data analysis (optional)
 */
const QuickRuleBuilder = ({
  datasetId,
  onRuleCreated,
  onCancel,
  sampleData = null,
  suggestedRules = []
}) => {
  const [rule, setRule] = useState({
    name: '',
    description: '',
    rule_type: 'validation',
    severity: 'medium',
    condition: '',
    tags: []
  });
  const [errors, setErrors] = useState({});
  const [newTag, setNewTag] = useState('');
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(suggestedRules.length > 0);

  // Handle rule field change
  const handleChange = (field, value) => {
    setRule(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: null
      }));
    }
  };

  // Add a tag
  const handleAddTag = () => {
    if (!newTag.trim()) return;
    
    if (!rule.tags.includes(newTag.trim())) {
      setRule(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }));
    }
    
    setNewTag('');
  };

  // Remove a tag
  const handleRemoveTag = (tag) => {
    setRule(prev => ({
      ...prev,
      tags: prev.tags.filter(t => t !== tag)
    }));
  };

  // Validate rule
  const validateRule = () => {
    const newErrors = {};
    
    if (!rule.name.trim()) {
      newErrors.name = 'Name is required';
    }
    
    if (!rule.condition.trim()) {
      newErrors.condition = 'Condition is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Save rule
  const handleSaveRule = async () => {
    if (!validateRule()) return;
    
    setSaving(true);
    try {
      const ruleData = {
        ...rule,
        dataset_id: datasetId
      };
      
      const response = await axios.post(`${API_BASE_URL}/business-rules`, ruleData);
      
      if (response.data.success) {
        onRuleCreated(response.data.data);
      } else {
        setErrors({ submit: response.data.error || 'Failed to create rule' });
      }
    } catch (err) {
      setErrors({ submit: err.message || 'Error creating rule' });
    } finally {
      setSaving(false);
    }
  };

  // Test rule
  const handleTestRule = async () => {
    if (!sampleData || sampleData.length === 0) {
      setErrors({ test: 'No sample data available for testing' });
      return;
    }
    
    if (!rule.condition.trim()) {
      setErrors({ condition: 'Condition is required for testing' });
      return;
    }
    
    setTesting(true);
    try {
      // Create a temporary rule for testing
      const testRuleData = {
        ...rule,
        name: rule.name || 'Test Rule',
        id: 'temp-test-rule',
        dataset_id: datasetId
      };
      
      const response = await axios.post(
        `${API_BASE_URL}/business-rules/test-sample/${datasetId}`,
        {
          sample_data: sampleData,
          test_rule: testRuleData
        }
      );
      
      if (response.data.success) {
        setTestResult(response.data.data);
      } else {
        setErrors({ test: response.data.error || 'Failed to test rule' });
      }
    } catch (err) {
      setErrors({ test: err.message || 'Error testing rule' });
    } finally {
      setTesting(false);
    }
  };

  // Use a suggested rule
  const handleUseSuggestedRule = (suggestedRule) => {
    setRule({
      name: suggestedRule.name,
      description: suggestedRule.description || '',
      rule_type: suggestedRule.rule_type || 'validation',
      severity: suggestedRule.severity || 'medium',
      condition: suggestedRule.condition || '',
      tags: suggestedRule.tags || []
    });
    
    setShowSuggestions(false);
  };

  // Render test result
  const renderTestResult = () => {
    if (!testResult) return null;
    
    const { validation_results } = testResult;
    const ruleResult = validation_results.rule_results[0];
    
    if (!ruleResult) return null;
    
    return (
      <Paper variant="outlined" sx={{ p: 2, mt: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          Test Result
        </Typography>
        
        {ruleResult.violation_count === 0 ? (
          <Alert severity="success" icon={<CheckIcon />}>
            Rule passed all {testResult.original_count} records
          </Alert>
        ) : (
          <Alert severity="warning">
            Rule found {ruleResult.violation_count} violations in {testResult.original_count} records
            ({Math.round(ruleResult.violation_count / testResult.original_count * 100)}%)
          </Alert>
        )}
        
        {ruleResult.violation_count > 0 && ruleResult.violations && (
          <Box mt={2}>
            <Typography variant="body2" gutterBottom>
              First violation:
            </Typography>
            <Box 
              sx={{ 
                backgroundColor: 'rgba(0, 0, 0, 0.04)',
                p: 1,
                borderRadius: 1,
                maxHeight: 200,
                overflowY: 'auto'
              }}
            >
              <Typography variant="body2" fontFamily="monospace">
                {JSON.stringify(ruleResult.violations[0], null, 2)}
              </Typography>
            </Box>
          </Box>
        )}
      </Paper>
    );
  };

  // Render suggested rules
  const renderSuggestedRules = () => {
    if (!showSuggestions || suggestedRules.length === 0) return null;
    
    return (
      <Box mb={3}>
        <Typography variant="subtitle1" gutterBottom>
          Suggested Rules
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          These rules were automatically generated based on your data patterns.
        </Typography>
        
        <Grid container spacing={2} sx={{ mt: 1 }}>
          {suggestedRules.slice(0, 3).map((suggestedRule) => (
            <Grid item xs={12} md={4} key={suggestedRule.id || suggestedRule.name}> {/* Use name as fallback key */}
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    {suggestedRule.name}
                  </Typography>
                  {suggestedRule.description && (
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {suggestedRule.description}
                    </Typography>
                  )}
                  <Box display="flex" flexWrap="wrap" gap={0.5} mt={1} mb={2}>
                    <Chip 
                      size="small" 
                      label={suggestedRule.rule_type || 'validation'} 
                      color="primary" 
                      variant="outlined" 
                    />
                    {suggestedRule.confidence && (
                      <Chip 
                        size="small" 
                        label={`Confidence: ${Math.round(suggestedRule.confidence * 100)}%`}
                        color="secondary" 
                        variant="outlined" 
                      />
                    )}
                  </Box>
                  <Button
                    variant="contained"
                    size="small"
                    fullWidth
                    onClick={() => handleUseSuggestedRule(suggestedRule)}
                  >
                    Use This Rule
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
        
        {suggestedRules.length > 3 && (
          <Box mt={1} textAlign="center">
            <Button 
              variant="text" 
              size="small"
              onClick={() => setShowSuggestions(false)}
            >
              Hide Suggestions
            </Button>
          </Box>
        )}
      </Box>
    );
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Create New Rule
      </Typography>
      
      {renderSuggestedRules()}
      
      <Card variant="outlined">
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Rule Name"
                fullWidth
                value={rule.name}
                onChange={(e) => handleChange('name', e.target.value)}
                error={!!errors.name}
                helperText={errors.name}
                required
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <FormControl fullWidth>
                    <InputLabel>Rule Type</InputLabel>
                    <Select
                      value={rule.rule_type}
                      label="Rule Type"
                      onChange={(e) => handleChange('rule_type', e.target.value)}
                    >
                      <MenuItem value="validation">Validation</MenuItem>
                      <MenuItem value="transformation">Transformation</MenuItem>
                      <MenuItem value="enrichment">Enrichment</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={6}>
                  <FormControl fullWidth>
                    <InputLabel>Severity</InputLabel>
                    <Select
                      value={rule.severity}
                      label="Severity"
                      onChange={(e) => handleChange('severity', e.target.value)}
                    >
                      <MenuItem value="low">Low</MenuItem>
                      <MenuItem value="medium">Medium</MenuItem>
                      <MenuItem value="high">High</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                label="Description"
                fullWidth
                multiline
                rows={2}
                value={rule.description}
                onChange={(e) => handleChange('description', e.target.value)}
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                label="Condition (Python/Pandas)"
                fullWidth
                multiline
                rows={4}
                value={rule.condition}
                onChange={(e) => handleChange('condition', e.target.value)}
                error={!!errors.condition}
                helperText={errors.condition || "Example: df['column_name'].notna().all()"}
                required
                InputProps={{
                  style: { fontFamily: 'monospace' },
                }}
              />
            </Grid>
             <Grid item xs={12}>
                <Button 
                    size="small" 
                    color="primary"
                    onClick={handleTestRule}
                    disabled={testing || !sampleData || !rule.condition.trim()}
                    startIcon={testing ? <CircularProgress size={16} /> : <CodeIcon />}
                >
                    {testing ? 'Testing...' : 'Test Rule with Sample Data'}
                </Button>
            </Grid>
            
            <Grid item xs={12}>
              <Box display="flex" alignItems="center" mb={1}>
                <TextField
                  label="Tags"
                  size="small"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                  sx={{ mr: 1 }}
                />
                <Button 
                  variant="outlined" 
                  size="small"
                  onClick={handleAddTag}
                  startIcon={<AddIcon />}
                  disabled={!newTag.trim()}
                >
                  Add
                </Button>
              </Box>
              
              <Box display="flex" flexWrap="wrap" gap={0.5}>
                {rule.tags.map((tag) => (
                  <Chip
                    key={tag}
                    label={tag}
                    onDelete={() => handleRemoveTag(tag)}
                    size="small"
                  />
                ))}
              </Box>
            </Grid>
          </Grid>
          
          {errors.submit && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {errors.submit}
            </Alert>
          )}
          
          {errors.test && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {errors.test}
            </Alert>
          )}
          
          {renderTestResult()}
          
          <Box mt={3} display="flex" justifyContent="flex-end">
            <Button 
              variant="outlined" 
              onClick={onCancel}
              sx={{ mr: 1 }}
            >
              Cancel
            </Button>
            <Button 
              variant="contained" 
              color="primary" 
              onClick={handleSaveRule}
              disabled={saving}
              startIcon={saving ? null : <SaveIcon />}
            >
              {saving ? 'Saving...' : 'Save Rule'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default QuickRuleBuilder;
