'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism';

const SyntaxHighlighter = dynamic(
  async () => {
    const mod = await import('react-syntax-highlighter');
    return mod.Prism;
  },
  {
    ssr: false,
    loading: () => (
      <div className="p-4 text-slate-500 animate-pulse font-mono text-xs">
        Loading code view...
      </div>
    ),
  }
);
import {
  X, Copy, Check, Download, AlertTriangle, FileCode, BookOpen, Terminal, Sparkles
} from 'lucide-react';
import { exportVersionCode } from '@/lib/api';
import { CodeExportResult, ExcludedOp } from '@/lib/types';

interface CodeExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  versionId?: string;
  datasetName?: string;
  targetColumn?: string;
  algorithm?: string;
  versionNumber?: number;
  initialFormat?: 'py' | 'ipynb';
}

export default function CodeExportModal({
  isOpen,
  onClose,
  versionId,
  datasetName = 'dataset',
  targetColumn,
  algorithm,
  versionNumber = 1,
  initialFormat = 'py',
}: CodeExportModalProps) {
  const [format, setFormat] = useState<'py' | 'ipynb'>(initialFormat);
  const [exportData, setExportData] = useState<CodeExportResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setFormat(initialFormat);
    }
  }, [isOpen, initialFormat]);

  useEffect(() => {
    if (isOpen && versionId) {
      loadCode(format);
    }
  }, [isOpen, versionId, format]);

  const loadCode = async (selectedFormat: 'py' | 'ipynb') => {
    if (!versionId) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await exportVersionCode(versionId, selectedFormat, targetColumn, algorithm);
      setExportData(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch code export');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = () => {
    if (!exportData?.code) return;
    navigator.clipboard.writeText(exportData.code);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 1500);
  };

  const handleDownload = () => {
    if (!exportData?.code) return;
    
    // Single-shot Blob creation and triggering single direct file download
    const mimeType = format === 'ipynb' ? 'application/json' : 'text/x-python';
    const blob = new Blob([exportData.code], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = exportData.filename || `pipeline_v${versionNumber}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-md p-0 sm:p-6 animate-in fade-in duration-200">
      {/* Modal Container: Full-screen on mobile (<640px), rounded dialog on desktop */}
      <div className="w-full h-full sm:h-auto sm:max-h-[85vh] sm:max-w-4xl glass-panel border border-slate-200 sm:rounded-3xl flex flex-col overflow-hidden shadow-2xl relative bg-white">
        
        {/* Header Bar */}
        <div className="px-4 sm:px-6 py-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 bg-slate-50 sticky top-0 z-10">
          
          {/* Title & Metadata */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-600 shrink-0">
              <FileCode className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
                ML Pipeline Code Export
                <span className="text-[10px] px-2 py-0.5 bg-brand-500/10 text-brand-700 border border-brand-500/20 rounded-full font-mono font-bold">
                  v{versionNumber}
                </span>
              </h3>
              <p className="text-[11px] text-slate-500 truncate max-w-[200px] sm:max-w-xs">
                {datasetName} {algorithm ? `• ${algorithm}` : ''}
              </p>
            </div>
          </div>

          {/* Center Format Toggle Pill */}
          <div className="flex items-center bg-slate-200/80 p-1 rounded-full border border-slate-300">
            <button
              onClick={() => setFormat('py')}
              className={`px-3.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all ${
                format === 'py'
                  ? 'bg-brand-gradient text-white shadow-md shadow-brand-500/20'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>.py Script</span>
            </button>
            <button
              onClick={() => setFormat('ipynb')}
              className={`px-3.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all ${
                format === 'ipynb'
                  ? 'bg-brand-gradient text-white shadow-md shadow-brand-500/20'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>.ipynb Notebook</span>
            </button>
          </div>

          {/* Action Buttons & Close Icon */}
          <div className="flex items-center gap-2">
            {/* Copy Button with micro-interaction */}
            <button
              onClick={handleCopy}
              disabled={isLoading || !exportData?.code}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all flex items-center gap-1.5 disabled:opacity-40 ${
                isCopied
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 shadow-sm'
                  : 'bg-white hover:bg-slate-100 border-slate-300 text-slate-700 hover:text-slate-900 shadow-sm'
              }`}
              title="Copy code to clipboard"
            >
              {isCopied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-brand-600" />
                  <span className="hidden sm:inline">Copy</span>
                </>
              )}
            </button>

            {/* Single-shot Download Button */}
            <button
              onClick={handleDownload}
              disabled={isLoading || !exportData?.code}
              className="px-3.5 py-1.5 rounded-full text-xs font-bold bg-brand-gradient hover:opacity-90 text-white shadow-md shadow-brand-500/20 transition-all flex items-center gap-1.5 disabled:opacity-40"
              title="Download full file (.py or .ipynb)"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Download .{format}</span>
            </button>

            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-1.5 rounded-full bg-slate-100 text-slate-500 hover:text-slate-900 border border-slate-300 hover:border-slate-400 transition-all ml-1 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 bg-slate-50 font-mono text-xs">
          
          {/* Error Banner */}
          {errorMsg && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400 text-xs flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 shrink-0 text-red-400" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Ineligible Operations Amber Warning Banner */}
          {exportData?.excluded_operations && exportData.excluded_operations.length > 0 && (
            <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-2xl text-amber-300 text-xs space-y-2">
              <div className="flex items-center gap-2 font-bold text-amber-200">
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                <span>Notice: Some custom lineage steps were excluded from standalone export:</span>
              </div>
              <ul className="pl-6 list-disc space-y-1 text-[11px] text-amber-300/90 font-mono">
                {exportData.excluded_operations.map((ex: ExcludedOp, idx: number) => (
                  <li key={idx}>
                    <strong className="text-amber-200">{ex.operation}</strong>: {ex.reason}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Loading Skeleton Shimmer */}
          {isLoading ? (
            <div className="space-y-3 p-6 glass-panel rounded-2xl animate-pulse">
              <div className="h-4 bg-white/10 rounded w-1/3" />
              <div className="h-4 bg-white/5 rounded w-2/3" />
              <div className="h-4 bg-white/10 rounded w-1/2" />
              <div className="h-24 bg-white/5 rounded w-full" />
              <div className="h-4 bg-white/10 rounded w-3/4" />
              <div className="h-16 bg-white/5 rounded w-full" />
            </div>
          ) : (
            /* Syntax Highlighted Code Display */
            <div className="rounded-2xl overflow-hidden border border-white/10 shadow-inner bg-[#1e1e1e]">
              <SyntaxHighlighter
                language="python"
                style={vscDarkPlus}
                customStyle={{
                  margin: 0,
                  padding: '1.25rem',
                  fontSize: '0.8rem',
                  lineHeight: '1.5',
                  backgroundColor: 'transparent',
                }}
                showLineNumbers
              >
                {exportData?.code || '# Code payload not ready'}
              </SyntaxHighlighter>
            </div>
          )}
        </div>

        {/* Footer Note Bar */}
        <div className="px-6 py-3 border-t border-slate-200 bg-slate-100 flex items-center justify-between text-[11px] text-slate-600">
          <span className="flex items-center gap-1.5 font-sans font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-brand-600" />
            <span>Runs standalone with pandas + scikit-learn only</span>
          </span>
          <span className="font-mono text-slate-500 hidden sm:inline">
            Single-shot Blob Download • {format.toUpperCase()} Format
          </span>
        </div>
      </div>
    </div>
  );
}
