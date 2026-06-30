'use client';

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { LogEntry } from '../types';
import { Terminal, ShieldAlert, CheckCircle, HelpCircle, ArrowDown } from 'lucide-react';

interface LogsPanelProps {
  logs: LogEntry[];
}

export default function LogsPanel({ logs }: LogsPanelProps) {
  const [filterLevel, setFilterLevel] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const terminalEndRef = useRef<HTMLDivElement>(null);
  const terminalBodyRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when logs update
  useEffect(() => {
    if (autoScroll && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  // Handle scroll detection to disable/enable autoScroll
  const handleScroll = () => {
    if (!terminalBodyRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = terminalBodyRef.current;
    // If user scrolled up by more than 30px, disable autoScroll
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 30;
    setAutoScroll(isAtBottom);
  };

  // Filter logs
  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      // Level check
      if (filterLevel !== 'ALL' && log.level !== filterLevel) {
        return false;
      }
      // Search check
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        return (
          log.message.toLowerCase().includes(q) ||
          log.stage.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [logs, filterLevel, searchQuery]);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR':
        return 'text-red-400';
      case 'WARNING':
        return 'text-yellow-400';
      case 'SUCCESS':
        return 'text-emerald-400';
      case 'DEBUG':
        return 'text-slate-500';
      default:
        return 'text-sky-400'; // INFO
    }
  };

  const getStageColor = (stage: string) => {
    const s = stage.toLowerCase();
    if (s.includes('parser') || s.includes('csv') || s.includes('pdf')) return 'text-indigo-400';
    if (s.includes('normalizer')) return 'text-pink-400';
    if (s.includes('merger')) return 'text-teal-400';
    if (s.includes('confidence')) return 'text-amber-400';
    if (s.includes('projection')) return 'text-purple-400';
    if (s.includes('validator') || s.includes('validation')) return 'text-emerald-400';
    return 'text-slate-400';
  };

  return (
    <div className="w-full flex flex-col h-[550px] bg-slate-950 border border-slate-900 rounded-xl overflow-hidden shadow-2xl font-mono text-xs text-slate-300">
      {/* Terminal Title Bar */}
      <div className="flex items-center justify-between border-b border-slate-900 px-4 py-3 bg-slate-900/60 shrink-0">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-indigo-400" />
          <span className="font-semibold text-slate-200">transformer-pipeline-console</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-full bg-red-500/80" />
          <span className="h-3 w-3 rounded-full bg-yellow-500/80" />
          <span className="h-3 w-3 rounded-full bg-green-500/80" />
        </div>
      </div>

      {/* Terminal Controls Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-4 py-3 bg-slate-900/20 border-b border-slate-900 shrink-0">
        {/* Level Filters */}
        <div className="flex items-center gap-1 bg-slate-950 p-0.5 rounded-lg border border-slate-900 w-full sm:w-auto overflow-x-auto scrollbar-none">
          {['ALL', 'INFO', 'SUCCESS', 'WARNING', 'ERROR'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setFilterLevel(lvl)}
              className={`px-2.5 py-1 rounded-md text-[10px] font-bold transition-all focus:outline-none shrink-0 ${
                filterLevel === lvl
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>

        {/* Text Filter */}
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <input
            type="text"
            placeholder="Grep messages..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full sm:w-[180px] bg-slate-950 border border-slate-900 rounded-lg px-2.5 py-1.5 text-[11px] text-slate-300 placeholder-slate-600 focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600"
          />

          {!autoScroll && logs.length > 0 && (
            <button
              onClick={() => setAutoScroll(true)}
              className="flex items-center gap-1 bg-indigo-950 border border-indigo-800 text-indigo-400 hover:text-indigo-300 px-2 py-1.5 rounded-lg text-[10px] font-bold transition-colors shrink-0"
            >
              <ArrowDown className="h-3 w-3 animate-bounce" />
              <span>Scroll Lock</span>
            </button>
          )}
        </div>
      </div>

      {/* Log Output Stream */}
      <div 
        ref={terminalBodyRef}
        onScroll={handleScroll}
        className="flex-1 p-4 overflow-y-auto space-y-1.5 scrollbar-thin select-text"
      >
        {filteredLogs.length > 0 ? (
          filteredLogs.map((log, idx) => (
            <div key={idx} className="flex items-start gap-3 hover:bg-slate-900/35 py-0.5 px-1 rounded transition-colors group">
              {/* Timestamp */}
              <span className="text-slate-600 select-none font-semibold shrink-0 group-hover:text-slate-500">
                {log.timestamp}
              </span>

              {/* Level indicator */}
              <span className={`font-semibold shrink-0 select-none min-w-[50px] ${getLevelColor(log.level)}`}>
                [{log.level}]
              </span>

              {/* Stage indicator */}
              <span className={`shrink-0 select-none min-w-[80px] font-medium ${getStageColor(log.stage)}`}>
                {log.stage}
              </span>

              {/* Message */}
              <span className="text-slate-300 break-words flex-1 group-hover:text-white leading-relaxed">
                {log.message}
              </span>
            </div>
          ))
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-slate-600 select-none">
            <Terminal className="h-10 w-10 text-slate-800 shrink-0 mb-2" />
            <p className="text-xs">
              {logs.length === 0 
                ? 'Console is idle. Run transformation pipeline to capture execution logs.' 
                : 'No logs matched the filters.'}
            </p>
          </div>
        )}
        <div ref={terminalEndRef} />
      </div>
    </div>
  );
}
