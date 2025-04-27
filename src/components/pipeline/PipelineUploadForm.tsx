
import React, { useState } from 'react';
import { UploadCloud, AlertCircle, File, Table, Check, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { useToast } from "@/hooks/use-toast";
import { pipelineService } from '@/api/services/pipeline/pipelineService';
import { pythonApi } from '@/api/pythonIntegration';
import { Stepper } from '@/components/ui/stepper';
import { Card } from '@/components/ui/card';

interface PipelineResponse {
  success: boolean;
  data?: {
    id: string;
  };
  error?: string;
}

interface PipelineStep {
  label: string;
  description: string;
  icon?: React.ReactNode;
}

interface PipelineStatus {
  current_stage: 'validate' | 'transform' | 'enrich' | 'load';
  progress: number;
  status: 'running' | 'completed' | 'failed';
}

const PipelineUploadForm: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dataSource, setDataSource] = useState<'local' | 'api' | 'database'>('local');
  const [fileType, setFileType] = useState<string>('csv');
  const [apiEndpoint, setApiEndpoint] = useState<string>('');
  const [dbConnection, setDbConnection] = useState<string>('');
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const { toast } = useToast();

  const pipelineSteps: PipelineStep[] = [
    { label: "Upload", description: "Upload data file", icon: <UploadCloud className="h-4 w-4" /> },
    { label: "Validate", description: "Validate data integrity", icon: <AlertCircle className="h-4 w-4" /> },
    { label: "Business Rules", description: "Apply business rules", icon: <Check className="h-4 w-4" /> },
    { label: "Transform", description: "Apply transformations", icon: <File className="h-4 w-4" /> },
    { label: "Enrich", description: "Add derived fields", icon: <Table className="h-4 w-4" /> },
    { label: "Load", description: "Save processed data", icon: <Check className="h-4 w-4" /> }
  ];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async (): Promise<void> => {
    if (dataSource === "local" && !selectedFile) {
      toast({
        title: "No file selected",
        description: "Please select a file to upload",
        variant: "destructive",
      });
      return;
    }

    if (dataSource === "api" && !apiEndpoint) {
      toast({
        title: "No API endpoint",
        description: "Please enter an API endpoint",
        variant: "destructive",
      });
      return;
    }

    if (dataSource === "database" && !dbConnection) {
      toast({
        title: "No database connection",
        description: "Please select a database connection",
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    
    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 200);
    
    try {
      let response;
      
      const formData = new FormData();
      
      if (dataSource === "local" && selectedFile) {
        formData.append('file', selectedFile);
        formData.append('file_type', fileType);
        formData.append('clean_data', 'true');
        formData.append('validate_data', 'true');
      } else if (dataSource === "api") {
        formData.append('api_endpoint', apiEndpoint);
        formData.append('output_format', fileType);
      } else if (dataSource === "database") {
        formData.append('connection_id', dbConnection);
        formData.append('output_format', fileType);
      } else {
        throw new Error("Invalid data source");
      }
      
      response = await pipelineService.uploadData(formData);
      
      clearInterval(progressInterval);
      
      if (response.success && response.data) {
        setDatasetId(response.data.id);
        setCurrentStep(1); // Move to validation step
        setUploadProgress(100);
        
        toast({
          title: "Upload successful",
          description: "Data uploaded successfully. Starting pipeline processing...",
        });

        // Start monitoring pipeline progress
        setIsProcessing(true);
        await monitorPipelineProgress(response.data.id);
      } else {
        throw new Error(response.error || "Upload failed");
      }
    } catch (error) {
      clearInterval(progressInterval);
      console.error("Upload error:", error);
      
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "Failed to upload data",
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
    }
  };

  const monitorPipelineProgress = async (pipelineId: string): Promise<void> => {
    try {
      let isComplete = false;
      while (!isComplete) {
        const status = await pipelineService.getPipelineStatus(pipelineId);
        
        if (status.success && status.data) {
          const { current_stage, progress, status: pipelineStatus } = status.data as PipelineStatus;
          
          // Update UI based on pipeline status
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
          }

          if (pipelineStatus === 'completed') {
            isComplete = true;
            setIsProcessing(false);
            toast({
              title: "Pipeline completed",
              description: "Data processing completed successfully",
            });
          } else if (pipelineStatus === 'failed') {
            throw new Error("Pipeline processing failed");
          }
        }

        // Wait before next status check
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    } catch (error) {
      setIsProcessing(false);
      toast({
        title: "Pipeline failed",
        description: error instanceof Error ? error.message : "Failed to process data",
        variant: "destructive",
      });
    }
  };
  
  const proceedThroughPipeline = async () => {
    if (!datasetId) return;
    
    setIsProcessing(true);
    
    try {
      // Execute each pipeline step in sequence
      if (currentStep === 1) {
        // Validate step
        toast({
          title: "Processing",
          description: "Validating data quality...",
        });
        
        const validationResponse = await pythonApi.validateDataInPipeline(datasetId);
        
        if (!validationResponse.success) {
          throw new Error(validationResponse.error || "Validation failed");
        }
        
        toast({
          title: "Validation complete",
          description: `Passed ${validationResponse.data.validation_results.passed_rules} out of ${validationResponse.data.validation_results.total_rules} validation rules.`,
        });
        
        // Move to business rules step after validation
        setCurrentStep(2);
      } else if (currentStep === 2) {
        // Business Rules step
        toast({
          title: "Processing",
          description: "Applying business rules...",
        });
        
        const businessRulesResponse = await pythonApi.validateWithBusinessRules(datasetId);
        
        if (!businessRulesResponse.success) {
          throw new Error(businessRulesResponse.error || "Business rules validation failed");
        }
        
        const { validation_summary } = businessRulesResponse.data;
        
        toast({
          title: "Business rules validation complete",
          description: `Passed ${validation_summary.passed_rules} out of ${validation_summary.total_rules} business rules with ${validation_summary.total_violations} violations.`,
        });
        
        setCurrentStep(3);
      } else if (currentStep === 3) {
        // Transform step
        toast({
          title: "Processing",
          description: "Applying data transformations...",
        });
        
        const transformResponse = await pythonApi.transformDataInPipeline(datasetId);
        
        if (!transformResponse.success) {
          throw new Error(transformResponse.error || "Transformation failed");
        }
        
        toast({
          title: "Transformation complete",
          description: `Applied ${transformResponse.data.transformation_results.transformations_applied.length} transformations and added ${transformResponse.data.transformation_results.new_columns_added.length} new columns.`,
        });
        
        setCurrentStep(4);
      } else if (currentStep === 4) {
        // Enrich step
        toast({
          title: "Processing",
          description: "Enriching data with additional insights...",
        });
        
        const enrichResponse = await pythonApi.enrichDataInPipeline(datasetId);
        
        if (!enrichResponse.success) {
          throw new Error(enrichResponse.error || "Enrichment failed");
        }
        
        toast({
          title: "Enrichment complete",
          description: `Applied ${enrichResponse.data.enrichment_results.enrichments_applied.length} enrichments and added ${enrichResponse.data.enrichment_results.new_columns_added.length} new fields.`,
        });
        
        setCurrentStep(5);
      } else if (currentStep === 5) {
        // Load step
        toast({
          title: "Processing",
          description: "Loading processed data to destination...",
        });
        
        const loadResponse = await pythonApi.loadDataInPipeline(datasetId, "datawarehouse", {
          mode: "append"
        });
        
        if (!loadResponse.success) {
          throw new Error(loadResponse.error || "Loading failed");
        }
        
        toast({
          title: "Pipeline complete",
          description: `Successfully processed and loaded ${loadResponse.data.loading_results.rows_loaded} rows with ${loadResponse.data.loading_results.columns_loaded} columns.`,
        });
        
        // Reset form after pipeline completion
        setTimeout(() => {
          setSelectedFile(null);
          setDatasetId(null);
          setCurrentStep(0);
          setUploadProgress(0);
          setApiEndpoint("");
          setDbConnection("");
        }, 5000);
      }
    } catch (error) {
      toast({
        title: "Process failed",
        description: error instanceof Error ? error.message : "An unexpected error occurred during processing",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const supportedFormats = {
    csv: "Comma Separated Values (.csv)",
    json: "JSON (.json)",
    excel: "Excel Spreadsheet (.xlsx, .xls)",
    pdf: "PDF Document (.pdf)"
  };
  
  const renderDataSourceFields = () => {
    switch (dataSource) {
      case "local":
        return (
          <div 
            className={`border-2 border-dashed rounded-lg p-8 text-center ${
              selectedFile ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/20' : 'border-gray-300 dark:border-gray-700'
            }`}
            onClick={() => document.getElementById('file-upload')?.click()}
          >
            <div className="flex flex-col items-center">
              {selectedFile ? (
                <>
                  <File className="h-10 w-10 text-blue-500 mb-2" />
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                  <Button 
                    variant="outline" 
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedFile(null);
                    }} 
                    className="mt-3"
                    size="sm"
                  >
                    Remove
                  </Button>
                </>
              ) : (
                <>
                  <UploadCloud className="h-10 w-10 text-gray-400 mb-2" />
                  <p className="text-lg font-medium">Drag and drop your file here</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 mb-4">
                    or click to browse files
                  </p>
                </>
              )}
              <Input
                type="file"
                id="file-upload"
                className="opacity-0 absolute"
                onChange={handleFileChange}
                onClick={(e) => e.stopPropagation()}
              />
            </div>
          </div>
        );
      
      case "api":
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">API Endpoint URL</label>
              <Input 
                placeholder="https://api.example.com/data"
                value={apiEndpoint}
                onChange={(e) => setApiEndpoint(e.target.value)}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Enter the URL of the API endpoint that provides the data
              </p>
            </div>
            
            <Card className="p-4 border border-dashed">
              <h4 className="font-medium mb-2">API Authentication</h4>
              <p className="text-sm text-muted-foreground mb-3">
                Authentication will be handled using configured credentials from Data Sources
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {}}
              >
                Configure API Authentication
              </Button>
            </Card>
          </div>
        );
      
      case "database":
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Database Connection</label>
              <Select value={dbConnection} onValueChange={setDbConnection}>
                <SelectTrigger>
                  <SelectValue placeholder="Select database connection" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="postgres_main">PostgreSQL: Main Database</SelectItem>
                  <SelectItem value="mysql_analytics">MySQL: Analytics DB</SelectItem>
                  <SelectItem value="mongodb_events">MongoDB: Event Store</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground mt-1">
                Select from your configured database connections
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Query or Table Name</label>
              <Input placeholder="SELECT * FROM users WHERE status = 'active'" />
              <p className="text-xs text-muted-foreground mt-1">
                Enter a SQL query or table name to import
              </p>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <Stepper currentStep={currentStep} orientation="horizontal">
          <div className="grid grid-cols-5 gap-4 w-full">
            {pipelineSteps.map((step, index) => (
              <div
                key={index}
                className={`flex items-center gap-2 ${
                  currentStep >= index ? 'text-primary' : 'text-muted-foreground'
                }`}
              >
                {step.icon}
                <div className="flex flex-col">
                  <span className="font-medium">{step.label}</span>
                  <span className="text-xs">{step.description}</span>
                </div>
              </div>
            ))}
          </div>
        </Stepper>
      </div>
      
      {currentStep === 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Data Source</label>
              <Select value={dataSource} onValueChange={setDataSource}>
                <SelectTrigger>
                  <SelectValue placeholder="Select source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="local">Local File Upload</SelectItem>
                  <SelectItem value="api">External API</SelectItem>
                  <SelectItem value="database">Database Connection</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">File Format</label>
              <Select value={fileType} onValueChange={setFileType}>
                <SelectTrigger>
                  <SelectValue placeholder="Select file format" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="csv">CSV</SelectItem>
                  <SelectItem value="json">JSON</SelectItem>
                  <SelectItem value="excel">Excel</SelectItem>
                  <SelectItem value="pdf">PDF</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          {/* Format description */}
          <Alert>
            <Table className="h-4 w-4" />
            <AlertDescription>
              {fileType in supportedFormats ? 
                supportedFormats[fileType as keyof typeof supportedFormats] : 
                "Select a file format"}
            </AlertDescription>
          </Alert>
          
          {/* Dynamic data source fields */}
          {renderDataSourceFields()}
          
          {isUploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="flex items-center">
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Uploading...
                </span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} />
            </div>
          )}
          
          <div className="flex justify-end">
            <Button 
              onClick={handleUpload} 
              disabled={isUploading || 
                (dataSource === "local" && !selectedFile) ||
                (dataSource === "api" && !apiEndpoint) ||
                (dataSource === "database" && !dbConnection)
              }
              className="px-6"
            >
              {isUploading ? 
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Processing...</> : 
                "Upload and Process"}
            </Button>
          </div>
        </>
      ) : (
        <div className="space-y-6">
          <div className="bg-muted/50 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-2">Dataset Information</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Dataset ID:</span>
                <span className="font-mono text-sm">{datasetId}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Current Stage:</span>
                <span className="font-medium">{pipelineSteps[currentStep].label}</span>
              </div>
              {currentStep < 4 ? (
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Next Stage:</span>
                  <span>{pipelineSteps[currentStep + 1].label}</span>
                </div>
              ) : (
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Status:</span>
                  <span className="text-green-600 dark:text-green-400">Ready for completion</span>
                </div>
              )}
            </div>
          </div>
          
          {currentStep === 1 && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Validation will check the data against business rules and identify quality issues.
              </AlertDescription>
            </Alert>
          )}
          
          {currentStep === 2 && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Transformation will clean and restructure the data according to business needs.
              </AlertDescription>
            </Alert>
          )}
          
          {currentStep === 3 && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Enrichment will add derived fields and external data to enhance analysis capabilities.
              </AlertDescription>
            </Alert>
          )}
          
          {currentStep === 4 && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Loading will persist the processed data to the target destination.
              </AlertDescription>
            </Alert>
          )}
          
          <div className="flex justify-end">
            <Button 
              onClick={proceedThroughPipeline}
              disabled={isProcessing}
              className="px-6"
            >
              {isProcessing ? 
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Processing...</> : 
                (currentStep < 4 ? `Proceed to ${pipelineSteps[currentStep].label}` : "Complete Pipeline")}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PipelineUploadForm;
