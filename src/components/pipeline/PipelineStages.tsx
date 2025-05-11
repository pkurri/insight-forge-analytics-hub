import React, { useState } from 'react';
import { 
  Sparkles, HardDrive, Filter, ChevronDown, ChevronUp,
  Database, ClipboardCheck, Wand2, BarChart3
} from 'lucide-react';
import { cn } from '@/utils/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';



interface StageProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  details?: string;
  sampleData?: Record<string, unknown>;
  expanded?: boolean;
}

const Stage: React.FC<StageProps> = ({ 
  icon, 
  title, 
  description, 
  details,
  sampleData,
  expanded = false
}) => {
  const [isExpanded, setIsExpanded] = useState(expanded);
  




  return (
    <Collapsible
      open={isExpanded}
      onOpenChange={setIsExpanded}
      className="rounded-lg border border-blue-200 transition-all mb-4 overflow-hidden shadow-sm hover:shadow-md bg-white hover:bg-blue-50/30"
    >
      <div 
        className="flex items-center p-4 cursor-pointer transition-colors duration-200 hover:bg-blue-50/50"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className={cn(
          "flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-full bg-white shadow-sm border border-blue-300 text-blue-600 transition-transform duration-300",
          isExpanded && "transform scale-110 bg-blue-50"
        )}>
          {icon}
        </div>
        <div className="ml-4 flex-1">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-lg">{title}</h3>
            </div>
            <div className="flex items-center gap-2">
              <CollapsibleTrigger asChild onClick={(e) => e.stopPropagation()}>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </Button>
              </CollapsibleTrigger>
            </div>
          </div>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
      <CollapsibleContent>
        <div className="p-4 bg-white/80 border-t animate-fadeIn">
          <div className="text-sm space-y-3">
            <h4 className="font-medium text-primary">Step Details</h4>
            <p className="text-muted-foreground">{details || "This step is part of the data processing pipeline."}</p>
            
            {/* Sample Data Visualization */}
            {sampleData && (
              <div className="mt-3 pt-3 border-t animate-slide-up">
                <h5 className="font-medium text-sm mb-2">Sample Data</h5>
                <div className="bg-slate-50 p-2 rounded border border-blue-100 text-xs font-mono overflow-x-auto shadow-inner">
                  {typeof sampleData === 'object' ? (
                    <pre>{JSON.stringify(sampleData, null, 2)}</pre>
                  ) : (
                    <div>{String(sampleData)}</div>
                  )}
                </div>
              </div>
            )}
            

          </div>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
};

interface StageDefinition {
  icon: React.ReactNode;
  title: string;
  description: string;
  details?: string;
  sampleData?: Record<string, unknown>;
}

interface PipelineStagesProps {
  customStages?: StageDefinition[];
  expandedStage?: number;
}

const PipelineStages: React.FC<PipelineStagesProps> = ({ 
  customStages,
  expandedStage = -1
}) => {
  
  // Sample data for each pipeline stage
  const sampleUploadData = {
    filename: "sales_data_2024.csv",
    size: "1.2MB",
    rows: 5000,
    columns: 12,
    preview: [
      { id: 1, product: "Widget A", sales: 1200, region: "North" },
      { id: 2, product: "Widget B", sales: 950, region: "South" }
    ]
  };

  const sampleValidateData = {
    schema_validation: "PASSED",
    data_types: {
      id: "integer",
      product: "string",
      sales: "number",
      region: "string"
    },
    missing_values: 12,
    duplicates: 0
  };

  const sampleBusinessRulesData: Record<string, unknown> = {
    rules: [
      { rule: "sales >= 0", passed: true },
      { rule: "region in ['North', 'South', 'East', 'West']", passed: true },
      { rule: "product != null", passed: true }
    ]
  };

  const sampleTransformData = {
    operations: [
      "Normalized region names",
      "Converted sales to USD",
      "Added timestamp column"
    ],
    rows_affected: 4850
  };

  const sampleEnrichData = {
    derived_fields: [
      "sales_category",
      "performance_score",
      "growth_rate"
    ],
    external_data: "Market trends from API"
  };

  const sampleLoadData = {
    destination: "analytics_db",
    tables: ["sales_fact", "product_dim", "region_dim"],
    status: "SUCCESS",
    rows_loaded: 4998
  };

  // Enhanced default pipeline stages with better icons and descriptions
  const defaultStages: StageDefinition[] = [
    {
      icon: <Database className="h-5 w-5 text-blue-600" />,
      title: "Upload",
      description: "Upload data from various sources",
      details: "This step represents data ingestion into the pipeline. In a real implementation, this would handle data uploads from local files, APIs, or database connections. Supported formats would include CSV, JSON, Excel, and SQL databases.",
      sampleData: sampleUploadData
    },
    {
      icon: <ClipboardCheck className="h-5 w-5 text-emerald-600" />,
      title: "Validate",
      description: "Ensure data meets schema requirements",
      details: "This step represents data validation to ensure datasets meet required schema and quality standards. In a real implementation, this would check data types, required fields, value ranges, and perform basic quality assessments.",
      sampleData: sampleValidateData
    },
    {
      icon: <Filter className="h-5 w-5 text-amber-600" />,
      title: "Business Rules",
      description: "Apply business logic and validation",
      details: "This step represents applying business rules to transform raw data into business-ready information. In a real implementation, this would apply domain-specific logic, validation rules, and conditional transformations.",
      sampleData: sampleBusinessRulesData
    },
    {
      icon: <Wand2 className="h-5 w-5 text-purple-600" />,
      title: "Transform",
      description: "Clean and transform data",
      details: "This step represents data transformation processes. In a real implementation, this would handle cleaning, normalizing, and restructuring data, including handling missing values, removing duplicates, and standardizing formats.",
      sampleData: sampleTransformData
    },
    {
      icon: <Sparkles className="h-5 w-5 text-yellow-600" />,
      title: "Enrich",
      description: "Add derived fields and insights",
      details: "This step represents data enrichment processes. In a real implementation, this would add value to datasets by incorporating derived fields, calculated metrics, external data sources, and AI-powered enhancements.",
      sampleData: sampleEnrichData
    },
    {
      icon: <HardDrive className="h-5 w-5 text-indigo-600" />,
      title: "Load",
      description: "Save processed data to destination",
      details: "This step represents the final data loading process. In a real implementation, this would load processed data into target destinations such as data warehouses, analytics databases, or visualization tools.",
      sampleData: sampleLoadData
    }
  ];
  
  const stages = customStages || defaultStages;

  return (
    <Card className="shadow-md border-muted overflow-hidden hover:shadow-lg transition-shadow duration-300">
      <CardHeader className="pb-3 bg-gradient-to-r from-blue-50 to-blue-100 border-b">
        <div className="flex items-center">
          <div>
            <CardTitle className="text-xl flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              Pipeline Workflow
            </CardTitle>
            <CardDescription className="mt-1">
              Visual representation of the data processing pipeline flow
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-4">
        <div className="space-y-1 animate-slide-up">
          {stages.map((stage, idx) => (
            <Stage 
              key={idx} 
              icon={stage.icon} 
              title={stage.title} 
              description={stage.description} 
              details={stage.details}
              sampleData={stage.sampleData}
              expanded={idx === expandedStage}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default PipelineStages;
