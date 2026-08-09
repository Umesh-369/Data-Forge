'use client';

import React, { useState } from 'react';
import { useAppStore } from '@/lib/store';
import {
  Sparkles, UploadCloud, Database, Activity, FileSpreadsheet,
  BrainCircuit, ArrowRight, ShieldCheck, Zap, Layers,
  ChevronRight, BarChart3, CheckCircle2, Terminal, Code2
} from 'lucide-react';

interface LandingPageProps {
  onFileUpload: (file: File) => void;
  onSeedLoad: (seedName: string) => void;
  isUploading: boolean;
}

export default function LandingPage({ onFileUpload, onSeedLoad, isUploading }: LandingPageProps) {
  const { setActiveTab, currentDataset } = useAppStore();
  const [dragActive, setDragActive] = useState(false);
  const [activePreviewTab, setActivePreviewTab] = useState<'profiling' | 'copilot' | 'automl'>('profiling');

  return (
    <div className="space-y-16 py-6 pb-16">
      {/* Hero Section */}
      <section className="relative flex flex-col items-center text-center space-y-8 max-w-4xl mx-auto px-4">
        {/* Glow ambient background element */}
        <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-96 h-96 bg-brand-400/15 blur-3xl rounded-full pointer-events-none" />

        {/* Headline */}
        <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight">
          Transform & Train Datasets with <br />
          <span className="animated-gradient-text font-black">
            Conversational AI & Sky Blue Safety
          </span>
        </h1>

        {/* Subtitle */}
        <p className="text-slate-600 text-base sm:text-lg max-w-2xl leading-relaxed">
          The next-generation data workbench featuring Python AST whitelisted execution, real-time statistical profiling, and automated machine learning.
        </p>

        {/* CTA Actions */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          {currentDataset ? (
            <button
              type="button"
              onClick={() => setActiveTab('profiling')}
              className="px-6 py-3.5 bg-brand-gradient text-white rounded-xl font-bold text-sm hover:opacity-90 transition-all flex items-center gap-2 shadow-xl shadow-brand-500/25 cursor-pointer"
            >
              Enter Data Studio <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={() => handleScrollToUpload()}
              className="px-6 py-3.5 bg-brand-gradient text-white rounded-xl font-bold text-sm hover:opacity-90 transition-all flex items-center gap-2 shadow-xl shadow-brand-500/25 cursor-pointer"
            >
              Upload Dataset <UploadCloud className="w-5 h-5" />
            </button>
          )}

          <button
            type="button"
            onClick={() => onSeedLoad('student')}
            disabled={isUploading}
            className="px-6 py-3.5 bg-white border border-slate-200 hover:border-brand-500/40 text-slate-700 rounded-xl font-semibold text-sm transition-all flex items-center gap-2 glass-panel cursor-pointer disabled:opacity-50 shadow-sm"
          >
            <Zap className="w-4 h-4 text-brand-500" />
            Try Student Demo Data
          </button>
        </div>

        {/* Hero Drag & Drop Card */}
        <div id="upload-section" className="w-full max-w-2xl pt-4">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragActive(false);
              if (e.dataTransfer.files?.[0]) onFileUpload(e.dataTransfer.files[0]);
            }}
            className={`p-10 glass-panel-glow rounded-3xl border-2 border-dashed transition-all flex flex-col items-center justify-center space-y-4 cursor-pointer relative overflow-hidden group ${
              dragActive ? 'border-brand-400 bg-brand-500/15 scale-[1.01]' : 'border-brand-400/30 hover:border-brand-400/60'
            }`}
          >
            <div className="w-16 h-16 bg-brand-500/15 rounded-2xl flex items-center justify-center text-brand-400 group-hover:scale-110 transition-transform">
              <UploadCloud className="w-8 h-8 animate-bounce" />
            </div>

            <div className="space-y-1">
              <p className="text-base font-bold text-slate-900">Drag & drop your CSV or Excel file here</p>
              <p className="text-xs text-slate-500">Supports CSV, XLSX, JSON, Parquet up to 50MB with instant auto-profiling</p>
            </div>

            <label className="px-6 py-2.5 bg-brand-400 hover:bg-brand-500 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-brand-500/20 cursor-pointer">
              Browse Local Files
              <input
                type="file"
                accept=".csv,.xlsx,.xls,.json,.parquet"
                className="hidden"
                onClick={(e) => { (e.target as HTMLInputElement).value = ''; }}
                onChange={(e) => e.target.files?.[0] && onFileUpload(e.target.files[0])}
              />
            </label>
          </div>
        </div>
      </section>

      {/* Pre-Seeded Quick Start Grid */}
      <section className="space-y-4 max-w-5xl mx-auto px-4 text-center">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">Or launch instantly with pre-seeded datasets</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { name: 'student', label: 'Student Marks', rows: '1,000 rows', icon: BarChart3, desc: 'Performance scores & demographics' },
            { name: 'housing', label: 'Housing Prices', rows: '506 rows', icon: Database, desc: 'Real estate features & valuations' },
            { name: 'iris', label: 'Iris Classification', rows: '150 rows', icon: Layers, desc: 'Classic multi-class benchmark' },
            { name: 'churn', label: 'Customer Churn', rows: '7,043 rows', icon: Activity, desc: 'Telecom churn prediction features' }
          ].map((item) => (
            <button
              key={item.name}
              onClick={() => onSeedLoad(item.name)}
              disabled={isUploading}
              className="glass-panel p-4 rounded-2xl border border-slate-200 hover:border-brand-500/50 hover:bg-white transition-all text-left group"
            >
              <div className="flex items-center justify-between mb-2">
                <item.icon className="w-5 h-5 text-brand-500 group-hover:scale-110 transition-transform" />
                <span className="text-[10px] font-mono px-2 py-0.5 bg-brand-500/10 text-brand-600 rounded border border-brand-500/20">{item.rows}</span>
              </div>
              <h4 className="text-sm font-bold text-slate-900 group-hover:text-brand-600 transition-colors">{item.label}</h4>
              <p className="text-[11px] text-slate-500 mt-1 line-clamp-1">{item.desc}</p>
            </button>
          ))}
        </div>
      </section>

      {/* 6 Core Platform Features Grid */}
      <section className="space-y-8 max-w-6xl mx-auto px-4">
        <div className="text-center space-y-2 max-w-xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900">Full-Stack Data Science Workbench</h2>
          <p className="text-xs sm:text-sm text-slate-600">Everything you need to profile, wrangle, transform, and model data with complete safety.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            {
              icon: Activity,
              title: '1. Instant Statistical Profiling',
              desc: 'Automatic missingness detection, distribution sparklines, duplicate detection, and anomaly alerts calculated in milliseconds.',
              tab: 'profiling'
            },
            {
              icon: FileSpreadsheet,
              title: '2. Smart Spreadsheet Editor',
              desc: 'High-density grid view with inline cell editing, formula bar, column type coercion, and immediate preview of modified data.',
              tab: 'editor'
            },
            {
              icon: Sparkles,
              title: '3. AI Conversational Copilot',
              desc: 'Describe data transformations in plain English. Generates Python pandas code evaluated against strict security AST whitelists.',
              tab: 'chat'
            },
            {
              icon: ShieldCheck,
              title: '4. Whitelisted AST Execution',
              desc: 'Sandboxed code executor prevents dangerous system calls (eval, os, subprocess) while preserving 100% deterministic reproducibility.',
              tab: 'chat'
            },
            {
              icon: BrainCircuit,
              title: '5. AutoML Model Training',
              desc: 'Automated problem detection, feature matrix preparation, model training (XGBoost, Random Forest, Logistic Reg), and leaderboards.',
              tab: 'automl'
            }
          ].map((feature, idx) => (
            <div
              key={idx}
              onClick={() => setActiveTab(feature.tab as any)}
              className="glass-panel p-6 rounded-2xl border border-slate-200 hover:border-brand-500/40 hover:bg-white transition-all cursor-pointer group flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 bg-brand-500/10 rounded-xl flex items-center justify-center text-brand-600 group-hover:bg-brand-500/20 transition-colors">
                  <feature.icon className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900 group-hover:text-brand-600 transition-colors">{feature.title}</h3>
                <p className="text-xs text-slate-600 leading-relaxed">{feature.desc}</p>
              </div>
              <div className="flex items-center text-xs font-semibold text-brand-600 group-hover:translate-x-1 transition-transform">
                Explore feature <ChevronRight className="w-4 h-4 ml-1" />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Live Interactive Preview Teaser */}
      <section className="max-w-6xl mx-auto px-4 space-y-6">
        <div className="glass-panel-glow rounded-3xl border border-brand-500/30 p-6 sm:p-8 overflow-hidden space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-6">
            <div>
              <span className="text-xs font-mono font-bold text-brand-600 uppercase tracking-widest">Interactive Teaser</span>
              <h3 className="text-xl font-bold text-slate-900 mt-1">Experience the Sky Blue Data Studio</h3>
            </div>

            <div className="flex items-center gap-2 bg-slate-100 p-1.5 rounded-xl border border-slate-200">
              {[
                { id: 'profiling', label: 'Profiling Sparklines' },
                { id: 'copilot', label: 'AI Copilot Diffs' },
                { id: 'automl', label: 'AutoML Leaderboard' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActivePreviewTab(tab.id as any)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activePreviewTab === tab.id
                      ? 'bg-brand-500 text-white shadow-md shadow-brand-500/30'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Interactive Preview Content Container */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 min-h-[220px] shadow-sm">
            {activePreviewTab === 'profiling' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span className="font-mono">Dataset: student_performance.csv (1,000 rows x 8 cols)</span>
                  <span className="text-sky-600 flex items-center gap-1 font-semibold"><CheckCircle2 className="w-3.5 h-3.5" /> 100% Quality Score</span>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {['math_score', 'reading_score', 'writing_score'].map(col => (
                    <div key={col} className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                      <div className="flex justify-between text-xs font-mono text-slate-900 font-bold">
                        <span>{col}</span>
                        <span className="text-brand-600">float64</span>
                      </div>
                      <div className="flex items-end gap-1 h-10 w-full bg-slate-200 p-1 rounded">
                        {[40, 65, 80, 95, 70, 85, 90, 50, 75, 88].map((val, i) => (
                          <div key={i} className="bg-brand-500 rounded-t-sm w-full" style={{ height: `${val}%` }} />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activePreviewTab === 'copilot' && (
              <div className="space-y-3 font-mono text-xs">
                <div className="p-3 bg-brand-500/10 border border-brand-500/20 rounded-xl text-brand-700 flex items-center gap-2 font-semibold">
                  <Terminal className="w-4 h-4 text-brand-600" />
                  <span>Prompt: "Fill missing math_score values with median and normalize reading_score"</span>
                </div>
                <div className="p-3 bg-slate-900 rounded-xl border border-slate-800 text-slate-200 overflow-x-auto shadow-inner">
                  <pre className="text-[11px] leading-relaxed">
                    <span className="text-slate-400"># Generated Sandboxed AST Whitelisted Code</span>{'\n'}
                    <span className="text-cyan-400">median_val</span> = df[<span className="text-emerald-300">'math_score'</span>].median(){'\n'}
                    df[<span className="text-emerald-300">'math_score'</span>] = df[<span className="text-emerald-300">'math_score'</span>].fillna(median_val){'\n'}
                    df[<span className="text-emerald-300">'reading_score_norm'</span>] = (df[<span className="text-emerald-300">'reading_score'</span>] - df[<span className="text-emerald-300">'reading_score'</span>].min()) / (df[<span className="text-emerald-300">'reading_score'</span>].max() - df[<span className="text-emerald-300">'reading_score'</span>].min())
                  </pre>
                </div>
              </div>
            )}

            {activePreviewTab === 'automl' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-600 font-mono">
                  <span>Target: math_score (Regression)</span>
                  <span className="text-brand-600 font-bold">Top Algo: XGBoost Regressor</span>
                </div>
                <div className="space-y-2">
                  {[
                    { model: 'XGBoost Regressor', r2: '0.884', rmse: '4.21', recommended: true },
                    { model: 'Random Forest Regressor', r2: '0.862', rmse: '4.58', recommended: false },
                    { model: 'Linear Regression', r2: '0.810', rmse: '5.12', recommended: false }
                  ].map((m, i) => (
                    <div key={i} className={`p-3 rounded-xl border flex items-center justify-between text-xs ${
                      m.recommended ? 'bg-brand-500/10 border-brand-500/30 text-slate-900' : 'bg-slate-50 border-slate-200 text-slate-600'
                    }`}>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900">{m.model}</span>
                        {m.recommended && <span className="px-2 py-0.5 bg-brand-500 text-white rounded text-[10px] font-bold uppercase shadow-sm">Top Candidate</span>}
                      </div>
                      <div className="flex gap-4 font-mono">
                        <span>R²: <strong className="text-brand-600">{m.r2}</strong></span>
                        <span>RMSE: <strong className="text-slate-800">{m.rmse}</strong></span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="max-w-6xl mx-auto px-4 pt-8 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-brand-gradient rounded-lg flex items-center justify-center text-white">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <span className="font-bold text-slate-900">DataForge AI</span>
          <span>— Sky Blue Data Wrangling & AutoML Platform</span>
        </div>

        <div className="flex items-center gap-4 text-slate-500 font-mono text-[11px]">
          <span>Next.js 15</span>
          <span>•</span>
          <span>FastAPI</span>
          <span>•</span>
          <span>Python AST Sandbox</span>
          <span>•</span>
          <span>Three.js</span>
        </div>
      </footer>
    </div>
  );
}

function handleScrollToUpload() {
  const el = document.getElementById('upload-section');
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' });
  }
}
