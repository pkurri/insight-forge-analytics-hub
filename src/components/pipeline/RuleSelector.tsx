import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  CardFooter
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { AlertCircle, AlertTriangle, Info, Plus, Trash2 } from 'lucide-react';

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

interface RuleSelectorProps {
  selectedRules: Rule[];
  onRulesChange: (rules: Rule[]) => void;
  availableRules?: Rule[];
  isLoading?: boolean;
  error?: string;
  onAddRule?: (rule: Rule) => void;
  onRemoveRule?: (ruleId: string) => void;
  showActions?: boolean;
}

/**
 * RuleSelector component for selecting and managing data validation rules
 */
const RuleSelector: React.FC<RuleSelectorProps> = ({
  selectedRules = [],
  onRulesChange,
  availableRules = [],
  isLoading = false,
  error = null,
  onAddRule,
  onRemoveRule,
  showActions = true
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedRules, setExpandedRules] = useState<Record<string, boolean>>({});
  const [openNewRuleDialog, setOpenNewRuleDialog] = useState(false);
  const [newRule, setNewRule] = useState<Partial<Rule>>({
    name: '',
    description: '',
    severity: 'medium',
    rule_type: 'validation',
    source: 'manual',
    tags: [],
    condition: ''
  });

  // Filter rules based on search query
  const filteredRules = availableRules.filter(rule => 
    rule.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (rule.description && rule.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (rule.tags && rule.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase())))
  );

  // Toggle rule expansion
  const toggleRuleExpansion = (ruleId: string) => {
    setExpandedRules(prev => ({
      ...prev,
      [ruleId]: !prev[ruleId]
    }));
  };

  // Get severity icon
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <AlertCircle className="h-4 w-4 text-destructive" />;
      case 'medium':
        return <AlertTriangle className="h-4 w-4 text-warning" />;
      case 'low':
        return <Info className="h-4 w-4 text-info" />;
      default:
        return <Info className="h-4 w-4 text-info" />;
    }
  };

  // Handle new rule dialog
  const handleOpenNewRuleDialog = () => {
    setOpenNewRuleDialog(true);
  };

  const handleCloseNewRuleDialog = () => {
    setOpenNewRuleDialog(false);
    setNewRule({
      name: '',
      description: '',
      severity: 'medium',
      rule_type: 'validation',
      source: 'manual',
      tags: [],
      condition: ''
    });
  };

  const handleNewRuleChange = (field: keyof Rule, value: any) => {
    setNewRule(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleAddNewRule = () => {
    if (newRule.name && onAddRule) {
      onAddRule({
        id: `rule_${Date.now()}`,
        name: newRule.name,
        description: newRule.description,
        severity: newRule.severity as 'high' | 'medium' | 'low',
        rule_type: newRule.rule_type,
        source: newRule.source,
        tags: newRule.tags,
        condition: newRule.condition
      });
      handleCloseNewRuleDialog();
    }
  };

  // Render rule card
  const renderRuleCard = (rule: Rule, isSelected: boolean) => {
    const isExpanded = !!expandedRules[rule.id];
    
    return (
      <Card key={rule.id} className="mb-2">
        <CardHeader className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getSeverityIcon(rule.severity)}
              <CardTitle className="text-base">{rule.name}</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleRuleExpansion(rule.id)}
              >
                {isExpanded ? 'Show Less' : 'Show More'}
              </Button>
              {isSelected ? (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onRemoveRule && onRemoveRule(rule.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              ) : (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onAddRule && onAddRule(rule)}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        
        {isExpanded && (
          <CardContent className="p-4 pt-0">
            {rule.description && (
              <CardDescription className="mb-4">
                {rule.description}
              </CardDescription>
            )}
            
            <div className="flex flex-wrap gap-2 mb-4">
              <Badge variant="outline">
                {rule.rule_type || 'validation'}
              </Badge>
              <Badge variant="outline">
                {rule.source || 'manual'}
              </Badge>
              {rule.tags?.map(tag => (
                <Badge key={tag} variant="secondary">
                  {tag}
                </Badge>
              ))}
            </div>
            
            {rule.condition && (
              <div className="mt-4">
                <div className="text-sm text-muted-foreground mb-2">
                  Condition:
                </div>
                <ScrollArea className="h-20 rounded-md border p-2">
                  <pre className="text-sm font-mono">
                    {rule.condition}
                  </pre>
                </ScrollArea>
              </div>
            )}
          </CardContent>
        )}
      </Card>
    );
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <CardTitle>Rule Selection</CardTitle>
        {showActions && (
          <Dialog open={openNewRuleDialog} onOpenChange={setOpenNewRuleDialog}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                New Rule
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Rule</DialogTitle>
                <DialogDescription>
                  Create a new validation rule for your data pipeline.
                </DialogDescription>
              </DialogHeader>
              
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Rule Name</Label>
                  <Input
                    id="name"
                    value={newRule.name}
                    onChange={(e) => handleNewRuleChange('name', e.target.value)}
                    placeholder="Enter rule name"
                  />
                </div>
                
                <div className="grid gap-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={newRule.description}
                    onChange={(e) => handleNewRuleChange('description', e.target.value)}
                    placeholder="Enter rule description"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label>Severity</Label>
                    <Select
                      value={newRule.severity}
                      onValueChange={(value) => handleNewRuleChange('severity', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select severity" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="low">Low</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="grid gap-2">
                    <Label>Rule Type</Label>
                    <Select
                      value={newRule.rule_type}
                      onValueChange={(value) => handleNewRuleChange('rule_type', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="validation">Validation</SelectItem>
                        <SelectItem value="transformation">Transformation</SelectItem>
                        <SelectItem value="enrichment">Enrichment</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div className="grid gap-2">
                  <Label htmlFor="source">Source</Label>
                  <Input
                    id="source"
                    value={newRule.source}
                    onChange={(e) => handleNewRuleChange('source', e.target.value)}
                    placeholder="Enter rule source"
                  />
                </div>
                
                <div className="grid gap-2">
                  <Label htmlFor="tags">Tags</Label>
                  <Input
                    id="tags"
                    value={newRule.tags?.join(', ')}
                    onChange={(e) => handleNewRuleChange('tags', e.target.value.split(',').map(tag => tag.trim()))}
                    placeholder="Enter tags (comma-separated)"
                  />
                </div>
                
                <div className="grid gap-2">
                  <Label htmlFor="condition">Condition</Label>
                  <Textarea
                    id="condition"
                    value={newRule.condition}
                    onChange={(e) => handleNewRuleChange('condition', e.target.value)}
                    placeholder="Enter rule condition in SQL-like syntax"
                  />
                </div>
              </div>
              
              <DialogFooter>
                <Button variant="outline" onClick={handleCloseNewRuleDialog}>
                  Cancel
                </Button>
                <Button onClick={handleAddNewRule} disabled={!newRule.name}>
                  Create Rule
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </div>

      <div className="mb-4">
        <Input
          placeholder="Search rules..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {isLoading ? (
        <div className="flex justify-center p-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div>
          {selectedRules.length > 0 && (
            <div className="mb-6">
              <CardTitle className="text-lg mb-4">
                Selected Rules ({selectedRules.length})
              </CardTitle>
              {selectedRules.map(rule => renderRuleCard(rule, true))}
            </div>
          )}

          {filteredRules.length > 0 && (
            <div>
              <CardTitle className="text-lg mb-4">
                Available Rules
              </CardTitle>
              {filteredRules
                .filter(rule => !selectedRules.some(selected => selected.id === rule.id))
                .map(rule => renderRuleCard(rule, false))}
            </div>
          )}

          {filteredRules.length === 0 && !isLoading && (
            <CardDescription>
              No rules found matching your search criteria.
            </CardDescription>
          )}
        </div>
      )}
    </div>
  );
};

export default RuleSelector; 