import re
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from app.schemas.tools import (
    WhitelistedOp, AddColumnOp, DropColumnOp, RenameColumnOp, FilterRowsOp,
    FillNAOp, DropNAOp, ExtractPatternOp, BucketColumnOp, AsTypeOp, MergeColumnsOp, DedupeOp
)

class SandboxExecutionError(Exception):
    pass

class SandboxExecutor:
    """
    Deterministic Sandbox Executor for Pandas operations.
    Fulfills Invariants I4, I5, I6.
    Executes only whitelisted operations generated from strict Pydantic schemas.
    """

    @staticmethod
    def apply_operation(df: pd.DataFrame, op: WhitelistedOp) -> pd.DataFrame:
        df_copy = df.copy()

        if isinstance(op, AddColumnOp):
            if op.expression_type == "constant":
                val = op.params.get("constant", "")
                df_copy[op.name] = val
            elif op.expression_type == "formula":
                expr = op.params.get("expression", "")
                # Simple safe binary operations or column mapping
                # Match simple colA + colB or colA * 2
                try:
                    df_copy[op.name] = df_copy.eval(expr)
                except Exception as e:
                    raise SandboxExecutionError(f"Failed to evaluate formula '{expr}': {str(e)}")
            elif op.expression_type == "conditional":
                cond_col = op.params.get("column")
                operator = op.params.get("operator", "==")
                val = op.params.get("value")
                true_val = op.params.get("true_val")
                false_val = op.params.get("false_val")
                if cond_col and cond_col in df_copy.columns:
                    if operator == "==":
                        mask = df_copy[cond_col] == val
                    elif operator == ">":
                        mask = df_copy[cond_col] > val
                    elif operator == "<":
                        mask = df_copy[cond_col] < val
                    elif operator == ">=":
                        mask = df_copy[cond_col] >= val
                    elif operator == "<=":
                        mask = df_copy[cond_col] <= val
                    else:
                        mask = df_copy[cond_col] == val
                    df_copy[op.name] = np.where(mask, true_val, false_val)
                else:
                    df_copy[op.name] = true_val

        elif isinstance(op, DropColumnOp):
            if op.name not in df_copy.columns:
                raise SandboxExecutionError(f"Column '{op.name}' does not exist in dataset.")
            df_copy.drop(columns=[op.name], inplace=True)

        elif isinstance(op, RenameColumnOp):
            if op.old_name not in df_copy.columns:
                raise SandboxExecutionError(f"Column '{op.old_name}' does not exist in dataset.")
            df_copy.rename(columns={op.old_name: op.new_name}, inplace=True)

        elif isinstance(op, FilterRowsOp):
            if op.condition_column not in df_copy.columns:
                raise SandboxExecutionError(f"Column '{op.condition_column}' does not exist in dataset.")
            col = df_copy[op.condition_column]

            if op.operator == "is_null":
                df_copy = df_copy[col.isna()]
            elif op.operator == "not_null":
                df_copy = df_copy[col.notna()]
            elif op.operator == "==":
                df_copy = df_copy[col == op.value]
            elif op.operator == "!=":
                df_copy = df_copy[col != op.value]
            elif op.operator == ">":
                df_copy = df_copy[col > float(op.value)]
            elif op.operator == "<":
                df_copy = df_copy[col < float(op.value)]
            elif op.operator == ">=":
                df_copy = df_copy[col >= float(op.value)]
            elif op.operator == "<=":
                df_copy = df_copy[col <= float(op.value)]
            elif op.operator == "contains":
                df_copy = df_copy[col.astype(str).str.contains(str(op.value), case=False, na=False)]

        elif isinstance(op, FillNAOp):
            if op.column not in df_copy.columns:
                raise SandboxExecutionError(f"Column '{op.column}' does not exist in dataset.")
            series = df_copy[op.column]
            if op.strategy == "constant":
                df_copy[op.column] = series.fillna(op.fill_value)
            elif op.strategy == "mean":
                df_copy[op.column] = series.fillna(series.mean())
            elif op.strategy == "median":
                df_copy[op.column] = series.fillna(series.median())
            elif op.strategy == "mode":
                mode_val = series.mode().iloc[0] if not series.mode().empty else ""
                df_copy[op.column] = series.fillna(mode_val)
            elif op.strategy == "ffill":
                df_copy[op.column] = series.ffill()
            elif op.strategy == "bfill":
                df_copy[op.column] = series.bfill()

        elif isinstance(op, DropNAOp):
            subset = op.subset if op.subset else None
            if subset:
                for col in subset:
                    if col not in df_copy.columns:
                        raise SandboxExecutionError(f"Column '{col}' does not exist in dataset.")
            df_copy.dropna(subset=subset, how=op.how, inplace=True)

        elif isinstance(op, ExtractPatternOp):
            if op.source_column not in df_copy.columns:
                raise SandboxExecutionError(f"Column '{op.source_column}' does not exist in dataset.")
            series = df_copy[op.source_column].astype(str)

            if op.pattern_type == "regex" and op.pattern:
                df_copy[op.new_column] = series.str.extract(op.pattern, expand=False)
            elif op.pattern_type == "email_username":
                df_copy[op.new_column] = series.str.extract(r'([^@]+)@', expand=False)
            elif op.pattern_type == "email_domain":
                df_copy[op.new_column] = series.str.extract(r'@([^@]+)', expand=False)
            elif op.pattern_type == "digits":
                df_copy[op.new_column] = series.str.extract(r'(\d+)', expand=False)
            elif op.pattern_type == "text_before" and op.pattern:
                escaped = re.escape(op.pattern)
                df_copy[op.new_column] = series.str.extract(rf'^(.*?){escaped}', expand=False)
            elif op.pattern_type == "text_after" and op.pattern:
                escaped = re.escape(op.pattern)
                df_copy[op.new_column] = series.str.extract(rf'{escaped}(.*)$', expand=False)
            else:
                df_copy[op.new_column] = series

        elif isinstance(op, BucketColumnOp):
            if op.source_column not in df_copy.columns:
                raise SandboxExecutionError(f"Column '{op.source_column}' does not exist in dataset.")
            df_copy[op.new_column] = pd.cut(
                df_copy[op.source_column],
                bins=op.bins,
                labels=op.labels,
                include_lowest=True
            ).astype(str)

        elif isinstance(op, AsTypeOp):
            if op.column not in df_copy.columns:
                raise SandboxExecutionError(f"Column '{op.column}' does not exist in dataset.")
            try:
                df_copy[op.column] = df_copy[op.column].astype(op.target_dtype)
            except Exception as e:
                raise SandboxExecutionError(f"Cannot convert column '{op.column}' to {op.target_dtype}: {str(e)}")

        elif isinstance(op, MergeColumnsOp):
            for c in op.columns:
                if c not in df_copy.columns:
                    raise SandboxExecutionError(f"Column '{c}' does not exist in dataset.")
            df_copy[op.new_column] = df_copy[op.columns].astype(str).agg(op.separator.join, axis=1)

        elif isinstance(op, DedupeOp):
            subset = op.subset if op.subset else None
            df_copy.drop_duplicates(subset=subset, keep=op.keep, inplace=True)

        return df_copy

    @classmethod
    def execute_pipeline(cls, df: pd.DataFrame, operations: List[WhitelistedOp]) -> Tuple[pd.DataFrame, Dict[str, Any]]:

        orig_df = df.copy()
        current_df = df.copy()

        for op in operations:
            current_df = cls.apply_operation(current_df, op)

        # Compute diff summary
        orig_cols = set(orig_df.columns)
        new_cols = set(current_df.columns)

        cols_added = list(new_cols - orig_cols)
        cols_dropped = list(orig_cols - new_cols)
        cols_renamed = {}

        # Sanitize dicts for JSON return
        def sanitize_records(dataframe: pd.DataFrame, max_rows: int = 5) -> List[Dict[str, Any]]:
            sample = dataframe.head(max_rows).copy()
            sample = sample.replace({np.nan: None})
            records = sample.to_dict(orient="records")
            # Ensure native serializable types
            sanitized = []
            for row in records:
                sanitized_row = {}
                for k, v in row.items():
                    if isinstance(v, (np.integer, int)):
                        sanitized_row[k] = int(v)
                    elif isinstance(v, (np.floating, float)):
                        sanitized_row[k] = float(v) if not np.isnan(v) else None
                    else:
                        sanitized_row[k] = str(v) if v is not None else None
                sanitized.append(sanitized_row)
            return sanitized

        diff_summary = {
            "cols_added": cols_added,
            "cols_dropped": cols_dropped,
            "cols_renamed": cols_renamed,
            "rows_before": len(orig_df),
            "rows_after": len(current_df),
            "affected_rows_count": abs(len(orig_df) - len(current_df)),
            "sample_before": sanitize_records(orig_df, 5),
            "sample_after": sanitize_records(current_df, 5)
        }

        return current_df, diff_summary
