'use client';

import React, { useState } from 'react';
import { Copy, Check, Download, Search, ChevronRight, ChevronDown } from 'lucide-react';

interface JsonViewerProps {
  data: any;
  filename?: string;
}

export default function JsonViewer({ data, filename = 'candidate_profile.json' }: JsonViewerProps) {
  const [copied, setCopied] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [collapsedPaths, setCollapsedPaths] = useState<Record<string, boolean>>({});

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const toggleCollapse = (path: string) => {
    setCollapsedPaths((prev) => ({
      ...prev,
      [path]: !prev[path]
    }));
  };

  const shouldHighlight = (text: string) => {
    if (!searchQuery) return false;
    return text.toLowerCase().includes(searchQuery.toLowerCase());
  };

  const HighlightedText = ({ text, className = '' }: { text: string; className?: string }) => {
    if (!shouldHighlight(text)) return <span className={className}>{text}</span>;
    
    const index = text.toLowerCase().indexOf(searchQuery.toLowerCase());
    const length = searchQuery.length;
    
    return (
      <span className={className}>
        {text.substring(0, index)}
        <mark className="bg-amber-400/30 text-white font-semibold rounded px-0.5 border border-amber-500/20">
          {text.substring(index, index + length)}
        </mark>
        {text.substring(index + length)}
      </span>
    );
  };

  const renderConfidenceBadge = (value: number) => {
    let color = 'bg-red-500/10 text-red-400 border-red-500/20';
    if (value >= 0.9) {
      color = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    } else if (value >= 0.75) {
      color = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    }

    return (
      <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[9px] font-bold border ${color} font-sans ml-2 select-none shadow-sm`}>
        {(value * 100).toFixed(0)}% Confidence
      </span>
    );
  };

  const renderNode = (node: any, path: string = 'root', indent: number = 0): React.ReactNode => {
    const isCollapsed = collapsedPaths[path];

    if (node === null) {
      return (
        <span className="text-slate-500 font-mono text-xs select-all">
          null
        </span>
      );
    }

    if (typeof node === 'boolean') {
      return (
        <span className="text-pink-400 font-mono text-xs font-bold select-all">
          {node.toString()}
        </span>
      );
    }

    if (typeof node === 'number') {
      const isConfidenceField = path.endsWith('confidence') || path.endsWith('overall_confidence');
      return (
        <div className="inline-flex items-center">
          <span className="text-amber-400 font-mono text-xs font-bold select-all">
            {node}
          </span>
          {isConfidenceField && renderConfidenceBadge(node)}
        </div>
      );
    }

    if (typeof node === 'string') {
      return (
        <span className="text-emerald-400 font-mono text-xs break-all select-all font-semibold">
          "<HighlightedText text={node} />"
        </span>
      );
    }

    if (Array.isArray(node)) {
      if (node.length === 0) return <span className="text-slate-400 font-mono text-xs">[]</span>;

      return (
        <div className="flex flex-col font-mono text-xs">
          <button
            onClick={() => toggleCollapse(path)}
            className="flex items-center text-slate-400 hover:text-white transition-colors focus:outline-none w-fit cursor-pointer select-none"
          >
            {isCollapsed ? (
              <ChevronRight className="h-3 w-3 mr-1 text-slate-500 shrink-0" />
            ) : (
              <ChevronDown className="h-3 w-3 mr-1 text-slate-500 shrink-0" />
            )}
            <span className="text-slate-400">Array({node.length}) [</span>
          </button>

          {!isCollapsed && (
            <div className="pl-4 border-l border-slate-800 ml-1.5 mt-1 space-y-1 bg-slate-900/10">
              {node.map((item, idx) => (
                <div key={idx} className="flex items-start">
                  <span className="text-slate-600 mr-2 select-none">{idx}:</span>
                  <div className="flex-1">
                    {renderNode(item, `${path}[${idx}]`, indent + 1)}
                  </div>
                </div>
              ))}
            </div>
          )}

          {!isCollapsed && <span className="text-slate-400 mt-0.5">]</span>}
          {isCollapsed && <span className="text-slate-500 pl-4 font-normal">... ]</span>}
        </div>
      );
    }

    if (typeof node === 'object') {
      const keys = Object.keys(node);
      if (keys.length === 0) return <span className="text-slate-400 font-mono text-xs">{"{}"}</span>;

      return (
        <div className="flex flex-col font-mono text-xs">
          <button
            onClick={() => toggleCollapse(path)}
            className="flex items-center text-slate-400 hover:text-white transition-colors focus:outline-none w-fit cursor-pointer select-none"
          >
            {isCollapsed ? (
              <ChevronRight className="h-3 w-3 mr-1 text-slate-500 shrink-0" />
            ) : (
              <ChevronDown className="h-3 w-3 mr-1 text-slate-500 shrink-0" />
            )}
            <span className="text-slate-400">Object{" {"}</span>
          </button>

          {!isCollapsed && (
            <div className="pl-4 border-l border-slate-800/80 ml-1.5 mt-1 space-y-1 bg-slate-900/10">
              {keys.map((key) => (
                <div key={key} className="flex items-start gap-1">
                  <span className="text-indigo-400 font-semibold select-all shrink-0">
                    <HighlightedText text={key} />
                  </span>
                  <span className="text-slate-600 shrink-0">:</span>
                  <div className="flex-1">
                    {renderNode(node[key], `${path}.${key}`, indent + 1)}
                  </div>
                </div>
              ))}
            </div>
          )}

          {!isCollapsed && <span className="text-slate-400 mt-0.5">{"}"}</span>}
          {isCollapsed && <span className="text-slate-500 pl-4 font-normal">... {"}"}</span>}
        </div>
      );
    }

    return null;
  };

  return (
    <div className="w-full flex flex-col border border-border/80 dark:border-slate-800 rounded-2xl bg-slate-950 text-slate-100 overflow-hidden shadow-md">
      
      {/* 1. Header controls bar */}
      <div className="flex items-center justify-between border-b border-slate-900 px-4.5 py-3 bg-slate-900/80 shrink-0">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="inline-flex h-2 w-2 rounded-full bg-indigo-500 shadow-glow" />
          <span className="text-xs font-semibold text-slate-300 font-mono truncate max-w-[160px] sm:max-w-[220px]" title={filename}>
            {filename}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Grep search filter */}
          <div className="relative flex items-center">
            <Search className="absolute left-2.5 h-3.5 w-3.5 text-slate-500 pointer-events-none" />
            <input
              type="text"
              placeholder="Search data..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-800 bg-slate-950 text-slate-100 focus:outline-none focus:border-slate-700 placeholder-slate-600 w-[120px] sm:w-[150px] transition-all"
            />
          </div>

          {/* Copy button */}
          <button
            onClick={handleCopy}
            className="p-1.5 rounded-lg hover:bg-slate-800 border border-slate-900/60 hover:border-slate-750 text-slate-400 hover:text-white transition-all focus:outline-none cursor-pointer"
            title="Copy JSON Profile"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
          </button>

          {/* Download button */}
          <button
            onClick={handleDownload}
            className="p-1.5 rounded-lg hover:bg-slate-800 border border-slate-900/60 hover:border-slate-750 text-slate-400 hover:text-white transition-all focus:outline-none cursor-pointer"
            title="Download JSON File"
          >
            <Download className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* 2. Visual tree viewport */}
      <div className="p-5 overflow-auto max-h-[520px] bg-slate-950/70 custom-scrollbar select-text text-left">
        {data ? (
          <div className="space-y-1">
            {renderNode(data)}
          </div>
        ) : (
          <div className="text-center py-12 text-slate-600 font-mono text-xs select-none">
            No profile data loaded. Execute candidate pipeline first.
          </div>
        )}
      </div>
    </div>
  );
}
