import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { PlusCircle, RefreshCw, Sparkles, Check, X, Upload } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import openevalsService, { AIRuleEngine } from '@/api/services/openevalsService';
import { api } from '@/api/api';
import type { BusinessRule } from '@/api/services/businessRules/businessRulesService';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';

type RuleSeverity = 'low' | 'medium' | 'high';

interface BusinessRulesProps {
  datasetId: string;
  validationComplete: boolean;
}

const BusinessRules: React.FC<BusinessRulesProps> = ({ datasetId, validationComplete }) => {
  const { toast } = useToast();
  const [rules, setRules] = useState<BusinessRule[]>([]);
  const [generatedRules, setGeneratedRules] = useState<BusinessRule[]>([]);
  const [showGeneratedDialog, setShowGeneratedDialog] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [jsonInput, setJsonInput] = useState('');
  const [selectedEngine, setSelectedEngine] = useState<AIRuleEngine>('ai_default');
  const [showAddRuleDialog, setShowAddRuleDialog] = useState(false);
  const [editRule, setEditRule] = useState<BusinessRule | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteRule, setDeleteRule] = useState<BusinessRule | null>(null);
  const [newRule, setNewRule] = useState<BusinessRule>({
    id: '',
    name: '',
    description: '',
    condition: '',
    severity: 'medium',
    message: '',
    active: true
  });

  // Fetch rules for the current datasetId using consistent API integration
  const fetchRules = useCallback(async () => {
    if (!datasetId) return;
    setIsLoading(true);
    try {
      // Always use callApi via api.businessRules for backend consistency
      const response = await api.businessRules.getBusinessRules(datasetId);
      if (response.success) {
        setRules(response.data as BusinessRule[] || []);
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

  useEffect(() => {
    fetchRules();
  }, [fetchRules]);

  // ---
  // All business rule CRUD operations below are consistently scoped to datasetId and use callApi via api.businessRules
  // ---
  // --- AI Engine Selection UI ---
  // Add this dropdown to the UI where appropriate (e.g., above the Generate button)
  // <Select value={selectedEngine} onValueChange={setSelectedEngine}>
  //   <SelectTrigger className="w-[220px]">
  //     <SelectValue placeholder="Select AI Engine" />
  //   </SelectTrigger>
  //   <SelectContent>
  //     <SelectItem value="ai_default">AI Default</SelectItem>
  //     <SelectItem value="huggingface">Hugging Face</SelectItem>
  //     <SelectItem value="pydantic">Pydantic</SelectItem>
  //     <SelectItem value="great_expectations">Great Expectations</SelectItem>
  //   </SelectContent>
  // </Select>
  // ---

  const handleGenerateRule = async (): Promise<void> => {
    setIsLoading(true);
    try {
      const response = await openevalsService.generateBusinessRules(datasetId, selectedEngine);
      if (response.success && response.data && Array.isArray(response.data)) {
        setGeneratedRules(response.data);
        setShowGeneratedDialog(true);
        toast({
          title: "AI Rules Generated",
          description: `Review and accept ${response.data.length} suggested rules.`,
        });
      } else {
        toast({
          title: "Generation failed",
          description: response.error || "Unknown error",
          variant: "destructive"
        });
      }
    } catch (e) {
      toast({
        title: "Error",
        description: "Failed to generate rules",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Save all current rules for the dataset using the consistent API
  const handleSaveRules = async () => {
    setIsLoading(true);
    try {
      // Always pass datasetId for correct scoping
      const response = await api.businessRules.saveBusinessRules(datasetId, rules);
      if (response.success) {
        toast({
          title: 'Success',
          description: 'Business rules saved successfully'
        });
      } else {
        throw new Error(response.error || 'Failed to save rules');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to save rules',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleImport = () => {
    try {
      const parsedRules = JSON.parse(jsonInput);
      if (!Array.isArray(parsedRules)) {
        throw new Error('Invalid format: Expected array of rules');
      }
      setRules(Array.isArray(parsedRules) ? parsedRules : []);
      toast({
        title: 'Success',
        description: `${parsedRules.length} rules imported`
      });
    } catch (error) {
      toast({
        title: 'Import failed',
        description: error instanceof Error ? error.message : 'Invalid JSON',
        variant: 'destructive'
      });
    }
  };

  const handleExport = () => {
    const dataStr = JSON.stringify(rules, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `business_rules_${new Date().toISOString()}.json`;
    link.click();
    toast({
      title: 'Exported',
      description: 'Business rules exported to JSON'
    });
  };

  // Add a new rule and immediately persist to backend using datasetId
  const handleAddRule = async () => {
    if (!newRule.name || !newRule.condition || !newRule.message) {
      toast({
        title: "Missing information",
        description: "Please fill in all required fields.",
        variant: "destructive"
      });
      return;
    }
    const ruleToAdd = {
      ...newRule,
      id: newRule.id || `manual-${Date.now()}`,
      dataset_id: datasetId,
      active: newRule.active,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    setRules(prev => [...prev, ruleToAdd]);
    setShowAddRuleDialog(false);
    setNewRule({ id: '', name: '', description: '', condition: '', severity: 'medium', message: '', active: true });
    try {
      // Save all rules including the new one, always scoped by datasetId
      const response = await api.businessRules.saveBusinessRules(datasetId, [...rules, ruleToAdd]);
      if (response.success) {
        toast({
          title: "Rule added successfully",
          description: `"${ruleToAdd.name}" has been added to your rule set.`
        });
      } else {
        setRules(rules);
        toast({
          title: "Failed to add rule",
          description: response.error || "An unknown error occurred",
          variant: "destructive"
        });
      }
    } catch (error) {
      setRules(rules);
      toast({
        title: "Error adding rule",
        description: "An unexpected error occurred while adding the rule.",
        variant: "destructive"
      });
    }
  };

  // Delete a rule and persist the change using datasetId
  const handleDeleteRule = async (id: string) => {
    const ruleToDelete = rules.find(rule => rule.id === id);
    if (!ruleToDelete) return;
    try {
      const updatedRules = rules.filter(rule => rule.id !== id);
      // Save the updated rules array for this dataset
      const response = await api.businessRules.saveBusinessRules(datasetId, updatedRules);
      if (response.success) {
        setRules(updatedRules);
        toast({
          title: "Rule deleted",
          description: "The rule has been removed from your rule set."
        });
      } else {
        toast({
          title: "Delete failed",
          description: response.error || "Failed to delete rule",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Delete error",
        description: "An unexpected error occurred while deleting the rule.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle rule activation and persist using datasetId
  const handleToggleRule = async (id: string) => {
    const ruleToToggle = rules.find(rule => rule.id === id);
    if (!ruleToToggle) return;
    const updatedRules = rules.map(rule => rule.id === id ? { ...rule, active: !rule.active } : rule);
    try {
      // Save the toggled rules array for this dataset
      const response = await api.businessRules.saveBusinessRules(datasetId, updatedRules);
      if (response.success) {
        setRules(updatedRules);
      } else {
        setRules(rules);
        toast({
          title: "Update failed",
          description: response.error || "Failed to update rule status",
          variant: "destructive"
        });
      }
    } catch (error) {
      setRules(rules);
      toast({
        title: "Update error",
        description: "An unexpected error occurred while updating the rule.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Edit and Delete Dialog Handlers
  const handleEditRule = (rule: BusinessRule) => {
    setEditRule({ ...rule });
    setEditDialogOpen(true);
  };

  // Update an existing rule using the datasetId and consistent API
  const handleUpdateRule = async () => {
    if (!editRule) return;
    if (!editRule.name || !editRule.condition || !editRule.message) {
      toast({
        title: 'Missing information',
        description: 'Please fill in all required fields.',
        variant: 'destructive',
      });
      return;
    }
    setIsLoading(true);
    try {
      // Use the update endpoint, always passing datasetId
      const response = await api.businessRules.updateBusinessRule(datasetId, editRule.id, editRule);
      if (response.success) {
        setRules(prev => prev.map(rule => rule.id === editRule.id ? { ...editRule } : rule));
        toast({
          title: 'Rule updated',
          description: 'Business rule updated successfully.',
        });
        setEditRule(null);
        setEditDialogOpen(false);
      } else {
        toast({
          title: 'Update failed',
          description: response.error || 'Failed to update rule',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Update error',
        description: 'An unexpected error occurred while updating the rule.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const confirmDeleteRule = (rule: BusinessRule) => {
    setDeleteRule(rule);
  };

  const handleConfirmDeleteRule = async () => {
    if (!deleteRule) return;
    
    setIsLoading(true);
    try {
      // Use the consistent API pattern for deleting rules
      const response = await api.businessRules.deleteRule(datasetId, deleteRule.id);
      
      if (response.success) {
        // Update local state after successful deletion
        setRules(rules.filter(r => r.id !== deleteRule.id));
        // Handle success
        setDeleteRule(null);
      } else {
        // Handle error
      }
    } catch (error) {
      // Handle error
    } finally {
      setIsLoading(false);
    }
  };

  const isRuleValid = () => {
    if (!editRule) return false;
    return !!editRule.name && !!editRule.condition && !!editRule.message;
  };

  return (
    <Tabs defaultValue="manage" className="w-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold tracking-tight">Business Rules</h2>
        <TabsList>
          <TabsTrigger value="manage" className="flex items-center gap-1">
            <PlusCircle className="h-4 w-4" />
            Manage Rules
          </TabsTrigger>
          <TabsTrigger value="ai" className="flex items-center gap-1">
            <Sparkles className="h-4 w-4" />
            AI Generated
          </TabsTrigger>
          <TabsTrigger value="import" className="flex items-center gap-1">
            <Upload className="h-4 w-4" />
            Import
          </TabsTrigger>
          <TabsTrigger value="export" className="flex items-center gap-1">
            <Upload className="h-4 w-4" />
            Export
          </TabsTrigger>
        </TabsList>
      </div>

      <TabsContent value="manage">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Manage Business Rules</h3>
              <p className="text-sm text-muted-foreground">Create and manage validation rules for your data</p>
            </div>
            <Button onClick={() => setShowAddRuleDialog(true)} disabled={!validationComplete}>
              <PlusCircle className="h-4 w-4 mr-2" />
              Add Rule
            </Button>
          </CardHeader>
          <CardContent>
            {rules.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">No business rules defined yet.</p>
                <Button onClick={() => setShowAddRuleDialog(true)} disabled={!validationComplete}>
                  <PlusCircle className="h-4 w-4 mr-2" />
                  Add Your First Rule
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {rules.filter(rule => !rule.model_generated).map((rule) => (
                  <Card key={rule.id} className="border p-2">
                    <CardHeader className="flex flex-row items-center justify-between p-3">
                      <div className="font-semibold">{rule.name}</div>
                      <div className="flex gap-2">
                        <Badge 
                          variant={rule.active ? "default" : "outline"}
                          className="cursor-pointer"
                          onClick={() => handleToggleRule(rule.id)}
                        >
                          {rule.active ? "Active" : "Inactive"}
                        </Badge>
                        <Button variant="ghost" size="sm" onClick={() => handleEditRule(rule)}>
                          Edit
                        </Button>
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
