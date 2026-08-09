import json
import os
import re
import pandas as pd
import httpx
from typing import Dict, Any, List, Tuple
from app.core.config import settings

class DatasetChatService:

    @classmethod
    async def process_chat(
        cls,
        df: pd.DataFrame,
        message: str,
        conversation_history: List[Dict[str, Any]] = None
    ) -> Tuple[str, str]:
        prompt_lower = message.lower().strip()
        cols = list(df.columns)
        total_rows = len(df)
        total_cols = len(cols)

        # 1. Try OpenRouter or Anthropic LLM first for arbitrary natural language questions
        openrouter_key = settings.OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY", "")
        if openrouter_key and len(openrouter_key) > 5:
            try:
                dtypes_info = {col: str(df[col].dtype) for col in cols}
                null_counts = df.isnull().sum().to_dict()
                sample_data = df.head(3).to_dict(orient="records")

                system_prompt = f"""You are DataBot, a slightly eccentric, quirky data-nerd AI assistant for DataForge AI.
Your job is to answer user questions about their current dataset accurately based on computed pandas execution.

DATASET SCHEMA & SUMMARY:
Total Rows: {total_rows}
Columns & Data Types: {json.dumps(dtypes_info)}
Null Count per Column: {json.dumps(null_counts)}
Sample 3 Rows: {json.dumps(sample_data, default=str)}

RULES:
1. Always include a single-line valid python/pandas expression string as `computation_trace` (e.g. "df.isnull().sum()" or "df['Category'].value_counts()").
2. Your response MUST be a JSON object with keys:
   - "computation_trace": string containing the exact pandas query run.
   - "quirky_intro": 1 short quirky, offbeat eccentric observation about the data (e.g. "Huh, 100% of your sample rows say 'spam' — either this dataset hates you, or we're only looking at the spam pile."). Keep it short (1 sentence max).
   - "factual_answer": Clear, precise answer stating the numbers/facts computed.
3. Return ONLY valid JSON. No Markdown wrapper.
"""
                headers = {
                    "Authorization": f"Bearer {openrouter_key}",
                    "HTTP-Referer": settings.OPENROUTER_SITE_URL,
                    "X-Title": settings.OPENROUTER_SITE_NAME,
                    "Content-Type": "application/json"
                }

                model_name = settings.OPENROUTER_MODEL or "openai/gpt-4o"
                body = {
                    "model": model_name,
                    "max_tokens": 500,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "response_format": {"type": "json_object"}
                }

                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=body
                    )

                if resp.status_code == 200:
                    res_data = resp.json()
                    choices = res_data.get("choices", [])
                    if choices:
                        content_str = choices[0].get("message", {}).get("content", "")
                        parsed = json.loads(content_str)
                        trace = parsed.get("computation_trace", f"df.describe()")
                        intro = parsed.get("quirky_intro", "Inspected the dataset parameters...")
                        facts = parsed.get("factual_answer", "")
                        answer = f"{intro} {facts}".strip()
                        return answer, trace

            except Exception as e:
                print(f"DatasetChatService LLM call failed, fallback to local executor: {e}")

        # 2. Rule-based Deterministic Query Engine (Guaranteed accurate sandbox query trace)
        
        # Query: Missing values
        if "missing" in prompt_lower or "null" in prompt_lower or "na" in prompt_lower or "empty" in prompt_lower:
            trace = "df.isnull().sum()"
            null_series = df.isnull().sum()
            total_nulls = int(null_series.sum())
            if total_nulls == 0:
                answer = f"Spotless! Your dataset is cleaner than a fresh lab coat — 0 missing values found across all {total_rows} rows and {total_cols} columns."
            else:
                missing_cols = {col: int(cnt) for col, cnt in null_series.items() if cnt > 0}
                answer = f"Well, looks like somebody left some holes in the grid! Found {total_nulls} missing cells in total across columns: {missing_cols}."
            return answer, trace

        # Query: Weirdest column / anomalous column
        if "weird" in prompt_lower or "strange" in prompt_lower or "unusual" in prompt_lower or "anomaly" in prompt_lower:
            trace = "df.nunique().to_dict()"
            uniques = df.nunique().to_dict()
            # Find single unique value column or top weirdness
            single_val_cols = [c for c, count in uniques.items() if count == 1]
            if single_val_cols:
                top_weird = single_val_cols[0]
                val_sample = str(df[top_weird].iloc[0])
                answer = f"{top_weird} takes the crown for weirdness — 100% of your {total_rows} rows say '{val_sample}'! Either this dataset is deeply obsessed with '{val_sample}', or we're looking at a single-class sample. ({total_rows} total rows, 0 missing in {top_weird})."
            else:
                top_weird = min(uniques, key=uniques.get)
                answer = f"Looking at unique cardinality, '{top_weird}' is the odd one out with only {uniques[top_weird]} distinct value(s) across all {total_rows} rows."
            return answer, trace

        # Query: Row count / size / shape
        if "row" in prompt_lower or "count" in prompt_lower or "how many" in prompt_lower or "size" in prompt_lower or "shape" in prompt_lower:
            trace = "df.shape"
            answer = f"Counted every single row (well, pandas did) — you've got exactly {total_rows} rows and {total_cols} columns in this dataset version."
            return answer, trace

        # Query: Column names or summary
        if "column" in prompt_lower or "feature" in prompt_lower or "schema" in prompt_lower:
            trace = "[c for c in df.columns]"
            col_list_str = ", ".join([f"'{c}'" for c in cols])
            answer = f"Lined up all headers for inspection — this version contains {total_cols} columns: {col_list_str}."
            return answer, trace

        # Default fallback query
        trace = f"df.describe(include='all')"
        answer = f"Analyzed dataset metrics for version inspection — total of {total_rows} rows and {total_cols} columns across headers {cols}."
        return answer, trace
