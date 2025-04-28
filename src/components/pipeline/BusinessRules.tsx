import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button, buttonVariants } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { PlusCircle, Save, RefreshCw, Sparkles, AlertTriangle, Info, Check, X, Upload } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
// import { pythonApi } from '@/api/pythonIntegration'; // Removed: No longer available, see handleGenerateRule for status handling.
import { api } from '@/api/api';
import type { BusinessRule } from '@/api/services/businessRules/businessRulesService';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';

type RuleSeverity = 'low' | 'medium' | 'high';

interface BusinessRulesResponse {
  success: boolean;
  data?: BusinessRule[];
  error?: string;
}

const BusinessRules: React.FC = () => {
  const { toast } = useToast();
  const [rules, setRules] = useState<BusinessRule[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<string>("ds001");
  const [jsonInput, setJsonInput] = useState('');
  const [showAddRuleDialog, setShowAddRuleDialog] = useState(false);
  
  const [newRule, setNewRule] = useState<BusinessRule>({
    id: '',
    name: '',
    description: '',
    condition: '',
    severity: 'medium',
    message: '',
    active: true
  });

  const fetchRules = useCallback(async () => {
    if (!selectedDataset) return;
    
    setIsLoading(true);
    try {
      const response = await api.businessRules.getBusinessRules(selectedDataset);
      
      if (response.success) {
        setRules(response.data as BusinessRule[] || []);
      } else {
        toast({
          title: 'Failed to load rules',
          description: response.error || 'Unknown error occurred',
          variant: 'destructive'
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch business rules',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  }, [selectedDataset, toast]);

  useEffect(() => {
    fetchRules();
  }, [fetchRules]);

  const handleSaveRules = async () => {
    setIsLoading(true);
    try {
      const response = await api.businessRules.saveBusinessRules(selectedDataset, rules);
      
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
      dataset_id: selectedDataset,
      active: newRule.active,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    // Add locally first for immediate UI feedback
    setRules(prev => [...prev, ruleToAdd]);
    setShowAddRuleDialog(false);
    
    // Reset the form
    setNewRule({
      id: '',
      name: '',
      description: '',
      condition: '',
      severity: 'medium',
      message: '',
      active: true
    });
    
    // Then save to the server
    try {
      // We'll use saveBusinessRules to add a new rule
      const response = await api.businessRules.saveBusinessRules(selectedDataset, [...rules, ruleToAdd]);
      
      if (response.success) {
        toast({
          title: "Rule added successfully",
          description: `"${ruleToAdd.name}" has been added to your rule set.`
        });
      } else {
        // Remove the rule if the server save failed
        setRules(rules);
        toast({
          title: "Failed to add rule",
          description: response.error || "An unknown error occurred",
          variant: "destructive"
        });
      }
    } catch (error) {
      // Remove the rule if there was an error
      setRules(rules);
      toast({
        title: "Error adding rule",
        description: "An unexpected error occurred while adding the rule.",
        variant: "destructive"
      });
    }
  };

  const handleDeleteRule = async (id: string) => {
    // Find the rule to delete
    const ruleToDelete = rules.find(rule => rule.id === id);
    if (!ruleToDelete) return;
    
    try {
      const updatedRules = rules.filter(rule => rule.id !== id);
      const response = await api.businessRules.saveBusinessRules(selectedDataset, updatedRules);
      
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
    }
  };

  const handleToggleRule = async (id: string) => {
    // Find the rule to toggle
    const ruleToToggle = rules.find(rule => rule.id === id);
    if (!ruleToToggle) return;
    
    // Update locally first for immediate UI feedback
    const updatedRules = rules.map(rule => 
      rule.id === id ? {...rule, active: !rule.active} : rule
    );
    
    // Then update on the server
    try {
      const response = await api.businessRules.saveBusinessRules(selectedDataset, updatedRules);
      
      if (response.success) {
        setRules(updatedRules);
      } else {
        // Revert the change if the server update failed
        setRules(rules);
        toast({
          title: "Update failed",
          description: response.error || "Failed to update rule status",
          variant: "destructive"
        });
      }
    } catch (error) {
      // Revert the change if there was an error
      setRules(rules);
      toast({
        title: "Update error",
        description: "An unexpected error occurred while updating the rule.",
        variant: "destructive"
      });
    }
  };

  // AI Rule Generation is currently disabled. This is a placeholder for future implementation.
  const handleGenerateRule = async (): Promise<void> => {
    setIsLoading(true);
    toast({
      title: "AI Rule Generation Unavailable",
      description: "Automatic business rule generation via AI is not currently supported. Please define rules manually.",
      variant: "destructive"
    });
    setIsLoading(false);
    // If/when AI-based rule generation is restored, implement here.
    return;
  }

  const handleSaveRulesToAPI = async () => {
    toast({
      title: "Saving rules",
      description: "Saving business rules to the data pipeline..."
    });
    
    try {
      const response = await api.businessRules.saveBusinessRules(selectedDataset, rules);
      
      if (response.success) {
        toast({
          title: "Rules saved successfully",
          description: response && response.data && response.data.message ? response.data.message : `${rules.length} rules have been saved.`
        });
      } else {
        toast({
          title: "Failed to save rules",
          description: response && response.error ? response.error : "An unknown error occurred",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "An unexpected error occurred when saving rules.",
        variant: "destructive"
      });
    }
  };

  return (
    <>
      <Tabs defaultValue="rules">
        <TabsList className="grid grid-cols-3 mb-4">
          <TabsTrigger value="rules">Active Rules</TabsTrigger>
          <TabsTrigger value="import">Import/Export</TabsTrigger>
          <TabsTrigger value="generate">Auto-Generate</TabsTrigger>
        </TabsList>
        
        <TabsContent value="rules" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-sm text-muted-foreground">
                Manage your business rules and validation criteria
              </p>
            </div>
            <div className="flex gap-2">
              <Button className="mb-2" onClick={() => setShowAddRuleDialog(true)}>
                <PlusCircle className="h-4 w-4 mr-2" />
                Add Rule
              </Button>
              <Button
                variant="outline"
                className="mb-2"
                onClick={handleSaveRulesToAPI}
              >
                <Save className="h-4 w-4 mr-2" />
                Save Rules
              </Button>
            </div>
          </div>
          
          {rules.map((rule) => (
            <Card key={rule.id} className={`mb-4 ${rule.model_generated ? 'border-blue-200 dark:border-blue-900' : ''}`}>
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg flex items-center gap-2">
                      {rule.name}
                      {rule.model_generated && (
                        <Badge variant="outline" className="ml-2 bg-blue-50 text-blue-700 dark:bg-blue-900 dark:text-blue-200 border-blue-200 dark:border-blue-800 flex items-center gap-1">
                          <Sparkles className="h-3 w-3" />
                          <span className="text-xs">AI Generated</span>
                        </Badge>
                      )}
                    </CardTitle>
                    {rule.description && (
                      <CardDescription>{rule.description}</CardDescription>
                    )}
                  </div>
                  <div className="flex items-center space-x-2 text-sm font-normal">
                    <Badge variant={rule.severity === 'high' ? 'destructive' : rule.severity === 'medium' ? 'default' : 'outline'}>
                      {rule.severity.charAt(0).toUpperCase() + rule.severity.slice(1)} Severity
                    </Badge>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => handleToggleRule(rule.id)}
                      className={rule.active === false ? 'text-muted-foreground' : 'text-primary'}
                    >
                      {rule.active === false ? 'Disabled' : 'Active'}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {typeof rule.confidence === 'number' && (
                  <div className="mb-3 flex items-center text-xs">
                    <Info className="h-3 w-3 mr-1 text-blue-500" />
                    <span>
                      Confidence: <span className="font-medium">{Math.round(rule.confidence * 100)}%</span>
                    </span>
                    {rule.confidence < 0.8 && (
                      <span className="flex items-center ml-2 text-amber-600">
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        Review recommended
                      </span>
                    )}
                  </div>
                )}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <div>
                    <Label className="mb-1 block text-xs">Condition</Label>
                    <code className="block p-2 rounded bg-muted text-sm overflow-x-auto">
                      {rule.condition}
                    </code>
                  </div>
                  <div>
                    <Label className="mb-1 block text-xs">Message</Label>
                    <code className="block p-2 rounded bg-muted text-sm overflow-x-auto">
                      {rule.message}
                    </code>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
        
        <TabsContent value="import">
          <Card>
            <CardHeader>
              <CardTitle>Import/Export Rules</CardTitle>
              <CardDescription>
                Share rule configurations between systems or create backups
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="mb-2 block">JSON Configuration</Label>
                <Textarea 
                  placeholder="Paste your JSON rules configuration here..."
                  className="font-mono"
                  rows={10}
                  value={jsonInput}
                  onChange={(e) => setJsonInput(e.target.value)}
                />
              </div>
              <div className="flex space-x-2">
                <Button onClick={handleImport}>
                  <Check className="h-4 w-4 mr-2" />
                  Import Rules
                </Button>
                <button
                  className={buttonVariants({ variant: 'outline' })}
                  onClick={handleExport}
                >
                  <Save className="h-4 w-4 mr-2" />
                  Export Current Rules
                </button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="generate">
          <Card>
            <CardHeader>
              <CardTitle>Auto-Generate Rules with ML</CardTitle>
              <CardDescription>
                Use Hugging Face models to analyze your data and automatically generate relevant business rules 
                based on detected patterns and anomalies.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4 border rounded-md p-4 bg-muted/30">
                <div className="space-y-2">
                  <Label htmlFor="data-source">Data Source</Label>
                  <Select 
                    value={selectedDataset} 
                    onValueChange={setSelectedDataset}
                  >
                    <SelectTrigger id="data-source">
                      <SelectValue placeholder="Select a dataset" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ds001">Customer Orders</SelectItem>
                      <SelectItem value="ds002">Product Inventory</SelectItem>
                      <SelectItem value="ds003">Sales Transactions</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="detection-type">Detection Type</Label>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      className={buttonVariants({ variant: 'outline', className: 'justify-start' })}
                      id="detection-type"
                    >
                      <Check className="h-4 w-4 mr-2" />
                      Outliers
                    </button>
                    <button
                      className={buttonVariants({ variant: 'outline', className: 'w-full' })}
                      id="import-button"
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      Import Rules
                    </button>
                    <button
                      className={buttonVariants({ variant: 'outline', className: 'justify-start' })}
                    >
                      <Check className="h-4 w-4 mr-2" />
                      Data Quality
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="model-selection">Machine Learning Model</Label>
                  <Select defaultValue="huggingface">
                    <SelectTrigger id="model-selection">
                      <SelectValue placeholder="Select model type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="huggingface">Hugging Face Models</SelectItem>
                      <SelectItem value="pydantic">Pydantic Schema Inference</SelectItem>
                      <SelectItem value="ge">Great Expectations</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <Button 
                onClick={handleGenerateRule} 
                className="w-full" 
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Generating Rules...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Rules with ML
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      
      <Dialog open={showAddRuleDialog} onOpenChange={setShowAddRuleDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add New Business Rule</DialogTitle>
            <DialogDescription>
              Create a custom business rule to validate your data
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="rule-name">Rule Name</Label>
              <Input 
                id="rule-name" 
                placeholder="e.g., Valid Customer Age" 
                value={newRule.name}
                onChange={(e) => setNewRule({...newRule, name: e.target.value})}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="rule-description">Description (Optional)</Label>
              <Input 
                id="rule-description" 
                placeholder="Briefly describe the purpose of this rule"
                value={newRule.description || ''}
                onChange={(e) => setNewRule({...newRule, description: e.target.value})}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="rule-condition">Condition</Label>
              <Textarea 
                id="rule-condition" 
                placeholder="e.g., data['age'] >= 18 && data['age'] <= 120"
                className="font-mono"
                value={newRule.condition}
                onChange={(e) => setNewRule({...newRule, condition: e.target.value})}
              />
              <p className="text-xs text-muted-foreground">
                Define the validation logic using JavaScript-like syntax
              </p>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="rule-message">Error Message</Label>
              <Input 
                id="rule-message" 
                placeholder="e.g., Age must be between 18 and 120"
                value={newRule.message}
                onChange={(e) => setNewRule({...newRule, message: e.target.value})}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="rule-severity">Severity</Label>
              <Select 
                value={newRule.severity} 
                onValueChange={(value) => setNewRule({...newRule, severity: value as 'low' | 'medium' | 'high'})}
              >
                <SelectTrigger id="rule-severity">
                  <SelectValue placeholder="Select severity level" />
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
            <button
              className={buttonVariants({ variant: 'outline' })}
              onClick={() => setShowAddRuleDialog(false)}
            >
              <X className="h-4 w-4 mr-2" />
              Cancel
            </button>
            <Button onClick={handleAddRule}>
              <PlusCircle className="h-4 w-4 mr-2" />
              Add Rule
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default BusinessRules;
