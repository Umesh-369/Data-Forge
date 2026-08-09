from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class DatasetSummaryResponse(BaseModel):
    id: str
    name: str
    original_filename: str
    file_type: str
    current_version_id: str
    version_number: int
    row_count: int
    col_count: int
    created_at: datetime

class ColumnProfile(BaseModel):
    name: str
    dtype: str
    missing_count: int
    missing_pct: float
    unique_count: int
    sample_values: List[Any]
    stats: Dict[str, Any]
    histogram: Optional[List[Dict[str, Any]]] = None

class ProfileResponse(BaseModel):
    dataset_id: str
    version_id: str
    version_number: int
    row_count: int
    col_count: int
    duplicate_rows: int
    total_missing_cells: int
    columns: List[ColumnProfile]

class PreviewDataResponse(BaseModel):
    dataset_id: str
    version_id: str
    version_number: int
    columns: List[str]
    dtypes: Dict[str, str]
    total_rows: int
    rows: List[Dict[str, Any]]

class AgentEditRequest(BaseModel):
    user_prompt: str

class DiffSummary(BaseModel):
    cols_added: List[str]
    cols_dropped: List[str]
    cols_renamed: Dict[str, str]
    rows_before: int
    rows_after: int
    affected_rows_count: int
    sample_before: List[Dict[str, Any]]
    sample_after: List[Dict[str, Any]]

class AgentEditResponse(BaseModel):
    edit_log_id: str
    user_prompt: str
    proposed_operations: List[Dict[str, Any]]
    explanation: str
    diff_summary: DiffSummary

class ConfirmEditRequest(BaseModel):
    edit_log_id: str
    action: str # "confirm" or "reject"

class AutoMLRequest(BaseModel):
    target_column: Optional[str] = None

class RecommendationCandidate(BaseModel):
    algorithm: str
    score: float
    reasoning: List[str]
    recommended: bool

class AutoMLRecommendResponse(BaseModel):
    dataset_id: str
    version_id: str
    target_column: str
    problem_type: str
    class_balance: Optional[Dict[str, float]] = None
    feature_count: int
    candidates: List[RecommendationCandidate]

class TrainModelRequest(BaseModel):
    target_column: str
    selected_algorithm: str

class TrainModelResponse(BaseModel):
    job_id: str
    status: str
    problem_type: str
    metrics: Dict[str, float]
    confusion_matrix: Optional[List[List[int]]] = None
    feature_importances: Optional[Dict[str, float]] = None
    residual_plot_data: Optional[List[Dict[str, float]]] = None

class AutoPipelineResponse(BaseModel):
    dataset_id: str
    version_id: str
    target_column: str
    target_detection_reason: str
    cleaning_logs: List[str]
    problem_type: str
    class_balance: Optional[Dict[str, float]] = None
    feature_count: int
    candidates: List[RecommendationCandidate]
    selected_algorithm: str
    training_results: TrainModelResponse
    cleaned_row_count: int
    cleaned_col_count: int

class VersionNode(BaseModel):
    version_id: str
    version_number: int
    parent_version_id: Optional[str]
    transformation_op: Optional[Dict[str, Any]]
    row_count: int
    col_count: int
    created_at: datetime

class VersionLineageResponse(BaseModel):
    dataset_id: str
    current_version_id: str
    versions: List[VersionNode]

class DatasetChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, Any]]] = None

class DatasetChatResponse(BaseModel):
    answer: str
    computation_trace: str

class ExcludedOperation(BaseModel):
    operation: str
    reason: str

class CodeExportResponse(BaseModel):
    version_id: str
    format: str # py or ipynb
    filename: str
    code: str
    excluded_operations: List[ExcludedOperation] = []


