'use client';

import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  File, 
  CheckCircle2, 
  X, 
  AlertCircle, 
  Loader2 
} from 'lucide-react';
import { apiService } from '../services/api';

interface UploadCardProps {
  title: string;
  description: string;
  acceptedTypes: string; // e.g. ".csv", ".pdf", ".json"
  fileType: 'csv' | 'pdf' | 'json';
  onUploadSuccess: (fileInfo: { name: string; size: number; path: string }) => void;
  onRemove: () => void;
  currentFile: { name: string; size: number } | null;
}

export default function UploadCard({
  title,
  description,
  acceptedTypes,
  fileType,
  onUploadSuccess,
  onRemove,
  currentFile
}: UploadCardProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadState, setUploadState] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [progress, setProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleFile = async (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    const allowed = acceptedTypes.split(',').map(t => t.trim().toLowerCase());
    
    if (!allowed.includes(ext)) {
      setUploadState('error');
      setErrorMessage(`Invalid file format. Please upload a ${acceptedTypes} file.`);
      return;
    }

    setUploadState('uploading');
    setProgress(15);
    setErrorMessage(null);

    // Simulate progress bar increase
    const interval = setInterval(() => {
      setProgress((prev) => (prev < 90 ? prev + 15 : prev));
    }, 200);

    try {
      let res;
      if (fileType === 'csv') {
        res = await apiService.uploadCSV(file);
      } else if (fileType === 'pdf') {
        res = await apiService.uploadResume(file);
      } else {
        res = await apiService.uploadConfig(file);
      }

      clearInterval(interval);
      setProgress(100);
      setUploadState('success');
      onUploadSuccess({
        name: res.filename,
        size: res.size,
        path: res.path
      });
    } catch (err: any) {
      clearInterval(interval);
      setUploadState('error');
      setErrorMessage(err.message || 'File upload failed. Please try again.');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const clearFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setUploadState('idle');
    setProgress(0);
    setErrorMessage(null);
    onRemove();
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="flex flex-col h-full">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={currentFile ? undefined : triggerFileInput}
        className={`flex-1 flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-6 transition-all duration-200 ${
          currentFile
            ? 'border-primary/20 bg-card'
            : isDragging
            ? 'border-primary bg-primary/5'
            : 'border-border hover:border-primary/50 bg-card cursor-pointer'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept={acceptedTypes}
          className="hidden"
          disabled={!!currentFile}
        />

        {currentFile ? (
          // File display state
          <div className="w-full flex flex-col gap-4">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-lg bg-primary/10 text-primary border border-primary/10 shrink-0">
                <File className="h-6 w-6" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-foreground truncate">
                  {currentFile.name}
                </p>
                <p className="text-xs text-muted-foreground font-mono">
                  {formatSize(currentFile.size)}
                </p>
              </div>
              <button
                onClick={clearFile}
                className="p-1 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                aria-label="Remove File"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-600 dark:text-emerald-455 mt-2">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span>Ready for Transformation</span>
            </div>
          </div>
        ) : uploadState === 'uploading' ? (
          // Uploading State
          <div className="w-full flex flex-col items-center gap-3 py-4">
            <Loader2 className="h-8 w-8 text-primary animate-spin" />
            <div className="w-full max-w-[200px] bg-muted border border-border/10 rounded-full h-1.5 overflow-hidden">
              <div 
                className="bg-primary h-1.5 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="text-xs font-semibold text-muted-foreground">
              Uploading... {progress}%
            </span>
          </div>
        ) : (
          // Empty / Drop Zone state
          <div className="flex flex-col items-center text-center gap-3">
            <div className="p-4 rounded-full bg-muted border border-border/80 text-muted-foreground/80">
              <UploadCloud className="h-7 w-7" />
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground">
                {title}
              </p>
              <p className="text-xs text-muted-foreground mt-1 max-w-[220px] leading-relaxed">
                {description}
              </p>
            </div>
            <span className="inline-flex items-center rounded-lg bg-primary/10 px-2.5 py-1 text-xs font-bold text-primary border border-primary/15">
              Drop or Browse ({acceptedTypes})
            </span>
          </div>
        )}

        {uploadState === 'error' && errorMessage && (
          <div className="mt-4 w-full flex items-start gap-2 rounded-lg bg-red-50 dark:bg-red-950/20 p-3 text-xs font-medium text-red-700 dark:text-red-400 border border-red-100 dark:border-red-900/30">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="font-semibold">Upload Error</p>
              <p className="mt-0.5 leading-relaxed">{errorMessage}</p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setUploadState('idle');
              }}
              className="p-0.5 hover:bg-red-100 dark:hover:bg-red-900/50 rounded"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
