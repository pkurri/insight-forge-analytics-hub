import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Checkbox, 
  FormControlLabel, 
  Chip, 
  Button,
  CircularProgress,
  Divider,
  TextField,
  InputAdornment,
  IconButton,
  Tooltip,
  Paper
} from '@mui/material';
import { 
  Search as SearchIcon, 
  FilterList as FilterIcon,
  Add as AddIcon,
  Info as InfoIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import axios from 'axios';
import { API_BASE_URL } from '../../config/constants'; // Adjust path as needed

/**
 * RuleSelector component for selecting business rules during data upload
 * 
 * @param {Object} props Component properties
 * @param {string} props.datasetId The dataset ID
 * @param {Array} props.selectedRules Currently selected rule IDs
 * @param {function} props.onRuleSelectionChange Callback when rule selection changes
 * @param {boolean} props.showAddNew Whether to show the "Add New Rule" button
 * @param {function} props.onAddNewRule Callback when "Add New Rule" is clicked
 * @param {Object} props.sampleData Sample data for rule testing (optional)
 */
const RuleSelector = ({ 
  datasetId, 
  selectedRules = [], 
  onRuleSelectionChange,
  showAddNew = true,
  onAddNewRule,
  sampleData = null
}) => {
  const theme = useTheme();
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    ruleType: null,
    severity: null,
    source: null
  });
  const [testResults, setTestResults] = useState(null);
  const [testingRules, setTestingRules] = useState(false);

  // Fetch rules when component mounts or datasetId changes
  useEffect(() => {
    const fetchRules = async () => {
      setLoading(true);
      setError(null);
      setTestResults(null); // Clear old results
      try {
        const response = await axios.get(`${API_BASE_URL}/business-rules?dataset_id=${datasetId}`);
        if (response.data.success) {
          setRules(response.data.data);
        } else {
          setError('Failed to fetch rules: ' + (response.data.error || 'Unknown error'));
        }
      } catch (err) {
        setError('Error fetching rules: ' + err.message);
      } finally {
        setLoading(false);
      }
    };

    if (datasetId) {
      fetchRules();
    }
  }, [datasetId]);

  // Filter rules based on search term and filters
  const filteredRules = rules.filter(rule => {
    // Search term filter
    const matchesSearch = 
      searchTerm === '' || 
      rule.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (rule.description && rule.description.toLowerCase().includes(searchTerm.toLowerCase()));
    
    // Rule type filter
    const matchesRuleType = 
      !filters.ruleType || 
      rule.rule_type === filters.ruleType;
    
    // Severity filter
    const matchesSeverity = 
      !filters.severity || 
      rule.severity === filters.severity;
    
    // Source filter
    const matchesSource = 
      !filters.source || 
      rule.source === filters.source;
    
    return matchesSearch && matchesRuleType && matchesSeverity && matchesSource;
  });

  // Handle rule selection change
  const handleRuleSelectionChange = (ruleId) => {
    let newSelectedRules;
    if (selectedRules.includes(ruleId)) {
      newSelectedRules = selectedRules.filter(id => id !== ruleId);
    } else {
      newSelectedRules = [...selectedRules, ruleId];
    }
    onRuleSelectionChange(newSelectedRules);
  };

  // Test rules against sample data
  const handleTestRules = async () => {
    if (!sampleData || sampleData.length === 0) {
      setError('No sample data available for testing');
      return;
    }

    setTestingRules(true);
    setError(null); // Clear previous errors
    try {
      const response = await axios.post(
        `${API_BASE_URL}/business-rules/test-sample/${datasetId}`, 
        {
          sample_data: sampleData,
          // Send all rules if none are selected, otherwise send selected
          rule_ids: selectedRules.length > 0 ? selectedRules : rules.map(r => r.id) 
        }
      );
      
      if (response.data.success) {
        setTestResults(response.data.data);
      } else {
        setError('Failed to test rules: ' + (response.data.error || 'Unknown error'));
      }
    } catch (err) {
      setError('Error testing rules: ' + err.message);
    } finally {
      setTestingRules(false);
    }
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

  // Render rule card
  const renderRuleCard = (rule) => {
    const isSelected = selectedRules.includes(rule.id);
    const testResult = testResults?.validation_results?.rule_results?.find(r => r.id === rule.id);
    
    return (
      <Card 
        key={rule.id} 
        variant="outlined" 
        sx={{ 
          mb: 1.5, 
          border: isSelected ? `2px solid ${theme.palette.primary.main}` : '1px solid rgba(0, 0, 0, 0.12)',
          backgroundColor: isSelected ? theme.palette.action.selected : 'transparent',
          transition: 'background-color 0.2s ease-in-out, border-color 0.2s ease-in-out'
        }}
      >
        <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start">
            <FormControlLabel
              control={
                <Checkbox 
                  checked={isSelected} 
                  onChange={() => handleRuleSelectionChange(rule.id)} 
                  size="small"
                  sx={{ p: 0.5, mr: 1}}
                />
              }
              label={
                <Box>
                  <Typography variant="subtitle1" fontWeight="medium">
                    {rule.name}
                  </Typography>
                  {rule.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                      {rule.description}
                    </Typography>
                  )}
                </Box>
              }
              sx={{ alignItems: 'flex-start' }} // Align checkbox with top of text
            />
            <Box display="flex" alignItems="center" ml={1}>
              <Tooltip title={`Severity: ${rule.severity}`}>
                {getSeverityIcon(rule.severity)}
              </Tooltip>
            </Box>
          </Box>
          
          <Box mt={1.5} display="flex" flexWrap="wrap" gap={0.5}>
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
          
          {testResult && (
            <Box mt={2} p={1} bgcolor={theme.palette.action.hover} borderRadius={1}>
              <Typography variant="body2" fontWeight="medium">
                Test Results: 
                {testResult.violation_count === 0 ? (
                  <Chip 
                    size="small" 
                    icon={<CheckIcon fontSize="small" />} 
                    label="All data passed" 
                    color="success" 
                    sx={{ ml: 1 }} 
                  />
                ) : (
                  <Chip 
                    size="small" 
                    icon={<ErrorIcon fontSize="small" />} 
                    label={`${testResult.violation_count} violations`}
                    color="error" 
                    sx={{ ml: 1 }} 
                  />
                )}
              </Typography>
              {testResult.violation_count > 0 && testResult.violations && testResult.violations.length > 0 && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  First violation: {testResult.violations[0].message}
                </Typography>
              )}
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  // Render test results summary
  const renderTestResultsSummary = () => {
    if (!testResults) return null;
    
    const { validation_results, impact_metrics } = testResults;
    
    return (
      <Paper variant="outlined" sx={{ mt: 2, mb: 2, p: 2 }}>
        <Typography variant="subtitle1" gutterBottom>Test Results Summary</Typography>
        <Box mt={1}>
          <Typography variant="body2">
            <strong>Rules Tested:</strong> {validation_results.total_rules}
          </Typography>
          <Typography variant="body2">
            <strong>Passed Rules:</strong> {validation_results.passed_rules}
          </Typography>
          <Typography variant="body2">
            <strong>Failed Rules:</strong> {validation_results.failed_rules}
          </Typography>
          <Typography variant="body2">
            <strong>Total Violations:</strong> {validation_results.total_violations}
          </Typography>
        </Box>
        
        {impact_metrics && (
          <>
            <Divider sx={{ my: 1.5 }} />
            <Typography variant="subtitle2">Impact Analysis</Typography>
            <Box mt={1}>
              <Typography variant="body2">
                <strong>Records Analyzed:</strong> {impact_metrics.total_records}
              </Typography>
              <Typography variant="body2">
                <strong>Records Passing Validation:</strong> {impact_metrics.records_passing_validation}
              </Typography>
              <Typography variant="body2">
                <strong>Records Failing Validation:</strong> {impact_metrics.records_failing_validation}
              </Typography>
              <Typography variant="body2">
                <strong>Impact Percentage:</strong> {impact_metrics.impact_percentage?.toFixed(2)}%
              </Typography>
            </Box>
          </>
        )}
      </Paper>
    );
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2} flexWrap="wrap">
        <Typography variant="h6">Select Business Rules</Typography>
        <Box>
          {showAddNew && (
            <Button 
              startIcon={<AddIcon />} 
              variant="outlined" 
              onClick={onAddNewRule}
              size="small"
              sx={{ mr: 1 }}
            >
              Add New Rule
            </Button>
          )}
          {sampleData && (
            <Button 
              variant="contained" 
              onClick={handleTestRules}
              size="small"
              disabled={testingRules || rules.length === 0}
              startIcon={testingRules ? <CircularProgress size={16} color="inherit" /> : null}
            >
              {testingRules ? 'Testing...' : (selectedRules.length > 0 ? 'Test Selected Rules' : 'Test All Rules')}
            </Button>
          )}
        </Box>
      </Box>
      
      {/* Search and filters */}
      <Box mb={2}>
        <TextField
          fullWidth
          placeholder="Search rules by name or description..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <IconButton disabled // Filter functionality not implemented yet
                >
                  <FilterIcon />
                </IconButton>
              </InputAdornment>
            )
          }}
          size="small"
          variant="outlined"
        />
      </Box>
      
      {/* Test results summary */}
      {renderTestResultsSummary()}
      
      {/* Rules list */}
      {loading ? (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Typography color="error" sx={{ mb: 2 }}>Error: {error}</Typography>
      ) : filteredRules.length === 0 ? (
        <Typography sx={{ mb: 2 }}>No rules found matching your criteria. {showAddNew && 'You can create a new rule.'}</Typography>
      ) : (
        <Box>
          <Typography variant="caption" color="text.secondary" mb={1} display="block">
            {selectedRules.length} of {filteredRules.length} rules selected
          </Typography>
          {filteredRules.map(renderRuleCard)}
        </Box>
      )}
    </Box>
  );
};

export default RuleSelector;
