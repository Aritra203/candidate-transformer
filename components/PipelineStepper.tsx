'use client';

import React from 'react';
import { 
  FileText, 
  Settings, 
  UserCheck, 
  Sparkles, 
  BarChart, 
  GitMerge, 
  CheckCircle,
  AlertTriangle,
  ArrowRight
} from 'lucide-react';

interface Stage {
  key: 'idle' | 'detect' | 'parse' | 'normalize' | 'merger' | 'confidence' | 'projection' | 'validation' | 'completed';
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface PipelineStepperProps {
  currentStage: Stage['key'];
  isProcessing: boolean;
  error: string | null;
}

export default function PipelineStepper({ currentStage, isProcessing, error }: PipelineStepperProps) {
  const stages: Stage[] = [
    { key: 'detect', label: 'Detection', description: 'Detect CSV or PDF formats', icon: FileText },
    { key: 'parse', label: 'Parser', description: 'Parse text and tabular data', icon: Settings },
    { key: 'normalize', label: 'Normalizer', description: 'Coerce values to standards', icon: Sparkles },
    { key: 'merger', label: 'Merger', description: 'Merge records and resolve conflicts', icon: GitMerge },
    { key: 'confidence', label: 'Confidence', description: 'Evaluate field authority', icon: BarChart },
    { key: 'projection', label: 'Projection', description: 'Map paths based on JSON config', icon: UserCheck },
    { key: 'validation', label: 'Validation', description: 'Enforce schema constraints', icon: CheckCircle }
  ];

  const getStageStatus = (stageKey: Stage['key'], index: number) => {
    if (error && currentStage === stageKey) return 'error';
    if (currentStage === 'completed') return 'completed';
    if (currentStage === 'idle') return 'pending';

    const currentIdx = stages.findIndex((s) => s.key === currentStage);
    if (index < currentIdx) return 'completed';
    if (index === currentIdx) return 'active';
    return 'pending';
  };

  return (
    <div className="w-full py-8 px-4 bg-white dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
      <div className="flex flex-col md:flex-row items-center justify-between gap-6 max-w-5xl mx-auto">
        {stages.map((stage, idx) => {
          const status = getStageStatus(stage.key, idx);
          const Icon = stage.icon;

          return (
            <React.Fragment key={stage.key}>
              {/* Stage Node */}
              <div className="flex flex-col items-center text-center relative group w-full md:w-36">
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-full border-2 transition-all duration-300 shadow-sm ${
                    status === 'completed'
                      ? 'bg-emerald-50 border-emerald-500 text-emerald-600 dark:bg-emerald-950/20 dark:border-emerald-400 dark:text-emerald-400'
                      : status === 'active'
                      ? 'bg-indigo-50 border-indigo-600 text-indigo-600 dark:bg-indigo-950/20 dark:border-indigo-400 dark:text-indigo-400 animate-pulse'
                      : status === 'error'
                      ? 'bg-red-50 border-red-500 text-red-600 dark:bg-red-950/20 dark:border-red-400 dark:text-red-400'
                      : 'bg-slate-50 border-slate-200 text-slate-400 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-600'
                  }`}
                >
                  {status === 'completed' ? (
                    <CheckCircle className="h-5 w-5" />
                  ) : status === 'error' ? (
                    <AlertTriangle className="h-5 w-5" />
                  ) : (
                    <Icon className="h-5 w-5" />
                  )}
                </div>

                <div className="mt-3">
                  <p
                    className={`text-sm font-semibold transition-colors duration-200 ${
                      status === 'active'
                        ? 'text-indigo-600 dark:text-indigo-400'
                        : status === 'completed'
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : status === 'error'
                        ? 'text-red-600 dark:text-red-400'
                        : 'text-slate-700 dark:text-slate-400'
                    }`}
                  >
                    {stage.label}
                  </p>
                  <p className="text-[10px] leading-normal text-slate-500 dark:text-slate-500 mt-0.5 max-w-[120px] mx-auto md:opacity-80 group-hover:opacity-100 transition-opacity">
                    {stage.description}
                  </p>
                </div>
              </div>

              {/* Connecting Arrow */}
              {idx < stages.length - 1 && (
                <div className="hidden md:block w-8 shrink-0 text-slate-300 dark:text-slate-800">
                  <ArrowRight className="h-4 w-4" />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Completion or active description */}
      <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-900 text-center">
        {currentStage === 'completed' ? (
          <div className="inline-flex items-center gap-2 bg-emerald-50 dark:bg-emerald-950/25 text-emerald-700 dark:text-emerald-400 px-4 py-2 rounded-full text-xs font-bold border border-emerald-100 dark:border-emerald-900/30">
            <CheckCircle className="h-4 w-4" />
            <span>Candidate Reshaped Successfully! Redirecting to Profiles...</span>
          </div>
        ) : isProcessing ? (
          <p className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 animate-pulse">
            Processing candidate records. Running step: <span className="underline uppercase">{currentStage}</span>...
          </p>
        ) : error ? (
          <div className="inline-flex items-center gap-2 bg-red-50 dark:bg-red-950/25 text-red-700 dark:text-red-400 px-4 py-2 rounded-full text-xs font-bold border border-red-100 dark:border-red-900/30">
            <AlertTriangle className="h-4 w-4" />
            <span>Pipeline error encountered: {error}</span>
          </div>
        ) : (
          <p className="text-xs text-slate-500 dark:text-slate-500 font-medium">
            Upload files and click "Run Pipeline" to visualize execution in real time.
          </p>
        )}
      </div>
    </div>
  );
}
