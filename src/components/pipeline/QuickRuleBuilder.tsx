import React, { useState } from 'react';
import { PlusCircle, Trash2, HelpCircle } from 'lucide-react';

// Import UI components
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface Rule {
  id: string;
  name: string;
  description?: string;
  severity: 'high' | 'medium' | 'low';
  rule_type?: string;
  source?: string;
  tags?: string[];
  condition?: string;
}

interface QuickRuleBuilderProps {
  onAddRule: (rule: Rule) => void;
  onCancel?: () => void;
}

/**
 * QuickRuleBuilder component for rapidly creating simple validation rules
 */
const QuickRuleBuilder: React.FC<QuickRuleBuilderProps> = ({
  onAddRule,
  onCancel
}) => {
  const [rule, setRule] = useState<Partial<Rule>>({
    name: '',
    description: '',
    severity: 'medium',
    rule_type: 'validation',
    source: 'quick_builder',
    tags: [],
    condition: ''
  });

  const [error, setError] = useState<string | null>(null);

  const handleChange = (field: keyof Rule, value: any) => {
    setRule(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleAddRule = () => {
    if (!rule.name) {
      setError('Rule name is required');
      return;
    }

    if (!rule.condition) {
      setError('Rule condition is required');
      return;
    }

    onAddRule({
      id: `rule_${Date.now()}`,
      name: rule.name,
      description: rule.description,
      severity: rule.severity as 'high' | 'medium' | 'low',
      rule_type: rule.rule_type,
      source: rule.source,
      tags: rule.tags,
      condition: rule.condition
    });

    // Reset form
    setRule({
      name: '',
      description: '',
      severity: 'medium',
      rule_type: 'validation',
      source: 'quick_builder',
      tags: [],
      condition: ''
    });
    setError(null);
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    }
  };

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle>Quick Rule Builder</CardTitle>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon">
                <HelpCircle className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Create simple validation rules quickly</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </CardHeader>

      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name" className={!!error && !rule.name ? "text-destructive" : ""}>
              Rule Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="name"
              value={rule.name}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleChange('name', e.target.value)}
              className={!!error && !rule.name ? "border-destructive" : ""}
            />
            {error && !rule.name && (
              <p className="text-sm font-medium text-destructive">Rule name is required</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={rule.description}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => handleChange('description', e.target.value)}
              rows={2}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="severity">Severity</Label>
              <Select
                value={rule.severity}
                onValueChange={(value) => handleChange('severity', value)}
              >
                <SelectTrigger id="severity">
                  <SelectValue placeholder="Select severity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="rule_type">Rule Type</Label>
              <Select
                value={rule.rule_type}
                onValueChange={(value) => handleChange('rule_type', value)}
              >
                <SelectTrigger id="rule_type">
                  <SelectValue placeholder="Select rule type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="validation">Validation</SelectItem>
                  <SelectItem value="transformation">Transformation</SelectItem>
                  <SelectItem value="enrichment">Enrichment</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="tags">Tags</Label>
            <Input
              id="tags"
              value={rule.tags?.join(', ')}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => 
                handleChange('tags', e.target.value.split(',').map((tag: string) => tag.trim()))
              }
            />
            <p className="text-sm text-muted-foreground">Comma-separated tags</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="condition" className={!!error && !rule.condition ? "text-destructive" : ""}>
              Condition <span className="text-destructive">*</span>
            </Label>
            <Textarea
              id="condition"
              value={rule.condition}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => handleChange('condition', e.target.value)}
              rows={3}
              className={!!error && !rule.condition ? "border-destructive" : ""}
            />
            {error && !rule.condition ? (
              <p className="text-sm font-medium text-destructive">Rule condition is required</p>
            ) : (
              <p className="text-sm text-muted-foreground">Enter the rule condition in SQL-like syntax</p>
            )}
          </div>
        </div>

      </CardContent>
      
      <CardFooter className="flex justify-end space-x-2">
        {onCancel && (
          <Button 
            variant="outline" 
            onClick={handleCancel}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Cancel
          </Button>
        )}
        <Button 
          onClick={handleAddRule}
        >
          <PlusCircle className="mr-2 h-4 w-4" />
          Add Rule
        </Button>
      </CardFooter>
    </Card>
  );
};

export default QuickRuleBuilder;