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
import { Separator } from '@/components/ui/separator';
import { AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';

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

interface ImpactAnalysis {
  totalRecords: number;
  passingRecords: number;
  failingRecords: number;
  impactPercentage: number;
}

interface RulePreviewProps {
  rules?: Rule[];
  onRemoveRule?: (ruleId: string) => void;
  impactAnalysis?: ImpactAnalysis | null;
  showActions?: boolean;
  onApplyRules?: () => void;
}

/**
 * RulePreview component to display selected rules and their potential impacts
 */
const RulePreview: React.FC<RulePreviewProps> = ({
  rules = [],
  onRemoveRule,
  impactAnalysis = null,
  showActions = true,
  onApplyRules
}) => {
  const [expandedRules, setExpandedRules] = useState<Record<string, boolean>>({});

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

  // Group rules by type
  const rulesByType = rules.reduce<Record<string, Rule[]>>((acc, rule) => {
    const type = rule.rule_type || 'validation';
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(rule);
    return acc;
  }, {});

  // Render impact analysis
  const renderImpactAnalysis = () => {
    if (!impactAnalysis) return null;

    return (
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Estimated Impact</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4">
              <div className="text-2xl font-bold text-primary">
                {impactAnalysis.totalRecords}
              </div>
              <div className="text-sm text-muted-foreground">
                Total Records
              </div>
            </div>
            <div className="text-center p-4">
              <div className="text-2xl font-bold text-success">
                {impactAnalysis.passingRecords}
              </div>
              <div className="text-sm text-muted-foreground">
                Passing Records
              </div>
            </div>
            <div className="text-center p-4">
              <div className="text-2xl font-bold text-destructive">
                {impactAnalysis.failingRecords}
              </div>
              <div className="text-sm text-muted-foreground">
                Failing Records
              </div>
            </div>
            <div className="text-center p-4">
              <div className={`text-2xl font-bold ${impactAnalysis.impactPercentage > 20 ? 'text-destructive' : 'text-warning'}`}>
                {impactAnalysis.impactPercentage}%
              </div>
              <div className="text-sm text-muted-foreground">
                Impact Rate
              </div>
            </div>
          </div>
          
          {impactAnalysis.impactPercentage > 20 && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                High impact detected. These rules will filter out a significant portion of your data.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    );
  };

  // Render rule card
  const renderRuleCard = (rule: Rule) => {
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
              {onRemoveRule && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onRemoveRule(rule.id)}
                >
                  Remove
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
      <CardHeader>
        <CardTitle>Selected Rules ({rules.length})</CardTitle>
      </CardHeader>
      
      {renderImpactAnalysis()}
      
      {rules.length === 0 ? (
        <CardDescription>
          No rules selected. Select rules to preview their impact.
        </CardDescription>
      ) : (
        <div>
          {Object.entries(rulesByType).map(([type, typeRules]) => (
            <div key={type} className="mb-6">
              <CardTitle className="text-lg mb-4">
                {type.charAt(0).toUpperCase() + type.slice(1)} Rules
              </CardTitle>
              {typeRules.map(renderRuleCard)}
            </div>
          ))}
          
          {showActions && onApplyRules && (
            <CardFooter className="flex justify-end">
              <Button
                onClick={onApplyRules}
                className="gap-2"
              >
                <CheckCircle className="h-4 w-4" />
                Apply Rules
              </Button>
            </CardFooter>
          )}
        </div>
      )}
    </div>
  );
};

export default RulePreview; 