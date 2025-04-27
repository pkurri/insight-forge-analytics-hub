import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button, buttonVariants } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { PlusCircle, Save, RefreshCw, Sparkles, AlertTriangle, Info, Check, X } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { pythonApi } from '@/api/pythonIntegration';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { api } from '@/api/api';

interface Rule {
  id: string;
  name: string;
  description?: string;
  condition: string;
  severity: 'low' | 'medium' | 'high';
  message: string;
  enabled?: boolean;
  confidence?: number;
  model_generated?: boolean;
}

const BusinessRules: React.FC = () => {
  const { toast } = useToast();
  const [jsonInput, setJsonInput] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<string>("ds001");
  const [showAddRuleDialog, setShowAddRuleDialog] = useState(false);
  
  const [newRule, setNewRule] = useState<Rule>({
    id: '',
    name: '',
    description: '',
    condition: '',
    severity: 'medium',
    message: '',
    enabled: true
  });
  
  const [rules, setRules] = useState<Rule[]>([
    {
      id: '1',
      name: 'Missing Values Check',
      description: 'Flag records with null values in critical fields',
      condition: 'column.isNull("customer_id") || column.isNull("order_date")',
      severity: 'high',
      message: 'Missing critical data in required fields',
      enabled: true
    },
    {
      id: '2',
      name: 'Date Range Validation',
      description: 'Ensure order dates are within acceptable range',
      condition: 'column.date("order_date") < "2023-01-01" || column.date("order_date") > currentDate()',
      severity: 'medium',
      message: 'Order date outside acceptable range',
      enabled: true
    }
  ]);

  useEffect(() => {
    // Fetch rules from API when dataset changes
    const fetchRules = async () => {
      if (!selectedDataset) return;
      
      try {
        const response = await api.getBusinessRules(selectedDataset);
        if (response.success && response.data) {
          // Map the API response to our component's rule format
          const fetchedRules = response.data.map(rule => ({
            id: rule.id,
            name: rule.name,
            description: rule.description || '',
            condition: rule.condition,
            severity: rule.severity || 'medium',
            message: rule.message || rule.description || '',
            enabled: rule.active
          }));
          setRules(fetchedRules);
        } else {
          // If API fails, set empty rules array
          setRules([]);
          toast({
            title: "Failed to fetch rules",
            description: response.error || "Could not load business rules",
            variant: "destructive"
          });
        }
      } catch (error) {
        setRules([]);
        toast({
          title: "Error",
          description: "An unexpected error occurred while fetching rules.",
          variant: "destructive"
        });
      }
    };
    
    fetchRules();
  }, [selectedDataset]);

  const handleImportJSON = () => {
    try {
      const importedRules = JSON.parse(jsonInput);
      if (Array.isArray(importedRules)) {
        setRules(importedRules);
        toast({
          title: "Rules imported successfully",
          description: `${importedRules.length} rules have been imported.`
        });
      } else {
        throw new Error("Invalid format. JSON must be an array of rule objects.");
      }
    } catch (error) {
      toast({
        title: "Import failed",
        description: error instanceof Error ? error.message : "Invalid JSON format",
        variant: "destructive"
      });
    }
  };

  const handleExportRules = async () => {
    try {
      // Call the API to get the export data
      const response = await api.exportBusinessRules(selectedDataset);
      
      if (response.success && response.data) {
        const jsonStr = JSON.stringify(response.data.rules, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `business_rules_${selectedDataset}_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        toast({
          title: "Rules exported",
          description: `${response.data.rules.length} rules have been exported to JSON.`
        });
      } else {
        toast({
          title: "Export failed",
          description: response.error || "Failed to export rules",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Export error",
        description: "An unexpected error occurred during export.",
        variant: "destructive"
      });
    }
  };

  const handleDeleteRule = async (id: string) => {
    // Find the rule to delete
    const ruleToDelete = rules.find(rule => rule.id === id);
    if (!ruleToDelete) return;
    
    // Remove locally first for immediate UI feedback
    setRules(rules.filter(rule => rule.id !== id));
    
    // Then delete on the server
    try {
      const response = await api.deleteBusinessRule(selectedDataset, id);
      
      if (response.success) {
        toast({
          title: "Rule deleted",
          description: "The rule has been removed from your rule set."
        });
      } else {
        // Revert the change if the server update failed
        setRules(rules);
        toast({
          title: "Delete failed",
          description: response.error || "Failed to delete rule",
          variant: "destructive"
        });
      }
    } catch (error) {
      // Revert the change if there was an error
      setRules(rules);
      toast({
        title: "Delete error",
        description: "An unexpected error occurred while deleting the rule.",
        variant: "destructive"
      });
    }
  };

  const handleImportRules = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const content = e.target?.result as string;
        
        // Call the API to import the rules
        const response = await api.importBusinessRules(selectedDataset, content);
        
        if (response.success) {
          // Refresh the rules list after import
          const rulesResponse = await api.getBusinessRules(selectedDataset);
          if (rulesResponse.success && rulesResponse.data) {
            setRules(rulesResponse.data);
          }
          
          toast({
            title: "Rules imported",
            description: response.data?.message || "Rules have been imported successfully."
          });
        } else {
          toast({
            title: "Import failed",
            description: response.error || "Failed to import rules",
            variant: "destructive"
          });
        }
      } catch (error) {
        toast({
          title: "Import failed",
          description: "Failed to parse the imported file.",
          variant: "destructive"
        });
      }
    };
    
    reader.readAsText(file);
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
      active: newRule.enabled,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    // Add locally first for immediate UI feedback
    setRules([...rules, ruleToAdd]);
    setShowAddRuleDialog(false);
    
    // Reset the form
    setNewRule({
      id: '',
      name: '',
      description: '',
      condition: '',
      severity: 'medium',
      message: '',
      enabled: true
    });
    
    // Then save to the server
    try {
      // We'll use saveBusinessRules to add a new rule
      const response = await api.saveBusinessRules(selectedDataset, [...rules, ruleToAdd]);
      
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

  const handleToggleRule = async (id: string) => {
    // Find the rule to toggle
    const ruleToToggle = rules.find(rule => rule.id === id);
    if (!ruleToToggle) return;
    
    // Update locally first for immediate UI feedback
    setRules(rules.map(rule => 
      rule.id === id ? { ...rule, enabled: !rule.enabled } : rule
    ));
    
    // Then update on the server
    try {
      const response = await api.updateBusinessRule(
        selectedDataset, 
        id, 
        { active: !ruleToToggle.enabled }
      );
      
      if (!response.success) {
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

  const handleGenerateRule = async () => {
    setIsGenerating(true);
    
    toast({
      title: "Generating rules",
      description: "Analyzing data patterns with AI models..."
    });
    
    try {
      const response = await pythonApi.generateBusinessRules(selectedDataset, {
        use_ml: true,
        confidence_threshold: 0.7
      });
      
      if (response.success && response.data) {
        const generatedRules = response.data.rules;
        
        // Map the generated rules to our format
        const formattedRules = generatedRules.map(rule => ({
          id: rule.id || `ai-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
          name: rule.name,
          description: rule.message || "",
          condition: rule.condition,
          severity: rule.severity || "medium",
          message: rule.message,
          enabled: true,
          dataset_id: selectedDataset,
          active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }));
        
        // Update local state
        setRules([...rules, ...formattedRules]);
        
        // Save to server
        await api.saveBusinessRules(selectedDataset, [...rules, ...formattedRules]);
        
        toast({
          title: "Rules generated successfully",
          description: `${formattedRules.length} new rules have been created based on data patterns.`
        });
      } else {
        toast({
          title: "Rule generation failed",
          description: response.error || "Failed to generate rules",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "An unexpected error occurred while generating rules.",
        variant: "destructive"
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveRulesToAPI = async () => {
    toast({
      title: "Saving rules",
      description: "Saving business rules to the data pipeline..."
    });
    
    try {
      const response = await api.saveBusinessRules(selectedDataset, rules);
      
      if (response.success) {
        toast({
          title: "Rules saved successfully",
          description: response.data?.message || `${rules.length} rules have been saved.`
        });
      } else {
        toast({
          title: "Failed to save rules",
          description: response.error || "An unknown error occurred",
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
              <button
                className={buttonVariants({ variant: 'outline', className: 'mb-2' })}
                onClick={handleSaveRulesToAPI}
              >
                <Save className="h-4 w-4 mr-2" />
                Save Rules
              </button>
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
                      className={rule.enabled === false ? 'text-muted-foreground' : 'text-primary'}
                    >
                      {rule.enabled === false ? 'Disabled' : 'Active'}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {rule.confidence && (
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
                <Button onClick={handleImportJSON}>
                  <Check className="h-4 w-4 mr-2" />
                  Import Rules
                </Button>
                <button
                  className={buttonVariants({ variant: 'outline' })}
                  onClick={handleExportJSON}
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
                disabled={isGenerating}
              >
                {isGenerating ? (
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
