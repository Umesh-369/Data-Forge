'use client';

import React, { useState } from 'react';
import { useAppStore } from '@/lib/store';
import { runAutoMLPipeline, downloadCleanedDataset } from '@/lib/api';
import { BrainCircuit, Play, CheckCircle, BarChart3, AlertCircle, RefreshCw, Cpu, Layers, ArrowRight, FileCode, Download, Sparkles, Check, Info } from 'lucide-react';
import { RecommendationCandidate, AutoPipelineResult } from '@/lib/types';
import CodeExportModal from '@/components/common/CodeExportModal';

export default function AutoMLDashboard() {
  const { currentDataset, currentVersionId, profile, setRecommendations, setTrainingResults } = useAppStore();
  const [pipelineResult, setPipelineResult] = useState<AutoPipelineResult | null>(null);
  const [selectedAlgo, setSelectedAlgo] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentStep, setCurrentStep] = useState<number>(0); // 0: Idle, 1: Detecting, 2: Cleaning, 3: Training, 4: Done
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isCodeModalOpen, setIsCodeModalOpen] = useState(false);
  const [isDownloadingCleaned, setIsDownloadingCleaned] = useState(false);

  const steps = [
    { id: 1, label: 'Detecting target' },
    { id: 2, label: 'Cleaning data' },
    { id: 3, label: 'Training candidates' },
    { id: 4, label: 'Done' }
  ];

  const handleRunPipeline = async () => {
    if (!currentDataset) return;
    setIsExecuting(true);
    setErrorMsg(null);
    setPipelineResult(null);

    // Animate progress steps
    setCurrentStep(1);

    try {
      // Step transition simulation for inline feedback
      await new Promise(r => setTimeout(r, 600));
      setCurrentStep(2);
      await new Promise(r => setTimeout(r, 600));
      setCurrentStep(3);

      const res = await runAutoMLPipeline(currentDataset.id, undefined, currentVersionId || undefined);

      setCurrentStep(4);
      setPipelineResult(res);
      setSelectedAlgo(res.selected_algorithm);

      // Sync with global store
      setRecommendations({
        dataset_id: res.dataset_id,
        version_id: res.version_id,
        target_column: res.target_column,
        problem_type: res.problem_type,
        class_balance: res.class_balance,
        feature_count: res.feature_count,
        candidates: res.candidates
      });

      setTrainingResults(res.training_results);

    } catch (err: any) {
      setErrorMsg(err.message || 'AutoML pipeline execution failed');
      setCurrentStep(0);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleDownloadCleaned = async (format: 'csv' | 'xlsx' = 'csv') => {
    if (!currentDataset || !pipelineResult) return;
    setIsDownloadingCleaned(true);
    try {
      await downloadCleanedDataset(
        currentDataset.id,
        pipelineResult.target_column,
        currentVersionId || undefined,
        format,
        currentDataset.name
      );
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to download cleaned dataset');
    } finally {
      setIsDownloadingCleaned(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & One-Click Trigger Card */}
      <div className="glass-panel rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <BrainCircuit className="w-5 h-5 text-brand-600" /> AutoML Model Recommender & Trainer
            </h3>
            <p className="text-xs text-slate-600 mt-1">
              One-click end-to-end automated pipeline: Target Inference → Auto-Cleaning → Candidate Evaluation → Best Model Training.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Single "Analyze & Recommend" Pill Button */}
            {!pipelineResult && !isExecuting && (
              <button
                type="button"
                onClick={handleRunPipeline}
                className="px-6 py-2.5 bg-brand-gradient hover:opacity-90 text-white font-bold rounded-full text-xs transition-all flex items-center gap-2 shadow-lg shadow-brand-500/25 transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
              >
                <Sparkles className="w-4 h-4 fill-white" />
                <span>Analyze & Recommend</span>
              </button>
            )}

            {/* Re-run button if pipeline has completed */}
            {pipelineResult && !isExecuting && (
              <button
                type="button"
                onClick={handleRunPipeline}
                className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer shadow-sm"
              >
                <RefreshCw className="w-3.5 h-3.5 text-brand-600" />
                Re-Analyze Dataset
              </button>
            )}

            {/* Side-by-Side Dual Download Buttons (Active once complete) */}
            {pipelineResult && !isExecuting && (
              <div className="flex items-center gap-2.5 animate-in fade-in duration-300">
                {/* View & Download Code Button */}
                <button
                  type="button"
                  onClick={() => setIsCodeModalOpen(true)}
                  className="px-4 py-2 bg-brand-gradient hover:opacity-90 text-white text-xs font-bold rounded-full transition-all flex items-center gap-2 shadow-lg shadow-brand-500/25 cursor-pointer"
                >
                  <FileCode className="w-4 h-4" />
                  <span>View & Download Code</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>

                {/* Download Cleaned Dataset Button */}
                <div className="relative group">
                  <button
                    type="button"
                    onClick={() => handleDownloadCleaned('csv')}
                    disabled={isDownloadingCleaned}
                    className="px-4 py-2 bg-sky-500 hover:bg-sky-400 text-white text-xs font-bold rounded-full transition-all flex items-center gap-2 shadow-lg shadow-sky-500/25 disabled:opacity-50 cursor-pointer"
                  >
                    {isDownloadingCleaned ? (
                      <RefreshCw className="w-4 h-4 animate-spin text-white" />
                    ) : (
                      <Download className="w-4 h-4 text-white" />
                    )}
                    <span>Download Cleaned Data</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Step-by-Step Progress Indicator Inline */}
        {isExecuting && (
          <div className="mt-6 pt-5 border-t border-white/10 space-y-3 animate-in fade-in duration-300">
            <div className="flex items-center justify-between text-xs text-slate-300 font-medium px-1">
              <span>Executing Automated AutoML Pipeline...</span>
              <span className="font-mono text-sky-400 font-bold">{currentStep}/4</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {steps.map((step) => {
                const isPassed = currentStep > step.id;
                const isCurrent = currentStep === step.id;
                return (
                  <div
                    key={step.id}
                    className={`p-3 rounded-xl border flex items-center gap-2.5 transition-all ${
                      isPassed
                        ? 'bg-sky-500/10 border-sky-500/30 text-sky-700 font-bold'
                        : isCurrent
                        ? 'bg-sky-500/15 border-sky-500/50 text-sky-800 font-bold animate-pulse'
                        : 'bg-slate-50 border-slate-200 text-slate-400'
                    }`}
                  >
                    {isPassed ? (
                      <Check className="w-4 h-4 text-sky-600 shrink-0" />
                    ) : isCurrent ? (
                      <RefreshCw className="w-4 h-4 text-sky-400 animate-spin shrink-0" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-slate-600 flex items-center justify-center text-[10px] shrink-0 font-mono">
                        {step.id}
                      </div>
                    )}
                    <span className="text-xs font-semibold truncate">{step.label}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {errorMsg && (
          <div className="mt-4 p-3.5 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs flex items-center gap-2 font-medium">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}
      </div>

      {/* Main Results Dashboard (Rendered after analysis) */}
      {pipelineResult && (
        <div className="space-y-6 animate-in fade-in duration-300">
          
          {/* Target Auto-Detection Banner */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl flex items-start gap-3 shadow-sm">
            <div className="p-2 bg-brand-500/10 border border-brand-500/20 rounded-xl text-brand-600 shrink-0 mt-0.5">
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="space-y-1 text-xs">
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-900 uppercase tracking-wider text-[11px]">Auto-Inferred Target Column:</span>
                <span className="px-2.5 py-0.5 bg-brand-500/10 text-brand-700 font-mono font-bold rounded-full border border-brand-500/30">
                  {pipelineResult.target_column}
                </span>
              </div>
              <p className="text-slate-600">{pipelineResult.target_detection_reason}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Candidates List with REAL Computed Match Scores */}
            <div className="lg:col-span-2 space-y-4">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Layers className="w-4 h-4 text-brand-600" />
                Algorithm Candidates ({pipelineResult.problem_type.toUpperCase()})
              </h4>

              <div className="space-y-3">
                {pipelineResult.candidates.map((cand: RecommendationCandidate) => {
                  const isSelected = selectedAlgo === cand.algorithm;
                  return (
                    <div
                      key={cand.algorithm}
                      onClick={() => setSelectedAlgo(cand.algorithm)}
                      className={`cursor-pointer p-4 rounded-xl border transition-all ${
                        isSelected
                          ? 'glass-panel-glow border-brand-500/60 bg-white shadow-md shadow-brand-500/10'
                          : 'glass-panel border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2.5">
                          <input
                            type="radio"
                            name="algorithm"
                            checked={isSelected}
                            onChange={(e) => { e.stopPropagation(); setSelectedAlgo(cand.algorithm); }}
                            className="text-brand-600 focus:ring-brand-500 cursor-pointer"
                          />
                          <h5 className="text-sm font-bold text-slate-900">{cand.algorithm}</h5>
                          {cand.recommended && (
                            <span className="px-2.5 py-0.5 bg-sky-500/10 text-sky-700 text-[10px] rounded-full border border-sky-500/30 font-bold uppercase tracking-wider">
                              Top Winner (Auto-Trained)
                            </span>
                          )}
                        </div>
                        <span className="text-xs font-mono text-brand-600 font-bold">
                          Match Score: {(cand.score * 100).toFixed(0)}%
                        </span>
                      </div>

                      <ul className="mt-3 space-y-1.5 pl-6 list-disc text-xs text-slate-600">
                        {cand.reasoning.map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Reasoning & Dataset Decision Meta-Features Panel */}
            <div className="glass-panel p-5 rounded-2xl border border-slate-200 space-y-4 h-fit">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Dataset Decision Meta-Features
              </h4>

              <div className="space-y-3 text-xs">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-slate-500 block text-[11px]">Problem Task Type:</span>
                  <span className="font-bold text-slate-900 uppercase text-sm mt-0.5 block">{pipelineResult.problem_type}</span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-slate-500 block text-[11px]">Predictor Feature Count:</span>
                  <span className="font-mono text-brand-600 font-bold text-sm mt-0.5 block">{pipelineResult.feature_count} features</span>
                </div>

                {pipelineResult.class_balance && (
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1.5">
                    <span className="text-slate-500 block text-[11px]">Class Balance Distribution:</span>
                    {Object.entries(pipelineResult.class_balance).map(([cls, pct]) => (
                      <div key={cls} className="flex justify-between font-mono text-slate-700">
                        <span className="truncate pr-2">Class "{cls}":</span>
                        <span className="text-brand-600 font-bold shrink-0">{(pct * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Auto-Cleaning Decision Log Panel */}
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                  <span className="text-slate-600 font-bold block text-[11px] flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5 text-brand-600" /> Auto-Cleaning Decisions Log
                  </span>
                  <ul className="space-y-1 text-[11px] text-slate-600 list-disc pl-4 font-mono">
                    {pipelineResult.cleaning_logs.map((log, idx) => (
                      <li key={idx} className="leading-snug">{log}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Evaluation Results & Metrics Section */}
          {pipelineResult.training_results && (
            <div className="glass-panel rounded-2xl border border-slate-200 p-6 space-y-6">
              <div className="flex items-center justify-between border-b border-slate-200 pb-4">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-sky-600" />
                  <h3 className="text-base font-bold text-slate-900">
                    Evaluation Results ({pipelineResult.selected_algorithm})
                  </h3>
                </div>
                <span className="text-xs px-3 py-1 bg-sky-500/10 text-sky-700 border border-sky-500/30 rounded-full font-mono font-bold">
                  Status: Completed
                </span>
              </div>

              {/* Metrics Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {Object.entries(pipelineResult.training_results.metrics).map(([mName, mValue]) => (
                  <div key={mName} className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-center">
                    <p className="text-[11px] text-slate-500 uppercase tracking-wider font-bold">{mName.replace('_', ' ')}</p>
                    <h4 className="text-xl font-extrabold text-slate-900 font-mono mt-1">{mValue}</h4>
                  </div>
                ))}
              </div>

              {/* Confusion Matrix */}
              {pipelineResult.training_results.confusion_matrix && (
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
                  <h4 className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-brand-600" /> Confusion Matrix
                  </h4>
                  <div className="inline-block border border-slate-300 rounded-lg overflow-hidden font-mono text-xs shadow-sm">
                    {pipelineResult.training_results.confusion_matrix.map((row, rIdx) => (
                      <div key={rIdx} className="flex">
                        {row.map((cell, cIdx) => (
                          <div
                            key={cIdx}
                            className={`w-14 h-10 flex items-center justify-center border-r border-b border-white/5 ${
                              rIdx === cIdx ? 'bg-sky-500/20 text-sky-300 font-bold' : 'bg-dark-800 text-slate-400'
                            }`}
                          >
                            {cell}
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Feature Importances */}
              {pipelineResult.training_results.feature_importances && Object.keys(pipelineResult.training_results.feature_importances).length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Top Feature Importances</h4>
                  <div className="space-y-2">
                    {Object.entries(pipelineResult.training_results.feature_importances).slice(0, 6).map(([fName, fVal]) => (
                      <div key={fName} className="space-y-1">
                        <div className="flex justify-between text-xs font-mono">
                          <span className="text-slate-300">{fName}</span>
                          <span className="text-cyan-400 font-semibold">{(fVal * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-dark-800 h-2 rounded-full overflow-hidden">
                          <div className="bg-brand-gradient h-full rounded-full" style={{ width: `${Math.min(100, fVal * 100)}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Code Export Modal */}
      <CodeExportModal
        isOpen={isCodeModalOpen}
        onClose={() => setIsCodeModalOpen(false)}
        versionId={currentVersionId || undefined}
        datasetName={currentDataset?.name}
        targetColumn={pipelineResult?.target_column || ''}
        algorithm={selectedAlgo || pipelineResult?.selected_algorithm}
        versionNumber={profile?.version_number || 1}
      />
    </div>
  );
}


