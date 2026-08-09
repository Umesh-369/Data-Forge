export interface DatasetSummary {
  id: string;
  name: string;
  original_filename: string;
  file_type: string;
  current_version_id: string;
  version_number: number;
  row_count: number;
  col_count: number;
  created_at: string;
}

export interface ColumnProfile {
  name: string;
  dtype: 'numeric' | 'categorical' | 'datetime' | 'boolean';
  missing_count: number;
  missing_pct: number;
  unique_count: number;
  sample_values: (string | number | boolean | null)[];
  stats: Record<string, any>;
  histogram?: { bin: string; count: number }[];
}

export interface DatasetProfile {
  dataset_id: string;
  version_id: string;
  version_number: number;
  row_count: number;
  col_count: number;
  duplicate_rows: number;
  total_missing_cells: number;
  columns: ColumnProfile[];
}

export interface PreviewData {
  dataset_id: string;
  version_id: string;
  version_number: number;
  columns: string[];
  dtypes: Record<string, string>;
  total_rows: number;
  rows: Record<string, any>[];
}

export interface DiffSummary {
  cols_added: string[];
  cols_dropped: string[];
  cols_renamed: Record<string, string>;
  rows_before: number;
  rows_after: number;
  affected_rows_count: number;
  sample_before: Record<string, any>[];
  sample_after: Record<string, any>[];
}

export interface ProposedEdit {
  edit_log_id: string;
  user_prompt: string;
  proposed_operations: Record<string, any>[];
  explanation: string;
  diff_summary: DiffSummary;
}

export interface RecommendationCandidate {
  algorithm: string;
  score: number;
  reasoning: string[];
  recommended: boolean;
}

export interface AutoMLRecommend {
  dataset_id: string;
  version_id: string;
  target_column: string;
  problem_type: 'classification' | 'regression';
  class_balance?: Record<string, number>;
  feature_count: number;
  candidates: RecommendationCandidate[];
}

export interface TrainModelResult {
  job_id: string;
  status: string;
  problem_type: 'classification' | 'regression';
  metrics: Record<string, number>;
  confusion_matrix?: number[][];
  feature_importances?: Record<string, number>;
  residual_plot_data?: { actual: number; predicted: number; residual: number }[];
}

export interface VersionNode {
  version_id: string;
  version_number: number;
  parent_version_id: string | null;
  transformation_op: Record<string, any> | null;
  row_count: number;
  col_count: number;
  created_at: string;
}

export interface VersionLineage {
  dataset_id: string;
  current_version_id: string;
  versions: VersionNode[];
}

export interface ExcludedOp {
  operation: string;
  reason: string;
}

export interface CodeExportResult {
  version_id: string;
  format: 'py' | 'ipynb';
  filename: string;
  code: string;
  excluded_operations: ExcludedOp[];
}

export interface AutoPipelineResult {
  dataset_id: string;
  version_id: string;
  target_column: string;
  target_detection_reason: string;
  cleaning_logs: string[];
  problem_type: 'classification' | 'regression';
  class_balance?: Record<string, number>;
  feature_count: number;
  candidates: RecommendationCandidate[];
  selected_algorithm: string;
  training_results: TrainModelResult;
  cleaned_row_count: number;
  cleaned_col_count: number;
}


