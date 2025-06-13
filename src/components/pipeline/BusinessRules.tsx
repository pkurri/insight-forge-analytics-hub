import { useState, useEffect, useCallback, FC } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Plus, RefreshCw, Sparkles, Edit, Trash2, Download } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

type BusinessRule = {
  id: string;
  dataset_id: string;
  name: string;
  description: string;
  condition: string;
  message: string;
  severity: 'low' | 'medium' | 'high';
  active: boolean;
  created_at: string;
  updated_at: string;
  model_generated?: boolean;
};

type AIRuleEngine = 'ai_default' | 'ai_advanced' | 'custom';
type RuleSeverity = 'low' | 'medium' | 'high';

interface BusinessRulesProps {
  datasetId?: string;
  validationComplete?: boolean;
  rules?: BusinessRule[];
  onRulesUpdate?: (rules: BusinessRule[]) => void;
}


const BusinessRules: FC<BusinessRulesProps> = ({
  datasetId = '',
  rules: externalRules = [],
  onRulesUpdate,
}) => {
  const { toast } = useToast();
  const [rules, setRules] = useState<BusinessRule[]>(externalRules || []);
  const [isLoading, setIsLoading] = useState(false);
  const [showAddRuleDialog, setShowAddRuleDialog] = useState(false);
  const [editRule, setEditRule] = useState<BusinessRule | null>(null);
  const [deleteRule, setDeleteRule] = useState<BusinessRule | null>(null);
  const [selectedEngine, setSelectedEngine] = useState<AIRuleEngine>('ai_default');
  const [newRule, setNewRule] = useState<Omit<BusinessRule, 'id' | 'dataset_id' | 'created_at' | 'updated_at' | 'model_generated'>>({
    name: '',
    description: '',
    condition: '',
    message: '',
    severity: 'medium',
    active: true,
  });

  const isRuleValid = useCallback((rule: BusinessRule): boolean => {
    return Boolean(rule?.name && rule?.condition && rule?.message);
  }, []);

  useEffect(() => {
    setRules(externalRules);
  }, [externalRules]);

  const handleRulesUpdate = useCallback((updatedRules: BusinessRule[]) => {
    setRules(updatedRules);
    if (onRulesUpdate) {
      onRulesUpdate(updatedRules);
    }
  }, [onRulesUpdate]);

  // Handle confirming rule deletion
  const handleConfirmDeleteRule = useCallback(async () => {
    if (!deleteRule) return;

    try {
      setIsLoading(true);
      // In a real app, you would call an API here
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
  }, [deleteRule, rules, handleRulesUpdate, toast]);

  // Handle importing rules from file
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

      // In a real app, you would call an API here
      const updatedRules = [...rules, ...rulesWithDataset];
      handleRulesUpdate(updatedRules);

      toast({
        title: 'Import successful',
        description: `Successfully imported ${validRules.length} rule(s)`,
      });

      // Reset file input
      if (event.target) {
        event.target.value = '';
      }
    } catch (error) {
      console.error('Error importing rules:', error);
      toast({
        title: 'Import failed',
        description: error instanceof Error ? error.message : 'Failed to import rules',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [rules, datasetId, handleRulesUpdate, toast]);

  // Handle rule export to file
  const handleExportToFile = useCallback(() => {
    if (rules.length === 0) {
      toast({
        title: 'No rules to export',
        description: 'There are no rules to export.',
        variant: 'destructive',
      });
      return;
    }

    try {
      const dataStr = JSON.stringify(rules, null, 2);
      const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
      
      const exportFileDefaultName = `business-rules-${new Date().toISOString().split('T')[0]}.json`;
      
      const linkElement = document.createElement('a');
      linkElement.setAttribute('href', dataUri);
      linkElement.setAttribute('download', exportFileDefaultName);
      linkElement.click();
      
      toast({
        title: 'Success',
        description: 'Rules exported successfully',
      });
    } catch (error) {
      console.error('Error exporting rules:', error);
      toast({
        title: 'Error',
        description: 'Failed to export rules',
        variant: 'destructive',
      });
    }
  }, [rules, toast]);

  // Handle copying rules to clipboard
  const handleCopyToClipboard = useCallback(() => {
    if (exportTextareaRef.current) {
      exportTextareaRef.current.select();
      document.execCommand('copy');
      toast({
        title: 'Copied!',
        description: 'Rules copied to clipboard',
      });
    }
  }, [toast]);

  // Handle generating AI rules
  const handleGenerateRule = useCallback(async () => {
    try {
      setIsLoading(true);
      const newRule: BusinessRule = {
        id: `rule-${Date.now()}`,
        dataset_id: datasetId,
        name: `New Rule ${rules.length + 1}`,
        description: 'Generated rule',
        condition: 'value > 0',
        message: 'Value must be greater than 0',
        severity: 'medium',
        active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        model_generated: true,
      };
      handleRulesUpdate([...rules, newRule]);
      toast({
        title: 'Success',
        description: 'New rule generated successfully',
      });
    } catch (error) {
      console.error('Error generating rule:', error);
      toast({
        title: 'Error',
        description: 'Failed to generate rule',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [rules, datasetId, handleRulesUpdate, toast]);

  // Handle adding a new rule
  const handleAddRule = useCallback(async () => {
    try {
      setIsLoading(true);
      if (!newRule.name || !newRule.condition) {
        toast({
          title: 'Error',
          description: 'Name and condition are required',
          variant: 'destructive',
        });
        return;
      }

      // In a real app, you would call an API here
      const newRuleWithId: BusinessRule = {
        ...newRule,
        id: `rule-${Date.now()}`,
        dataset_id: datasetId,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        model_generated: false
      };

      const updatedRules = [...rules, newRuleWithId];
      handleRulesUpdate(updatedRules);
      setShowAddRuleDialog(false);
      setNewRule({
        name: '',
        description: '',
        condition: '',
        message: '',
        severity: 'medium',
        active: true,
      });

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
  }, [newRule, rules, datasetId, handleRulesUpdate, toast]);

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
}, [rules, handleRulesUpdate, toast]);

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
        <Button onClick={() => setShowAddRuleDialog(true)}>
          <Plus className="h-4 w-4 mr-2" /> Add Rule
        </Button>
      </div>

      <Tabs defaultValue="manual" className="w-full space-y-4">
        <TabsList>
          <TabsTrigger value="manual">Manual Rules</TabsTrigger>
          <TabsTrigger value="ai">AI-Generated Rules</TabsTrigger>
          <TabsTrigger value="import">Import</TabsTrigger>
          <TabsTrigger value="export">Export</TabsTrigger>
        </TabsList>

        <TabsContent value="manual">
          <Card>
            <CardHeader>Business Rules</CardHeader>
            <CardContent className="space-y-4">
              {rules.length > 0 ? (
                rules.map((rule) => (
                  <Card key={rule.id}>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-medium">{rule.name}</h3>
                          <p className="text-sm text-muted-foreground">{rule.condition}</p>
                        </div>
                        <div className="flex space-x-2">
                          <Button variant="ghost" size="icon" onClick={() => {
                            setEditRule(rule);
                            setIsEditDialogOpen(true);
                          }}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => setDeleteRule(rule)}>
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm">{rule.description}</p>
                      <div className="mt-2 flex items-center space-x-2">
                        <Badge variant={rule.severity === 'high' ? 'destructive' : rule.severity === 'medium' ? 'warning' : 'default'}>
                          {rule.severity}
                        </Badge>
                        {rule.active ? (
                          <Badge variant="outline">Active</Badge>
                        ) : (
                          <Badge variant="outline">Inactive</Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">No business rules defined.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ai">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="font-medium">AI-Generated Rules</h3>
                  <p className="text-sm text-muted-foreground">
                    Generate rules using AI based on your data patterns
                  </p>
                </div>
                <Select value={selectedEngine} onValueChange={(value) => setSelectedEngine(value as AIRuleEngine)}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Select AI Engine" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ai_default">Default AI</SelectItem>
                    <SelectItem value="ai_advanced">Advanced AI</SelectItem>
                    <SelectItem value="custom">Custom Model</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              <Button disabled={isLoading} onClick={handleGenerateRule}>
                {isLoading ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Rules
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="import">
          <Card>
            <CardHeader>
              <h3 className="font-medium">Import Rules</h3>
              <p className="text-sm text-muted-foreground">
                Import rules from a JSON file
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <Input 
                    type="file" 
                    accept=".json" 
                    onChange={handleImport} 
                    className="w-full max-w-sm"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="export">
          <Card>
            <CardHeader>
              <h3 className="font-medium">Export Rules</h3>
              <p className="text-sm text-muted-foreground">
                Export your current rules to a JSON file
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Button variant="outline" onClick={handleExportToFile}>
                  <Download className="mr-2 h-4 w-4" />
                  Export Rules
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Tabs defaultValue="manual" className="w-full">
        <TabsList>
          <TabsTrigger value="manual">Manual Rules</TabsTrigger>
          <TabsTrigger value="ai">AI-Generated Rules</TabsTrigger>
          <TabsTrigger value="import">Import</TabsTrigger>
          <TabsTrigger value="export">Export</TabsTrigger>
        </TabsList>

      {/* Add/Edit Rule Dialog */}
      <Dialog open={showAddRuleDialog} onOpenChange={setShowAddRuleDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Business Rule</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Rule Name</Label>
              <Input
                id="name"
                value={newRule.name}
                onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                placeholder="Enter rule name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={newRule.description}
                onChange={(e) => setNewRule({ ...newRule, description: e.target.value })}
                placeholder="Enter rule description"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="condition">Condition</Label>
              <Textarea
                id="condition"
                value={newRule.condition}
                onChange={(e) => setNewRule({ ...newRule, condition: e.target.value })}
                placeholder="e.g., price > 100"
                className="font-mono text-sm"
              />
              <p className="text-xs text-muted-foreground">
                Use SQL-like conditions (e.g., column_name = 'value' AND other_column > 100)
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="severity">Severity</Label>
              <Select
                value={newRule.severity}
                onValueChange={(value) => setNewRule({ ...newRule, severity: value as RuleSeverity })}
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
              <Label htmlFor="message">Error Message</Label>
              <Input
                id="message"
                value={newRule.message}
                onChange={(e) => setNewRule({ ...newRule, message: e.target.value })}
                placeholder="Enter error message to display when rule fails"
              />
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="active"
                checked={newRule.active}
                onChange={(e) => setNewRule({ ...newRule, active: e.target.checked })}
                className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <Label htmlFor="active" className="text-sm font-medium leading-none">
                Active
              </Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddRuleDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddRule}>
              Add Rule
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Tabs defaultValue="manual" className="w-full">
        <TabsList>
          <TabsTrigger value="manual">Manual Rules</TabsTrigger>
          <TabsTrigger value="ai">AI-Generated Rules</TabsTrigger>
          <TabsTrigger value="import-export">Import/Export</TabsTrigger>
        </TabsList>

        <TabsContent value="manual">
          <Card>
            <CardHeader>Business Rules</CardHeader>
            <CardContent>
              {rules.length > 0 ? (
                rules.map((rule) => (
                  <div key={rule.id} className="mb-4 p-4 border rounded-lg">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium">{rule.name}</h3>
                        <p className="text-sm text-muted-foreground">{rule.condition}</p>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => {
                            setEditRule(rule);
                            setIsEditDialogOpen(true);
                          }}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeleteRule(rule)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </div>
                    <p className="mt-2 text-sm">{rule.description}</p>
                    <div className="mt-2 flex items-center space-x-2">
                      <Badge
                        variant={
                          rule.severity === 'high'
                            ? 'destructive'
                            : rule.severity === 'medium'
                            ? 'warning'
                            : 'default'
                        }
                      >
                        {rule.severity}
                      </Badge>
                      {rule.active ? (
                        <Badge variant="outline">Active</Badge>
                      ) : (
                        <Badge variant="outline">Inactive</Badge>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">No business rules defined.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

      {/* Add/Edit Rule Dialog */}
      <Dialog open={showAddRuleDialog} onOpenChange={setShowAddRuleDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Business Rule</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Rule Name</Label>
              <Input
                id="name"
                value={newRule.name}
                onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                placeholder="Enter rule name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={newRule.description}
                onChange={(e) => setNewRule({ ...newRule, description: e.target.value })}
                placeholder="Enter rule description"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="condition">Condition</Label>
              <Textarea
                id="condition"
                value={newRule.condition}
                onChange={(e) => setNewRule({ ...newRule, condition: e.target.value })}
                placeholder="e.g., price > 100"
                className="font-mono text-sm"
              />
              <p className="text-xs text-muted-foreground">
                Use SQL-like conditions (e.g., column_name = 'value' AND other_column > 100)
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="severity">Severity</Label>
              <Select
                value={newRule.severity}
                onValueChange={(value) => setNewRule({ ...newRule, severity: value as RuleSeverity })}
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
              <Label htmlFor="message">Error Message</Label>
              <Input
                id="message"
                value={newRule.message}
                onChange={(e) => setNewRule({ ...newRule, message: e.target.value })}
                placeholder="Enter error message to display when rule fails"
              />
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="active"
                checked={newRule.active}
                onChange={(e) => setNewRule({ ...newRule, active: e.target.checked })}
                className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <Label htmlFor="active" className="text-sm font-medium leading-none">
                Active
              </Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddRuleDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddRule}>
              Add Rule
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteRule} onOpenChange={(open) => !open && setDeleteRule(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Rule</DialogTitle>
          </DialogHeader>
          {deleteRule && (
            <div>
              <p>Are you sure you want to delete this rule?</p>
              <div className="font-medium">{deleteRule.name}</div>
              <div className="text-sm mt-1 font-mono">{deleteRule.condition}</div>
            </div>
          )}
          <DialogFooter className="mt-4">
            <Button type="button" onClick={() => setDeleteRule(null)} variant="outline">
              Cancel
            </Button>
            <Button type="button" onClick={handleConfirmDeleteRule} variant="destructive">
              Delete Rule
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Tabs defaultValue="manual" className="w-full">
        <TabsList>
          <TabsTrigger value="manual">Manual Rules</TabsTrigger>
          <TabsTrigger value="ai">AI-Generated Rules</TabsTrigger>
          <TabsTrigger value="import-export">Import/Export</TabsTrigger>
        </TabsList>

        <TabsContent value="manual">
          <Card>
            <CardHeader>Business Rules</CardHeader>
            <CardContent>
              {rules.length > 0 ? (
                rules.map((rule) => (
                  <Card key={rule.id}>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-medium">{rule.name}</h3>
                          <p className="text-sm text-muted-foreground">{rule.condition}</p>
                        </div>
                        <div className="flex space-x-2">
                          <Button variant="ghost" size="icon" onClick={() => {
                            setEditRule(rule);
                            setIsEditDialogOpen(true);
                          }}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => setDeleteRule(rule)}>
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm">{rule.description}</p>
                      <div className="mt-2 flex items-center space-x-2">
                        <Badge variant={rule.severity === 'high' ? 'destructive' : rule.severity === 'medium' ? 'warning' : 'default'}>
                          {rule.severity}
                        </Badge>
                        {rule.active ? (
                          <Badge variant="outline">Active</Badge>
                        ) : (
                          <Badge variant="outline">Inactive</Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">No business rules defined.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ai">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="font-medium">AI-Generated Rules</h3>
                  <p className="text-sm text-muted-foreground">
                    Generate rules using AI based on your data patterns
                  </p>
                </div>
                <Select value={selectedEngine} onValueChange={(value) => setSelectedEngine(value as AIRuleEngine)}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Select AI Engine" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ai_default">Default AI</SelectItem>
                    <SelectItem value="ai_advanced">Advanced AI</SelectItem>
                    <SelectItem value="custom">Custom Model</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              <Button disabled={isLoading}>
                {isLoading ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Rules
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="import" className="space-y-4">
          <Card>
            <CardHeader>
              <h3 className="font-medium">Import Rules</h3>
              <p className="text-sm text-muted-foreground">
                Import rules from a JSON file
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <Input type="file" accept=".json" onChange={handleImport} />
                  <Button variant="outline" onClick={handleExport}>
                    <Upload className="mr-2 h-4 w-4" />
                    Export Rules
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add Rule Dialog */}
      <Dialog open={showAddRuleDialog} onOpenChange={setShowAddRuleDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Business Rule</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Name</Label>
              <Input value={newRule.name} onChange={(e) => setNewRule({...newRule, name: e.target.value})} />
            </div>
            <div>
              <Label>Description</Label>
              <Textarea value={newRule.description} onChange={(e) => setNewRule({...newRule, description: e.target.value})} />
            </div>
            <div>
              <Label>Condition</Label>
              <Textarea value={newRule.condition} onChange={(e) => setNewRule({...newRule, condition: e.target.value})} />
            </div>
            <div>
              <Label>Message</Label>
              <Textarea value={newRule.message} onChange={(e) => setNewRule({...newRule, message: e.target.value})} />
            </div>
            <div>
              <Label>Severity</Label>
              <Select value={newRule.severity} onValueChange={(value) => setNewRule({...newRule, severity: value as RuleSeverity})}>
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
            <Button variant="outline" onClick={() => setShowAddRuleDialog(false)}>Cancel</Button>
            <Button onClick={handleAddRule} disabled={!isRuleValid(newRule as BusinessRule)}>
              Add Rule
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteRule} onOpenChange={(open) => !open && setDeleteRule(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Rule</DialogTitle>
          </DialogHeader>
          {deleteRule && (
            <div>
              <p>Are you sure you want to delete this rule?</p>
              <div className="font-medium">{deleteRule.name}</div>
              <div className="text-sm mt-1 font-mono">{deleteRule.condition}</div>
            </div>
          )}
          <DialogFooter className="mt-4">
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
                ref={exportTextareaRef}
                value={JSON.stringify(rules, null, 2)}
                readOnly
                rows={8}
                className="font-mono text-xs"
              />
              <Button onClick={handleCopyToClipboard} variant="default">
                <Upload className="h-4 w-4 mr-2" /> Copy to Clipboard
              </Button>
              <Button onClick={handleExportToFile} variant="outline" className="mt-2">
                <Download className="h-4 w-4 mr-2" /> Download as File
              </Button>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  </div>
);
export default BusinessRules;
