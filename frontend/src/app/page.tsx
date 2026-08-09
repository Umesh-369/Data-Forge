'use client';

import React, { useEffect, useState } from 'react';
import { useAppStore } from '@/lib/store';
import { fetchDatasets, uploadDataset, loadSeedDataset, fetchDatasetProfile, fetchDatasetPreview } from '@/lib/api';
import DataParticlesCanvas from '@/components/3d/DataParticles';
import LandingPage from '@/components/landing/LandingPage';
import ProfilingDashboard from '@/components/profiling/ProfilingDashboard';
import SpreadsheetGrid from '@/components/editor/SpreadsheetGrid';
import ChatPanel from '@/components/chat/ChatPanel';
import AutoMLDashboard from '@/components/auto_ml/AutoMLDashboard';
import DownloadSplitButton from '@/components/common/DownloadSplitButton';
import CodeExportModal from '@/components/common/CodeExportModal';
import {
  Sparkles, UploadCloud, Database, Activity, FileSpreadsheet,
  BrainCircuit, MessageSquare, Home, Layers, CheckCircle2,
  RefreshCw, ChevronRight, AlertCircle
} from 'lucide-react';

export default function HomePage() {
  const {
    currentDataset, currentVersionId, profile, activeTab,
    setCurrentDataset, setCurrentVersionId, setProfile, setPreview, setActiveTab,
    setIsLoading, isLoading
  } = useAppStore();

  const [datasetsList, setDatasetsList] = useState<any[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isHeaderCodeModalOpen, setIsHeaderCodeModalOpen] = useState(false);
  const [headerCodeFormat, setHeaderCodeFormat] = useState<'py' | 'ipynb'>('py');


  useEffect(() => {
    loadAllDatasets();
  }, []);

  const loadAllDatasets = async () => {
    try {
      const list = await fetchDatasets();
      setDatasetsList(list);
      if (list.length > 0 && !currentDataset) {
        selectDataset(list[0]);
      }
    } catch (err) {
      console.error('Failed to load datasets list:', err);
    }
  };

  const selectDataset = async (dataset: any) => {
    setCurrentDataset(dataset);
    setCurrentVersionId(dataset.current_version_id);
    setIsLoading(true);
    try {
      const [prof, prev] = await Promise.all([
        fetchDatasetProfile(dataset.id, dataset.current_version_id),
        fetchDatasetPreview(dataset.id, dataset.current_version_id)
      ]);
      setProfile(prof);
      setPreview(prev);
    } catch (err) {
      console.error('Failed to load dataset details:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!file) return;
    setIsUploading(true);
    try {
      const newDataset = await uploadDataset(file);
      await loadAllDatasets();
      await selectDataset(newDataset);
      setActiveTab('profiling');
    } catch (err: any) {
      alert(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSeedLoad = async (seedName: string) => {
    setIsUploading(true);
    try {
      const seedDataset = await loadSeedDataset(seedName);
      await loadAllDatasets();
      await selectDataset(seedDataset);
      setActiveTab('profiling');
    } catch (err: any) {
      alert(err.message || 'Seed load failed');
    } finally {
      setIsUploading(false);
    }
  };

  const navTabs = [
    { id: 'landing', label: 'Landing Page', icon: Home, badge: 'Home' },
    { id: 'profiling', label: 'Data Hub', icon: Activity, badge: 'Profile' },
    { id: 'editor', label: 'Smart Grid', icon: FileSpreadsheet, badge: 'Grid' },
    { id: 'chat', label: 'AI Assistant', icon: MessageSquare, badge: 'Copilot' },
    { id: 'automl', label: 'AutoML Studio', icon: BrainCircuit, badge: 'ML' }
  ];

  return (
    <div className="min-h-screen gradient-mesh-bg text-slate-900 flex flex-col relative overflow-x-hidden selection:bg-brand-500 selection:text-white">
      {/* Ambient Animated Glow Aura */}
      <div className="fixed inset-0 pointer-events-none z-0 ambient-glow-overlay" />

      {/* 3D Particle Canvas - Pauses/unmounts when in editor/data heavy tabs */}
      <DataParticlesCanvas active={activeTab === 'landing' || activeTab === 'profiling'} />

      {/* Primary Sky Navigation Header */}
      <header className="relative z-30 border-b border-slate-200 glass-panel sticky top-0 px-4 sm:px-8 py-3 flex flex-wrap lg:flex-nowrap items-center justify-between gap-4 shadow-sm shadow-slate-900/5 backdrop-blur-2xl">
        {/* Brand Logo & Tagline */}
        <div className="flex items-center gap-3.5 shrink-0">
          <div
            onClick={() => setActiveTab('landing')}
            className="w-10 h-10 bg-brand-gradient rounded-xl flex items-center justify-center shadow-lg shadow-brand-500/30 cursor-pointer hover:scale-105 transition-all animated-gradient-border"
          >
            <Sparkles className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <h1
              onClick={() => setActiveTab('landing')}
              className="text-base sm:text-lg font-extrabold text-slate-900 tracking-tight flex items-center gap-2 cursor-pointer hover:text-brand-600 transition-colors"
            >
              DataForge
            </h1>
            <p className="hidden sm:block text-[11px] text-slate-600 font-medium">Conversational AutoML & Wrangling Platform</p>
          </div>
        </div>

        {/* 5 Max Structured Navigation Tabs */}
        <nav className="flex items-center gap-2 glass-nav-pill p-1.5 rounded-full overflow-x-auto no-scrollbar max-w-full justify-start lg:justify-center mx-auto shrink-0 my-1 lg:my-0">
          {navTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-4 py-2 rounded-full text-xs font-semibold flex items-center gap-2 transition-all whitespace-nowrap shrink-0 cursor-pointer ${
                  isActive
                    ? 'glass-nav-item-active'
                    : 'glass-nav-item-inactive'
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white drop-shadow' : 'text-slate-600'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right Dataset Selector & Upload CTA */}
        <div className="flex items-center gap-3 shrink-0">
          {datasetsList.length > 0 && (
            <div className="relative">
              <select
                value={currentDataset?.id || ''}
                onChange={(e) => {
                  const ds = datasetsList.find(d => d.id === e.target.value);
                  if (ds) selectDataset(ds);
                }}
                className="px-3.5 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-800 focus:outline-none focus:border-brand-500 cursor-pointer font-medium max-w-[180px] truncate shadow-sm"
              >
                {datasetsList.map(ds => (
                  <option key={ds.id} value={ds.id}>
                    {ds.name} ({ds.row_count} rows)
                  </option>
                ))}
              </select>
            </div>
          )}

          <label className="cursor-pointer px-4 py-2 bg-brand-gradient hover:opacity-90 text-white text-xs font-bold rounded-xl transition-all flex items-center gap-2 shadow-lg shadow-brand-500/20 shrink-0">
            <UploadCloud className="w-4 h-4" />
            <span className="hidden sm:inline">Upload CSV/XLSX</span>
            <input
              type="file"
              accept=".csv,.xlsx,.xls,.json,.parquet"
              className="hidden"
              onClick={(e) => { (e.target as HTMLInputElement).value = ''; }}
              onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
            />
          </label>

          {/* Export Download Split Button */}
          {currentDataset && (
            <DownloadSplitButton
              datasetId={currentDataset.id}
              versionId={currentVersionId || undefined}
              datasetName={currentDataset.name}
              versionNumber={profile?.version_number || 1}
              onOpenCodeModal={(fmt) => {
                setHeaderCodeFormat(fmt || 'py');
                setIsHeaderCodeModalOpen(true);
              }}
            />
          )}
        </div>
      </header>


      {/* Main Page View Container */}
      <main className="relative z-10 flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6">
        {isLoading && (
          <div className="mb-4 p-3 bg-brand-500/10 border border-brand-400/30 rounded-xl text-brand-300 text-xs flex items-center gap-2 animate-pulse">
            <RefreshCw className="w-4 h-4 animate-spin text-brand-400" />
            <span>Loading dataset computations & version metadata...</span>
          </div>
        )}

        {/* 6 Structured Application Views */}
        {activeTab === 'landing' && (
          <LandingPage
            onFileUpload={handleFileUpload}
            onSeedLoad={handleSeedLoad}
            isUploading={isUploading}
          />
        )}

        {activeTab === 'profiling' && (
          <div className="space-y-6">
            {!currentDataset ? (
              <div className="glass-panel p-12 rounded-3xl text-center space-y-4 max-w-xl mx-auto my-12">
                <Database className="w-12 h-12 text-brand-400 mx-auto animate-bounce" />
                <h3 className="text-xl font-bold text-slate-900">No Dataset Selected</h3>
                <p className="text-xs text-slate-600">Please choose a dataset from the header or upload a CSV file on the Landing Page.</p>
                <button
                  type="button"
                  onClick={() => setActiveTab('landing')}
                  className="px-5 py-2.5 bg-brand-gradient text-white text-xs font-bold rounded-xl shadow-lg shadow-brand-500/20 cursor-pointer"
                >
                  Go to Landing Page
                </button>
              </div>
            ) : (
              <ProfilingDashboard />
            )}
          </div>
        )}

        {activeTab === 'editor' && (
          <div className="space-y-6 min-h-[600px]">
            {!currentDataset ? (
              <div className="glass-panel p-12 rounded-3xl text-center space-y-4 max-w-xl mx-auto my-12">
                <FileSpreadsheet className="w-12 h-12 text-brand-400 mx-auto" />
                <h3 className="text-xl font-bold text-slate-900">No Active Spreadsheet Data</h3>
                <p className="text-xs text-slate-600">Select a dataset from the header to view live rows and columns.</p>
                <button
                  type="button"
                  onClick={() => setActiveTab('landing')}
                  className="px-5 py-2.5 bg-brand-gradient text-white text-xs font-bold rounded-xl shadow-lg shadow-brand-500/20 cursor-pointer"
                >
                  Go to Landing Page
                </button>
              </div>
            ) : (
              <SpreadsheetGrid />
            )}
          </div>
        )}

        {activeTab === 'chat' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-[600px]">
            <div className="lg:col-span-1">
              <ChatPanel />
            </div>
            <div className="lg:col-span-2">
              <SpreadsheetGrid />
            </div>
          </div>
        )}

        {activeTab === 'automl' && (
          <div className="space-y-6">
            {!currentDataset ? (
              <div className="glass-panel p-12 rounded-3xl text-center space-y-4 max-w-xl mx-auto my-12">
                <BrainCircuit className="w-12 h-12 text-brand-400 mx-auto" />
                <h3 className="text-xl font-bold text-slate-900">AutoML Studio Ready</h3>
                <p className="text-xs text-slate-600">Load a dataset to train machine learning models and view algorithm leaderboards.</p>
                <button
                  type="button"
                  onClick={() => setActiveTab('landing')}
                  className="px-5 py-2.5 bg-brand-gradient text-white text-xs font-bold rounded-xl shadow-lg shadow-brand-500/20 cursor-pointer"
                >
                  Go to Landing Page
                </button>
              </div>
            ) : (
              <AutoMLDashboard />
            )}
          </div>
        )}
      </main>

      {/* Header Scoped Code Export Modal */}
      <CodeExportModal
        isOpen={isHeaderCodeModalOpen}
        onClose={() => setIsHeaderCodeModalOpen(false)}
        versionId={currentVersionId || undefined}
        datasetName={currentDataset?.name}
        versionNumber={profile?.version_number || 1}
        initialFormat={headerCodeFormat}
      />
    </div>
  );
}

