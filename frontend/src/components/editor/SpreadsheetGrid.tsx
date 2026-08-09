import React, { useState } from 'react';
import { useAppStore } from '@/lib/store';
import { Table, Search, ChevronLeft, ChevronRight, Layers } from 'lucide-react';
import DownloadSplitButton from '@/components/common/DownloadSplitButton';
import CodeExportModal from '@/components/common/CodeExportModal';

export default function SpreadsheetGrid() {
  const { preview, currentDataset } = useAppStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [isCodeModalOpen, setIsCodeModalOpen] = useState(false);
  const [codeModalFormat, setCodeModalFormat] = useState<'py' | 'ipynb'>('py');
  const pageSize = 15;

  if (!preview || !preview.rows) {
    return (
      <div className="flex flex-col items-center justify-center p-12 glass-panel rounded-2xl min-h-[400px]">
        <Table className="w-10 h-10 text-gray-500 mb-3 animate-pulse" />
        <p className="text-gray-400 text-sm">No dataset loaded in spreadsheet view.</p>
      </div>
    );
  }

  const filteredRows = preview.rows.filter((row) =>
    Object.values(row).some(
      (val) => val !== null && String(val).toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  const totalPages = Math.ceil(filteredRows.length / pageSize) || 1;
  const paginatedRows = filteredRows.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <div className="glass-panel rounded-2xl border border-white/5 overflow-hidden flex flex-col h-full">
      {/* Header Toolbar */}
      <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-50/80">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-brand-500/10 text-brand-600 rounded-lg">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-900">Live Data Table</h4>
            <p className="text-xs text-slate-500">
              Showing {filteredRows.length} of {preview.total_rows} rows • Version #{preview.version_number}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search values..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="pl-9 pr-4 py-1.5 bg-white border border-slate-300 rounded-xl text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-brand-500 w-48 sm:w-64 shadow-sm"
            />
          </div>

          <DownloadSplitButton
            datasetId={currentDataset?.id || preview.dataset_id}
            versionId={preview.version_id}
            datasetName={currentDataset?.name}
            versionNumber={preview.version_number}
            onOpenCodeModal={(fmt) => {
              setCodeModalFormat(fmt || 'py');
              setIsCodeModalOpen(true);
            }}
          />
        </div>
      </div>

      {/* Grid Container */}
      <div className="overflow-x-auto overflow-y-auto max-h-[520px] flex-1">
        <table className="w-full text-left text-xs border-collapse font-mono">
          <thead className="sticky top-0 bg-slate-100 z-10 border-b border-slate-200 shadow-sm">
            <tr>
              <th className="py-2.5 px-3 bg-slate-100 text-slate-500 border-r border-slate-200 text-center w-12 font-sans font-bold">
                #
              </th>
              {preview.columns.map((col) => (
                <th key={col} className="py-2.5 px-4 text-slate-700 border-r border-slate-200 font-medium min-w-[140px]">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-slate-900 font-bold truncate">{col}</span>
                    <span className="text-[10px] text-slate-500 uppercase font-sans px-1.5 py-0.5 bg-slate-200 rounded font-semibold">
                      {preview.dtypes[col] || 'str'}
                    </span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {paginatedRows.length > 0 ? (
              paginatedRows.map((row, idx) => {
                const rowNum = (currentPage - 1) * pageSize + idx + 1;
                return (
                  <tr key={idx} className="hover:bg-slate-50 transition-colors">
                    <td className="py-2 px-3 text-center text-slate-400 border-r border-slate-200 bg-slate-50/80 select-none font-sans">
                      {rowNum}
                    </td>
                    {preview.columns.map((col) => (
                      <td key={col} className="py-2 px-4 text-slate-800 border-r border-slate-100 truncate max-w-[240px]">
                        {row[col] === null || row[col] === undefined ? (
                          <em className="text-slate-400 text-[11px]">null</em>
                        ) : (
                          String(row[col])
                        )}
                      </td>
                    ))}
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={preview.columns.length + 1} className="py-8 text-center text-slate-400 font-sans">
                  No matching rows found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-3 border-t border-slate-200 bg-slate-50/80 flex items-center justify-between text-xs text-slate-600">
        <span>
          Page {currentPage} of {totalPages}
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="p-1.5 bg-white border border-slate-300 rounded-lg hover:bg-slate-100 disabled:opacity-40 disabled:pointer-events-none text-slate-700 cursor-pointer shadow-sm"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="p-1.5 bg-white border border-slate-300 rounded-lg hover:bg-slate-100 disabled:opacity-40 disabled:pointer-events-none text-slate-700 cursor-pointer shadow-sm"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      <CodeExportModal
        isOpen={isCodeModalOpen}
        onClose={() => setIsCodeModalOpen(false)}
        versionId={preview.version_id}
        datasetName={currentDataset?.name}
        versionNumber={preview.version_number}
        initialFormat={codeModalFormat}
      />
    </div>
  );
}

