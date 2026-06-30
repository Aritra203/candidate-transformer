'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { ActivePage, ProjectionConfig, LogEntry, UploadResponse } from '../types';
import { apiService } from '../services/api';

interface FileInfo {
  name: string;
  size: number;
  path: string;
}

interface PipelineContextType {
  activePage: ActivePage;
  setActivePage: (page: ActivePage) => void;
  csvFile: FileInfo | null;
  setCsvFile: (file: FileInfo | null) => void;
  resumeFile: FileInfo | null;
  setResumeFile: (file: FileInfo | null) => void;
  configFile: FileInfo | null;
  setConfigFile: (file: FileInfo | null) => void;
  config: ProjectionConfig;
  setConfig: (config: ProjectionConfig) => void;
  isProcessing: boolean;
  pipelineStage: 'idle' | 'detect' | 'parse' | 'normalize' | 'merger' | 'confidence' | 'projection' | 'validation' | 'completed';
  profiles: any[];
  logs: LogEntry[];
  error: string | null;
  setError: (err: string | null) => void;
  runPipeline: () => Promise<void>;
  resetPipeline: () => void;
}

const defaultProjectionConfig: ProjectionConfig = {
  fields: [
    { path: 'candidate_id', type: 'string', required: true },
    { path: 'full_name', type: 'string', required: true },
    { path: 'emails', type: 'string[]' },
    { path: 'phones', type: 'string[]' },
    { path: 'location', type: 'object' },
    { path: 'links', type: 'object' },
    { path: 'headline', type: 'string' },
    { path: 'years_experience', type: 'number' },
    { path: 'skills', type: 'object[]' },
    { path: 'experience', type: 'object[]' },
    { path: 'education', type: 'object[]' }
  ],
  include_confidence: true,
  include_provenance: true,
  on_missing: 'null'
};

const PipelineContext = createContext<PipelineContextType | undefined>(undefined);

export function PipelineProvider({ children }: { children: React.ReactNode }) {
  const [activePage, setActivePage] = useState<ActivePage>('dashboard');
  const [csvFile, setCsvFile] = useState<FileInfo | null>(null);
  const [resumeFile, setResumeFile] = useState<FileInfo | null>(null);
  const [configFile, setConfigFile] = useState<FileInfo | null>(null);
  const [config, setConfig] = useState<ProjectionConfig>(defaultProjectionConfig);
  
  const [isProcessing, setIsProcessing] = useState(false);
  const [pipelineStage, setPipelineStage] = useState<'idle' | 'detect' | 'parse' | 'normalize' | 'merger' | 'confidence' | 'projection' | 'validation' | 'completed'>('idle');
  const [profiles, setProfiles] = useState<any[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Load defaults from local storage if available on mount
  useEffect(() => {
    const savedConfig = localStorage.getItem('projection_config');
    if (savedConfig) {
      try {
        setConfig(JSON.parse(savedConfig));
      } catch (e) {
        console.error('Failed to parse saved config', e);
      }
    }
  }, []);

  const saveConfig = (newConfig: ProjectionConfig) => {
    setConfig(newConfig);
    localStorage.setItem('projection_config', JSON.stringify(newConfig));
  };

  const runPipeline = async () => {
    if (!csvFile && !resumeFile) {
      setError('Please upload at least a Recruiter CSV or a Resume PDF to run the pipeline.');
      setActivePage('upload');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setProfiles([]);
    setLogs([]);
    setActivePage('pipeline');

    // Helper to simulate stages and add logs
    const stages: Array<typeof pipelineStage> = [
      'detect',
      'parse',
      'normalize',
      'merger',
      'confidence',
      'projection',
      'validation'
    ];

    try {
      // Step through stages visually to give a high-fidelity recruiter dashboard experience
      // during the loading duration.
      for (const stage of stages) {
        setPipelineStage(stage);
        await new Promise((resolve) => setTimeout(resolve, 350));
      }

      // Call API
      const response = await apiService.transformCandidate(
        csvFile?.path,
        resumeFile?.path,
        config
      );

      if (response.success) {
        setProfiles(response.profiles);
        setLogs(response.logs);
        setPipelineStage('completed');
        
        // Show output page once completed successfully
        setTimeout(() => {
          setActivePage('output');
        }, 500);
      } else {
        throw new Error('Transformation failed on server.');
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'An error occurred during candidate transformation.');
      setPipelineStage('idle');
      // Append error to logs
      setLogs((prev) => [
        ...prev,
        {
          timestamp: new Date().toISOString().split('T')[1].substring(0, 8),
          level: 'ERROR',
          stage: 'system',
          message: err.message || 'Pipeline failed with an unexpected error.'
        }
      ]);
      setActivePage('logs');
    } finally {
      setIsProcessing(false);
    }
  };

  const resetPipeline = () => {
    setCsvFile(null);
    setResumeFile(null);
    setConfigFile(null);
    setConfig(defaultProjectionConfig);
    setProfiles([]);
    setLogs([]);
    setError(null);
    setPipelineStage('idle');
    setIsProcessing(false);
    localStorage.removeItem('projection_config');
  };

  return (
    <PipelineContext.Provider
      value={{
        activePage,
        setActivePage,
        csvFile,
        setCsvFile,
        resumeFile,
        setResumeFile,
        configFile,
        setConfigFile,
        config,
        setConfig: saveConfig,
        isProcessing,
        pipelineStage,
        profiles,
        logs,
        error,
        setError,
        runPipeline,
        resetPipeline
      }}
    >
      {children}
    </PipelineContext.Provider>
  );
}

export function usePipeline() {
  const context = useContext(PipelineContext);
  if (context === undefined) {
    throw new Error('usePipeline must be used within a PipelineProvider');
  }
  return context;
}
