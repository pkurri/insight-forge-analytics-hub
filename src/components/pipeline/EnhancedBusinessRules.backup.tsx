import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Check, X, Plus, RefreshCw, Sparkles } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { api } from '@/api/api';
import type { BusinessRule } from '@/api/services/businessRules/businessRulesService';

// Types
type RuleStatus = 'idle' | 'loading' | 'applying' | 'success' | 'error' | 'generating' | 'warning';
type RuleGenerationEngine = 'openai' | 'anthropic' | 'gemini';
type RuleAction = 'warn' | 'error' | 'correct';

interface RuleSuggestion extends Omit<BusinessRule, 'severity'> {
  severity: 'low' | 'medium' | 'high';
  category?: string;
  isNew?: boolean;
  ruleType: string;
  action: 'warn' | 'error' | 'correct';
}

interface EnhancedBusinessRulesProps {
  datasetId: string;
  sampleData: any[];
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
    generating: { icon: Loader2, className: 'text-blue-500', label: 'Generating...' },
    warning: { icon: X, className: 'text-yellow-500', label: 'Warning' },
  }[status];

  const Icon = statusConfig?.icon;

  return (
    <div className={`flex items-center gap-2 text-sm ${statusConfig?.className || ''}`}>
      {Icon && <Icon className="h-4 w-4" />}
      <span>{message || statusConfig?.label || ''}</span>
    </div>
  );
};

const RulePreview: React.FC<RulePreviewProps> = ({ rules, onApply, onCancel, isLoading = false }) => (
  <Card className="mt-4">
    <CardHeader>
      <CardTitle>Review Generated Rules</CardTitle>
      <CardDescription>
        Review and apply the generated business rules to your dataset.
      </CardDescription>
    </CardHeader>
    <CardContent>
      <ScrollArea className="h-64 rounded-md border p-4">
        <div className="space-y-4">
          {rules.map((rule) => (
            <div key={rule.id} className="rounded-lg border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium">{rule.name}</h4>
                  <p className="text-sm text-muted-foreground">{rule.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                    {rule.ruleType}
                  </span>
                  <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                    {(rule as any).action}
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
            'Apply Rules'
          )}
        </Button>
      </div>
    </CardContent>
  </Card>
);

// Extend BusinessRule type to include missing properties
type ExtendedBusinessRule = BusinessRule & {
  action?: 'warn' | 'error' | 'correct';
  ruleType?: string;
  isActive?: boolean;
};

          Review and apply the generated business rules to your dataset.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-64 rounded-md border p-4">
          <div className="space-y-4">
            {rules.map((rule) => (
              <div key={rule.id} className="rounded-lg border p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{rule.name}</h4>
                    <p className="text-sm text-muted-foreground">{rule.description}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                      {rule.ruleType}
                    </span>
                    <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                      {(rule as any).action}
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
              'Apply Rules'
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

const EnhancedBusinessRules: React.FC<EnhancedBusinessRulesProps> = ({
  datasetId,
  sampleData = [],
  onRulesApplied = () => {},
  onComplete = () => {},
}) => {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState('suggested');
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [rules, setRules] = useState<BusinessRule[]>([]);
  const [suggestedRules, setSuggestedRules] = useState<BusinessRule[]>([]);
  const [selectedRules, setSelectedRules] = useState<string[]>([]);
  const [selectedEngine, setSelectedEngine] = useState<RuleGenerationEngine>('openai');
  const [ruleStatus, setRuleStatus] = useState<RuleStatus>('idle');
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isRuleBuilderOpen, setIsRuleBuilderOpen] = useState(false);
  const [newRule, setNewRule] = useState<Omit<BusinessRule, 'id' | 'createdAt' | 'updatedAt' | 'datasetId'>>({
    name: '',
    description: '',
    condition: '',
    ruleType: 'validation',
    action: 'warn',
    isActive: true,
    datasetId,
  });

  const selectedRuleObjects = useMemo(() => {
    return rules.filter(rule => selectedRules.includes(rule.id));
  }, [rules, selectedRules]);

  const handleRuleSelectionChange = useCallback((ruleId: string, isSelected: boolean) => {
    setSelectedRules(prev => 
      isSelected 
        ? [...prev, ruleId]
        : prev.filter(id => id !== ruleId)
    );
  }, []);

  // Load existing rules
  useEffect(() => {
    const loadRules = async () => {
      try {
        setIsLoading(true);
        setRuleStatus('loading');
        const response = await api.businessRules.getBusinessRules(datasetId);
        if (response.success && response.data) {
          setRules(Array.isArray(response.data) ? response.data : [response.data]);
        }
      } catch (err) {
        setError('Failed to load business rules');
        console.error('Error loading rules:', err);
      } finally {
        setIsLoading(false);
        setRuleStatus('idle');
      }
    };

    loadRules();
  }, [datasetId]);

  // Handle rule generation
  const handleGenerateRules = useCallback(async () => {
    try {
      setIsGenerating(true);
      setRuleStatus('generating');
      setStatusMessage('Generating business rules...');
      
      const response = await api.businessRules.suggestRules(datasetId, [
        { engine: selectedEngine },
        ...sampleData
      ]);

      if (response.success && response.suggested_rules) {
        const generatedRules = response.suggested_rules.map(rule => ({
          ...rule,
          id: `temp-${Math.random().toString(36).substr(2, 9)}`,
          isActive: true,
          datasetId,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }));
        
        setSuggestedRules(generatedRules);
        setActiveTab('suggested');
        setRuleStatus('success');
        setStatusMessage('Rules generated successfully');
      } else {
        throw new Error(response.error || 'Failed to generate rules');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate rules';
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

  // Handle applying rules
  const handleApplyRules = useCallback(async (rulesToApply: BusinessRule[]) => {
    try {
      setIsLoading(true);
      setRuleStatus('applying');
      setStatusMessage('Applying rules...');

      const response = await api.businessRules.saveBusinessRules(datasetId, rulesToApply);
      
      if (response.success) {
        setRules(rulesToApply);
        onRulesApplied(rulesToApply);
        setRuleStatus('success');
        setStatusMessage('Rules applied successfully');
        toast({
          title: 'Success',
          description: 'Business rules have been applied successfully.',
        });
        onComplete();
      } else {
        throw new Error(response.error || 'Failed to apply rules');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to apply rules';
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

  // Handle creating a new rule
  const handleCreateRule = useCallback(async () => {
    try {
      if (!newRule.name || !newRule.condition) {
        toast({
          title: 'Validation Error',
          description: 'Please fill in all required fields',
          variant: 'destructive',
        });
        return;
      }

      setIsLoading(true);
      setRuleStatus('applying');
      setStatusMessage('Creating rule...');

      const response = await api.businessRules.createBusinessRule(datasetId, newRule);
      
      if (response.success && response.data) {
        const createdRule = Array.isArray(response.data) ? response.data[0] : response.data;
        setRules(prev => [...prev, createdRule]);
        setNewRule({
          name: '',
          description: '',
          condition: '',
          ruleType: 'validation',
          action: 'warn',
          isActive: true,
          datasetId,
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

  // Handle input changes for new rule form
  const handleNewRuleChange = useCallback((field: keyof Omit<BusinessRule, 'id' | 'createdAt' | 'updatedAt' | 'datasetId'>, value: string | boolean) => {
    setNewRule(prev => ({
      ...prev,
      [field]: value,
    }));
  }, []);

  // Handle applying rules
  const handleApplyRules = useCallback(async (rulesToApply: BusinessRule[]) => {
    try {
      setIsLoading(true);
      setRuleStatus('applying');
      setStatusMessage('Applying rules...');

      const response = await api.businessRules.saveBusinessRules(datasetId, rulesToApply);
      
      if (response.success) {
        setRules(rulesToApply);
        onRulesApplied(rulesToApply);
        setRuleStatus('success');
        setStatusMessage('Rules applied successfully');
        toast({
          title: 'Success',
          description: 'Business rules have been applied successfully.',
        });
        onComplete();
      } else {
        throw new Error(response.error || 'Failed to apply rules');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to apply rules';
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

  // Handle rule selection change
  const handleRuleSelectionChange = useCallback((ruleId: string, isSelected: boolean) => {
    setSelectedRules(prev => 
      isSelected 
        ? [...prev, ruleId] 
        : prev.filter(id => id !== ruleId)
    );
  }, []);

  // Get selected rule objects
  const selectedRuleObjects = useMemo(() => {
    return rules.filter(rule => selectedRules.includes(rule.id));
  }, [rules, selectedRules]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Business Rules</h2>
        <div className="flex items-center gap-2">
          <Select
            value={selectedEngine}
            onValueChange={(value: RuleGenerationEngine) => setSelectedEngine(value)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select AI Engine" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="openai">OpenAI</SelectItem>
              <SelectItem value="anthropic">Anthropic</SelectItem>
              <SelectItem value="gemini">Gemini</SelectItem>
            </SelectContent>
          </Select>
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
          <Button 
            variant="outline" 
            onClick={() => setIsRuleBuilderOpen(true)}
            disabled={isLoading || isGenerating}
          >
            <Plus className="mr-2 h-4 w-4" />
            Create Rule
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="suggested">Suggested Rules</TabsTrigger>
          <TabsTrigger value="existing">Existing Rules</TabsTrigger>
        </TabsList>

        <TabsContent value="suggested">
          {suggestedRules.length > 0 ? (
            <RulePreview
              rules={suggestedRules}
              onApply={() => handleApplyRules(suggestedRules)}
              onCancel={() => setSuggestedRules([])}
              isLoading={isLoading}
            />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>No Suggested Rules</CardTitle>
                <CardDescription>
                  Click "Generate Rules" to get AI-suggested rules for your dataset.
                </CardDescription>
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
                  <Label htmlFor="rule-type">Rule Type</Label>
                  <Select
                    value={newRule.ruleType}
                    onValueChange={(value) => handleNewRuleChange('ruleType', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select rule type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="validation">Validation</SelectItem>
                      <SelectItem value="transformation">Transformation</SelectItem>
                      <SelectItem value="enrichment">Enrichment</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="rule-action">Action</Label>
                  <Select
                    value={newRule.action}
                    onValueChange={(value) => handleNewRuleChange('action', value as RuleAction)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select action" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="warn">Warn</SelectItem>
                      <SelectItem value="error">Error</SelectItem>
                      <SelectItem value="correct">Auto-correct</SelectItem>
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
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => setIsRuleBuilderOpen(false)}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
                <Button onClick={handleCreateRule} disabled={isLoading}>
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
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      )}

      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Business Rules</h2>
          <p className="text-sm text-muted-foreground">
            Define and manage validation and transformation rules for your dataset
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <RuleStatusIndicator status={ruleStatus} message={statusMessage} />
          <div className="flex space-x-2">
            <Button 
              variant="outline" 
              onClick={() => setIsRuleBuilderOpen(true)}
              disabled={isLoading || isGenerating}
            >
              <Plus className="mr-2 h-4 w-4" />
              Create Rule
            </Button>
            <Button 
              onClick={handleGenerateRules}
              disabled={isLoading || isGenerating || sampleData.length === 0}
            >
              <Sparkles className="mr-2 h-4 w-4" />
              Generate Rules
            </Button>
          </div>
        </div>
      </div>
      
      <Tabs 
        value={activeTab} 
        onValueChange={setActiveTab}
        className="space-y-4"
      >
        <TabsList>
          <TabsTrigger value="suggested">Suggested Rules</TabsTrigger>
          <TabsTrigger value="existing">Existing Rules</TabsTrigger>
          <TabsTrigger value="preview">Preview Selected</TabsTrigger>
        </TabsList>

        <TabsContent value="rules" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Available Rules</CardTitle>
                  <CardDescription>
                    {ruleObjects.length} rule{ruleObjects.length !== 1 ? 's' : ''} available
                  </CardDescription>
                </div>
                <div className="flex items-center space-x-2">
                  <Select
                    value={selectedEngine}
                    onValueChange={(value: RuleGenerationEngine) => setSelectedEngine(value)}
                  >
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Select AI Engine" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="openai">OpenAI</SelectItem>
                      <SelectItem value="anthropic">Anthropic</SelectItem>
                      <SelectItem value="gemini">Gemini</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button 
                    onClick={handleGenerateRules} 
                    disabled={isGenerating || sampleData.length === 0}
                    variant="outline"
                  >
                    {isGenerating ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Sparkles className="mr-2 h-4 w-4" />
                    )}
                    Generate Rules
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <table className="w-full">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="w-[50px] px-4 py-3 text-left">
                        <input
                          type="checkbox"
                          className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                          checked={selectedRules.length === ruleObjects.length && ruleObjects.length > 0}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedRules(ruleObjects.map((rule) => rule.id));
                            } else {
                              setSelectedRules([]);
                            }
                          }}
                          aria-label="Select all"
                        />
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Name</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Description</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Type</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Created</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {ruleObjects.length > 0 ? (
                      ruleObjects.map((rule) => (
                        <tr 
                          key={rule.id} 
                          className={`hover:bg-muted/50 ${selectedRules.includes(rule.id) ? 'bg-primary/5' : ''}`}
                        >
                          <td className="whitespace-nowrap px-4 py-3">
                            <input
                              type="checkbox"
                              className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                              checked={selectedRules.includes(rule.id)}
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
                  <Label htmlFor="rule-type">Rule Type</Label>
                  <Select
                    value={newRule.ruleType}
                    onValueChange={(value) => handleNewRuleChange('ruleType', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select rule type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="validation">Validation</SelectItem>
                      <SelectItem value="transformation">Transformation</SelectItem>
                      <SelectItem value="enrichment">Enrichment</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="rule-action">Action</Label>
                  <Select
                    value={newRule.action}
                    onValueChange={(value) => handleNewRuleChange('action', value as RuleAction)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select action" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="warn">Warn</SelectItem>
                      <SelectItem value="error">Error</SelectItem>
                      <SelectItem value="correct">Auto-correct</SelectItem>
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
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => setIsRuleBuilderOpen(false)}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
                <Button onClick={handleCreateRule} disabled={isLoading}>
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

export default EnhancedBusinessRules;
