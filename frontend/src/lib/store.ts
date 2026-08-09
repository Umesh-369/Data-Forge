import { create } from 'zustand';
import {
  DatasetSummary, DatasetProfile, PreviewData, ProposedEdit,
  AutoMLRecommend, TrainModelResult, VersionLineage
} from './types';

interface AppState {
  currentDataset: DatasetSummary | null;
  currentVersionId: string | null;
  profile: DatasetProfile | null;
  preview: PreviewData | null;
  activeTab: 'landing' | 'profiling' | 'editor' | 'chat' | 'automl';
  pendingEdit: ProposedEdit | null;
  recommendations: AutoMLRecommend | null;
  trainingResults: TrainModelResult | null;
  lineage: VersionLineage | null;
  isLoading: boolean;
  error: string | null;

  setCurrentDataset: (dataset: DatasetSummary | null) => void;
  setCurrentVersionId: (versionId: string | null) => void;
  setProfile: (profile: DatasetProfile | null) => void;
  setPreview: (preview: PreviewData | null) => void;
  setActiveTab: (tab: 'landing' | 'profiling' | 'editor' | 'chat' | 'automl') => void;
  setPendingEdit: (edit: ProposedEdit | null) => void;
  setRecommendations: (recs: AutoMLRecommend | null) => void;
  setTrainingResults: (results: TrainModelResult | null) => void;
  setLineage: (lineage: VersionLineage | null) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentDataset: null,
  currentVersionId: null,
  profile: null,
  preview: null,
  activeTab: 'landing',
  pendingEdit: null,
  recommendations: null,
  trainingResults: null,
  lineage: null,
  isLoading: false,
  error: null,

  setCurrentDataset: (dataset) => set({ currentDataset: dataset }),
  setCurrentVersionId: (versionId) => set({ currentVersionId: versionId }),
  setProfile: (profile) => set({ profile }),
  setPreview: (preview) => set({ preview }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setPendingEdit: (pendingEdit) => set({ pendingEdit }),
  setRecommendations: (recommendations) => set({ recommendations }),
  setTrainingResults: (trainingResults) => set({ trainingResults }),
  setLineage: (lineage) => set({ lineage }),
  setIsLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}));

