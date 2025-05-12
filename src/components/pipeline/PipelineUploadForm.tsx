import React, { useState, useCallback } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2, UploadCloud, CheckCircle2, XCircle, AlertCircle, Info, Sparkles, HardDrive, Filter, ChevronLeft, ChevronRight } from 'lucide-react';
import EnhancedBusinessRules from './EnhancedBusinessRules';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { api } from '@/api/api';
import PipelineStep, { StepStatus } from './PipelineStep';

// Define types
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

interface PipelineStep {
  name: string;
  status: StepStatus;
  description: string;
  icon: React.ReactNode;
  details: string;
}

interface PipelineUploadFormProps {
  onUploadComplete?: (datasetId: string) => void;
}

/**
 * PipelineUploadForm Component
 * 
 * Handles the data pipeline process including file upload, validation,
 * business rule application, transformation, enrichment, and loading.
 */
const PipelineUploadForm: React.FC<PipelineUploadFormProps> = () => {
  // State variables
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [name, setName] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [selectedRules] = useState<string[]>([]);
  const [sampleData, setSampleData] = useState<Record<string, unknown>[]>([]);
  const [pipelineCompleted, setPipelineCompleted] = useState<boolean>(false);
  const [stageLoading, setStageLoading] = useState({
    upload: false,
    validate: false,
    rules: false,
    transform: false,
    enrich: false,
    load: false
  });
  
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
      description: 'Define and apply business rules',
      icon: <Filter className="h-5 w-5" />,
      details: 'Define, select, and apply custom business rules to validate and transform your data'
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
  const [fileType, setFileType] = useState<FileType>('csv');
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

  // Helper function to update step status safely with proper typing
  const updateStepStatus = (steps: PipelineStep[], index: number, status: StepStatus): PipelineStep[] => {
    return steps.map((step, i) => i === index ? { ...step, status } : step);
  };

  // Handle file change
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
      
      // Set data source to local when a file is selected
      setDataSource('local');
    }
  };

  // Handle API config change
  const handleApiConfigChange = (field: keyof ApiConfig, value: string) => {
    setApiConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Handle database config change
  const handleDbConfigChange = (field: keyof DatabaseConfig, value: string | number) => {
    setDbConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };



  // Function to fetch sample data for business rules
  const fetchSampleData = useCallback(async (datasetId: string) => {
    try {
      // Call API to get sample data
      const response = await api.pipeline.getSampleData(datasetId);
      
      if (response.success && response.data) {
        // Store sample data for business rules
        setSampleData(response.data.sample || []);
        return response.data.sample;
      }
      return [];
    } catch (error) {
      console.error('Error fetching sample data:', error);
      toast({
        title: "Error",
        description: "Failed to fetch sample data for rule testing",
        variant: "destructive"
      });
      return [];
    }
  }, [toast]);

  // Handle file validation
  const handleValidateFile = useCallback(async (uploadedDatasetId?: string) => {
    const datasetToValidate = uploadedDatasetId || datasetId;
    
    if (!datasetToValidate) {
      setError('No dataset available to validate');
      return;
    }
    
    try {
      setStageLoading({...stageLoading, validate: true});
      setPipelineSteps(steps => updateStepStatus(steps, 1, 'processing'));
      
      // Call API to validate the file
      const validationResponse = await api.pipeline.validateData(datasetToValidate);
      
      if (validationResponse.success) {
        setCompletedSteps(prev => [...new Set([...prev, 1])]);
        setCurrentStep(2);
        // Update validation step to completed and set next step as active
        setPipelineSteps(steps => {
          let newSteps = [...steps];
          newSteps = updateStepStatus(newSteps, 1, 'completed');
          return updateStepStatus(newSteps, 2, 'processing');
        });

        // Extract sample data for rule testing
        await fetchSampleData(datasetToValidate);

        toast({
          title: "Validation Successful",
          description: "Your data has been validated successfully."
        });
      } else {
        setPipelineSteps(steps => updateStepStatus(steps, 1, 'failed'));
        throw new Error(validationResponse.error || "Failed to start validation");
      }
    } catch (error) {
      setPipelineSteps(steps => updateStepStatus(steps, 1, 'failed'));
      setError(error instanceof Error ? error.message : 'Failed to validate file');
      toast({
        title: "Validation Failed",
        description: error instanceof Error ? error.message : 'Failed to validate file',
        variant: "destructive"
      });
    } finally {
      setStageLoading({...stageLoading, validate: false});
    }
  }, [datasetId, fetchSampleData, setCompletedSteps, setCurrentStep, setError, setPipelineSteps, setStageLoading, stageLoading, toast]);

  // Handle file upload for all data sources (local file, API, database)
  const handleUpload = useCallback(async () => {
    if (!name) {
      setError('Please provide a name for the dataset');
      return;
    }
    
    // Validate input based on data source
    if (dataSource === 'local' && !selectedFile) {
      setError('Please select a file to upload');
      return;
    } else if (dataSource === 'api' && !apiConfig.url) {
      setError('Please provide an API URL');
      return;
    } else if (dataSource === 'database' && (!dbConfig.host || !dbConfig.database || !dbConfig.username)) {
      setError('Please provide all required database connection details');
      return;
    }
    
    try {
      setStageLoading({...stageLoading, upload: true});
      setPipelineSteps(steps => updateStepStatus(steps, 0, 'processing'));
      
      let uploadResponse;
      
      // Handle different data sources
      if (dataSource === 'local') {
        // Upload local file
        const formData = new FormData();
        formData.append('file', selectedFile as File);
        formData.append('name', name);
        formData.append('description', '');
        formData.append('fileType', fileType || 'csv');
        
        uploadResponse = await api.pipeline.uploadData(formData);
      } else if (dataSource === 'api') {
        // Upload from API source
        const apiFormData = new FormData();
        apiFormData.append('name', name);
        apiFormData.append('description', '');
        apiFormData.append('file_type', 'json'); // API data is typically JSON
        apiFormData.append('api_config', JSON.stringify({
          url: apiConfig.url,
          method: apiConfig.method,
          headers: apiConfig.headers || {},
          body: apiConfig.body || ''
        }));
        uploadResponse = await api.pipeline.uploadData(apiFormData);
      } else if (dataSource === 'database') {
        // Upload from database source
        const dbFormData = new FormData();
        dbFormData.append('name', name);
        dbFormData.append('description', '');
        dbFormData.append('file_type', 'csv'); // Database data is typically exported as CSV
        dbFormData.append('db_config', JSON.stringify({
          type: dbConfig.type,
          host: dbConfig.host,
          port: dbConfig.port,
          database: dbConfig.database,
          username: dbConfig.username,
          password: dbConfig.password,
          query: dbConfig.query || 'SELECT * FROM main_table LIMIT 1000'
        }));
        uploadResponse = await api.pipeline.uploadData(dbFormData);
      }
      
      if (uploadResponse && uploadResponse.success) {
        // Extract dataset_id from response
        // Using type assertion since the API response structure may vary
        const datasetId = uploadResponse.data?.dataset_id || 
          (uploadResponse as { dataset_id?: string }).dataset_id;
        
        if (!datasetId) {
          throw new Error('No dataset ID returned from upload');
        }
        
        setDatasetId(datasetId);
        setCompletedSteps(prev => [...new Set([...prev, 0])]);
        setCurrentStep(1);
        
        // Update upload step to completed and set validation step as active
        setPipelineSteps(steps => {
          let newSteps = [...steps];
          newSteps = updateStepStatus(newSteps, 0, 'completed');
          return updateStepStatus(newSteps, 1, 'processing');
        });

        toast({
          title: "Upload Successful",
          description: `Your data from ${dataSource} source has been uploaded successfully.`
        });
        
        // Automatically start validation
        await handleValidateFile(datasetId);
      } else {
        setPipelineSteps(steps => updateStepStatus(steps, 0, 'failed'));
        throw new Error((uploadResponse?.error || "Failed to upload data"));
      }
    } catch (error) {
      setPipelineSteps(steps => updateStepStatus(steps, 0, 'failed'));
      setError(error instanceof Error ? error.message : 'Failed to upload data');
      toast({
        title: "Upload Failed",
        description: error instanceof Error ? error.message : 'Failed to upload data',
        variant: "destructive"
      });
    } finally {
      setStageLoading({...stageLoading, upload: false});
    }
  }, [apiConfig, dataSource, dbConfig, fileType, handleValidateFile, name, selectedFile, setCompletedSteps, setCurrentStep, setDatasetId, setError, setPipelineSteps, setStageLoading, stageLoading, toast]);

  // Handle transform step
  const handleTransform = useCallback(async () => {
    if (!datasetId) {
      setError('No dataset available to transform');
      return;
    }
    
    try {
      setStageLoading({...stageLoading, transform: true});
      setPipelineSteps(steps => updateStepStatus(steps, 3, 'processing'));
      
      // Call API to transform the data
      const transformResponse = await api.pipeline.transformData(datasetId);
      
      if (transformResponse.success) {
        // Update step status
        setCompletedSteps(prev => [...new Set([...prev, 3])]);
        setCurrentStep(4);
        setPipelineSteps(steps => {
          let newSteps = [...steps];
          newSteps = updateStepStatus(newSteps, 3, 'completed');
          return updateStepStatus(newSteps, 4, 'processing');
        });
        
        toast({
          title: "Transform Complete",
          description: "Data transformation completed successfully."
        });
      } else {
        setPipelineSteps(steps => updateStepStatus(steps, 3, 'failed'));
        throw new Error(transformResponse.error || "Failed to transform data");
      }
    } catch (error) {
      setPipelineSteps(steps => updateStepStatus(steps, 3, 'failed'));
      setError(error instanceof Error ? error.message : 'Failed to transform data');
      toast({
        title: "Transform Failed",
        description: error instanceof Error ? error.message : "Failed to transform data.",
        variant: "destructive"
      });
    } finally {
      setStageLoading({...stageLoading, transform: false});
    }
  }, [datasetId, setCompletedSteps, setCurrentStep, setError, setPipelineSteps, setStageLoading, stageLoading, toast]);
  
  // Handle enrich data step
  const handleEnrichData = useCallback(async () => {
    if (!datasetId) {
      setError('No dataset available to enrich');
      return;
    }
    
    try {
      setStageLoading({...stageLoading, enrich: true});
      setPipelineSteps(steps => updateStepStatus(steps, 4, 'processing'));
      
      // Call API to enrich the data
      const enrichResponse = await api.pipeline.enrichData(datasetId);
      
      if (enrichResponse.success) {
        // Update step status - mark the current step as completed
        setCompletedSteps(prev => {
          const updatedSteps = [...new Set([...prev, 4])];
          console.log('Updated completed steps after enrichment:', updatedSteps);
          return updatedSteps;
        });
        
        // Move to the next step
        setCurrentStep(5);
        
        // Update pipeline steps UI
        setPipelineSteps(steps => {
          let newSteps = [...steps];
          newSteps = updateStepStatus(newSteps, 4, 'completed');
          return updateStepStatus(newSteps, 5, 'processing');
        });
        
        toast({
          title: "Enrichment Complete",
          description: "Data enrichment completed successfully. You can now proceed to load data to the vector database."
        });
      } else {
        setPipelineSteps(steps => updateStepStatus(steps, 4, 'failed'));
        throw new Error(enrichResponse.error || "Failed to enrich data");
      }
    } catch (error) {
      setPipelineSteps(steps => updateStepStatus(steps, 4, 'failed'));
      setError(error instanceof Error ? error.message : 'Failed to enrich data');
      toast({
        title: "Enrichment Failed",
        description: error instanceof Error ? error.message : "Failed to enrich data.",
        variant: "destructive"
      });
    } finally {
      setStageLoading({...stageLoading, enrich: false});
    }
  }, [datasetId, setCompletedSteps, setCurrentStep, setError, setPipelineSteps, setStageLoading, stageLoading, toast]);
  
  // Handle load to vector database step
  const handleLoadData = useCallback(async () => {
    if (!datasetId) {
      setError('No dataset available to load to vector database');
      return;
    }
    
    try {
      setStageLoading({...stageLoading, load: true});
      setPipelineSteps(steps => updateStepStatus(steps, 5, 'processing'));
      
      // Call API to load the data to vector database
      const loadResponse = await api.pipeline.loadData(datasetId);
      
      if (loadResponse.success) {
        // Update step status
        setCompletedSteps(prev => [...new Set([...prev, 5])]);
        setPipelineSteps(steps => updateStepStatus(steps, 5, 'completed'));
        
        // Show success toast with longer duration
        toast({
          title: "Pipeline Complete",
          description: "Data has been successfully loaded to the vector database. Your data is now ready for analysis!",
          duration: 5000
        });
        
        // Set pipeline completion state
        setPipelineCompleted(true);
      } else {
        setPipelineSteps(steps => updateStepStatus(steps, 5, 'failed'));
        throw new Error(loadResponse.error || "Failed to load data to vector database");
      }
    } catch (error) {
      setPipelineSteps(steps => updateStepStatus(steps, 5, 'failed'));
      setError(error instanceof Error ? error.message : 'Failed to load data to vector database');
      toast({
        title: "Vector Database Load Failed",
        description: error instanceof Error ? error.message : "Failed to load data to vector database.",
        variant: "destructive"
      });
    } finally {
      setStageLoading({...stageLoading, load: false});
    }
  }, [datasetId, setCompletedSteps, setError, setPipelineSteps, setStageLoading, stageLoading, toast, setPipelineCompleted]);

  // Navigate to a specific step without triggering API calls if step is already completed
  const handleNavigate = useCallback((step: number) => {
    // Only allow navigation to completed steps or the current step + 1
    if (completedSteps.includes(step) || step === currentStep || step === currentStep + 1) {
      setCurrentStep(step);
      
      // Update the active step in the UI
      setPipelineSteps(steps => {
        let newSteps = [...steps];
        // Reset all steps to their proper status
        newSteps = newSteps.map((step, idx) => {
          if (completedSteps.includes(idx)) {
            return { ...step, status: 'completed' as StepStatus };
          } else if (idx === currentStep) {
            return { ...step, status: 'processing' as StepStatus };
          } else {
            return { ...step, status: 'pending' as StepStatus };
          }
        });
        return newSteps;
      });
    }
  }, [completedSteps, currentStep, setCurrentStep, setPipelineSteps]);

  // Handle continue button - only trigger API calls if the step hasn't been completed
  const handleContinue = useCallback(async () => {
    console.log('Current step:', currentStep);
    console.log('Completed steps:', completedSteps);
    
    // If we're at the final step and it's completed, don't do anything
    if (currentStep === pipelineSteps.length - 1 && completedSteps.includes(currentStep)) {
      console.log('Final step already completed');
      return;
    }
    
    // If the next step is already completed, just navigate to it
    if (completedSteps.includes(currentStep + 1)) {
      console.log('Next step already completed, navigating to it');
      handleNavigate(currentStep + 1);
      return;
    }
    
    // Otherwise, trigger the appropriate API call based on the current step
    console.log('Triggering action for step:', currentStep);
    switch (currentStep) {
      case 0: // Upload step
        await handleUpload();
        break;
      case 1: // Validation step
        await handleValidateFile();
        break;
      case 2: // Business Rules step
        // This is handled by the EnhancedBusinessRules component
        break;
      case 3: // Transform step
        await handleTransform();
        break;
      case 4: // Enrich step
        await handleEnrichData();
        break;
      case 5: // Load to Vector Database step
        await handleLoadData();
        break;
      default:
        break;
    }
  }, [currentStep, completedSteps, handleNavigate, handleUpload, handleValidateFile, handleTransform, handleEnrichData, handleLoadData, pipelineSteps.length]);
  
  // Reset pipeline process for a new dataset
  const resetPipeline = useCallback(() => {
    // Reset all state variables
    setSelectedFile(null);
    setName('');
    setError(null);
    setDatasetId(null);
    setCurrentStep(0);
    setCompletedSteps([]);
    setSampleData([]);
    setPipelineCompleted(false);
    setStageLoading({
      upload: false,
      validate: false,
      rules: false,
      transform: false,
      enrich: false,
      load: false
    });
    
    // Reset pipeline steps
    setPipelineSteps(steps => 
      steps.map(step => ({
        ...step,
        status: 'pending'
      }))
    );
    
    toast({
      title: "New Pipeline Started",
      description: "You can now upload a new dataset to process.",
      variant: "default"
    });
  }, [setSelectedFile, setName, setError, setDatasetId, setCurrentStep, setCompletedSteps, 
      setSampleData, setPipelineCompleted, setStageLoading, setPipelineSteps, toast]);

  // Handle business rules application
  const handleBusinessRules = async (appliedRuleIds?: string[]) => {
    setStageLoading({...stageLoading, rules: true});
    try {
      // If rule IDs are provided, use them; otherwise use selectedRules
      const ruleIds = appliedRuleIds || selectedRules;

      if (ruleIds.length === 0) {
        toast({
          title: "No Rules Selected",
          description: "No business rules were selected to apply.",
          variant: "default"
        });
        return;
      }

      // Call the API to apply the selected rules
      const response = await api.pipeline.applyBusinessRules(datasetId || '', ruleIds);

      if (response.success) {
        // Update step status
        setCompletedSteps(prev => [...new Set([...prev, 2])]);
        setCurrentStep(3); // Move to transform step
        setPipelineSteps(steps => {
          let newSteps = [...steps];
          newSteps = updateStepStatus(newSteps, 2, 'completed');
          return updateStepStatus(newSteps, 3, 'processing');
        });

        toast({
          title: "Business Rules Applied",
          description: `Successfully applied ${ruleIds.length} business rules.`
        });
      } else {
        setPipelineSteps(steps => updateStepStatus(steps, 2, 'failed'));
        toast({
          title: "Error",
          description: response.error || "Failed to apply business rules.",
          variant: "destructive"
        });
      }
    } catch {
      setPipelineSteps(steps => updateStepStatus(steps, 2, 'failed'));
      toast({
        title: "Error",
        description: "Failed to apply business rules.",
        variant: "destructive"
      });
    } finally {
      setStageLoading({...stageLoading, rules: false});
    }
  };

  // Render the form
  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>Data Pipeline</CardTitle>
          <CardDescription>Upload, validate, transform, and load your data</CardDescription>
          {pipelineCompleted && (
            <div className="mt-2 flex items-center">
              <Badge variant="success" className="bg-green-100 text-green-800 hover:bg-green-200 mr-2">
                Pipeline Complete
              </Badge>
              <Button 
                variant="outline" 
                size="sm" 
                className="ml-auto" 
                onClick={resetPipeline}
              >
                <span className="mr-1">+</span> Start New Pipeline
              </Button>
            </div>
          )}
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Pipeline Steps - Vertical Layout */}
            <div className="flex">
              {/* Left sidebar with steps */}
              <div className="w-1/4 space-y-2 border-r pr-4">
                {pipelineSteps.map((step, index) => (
                  <div 
                    key={index}
                    onClick={() => {
                      // Only allow clicking on completed steps or the current step
                      if (completedSteps.includes(index) || index === currentStep) {
                        setCurrentStep(index);
                      }
                    }}
                    className={`
                      p-3 rounded-md flex flex-col space-y-1 cursor-pointer
                      ${currentStep === index ? 'bg-blue-50 border-l-4 border-blue-500' : ''}
                      ${completedSteps.includes(index) ? 'text-blue-700' : 'text-gray-500'}
                      ${!completedSteps.includes(index) && index !== currentStep ? 'opacity-60' : ''}
                    `}
                  >
                    <div className="flex items-center space-x-2">
                      <div className={`
                        flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center
                        ${step.status === 'completed' ? 'bg-green-100 text-green-600' : 
                          step.status === 'failed' ? 'bg-red-100 text-red-600' : 
                          step.status === 'processing' ? 'bg-blue-100 text-blue-600' : 
                          currentStep === index ? 'bg-blue-100 text-blue-600' : 
                          'bg-gray-100 text-gray-500'}
                      `}>
                        {step.status === 'completed' ? <CheckCircle2 className="h-4 w-4" /> :
                         step.status === 'failed' ? <XCircle className="h-4 w-4" /> :
                         step.status === 'processing' ? <Loader2 className="h-4 w-4 animate-spin" /> :
                         step.icon}
                      </div>
                      <div className="font-medium">{step.name}</div>
                    </div>
                    <div className="text-xs text-muted-foreground pl-8">{step.description}</div>
                  </div>
                ))}
              </div>
              
              {/* Right content area */}
              <div className="w-3/4 pl-6 space-y-4">
              {/* Upload Step */}
              {currentStep === 0 && (
                <div className="space-y-4">
                  <Tabs defaultValue="local" className="w-full">
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="local" onClick={() => setDataSource('local')}>Local File</TabsTrigger>
                      <TabsTrigger value="api" onClick={() => setDataSource('api')}>API</TabsTrigger>
                      <TabsTrigger value="database" onClick={() => setDataSource('database')}>Database</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="local" className="space-y-4">
                      <div className="grid gap-4">
                        <div>
                          <label htmlFor="name" className="block text-sm font-medium mb-1">Dataset Name</label>
                          <input 
                            id="name"
                            type="text"
                            className="w-full p-2 border rounded"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="Enter dataset name"
                          />
                        </div>
                        
                        <div>
                          <label htmlFor="file" className="block text-sm font-medium mb-1">Upload File</label>
                          <input 
                            id="file"
                            type="file"
                            className="w-full p-2 border rounded"
                            onChange={handleFileChange}
                            accept=".csv,.json,.xlsx,.xls,.parquet"
                          />
                        </div>
                        
                        {selectedFile && (
                          <Alert>
                            <CheckCircle2 className="h-4 w-4" />
                            <AlertTitle>File Selected</AlertTitle>
                            <AlertDescription>
                              {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                            </AlertDescription>
                          </Alert>
                        )}
                      </div>
                      
                      <div className="flex justify-between">
                        <div></div> {/* Empty div for spacing */}
                        <button
                          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center"
                          onClick={handleUpload}
                          disabled={!selectedFile || !name || stageLoading.upload}
                        >
                          {stageLoading.upload ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Uploading...
                            </>
                          ) : (
                            <>
                              <UploadCloud className="mr-2 h-4 w-4" />
                              Upload & Continue
                            </>
                          )}
                        </button>
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="api" className="space-y-4">
                      {/* API configuration UI */}
                      <div className="grid gap-4">
                        <div>
                          <label htmlFor="api-name" className="block text-sm font-medium mb-1">Dataset Name</label>
                          <input 
                            id="api-name"
                            type="text"
                            className="w-full p-2 border rounded"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="Enter dataset name"
                          />
                        </div>
                        
                        <div>
                          <label htmlFor="api-url" className="block text-sm font-medium mb-1">API URL</label>
                          <input 
                            id="api-url"
                            type="text"
                            className="w-full p-2 border rounded"
                            value={apiConfig.url}
                            onChange={(e) => handleApiConfigChange('url', e.target.value)}
                            placeholder="https://api.example.com/data"
                          />
                        </div>
                        
                        <div>
                          <label htmlFor="api-method" className="block text-sm font-medium mb-1">Method</label>
                          <Select 
                            value={apiConfig.method} 
                            onValueChange={(value) => handleApiConfigChange('method', value as 'GET' | 'POST')}
                          >
                            <SelectTrigger id="api-method">
                              <SelectValue placeholder="Select method" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="GET">GET</SelectItem>
                              <SelectItem value="POST">POST</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="database" className="space-y-4">
                      {/* Database configuration UI */}
                      <div className="grid gap-4">
                        <div>
                          <label htmlFor="db-name" className="block text-sm font-medium mb-1">Dataset Name</label>
                          <input 
                            id="db-name"
                            type="text"
                            className="w-full p-2 border rounded"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="Enter dataset name"
                          />
                        </div>
                        
                        <div>
                          <label htmlFor="db-type" className="block text-sm font-medium mb-1">Database Type</label>
                          <Select 
                            value={dbConfig.type} 
                            onValueChange={(value: string) => handleDbConfigChange('type', value)}
                          >
                            <SelectTrigger id="db-type">
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
                      </div>
                    </TabsContent>
                  </Tabs>
                </div>
              )}

              {/* Validate Step */}
              {currentStep === 1 && (
                <div className="space-y-4">
                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertTitle>Validation in Progress</AlertTitle>
                    <AlertDescription>
                      Validating your data structure and integrity...
                    </AlertDescription>
                  </Alert>
                </div>
              )}

              {/* Business Rules Step */}
              {currentStep === 2 && (
                <div className="space-y-4">
                  <EnhancedBusinessRules 
                    datasetId={datasetId || ''}
                    sampleData={sampleData}
                    onRulesApplied={handleBusinessRules}
                    onComplete={() => {
                      setCompletedSteps(prev => [...new Set([...prev, 2])]);
                      setCurrentStep(3);
                    }}
                  />
                </div>
              )}
              
              {/* Transform Step */}
              {currentStep === 3 && (
                <div className="space-y-4">
                  <Alert>
                    <Sparkles className="h-4 w-4" />
                    <AlertTitle>Transform Data</AlertTitle>
                    <AlertDescription>
                      Apply transformations to your data.
                    </AlertDescription>
                  </Alert>
                </div>
              )}

              {/* Enrich Step */}
              {currentStep === 4 && (
                <div className="space-y-4">
                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertTitle>Enrich Data</AlertTitle>
                    <AlertDescription>
                      Add derived fields and enrichments to your data.
                    </AlertDescription>
                  </Alert>
                </div>
              )}

              {/* Load Step */}
              {currentStep === 5 && (
                <div className="space-y-4">
                  {pipelineCompleted ? (
                    <div className="space-y-4">
                      <Alert className="bg-green-50 border-green-200">
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                        <AlertTitle>Pipeline Complete</AlertTitle>
                        <AlertDescription>
                          Your data has been successfully processed and loaded to the vector database.
                        </AlertDescription>
                      </Alert>
                      
                      <Card className="bg-blue-50/30">
                        <CardHeader>
                          <CardTitle className="text-lg">Pipeline Summary</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span className="font-medium">Dataset ID:</span>
                              <span className="font-mono bg-white px-2 py-0.5 rounded border">{datasetId}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="font-medium">Dataset Name:</span>
                              <span>{name}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="font-medium">Completed Steps:</span>
                              <span>{completedSteps.length} of {pipelineSteps.length}</span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                      
                      <div className="flex justify-center">
                        <Button 
                          onClick={resetPipeline}
                          className="bg-blue-600 hover:bg-blue-700 text-white"
                        >
                          <span className="mr-2">+</span> Start New Pipeline
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <Alert>
                      <HardDrive className="h-4 w-4" />
                      <AlertTitle>Load Data to Vector Database</AlertTitle>
                      <AlertDescription>
                        Loading your processed data to the vector database for semantic search and RAG capabilities.
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}
              </div>
              
              {/* Only show navigation controls after the first step */}
              {currentStep > 0 && (
                <div className="flex justify-between mt-6">
                  <Button
                    variant="outline"
                    className="flex items-center gap-2"
                    onClick={() => handleNavigate(currentStep - 1)}
                    disabled={currentStep === 0 || Object.values(stageLoading).some(loading => loading)}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Back
                  </Button>
                  
                  <Button
                    variant="default"
                    className="bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2"
                    onClick={handleContinue}
                    disabled={Object.values(stageLoading).some(loading => loading) || 
                             (pipelineCompleted && currentStep === pipelineSteps.length - 1)}
                  >
                    {Object.values(stageLoading).some(loading => loading) ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        Continue
                        <ChevronRight className="h-4 w-4" />
                      </>
                    )}
                  </Button>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default PipelineUploadForm;
