import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { Loader2, Filter, PlusCircle, RefreshCw, Sparkles, Check, X, Upload, Download, FileText, AlertCircle } from 'lucide-react';
import { api } from '@/api/api';
import type { BusinessRule } from '@/api/services/businessRules/businessRulesService';

// Import our new components
import RuleSelector from './RuleSelector';
import RulePreview from './RulePreview';
import QuickRuleBuilder from './QuickRuleBuilder';
import RuleStatusIndicator from './RuleStatusIndicator';

interface EnhancedBusinessRulesProps {
  datasetId: string;
  sampleData?: any[];
  onRulesApplied?: (ruleIds: string[]) => void;
  onComplete?: () => void;
}

const EnhancedBusinessRules: React.FC<EnhancedBusinessRulesProps> = ({ 
  datasetId, 
  sampleData = [],
  onRulesApplied,
  onComplete
}) => {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<string>('select');
  const [selectedRules, setSelectedRules] = useState<string[]>([]);
  const [ruleObjects, setRuleObjects] = useState<BusinessRule[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [showRuleBuilder, setShowRuleBuilder] = useState(false);
  const [impactAnalysis, setImpactAnalysis] = useState<any>(null);
  const [ruleStatus, setRuleStatus] = useState<'idle' | 'pending' | 'processing' | 'success' | 'failed' | 'warning'>('idle');
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [suggestedRules, setSuggestedRules] = useState<BusinessRule[]>([]);

  // Fetch rules for the dataset
  const fetchRules = useCallback(async () => {
    if (!datasetId) return;
    
    setIsLoading(true);
    try {
      const response = await api.businessRules.getBusinessRules(datasetId);
      if (response.success) {
        setRuleObjects(response.data as BusinessRule[] || []);
      } else {
        toast({
          title: 'Failed to load rules',
          description: response.error || 'Unknown error occurred',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch business rules',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [datasetId, toast]);

  // Fetch rule suggestions if sample data is available
  const fetchRuleSuggestions = useCallback(async () => {
    if (!datasetId || !sampleData || sampleData.length === 0) return;
    
    try {
      const response = await api.businessRules.suggestRules(datasetId, sampleData);
      if (response.success && response.data) {
        setSuggestedRules(response.data.suggested_rules || []);
      }
    } catch (error) {
      console.error('Error fetching rule suggestions:', error);
    }
  }, [datasetId, sampleData]);

  // Load rules and suggestions on component mount
  useEffect(() => {
    fetchRules();
    if (sampleData && sampleData.length > 0) {
      fetchRuleSuggestions();
    }
  }, [fetchRules, fetchRuleSuggestions, sampleData]);

  // Handle rule selection change
  const handleRuleSelectionChange = (ruleIds: string[]) => {
    setSelectedRules(ruleIds);
    
    // If we have sample data, analyze the impact of selected rules
    if (sampleData && sampleData.length > 0 && ruleIds.length > 0) {
      analyzeRuleImpact(ruleIds);
    } else {
      setImpactAnalysis(null);
    }
  };

  // Analyze the impact of selected rules on sample data
  const analyzeRuleImpact = async (ruleIds: string[]) => {
    if (!sampleData || sampleData.length === 0 || ruleIds.length === 0) return;
    
    try {
      const response = await api.businessRules.testRulesOnSample(datasetId, sampleData, ruleIds);
      if (response.success && response.data) {
        const { validation_results, impact_metrics } = response.data;
        
        setImpactAnalysis({
          totalRecords: impact_metrics?.total_records || sampleData.length,
          passingRecords: impact_metrics?.records_passing_validation || 0,
          failingRecords: impact_metrics?.records_failing_validation || 0,
          impactPercentage: impact_metrics?.impact_percentage || 0
        });
      }
    } catch (error) {
      console.error('Error analyzing rule impact:', error);
    }
  };

  // Handle rule creation from QuickRuleBuilder
  const handleRuleCreated = (newRule: BusinessRule) => {
    setRuleObjects(prev => [...prev, newRule]);
    setSelectedRules(prev => [...prev, newRule.id]);
    setShowRuleBuilder(false);
    
    toast({
      title: 'Rule Created',
      description: `Rule "${newRule.name}" has been created successfully.`,
    });
  };

  // Apply selected rules to the dataset
  const handleApplyRules = async () => {
    if (selectedRules.length === 0) {
      toast({
        title: 'No Rules Selected',
        description: 'Please select at least one rule to apply.',
        variant: 'destructive',
      });
      return;
    }
    
    setIsApplying(true);
    setRuleStatus('processing');
    setStatusMessage('Applying business rules to dataset...');
    
    try {
      // Apply rules to the dataset
      const response = await api.businessRules.applyRules(datasetId, selectedRules);
      
      if (response.success) {
        setRuleStatus('success');
        setStatusMessage(`Successfully applied ${selectedRules.length} rules to the dataset.`);
        
        toast({
          title: 'Rules Applied',
          description: `Successfully applied ${selectedRules.length} rules to the dataset.`,
        });
        
        // Call the onRulesApplied callback if provided
        if (onRulesApplied) {
          onRulesApplied(selectedRules);
        }
        
        // Call the onComplete callback if provided
        if (onComplete) {
          onComplete();
        }
      } else {
        setRuleStatus('failed');
        setStatusMessage(`Failed to apply rules: ${response.error || 'Unknown error'}`);
        
        toast({
          title: 'Failed to Apply Rules',
          description: response.error || 'Unknown error occurred',
          variant: 'destructive',
        });
      }
    } catch (error) {
      setRuleStatus('failed');
      setStatusMessage('Error applying rules. Please try again.');
      
      toast({
        title: 'Error',
        description: 'Failed to apply business rules',
        variant: 'destructive',
      });
    } finally {
      setIsApplying(false);
    }
  };

  // Export selected rules to JSON
  const handleExportRules = () => {
    const rulesToExport = ruleObjects.filter(rule => selectedRules.includes(rule.id));
    const dataStr = JSON.stringify(rulesToExport, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `business_rules_${datasetId}_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    toast({
      title: 'Rules Exported',
      description: `Exported ${rulesToExport.length} rules to JSON file.`,
    });
  };

  // Get selected rule objects
  const getSelectedRuleObjects = () => {
    return ruleObjects.filter(rule => selectedRules.includes(rule.id));
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Business Rules
              {selectedRules.length > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {selectedRules.length} selected
                </Badge>
              )}
            </CardTitle>
            <CardDescription>
              Define, select, and apply business rules to your dataset
            </CardDescription>
          </div>
          <RuleStatusIndicator 
            status={ruleStatus} 
            message={statusMessage} 
          />
        </div>
      </CardHeader>
      <CardContent>
        {showRuleBuilder ? (
          <QuickRuleBuilder 
            datasetId={datasetId}
            onRuleCreated={handleRuleCreated}
            onCancel={() => setShowRuleBuilder(false)}
            sampleData={sampleData}
            suggestedRules={suggestedRules}
          />
        ) : (
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="select">Select Rules</TabsTrigger>
              <TabsTrigger value="preview">Rule Preview</TabsTrigger>
            </TabsList>
            
            <TabsContent value="select">
              <RuleSelector 
                datasetId={datasetId}
                selectedRules={selectedRules}
                onRuleSelectionChange={handleRuleSelectionChange}
                showAddNew={true}
                onAddNewRule={() => setShowRuleBuilder(true)}
                sampleData={sampleData}
              />
            </TabsContent>
            
            <TabsContent value="preview">
              <RulePreview 
                rules={getSelectedRuleObjects()}
                onRemoveRule={(ruleId) => setSelectedRules(prev => prev.filter(id => id !== ruleId))}
                impactAnalysis={impactAnalysis}
                showActions={true}
                onApplyRules={handleApplyRules}
              />
            </TabsContent>
          </Tabs>
        )}
      </CardContent>
      <CardFooter className="flex justify-between">
        <div>
          <Button
            variant="outline"
            onClick={handleExportRules}
            disabled={selectedRules.length === 0}
            className="mr-2"
          >
            <Download className="h-4 w-4 mr-2" />
            Export Rules
          </Button>
        </div>
        <div>
          {!showRuleBuilder && (
            <Button
              variant="default"
              onClick={handleApplyRules}
              disabled={isApplying || selectedRules.length === 0}
            >
              {isApplying ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Check className="h-4 w-4 mr-2" />
              )}
              {isApplying ? 'Applying...' : 'Apply Rules'}
            </Button>
          )}
        </div>
      </CardFooter>
    </Card>
  );
};

export default EnhancedBusinessRules;
