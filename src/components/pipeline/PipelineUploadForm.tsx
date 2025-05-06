import React, { useState, useEffect } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, UploadCloud, CheckCircle2, XCircle, FileUp, Globe, Upload } from 'lucide-react';
import { pipelineService, BusinessRule, ValidationResult } from '@/api/services/pipeline';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface StepProps {
  children: React.ReactNode;
  isActive: boolean;
  isCompleted: boolean;
  description: string;
  icon?: React.ReactNode;
}

const Step: React.FC<StepProps> = ({ children, isActive, isCompleted, description, icon }) => {
  return (
    <div className={`flex items-start gap-4 p-4 rounded-lg ${isActive ? 'bg-accent' : ''}`}>
      <div className="flex-shrink-0">
        {icon}
      </div>
      <div className="flex-grow">
        {children}
      </div>
    </div>
  );
};

type DataSource = 'local' | 'api' | 'database';
type FileType = 'csv' | 'json' | 'excel' | 'parquet';

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
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [businessRules, setBusinessRules] = useState<BusinessRule[]>([]);
  const [rulesLoading, setRulesLoading] = useState(false);
  const [stageLoading, setStageLoading] = useState({
    validate: false,
    rules: false,
    transform: false,
    enrich: false,
    load: false
  });
  const [pipelineSteps, setPipelineSteps] = useState([
    { name: 'Upload', status: 'pending' },
    { name: 'Validate', status: 'pending' },
    { name: 'Business Rules', status: 'pending' },
    { name: 'Transform', status: 'pending' },
    { name: 'Enrich', status: 'pending' },
    { name: 'Load', status: 'pending' }
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
        toast({
          title: 'Success',
          description: 'Data uploaded successfully'
        });
        onUploadComplete(response.data.dataset_id);
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

    setStageLoading((prev) => ({ ...prev, validate: true }));
    setError(null);

    try {
      const validationResponse = await pipelineService.validateData(datasetId);
      if (validationResponse.success && validationResponse.data) {
        setValidationResult(validationResponse.data);
        setPipelineSteps((steps) => steps.map((step, index) => ({
          ...step,
          status: index === 1 ? "completed" : step.status
        })));
        
        toast({
          title: "Validation started",
          description: "Data validation has been initiated. You can now start applying business rules.",
        });
      } else {
        throw new Error(validationResponse.error || "Failed to start validation");
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : "Failed to start validation");
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

    setRulesLoading(true);
    setError(null);

    try {
      const rulesResponse = await pipelineService.applyBusinessRules(datasetId, businessRules);
      if (rulesResponse.success) {
        setPipelineSteps((steps) => steps.map((step, index) => ({
          ...step,
          status: index === 2 ? "completed" : step.status
        })));
        
        toast({
          title: "Business rules applied",
          description: "Business rules have been applied successfully. You can now start the transform step.",
        });
      } else {
        throw new Error(rulesResponse.error || "Failed to apply business rules");
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : "Failed to apply business rules");
      toast({
        title: "Business rules failed",
        description: error instanceof Error ? error.message : "Failed to apply business rules",
        variant: "destructive",
      });
    } finally {
      setRulesLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        {pipelineSteps.map((step, index) => (
          <Step
            key={step.name}
            isActive={index === currentStep}
            isCompleted={index < currentStep}
            description={step.name}
            icon={
              step.name === 'Upload' ? <UploadCloud className="h-4 w-4" /> :
              step.name === 'Validate' ? (
                step.status === 'completed' ? <CheckCircle2 className="h-4 w-4 text-green-500" /> :
                step.status === 'failed' ? <XCircle className="h-4 w-4 text-red-500" /> :
                <UploadCloud className="h-4 w-4" />
              ) : <UploadCloud className="h-4 w-4" />
            }
          >
            <div className="flex items-center gap-2">
              <div>
                <div className="font-medium">{step.name}</div>
                <div className="text-xs text-muted-foreground">
                  {step.name === 'Upload' ? 'Upload and validate data file' :
                   step.name === 'Validate' ? 'Validate data structure and integrity' :
                   step.name === 'Business Rules' ? 'Apply business rules and constraints' :
                   step.name === 'Transform' ? 'Apply data transformations' :
                   step.name === 'Enrich' ? 'Add derived fields and enrichments' :
                   'Save processed data to destination'}
                </div>
              </div>
              {stageLoading[step.name.toLowerCase() as keyof typeof stageLoading] && (
                <Loader2 className="h-4 w-4 animate-spin ml-2" />
              )}
            </div>
          </Step>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Upload Data</CardTitle>
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

          <div className="flex justify-end">
            <Button
              onClick={() => {
                if (currentStep === 0) {
                  handleUpload();
                } else if (currentStep === 1) {
                  handleStartValidation();
                } else if (currentStep === 2) {
                  handleStartBusinessRules();
                }
              }}
              disabled={loading || rulesLoading || stageLoading.validate || stageLoading.rules}
            >
              {loading || rulesLoading || stageLoading.validate || stageLoading.rules ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                'Next'
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PipelineUploadForm;
