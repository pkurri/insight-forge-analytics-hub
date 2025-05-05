import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { FileInput } from '@/components/ui/file-input';
import { api } from '@/api/api';
import { PipelineStatus } from '@/api/types';

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

  const handleFileChange = (newFile: File | null) => {
    setFile(newFile);
  };

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPipelineName(e.target.value);
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
      const response = await api.datasets.uploadDataset(file, pipelineName);

      if (response.success && response.data) {
        setStatus({
          current_stage: 'Upload Complete',
          progress: 100,
          status: 'completed',
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
      <Button onClick={handleUpload} disabled={uploading}>
        {uploading ? 'Uploading...' : 'Upload'}
      </Button>
      {error && <div className="text-red-500">{error}</div>}
      {renderStatus()}
    </div>
  );
};

export default PipelineUploadForm;
