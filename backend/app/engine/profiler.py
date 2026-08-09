import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List

class ProfilerEngine:
    @staticmethod
    def load_dataframe(file_path: str) -> pd.DataFrame:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            return pd.read_csv(file_path)
        elif ext in [".xlsx", ".xls"]:
            return pd.read_excel(file_path)
        elif ext == ".json":
            return pd.read_json(file_path)
        elif ext == ".parquet":
            return pd.read_parquet(file_path)
        else:
            # Fallback csv
            return pd.read_csv(file_path)

    @staticmethod
    def profile(df: pd.DataFrame) -> Dict[str, Any]:
        total_rows = len(df)
        total_cols = len(df.columns)
        duplicate_rows = int(df.duplicated().sum())
        total_missing = int(df.isna().sum().sum())

        columns_profile = []
        for col in df.columns:
            series = df[col]
            missing_count = int(series.isna().sum())
            missing_pct = round((missing_count / total_rows * 100), 2) if total_rows > 0 else 0.0
            unique_count = int(series.nunique(dropna=True))

            # Detect data type category
            if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
                col_type = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(series):
                col_type = "datetime"
            elif pd.api.types.is_bool_dtype(series):
                col_type = "boolean"
            else:
                col_type = "categorical"

            # Sample values (up to 5 non-null values)
            clean_series = series.dropna()
            sample_vals = clean_series.head(5).tolist()
            # Convert non-serializable types
            sample_vals = [int(v) if isinstance(v, (np.integer, int)) else
                           float(v) if isinstance(v, (np.floating, float)) else str(v)
                           for v in sample_vals]

            stats = {}
            histogram = None

            if col_type == "numeric" and len(clean_series) > 0:
                stats = {
                    "mean": float(round(clean_series.mean(), 4)),
                    "std": float(round(clean_series.std(), 4)) if len(clean_series) > 1 else 0.0,
                    "min": float(clean_series.min()),
                    "p25": float(clean_series.quantile(0.25)),
                    "median": float(clean_series.median()),
                    "p75": float(clean_series.quantile(0.75)),
                    "max": float(clean_series.max()),
                }
                # Create 10-bin histogram for sparklines
                try:
                    counts, bin_edges = np.histogram(clean_series, bins=min(10, max(2, unique_count)))
                    histogram = []
                    for i in range(len(counts)):
                        histogram.append({
                            "bin": f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}",
                            "count": int(counts[i])
                        })
                except Exception:
                    histogram = []
            elif col_type == "categorical" or col_type == "boolean":
                val_counts = clean_series.value_counts().head(5)
                top_cats = {}
                for k, v in val_counts.items():
                    top_cats[str(k)] = int(v)
                stats = {
                    "top_categories": top_cats
                }

            columns_profile.append({
                "name": str(col),
                "dtype": col_type,
                "missing_count": missing_count,
                "missing_pct": missing_pct,
                "unique_count": unique_count,
                "sample_values": sample_vals,
                "stats": stats,
                "histogram": histogram
            })

        return {
            "row_count": total_rows,
            "col_count": total_cols,
            "duplicate_rows": duplicate_rows,
            "total_missing_cells": total_missing,
            "columns": columns_profile
        }
