import React, { useState } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, UploadCloud, CheckCircle2, XCircle } from 'lucide-react';
import { pipelineService, BusinessRule, ValidationResult } from '@/api/services/pipeline';

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

const PipelineUploadForm: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<string>('');
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

  const { toast } = useToast();

  const handleFileUpload = async (): Promise<void> => {
    if (!selectedFile || !fileType) {
      setError("Please select a file and specify its type");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await pipelineService.uploadData(selectedFile, fileType, name, description);
      if (response.success && response.data) {
        setDatasetId(response.data.dataset_id);
        setCurrentStep(1);
        toast({
          title: "File uploaded successfully",
          description: "Your file has been uploaded and is ready for validation.",
        });
      } else {
        throw new Error(response.error || "Failed to upload file");
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : "Failed to upload file");
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "Failed to upload file",
        variant: "destructive",
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
            <label htmlFor="file" className="text-sm font-medium">
              Select File
            </label>
            <Input
              id="file"
              type="file"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  setSelectedFile(file);
                  const extension = file.name.split('.').pop()?.toLowerCase();
                  if (extension) {
                    setFileType(extension);
                  }
                }
              }}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="dataset-name" className="text-sm font-medium">
              Dataset Name
            </label>
            <Input
              id="dataset-name"
              placeholder="Enter a name for this dataset"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="dataset-description" className="text-sm font-medium">
              Description
            </label>
            <Textarea
              id="dataset-description"
              placeholder="Enter a description for this dataset"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
            />
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
                  handleFileUpload();
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
