
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { PlusCircle, Save, RefreshCw } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

interface Rule {
  id: string;
  name: string;
  description: string;
  condition: string;
  action: string;
  enabled: boolean;
}

const BusinessRules: React.FC = () => {
  const { toast } = useToast();
  const [jsonInput, setJsonInput] = useState<string>('');
  const [rules, setRules] = useState<Rule[]>([
    {
      id: '1',
      name: 'Missing Values Check',
      description: 'Flag records with null values in critical fields',
      condition: 'column.isNull("customer_id") || column.isNull("order_date")',
      action: 'flag("missing_critical_data")',
      enabled: true
    },
    {
      id: '2',
      name: 'Date Range Validation',
      description: 'Ensure order dates are within acceptable range',
      condition: 'column.date("order_date") < "2023-01-01" || column.date("order_date") > currentDate()',
      action: 'flag("invalid_date_range")',
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

  const handleGenerateRule = () => {
    toast({
      title: "Generating rule",
      description: "Analyzing data patterns to suggest new business rules..."
    });
    
    // Simulate AI generating a rule after a delay
    setTimeout(() => {
      const newRule: Rule = {
        id: `${rules.length + 1}`,
        name: `Auto-generated Rule ${rules.length + 1}`,
        description: "Detect potential outliers in transaction amounts",
        condition: "column.numeric('amount') > column.mean('amount') + 3*column.stdDev('amount')",
        action: "flag('potential_outlier')",
        enabled: true
      };
      
      setRules([...rules, newRule]);
      
      toast({
        title: "Rule generated",
        description: "New rule for outlier detection has been created based on data patterns."
      });
    }, 1500);
  };

  return (
    <Tabs defaultValue="rules">
      <TabsList className="grid grid-cols-3 mb-4">
        <TabsTrigger value="rules">Active Rules</TabsTrigger>
        <TabsTrigger value="import">Import/Export</TabsTrigger>
        <TabsTrigger value="generate">Auto-Generate</TabsTrigger>
      </TabsList>
      
      <TabsContent value="rules" className="space-y-4">
        <div className="flex justify-end">
          <Button size="sm" className="mb-2">
            <PlusCircle className="h-4 w-4 mr-2" />
            Add Rule
          </Button>
        </div>
        
        {rules.map((rule) => (
          <Card key={rule.id} className="mb-4">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex justify-between">
                <span>{rule.name}</span>
                <div className="flex items-center space-x-2 text-sm font-normal">
                  <span className={`px-2 py-1 rounded-full text-xs ${rule.enabled ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300'}`}>
                    {rule.enabled ? 'Active' : 'Disabled'}
                  </span>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-2">{rule.description}</p>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div>
                  <Label className="mb-1 block text-xs">Condition</Label>
                  <code className="block p-2 rounded bg-muted text-sm overflow-x-auto">
                    {rule.condition}
                  </code>
                </div>
                <div>
                  <Label className="mb-1 block text-xs">Action</Label>
                  <code className="block p-2 rounded bg-muted text-sm overflow-x-auto">
                    {rule.action}
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
              <Button onClick={handleImportJSON}>Import Rules</Button>
              <Button variant="outline" onClick={handleExportJSON}>Export Current Rules</Button>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
      
      <TabsContent value="generate">
        <Card>
          <CardHeader>
            <CardTitle>Auto-Generate Rules</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              Use machine learning algorithms to analyze your data and automatically generate relevant business rules 
              based on detected patterns and anomalies.
            </p>
            
            <div className="space-y-4 border rounded-md p-4 bg-muted/30">
              <div className="space-y-2">
                <Label htmlFor="data-source">Data Source</Label>
                <Input id="data-source" placeholder="Select a data source" />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="detection-type">Detection Type</Label>
                <div className="grid grid-cols-3 gap-2">
                  <Button variant="outline" className="justify-start" id="detection-type">Outliers</Button>
                  <Button variant="outline" className="justify-start">Patterns</Button>
                  <Button variant="outline" className="justify-start">Data Quality</Button>
                </div>
              </div>
            </div>
            
            <Button onClick={handleGenerateRule} className="w-full">
              <RefreshCw className="mr-2 h-4 w-4" />
              Generate Rules
            </Button>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
};

export default BusinessRules;
