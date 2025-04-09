
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { PlusCircle, Save, RefreshCw, Sparkles, AlertTriangle, Info, Check } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { pythonApi } from '@/api/pythonIntegration';

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

  const handleExportJSON = () => {
    const jsonString = JSON.stringify(rules, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const href = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = href;
    link.download = 'business_rules.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(href);
    
    toast({
      title: "Rules exported",
      description: `${rules.length} rules have been exported to JSON.`
    });
  };

  const handleGenerateRule = async () => {
    setIsGenerating(true);
    
    toast({
      title: "Generating rules",
      description: "Analyzing data patterns with Hugging Face models..."
    });
    
    try {
      // Call the Python API to generate rules
      const response = await pythonApi.generateBusinessRules(selectedDataset, {
        use_ml: true,
        confidence_threshold: 0.7
      });
      
      if (response.success && response.data) {
        // Add the generated rules to existing rules
        const generatedRules = response.data.rules;
        setRules([...rules, ...generatedRules]);
        
        toast({
          title: "Rules generated successfully",
          description: `${generatedRules.length} new rules have been created based on data patterns.`
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

  return (
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
          <Button size="sm" className="mb-2">
            <PlusCircle className="h-4 w-4 mr-2" />
            Add Rule
          </Button>
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
                  <Badge variant={rule.enabled === false ? 'outline' : 'secondary'}>
                    {rule.enabled === false ? 'Disabled' : 'Active'}
                  </Badge>
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
              <Button variant="outline" onClick={handleExportJSON}>
                <Save className="h-4 w-4 mr-2" />
                Export Current Rules
              </Button>
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
                  <Button variant="outline" className="justify-start" id="detection-type">
                    <Check className="h-4 w-4 mr-2" />
                    Outliers
                  </Button>
                  <Button variant="outline" className="justify-start">
                    <Check className="h-4 w-4 mr-2" />
                    Patterns
                  </Button>
                  <Button variant="outline" className="justify-start">
                    <Check className="h-4 w-4 mr-2" />
                    Data Quality
                  </Button>
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
  );
};

export default BusinessRules;
