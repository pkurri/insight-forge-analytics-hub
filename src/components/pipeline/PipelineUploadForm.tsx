import React, { useState, useEffect } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2, UploadCloud, CheckCircle2, XCircle, FileUp, Globe, Upload, Database, AlertCircle, ArrowRight, ArrowLeft, Info, Sparkles, HardDrive, Filter } from 'lucide-react';
import { pipelineService, BusinessRule, ValidationResult } from '@/api/services/pipeline';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface StepProps {
  children: React.ReactNode;
  isActive: boolean;
  isCompleted: boolean;
  description: string;
  icon?: React.ReactNode;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  onClick?: () => void;
  disabled?: boolean;
}

const Step: React.FC<StepProps> = ({ 
  children, 
  isActive, 
  isCompleted, 
  description, 
  icon, 
  status, 
  onClick, 
  disabled = false 
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'processing':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
      default:
        return icon;
    }
  };

  return (
    <div 
      onClick={disabled ? undefined : onClick}
      className={`flex items-start gap-4 p-4 rounded-lg transition-all ${onClick && !disabled ? 'cursor-pointer hover:shadow-md' : ''} ${
        isActive ? 'bg-accent shadow-sm' : 
        isCompleted ? 'bg-muted/30' : 
        status === 'failed' ? 'bg-red-50' : 
        'bg-background'
      } border ${isActive ? 'border-primary' : 'border-border'} ${disabled ? 'opacity-60' : ''}`}
    >
      <div className={`flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-full transition-colors ${
        status === 'completed' ? 'bg-green-100 text-green-600' : 
        status === 'failed' ? 'bg-red-100 text-red-600' : 
        status === 'processing' ? 'bg-blue-100 text-blue-600' : 
        isActive ? 'bg-primary/10 text-primary' : 
        'bg-muted text-muted-foreground'
      }`}>
        {getStatusIcon()}
      </div>
      <div className="flex-grow">
        {children}
      </div>
    </div>
  );
};

type DataSource = 'local' | 'api' | 'database';
type FileType = 'csv' | 'json' | 'excel' | 'parquet';
type StepStatus = 'pending' | 'processing' | 'completed' | 'failed';

interface ApiConfig {
  url: string;
  method: 'GET' | 'POST';
  headers?: Record<string, string>;
  body?: string;
}

interface DatabaseConfig {
  type: 'postgresql' | 'mysql' | 'sqlserver' | 'oracle';
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  query: string;
}

interface PipelineUploadFormProps {
  onUploadComplete: (datasetId: string) => void;
}

const PipelineUploadForm: React.FC<PipelineUploadFormProps> = ({ onUploadComplete }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<FileType>('csv');
  const [name, setName] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [businessRules, setBusinessRules] = useState<BusinessRule[]>([]);
  const [rulesLoading, setRulesLoading] = useState(false);
  const [stageLoading, setStageLoading] = useState({
    validate: false,
    rules: false,
    transform: false,
    enrich: false,
    load: false
  } as const);
  interface PipelineStep {
  name: string;
  status: StepStatus;
  description: string;
  icon: React.ReactNode;
  details: string;
}

// Helper function to update step status safely with proper typing
const updateStepStatus = (steps: PipelineStep[], index: number, status: StepStatus): PipelineStep[] => {
  return steps.map((step, i) => i === index ? { ...step, status } : step);
}

const [pipelineSteps, setPipelineSteps] = useState<PipelineStep[]>([
    { 
      name: 'Upload', 
      status: 'pending',
      description: 'Upload and validate data file',
      icon: <UploadCloud className="h-5 w-5" />,
      details: 'Upload your data from a local file, API, or database connection'
    },
    { 
      name: 'Validate', 
      status: 'pending',
      description: 'Validate data structure and integrity',
      icon: <CheckCircle2 className="h-5 w-5" />,
      details: 'Verify data schema, types, and basic integrity checks'
    },
    { 
      name: 'Business Rules', 
      status: 'pending',
      description: 'Apply business rules and constraints',
      icon: <Filter className="h-5 w-5" />,
      details: 'Apply custom business rules and data quality constraints'
    },
    { 
      name: 'Transform', 
      status: 'pending',
      description: 'Apply data transformations',
      icon: <Sparkles className="h-5 w-5" />,
      details: 'Transform data structure and format for analysis'
    },
    { 
      name: 'Enrich', 
      status: 'pending',
      description: 'Add derived fields and enrichments',
      icon: <Info className="h-5 w-5" />,
      details: 'Add derived fields, external data, and enrich your dataset'
    },
    { 
      name: 'Load', 
      status: 'pending',
      description: 'Save processed data to destination',
      icon: <HardDrive className="h-5 w-5" />,
      details: 'Load processed data to your target destination'
    }
  ]);
  const [dataSource, setDataSource] = useState<DataSource>('local');
  const [apiConfig, setApiConfig] = useState<ApiConfig>({
    url: '',
    method: 'GET',
    headers: {},
    body: ''
  });
  const [dbConfig, setDbConfig] = useState<DatabaseConfig>({
    type: 'postgresql',
    host: '',
    port: 5432,
    database: '',
    username: '',
    password: '',
    query: ''
  });

  const { toast } = useToast();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      // Auto-detect file type from extension
      const extension = file.name.split('.').pop()?.toLowerCase();
      if (extension === 'csv') setFileType('csv');
      else if (extension === 'json') setFileType('json');
      else if (extension === 'xlsx' || extension === 'xls') setFileType('excel');
      else if (extension === 'parquet') setFileType('parquet');
    }
  };

  const handleApiConfigChange = (field: keyof ApiConfig, value: string) => {
    setApiConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleDbConfigChange = (field: keyof DatabaseConfig, value: string | number) => {
    setDbConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleUpload = async () => {
    if (!name) {
      setError('Please provide a name for the dataset');
      return;
    }

    if (dataSource === 'local' && !selectedFile) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let uploadData: any = {
        name,
        description,
        fileType
      };

      switch (dataSource) {
        case 'local':
          if (!selectedFile) {
            throw new Error('Please select a file');
          }
          uploadData.file = selectedFile;
          break;

        case 'api':
          if (!apiConfig.url) {
            throw new Error('Please provide an API URL');
          }
          uploadData.apiConfig = apiConfig;
          break;

        case 'database':
          if (!dbConfig.host || !dbConfig.database || !dbConfig.query) {
            throw new Error('Please provide all required database configuration');
          }
          uploadData.dbConfig = dbConfig;
          break;
      }

      const response = await pipelineService.uploadData(uploadData);
      
      if (response.success && response.data?.dataset_id) {
        setDatasetId(response.data.dataset_id);
        setCompletedSteps(prev => [...prev, 0]); // Mark upload step as completed
        setCurrentStep(1); // Move to validation step
        
        toast({
          title: 'Success',
          description: 'Data uploaded successfully. Proceeding to validation.'
        });
        
        // Auto-start validation
        await handleStartValidation();
      } else {
        throw new Error(response.error || 'Failed to upload data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      toast({
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to upload data',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleStartValidation = async (): Promise<void> => {
    if (!datasetId) {
      setError("No dataset ID available");
      return;
    }
    
    setStageLoading(prev => ({ ...prev, validate: true }));
    setError(null);
    
    // Update step status to processing
    setPipelineSteps(steps => updateStepStatus(steps, 1, 'processing'));

    try {
      const validationResponse = await pipelineService.validateData(datasetId);
      if (validationResponse.success && validationResponse.data) {
        setValidationResult(validationResponse.data);
        setCompletedSteps(prev => [...new Set([...prev, 1])]);
        setCurrentStep(2);
        // Update validation step to completed and set next step as active
        setPipelineSteps(steps => {
          let newSteps = [...steps];
          newSteps = updateStepStatus(newSteps, 1, 'completed');
          return updateStepStatus(newSteps, 2, 'pending');
        });
        
        toast({
          title: "Validation started",
          description: "Data validation has been initiated. You can now start applying business rules.",
        });
      } else {
        throw new Error(validationResponse.error || "Failed to start validation");
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : "Failed to start validation");
      setPipelineSteps(steps => updateStepStatus(steps, 1, 'failed'));
      toast({
        title: "Validation failed",
        description: error instanceof Error ? error.message : "Failed to start validation",
        variant: "destructive",
      });
    } finally {
      setStageLoading((prev) => ({ ...prev, validate: false }));
    }
  };

  const handleStartBusinessRules = async (): Promise<void> => {
    if (!datasetId) {
      setError("No dataset ID available");
      return;
    }
    
    setStageLoading(prev => ({ ...prev, rules: true }));
    setError(null);
    
    // Mark validation as completed if not already
    if (!completedSteps.includes(1)) {
      setCompletedSteps(prev => [...prev, 1]);
    }
    
    // Update step status to processing
    setPipelineSteps(steps => updateStepStatus(steps, 2, 'processing'));

    setRulesLoading(true);

    try {
      const rulesResponse = await pipelineService.applyBusinessRules(datasetId, businessRules);
      if (rulesResponse.success) {
        setCompletedSteps(prev => [...new Set([...prev, 2])]);
        setCurrentStep(3);
        // Update business rules step to completed and set next step as active
        setPipelineSteps(steps => {
          let newSteps = [...steps];
          newSteps = updateStepStatus(newSteps, 2, 'completed');
          return updateStepStatus(newSteps, 3, 'pending');
        });
        
        toast({
          title: "Business rules applied",
          description: "Business rules have been applied successfully. You can now start the transform step.",
        });
      } else {
        throw new Error(rulesResponse.error || "Failed to apply business rules");
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : "Failed to apply business rules");
      setPipelineSteps(steps => updateStepStatus(steps, 2, 'failed'));
      toast({
        title: "Business rules failed",
        description: error instanceof Error ? error.message : "Failed to apply business rules",
        variant: "destructive",
      });
    } finally {
      setRulesLoading(false);
    }
  };

  // Calculate overall progress percentage
  const calculateProgress = () => {
    const totalSteps = pipelineSteps.length;
    const completedSteps = pipelineSteps.filter(step => step.status === 'completed').length;
    return (completedSteps / totalSteps) * 100;
  };

  // Handle step click to navigate (if allowed)
  const handleStepClick = (index: number) => {
    // Only allow clicking on completed steps or the next step
    if (index <= Math.max(...completedSteps, currentStep)) {
      setCurrentStep(index);
    }
  };

  // Get appropriate card title based on current step
  const getCardTitle = () => {
    return pipelineSteps[currentStep]?.name || 'Data Pipeline';
  };

  // Get appropriate card description based on current step
  const getCardDescription = () => {
    return pipelineSteps[currentStep]?.details || '';
  };

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-xl font-semibold">Pipeline Progress</h2>
          <Badge className={calculateProgress() === 100 ? "bg-green-500 text-white" : ""} variant="outline">
            {Math.round(calculateProgress())}% Complete
          </Badge>
        </div>
        <Progress value={calculateProgress()} className="h-2" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1 space-y-3">
          {pipelineSteps.map((step, index) => (
            <Step
              key={step.name}
              isActive={index === currentStep}
              isCompleted={completedSteps.includes(index)}
              description={step.name}
              status={step.status}
              icon={step.icon}
              onClick={() => handleStepClick(index)}
              disabled={index > Math.max(...completedSteps, currentStep)}
            >
              <div className="flex items-center justify-between w-full">
                <div>
                  <div className="font-medium">{step.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {step.description}
                  </div>
                </div>
                {index === currentStep && (
                  <Badge variant="outline" className="ml-2">Current</Badge>
                )}
              </div>
            </Step>
          ))}
        </div>
      </div>

      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle>{getCardTitle()}</CardTitle>
          <CardDescription>{getCardDescription()}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="name" className="text-sm font-medium">
              Dataset Name
            </label>
            <Input
              id="name"
              placeholder="Enter a name for this dataset"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="description" className="text-sm font-medium">
              Description
            </label>
            <Textarea
              id="description"
              placeholder="Enter a description for this dataset"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Data Source</label>
            <Tabs value={dataSource} onValueChange={(value) => setDataSource(value as DataSource)}>
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="local">
                  <FileUp className="w-4 h-4 mr-2" />
                  Local File
                </TabsTrigger>
                <TabsTrigger value="api">
                  <Globe className="w-4 h-4 mr-2" />
                  API
                </TabsTrigger>
                <TabsTrigger value="database">
                  <Database className="w-4 h-4 mr-2" />
                  Database
                </TabsTrigger>
              </TabsList>

              <TabsContent value="local" className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">File Type</label>
                  <Select value={fileType} onValueChange={(value) => setFileType(value as FileType)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select file type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="csv">CSV</SelectItem>
                      <SelectItem value="json">JSON</SelectItem>
                      <SelectItem value="excel">Excel</SelectItem>
                      <SelectItem value="parquet">Parquet</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Select File</label>
                  <Input
                    type="file"
                    onChange={handleFileChange}
                    accept=".csv,.json,.xlsx,.xls,.parquet"
                  />
                </div>
              </TabsContent>

              <TabsContent value="api" className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">API URL</label>
                  <Input
                    value={apiConfig.url}
                    onChange={(e) => handleApiConfigChange('url', e.target.value)}
                    placeholder="https://api.example.com/data"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Method</label>
                  <Select
                    value={apiConfig.method}
                    onValueChange={(value) => handleApiConfigChange('method', value as 'GET' | 'POST')}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select method" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="GET">GET</SelectItem>
                      <SelectItem value="POST">POST</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Headers (JSON)</label>
                  <Textarea
                    value={JSON.stringify(apiConfig.headers, null, 2)}
                    onChange={(e) => {
                      try {
                        const headers = JSON.parse(e.target.value);
                        handleApiConfigChange('headers', headers);
                      } catch (err) {
                        // Invalid JSON, ignore
                      }
                    }}
                    placeholder='{"Authorization": "Bearer token"}'
                  />
                </div>

                {apiConfig.method === 'POST' && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Request Body (JSON)</label>
                    <Textarea
                      value={apiConfig.body}
                      onChange={(e) => handleApiConfigChange('body', e.target.value)}
                      placeholder='{"key": "value"}'
                    />
                  </div>
                )}
              </TabsContent>

              <TabsContent value="database" className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Database Type</label>
                  <Select
                    value={dbConfig.type}
                    onValueChange={(value) => handleDbConfigChange('type', value as DatabaseConfig['type'])}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select database type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="postgresql">PostgreSQL</SelectItem>
                      <SelectItem value="mysql">MySQL</SelectItem>
                      <SelectItem value="sqlserver">SQL Server</SelectItem>
                      <SelectItem value="oracle">Oracle</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Host</label>
                    <Input
                      value={dbConfig.host}
                      onChange={(e) => handleDbConfigChange('host', e.target.value)}
                      placeholder="localhost"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Port</label>
                    <Input
                      type="number"
                      value={dbConfig.port}
                      onChange={(e) => handleDbConfigChange('port', parseInt(e.target.value))}
                      placeholder="5432"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Database Name</label>
                  <Input
                    value={dbConfig.database}
                    onChange={(e) => handleDbConfigChange('database', e.target.value)}
                    placeholder="mydatabase"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Username</label>
                    <Input
                      value={dbConfig.username}
                      onChange={(e) => handleDbConfigChange('username', e.target.value)}
                      placeholder="user"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Password</label>
                    <Input
                      type="password"
                      value={dbConfig.password}
                      onChange={(e) => handleDbConfigChange('password', e.target.value)}
                      placeholder="password"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">SQL Query</label>
                  <Textarea
                    value={dbConfig.query}
                    onChange={(e) => handleDbConfigChange('query', e.target.value)}
                    placeholder="SELECT * FROM table"
                  />
                </div>
              </TabsContent>
            </Tabs>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

        </CardContent>
        <CardFooter className="flex justify-between items-center border-t pt-6">
          {currentStep > 0 && (
            <Button
              variant="outline"
              onClick={() => setCurrentStep(prev => prev - 1)}
              disabled={loading || rulesLoading || Object.values(stageLoading).some(val => val)}
              className="flex items-center"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
          )}
          {currentStep === 0 && <div></div>}
          <div className="flex items-center gap-2">
            {error && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="flex items-center text-destructive text-sm mr-4 cursor-help">
                      <AlertCircle className="h-4 w-4 mr-1" />
                      Error
                    </div>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-sm">
                    <p>{error}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
            <Button
              onClick={async () => {
                try {
                  if (currentStep === 0) {
                    await handleUpload();
                  } else if (currentStep === 1) {
                    await handleStartValidation();
                  } else if (currentStep === 2) {
                    await handleStartBusinessRules();
                  } else if (currentStep === 3) {
                    // Transform handler
                    setPipelineSteps(steps => updateStepStatus(steps, 3, 'processing'));
                    setTimeout(() => {
                      setPipelineSteps(steps => {
                        let newSteps = [...steps];
                        newSteps = updateStepStatus(newSteps, 3, 'completed');
                        return updateStepStatus(newSteps, 4, 'pending');
                      });
                      setCompletedSteps(prev => [...new Set([...prev, 3])]);
                      setCurrentStep(prev => prev + 1);
                      toast({
                        title: "Transform completed",
                        description: "Data transformation has been completed successfully."
                      });
                    }, 1500);
                  } else if (currentStep === 4) {
                    // Enrich handler
                    setPipelineSteps(steps => updateStepStatus(steps, 4, 'processing'));
                    setTimeout(() => {
                      setPipelineSteps(steps => {
                        let newSteps = [...steps];
                        newSteps = updateStepStatus(newSteps, 4, 'completed');
                        return updateStepStatus(newSteps, 5, 'pending');
                      });
                      setCompletedSteps(prev => [...new Set([...prev, 4])]);
                      setCurrentStep(prev => prev + 1);
                      toast({
                        title: "Enrichment completed",
                        description: "Data enrichment has been completed successfully."
                      });
                    }, 1500);
                  } else if (currentStep === 5) {
                    // Load handler
                    setPipelineSteps(steps => updateStepStatus(steps, 5, 'processing'));
                    setTimeout(() => {
                      setPipelineSteps(steps => updateStepStatus(steps, 5, 'completed'));
                      setCompletedSteps(prev => [...new Set([...prev, 5])]);
                      toast({
                        title: "Pipeline completed",
                        description: "All pipeline steps have been completed successfully."
                      });
                      onUploadComplete(datasetId || '');
                    }, 1500);
                  }
                } catch (error) {
                  console.error('Step error:', error);
                }
              }}
              disabled={loading || rulesLoading || Object.values(stageLoading).some(val => val)}
              className="flex items-center"
              variant={currentStep === pipelineSteps.length - 1 ? "default" : "default"}
            >
              {loading || rulesLoading || Object.values(stageLoading).some(val => val) ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : currentStep === pipelineSteps.length - 1 ? (
                <>
                  Finish
                  <CheckCircle2 className="ml-2 h-4 w-4" />
                </>
              ) : (
                <>
                  Next
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
};


export default PipelineUploadForm;
