'use client';

import React from 'react';
import { useAppStore } from '@/lib/store';
import { Database, Hash, AlertTriangle, Layers, Activity, FileSpreadsheet } from 'lucide-react';
import { ColumnProfile } from '@/lib/types';

import DownloadSplitButton from '@/components/common/DownloadSplitButton';
import CodeExportModal from '@/components/common/CodeExportModal';

export default function ProfilingDashboard() {
  const { profile, currentDataset, currentVersionId } = useAppStore();
  const [isCodeModalOpen, setIsCodeModalOpen] = React.useState(false);
  const [codeModalFormat, setCodeModalFormat] = React.useState<'py' | 'ipynb'>('py');

  if (!profile) {
    return (
      <div className="flex flex-col items-center justify-center p-12 glass-panel rounded-2xl min-h-[400px]">
        <Activity className="w-12 h-12 text-brand-500 animate-spin mb-4" />
        <p className="text-gray-400 text-sm">Computing dataset statistics & sparklines...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Stat Summary Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-2xl border border-slate-200 flex items-center gap-4">
          <div className="p-3 bg-brand-500/10 rounded-xl text-brand-600">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Rows</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">{profile.row_count.toLocaleString()}</h3>
          </div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-200 flex items-center gap-4">
          <div className="p-3 bg-cyan-500/10 rounded-xl text-cyan-600">
            <Hash className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Columns</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">{profile.col_count}</h3>
          </div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-200 flex items-center gap-4">
          <div className="p-3 bg-amber-500/10 rounded-xl text-amber-600">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Missing Cells</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">{profile.total_missing_cells.toLocaleString()}</h3>
          </div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-200 flex items-center gap-4">
          <div className="p-3 bg-sky-500/10 rounded-xl text-sky-600">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Duplicate Rows</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">{profile.duplicate_rows}</h3>
          </div>
        </div>
      </div>

      {/* Column Details Table */}
      <div className="glass-panel rounded-2xl border border-slate-200 p-6 overflow-hidden">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-brand-600" />
              Column Profiles & Distributions
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Cached statistical breakdown for {currentDataset?.name} (Version #{profile.version_number})
            </p>
          </div>

          <DownloadSplitButton
            datasetId={currentDataset?.id}
            versionId={currentVersionId || profile.version_id}
            datasetName={currentDataset?.name}
            versionNumber={profile.version_number}
            onOpenCodeModal={(fmt) => {
              setCodeModalFormat(fmt || 'py');
              setIsCodeModalOpen(true);
            }}
          />
        </div>


        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-700 border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider bg-slate-50/50">
                <th className="py-3 px-4">Column Name</th>
                <th className="py-3 px-4">Data Type</th>
                <th className="py-3 px-4">Missingness</th>
                <th className="py-3 px-4">Uniques</th>
                <th className="py-3 px-4">Sample Values</th>
                <th className="py-3 px-4">Distribution (Sparkline)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {profile.columns.map((col: ColumnProfile) => (
                <tr key={col.name} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-4 px-4 font-mono font-bold text-slate-900">{col.name}</td>
                  <td className="py-4 px-4">
                    <span className={`inline-block px-2.5 py-1 rounded-full text-xs font-semibold border ${
                      col.dtype === 'numeric' ? 'bg-cyan-500/10 text-cyan-700 border-cyan-500/30' :
                      col.dtype === 'categorical' ? 'bg-sky-500/10 text-sky-700 border-sky-500/30' :
                      col.dtype === 'datetime' ? 'bg-amber-500/10 text-amber-700 border-amber-500/30' :
                      'bg-slate-100 text-slate-700 border-slate-300'
                    }`}>
                      {col.dtype}
                    </span>
                  </td>
                  <td className="py-4 px-4 min-w-[140px]">
                    <div className="flex items-center gap-2">
                      <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${col.missing_pct > 20 ? 'bg-amber-500' : 'bg-brand-500'}`}
                          style={{ width: `${Math.min(100, col.missing_pct)}%` }}
                        />
                      </div>
                      <span className="text-xs font-mono text-slate-500 min-w-[36px]">{col.missing_pct}%</span>
                    </div>
                  </td>
                  <td className="py-4 px-4 font-mono text-slate-700">{col.unique_count}</td>
                  <td className="py-4 px-4">
                    <div className="flex flex-wrap gap-1 max-w-xs">
                      {col.sample_values.slice(0, 3).map((val, idx) => (
                        <span key={idx} className="px-2 py-0.5 bg-slate-100 border border-slate-200 rounded text-xs font-mono text-slate-700 truncate max-w-[100px]">
                          {val === null ? <em className="text-slate-400">null</em> : String(val)}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    {col.histogram && col.histogram.length > 0 ? (
                      <div className="flex items-end gap-1 h-8 w-28 bg-slate-100 p-1 rounded border border-slate-200">
                        {(() => {
                          const maxCount = Math.max(...col.histogram.map(h => h.count), 1);
                          return col.histogram.map((h, i) => (
                            <div
                              key={i}
                              title={`${h.bin}: ${h.count}`}
                              className="bg-brand-500 hover:bg-cyan-600 transition-colors w-full rounded-t-sm"
                              style={{ height: `${Math.max(10, (h.count / maxCount) * 100)}%` }}
                            />
                          ));
                        })()}
                      </div>
                    ) : col.stats.top_categories ? (
                      <span className="text-xs text-slate-500 font-mono">
                        Top: {Object.keys(col.stats.top_categories)[0] || 'N/A'}
                      </span>
                    ) : (
                      <span className="text-xs text-slate-400">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <CodeExportModal
        isOpen={isCodeModalOpen}
        onClose={() => setIsCodeModalOpen(false)}
        versionId={currentVersionId || profile?.version_id}
        datasetName={currentDataset?.name}
        versionNumber={profile?.version_number || 1}
        initialFormat={codeModalFormat}
      />
    </div>
  );
}

