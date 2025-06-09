import { useState, useEffect, useCallback } from 'react';
import { api } from '@/api';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { X, Upload, PlusCircle, Download, FileText, Trash2, Pencil, Check, RefreshCw } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Types
type AIRuleEngine = 'ai_default' | 'ai_advanced' | 'custom';
type RuleSeverity = 'low' | 'medium' | 'high';

interface BusinessRule {
  id: string;
  dataset_id: string;
  name: string;
  description: string;
  condition: string;
  message: string;
  severity: RuleSeverity;
  active: boolean;
  created_at: string;
  updated_at: string;
  model_generated: boolean;
  field?: string;
  source?: string;
  model?: string;
}

interface BusinessRulesProps {
  datasetId?: string;
  validationComplete?: boolean;
  rules?: BusinessRule[];
  onRulesUpdate?: (rules: BusinessRule[]) => void;
}

type NewRuleState = Omit<BusinessRule, 'id' | 'dataset_id' | 'created_at' | 'updated_at' | 'model_generated'>;



const BusinessRules: React.FC<BusinessRulesProps> = ({
  datasetId,
  rules: externalRules = [],
  onRulesUpdate,
}) => {
  const { toast } = useToast();
  
  // State management
  const [rules, setRules] = useState<BusinessRule[]>(externalRules);
  const [isLoading, setIsLoading] = useState(false);
  const [showAddRuleDialog, setShowAddRuleDialog] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<BusinessRule | null>(null);
  const [deleteRule, setDeleteRule] = useState<BusinessRule | null>(null);
  const [jsonInput, setJsonInput] = useState('');
  const [selectedEngine, setSelectedEngine] = useState<AIRuleEngine>('ai_default');
  const [newRule, setNewRule] = useState<NewRuleState>({
    name: '',
    description: '',
    condition: '',
    message: '',
    active: true,
    severity: 'medium',
  });
  
  // Update local state when external rules change
  useEffect(() => {
    setRules(externalRules);
  }, [externalRules]);
  
  // Handle rules update
  const handleRulesUpdate = useCallback((updatedRules: BusinessRule[]) => {
    setRules(updatedRules);
    if (onRulesUpdate) {
      onRulesUpdate(updatedRules);
    }
  }, [onRulesUpdate]);

  // Handle adding a new rule
  const handleAddRule = useCallback(async () => {
    if (!newRule.name || !newRule.condition) {
      toast({
        title: 'Error',
        description: 'Please fill in all required fields',
        variant: 'destructive',
      });
      return;
    }

    try {
      setIsLoading(true);
      const response = await api.businessRules.create({
        ...newRule,
        dataset_id: datasetId || '',
      });

      const updatedRules = [...rules, response.data];
      handleRulesUpdate(updatedRules);

      setNewRule({
        name: '',
        description: '',
        condition: '',
        message: '',
        active: true,
        severity: 'medium',
      });
      setShowAddRuleDialog(false);

      toast({
        title: 'Success',
        description: 'Business rule added successfully',
      });
    } catch (error) {
      console.error('Error adding rule:', error);
      toast({
        title: 'Error',
        description: 'Failed to add business rule',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [datasetId, newRule, toast]);

  // Handle editing an existing rule
  const handleEditRule = useCallback((rule: BusinessRule) => {
    setEditingRule(rule);
    setIsEditDialogOpen(true);
  }, []);

  const handleUpdateRule = useCallback(async (updatedRule: BusinessRule) => {
    try {
      setIsLoading(true);
      const response = await api.businessRules.update(updatedRule.id, updatedRule);

      const updatedRules = rules.map(rule =>
        rule.id === updatedRule.id ? response.data : rule
      );

      handleRulesUpdate(updatedRules);
      setEditDialogOpen(false);

      toast({
        title: 'Success',
        description: 'Business rule updated successfully',
      });
    } catch (error) {
      console.error('Error updating rule:', error);
      toast({
        title: 'Error',
        description: 'Failed to update business rule',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [rules, toast]);

  // Handle rule export
  const handleExport = useCallback(() => {
    if (rules.length === 0) {
      toast({
        title: 'No rules to export',
        description: 'There are no rules to export.',
      });
      return;
    }

    try {
      const data = JSON.stringify(rules, null, 2);
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `business-rules-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast({
        title: 'Export successful',
        description: `Exported ${rules.length} rule(s)`,
      });
    } catch (error) {
      console.error('Error exporting rules:', error);
      toast({
        title: 'Export failed',
        description: 'Failed to export rules. Please try again.',
        variant: 'destructive',
      });
    }
  }, [rules, toast]);

  // Toggle rule active status
  const toggleRuleActive = useCallback(async (ruleId: string) => {
    try {
      setIsLoading(true);
      const ruleToUpdate = rules.find(rule => rule.id === ruleId);
      if (!ruleToUpdate) return;
      
      const updatedRule = { ...ruleToUpdate, active: !ruleToUpdate.active };
      const response = await api.businessRules.update(ruleId, updatedRule);
      
      const updatedRules = rules.map(rule => 
        rule.id === ruleId ? response.data : rule
      );
      
      handleRulesUpdate(updatedRules);
      
      toast({
        title: 'Rule updated',
        description: `Rule has been ${updatedRule.active ? 'activated' : 'deactivated'}`,
      });
    } catch (error) {
      console.error('Error toggling rule status:', error);
      toast({
        title: 'Error',
        description: 'Failed to update rule status',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [rules, handleRulesUpdate, toast]);

  const handleDeleteRule = useCallback((rule: BusinessRule) => {
    setDeleteRule(rule);
  }, []);

  const handleConfirmDeleteRule = useCallback(async () => {
    if (!deleteRule) return;

    try {
      setIsLoading(true);
      await api.businessRules.delete(deleteRule.id);

      const updatedRules = rules.filter(rule => rule.id !== deleteRule.id);
      handleRulesUpdate(updatedRules);
      setDeleteRule(null);

      toast({
        title: 'Success',
        description: 'Business rule deleted successfully',
      });
    } catch (error) {
      console.error('Error deleting rule:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete business rule',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [deleteRule, rules, toast]);

  // Notify parent component of rules changes
  useEffect(() => {
    if (onRulesUpdate) {
      onRulesUpdate(rules);
    }
  }, [rules, onRulesUpdate]);

  // Handle rule import
  const handleImport = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setIsLoading(true);
      const content = await file.text();
      const importedRules = JSON.parse(content);

      // Validate imported rules
      if (!Array.isArray(importedRules)) {
        throw new Error('Invalid file format. Expected an array of rules.');
      }

      // Validate each rule
      const validRules = importedRules.filter((rule: any) => {
        const isValid = rule.name &&
          rule.condition &&
          rule.severity &&
          typeof rule.active === 'boolean';
        
        if (!isValid) {
          console.warn('Invalid rule format:', rule);
          return false;
        }
        return true;
      }) as BusinessRule[];

      if (validRules.length === 0) {
        throw new Error('No valid rules found in the imported file.');
      }

      // Add dataset_id to each rule
      const rulesWithDataset = validRules.map(rule => ({
        ...rule,
        dataset_id: datasetId || '',
      }));

      // Save rules to the server
      const response = await api.businessRules.saveBusinessRules(
        datasetId || '',
        rulesWithDataset
      );

      // Update local state
      const updatedRules = [...rules, ...response.data];
      handleRulesUpdate(updatedRules);

      toast({
        title: 'Import successful',
        description: `Successfully imported ${response.data.length} rule(s)`,
      });

      // Reset file input
      event.target.value = '';
    } catch (error) {
      console.error('Error importing rules:', error);
      toast({
        title: 'Import failed',
        description:
          error instanceof Error ? error.message : 'Failed to import rules',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [datasetId, rules, handleRulesUpdate, toast]);

// ...

{rules?.length > 0 ? (
  rules.map((rule) => (
    <div key={rule.id} className="border rounded-lg p-4">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-medium">{rule.name}</h3>
          <p className="text-sm text-muted-foreground">{rule.description}</p>
                      <X className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-3 pt-0">
                <div className="text-sm mb-1"><span className="font-medium">Condition:</span> <span className="font-mono">{rule.condition}</span></div>
                <div className="text-xs mb-1"><span className="font-medium">Severity:</span> {rule.severity}</div>
                <div className="text-xs mb-1"><span className="font-medium">Message:</span> {rule.message}</div>
                {rule.description && <div className="text-xs text-muted-foreground">{rule.description}</div>}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No business rules defined.</p>
      )}
      
      {/* Add Rule Dialog */}
      <Dialog open={showAddRuleDialog} onOpenChange={setShowAddRuleDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Business Rule</DialogTitle>
            <DialogDescription>
              Create a new business rule to validate your data.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="rule-name">Rule Name</Label>
              <Input
                id="rule-name"
                value={newRule.name}
                onChange={e => setNewRule({...newRule, name: e.target.value})}
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Add Rule Dialog */}
        <Dialog open={showAddRuleDialog} onOpenChange={setShowAddRuleDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Business Rule</DialogTitle>
              <DialogDescription>
                Create a new business rule to validate your data.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <Label htmlFor="rule-name">Rule Name</Label>
                <Input
                  id="rule-name"
                  value={newRule.name}
                  onChange={e => setNewRule({...newRule, name: e.target.value})}
                  disabled={isLoading}
                  className={!newRule.name && showAddRuleDialog ? 'border-red-500' : ''}
                />
                {!newRule.name && showAddRuleDialog && <div className="text-xs text-red-500">Name is required.</div>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="rule-description">Description (Optional)</Label>
                <Input
                  id="rule-description"
                  value={newRule.description}
                  onChange={e => setNewRule({...newRule, description: e.target.value})}
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rule-condition">Condition</Label>
                <Textarea
                  id="rule-condition"
                  className={`font-mono ${!newRule.condition && showAddRuleDialog ? 'border-red-500' : ''}`}
                  value={newRule.condition}
                  onChange={e => setNewRule({...newRule, condition: e.target.value})}
                  disabled={isLoading}
                />
                {!newRule.condition && showAddRuleDialog && <div className="text-xs text-red-500">Condition is required.</div>}
                <p className="text-xs text-muted-foreground">
                  Define the validation logic using JavaScript-like syntax
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="rule-message">Error Message</Label>
                <Input
                  id="rule-message"
                  value={newRule.message}
                  onChange={e => setNewRule({...newRule, message: e.target.value})}
                  disabled={isLoading}
                  className={!newRule.message && showAddRuleDialog ? 'border-red-500' : ''}
                />
                {!newRule.message && showAddRuleDialog && <div className="text-xs text-red-500">Message is required.</div>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="rule-severity">Severity</Label>
                <Select
                  value={newRule.severity}
                  onValueChange={value => setNewRule({...newRule, severity: value as RuleSeverity})}
                  disabled={isLoading}
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
            </div>
            <DialogFooter>
              <Button type="button" onClick={() => setShowAddRuleDialog(false)} variant="outline" disabled={isLoading}>
                Cancel
              </Button>
              <Button 
                type="button" 
                onClick={handleAddRule} 
                disabled={isLoading || !newRule.name || !newRule.condition || !newRule.message}
              >
                {isLoading ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Check className="mr-2 h-4 w-4" />}
                Add Rule
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
        
        {/* Edit Rule Dialog */}
        <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit Business Rule</DialogTitle>
              <DialogDescription>
                Update your business rule details.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <Label htmlFor="edit-rule-name">Rule Name</Label>
                <Input
                  id="edit-rule-name"
                  value={editRule?.name || ''}
                  onChange={e => setEditRule(r => r ? { ...r, name: e.target.value } : r)}
                  disabled={isLoading}
                  className={(!editRule?.name && editDialogOpen) ? 'border-red-500' : ''}
                />
                {!editRule?.name && editDialogOpen && <div className="text-xs text-red-500">Name is required.</div>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-rule-description">Description (Optional)</Label>
                <Input
                  id="edit-rule-description"
                  value={editRule?.description || ''}
                  onChange={e => setEditRule(r => r ? { ...r, description: e.target.value } : r)}
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-rule-condition">Condition</Label>
                <Textarea
                  id="edit-rule-condition"
                  className={`font-mono ${(!editRule?.condition && editDialogOpen) ? 'border-red-500' : ''}`}
                  value={editRule?.condition || ''}
                  onChange={e => setEditRule(r => r ? { ...r, condition: e.target.value } : r)}
                  disabled={isLoading}
                />
                {!editRule?.condition && editDialogOpen && <div className="text-xs text-red-500">Condition is required.</div>}
                <p className="text-xs text-muted-foreground">
                  Define the validation logic using JavaScript-like syntax
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-rule-message">Error Message</Label>
                <Input
                  id="edit-rule-message"
                  value={editRule?.message || ''}
                  onChange={e => setEditRule(r => r ? { ...r, message: e.target.value } : r)}
                  disabled={isLoading}
                  className={(!editRule?.message && editDialogOpen) ? 'border-red-500' : ''}
                />
                {!editRule?.message && editDialogOpen && <div className="text-xs text-red-500">Message is required.</div>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-rule-severity">Severity</Label>
                <Select
                  value={editRule?.severity || 'medium'}
                  onValueChange={value => setEditRule(r => r ? { ...r, severity: value as RuleSeverity } : r)}
                  disabled={isLoading}
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
              <Button
                variant="destructive"
                onClick={() => confirmDeleteRule(editRule!)}
                disabled={isLoading}
              >
                <X className="h-4 w-4 mr-2" />
                Delete
              </Button>
            </div>
            <DialogFooter>
              <Button type="button" onClick={() => setEditDialogOpen(false)} variant="outline" disabled={isLoading}>
                Cancel
              </Button>
              <Button type="button" onClick={handleUpdateRule} disabled={isLoading || !isRuleValid()}>
                {isLoading ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Check className="mr-2 h-4 w-4" />}
                Save Changes
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
        
        {/* Delete Rule Confirmation Dialog */}
        <Dialog open={!!deleteRule} onOpenChange={(open) => !open && setDeleteRule(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Rule</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete this rule? This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <div className="pt-2 pb-4">
              {deleteRule && (
                <div className="border rounded-md p-3 bg-muted/50">
                  <div className="font-medium">{deleteRule.name}</div>
                  <div className="text-sm mt-1 font-mono">{deleteRule.condition}</div>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button type="button" onClick={() => setDeleteRule(null)} variant="outline">
                Cancel
              </Button>
              <Button type="button" onClick={handleConfirmDeleteRule} variant="destructive">
                Delete Rule
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </TabsContent>

      {/* AI Generated Tab */}
      <TabsContent value="ai">
        <Card>
          <CardHeader>AI-Generated Business Rules</CardHeader>
          <CardContent>
            <p className="mb-4">Use AI to automatically generate business rules based on your dataset patterns and schema.</p>
            <div className="flex flex-col gap-4">
              <div className="flex gap-2 items-center">
                <Label htmlFor="ai-engine-select">Select AI Engine:</Label>
                <Select value={selectedEngine} onValueChange={(value) => setSelectedEngine(value as AIRuleEngine)}>
                  <SelectTrigger className="w-[220px]">
                    <SelectValue placeholder="Select AI Engine" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ai_default">AI Default</SelectItem>
                    <SelectItem value="huggingface">Hugging Face</SelectItem>
                    <SelectItem value="pydantic">Pydantic</SelectItem>
                    <SelectItem value="great_expectations">Great Expectations</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button onClick={handleGenerateRule} disabled={isLoading}>
                {isLoading ? (
                  <><RefreshCw className="mr-2 h-4 w-4 animate-spin" /> Generating...</>
                ) : (
                  <><Sparkles className="mr-2 h-4 w-4" /> Generate Rules with {selectedEngine.replace('_', ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}</>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
        <div className="mb-2 font-semibold">
          {rules.filter(rule => rule.model_generated).length} AI-generated rules
        </div>
        <div className="space-y-4">
          {rules.filter(rule => rule.model_generated).length === 0 ? (
            <div className="text-muted-foreground">No AI-generated business rules found.</div>
          ) : rules.filter(rule => rule.model_generated).map((rule) => (
            <Card key={rule.id} className="border p-2">
              <CardHeader className="flex flex-row items-center justify-between">
                <div className="font-semibold">{rule.name}</div>
                <div className="flex gap-2">
                  <Badge variant={rule.active ? "default" : "outline"}>{rule.active ? "Active" : "Inactive"}</Badge>
                  <Badge variant="outline">AI</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-sm mb-1"><span className="font-medium">Condition:</span> <span className="font-mono">{rule.condition}</span></div>
                <div className="text-xs mb-1"><span className="font-medium">Severity:</span> {rule.severity}</div>
                <div className="text-xs mb-1"><span className="font-medium">Message:</span> {rule.message}</div>
                {rule.description && <div className="text-xs text-muted-foreground">{rule.description}</div>}
                {/* Show AI model/source if available */}
                {(rule.model || rule.source) && (
                  <div className="text-xs text-blue-700 mt-1">AI Source: {rule.model || rule.source}</div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </TabsContent>

      <TabsContent value="import">
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Import Business Rules</h3>
            <p className="text-sm text-muted-foreground">Import rules from JSON format</p>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-4">
              <Textarea
                value={jsonInput || ''}
                onChange={e => setJsonInput(e.target.value)}
                placeholder="Paste business rules JSON here"
                rows={8}
              />
              <Button onClick={handleImport} variant="default">
                <Upload className="h-4 w-4 mr-2" /> Import Rules
              </Button>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
      <TabsContent value="export">
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Export Business Rules</h3>
            <p className="text-sm text-muted-foreground">Export rules to JSON format</p>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-4">
              <Textarea
                value={JSON.stringify(rules, null, 2)}
                readOnly
                rows={8}
              />
              <Button onClick={handleExport} variant="default">
                <Upload className="h-4 w-4 mr-2" /> Copy to Clipboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}

export default BusinessRules;
