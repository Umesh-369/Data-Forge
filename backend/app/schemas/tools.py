from typing import Literal, List, Optional, Union, Any, Dict
from pydantic import BaseModel, Field

# 1. Add Column
class AddColumnOp(BaseModel):
    tool: Literal["add_column"] = "add_column"
    name: str = Field(..., description="Name of the new column to create")
    expression_type: Literal["formula", "constant", "conditional"] = Field(
        ..., description="Type of expression: formula (e.g. colA + colB), constant, or conditional"
    )
    params: Dict[str, Any] = Field(
        ..., description="Parameters such as {'expression': 'colA * 2'} or {'constant': 100} or {'condition': 'colA > 10', 'true_val': 'High', 'false_val': 'Low'}"
    )

# 2. Drop Column
class DropColumnOp(BaseModel):
    tool: Literal["drop_column"] = "drop_column"
    name: str = Field(..., description="Name of the column to drop")

# 3. Rename Column
class RenameColumnOp(BaseModel):
    tool: Literal["rename_column"] = "rename_column"
    old_name: str = Field(..., description="Current name of the column")
    new_name: str = Field(..., description="New name for the column")

# 4. Filter Rows
class FilterRowsOp(BaseModel):
    tool: Literal["filter_rows"] = "filter_rows"
    condition_column: str = Field(..., description="Column to evaluate condition on")
    operator: Literal["==", "!=", ">", "<", ">=", "<=", "contains", "is_null", "not_null"] = Field(
        ..., description="Comparison operator"
    )
    value: Optional[Any] = Field(None, description="Value to compare against (ignored for is_null / not_null)")

# 5. Fill NA
class FillNAOp(BaseModel):
    tool: Literal["fillna"] = "fillna"
    column: str = Field(..., description="Target column to fill missing values in")
    strategy: Literal["mean", "median", "mode", "constant", "ffill", "bfill"] = Field(
        ..., description="Strategy to fill missing values"
    )
    fill_value: Optional[Any] = Field(None, description="Value to fill if strategy is 'constant'")

# 6. Drop NA
class DropNAOp(BaseModel):
    tool: Literal["dropna"] = "dropna"
    subset: Optional[List[str]] = Field(None, description="List of columns to check for missing values")
    how: Literal["any", "all"] = Field("any", description="Drop row if any or all specified columns are null")

# 7. Extract Pattern
class ExtractPatternOp(BaseModel):
    tool: Literal["extract_pattern"] = "extract_pattern"
    source_column: str = Field(..., description="Source text column to extract pattern from")
    new_column: str = Field(..., description="Name of the new column for extracted values")
    pattern_type: Literal["regex", "email_username", "email_domain", "digits", "text_before", "text_after"] = Field(
        ..., description="Type of pattern to extract"
    )
    pattern: Optional[str] = Field(None, description="Regex pattern or delimiter string if required")

# 8. Bucket Column
class BucketColumnOp(BaseModel):
    tool: Literal["bucket_column"] = "bucket_column"
    source_column: str = Field(..., description="Source numeric column to bucket")
    new_column: str = Field(..., description="Name of the new bucketed categorical column")
    bins: List[float] = Field(..., description="List of numerical cut points e.g. [0, 50000, 100000, 1000000]")
    labels: List[str] = Field(..., description="List of bin labels e.g. ['low', 'medium', 'high']")

# 9. AsType
class AsTypeOp(BaseModel):
    tool: Literal["astype"] = "astype"
    column: str = Field(..., description="Column to change type for")
    target_dtype: Literal["int64", "float64", "string", "category", "datetime64[ns]", "bool"] = Field(
        ..., description="Target data type"
    )

# 10. Merge Columns
class MergeColumnsOp(BaseModel):
    tool: Literal["merge_columns"] = "merge_columns"
    columns: List[str] = Field(..., description="List of column names to concatenate")
    new_column: str = Field(..., description="Name of the new merged column")
    separator: str = Field(" ", description="Separator string between column values")

# 11. Dedupe
class DedupeOp(BaseModel):
    tool: Literal["dedupe"] = "dedupe"
    subset: Optional[List[str]] = Field(None, description="Columns to consider when identifying duplicate rows")
    keep: Literal["first", "last"] = Field("first", description="Which duplicate to keep")

# Union of all whitelisted operations
WhitelistedOp = Union[
    AddColumnOp,
    DropColumnOp,
    RenameColumnOp,
    FilterRowsOp,
    FillNAOp,
    DropNAOp,
    ExtractPatternOp,
    BucketColumnOp,
    AsTypeOp,
    MergeColumnsOp,
    DedupeOp
]

class OperationPayload(BaseModel):
    operations: List[WhitelistedOp] = Field(..., description="List of whitelisted operations to execute sequentially")
