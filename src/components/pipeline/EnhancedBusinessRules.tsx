import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Check, X, Plus, RefreshCw, Sparkles, AlertCircle, AlertTriangle } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { api } from '@/api/api';
import type { BusinessRule } from '@/api/services/businessRules/businessRulesService';

// Types
type RuleStatus = 'idle' | 'loading' | 'applying' | 'success' | 'error' | 'generating' | 'warning';
type RuleGenerationEngine = 'openai' | 'anthropic' | 'gemini';
type RuleAction = 'warn' | 'error' | 'correct';
type RuleSeverity = 'low' | 'medium' | 'high';

interface RuleSuggestion extends Omit<BusinessRule, 'severity'> {
  severity: RuleSeverity;
  category?: string;
  isNew?: boolean;
  ruleType: string;
  action: RuleAction;
  id: string;
  condition: string;
  name: string;
  description?: string;
  active?: boolean;
  model_generated?: boolean;
  lastUpdated?: string;
  confidence?: number;
}

interface EnhancedBusinessRulesProps {
  datasetId: string;
  sampleData: Record<string, unknown>[];
  onRulesApplied?: (rules: BusinessRule[]) => void;
  onComplete?: () => void;
}

interface RulePreviewProps {
  rules: BusinessRule[];
  onApply: () => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const RuleStatusIndicator: React.FC<{ status: RuleStatus; message?: string }> = ({ 
  status, 
  message 
}) => {
  if (!status || status === 'idle') return null;

  const statusConfig = {
    loading: { icon: Loader2, className: 'text-blue-500', label: 'Loading...' },
    applying: { icon: Loader2, className: 'text-blue-500', label: 'Applying...' },
    success: { icon: Check, className: 'text-green-500', label: 'Success' },
    error: { icon: X, className: 'text-red-500', label: 'Error' },
    generating: { icon: RefreshCw, className: 'text-yellow-500', label: 'Generating...' },
    warning: { icon: X, className: 'text-yellow-500', label: 'Warning' },
  };

  const { icon: Icon, className, label } = statusConfig[status] || statusConfig.error;

  return (
    <div className={`flex items-center gap-2 text-sm ${className}`}>
      <Icon className="h-4 w-4 animate-spin" />
      <span>{message || label}</span>
    </div>
  );
};

const RulePreview: React.FC<RulePreviewProps> = ({ rules, onApply, onCancel, isLoading = false }) => (
  <Card className="mt-4">
    <CardHeader>
      <CardTitle>Review Generated Rules</CardTitle>
      <CardDescription>Review and apply the generated business rules to your dataset.</CardDescription>
    </CardHeader>
    <CardContent>
      <ScrollArea className="h-64 rounded-md border p-4">
        <div className="space-y-4">
          {rules.map((rule) => (
            <div key={rule.id} className="rounded-lg border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium">{rule.name}</h4>
                  <p className="text-sm text-muted-foreground">
                    {rule.description || 'No description'}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                    {(rule as any).ruleType || 'validation'}
                  </span>
                  <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                    {(rule as any).action || 'warn'}
                  </span>
                </div>
              </div>
              <div className="mt-2">
                <code className="rounded bg-muted px-2 py-1 text-xs">
                  {rule.condition}
                </code>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
        <Button onClick={onApply} disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Applying...
            </>
          ) : (
            `Apply ${rules.length} Rule${rules.length !== 1 ? 's' : ''}`
          )}
        </Button>
      </div>
    </CardContent>
  </Card>
);

const EnhancedBusinessRules: React.FC<EnhancedBusinessRulesProps> = ({
  datasetId,
  sampleData = [],
  onRulesApplied = () => {},
  onComplete = () => {},
}) => {

  // State management
  const [rules, setRules] = useState<BusinessRule[]>([]);
  const [suggestedRules, setSuggestedRules] = useState<RuleSuggestion[]>([]);
  const [selectedRules, setSelectedRules] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRuleBuilderOpen, setIsRuleBuilderOpen] = useState(false);
  const [selectedEngine, setSelectedEngine] = useState<RuleGenerationEngine>('openai');
  const [ruleStatus, setRuleStatus] = useState<RuleStatus>('idle');
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const [newRule, setNewRule] = useState<Omit<BusinessRule, 'id' | 'createdAt' | 'updatedAt' | 'datasetId'>>({ 
    name: '',
    description: '',
    condition: '',
    severity: 'medium' as RuleSeverity,
    message: '',
    active: true,
    confidence: 0,
    lastUpdated: new Date().toISOString(),
    model_generated: false
  });

  // Load existing rules when component mounts
  const loadRules = useCallback(async () => {
    try {
      setIsLoading(true);
      setRuleStatus('loading');
      setStatusMessage('Loading rules...');
      
      const response = await api.businessRules.getBusinessRules(datasetId);
      
      if (response.success) {
        const loadedRules = response.rules || [];
        setRules(loadedRules);
        setRuleStatus('success');
        return loadedRules;
      } else {
        throw new Error(response.error || 'Failed to load rules');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load rules';
      setError(errorMessage);
      setRuleStatus('error');
      setStatusMessage('Error loading rules');
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [datasetId, toast]);

  useEffect(() => {
    loadRules();
  }, [loadRules]);

  // Handle rule generation
  const handleGenerateRules = useCallback(async () => {
    try {
      setIsGenerating(true);
      setRuleStatus('generating');
      setStatusMessage('Generating business rules...');
      
      // Prepare the request payload with proper typing
      const requestData = {
        engine: selectedEngine,
        sampleData: sampleData || []
      };
      
      const response = await api.businessRules.suggestRules(datasetId, requestData);

      if (response.success && response.suggested_rules) {
        const generatedRules: RuleSuggestion[] = response.suggested_rules.map((rule: any) => ({
          ...rule,
          id: rule.id || `generated-${Math.random().toString(36).substr(2, 9)}`,
          isNew: true,
          severity: (rule.severity || 'medium') as RuleSeverity,
          active: rule.active !== undefined ? rule.active : true,
          model_generated: true,
          lastUpdated: new Date().toISOString(),
          confidence: rule.confidence || 0.8 // Default confidence if not provided
        }));
        
        setSuggestedRules(generatedRules);
        setRuleStatus('success');
        setStatusMessage(`${generatedRules.length} rules generated successfully`);
        
        toast({
          title: 'Success',
          description: `Generated ${generatedRules.length} business rules.`,
        });
      } else {
        throw new Error(response.error || 'Failed to generate rules');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate rules';
      console.error('Error generating rules:', err);
      setError(errorMessage);
      setRuleStatus('error');
      setStatusMessage('Error generating rules');
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setIsGenerating(false);
    }
  }, [datasetId, sampleData, selectedEngine, toast]);

  // Handle creating a new rule
  const handleCreateRule = useCallback(async () => {
    try {
      setIsLoading(true);
      setRuleStatus('applying');
      setStatusMessage('Creating rule...');

      const response = await api.businessRules.createBusinessRule(datasetId, {
        ...newRule,
        datasetId,
      });

      if (response.success && response.rule) {
        setRules(prev => [...prev, response.rule!]);
        setNewRule({
          name: '',
          description: '',
          condition: '',
          severity: 'medium',
          message: '',
          active: true,
          confidence: 0,
          lastUpdated: new Date().toISOString(),
          model_generated: false
        });
        setIsRuleBuilderOpen(false);
        setRuleStatus('success');
        setStatusMessage('Rule created successfully');
        
        toast({
          title: 'Success',
          description: 'Business rule has been created successfully.',
        });
      } else {
        throw new Error(response.error || 'Failed to create rule');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create rule';
      setError(errorMessage);
      setRuleStatus('error');
      setStatusMessage('Error creating rule');
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [datasetId, newRule, toast]);

  // Handle applying rules
  const handleApplyRules = useCallback(async (rulesToApply: Array<BusinessRule | RuleSuggestion>) => {
    try {
      setIsLoading(true);
      setRuleStatus('applying');
      setStatusMessage('Applying rules...');

      // Convert RuleSuggestion to BusinessRule if needed
      const rulesToSave = rulesToApply.map(rule => ({
        ...rule,
        // Ensure required fields are present
        id: 'id' in rule ? rule.id : `rule-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
        datasetId: datasetId,
        active: 'active' in rule ? rule.active !== false : true, // Default to true if not set
        severity: rule.severity || 'medium',
        model_generated: 'model_generated' in rule ? rule.model_generated : true,
        lastUpdated: new Date().toISOString(),
        createdAt: 'createdAt' in rule ? rule.createdAt : new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      })) as BusinessRule[];

      const response = await api.businessRules.saveBusinessRules(datasetId, rulesToSave);
      
      if (response.success) {
        // Update local state with the saved rules (which now have proper IDs from the server)
        const savedRules = response.rules || rulesToSave;
        setRules(savedRules);
        
        // Clear suggestions if we just applied them
        if (rulesToApply.some(rule => 'isNew' in rule && rule.isNew)) {
          setSuggestedRules([]);
        }
        
        // Clear selection
        setSelectedRules([]);
        
        // Notify parent component
        onRulesApplied(savedRules);
        
        setRuleStatus('success');
        setStatusMessage(`${savedRules.length} rules applied successfully`);
        
        toast({
          title: 'Success',
          description: `Applied ${savedRules.length} business rules to your dataset.`,
        });
        
        onComplete?.();
      } else {
        throw new Error(response.error || 'Failed to apply rules');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to apply rules';
      console.error('Error applying rules:', err);
      setError(errorMessage);
      setRuleStatus('error');
      setStatusMessage('Error applying rules');
      
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [datasetId, onComplete, onRulesApplied, toast]);

  // Handle input changes for new rule form
  const handleNewRuleChange = useCallback((
    field: keyof Omit<BusinessRule, 'id' | 'createdAt' | 'updatedAt' | 'datasetId'>,
    value: string | boolean | number
  ) => {
    setNewRule(prev => ({
      ...prev,
      [field]: value,
    }));
  }, []);

  // Toggle rule selection
  const toggleRuleSelection = useCallback((ruleId: string) => {
    setSelectedRules(prev => 
      prev.includes(ruleId)
        ? prev.filter(id => id !== ruleId)
        : [...prev, ruleId]
    );
  }, []);

  // Select all rules in the current view
  const selectAllRules = useCallback((ruleIds: string[]) => {
    setSelectedRules(prev => {
      // If all rules are already selected, clear selection
      if (ruleIds.every(id => prev.includes(id))) {
        return [];
      }
      // Otherwise select all rules, preserving any existing selections
      return [...new Set([...prev, ...ruleIds])];
    });
  }, []);

  // Get selected rule objects from both rules and suggestedRules
  const selectedRuleObjects = useMemo(() => {
    const allRules = [...rules, ...suggestedRules];
    return allRules.filter(rule => selectedRules.includes(rule.id));
  }, [rules, suggestedRules, selectedRules]);

  // Get all rule IDs in the current view
  const allRuleIds = useMemo(() => {
    return [...rules, ...suggestedRules].map(rule => rule.id);
  }, [rules, suggestedRules]);

  // Check if all rules are selected
  const allRulesSelected = useMemo(() => {
    return allRuleIds.length > 0 && allRuleIds.every(id => selectedRules.includes(id));
  }, [allRuleIds, selectedRules]);

  // Handle applying selected rules
  const handleApplySelectedRules = useCallback(() => {
    if (selectedRuleObjects.length > 0) {
      handleApplyRules(selectedRuleObjects);
    }
  }, [selectedRuleObjects, handleApplyRules]);
  
  // Toggle rule selection
  const toggleRuleSelection = useCallback((ruleId: string) => {
    setSelectedRules(prev => 
      prev.includes(ruleId)
        ? prev.filter(id => id !== ruleId)
        : [...prev, ruleId]
    );
  }, []);
  
  // Toggle select all rules
  const toggleSelectAllRules = useCallback(() => {
    if (allRulesSelected) {
      setSelectedRules([]);
    } else {
      setSelectedRules([...allRuleIds]);
    }
  }, [allRuleIds, allRulesSelected]);
  
  // Check if a rule is selected
  const isRuleSelected = useCallback((ruleId: string) => {
    return selectedRules.includes(ruleId);
  }, [selectedRules]);
  
  // Check if all rules in the current view are selected
  const areAllRulesSelected = useCallback((ruleIds: string[]) => {
    return ruleIds.length > 0 && ruleIds.every(id => selectedRules.includes(id));
  }, [selectedRules]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col space-y-4 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Business Rules</h2>
          <p className="text-sm text-muted-foreground">
            {rules.length > 0 
              ? `Managing ${rules.length} rule${rules.length !== 1 ? 's' : ''}`
              : 'No rules defined yet'}
          </p>
        </div>
        
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center space-x-2">
            <Label htmlFor="ai-engine" className="text-sm font-medium text-muted-foreground">
              AI Engine:
            </Label>
            <Select
              value={selectedEngine}
              onValueChange={(value: RuleGenerationEngine) => setSelectedEngine(value)}
              disabled={isGenerating}
            >
              <SelectTrigger className="w-[140px]" id="ai-engine">
                <SelectValue placeholder="Select AI Engine" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="anthropic">Anthropic</SelectItem>
                <SelectItem value="gemini">Gemini</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="flex space-x-2">
            <Button
              onClick={handleGenerateRules}
              disabled={isGenerating || sampleData.length === 0}
              variant="outline"
              className="whitespace-nowrap"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Generate Rules
                </>
              )}
            </Button>
            
            <Button
              onClick={() => setIsRuleBuilderOpen(true)}
              disabled={isLoading}
              className="whitespace-nowrap"
            >
              <Plus className="mr-2 h-4 w-4" />
              Create Rule
            </Button>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <X className="h-5 w-5 text-red-400" aria-hidden="true" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Status and Error Display */}
      <div className="space-y-2">
        <RuleStatusIndicator status={ruleStatus} message={statusMessage} />
        
        {error && (
          <div className="rounded-md bg-destructive/10 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <X className="h-5 w-5 text-destructive" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-destructive">Error</h3>
                <div className="mt-1 text-sm text-destructive">
                  <p>{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Tabs */}
      <Tabs defaultValue={suggestedRules.length > 0 ? "suggested" : "existing"} className="space-y-4">
        <div className="flex items-center justify-between">
          <TabsList>
            <TabsTrigger value="suggested" disabled={suggestedRules.length === 0}>
              Suggested Rules {suggestedRules.length > 0 && `(${suggestedRules.length})`}
            </TabsTrigger>
            <TabsTrigger value="existing">
              Existing Rules {rules.length > 0 && `(${rules.length})`}
            </TabsTrigger>
            {selectedRules.length > 0 && (
              <TabsTrigger value="preview" className="ml-2">
                Selected ({selectedRules.length})
              </TabsTrigger>
            )}
          </TabsList>
          
          {rules.length > 0 && (
            <div className="text-sm text-muted-foreground">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => loadRules()}
                disabled={isLoading}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          )}
        </div>

        <TabsContent value="suggested">
          {suggestedRules.length > 0 ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <Checkbox
                    id="select-all-suggested"
                    checked={areAllRulesSelected(suggestedRules.map(r => r.id))}
                    onCheckedChange={() => selectAllRules(suggestedRules.map(r => r.id))}
                  />
                  <Label htmlFor="select-all-suggested" className="text-sm font-medium">
                    {selectedRules.length > 0 
                      ? `${selectedRules.length} selected` 
                      : 'Select all'}
                  </Label>
                </div>
                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setSuggestedRules([])}
                    disabled={isLoading}
                  >
                    <X className="mr-2 h-4 w-4" />
                    Dismiss All
                  </Button>
                  <Button 
                    onClick={() => handleApplyRules(suggestedRules)}
                    disabled={isLoading || suggestedRules.length === 0}
                  >
                    <Check className="mr-2 h-4 w-4" />
                    Apply All ({suggestedRules.length})
                  </Button>
                </div>
              </div>
              
              <div className="space-y-3">
                {suggestedRules.map(rule => (
                  <RuleCard 
                    key={rule.id}
                    rule={rule}
                    isSelected={isRuleSelected(rule.id)}
                    onSelect={() => toggleRuleSelection(rule.id)}
                    onApply={() => handleApplyRules([rule])}
                    onDismiss={() => setSuggestedRules(prev => prev.filter(r => r.id !== rule.id))}
                  />
                ))}
              </div>
            </div>
          ) : (
            <Card className="bg-muted/50">
              <CardHeader className="text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
                  <Sparkles className="h-6 w-6 text-blue-600" />
                </div>
                <CardTitle className="mt-4">No Suggested Rules</CardTitle>
                <CardDescription className="max-w-md mx-auto">
                  Click the "Generate Rules" button to get AI-suggested rules based on your dataset.
                </CardDescription>
                <div className="mt-4">
                  <Button 
                    onClick={handleGenerateRules}
                    disabled={isGenerating || sampleData.length === 0}
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-4 w-4" />
                        Generate Rules
                      </>
                    )}
                  </Button>
                </div>
              </CardHeader>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="existing">
          <Card>
            <CardHeader>
              <CardTitle>Existing Rules</CardTitle>
              <CardDescription>
                {rules.length > 0
                  ? `You have ${rules.length} active rule${rules.length !== 1 ? 's' : ''}`
                  : 'No rules have been created yet.'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {rules.length > 0 ? (
                <div className="space-y-4">
                  {rules.map((rule) => (
                    <div key={rule.id} className="rounded-lg border p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">{rule.name}</h4>
                          <p className="text-sm text-muted-foreground">
                            {rule.description || 'No description'}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                            {(rule as any).ruleType || 'validation'}
                          </span>
                          <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                            {(rule as any).action || 'warn'}
                          </span>
                        </div>
                      </div>
                      <div className="mt-2">
                        <code className="rounded bg-muted px-2 py-1 text-xs">
                          {rule.condition}
                        </code>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex h-40 flex-col items-center justify-center rounded-md border-2 border-dashed p-8 text-center">
                  <p className="text-muted-foreground">No rules found</p>
                  <p className="text-sm text-muted-foreground">
                    Create your first rule to get started
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {selectedRules.length > 0 && (
          <TabsContent value="preview">
            <RulePreview
              rules={selectedRuleObjects}
              onApply={() => handleApplyRules(selectedRuleObjects)}
              onCancel={() => setSelectedRules([])}
              isLoading={isLoading}
            />
          </TabsContent>
        )}
      </Tabs>

      {/* Rule Builder Dialog */}
      {isRuleBuilderOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-2xl">
            <CardHeader>
              <CardTitle>Create New Rule</CardTitle>
              <CardDescription>
                Define a new business rule for your dataset
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="rule-name">Rule Name</Label>
                <Input
                  id="rule-name"
                  placeholder="Enter rule name"
                  value={newRule.name}
                  onChange={(e) => handleNewRuleChange('name', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rule-description">Description (Optional)</Label>
                <Textarea
                  id="rule-description"
                  placeholder="Enter rule description"
                  value={newRule.description}
                  onChange={(e) => handleNewRuleChange('description', e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="rule-severity">Severity</Label>
                  <Select
                    value={newRule.severity}
                    onValueChange={(value) => handleNewRuleChange('severity', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select severity" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="rule-active">Status</Label>
                  <Select
                    value={newRule.active ? 'active' : 'inactive'}
                    onValueChange={(value) => handleNewRuleChange('active', value === 'active')}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="inactive">Inactive</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="rule-condition">Condition</Label>
                <Textarea
                  id="rule-condition"
                  placeholder="Enter rule condition (e.g., value > 100)"
                  className="font-mono text-sm"
                  rows={4}
                  value={newRule.condition}
                  onChange={(e) => handleNewRuleChange('condition', e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Use JavaScript syntax for conditions. The value will be available as 'value'.
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="rule-message">Error Message (Optional)</Label>
                <Input
                  id="rule-message"
                  placeholder="Enter error message to display when condition fails"
                  value={newRule.message}
                  onChange={(e) => handleNewRuleChange('message', e.target.value)}
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setIsRuleBuilderOpen(false)}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleCreateRule} 
                  disabled={isLoading || !newRule.name || !newRule.condition}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create Rule'
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

// Component for displaying individual rule cards
interface RuleCardProps {
  rule: BusinessRule | RuleSuggestion;
  isSelected?: boolean;
  onSelect?: () => void;
  onApply?: () => void;
  onDismiss?: () => void;
}

const RuleCard: React.FC<RuleCardProps> = ({
  rule,
  isSelected = false,
  onSelect,
  onApply,
  onDismiss
}) => {
  const severityIcons = {
    high: <AlertCircle className="h-4 w-4 text-destructive" />,
    medium: <AlertTriangle className="h-4 w-4 text-yellow-500" />,
    low: <AlertCircle className="h-4 w-4 text-blue-500" />
  };

  const actionLabels = {
    error: 'Error',
    warn: 'Warning',
    correct: 'Auto-correct'
  };

  return (
    <div className={`relative rounded-lg border p-4 transition-colors ${isSelected ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'}`}>
      {onSelect && (
        <div className="absolute right-3 top-3">
          <Checkbox 
            id={`select-${rule.id}`}
            checked={isSelected}
            onCheckedChange={onSelect}
            className="h-5 w-5 rounded-md"
          />
        </div>
      )}
      
      <div className="flex items-start justify-between">
        <div className="space-y-1 pr-6">
          <div className="flex items-center space-x-2">
            <h3 className="font-medium">{rule.name}</h3>
            {rule.severity && severityIcons[rule.severity as keyof typeof severityIcons]}
            {rule.severity && (
              <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                rule.severity === 'high' 
                  ? 'bg-red-100 text-red-800' 
                  : rule.severity === 'medium'
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {rule.severity}
              </span>
            )}
            {'action' in rule && rule.action && (
              <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                {actionLabels[rule.action as keyof typeof actionLabels] || rule.action}
              </span>
            )}
          </div>
          
          {rule.description && (
            <p className="text-sm text-muted-foreground">{rule.description}</p>
          )}
          
          <div className="mt-2">
            <code className="rounded bg-muted px-2 py-1 text-xs font-mono">
              {rule.condition}
            </code>
          </div>
          
          {'message' in rule && rule.message && (
            <p className="mt-2 text-sm text-muted-foreground">
              <span className="font-medium">Message:</span> {rule.message}
            </p>
          )}
          
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            {'model_generated' in rule && rule.model_generated && (
              <span className="inline-flex items-center">
                <Sparkles className="mr-1 h-3 w-3" /> AI-generated
              </span>
            )}
            {rule.lastUpdated && (
              <span>Last updated: {new Date(rule.lastUpdated).toLocaleString()}</span>
            )}
          </div>
        </div>
      </div>
      
      <div className="mt-4 flex justify-end space-x-2">
        {onDismiss && (
          <Button 
            variant="outline" 
            size="sm" 
            onClick={onDismiss}
          >
            <X className="mr-2 h-4 w-4" /> Dismiss
          </Button>
        )}
        {onApply && (
          <Button 
            size="sm" 
            onClick={onApply}
            className="bg-green-600 hover:bg-green-700"
          >
            <Check className="mr-2 h-4 w-4" /> Apply Rule
          </Button>
        )}
      </div>
    </div>
  );
};

export default EnhancedBusinessRules;
