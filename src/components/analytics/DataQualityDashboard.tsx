import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  FileCheck, 
  Sparkles, 
  ArrowDownToLine, 
  GitBranch 
} from 'lucide-react';
import { api } from '@/api/api';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';

interface ValidationResult {
  name: string;
  type: string;
  passed: boolean;
  message?: string;
  score?: number;
  threshold?: number;
}

interface ValidationSummary {
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  completeness_score?: number;
  consistency_score?: number;
  format_score?: number;
  overall_quality_score?: number;
}

interface CleaningOperation {
  operation: string;
  column?: string;
  count?: number;
  strategy?: string;
}

interface CleaningSummary {
  rows_before: number;
  rows_after: number;
  rows_removed: number;
  cells_changed: number;
  cells_changed_percent: number;
  operations: CleaningOperation[];
}

const DataQualityDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [validationData, setValidationData] = useState<any>(null);
  const [cleaningData, setCleaningData] = useState<any>(null);
  const { toast } = useToast();
  const [selectedDataset, setSelectedDataset] = useState('ds001');
  const [selectedOperations, setSelectedOperations] = useState([]);

  const loadQualityData = async () => {
    setLoading(true);
    try {
      const response = await api.analyticsService.getDataQuality(selectedDataset);
      if (response.success) {
        setValidationData(response.data.validation);
        setCleaningData(response.data.cleaning);
        toast({
          title: "Success",
          description: "Data quality information loaded",
        });
      } else {
        toast({
          title: "Error",
          description: response.error || "Failed to load data quality information",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error fetching data quality:", error);
      toast({
        title: "Error",
        description: "An error occurred while fetching data quality information",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCleanData = async () => {
    setLoading(true);
    try {
      const response = await api.analyticsService.cleanData(selectedDataset, {
        operations: selectedOperations
      });
      if (response.success) {
        setCleaningData(response.data);
        toast({
          title: "Success",
          description: "Data cleaning completed successfully",
        });
      } else {
        toast({
          title: "Error",
          description: response.error || "Failed to clean data",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error cleaning data:", error);
      toast({
        title: "Error",
        description: "An error occurred while cleaning data",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return 'bg-green-500';
    if (score >= 0.7) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getScoreText = (score: number) => {
    if (score >= 0.9) return 'text-green-700';
    if (score >= 0.7) return 'text-yellow-700';
    return 'text-red-700';
  };

  // Mock data for UI display when API is not yet connected
  const mockValidationSummary: ValidationSummary = {
    total_checks: 24,
    passed_checks: 19,
    failed_checks: 5,
    completeness_score: 0.92,
    consistency_score: 0.85,
    format_score: 0.78,
    overall_quality_score: 0.85
  };

  const mockValidationResults: ValidationResult[] = [
    { name: "Data Completeness", type: "completeness", passed: true, score: 0.92, threshold: 0.9 },
    { name: "Column existence: customer_id", type: "schema", passed: true },
    { name: "Email Format: email", type: "format", passed: false, message: "Column 'email' contains email values with invalid format", score: 0.82 },
    { name: "Duplicate Rows", type: "consistency", passed: true, score: 0.98 },
    { name: "Valid Age", type: "row_level", passed: false, message: "24 rows (2.4%) violate rule 'Valid Age'" }
  ];

  const mockCleaningSummary: CleaningSummary = {
    rows_before: 1000,
    rows_after: 985,
    rows_removed: 15,
    cells_changed: 78,
    cells_changed_percent: 1.56,
    operations: [
      { operation: "remove_duplicates", count: 12 },
      { operation: "fill_missing", column: "email", strategy: "mode", count: 23 },
      { operation: "clip_outliers", column: "age", count: 15 },
      { operation: "standardize_values", column: "status", count: 28 }
    ]
  };

  // Use mock data if actual data not available
  const validationSummary = validationData?.summary || mockValidationSummary;
  const validationResults = validationData?.checks || mockValidationResults;
  const cleaningSummary = cleaningData?.summary || mockCleaningSummary;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Data Quality</h2>
        <div className="space-x-2">
          <Button 
            onClick={loadQualityData} 
            disabled={loading}
            variant="outline"
          >
            <FileCheck className="mr-2 h-4 w-4" />
            Check Quality
          </Button>
          <Button 
            onClick={handleCleanData} 
            disabled={loading}
            variant="default"
          >
            <Sparkles className="mr-2 h-4 w-4" />
            Clean Data
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview">
        <TabsList className="mb-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="validation">Validation</TabsTrigger>
          <TabsTrigger value="cleaning">Cleaning</TabsTrigger>
          <TabsTrigger value="pipeline">Pipeline</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <Card>
              <CardHeader>
                <CardTitle>Overall Quality Score</CardTitle>
                <CardDescription>Combined score from all validation checks</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center space-y-4">
                  <div className="relative h-40 w-40 flex items-center justify-center">
                    <svg className="h-full w-full" viewBox="0 0 100 100">
                      <circle
                        className="text-gray-200"
                        strokeWidth="10"
                        stroke="currentColor"
                        fill="transparent"
                        r="40"
                        cx="50"
                        cy="50"
                      />
                      <circle
                        className={getScoreColor(validationSummary.overall_quality_score)}
                        strokeWidth="10"
                        strokeDasharray={`${validationSummary.overall_quality_score * 251.2} 251.2`}
                        strokeLinecap="round"
                        stroke="currentColor"
                        fill="transparent"
                        r="40"
                        cx="50"
                        cy="50"
                      />
                    </svg>
                    <div className="absolute text-3xl font-bold">
                      {Math.round(validationSummary.overall_quality_score * 100)}%
                    </div>
                  </div>
                  <div className={`text-lg ${getScoreText(validationSummary.overall_quality_score)} font-semibold`}>
                    {validationSummary.overall_quality_score >= 0.9 ? 'Excellent' : 
                     validationSummary.overall_quality_score >= 0.7 ? 'Good' : 'Needs Improvement'}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Validation Summary</CardTitle>
                <CardDescription>Results from all validation checks</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span>Passed Checks:</span>
                    <span className="font-bold text-green-600">
                      {validationSummary.passed_checks} / {validationSummary.total_checks}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Failed Checks:</span>
                    <span className="font-bold text-red-600">
                      {validationSummary.failed_checks}
                    </span>
                  </div>
                  <div className="pt-2">
                    <div className="flex justify-between items-center mb-1">
                      <span>Completeness:</span>
                      <span className="font-semibold">
                        {Math.round(validationSummary.completeness_score * 100)}%
                      </span>
                    </div>
                    <Progress value={validationSummary.completeness_score * 100} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span>Consistency:</span>
                      <span className="font-semibold">
                        {Math.round(validationSummary.consistency_score * 100)}%
                      </span>
                    </div>
                    <Progress value={validationSummary.consistency_score * 100} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span>Format:</span>
                      <span className="font-semibold">
                        {Math.round(validationSummary.format_score * 100)}%
                      </span>
                    </div>
                    <Progress value={validationSummary.format_score * 100} className="h-2" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Recent Validation Issues</CardTitle>
              <CardDescription>Top issues that need attention</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {validationResults
                  .filter(result => !result.passed)
                  .slice(0, 3)
                  .map((result, index) => (
                    <div key={index} className="flex items-start border-l-4 border-red-500 pl-4 py-2">
                      <AlertTriangle className="h-5 w-5 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="font-semibold">{result.name}</p>
                        <p className="text-sm text-gray-600">{result.message}</p>
                      </div>
                    </div>
                  ))}

                {validationResults.filter(result => !result.passed).length === 0 && (
                  <div className="flex items-start border-l-4 border-green-500 pl-4 py-2">
                    <CheckCircle2 className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                    <div>
                      <p className="font-semibold">All checks passed!</p>
                      <p className="text-sm text-gray-600">No validation issues detected.</p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="validation">
          <Card>
            <CardHeader>
              <CardTitle>Validation Results</CardTitle>
              <CardDescription>Detailed results from all validation checks</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Check</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {validationResults.map((result, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{result.name}</TableCell>
                      <TableCell>{result.type}</TableCell>
                      <TableCell>
                        {result.passed ? (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            <CheckCircle2 className="h-3 w-3 mr-1" /> Pass
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            <XCircle className="h-3 w-3 mr-1" /> Fail
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="max-w-md truncate">
                        {result.message || (
                          result.score !== undefined ? 
                            `Score: ${Math.round(result.score * 100)}%` :
                            "Check passed successfully"
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cleaning">
          <Card>
            <CardHeader>
              <CardTitle>Cleaning Summary</CardTitle>
              <CardDescription>Results from automated data cleaning</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-gray-100 rounded-lg p-4 text-center">
                  <p className="text-gray-500 text-sm">Rows Before</p>
                  <p className="text-2xl font-bold">{cleaningSummary.rows_before}</p>
                </div>
                <div className="bg-gray-100 rounded-lg p-4 text-center">
                  <p className="text-gray-500 text-sm">Rows After</p>
                  <p className="text-2xl font-bold">{cleaningSummary.rows_after}</p>
                </div>
                <div className="bg-gray-100 rounded-lg p-4 text-center">
                  <p className="text-gray-500 text-sm">Rows Removed</p>
                  <p className="text-2xl font-bold text-amber-600">{cleaningSummary.rows_removed}</p>
                </div>
              </div>

              <div className="mb-6">
                <h3 className="font-semibold mb-2">Data Changes</h3>
                <div className="flex items-center space-x-4">
                  <div className="flex-1">
                    <Progress value={cleaningSummary.cells_changed_percent} max={10} className="h-3" />
                  </div>
                  <div className="text-sm font-medium">
                    {cleaningSummary.cells_changed} cells changed ({cleaningSummary.cells_changed_percent.toFixed(2)}%)
                  </div>
                </div>
              </div>

              <h3 className="font-semibold mb-2">Cleaning Operations</h3>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Operation</TableHead>
                    <TableHead>Column</TableHead>
                    <TableHead>Strategy</TableHead>
                    <TableHead>Count</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cleaningSummary.operations.map((operation, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">
                        {operation.operation.replace(/_/g, ' ')}
                      </TableCell>
                      <TableCell>{operation.column || 'N/A'}</TableCell>
                      <TableCell>{operation.strategy || 'N/A'}</TableCell>
                      <TableCell>{operation.count || 'N/A'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pipeline">
          <Card>
            <CardHeader>
              <CardTitle>Data Pipeline</CardTitle>
              <CardDescription>Configure and run data processing pipelines</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-6">
                <h3 className="font-semibold mb-4">Available Pipeline Steps</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="border rounded-lg p-4 flex items-center space-x-3">
                    <div className="bg-blue-100 p-2 rounded-full">
                      <FileCheck className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <h4 className="font-medium">Data Profiling</h4>
                      <p className="text-sm text-gray-500">Analyze and summarize dataset characteristics</p>
                    </div>
                  </div>
                  
                  <div className="border rounded-lg p-4 flex items-center space-x-3">
                    <div className="bg-green-100 p-2 rounded-full">
                      <Sparkles className="h-5 w-5 text-green-600" />
                    </div>
                    <div>
                      <h4 className="font-medium">Data Cleaning</h4>
                      <p className="text-sm text-gray-500">Fix quality issues automatically</p>
                    </div>
                  </div>
                  
                  <div className="border rounded-lg p-4 flex items-center space-x-3">
                    <div className="bg-amber-100 p-2 rounded-full">
                      <AlertTriangle className="h-5 w-5 text-amber-600" />
                    </div>
                    <div>
                      <h4 className="font-medium">Anomaly Detection</h4>
                      <p className="text-sm text-gray-500">Find unusual patterns and outliers</p>
                    </div>
                  </div>
                  
                  <div className="border rounded-lg p-4 flex items-center space-x-3">
                    <div className="bg-purple-100 p-2 rounded-full">
                      <GitBranch className="h-5 w-5 text-purple-600" />
                    </div>
                    <div>
                      <h4 className="font-medium">Data Validation</h4>
                      <p className="text-sm text-gray-500">Check data against business rules</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-center mt-6">
                <Button className="w-full md:w-auto">
                  <ArrowDownToLine className="mr-2 h-4 w-4" />
                  Run Complete Pipeline
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DataQualityDashboard;
