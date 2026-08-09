'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Download, ChevronDown, FileSpreadsheet, FileCode, BookOpen, Layers, FileJson } from 'lucide-react';
import { downloadDatasetFile } from '@/lib/api';

interface DownloadSplitButtonProps {
  datasetId?: string;
  versionId?: string;
  datasetName?: string;
  versionNumber?: number;
  onOpenCodeModal?: (format: 'py' | 'ipynb') => void;
  className?: string;
}

export default function DownloadSplitButton({
  datasetId,
  versionId,
  datasetName = 'dataset',
  versionNumber = 1,
  onOpenCodeModal,
  className = '',
}: DownloadSplitButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleDownloadDataset = async (format: 'csv' | 'xlsx' | 'json') => {
    setIsOpen(false);
    if (!datasetId) {
      alert('No active dataset selected.');
      return;
    }

    try {
      await downloadDatasetFile(datasetId, versionId || undefined, format, datasetName);
    } catch (err: any) {
      alert(err.message || 'Dataset download failed');
    }
  };

  const handleDownloadCode = (format: 'py' | 'ipynb') => {
    setIsOpen(false);
    if (onOpenCodeModal) {
      onOpenCodeModal(format);
    }
  };

  return (
    <div className={`relative inline-block ${className}`} ref={dropdownRef}>
      <div className="flex items-center rounded-xl bg-brand-gradient shadow-lg shadow-brand-500/20 text-white overflow-hidden p-0.5 border border-white/20">
        <button
          type="button"
          onClick={() => handleDownloadDataset('csv')}
          className="px-3.5 py-1.5 text-xs font-bold flex items-center gap-1.5 hover:opacity-90 transition-all cursor-pointer"
        >
          <Download className="w-4 h-4" />
          <span>Export</span>
        </button>

        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="px-2 py-1.5 hover:bg-white/15 border-l border-white/20 transition-all cursor-pointer flex items-center justify-center"
          title="Export options"
        >
          <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>
      </div>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 glass-panel border border-slate-200 rounded-2xl shadow-xl p-2 z-50 animate-in fade-in zoom-in-95 duration-150 bg-white/95">
          <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-100">
            Dataset Formats
          </div>

          <button
            type="button"
            onClick={() => handleDownloadDataset('csv')}
            className="w-full text-left px-3 py-2 rounded-xl text-xs text-slate-700 hover:text-slate-900 hover:bg-slate-100 flex items-center gap-2.5 transition-all font-semibold cursor-pointer"
          >
            <FileSpreadsheet className="w-4 h-4 text-brand-600" />
            <span>Dataset (.CSV)</span>
          </button>

          <button
            type="button"
            onClick={() => handleDownloadDataset('xlsx')}
            className="w-full text-left px-3 py-2 rounded-xl text-xs text-slate-700 hover:text-slate-900 hover:bg-slate-100 flex items-center gap-2.5 transition-all font-semibold cursor-pointer"
          >
            <Layers className="w-4 h-4 text-cyan-600" />
            <span>Dataset (.XLSX)</span>
          </button>

          <button
            type="button"
            onClick={() => handleDownloadDataset('json')}
            className="w-full text-left px-3 py-2 rounded-xl text-xs text-slate-700 hover:text-slate-900 hover:bg-slate-100 flex items-center gap-2.5 transition-all font-semibold cursor-pointer"
          >
            <FileJson className="w-4 h-4 text-amber-600" />
            <span>Dataset (.JSON)</span>
          </button>

          <div className="mt-1 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500 border-t border-b border-slate-100">
            ML Pipeline Code
          </div>

          <button
            type="button"
            onClick={() => handleDownloadCode('py')}
            className="w-full text-left px-3 py-2 rounded-xl text-xs text-slate-700 hover:text-slate-900 hover:bg-slate-100 flex items-center gap-2.5 transition-all font-semibold cursor-pointer"
          >
            <FileCode className="w-4 h-4 text-brand-600" />
            <span>Python Script (.PY)</span>
          </button>

          <button
            type="button"
            onClick={() => handleDownloadCode('ipynb')}
            className="w-full text-left px-3 py-2 rounded-xl text-xs text-slate-700 hover:text-slate-900 hover:bg-slate-100 flex items-center gap-2.5 transition-all font-semibold cursor-pointer"
          >
            <BookOpen className="w-4 h-4 text-emerald-600" />
            <span>Jupyter Notebook (.IPYNB)</span>
          </button>
        </div>
      )}
    </div>
  );
}
