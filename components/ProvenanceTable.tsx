'use client';

import React, { useState, useMemo } from 'react';
import { ProvenanceRecord } from '../types';
import { Search, ArrowUpDown, ChevronDown, ChevronUp } from 'lucide-react';

interface ProvenanceTableProps {
  records: ProvenanceRecord[];
}

type SortKey = 'field' | 'source' | 'method' | 'confidence';
type SortOrder = 'asc' | 'desc';

export default function ProvenanceTable({ records }: ProvenanceTableProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('field');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('asc');
    }
  };

  // Filter and sort records
  const processedRecords = useMemo(() => {
    let result = [...records];

    // Search filter
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (rec) =>
          rec.field.toLowerCase().includes(q) ||
          rec.source.toLowerCase().includes(q) ||
          rec.method.toLowerCase().includes(q)
      );
    }

    // Sort
    result.sort((a, b) => {
      const valA = a[sortKey];
      const valB = b[sortKey];

      if (typeof valA === 'string' && typeof valB === 'string') {
        return sortOrder === 'asc' 
          ? valA.localeCompare(valB) 
          : valB.localeCompare(valA);
      }
      
      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortOrder === 'asc' 
          ? valA - valB 
          : valB - valA;
      }
      return 0;
    });

    return result;
  }, [records, searchQuery, sortKey, sortOrder]);

  const renderConfidenceBadge = (confidence: number) => {
    let color = 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/20 dark:text-red-400 dark:border-red-900/30';
    if (confidence >= 0.9) {
      color = 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-900/30';
    } else if (confidence >= 0.75) {
      color = 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/20 dark:text-amber-400 dark:border-amber-900/30';
    }

    return (
      <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${color} shadow-sm`}>
        {(confidence * 100).toFixed(0)}%
      </span>
    );
  };

  const SortIcon = ({ column }: { column: SortKey }) => {
    if (sortKey !== column) return <ArrowUpDown className="ml-2 h-3.5 w-3.5 shrink-0 opacity-40 hover:opacity-75 transition-opacity" />;
    return sortOrder === 'asc' 
      ? <ChevronUp className="ml-2 h-3.5 w-3.5 shrink-0 text-indigo-650 dark:text-indigo-400" />
      : <ChevronDown className="ml-2 h-3.5 w-3.5 shrink-0 text-indigo-650 dark:text-indigo-400" />;
  };

  return (
    <div className="w-full bg-card border border-border rounded-xl shadow-sm overflow-hidden transition-all duration-200">
      
      {/* 1. Header controls panel */}
      <div className="p-5 border-b border-border flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="space-y-1">
          <h3 className="text-sm font-bold text-foreground">
            Ingestion Provenance Trail
          </h3>
          <p className="text-xs text-muted-foreground leading-normal max-w-lg">
            Audit history explaining which source file, parser, and extraction method determined each field value.
          </p>
        </div>

        <div className="relative w-full sm:max-w-xs flex items-center">
          <Search className="absolute left-3 h-4 w-4 text-muted-foreground pointer-events-none" />
          <input
            type="text"
            placeholder="Search fields or sources..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs rounded-lg border border-border bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-primary transition-all duration-150"
          />
        </div>
      </div>

      {/* 2. Table viewport */}
      <div className="overflow-x-auto custom-scrollbar">
        <table className="w-full text-left border-collapse min-w-[600px]">
          <thead>
            <tr className="border-b border-border bg-muted/40 text-[10px] font-bold text-muted-foreground uppercase tracking-wider select-none">
              <th 
                onClick={() => handleSort('field')}
                className="px-6 py-4 cursor-pointer hover:bg-muted/80 hover:text-foreground transition-all duration-150"
              >
                <div className="flex items-center">
                  <span>Field Path</span>
                  <SortIcon column="field" />
                </div>
              </th>
              <th 
                onClick={() => handleSort('source')}
                className="px-6 py-4 cursor-pointer hover:bg-muted/80 hover:text-foreground transition-all duration-150"
              >
                <div className="flex items-center">
                  <span>Original Source</span>
                  <SortIcon column="source" />
                </div>
              </th>
              <th 
                onClick={() => handleSort('method')}
                className="px-6 py-4 cursor-pointer hover:bg-muted/80 hover:text-foreground transition-all duration-150"
              >
                <div className="flex items-center">
                  <span>Extraction Method</span>
                  <SortIcon column="method" />
                </div>
              </th>
              <th 
                onClick={() => handleSort('confidence')}
                className="px-6 py-4 cursor-pointer hover:bg-muted/80 hover:text-foreground transition-all duration-150 text-right"
              >
                <div className="flex items-center justify-end">
                  <span>Confidence Score</span>
                  <SortIcon column="confidence" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {processedRecords.length > 0 ? (
              processedRecords.map((rec, index) => (
                <tr 
                  key={index}
                  className="hover:bg-muted/15 transition-colors duration-150"
                >
                  <td className="px-6 py-4 text-xs font-semibold text-foreground font-mono">
                    {rec.field}
                  </td>
                  <td className="px-6 py-4 text-xs text-muted-foreground truncate max-w-[200px]" title={rec.source}>
                    {rec.source}
                  </td>
                  <td className="px-6 py-4 text-xs">
                    <span className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 font-semibold text-muted-foreground border border-border/50">
                      {rec.method}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-xs text-right">
                    {renderConfidenceBadge(rec.confidence)}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} className="px-6 py-12 text-center text-xs text-muted-foreground font-medium">
                  {searchQuery ? 'No provenance records matched your search query.' : 'No provenance records loaded.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
