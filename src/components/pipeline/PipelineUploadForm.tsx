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
import { PipelineStatus } from '@/api/types';

type DataSource = 'local' | 'api' | 'database';
type PipelineStage = 'validate' | 'transform' | 'enrich' | 'load';

interface PipelineResponse {
  success: boolean;
  data?: {
    id: string;
  };
  error?: string;
}

interface PipelineStatusResponse {
  success: boolean;
  data?: PipelineStatus;
  error?: string;
}

interface PipelineStep {
  label: string;
  description: string;
  icon?: React.ReactNode;
}

const PipelineUploadForm: React.FC = () => {
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

  const pipelineSteps: PipelineStep[] = [
    { label: "Upload", description: "Upload data file", icon: <UploadCloud className="h-4 w-4" /> },
    { label: "Validate", description: "Validate data integrity", icon: <AlertCircle className="h-4 w-4" /> },
    { label: "Business Rules", description: "Apply business rules", icon: <Check className="h-4 w-4" /> },
    { label: "Transform", description: "Apply transformations", icon: <File className="h-4 w-4" /> },
    { label: "Enrich", description: "Add derived fields", icon: <Table className="h-4 w-4" /> },
    { label: "Load", description: "Save processed data", icon: <Check className="h-4 w-4" /> }
  ];

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
      setError("Please select a database connection");
      return false;
    }

    setError(null);
    return true;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      
      // Basic file validation
      const validTypes = ['text/csv', 'application/json', 'application/vnd.ms-excel'];
      if (!validTypes.includes(file.type)) {
        setError('Invalid file type. Please upload a CSV or JSON file.');
        return;
      }
      
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        setError('File size exceeds 10MB limit');
        return;
      }
      
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleUpload = async (): Promise<void> => {
    if (!validateInputs()) return;

    setIsUploading(true);
    setUploadProgress(0);
    setError(null);
    
    try {
      const formData = new FormData();
      
      if (dataSource === "local" && selectedFile) {
        formData.append('file', selectedFile);
        formData.append('file_type', fileType);
      } else if (dataSource === "api") {
        formData.append('api_endpoint', apiEndpoint);
      } else if (dataSource === "database") {
        formData.append('connection_id', dbConnection);
      }
      
      // Real progress tracking with axios
      const response = await api.pipelineService.uploadData(formData, {
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(progress);
          }
        }
      });
      
      if (response.success && response.data) {
        setDatasetId(response.data.id);
        setCurrentStep(1);
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
      console.error("Upload error:", error);
      setError(error instanceof Error ? error.message : "Failed to upload data");
      toast({
        title: "Upload failed",
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
        const status = await api.pipelineService.getPipelineStatus(pipelineId);
        
        if (status.success && status.data) {
          const { current_stage, progress, status: pipelineStatus, statusMessage } = status.data;
          
          // Update loading states
          setStageLoading(prev => ({
            ...prev,
            validate: current_stage === 'validate',
            transform: current_stage === 'transform',
            enrich: current_stage === 'enrich',
            load: current_stage === 'load'
          }));

          // Update UI based on pipeline status
          switch (current_stage) {
            case 'validate': setCurrentStep(1); break;
            case 'transform': setCurrentStep(3); break;
            case 'enrich': setCurrentStep(4); break;
            case 'load': setCurrentStep(5); break;
          }

          if (pipelineStatus === 'completed') {
            isComplete = true;
            setIsProcessing(false);
            toast({
              title: "Pipeline completed",
              description: statusMessage || "Data processing completed successfully",
            });
          } else if (pipelineStatus === 'failed') {
            throw new Error(statusMessage || "Pipeline processing failed");
          }
        }

        // Wait before next status check
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    } catch (error) {
      setIsProcessing(false);
      setStageLoading({
        validate: false,
        transform: false,
        enrich: false,
        load: false
      });
      setError(error instanceof Error ? error.message : "Pipeline processing failed");
      toast({
        title: "Pipeline error",
        description: error instanceof Error ? error.message : "An error occurred during processing",
        variant: "destructive",
      });
    }
  };

  return (
    <Card className="w-full p-6">
      <div className="space-y-6">
        <Stepper currentStep={currentStep}>
          {pipelineSteps.map((step, index) => (
            <Step key={index}>
              {step.icon && (
                <div className="mr-2">
                  {step.icon}
                </div>
              )}
              <div>
                <div className="text-sm font-medium">{step.label}</div>
                <div className="text-sm text-muted-foreground">{step.description}</div>
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
              <div className="space-y-2">
                <label className="text-sm font-medium">File Type</label>
                <Select value={fileType} onValueChange={setFileType}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select file type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="csv">CSV</SelectItem>
                    <SelectItem value="json">JSON</SelectItem>
                    <SelectItem value="excel">Excel</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {dataSource === 'local' && (
            <div className="space-y-2">
              <label className="text-sm font-medium">File</label>
              <Input type="file" onChange={handleFileChange} accept=".csv,.json,.xlsx" />
              {selectedFile && (
                <div className="text-sm text-muted-foreground">
                  Selected: {selectedFile.name} ({Math.round(selectedFile.size / 1024)} KB)
                </div>
              )}
            </div>
          )}

          {dataSource === 'api' && (
            <div className="space-y-2">
              <label className="text-sm font-medium">API Endpoint</label>
              <Input 
                type="text" 
                value={apiEndpoint} 
                onChange={(e) => setApiEndpoint(e.target.value)} 
                placeholder="https://api.example.com/data"
              />
            </div>
          )}

          {dataSource === 'database' && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Database Connection</label>
              <Select value={dbConnection} onValueChange={setDbConnection}>
                <SelectTrigger>
                  <SelectValue placeholder="Select connection" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="prod">Production DB</SelectItem>
                  <SelectItem value="staging">Staging DB</SelectItem>
                  <SelectItem value="backup">Backup DB</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Button 
              onClick={handleUpload} 
              disabled={isUploading || isProcessing}
              className="w-full"
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
        </div>
      </div>
    </Card>
  );
};

export default PipelineUploadForm;
