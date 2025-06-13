import React from 'react';

// Mock implementation of the EnhancedBusinessRules component
const EnhancedBusinessRules: React.FC<{
  datasetId: string;
  sampleData: Array<{ id: number; [key: string]: unknown }>;
  onRulesApplied?: (rules: any[]) => void;
  onComplete?: () => void;
}> = ({ datasetId, sampleData, onRulesApplied = () => {}, onComplete = () => {} }) => {
  const [showRules, setShowRules] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(false);
  
  const handleGenerateRules = () => {
    setIsLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      setShowRules(true);
      setIsLoading(false);
      onRulesApplied([{ id: 'rule-1', name: 'Email Validation' }]);
    }, 500);
  };

  const handleApplyRules = () => {
    onRulesApplied([{ id: 'rule-1', name: 'Email Validation' }]);
  };

  return (
    <div data-testid="enhanced-business-rules">
      <h1>Business Rules</h1>
      <div>Dataset ID: {datasetId}</div>
      <div>Sample Data Rows: {sampleData.length}</div>
      
      <button 
        onClick={handleGenerateRules}
        disabled={isLoading}
        data-testid="generate-rules-button"
      >
        {isLoading ? 'Generating Rules...' : 'Generate Rules'}
      </button>
      
      {showRules && (
        <div data-testid="rules-list">
          <div>Rule 1: Email Validation</div>
          <button 
            onClick={handleApplyRules}
            data-testid="apply-rules-button"
          >
            Apply Selected
          </button>
        </div>
      )}
      
      <button 
        onClick={onComplete}
        data-testid="complete-button"
      >
        Complete
      </button>
    </div>
  );
};

export default EnhancedBusinessRules;
