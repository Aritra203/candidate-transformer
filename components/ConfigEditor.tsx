'use client';

import React, { useState, useEffect } from 'react';
import { ProjectionConfig, FieldProjection } from '../types';
import { apiService } from '../services/api';
import { 
  Sliders, 
  Code2, 
  CheckCircle, 
  AlertTriangle, 
  Plus, 
  Trash2, 
  Info,
  Sparkles,
  ShieldCheck
} from 'lucide-react';

interface ConfigEditorProps {
  config: ProjectionConfig;
  onChange: (config: ProjectionConfig) => void;
}

export default function ConfigEditor({ config, onChange }: ConfigEditorProps) {
  const [activeTab, setActiveTab] = useState<'visual' | 'json'>('visual');
  const [jsonText, setJsonText] = useState(JSON.stringify(config, null, 2));
  const [validationResult, setValidationResult] = useState<{
    status: 'idle' | 'valid' | 'invalid';
    message: string;
    errors?: any[];
  }>({ status: 'idle', message: '' });

  // Keep JSON string in sync when config changes from external/parent
  useEffect(() => {
    setJsonText(JSON.stringify(config, null, 2));
  }, [config]);

  // Handle changes in Visual Form editor
  const updateConfigField = (updater: (prev: ProjectionConfig) => ProjectionConfig) => {
    const updated = updater(config);
    onChange(updated);
    setJsonText(JSON.stringify(updated, null, 2));
    setValidationResult({ status: 'idle', message: '' });
  };

  // Add field projection
  const addField = () => {
    updateConfigField((prev) => ({
      ...prev,
      fields: [...prev.fields, { path: 'new_field', from: '', type: 'string', required: false }]
    }));
  };

  // Remove field projection
  const removeField = (index: number) => {
    updateConfigField((prev) => {
      const fields = [...prev.fields];
      fields.splice(index, 1);
      return { ...prev, fields };
    });
  };

  // Modify individual field property
  const modifyField = (index: number, key: keyof FieldProjection, value: any) => {
    updateConfigField((prev) => {
      const fields = [...prev.fields];
      fields[index] = {
        ...fields[index],
        [key]: value === '' ? undefined : value
      };
      return { ...prev, fields };
    });
  };

  // Handle raw JSON manual editing
  const handleJsonChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    setJsonText(text);
    setValidationResult({ status: 'idle', message: '' });

    try {
      const parsed = JSON.parse(text);
      // Validate schema has 'fields' array
      if (parsed && Array.isArray(parsed.fields)) {
        onChange(parsed);
      }
    } catch {
      // Don't propagate changes if JSON syntax is invalid
    }
  };

  // Format code in editor
  const formatJson = () => {
    try {
      const parsed = JSON.parse(jsonText);
      setJsonText(JSON.stringify(parsed, null, 2));
    } catch {
      setValidationResult({ status: 'invalid', message: 'Cannot format: JSON is invalid' });
    }
  };

  // Trigger backend JSON schema validation
  const validateConfig = async () => {
    let currentConfig: any;
    try {
      currentConfig = JSON.parse(jsonText);
    } catch (err: any) {
      setValidationResult({
        status: 'invalid',
        message: `JSON syntax error: ${err.message}`
      });
      return;
    }

    try {
      const res = await apiService.validateConfig(currentConfig);
      if (res.valid) {
        setValidationResult({
          status: 'valid',
          message: 'Success: JSON is valid and matches backend schema requirements.'
        });
      } else {
        setValidationResult({
          status: 'invalid',
          message: res.message,
          errors: res.errors
        });
      }
    } catch (err: any) {
      setValidationResult({
        status: 'invalid',
        message: err.message || 'Validation request failed.'
      });
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Editor Main body */}
      <div className="lg:col-span-8 bg-white dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden flex flex-col h-[580px]">
        {/* Toggle tabs bar */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30">
          <div className="flex items-center gap-2">
            <Sliders className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            <span className="text-sm font-semibold text-slate-900 dark:text-white">Projection Rules</span>
          </div>

          <div className="flex items-center bg-slate-100 dark:bg-slate-900 p-0.5 rounded-lg border border-slate-200/50 dark:border-slate-850">
            <button
              onClick={() => setActiveTab('visual')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold transition-all focus:outline-none ${
                activeTab === 'visual'
                  ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <Sliders className="h-3 w-3" />
              <span>GUI Builder</span>
            </button>
            <button
              onClick={() => setActiveTab('json')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold transition-all focus:outline-none ${
                activeTab === 'json'
                  ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <Code2 className="h-3 w-3" />
              <span>JSON Code</span>
            </button>
          </div>
        </div>

        {/* Dynamic viewport */}
        <div className="flex-1 overflow-y-auto p-5">
          {activeTab === 'visual' ? (
            /* Visual Builder Page */
            <div className="space-y-6">
              {/* Top controls */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-xl border border-slate-100 dark:border-slate-900 bg-slate-50/50 dark:bg-slate-900/10">
                <div>
                  <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                    Confidence Badge
                  </label>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="include_confidence"
                      checked={config.include_confidence}
                      onChange={(e) => updateConfigField((prev) => ({ ...prev, include_confidence: e.target.checked }))}
                      className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 dark:border-slate-800 dark:bg-slate-900"
                    />
                    <label htmlFor="include_confidence" className="ml-2 text-xs font-medium text-slate-700 dark:text-slate-300">
                      Include Confidence
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                    Provenance Tracking
                  </label>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="include_provenance"
                      checked={config.include_provenance}
                      onChange={(e) => updateConfigField((prev) => ({ ...prev, include_provenance: e.target.checked }))}
                      className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 dark:border-slate-800 dark:bg-slate-900"
                    />
                    <label htmlFor="include_provenance" className="ml-2 text-xs font-medium text-slate-700 dark:text-slate-300">
                      Include Provenance List
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                    Missing Values Policy
                  </label>
                  <select
                    value={config.on_missing}
                    onChange={(e) => updateConfigField((prev) => ({ ...prev, on_missing: e.target.value as any }))}
                    className="w-full text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/25"
                  >
                    <option value="null">Coerce to Null</option>
                    <option value="omit">Omit Field</option>
                    <option value="error">Raise Pipeline Error</option>
                  </select>
                </div>
              </div>

              {/* Field mapping list */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Projection Schema Definitions
                  </h4>
                  <button
                    onClick={addField}
                    className="flex items-center gap-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-600 dark:bg-indigo-950/40 dark:hover:bg-indigo-900/60 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-900/40 px-2.5 py-1.5 rounded-lg text-xs font-semibold transition-all focus:outline-none"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    <span>Add Output Field</span>
                  </button>
                </div>

                <div className="space-y-3.5">
                  {config.fields.map((field, idx) => (
                    <div 
                      key={idx}
                      className="grid grid-cols-1 md:grid-cols-12 gap-3.5 items-end p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 relative hover:border-slate-300 dark:hover:border-slate-700 transition-colors group"
                    >
                      {/* Destination Path */}
                      <div className="md:col-span-3">
                        <label className="block text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase mb-1">
                          Output Field Name
                        </label>
                        <input
                          type="text"
                          value={field.path}
                          onChange={(e) => modifyField(idx, 'path', e.target.value)}
                          className="w-full text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-2.5 py-1.5 focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      {/* Source Path */}
                      <div className="md:col-span-3">
                        <label className="block text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase mb-1">
                          Source Path (from)
                        </label>
                        <input
                          type="text"
                          placeholder={field.path}
                          value={field.from || ''}
                          onChange={(e) => modifyField(idx, 'from', e.target.value)}
                          className="w-full text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-2.5 py-1.5 focus:outline-none focus:border-indigo-500 font-mono"
                        />
                      </div>

                      {/* Type select */}
                      <div className="md:col-span-2">
                        <label className="block text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase mb-1">
                          Type
                        </label>
                        <select
                          value={field.type || 'string'}
                          onChange={(e) => modifyField(idx, 'type', e.target.value)}
                          className="w-full text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-2 py-1.5 focus:outline-none"
                        >
                          <option value="string">string</option>
                          <option value="string[]">string[]</option>
                          <option value="number">number</option>
                          <option value="object">object</option>
                          <option value="object[]">object[]</option>
                        </select>
                      </div>

                      {/* Normalization select */}
                      <div className="md:col-span-2">
                        <label className="block text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase mb-1">
                          Normalize
                        </label>
                        <select
                          value={field.normalize || ''}
                          onChange={(e) => modifyField(idx, 'normalize', e.target.value)}
                          className="w-full text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-2 py-1.5 focus:outline-none"
                        >
                          <option value="">None</option>
                          <option value="E164">Phone (E.164)</option>
                          <option value="canonical">Skill (Canonical)</option>
                        </select>
                      </div>

                      {/* Required / Actions */}
                      <div className="md:col-span-2 flex items-center justify-between pb-1.5 px-1">
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            id={`req_${idx}`}
                            checked={field.required}
                            onChange={(e) => modifyField(idx, 'required', e.target.checked)}
                            className="h-3.5 w-3.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 dark:border-slate-800"
                          />
                          <label htmlFor={`req_${idx}`} className="ml-1 text-[11px] font-medium text-slate-600 dark:text-slate-400 select-none">
                            Req.
                          </label>
                        </div>

                        <button
                          onClick={() => removeField(idx)}
                          className="p-1 rounded text-slate-450 hover:bg-red-50 hover:text-red-650 dark:hover:bg-red-950/20 dark:hover:text-red-400 transition-colors"
                          title="Delete mapping"
                          disabled={config.fields.length <= 1}
                        >
                          <Trash2 className="h-4 w-4 shrink-0" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            /* JSON Code view */
            <div className="h-full flex flex-col font-mono text-xs gap-3">
              <div className="flex justify-end gap-2 shrink-0">
                <button
                  onClick={formatJson}
                  className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 dark:bg-slate-900 dark:hover:bg-slate-800 text-[10px] text-slate-700 dark:text-slate-300 rounded border border-slate-200 dark:border-slate-800 transition-all font-semibold"
                >
                  Format JSON
                </button>
              </div>
              <textarea
                value={jsonText}
                onChange={handleJsonChange}
                className="flex-1 bg-slate-950 text-slate-100 border border-slate-900 rounded-lg p-4 font-mono text-xs focus:outline-none focus:border-slate-750 resize-none h-[420px]"
                spellCheck={false}
              />
            </div>
          )}
        </div>
      </div>

      {/* Editor Sidebar: Validation panel & details */}
      <div className="lg:col-span-4 space-y-6">
        {/* Schema validation card */}
        <div className="bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            <span>Config Validation</span>
          </h3>

          <p className="text-xs leading-relaxed text-slate-500 dark:text-slate-400">
            Validate the current projection schema configuration against the backend schema format to prevent pipeline failures.
          </p>

          <button
            onClick={validateConfig}
            className="w-full flex items-center justify-center gap-1.5 px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-500 shadow-sm focus:outline-none"
          >
            <span>Validate Config</span>
          </button>

          {/* Validation Result Output */}
          {validationResult.status === 'valid' && (
            <div className="flex items-start gap-2.5 p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/20 text-emerald-800 dark:text-emerald-400 text-xs border border-emerald-100 dark:border-emerald-900/30">
              <CheckCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">Schema Valid</p>
                <p className="mt-0.5 leading-normal">{validationResult.message}</p>
              </div>
            </div>
          )}

          {validationResult.status === 'invalid' && (
            <div className="flex items-start gap-2.5 p-3 rounded-lg bg-red-50 dark:bg-red-950/20 text-red-800 dark:text-red-400 text-xs border border-red-100 dark:border-red-900/30">
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="font-bold">Validation Failed</p>
                <p className="mt-0.5 leading-normal">{validationResult.message}</p>
                
                {validationResult.errors && validationResult.errors.length > 0 && (
                  <div className="mt-2 space-y-1 font-mono text-[10px] bg-red-100/50 dark:bg-red-950/50 p-2 rounded max-h-[120px] overflow-y-auto">
                    {validationResult.errors.map((err, i) => (
                      <div key={i} className="leading-relaxed border-b border-red-200/50 dark:border-red-900/30 pb-0.5 mb-0.5 last:border-b-0">
                        <span className="font-bold">{err.loc}:</span> {err.msg}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Documentation Helper */}
        <div className="bg-slate-50 dark:bg-slate-900/55 border border-slate-200/60 dark:border-slate-800/80 rounded-xl p-5 shadow-sm space-y-3.5">
          <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
            <Info className="h-4 w-4 text-indigo-500" />
            <span>Path Notation Syntax</span>
          </h4>

          <div className="space-y-3 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
            <div>
              <p className="font-semibold text-slate-800 dark:text-slate-300">Simple path mappings</p>
              <p className="font-mono text-[10px] text-slate-500 dark:text-slate-500">full_name</p>
              <p className="mt-0.5">Copies the root field directly to output.</p>
            </div>

            <div className="pt-2 border-t border-slate-200 dark:border-slate-800">
              <p className="font-semibold text-slate-800 dark:text-slate-300">Nested object mappings</p>
              <p className="font-mono text-[10px] text-slate-500 dark:text-slate-500">location.country</p>
              <p className="mt-0.5">Extracts nested values using dot-notation.</p>
            </div>

            <div className="pt-2 border-t border-slate-200 dark:border-slate-800">
              <p className="font-semibold text-slate-800 dark:text-slate-300">Array indices</p>
              <p className="font-mono text-[10px] text-slate-500 dark:text-slate-500">emails[0]</p>
              <p className="mt-0.5">Extracts the first element of an array list.</p>
            </div>

            <div className="pt-2 border-t border-slate-200 dark:border-slate-800">
              <p className="font-semibold text-slate-800 dark:text-slate-300">Array plucking</p>
              <p className="font-mono text-[10px] text-slate-500 dark:text-slate-500">skills[].name</p>
              <p className="mt-0.5">Extracts specific nested property from every array object.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
