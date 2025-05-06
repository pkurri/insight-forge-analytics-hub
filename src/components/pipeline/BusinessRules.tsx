
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { 
  Dialog, 
  DialogContent, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { api } from '@/api/api';
import { BusinessRule } from '@/api/types';
import { Pencil, Trash, Plus, Filter, Database } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Badge } from '@/components/ui/badge';

const BusinessRules: React.FC = () => {
  const [rules, setRules] = useState<BusinessRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [currentRule, setCurrentRule] = useState<Partial<BusinessRule> | null>(null);
  const [ruleToDelete, setRuleToDelete] = useState<string | null>(null);
  const { toast } = useToast();

  const fetchRules = async () => {
    setLoading(true);
    try {
      const response = await api.businessRules.getBusinessRules();
      if (response.success && response.data) {
        setRules(response.data);
      } else {
        setError(response.error || 'Failed to fetch business rules');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const handleAddRule = () => {
    setCurrentRule({
      name: '',
      description: '',
      condition: '',
      severity: 'medium',
      active: true
    });
    setIsDialogOpen(true);
  };

  const handleEditRule = (rule: BusinessRule) => {
    setCurrentRule(rule);
    setIsDialogOpen(true);
  };

  const handleDeleteRule = (ruleId: string) => {
    setRuleToDelete(ruleId);
    setIsDeleteDialogOpen(true);
  };

  const handleSaveRule = async () => {
    if (!currentRule?.name || !currentRule?.condition) {
      toast({
        title: "Validation error",
        description: "Name and condition are required",
        variant: "destructive",
      });
      return;
    }

    try {
      let response;
      
      if (currentRule.id) {
        // Update existing rule
        response = await api.businessRules.updateBusinessRule(
          currentRule.id,
          currentRule
        );
      } else {
        // Create new rule
        response = await api.businessRules.createBusinessRule(currentRule);
      }

      if (response.success) {
        toast({
          title: currentRule.id ? "Rule updated" : "Rule created",
          description: `Business rule "${currentRule.name}" was ${currentRule.id ? 'updated' : 'created'} successfully`,
        });
        setIsDialogOpen(false);
        fetchRules();
      } else {
        toast({
          title: "Operation failed",
          description: response.error || "Failed to save business rule",
          variant: "destructive",
        });
      }
    } catch (e) {
      toast({
        title: "Error",
        description: e instanceof Error ? e.message : "An unexpected error occurred",
        variant: "destructive",
      });
    }
  };

  const handleConfirmDelete = async () => {
    if (!ruleToDelete) return;

    try {
      const response = await api.businessRules.deleteBusinessRule(ruleToDelete);
      
      if (response.success) {
        toast({
          title: "Rule deleted",
          description: "Business rule was deleted successfully",
        });
        setIsDeleteDialogOpen(false);
        fetchRules();
      } else {
        toast({
          title: "Deletion failed",
          description: response.error || "Failed to delete business rule",
          variant: "destructive",
        });
      }
    } catch (e) {
      toast({
        title: "Error",
        description: e instanceof Error ? e.message : "An unexpected error occurred",
        variant: "destructive",
      });
    }
  };

  const renderSeverityBadge = (severity: string) => {
    const badgeClass = 
      severity === 'high' ? "bg-red-100 text-red-800 hover:bg-red-200" :
      severity === 'medium' ? "bg-yellow-100 text-yellow-800 hover:bg-yellow-200" :
      "bg-blue-100 text-blue-800 hover:bg-blue-200";
      
    return (
      <Badge variant="outline" className={badgeClass}>
        {severity}
      </Badge>
    );
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Business Rules</CardTitle>
          <Button onClick={handleAddRule}>
            <Plus className="h-4 w-4 mr-2" />
            Add Rule
          </Button>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center p-4">Loading business rules...</div>
          ) : error ? (
            <div className="text-center text-red-500 p-4">{error}</div>
          ) : rules.length === 0 ? (
            <div className="text-center p-8 space-y-4">
              <div className="text-muted-foreground">No business rules defined yet</div>
              <Button onClick={handleAddRule} variant="outline">Create your first rule</Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Condition</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rules.map((rule) => (
                  <TableRow key={rule.id}>
                    <TableCell className="font-medium">{rule.name}</TableCell>
                    <TableCell className="max-w-md truncate">{rule.condition}</TableCell>
                    <TableCell>{renderSeverityBadge(rule.severity)}</TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        rule.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {rule.active ? 'Active' : 'Inactive'}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" onClick={() => handleEditRule(rule)}>
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDeleteRule(rule.id)}>
                        <Trash className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
        <CardFooter className="flex justify-between">
          <div className="text-xs text-muted-foreground">
            {rules.length} business rule{rules.length !== 1 ? 's' : ''}
          </div>
          <div className="flex space-x-2">
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              Filter
            </Button>
            <Button variant="outline" size="sm">
              <Database className="h-4 w-4 mr-2" />
              Import Rules
            </Button>
          </div>
        </CardFooter>
      </Card>

      {/* Add/Edit Rule Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{currentRule?.id ? 'Edit' : 'Add'} Business Rule</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="name">Rule Name</Label>
              <Input
                id="name"
                value={currentRule?.name || ''}
                onChange={(e) => setCurrentRule({ ...currentRule, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description (Optional)</Label>
              <Textarea
                id="description"
                value={currentRule?.description || ''}
                onChange={(e) => setCurrentRule({ ...currentRule, description: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="condition">Condition</Label>
              <Textarea
                id="condition"
                value={currentRule?.condition || ''}
                onChange={(e) => setCurrentRule({ ...currentRule, condition: e.target.value })}
                placeholder="e.g., data['age'] >= 18"
              />
              <p className="text-xs text-muted-foreground">
                Enter a condition using Python-like syntax. Use 'data' to access column values.
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="severity">Severity</Label>
              <Select
                value={currentRule?.severity || 'medium'}
                onValueChange={(value) => setCurrentRule({ ...currentRule, severity: value as 'low' | 'medium' | 'high' })}
              >
                <SelectTrigger id="severity">
                  <SelectValue placeholder="Select severity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="active"
                checked={currentRule?.active}
                onCheckedChange={(checked) => setCurrentRule({ ...currentRule, active: checked })}
              />
              <Label htmlFor="active">Active</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSaveRule}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Business Rule</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p>Are you sure you want to delete this business rule? This action cannot be undone.</p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleConfirmDelete}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default BusinessRules;
