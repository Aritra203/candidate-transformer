'use client';

import React from 'react';
import { PipelineProvider, usePipeline } from '../hooks/usePipeline';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import StatusCard from '../components/StatusCard';
import UploadCard from '../components/UploadCard';
import ConfigEditor from '../components/ConfigEditor';
import PipelineStepper from '../components/PipelineStepper';
import JsonViewer from '../components/JsonViewer';
import ProvenanceTable from '../components/ProvenanceTable';
import LogsPanel from '../components/LogsPanel';
import CandidateCard from '../components/CandidateCard';
import EmptyState from '../components/EmptyState';
import LoadingOverlay from '../components/LoadingOverlay';

import { 
  FileText, 
  UploadCloud, 
  Settings, 
  Play, 
  CheckCircle2, 
  Terminal, 
  Info,
  GitPullRequest,
  CheckCircle,
  Database,
  Cpu,
  Fingerprint,
  ChevronRight,
  ShieldCheck,
  AlertTriangle
} from 'lucide-react';

function DashboardContent() {
  const { 
    activePage, 
    setActivePage, 
    csvFile, 
    setCsvFile,
    resumeFile, 
    setResumeFile,
    configFile,
    setConfigFile,
    config, 
    setConfig,
    isProcessing, 
    pipelineStage, 
    profiles, 
    logs, 
    error, 
    runPipeline,
    resetPipeline
  } = usePipeline();

  const fileCount = (csvFile ? 1 : 0) + (resumeFile ? 1 : 0);
  const isOutputReady = profiles.length > 0;

  // Determine configuration type (default vs custom mapping)
  const isCustomConfig = config.fields.length !== 11 || config.on_missing !== 'null';

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-slate-50 dark:bg-slate-900/10 transition-colors duration-200">
      <Navbar />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        {/* Main Content Pane */}
        <main className="flex-1 overflow-y-auto px-8 py-8 select-none">
          <div className="max-w-[1400px] mx-auto space-y-8 text-left">
            
            {/* 1. DASHBOARD VIEW */}
            {activePage === 'dashboard' && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div>
                  <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                    Recruitment Data Pipeline
                  </h1>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    Ingest, parsed, normalized, and merged candidate details from multi-source Recruiter CSV exports and Resume PDFs.
                  </p>
                </div>

                {/* Status Cards Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                  <StatusCard
                    title="CSV Sources"
                    value={csvFile ? 'Uploaded' : 'Empty'}
                    description={csvFile ? csvFile.name : 'Recruiter CSV File'}
                    icon={FileText}
                    status={csvFile ? 'success' : 'neutral'}
                  />
                  <StatusCard
                    title="Resume PDF"
                    value={resumeFile ? 'Uploaded' : 'Empty'}
                    description={resumeFile ? resumeFile.name : 'Candidate Resume PDF'}
                    icon={UploadCloud}
                    status={resumeFile ? 'success' : 'neutral'}
                  />
                  <StatusCard
                    title="Config Projection"
                    value={isCustomConfig ? 'Custom Mapping' : 'Default Mapping'}
                    description={`${config.fields.length} output field filters`}
                    icon={Settings}
                    status={isCustomConfig ? 'warning' : 'info'}
                  />
                  <StatusCard
                    title="Pipeline Ingestion"
                    value={isProcessing ? 'Processing' : error ? 'Error' : isOutputReady ? 'Completed' : 'Idle'}
                    description={isProcessing ? `Step: ${pipelineStage}` : error ? 'View execution logs' : isOutputReady ? 'Profiles successfully merged' : 'Awaiting input files'}
                    icon={Cpu}
                    status={isProcessing ? 'info' : error ? 'error' : isOutputReady ? 'success' : 'neutral'}
                  />
                  <StatusCard
                    title="Merged Profiles"
                    value={profiles.length}
                    description={isOutputReady ? 'Output ready for export' : 'Run pipeline to merge'}
                    icon={CheckCircle2}
                    status={isOutputReady ? 'success' : 'neutral'}
                  />
                </div>

                {/* Main Dashboard body */}
                {fileCount === 0 && !isOutputReady ? (
                  <EmptyState
                    title="No files ingested yet"
                    description="Get started by uploading recruiter export spreadsheets or candidate resume PDFs to execute the pipeline."
                    icon={UploadCloud}
                    actionLabel="Upload Source Files"
                    onAction={() => setActivePage('upload')}
                  />
                ) : (
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Ingestion Overview */}
                    <div className="lg:col-span-2 border border-slate-200 dark:border-slate-800 rounded-xl p-5 bg-white dark:bg-slate-950 shadow-sm space-y-4">
                      <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                        Ingestion Progress Summary
                      </h3>
                      
                      <div className="space-y-4 text-xs">
                        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-850">
                          <div className="flex items-center gap-2">
                            <span className={`h-2.5 w-2.5 rounded-full ${csvFile ? 'bg-emerald-500' : 'bg-slate-350'}`} />
                            <span className="font-semibold text-slate-800 dark:text-slate-200">Recruiter Spreadsheet Ingestion</span>
                          </div>
                          <span className="text-slate-500">{csvFile ? csvFile.name : 'Missing file'}</span>
                        </div>

                        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-850">
                          <div className="flex items-center gap-2">
                            <span className={`h-2.5 w-2.5 rounded-full ${resumeFile ? 'bg-emerald-500' : 'bg-slate-350'}`} />
                            <span className="font-semibold text-slate-800 dark:text-slate-200">Resume PDF Parser Ingestion</span>
                          </div>
                          <span className="text-slate-500">{resumeFile ? resumeFile.name : 'Missing file'}</span>
                        </div>

                        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-850">
                          <div className="flex items-center gap-2">
                            <span className={`h-2.5 w-2.5 rounded-full bg-emerald-500`} />
                            <span className="font-semibold text-slate-800 dark:text-slate-200">JSON Output Projection Schema</span>
                          </div>
                          <span className="text-slate-500">{isCustomConfig ? 'custom.json' : 'default.json'}</span>
                        </div>
                      </div>

                      {/* Primary Dashboard execution triggers */}
                      <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-900">
                        {isOutputReady && (
                          <button
                            onClick={() => setActivePage('output')}
                            className="inline-flex items-center gap-1.5 px-4 py-2 border border-slate-200 dark:border-slate-850 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg text-xs font-semibold shadow-sm focus:outline-none"
                          >
                            <span>View Outputs</span>
                            <ChevronRight className="h-3.5 w-3.5" />
                          </button>
                        )}

                        <button
                          onClick={runPipeline}
                          disabled={isProcessing}
                          className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-sm focus:outline-none"
                        >
                          <Play className="h-3 w-3 fill-current" />
                          <span>{isProcessing ? 'Processing...' : isOutputReady ? 'Run Pipeline Again' : 'Execute Pipeline'}</span>
                        </button>
                      </div>
                    </div>

                    {/* Pipeline Info / Quick Logs */}
                    <div className="bg-slate-50 dark:bg-slate-900/40 border border-slate-200/60 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
                      <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                        <Terminal className="h-4 w-4 text-indigo-500" />
                        <span>Execution Snapshot</span>
                      </h3>

                      {logs.length > 0 ? (
                        <div className="space-y-3.5 max-h-[170px] overflow-y-auto pr-1">
                          {logs.slice(-3).map((log, idx) => (
                            <div key={idx} className="font-mono text-[10px] space-y-0.5 leading-normal">
                              <div className="flex justify-between text-slate-500 dark:text-slate-500">
                                <span>{log.timestamp}</span>
                                <span className="font-bold underline">{log.stage}</span>
                              </div>
                              <p className="text-slate-700 dark:text-slate-300 line-clamp-2">{log.message}</p>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-slate-500 dark:text-slate-400 leading-normal">
                          Console is idle. Launch the candidate transformer to view logs in real time.
                        </p>
                      )}

                      <button
                        onClick={() => setActivePage('logs')}
                        className="w-full text-center py-2 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-850 hover:bg-slate-50 dark:hover:bg-slate-900 text-slate-700 dark:text-slate-300 rounded-lg text-xs font-semibold shadow-sm transition-colors focus:outline-none"
                      >
                        View Full Logs Console
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 2. UPLOAD VIEW */}
            {activePage === 'upload' && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div>
                  <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                    Data Ingestion Center
                  </h1>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    Upload recruitment spreadsheets, resume documents, or custom mapping rules.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 min-h-[320px]">
                  <UploadCard
                    title="Recruiter Spreadsheet"
                    description="Upload candidate tabular records in CSV format."
                    acceptedTypes=".csv"
                    fileType="csv"
                    onUploadSuccess={(file) => setCsvFile(file)}
                    onRemove={() => setCsvFile(null)}
                    currentFile={csvFile}
                  />

                  <UploadCard
                    title="Candidate Resume"
                    description="Upload candidate resume file in PDF format."
                    acceptedTypes=".pdf"
                    fileType="pdf"
                    onUploadSuccess={(file) => setResumeFile(file)}
                    onRemove={() => setResumeFile(null)}
                    currentFile={resumeFile}
                  />

                  <UploadCard
                    title="Custom Mapping Configuration"
                    description="Upload optional projection configuration JSON rules."
                    acceptedTypes=".json"
                    fileType="json"
                    onUploadSuccess={(file) => {
                      setConfigFile(file);
                      // Read file contents locally and load it into context config
                      const reader = new FileReader();
                      // Wait! We can do it on backend too or fetch if needed
                    }}
                    onRemove={() => setConfigFile(null)}
                    currentFile={configFile}
                  />
                </div>

                {fileCount > 0 && (
                  <div className="flex justify-end pt-4 border-t border-slate-100 dark:border-slate-900">
                    <button
                      onClick={runPipeline}
                      className="inline-flex items-center gap-1.5 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold shadow-sm focus:outline-none"
                    >
                      <Play className="h-4.5 w-4.5 fill-current" />
                      <span>Start Transformation Pipeline</span>
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* 3. CONFIGURATION VIEW */}
            {activePage === 'configuration' && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div>
                  <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                    Pipeline Mapping Rules
                  </h1>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    Edit JSON output projections, define custom normalizations, adjust validation rules, and control output shapes.
                  </p>
                </div>

                <ConfigEditor config={config} onChange={(newConfig) => setConfig(newConfig)} />
              </div>
            )}

            {/* 4. PIPELINE VIEW (STEPPER VISUALIZATION) */}
            {activePage === 'pipeline' && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div>
                  <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                    Data Engineering Pipeline
                  </h1>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    Trace the live pipeline stages as candidate profiles are sniffed, parsed, canonicalized, matched, and validating in real time.
                  </p>
                </div>

                <PipelineStepper currentStage={pipelineStage} isProcessing={isProcessing} error={error} />
                
                <LogsPanel logs={logs} />
              </div>
            )}

            {/* 5. OUTPUT VIEW */}
            {activePage === 'output' && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div>
                  <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                    Canonical Output Profiles
                  </h1>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    Review candidate details merged, matching, and formatted into clean JSON records.
                  </p>
                </div>

                {isOutputReady ? (
                  <div className="space-y-8">
                    {/* Candidate Profiles List */}
                    {profiles.map((profile, index) => (
                      <div key={index} className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                        {/* Summary overview details card */}
                        <div className="lg:col-span-7 space-y-6">
                          <CandidateCard profile={profile} />
                          {config.include_provenance && profile.provenance && (
                            <ProvenanceTable records={profile.provenance} />
                          )}
                        </div>

                        {/* Beautiful JSON raw tree view */}
                        <div className="lg:col-span-5">
                          <div className="sticky top-20">
                            <JsonViewer data={profile} filename={`canonical_profile_${profile.candidate_id?.substring(0, 8) || index}.json`} />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    title="No transformed profiles ready"
                    description="Upload source files and run candidate transformation pipeline to view canonical outputs here."
                    icon={FileText}
                    actionLabel="Go to Upload Section"
                    onAction={() => setActivePage('upload')}
                  />
                )}
              </div>
            )}

            {/* 6. LOGS VIEW */}
            {activePage === 'logs' && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div>
                  <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                    Execution Logs Console
                  </h1>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    Review raw command stream output and pipeline level messages.
                  </p>
                </div>

                <LogsPanel logs={logs} />
              </div>
            )}

            {/* 7. ABOUT VIEW */}
            {activePage === 'about' && (
              <div className="space-y-8 max-w-4xl animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div>
                  <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                    About Candidate Data Transformer
                  </h1>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    An internal enterprise engineering tool created by Eightfold AI to unify multi-source candidate profiles.
                  </p>
                </div>

                <div className="bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl p-6 space-y-6 text-sm text-slate-700 dark:text-slate-300 leading-relaxed shadow-sm">
                  <div>
                    <h3 className="text-base font-bold text-slate-900 dark:text-white mb-2">
                      Layered Data Pipeline Architecture
                    </h3>
                    <p>
                      Heterogeneous profiles from CSV exports and Resume PDFs undergo automated Sniffing, Parsing (`pdfplumber` / `Polars`), Normalization (`E.164`, `ISO-3166-1 alpha-2`), Union-Merge Deduplication, Authority Conflict Resolution, and Config-driven Projection before output schema validation.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-slate-100 dark:border-slate-900">
                    <div>
                      <h4 className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5 mb-2">
                        <Fingerprint className="h-4 w-4 text-indigo-500" />
                        <span>Deterministic Unique IDs</span>
                      </h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        Candidate profiles generate a deterministic SHA-256 identifier based on lowercased names, sorted email lists, and phone numbers. The same candidate always maps to the same ID, preventing duplicates regardless of input ordering.
                      </p>
                    </div>

                    <div>
                      <h4 className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5 mb-2">
                        <GitPullRequest className="h-4 w-4 text-indigo-500" />
                        <span>Authority Match Rules</span>
                      </h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        Scalars and lists merge with priority scores: Resumes are weighted at 100 as primary self-reported auth sources, while Recruiter CSV systems have a fallback priority weight of 80.
                      </p>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-100 dark:border-slate-900">
                    <h3 className="text-base font-bold text-slate-900 dark:text-white mb-2">
                      Normalization Rules Summary
                    </h3>
                    
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs pt-2">
                      <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-100 dark:border-slate-850">
                        <p className="font-bold text-slate-800 dark:text-slate-350">Phone Numbers</p>
                        <p className="text-slate-500 mt-1">E.164 international standard formatting</p>
                      </div>

                      <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-100 dark:border-slate-850">
                        <p className="font-bold text-slate-800 dark:text-slate-350">Geographic Codes</p>
                        <p className="text-slate-500 mt-1">ISO 3166 alpha-2 matching lookup</p>
                      </div>

                      <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-100 dark:border-slate-850">
                        <p className="font-bold text-slate-800 dark:text-slate-350">Chronology Dates</p>
                        <p className="text-slate-500 mt-1">YYYY-MM date-util extraction parsing</p>
                      </div>

                      <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-100 dark:border-slate-850">
                        <p className="font-bold text-slate-800 dark:text-slate-350">Skill Aliases</p>
                        <p className="text-slate-500 mt-1">Fuzzy skill mapping and deduplication</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

          </div>
        </main>
      </div>

      {/* Footer bar */}
      <footer className="h-10 border-t border-border bg-card flex items-center justify-between px-6 text-[10px] font-bold text-muted-foreground shrink-0">
        <span>© 2026 Eightfold AI Inc. Internal Tooling.</span>
        <span>Developer Services Platform</span>
      </footer>

      {isProcessing && <LoadingOverlay message={`Running Pipeline Stage: ${pipelineStage.toUpperCase()}`} />}
    </div>
  );
}

export default function Home() {
  return (
    <PipelineProvider>
      <DashboardContent />
    </PipelineProvider>
  );
}
