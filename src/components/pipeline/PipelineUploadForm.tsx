
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { FileInput } from '@/components/ui/file-input';
import { api } from '@/api/api';
import { PipelineStatus } from '@/api/types';
import BusinessRulesSelect from './BusinessRulesSelect';
import { Switch } from '@/components/ui/switch';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { AlertCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface PipelineUploadFormProps {
  onUploadComplete?: (pipelineId: string) => void;
}

export const PipelineUploadForm: React.FC<PipelineUploadFormProps> = ({
  onUploadComplete
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [pipelineName, setPipelineName] = useState<string>('');
  const [uploading, setUploading] = useState<boolean>(false);
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedRules, setSelectedRules] = useState<string[]>([]);
  const [applyRulesOnUpload, setApplyRulesOnUpload] = useState<boolean>(true);
  const { toast } = useToast();

  const handleFileChange = (newFile: File | null) => {
    setFile(newFile);
  };

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPipelineName(e.target.value);
  };

  const handleRuleSelection = (ruleIds: string[]) => {
    setSelectedRules(ruleIds);
  };

  const handleUpload = async () => {
    if (!file || !pipelineName) {
      setError('Please select a file and enter a pipeline name.');
      return;
    }

    setUploading(true);
    setError(null);
    setStatus(null);

    try {
      // Create FormData with file and metadata
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', pipelineName);
      
      // Add business rules if selected
      if (selectedRules.length > 0) {
        formData.append('business_rules', JSON.stringify(selectedRules));
      }
      
      // Set whether to apply rules during upload
      formData.append('apply_rules_on_upload', String(applyRulesOnUpload));

      const response = await api.datasets.uploadDataset(formData);

      if (response.success && response.data) {
        setStatus({
          current_stage: 'Upload Complete',
          progress: 100,
          status: 'completed',
        });
        
        toast({
          title: "Upload successful",
          description: `${pipelineName} uploaded successfully${selectedRules.length > 0 ? ' with business rules applied' : ''}`,
        });
        
        if (onUploadComplete) {
          onUploadComplete(response.data.id);
        }
      } else {
        setError(response.error || 'Upload failed.');
        setStatus({
          current_stage: 'Upload Failed',
          progress: 0,
          status: 'failed',
          statusMessage: response.error || 'Upload failed.',
        });
        
        toast({
          title: "Upload failed",
          description: response.error || "An error occurred during upload",
          variant: "destructive",
        });
      }
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'An unexpected error occurred';
      setError(errorMessage);
      setStatus({
        current_stage: 'Upload Failed',
        progress: 0,
        status: 'failed',
        statusMessage: errorMessage,
      });
      
      toast({
        title: "Upload failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setUploading(false);
    }
  };

  const renderStatus = () => {
    if (!status) return null;

    return (
      <div className="mt-4 space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span>{status.current_stage}</span>
          <span>{status.progress}%</span>
        </div>
        <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
          <div 
            className={`h-2 ${status.status === 'failed' ? 'bg-red-500' : 'bg-blue-500'}`} 
            style={{ width: `${status.progress}%` }}
          ></div>
        </div>
        {status.status === 'failed' && status.statusMessage && (
          <div className="text-sm text-red-500">{status.statusMessage}</div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="pipelineName">Pipeline Name</Label>
        <Input
          id="pipelineName"
          type="text"
          placeholder="Enter pipeline name"
          value={pipelineName}
          onChange={handleNameChange}
          disabled={uploading}
        />
      </div>
      <div>
        <FileInput
          id="pipelineFile"
          onChange={handleFileChange}
          disabled={uploading}
        />
      </div>
      
      <BusinessRulesSelect
        onSelect={handleRuleSelection}
      />
      
      <div className="flex items-center justify-between space-x-2">
        <div className="flex items-center space-x-2">
          <Switch
            id="apply-rules"
            checked={applyRulesOnUpload}
            onCheckedChange={setApplyRulesOnUpload}
            disabled={uploading}
          />
          <Label htmlFor="apply-rules" className="text-sm">
            Apply business rules during upload
          </Label>
        </div>
        
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div>
                <AlertCircle className="h-4 w-4 text-muted-foreground" />
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p className="max-w-xs text-xs">
                When enabled, selected business rules will be applied as data is processed.
                This may increase processing time but ensures data quality from the start.
              </p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
      
      <Button onClick={handleUpload} disabled={uploading}>
        {uploading ? 'Uploading...' : 'Upload'}
      </Button>
      {error && <div className="text-red-500">{error}</div>}
      {renderStatus()}
    </div>
  );
};

export default PipelineUploadForm;
