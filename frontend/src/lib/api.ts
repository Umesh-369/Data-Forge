import {
  DatasetSummary, DatasetProfile, PreviewData, ProposedEdit,
  AutoMLRecommend, TrainModelResult, VersionLineage, CodeExportResult, AutoPipelineResult
} from './types';


const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export async function fetchDatasets(): Promise<DatasetSummary[]> {
  const res = await fetch(`${API_BASE}/datasets`);
  if (!res.ok) throw new Error('Failed to fetch datasets');
  return res.json();
}

export async function uploadDataset(file: File): Promise<DatasetSummary> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/datasets/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Upload failed');
  }
  return res.json();
}

export async function loadSeedDataset(seedName: string): Promise<DatasetSummary> {
  const res = await fetch(`${API_BASE}/datasets/load-seed/${seedName}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to load seed dataset');
  return res.json();
}

export async function fetchDatasetProfile(datasetId: string, versionId?: string): Promise<DatasetProfile> {
  const url = versionId
    ? `${API_BASE}/datasets/${datasetId}/profile?version_id=${versionId}`
    : `${API_BASE}/datasets/${datasetId}/profile`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch dataset profile');
  return res.json();
}

export async function fetchDatasetPreview(datasetId: string, versionId?: string, limit = 100): Promise<PreviewData> {
  const url = versionId
    ? `${API_BASE}/datasets/${datasetId}/preview?version_id=${versionId}&limit=${limit}`
    : `${API_BASE}/datasets/${datasetId}/preview?limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch dataset preview');
  return res.json();
}

export function getDatasetExportUrl(datasetId: string, versionId?: string, format: 'csv' | 'xlsx' | 'json' = 'csv'): string {
  const validVersion = versionId && versionId !== 'undefined' && versionId !== 'null' ? versionId : undefined;
  return validVersion
    ? `${API_BASE}/datasets/${datasetId}/export?version_id=${validVersion}&format=${format}`
    : `${API_BASE}/datasets/${datasetId}/export?format=${format}`;
}

export async function downloadDatasetFile(
  datasetId: string,
  versionId?: string,
  format: 'csv' | 'xlsx' | 'json' = 'csv',
  defaultFilename = 'dataset'
): Promise<void> {
  const url = getDatasetExportUrl(datasetId, versionId, format);
  const res = await fetch(url);
  if (!res.ok) {
    const errText = await res.text().catch(() => '');
    throw new Error(errText || 'Failed to download dataset export file');
  }
  const blob = await res.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = blobUrl;
  
  const contentDisposition = res.headers.get('Content-Disposition');
  let filename = `${defaultFilename}_export.${format}`;
  if (contentDisposition) {
    const match = contentDisposition.match(/filename="?([^"]+)"?/);
    if (match && match[1]) {
      filename = match[1];
    }
  }
  a.download = filename;
  document.body.appendChild(a);
  a.click();

  setTimeout(() => {
    if (document.body.contains(a)) {
      document.body.removeChild(a);
    }
    URL.revokeObjectURL(blobUrl);
  }, 1000);
}

export async function requestAgentEdit(datasetId: string, prompt: string, versionId?: string): Promise<ProposedEdit> {
  const url = versionId
    ? `${API_BASE}/agent/${datasetId}/edit?version_id=${versionId}`
    : `${API_BASE}/agent/${datasetId}/edit`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_prompt: prompt }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to generate edit proposal');
  }
  return res.json();
}

export async function confirmOrRejectEdit(datasetId: string, editLogId: string, action: 'confirm' | 'reject'): Promise<PreviewData> {
  const res = await fetch(`${API_BASE}/agent/${datasetId}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ edit_log_id: editLogId, action }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to process confirmation');
  }
  return res.json();
}

export async function runAutoMLPipeline(datasetId: string, targetColumn?: string, versionId?: string): Promise<AutoPipelineResult> {
  const url = versionId
    ? `${API_BASE}/auto-ml/${datasetId}/auto-pipeline?version_id=${versionId}`
    : `${API_BASE}/auto-ml/${datasetId}/auto-pipeline`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_column: targetColumn || null }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'AutoML pipeline failed');
  }
  return res.json();
}

export async function downloadCleanedDataset(
  datasetId: string,
  targetColumn?: string,
  versionId?: string,
  format: 'csv' | 'xlsx' = 'csv',
  defaultFilename = 'dataset'
): Promise<void> {
  let url = `${API_BASE}/auto-ml/${datasetId}/export-cleaned?format=${format}`;
  if (versionId && versionId !== 'undefined' && versionId !== 'null') {
    url += `&version_id=${versionId}`;
  }
  if (targetColumn) {
    url += `&target_column=${encodeURIComponent(targetColumn)}`;
  }
  const res = await fetch(url);
  if (!res.ok) {
    const errText = await res.text().catch(() => '');
    throw new Error(errText || 'Failed to download cleaned dataset export');
  }
  const blob = await res.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = blobUrl;
  
  const contentDisposition = res.headers.get('Content-Disposition');
  let filename = `${defaultFilename}_cleaned.${format}`;
  if (contentDisposition) {
    const match = contentDisposition.match(/filename="?([^"]+)"?/);
    if (match && match[1]) {
      filename = match[1];
    }
  }
  a.download = filename;
  document.body.appendChild(a);
  a.click();

  setTimeout(() => {
    if (document.body.contains(a)) {
      document.body.removeChild(a);
    }
    URL.revokeObjectURL(blobUrl);
  }, 1000);
}

export async function fetchAutoMLRecommendations(datasetId: string, targetColumn: string, versionId?: string): Promise<AutoMLRecommend> {
  const url = versionId
    ? `${API_BASE}/auto-ml/${datasetId}/recommend?version_id=${versionId}`
    : `${API_BASE}/auto-ml/${datasetId}/recommend`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_column: targetColumn }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to fetch algorithm recommendations');
  }
  return res.json();
}

export async function trainAutoMLModel(datasetId: string, targetColumn: string, algorithm: string, versionId?: string): Promise<TrainModelResult> {
  const url = versionId
    ? `${API_BASE}/auto-ml/${datasetId}/train?version_id=${versionId}`
    : `${API_BASE}/auto-ml/${datasetId}/train`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_column: targetColumn, selected_algorithm: algorithm }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Model training failed');
  }
  return res.json();
}

export async function fetchVersionLineage(datasetId: string): Promise<VersionLineage> {
  const res = await fetch(`${API_BASE}/versions/${datasetId}`);
  if (!res.ok) throw new Error('Failed to fetch version lineage');
  return res.json();
}

export async function revertToVersion(datasetId: string, versionId: string): Promise<PreviewData> {
  const res = await fetch(`${API_BASE}/versions/${datasetId}/revert/${versionId}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to revert to version');
  return res.json();
}

export interface DatasetChatResponse {
  answer: string;
  computation_trace: string;
}

export async function sendDatasetChatMessage(
  versionId: string,
  message: string,
  conversationHistory: { role: string; content: string }[] = []
): Promise<DatasetChatResponse> {
  const res = await fetch(`${API_BASE}/versions/${versionId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, conversation_history: conversationHistory }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Data Chatbot request failed');
  }
  return res.json();
}

export async function exportVersionCode(
  versionId: string,
  format: 'py' | 'ipynb' = 'py',
  targetColumn?: string,
  algorithm?: string
): Promise<CodeExportResult> {
  const queryParams = new URLSearchParams({ format });
  if (targetColumn) queryParams.append('target_column', targetColumn);
  if (algorithm) queryParams.append('algorithm', algorithm);

  const res = await fetch(`${API_BASE}/versions/${versionId}/export/code?${queryParams.toString()}`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to export version code');
  }
  return res.json();
}

