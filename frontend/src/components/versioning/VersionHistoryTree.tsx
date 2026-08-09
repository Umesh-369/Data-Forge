import React, { useEffect, useState } from 'react';
import { useAppStore } from '@/lib/store';
import { fetchVersionLineage, revertToVersion, fetchDatasetProfile } from '@/lib/api';
import { GitCommit, RotateCcw, Clock, Layers, ArrowDown, Code2 } from 'lucide-react';
import { VersionNode } from '@/lib/types';
import CodeExportModal from '@/components/common/CodeExportModal';
import DownloadSplitButton from '@/components/common/DownloadSplitButton';

export default function VersionHistoryTree() {
  const { currentDataset, currentVersionId, lineage, setLineage, setPreview, setProfile, setCurrentVersionId } = useAppStore();
  const [selectedVersionForCode, setSelectedVersionForCode] = useState<{ id: string; num: number } | null>(null);

  useEffect(() => {
    if (currentDataset) {
      fetchVersionLineage(currentDataset.id).then(setLineage).catch(console.error);
    }
  }, [currentDataset, currentVersionId, setLineage]);

  const handleRevert = async (versionId: string) => {
    if (!currentDataset) return;
    try {
      const targetPreview = await revertToVersion(currentDataset.id, versionId);
      setPreview(targetPreview);
      setCurrentVersionId(versionId);
      const updatedProfile = await fetchDatasetProfile(currentDataset.id, versionId);
      setProfile(updatedProfile);
    } catch (err) {
      console.error('Failed to revert version:', err);
    }
  };

  if (!lineage || lineage.versions.length === 0) {
    return (
      <div className="glass-panel p-8 rounded-2xl text-center text-gray-400">
        No version history available for this dataset.
      </div>
    );
  }

  return (
    <div className="glass-panel rounded-2xl border border-white/5 p-6 space-y-6">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <GitCommit className="w-5 h-5 text-brand-400" /> Immutable Version Lineage Tree
          </h3>
          <p className="text-xs text-gray-400 mt-1">
            Complete audit trail of all transformations applied (Invariants I1 & I2).
          </p>
        </div>
        <span className="text-xs text-gray-400 font-mono">Total Versions: {lineage.versions.length}</span>
      </div>

      <div className="relative pl-6 space-y-6 before:absolute before:left-3 before:top-3 before:bottom-3 before:w-0.5 before:bg-gradient-to-b before:from-brand-500 before:to-cyan-500">
        {lineage.versions.map((ver: VersionNode, idx: number) => {
          const isCurrent = ver.version_id === currentVersionId;
          return (
            <div key={ver.version_id} className="relative group">
              {/* Timeline Dot */}
              <div
                className={`absolute -left-6 top-1.5 w-3.5 h-3.5 rounded-full border-2 transition-all ${
                  isCurrent
                    ? 'bg-brand-500 border-white ring-4 ring-brand-500/20'
                    : 'bg-dark-900 border-gray-600 group-hover:border-brand-400'
                }`}
              />

              <div className={`p-4 rounded-xl border transition-all ${
                isCurrent ? 'glass-panel-glow border-brand-500/50' : 'bg-dark-850/50 border-white/5 hover:border-white/15'
              }`}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white font-mono">Version #{ver.version_number}</span>
                      {isCurrent && (
                        <span className="px-2 py-0.5 bg-brand-500/20 text-brand-300 text-[10px] rounded-full border border-brand-500/30 font-semibold uppercase">
                          Active State
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 flex items-center gap-1 mt-1 font-mono">
                      <Clock className="w-3 h-3 text-gray-500" />
                      {new Date(ver.created_at).toLocaleString()} • {ver.row_count} rows, {ver.col_count} cols
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <DownloadSplitButton
                      datasetId={currentDataset?.id}
                      versionId={ver.version_id}
                      datasetName={currentDataset?.name}
                      versionNumber={ver.version_number}
                      onOpenCodeModal={() => setSelectedVersionForCode({ id: ver.version_id, num: ver.version_number })}
                    />

                    {!isCurrent && (
                      <button
                        type="button"
                        onClick={() => handleRevert(ver.version_id)}
                        className="py-1.5 px-3 bg-dark-800 hover:bg-brand-500/20 border border-white/10 hover:border-brand-500/40 rounded-lg text-xs font-medium text-gray-300 hover:text-white flex items-center gap-1.5 transition-all cursor-pointer"
                      >
                        <RotateCcw className="w-3.5 h-3.5 text-brand-400" /> Revert
                      </button>
                    )}
                  </div>
                </div>

                {/* Operation details */}
                {ver.transformation_op && (
                  <div className="mt-3 pt-3 border-t border-white/5">
                    <p className="text-[11px] text-gray-400 font-medium">Transformation Details:</p>
                    <pre className="text-[11px] font-mono bg-dark-900/60 p-2 rounded text-cyan-300 mt-1 overflow-x-auto">
                      {JSON.stringify(ver.transformation_op, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Code Export Modal scoped to selected version */}
      <CodeExportModal
        isOpen={Boolean(selectedVersionForCode)}
        onClose={() => setSelectedVersionForCode(null)}
        versionId={selectedVersionForCode?.id}
        datasetName={currentDataset?.name}
        versionNumber={selectedVersionForCode?.num}
      />
    </div>
  );
}

