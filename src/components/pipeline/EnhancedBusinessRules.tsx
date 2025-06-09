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
  action: RuleAction;
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
  const { toast } = useToast();
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

  const [newRule, setNewRule] = useState<Omit<BusinessRule, 'id' | 'createdAt' | 'updatedAt' | 'datasetId'>>({ 
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

  // Load existing rules when component mounts
  useEffect(() => {
    const loadRules = async () => {
      try {
        setIsLoading(true);
        setRuleStatus('loading');
        setStatusMessage('Loading rules...');
        
        const response = await api.businessRules.getBusinessRules(datasetId);
        
        if (response.success) {
          setRules(response.rules || []);
          setRuleStatus('success');
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
      } finally {
        setIsLoading(false);
      }
    };

    loadRules();
  }, [datasetId, toast]);

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
          isNew: true,
          id: `generated-${Math.random().toString(36).substr(2, 9)}`,
        }));
        
        setSuggestedRules(generatedRules);
        setRuleStatus('success');
        setStatusMessage('Rules generated successfully');
        
        toast({
          title: 'Success',
          description: 'Business rules have been generated successfully.',
        });
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
            onClick={() => setIsRuleBuilderOpen(true)}
            variant="outline"
            disabled={isLoading}
          >
            <Plus className="mr-2 h-4 w-4" />
            Create Rule
          </Button>
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

      <RuleStatusIndicator status={ruleStatus} message={statusMessage} />

      <Tabs defaultValue="suggested" className="space-y-4">
        <TabsList>
          <TabsTrigger value="suggested">Suggested Rules</TabsTrigger>
          <TabsTrigger value="existing">Existing Rules</TabsTrigger>
          {selectedRules.length > 0 && (
            <TabsTrigger value="preview">
              Preview Selected ({selectedRules.length})
            </TabsTrigger>
          )}
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

export default EnhancedBusinessRules;
