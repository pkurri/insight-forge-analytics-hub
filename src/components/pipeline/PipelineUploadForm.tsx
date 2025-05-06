import React, { useState, useEffect } from 'react';
import { UploadCloud, AlertCircle, File, Table, Check, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { useToast } from "@/hooks/use-toast";
import { api } from '@/api/api';
import { Stepper, Step } from '@/components/ui/stepper';
import { Card } from '@/components/ui/card';
import { pipelineService } from '@/api/services/pipeline/pipelineService';
import type { BusinessRule } from '@/api/services/businessRules/businessRulesService';

type DataSource = 'local' | 'api' | 'database';
type PipelineStage = 'validate' | 'transform' | 'enrich' | 'load';
type PipelineStatus = 'running' | 'completed' | 'failed';

interface PipelineStepUI {
  label: string;
  description: string;
  icon?: React.ReactNode;
  status: 'pending' | 'running' | 'completed' | 'failed';
}

interface PipelineStatusData {
  current_stage: PipelineStage;
  progress: number;
  status: PipelineStatus;
  message?: string;
  stages: {
    name: string;
    status: PipelineStatus;
    start_time?: string;
    end_time?: string;
    error?: string;
    metadata?: any;
  }[];
  pipeline_metadata?: any;
}

interface RuleResult {
  id: string;
  name: string;
  severity: string;
  model_generated?: boolean;
  source?: string;
  violation_count: number;
  violations: any[];
}

interface RulesValidation {
  total_rules: number;
  passed_rules: number;
  failed_rules: number;
  total_violations: number;
  rule_results: RuleResult[];
}

const PipelineUploadForm: React.FC = () => {
  const [businessRules, setBusinessRules] = useState<BusinessRule[]>([]);
  const [rulesLoading, setRulesLoading] = useState(false);
  const [rulesError, setRulesError] = useState<string | null>(null);
  const [rulesValidation, setRulesValidation] = useState<RulesValidation | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dataSource, setDataSource] = useState<DataSource>('local');
  const [fileType, setFileType] = useState<string>('csv');
  const [apiEndpoint, setApiEndpoint] = useState<string>('');
  const [dbConnection, setDbConnection] = useState<string>('');
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [stageLoading, setStageLoading] = useState<Record<PipelineStage, boolean>>({
    validate: false,
    transform: false,
    enrich: false,
    load: false
  });
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();
  const [isOverrideActive, setIsOverrideActive] = useState(false);
  const [pipelineSteps, setPipelineSteps] = useState<PipelineStepUI[]>([]);

  const defaultPipelineSteps: PipelineStepUI[] = [
    { 
      label: "Upload", 
      description: "Upload and validate data file", 
      icon: <UploadCloud className="h-4 w-4" />,
      status: "pending"
    },
    { 
      label: "Data Validation", 
      description: "Validate data structure and integrity", 
      icon: <AlertCircle className="h-4 w-4" />,
      status: "pending"
    },
    { 
      label: "Business Rules", 
      description: "Apply business rules and constraints", 
      icon: <Check className="h-4 w-4" />,
      status: "pending"
    },
    { 
      label: "Transform", 
      description: "Apply data transformations", 
      icon: <File className="h-4 w-4" />,
      status: "pending"
    },
    { 
      label: "Enrich", 
      description: "Add derived fields and enrichments", 
      icon: <Table className="h-4 w-4" />,
      status: "pending"
    },
    { 
      label: "Load", 
      description: "Save processed data to destination", 
      icon: <Check className="h-4 w-4" />,
      status: "pending"
    }
  ];

  useEffect(() => {
    setPipelineSteps(defaultPipelineSteps);
  }, []);

  const validateInputs = (): boolean => {
    if (dataSource === "local" && !selectedFile) {
      setError("Please select a file to upload");
      return false;
    }

    if (dataSource === "api" && !apiEndpoint) {
      setError("Please enter an API endpoint");
      return false;
    }

    if (dataSource === "database" && !dbConnection) {
      setError("Please enter database connection details");
      return false;
    }

    setError(null);
    return true;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setSelectedFile(file);
      
      // Auto-detect file type from extension
      const extension = file.name.split('.').pop()?.toLowerCase();
      if (extension) {
        if (['csv', 'xlsx', 'xls', 'json', 'parquet', 'avro'].includes(extension)) {
          setFileType(extension);
        }
      }
    }
  };

  const handleUpload = async (): Promise<void> => {
    if (!validateInputs()) {
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      let formData = new FormData();

      if (dataSource === 'local' && selectedFile) {
        formData.append('file', selectedFile);
        formData.append('fileType', fileType);
      } else if (dataSource === 'api') {
        formData.append('apiEndpoint', apiEndpoint);
      } else if (dataSource === 'database') {
        formData.append('dbConnection', dbConnection);
      }

      formData.append('dataSource', dataSource);

      const onUploadProgress = (progressEvent: { loaded: number; total: number }) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(percentCompleted);
      };

      const response = await pipelineService.uploadData(formData, { onUploadProgress });

      if (response.success && response.data) {
        setIsUploading(false);
        setIsProcessing(true);
        setError(null);
        setDatasetId(response.data.id);
        setCurrentStep(1);
        setUploadProgress(100);

        // Update step status
        setPipelineSteps(steps => steps.map((step, index) => ({
          ...step,
          status: index === 0 ? "completed" : step.status
        })));

        toast({
          title: "Upload successful",
          description: "Data uploaded successfully. Starting validation...",
        });

        // Start data validation
        try {
          const validationResponse = await pipelineService.validateData(response.data.id);
          if (validationResponse.success) {
            setPipelineSteps(steps => steps.map((step, index) => ({
              ...step,
              status: index === 1 ? "completed" : step.status
            })));
            
            // Fetch and apply business rules
            setRulesLoading(true);
            setRulesError(null);
            try {
              const rulesResponse = await api.businessRules.getBusinessRules(response.data.id);
              if (rulesResponse.success && rulesResponse.data) {
                setBusinessRules(rulesResponse.data);
                const businessRulesResponse = await pipelineService.applyBusinessRules(response.data.id);
                if (businessRulesResponse.success && businessRulesResponse.data) {
                  setRulesValidation(businessRulesResponse.data);
                  setPipelineSteps(steps => steps.map((step, index) => ({
                    ...step,
                    status: index === 2 ? "completed" : step.status
                  })));
                  toast({
                    title: "Business rules applied",
                    description: `Validation complete: ${businessRulesResponse.data.failed_rules || 0} failed, ${businessRulesResponse.data.passed_rules || 0} passed.`
                  });
                } else {
                  setRulesError(businessRulesResponse.error || "Failed to apply business rules");
                }
              } else {
                setRulesError(rulesResponse.error || "Could not fetch business rules.");
              }
            } catch (err: any) {
              setRulesError(err?.message || "Could not fetch/apply business rules.");
              toast({ title: "Error", description: err?.message || "Could not fetch/apply business rules.", variant: "destructive" });
            } finally {
              setRulesLoading(false);
            }
          } else {
            setError(validationResponse.error || "Data validation failed");
          }
        } catch (err: any) {
          setError(err?.message || "Error during data validation");
        }

        // Start monitoring the pipeline progress
        await monitorPipelineProgress(response.data.id);
      }
    } catch (err: any) {
      setError(err?.message || "Upload failed");
      setIsUploading(false);
    }
  };

  const monitorPipelineProgress = async (pipelineId: string): Promise<() => void> => {
    let isRunning = true;
    let intervalId: ReturnType<typeof setInterval>;

    const checkStatus = async () => {
      try {
        const response = await pipelineService.getPipelineStatus(pipelineId);
        
        if (response.success && response.data) {
          const { current_stage, progress, status, error, stages } = response.data;
          
          // Update loading state for the current stage
          setStageLoading(prev => ({
            ...prev,
            [current_stage]: status === 'running'
          }));
          
          setUploadProgress(progress);
          
          // Update current step based on stage
          switch (current_stage) {
            case 'validate':
              setCurrentStep(1);
              break;
            case 'transform':
              setCurrentStep(3);
              break;
            case 'enrich':
              setCurrentStep(4);
              break;
            case 'load':
              setCurrentStep(5);
              break;
            default:
              setCurrentStep(0);
          }

          // Check for OpenEvals evaluations
          if (stages) {
            for (const stage of stages) {
              if (stage.status === 'completed' && stage.metadata?.evaluations) {
                const evaluations = await pipelineService.getPipelineStepEvaluations(pipelineId, stage.name);
                if (evaluations.success && evaluations.data) {
                  toast({
                    title: `${stage.name} evaluations complete`,
                    description: `Quality score: ${evaluations.data.quality_score || 'N/A'}`
                  });
                }
              }
            }
          }

          if (status === 'completed') {
            isRunning = false;
            clearInterval(intervalId);
            setIsProcessing(false);
            toast({
              title: "Pipeline completed",
              description: "All stages have been processed successfully",
            });
          } else if (status === 'failed') {
            isRunning = false;
            clearInterval(intervalId);
            setIsProcessing(false);
            setError(error || "Pipeline failed");
            toast({
              title: "Pipeline failed",
              description: error || "An error occurred during pipeline execution",
              variant: "destructive",
            });
          }
        }
      } catch (err: any) {
        isRunning = false;
        clearInterval(intervalId);
        setIsProcessing(false);
        setError(err.message || "Error monitoring pipeline progress");
        toast({
          title: "Monitoring error",
          description: err.message || "Error monitoring pipeline progress",
          variant: "destructive",
        });
      }
    };

    // Initial check
    await checkStatus();

    // Set up interval for subsequent checks
    intervalId = setInterval(checkStatus, 5000);

    // Cleanup function
    const cleanup = () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };

    return cleanup;
  };

  return (
    <Card className="w-full">
      <div className="p-6">
        <h2 className="text-2xl font-bold mb-4">Data Pipeline</h2>
        
        <Stepper
          currentStep={currentStep}
          orientation="horizontal"
          error={error || undefined}
        >
          {pipelineSteps.map((step, index) => (
            <Step
              key={step.label}
              isActive={index === currentStep}
              isCompleted={index < currentStep}
              description={step.description}
              icon={step.icon}
            >
              <div className="flex items-center gap-2">
                {step.icon}
                <div>
                  <div className="font-medium">{step.label}</div>
                  <div className="text-xs text-muted-foreground">{step.description}</div>
                </div>
                {stageLoading[step.label.toLowerCase() as PipelineStage] && (
                  <Loader2 className="h-4 w-4 animate-spin ml-2" />
                )}
              </div>
            </Step>
          ))}
        </Stepper>
        
        <div className="grid gap-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Data Source</label>
              <Select 
                value={dataSource} 
                onValueChange={(value) => setDataSource(value as DataSource)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="local">Local File</SelectItem>
                  <SelectItem value="api">API</SelectItem>
                  <SelectItem value="database">Database</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {dataSource === 'local' && (
              <>
                <div className="space-y-2">
                  <label className="text-sm font-medium">File Type</label>
                  <Select value={fileType} onValueChange={setFileType}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select file type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="csv">CSV</SelectItem>
                      <SelectItem value="xlsx">Excel</SelectItem>
                      <SelectItem value="json">JSON</SelectItem>
                      <SelectItem value="parquet">Parquet</SelectItem>
                      <SelectItem value="avro">Avro</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium">Select File</label>
                  <Input 
                    type="file" 
                    onChange={handleFileChange}
                    accept=".csv,.xlsx,.xls,.json,.parquet,.avro"
                  />
                  {selectedFile && (
                    <div className="text-xs text-muted-foreground">
                      Selected: {selectedFile.name} ({Math.round(selectedFile.size / 1024)} KB)
                    </div>
                  )}
                </div>
              </>
            )}
            
            {dataSource === 'api' && (
              <div className="space-y-2 col-span-2">
                <label className="text-sm font-medium">API Endpoint</label>
                <Input 
                  type="text" 
                  placeholder="https://api.example.com/data" 
                  value={apiEndpoint}
                  onChange={(e) => setApiEndpoint(e.target.value)}
                />
              </div>
            )}
            
            {dataSource === 'database' && (
              <div className="space-y-2 col-span-2">
                <label className="text-sm font-medium">Database Connection</label>
                <Input 
                  type="text" 
                  placeholder="postgresql://user:password@localhost:5432/db" 
                  value={dbConnection}
                  onChange={(e) => setDbConnection(e.target.value)}
                />
              </div>
            )}
          </div>
          
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          <div className="flex justify-end">
            <Button 
              onClick={handleUpload} 
              disabled={isUploading || isProcessing}
              className="w-40"
            >
              {(isUploading || isProcessing) ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {isUploading ? 'Uploading...' : 'Processing...'}
                </>
              ) : (
                <>
                  <UploadCloud className="mr-2 h-4 w-4" />
                  Upload Data
                </>
              )}
            </Button>
            {(isUploading || isProcessing) && (
              <Progress value={uploadProgress} className="h-2" />
            )}
          </div>

          {/* Business Rules Validation Results */}
          {rulesLoading && (
            <div className="text-sm text-muted-foreground">Fetching and applying business rules...</div>
          )}
          <Button
            variant="outline"
            size="sm"
            className="mt-2"
            disabled={rulesLoading || !datasetId}
            onClick={async () => {
              if (!datasetId) return;
              setRulesLoading(true);
              setRulesError(null);
              try {
                const rulesResp = await api.businessRules.getBusinessRules(datasetId);
                if (rulesResp.success && rulesResp.data) {
                  setBusinessRules(rulesResp.data);
                  const validationResp = await pipelineService.applyBusinessRules(datasetId);
                  if (validationResp.success && validationResp.data) {
                    setRulesValidation(validationResp.data);
                    toast({
                      title: "Business rules re-applied",
                      description: `Validation complete: ${validationResp.data.failed_rules || 0} failed, ${validationResp.data.passed_rules || 0} passed.`
                    });
                  } else {
                    setRulesError(validationResp.error || "Failed to apply business rules");
                  }
                } else {
                  setRulesError(rulesResp.error || "Could not fetch business rules.");
                }
              } catch (err: any) {
                setRulesError(err?.message || "Could not fetch/apply business rules.");
                toast({ title: "Error", description: err?.message || "Could not fetch/apply business rules.", variant: "destructive" });
              } finally {
                setRulesLoading(false);
              }
            }}
          >
            Refresh Business Rules
          </Button>
          {rulesError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{rulesError}</AlertDescription>
            </Alert>
          )}
          {rulesValidation && (
            <div className="border rounded p-4 mt-4">
              <div className="font-semibold mb-2">Business Rules Validation Summary</div>
              <div className="text-sm mb-1">Total Rules: {rulesValidation.total_rules}</div>
              <div className="text-sm mb-1 text-green-700">Passed: {rulesValidation.passed_rules}</div>
              <div className="text-sm mb-1 text-red-700">Failed: {rulesValidation.failed_rules}</div>
              <div className="text-sm mb-1">Total Violations: {rulesValidation.total_violations}</div>
              {rulesValidation.rule_results && Array.isArray(rulesValidation.rule_results) && (
                <div className="mt-2">
                  <div className="font-medium">Rule Details:</div>
                  <ul className="list-disc ml-6">
                    {rulesValidation.rule_results.map((r: RuleResult, idx: number) => (
                      <li key={idx} className={r.violation_count > 0 ? 'text-red-700' : 'text-green-700'}>
                        <span className="font-semibold">{r.name}</span> ({r.severity})
                        {r.model_generated && <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">AI</span>}
                        {r.source && <span className="ml-2 text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded capitalize">{r.source.replace('_', ' ')}</span>}
                        : {r.violation_count} violation(s)
                        {r.violation_count > 0 && r.violations && (
                          <ul className="list-disc ml-6 text-xs">
                            {r.violations.slice(0, 5).map((v: any, vidx: number) => (
                              <li key={vidx}>{JSON.stringify(v)}</li>
                            ))}
                            {r.violations.length > 5 && <li>...and {r.violations.length - 5} more</li>}
                          </ul>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

export default PipelineUploadForm;
