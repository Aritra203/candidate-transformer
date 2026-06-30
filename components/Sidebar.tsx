'use client';

import React from 'react';
import { usePipeline } from '../hooks/usePipeline';
import { ActivePage } from '../types';
import { 
  LayoutDashboard, 
  UploadCloud, 
  Sliders, 
  FileJson, 
  Terminal, 
  Info,
  Play,
  RotateCcw
} from 'lucide-react';

interface MenuItem {
  id: ActivePage;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

export default function Sidebar() {
  const { 
    activePage, 
    setActivePage, 
    csvFile, 
    resumeFile, 
    profiles, 
    runPipeline, 
    resetPipeline,
    isProcessing 
  } = usePipeline();

  const menuItems: MenuItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'upload', label: 'Upload Files', icon: UploadCloud },
    { id: 'configuration', label: 'Configuration', icon: Sliders },
    { id: 'output', label: 'Output Profile', icon: FileJson },
    { id: 'logs', label: 'Execution Logs', icon: Terminal },
    { id: 'about', label: 'About Project', icon: Info },
  ];

  const fileCount = (csvFile ? 1 : 0) + (resumeFile ? 1 : 0);
  const isOutputReady = profiles.length > 0;

  return (
    <aside className="w-64 border-r border-border bg-card/45 flex flex-col h-full transition-all duration-200 select-none">
      
      {/* List items navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto custom-scrollbar">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setActivePage(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all duration-150 cursor-pointer ${
                isActive
                  ? 'bg-primary/10 text-primary shadow-xs border border-primary/10'
                  : 'text-muted-foreground border border-transparent hover:bg-muted/70 hover:text-foreground'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`h-4.5 w-4.5 ${isActive ? 'text-primary' : 'text-slate-450'}`} />
                <span>{item.label}</span>
              </div>
              
              {/* Badge metrics indicators */}
              {item.id === 'upload' && fileCount > 0 && (
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/15 text-[10px] font-bold text-primary border border-primary/10">
                  {fileCount}
                </span>
              )}

              {item.id === 'output' && isOutputReady && (
                <span className="inline-flex items-center rounded-full bg-emerald-500/10 text-[9px] font-bold px-2 py-0.5 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400">
                  Ready
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Action buttons (Execute / Reset) */}
      <div className="p-4 border-t border-border bg-muted/10 space-y-2">
        <button
          onClick={runPipeline}
          disabled={isProcessing || (!csvFile && !resumeFile)}
          className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all duration-150 cursor-pointer ${
            isProcessing || (!csvFile && !resumeFile)
              ? 'bg-muted text-muted-foreground/60 cursor-not-allowed opacity-60 border border-border/50'
              : 'bg-primary text-primary-foreground hover:bg-primary/90 active:bg-primary/95 shadow-sm hover:shadow'
          }`}
        >
          <Play className="h-3.5 w-3.5 fill-current" />
          <span>{isProcessing ? 'Processing...' : 'Run Pipeline'}</span>
        </button>

        <button
          onClick={resetPipeline}
          disabled={isProcessing || (!csvFile && !resumeFile && !isOutputReady)}
          className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold border border-border transition-all duration-150 cursor-pointer ${
            isProcessing || (!csvFile && !resumeFile && !isOutputReady)
              ? 'text-muted-foreground/40 border-border/60 cursor-not-allowed bg-transparent'
              : 'text-foreground bg-card hover:bg-muted/70 hover:border-slate-350 dark:hover:border-slate-700'
          }`}
        >
          <RotateCcw className="h-3.5 w-3.5" />
          <span>Reset All</span>
        </button>
      </div>
    </aside>
  );
}
