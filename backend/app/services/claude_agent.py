import json
import os
import re
import pandas as pd
import httpx
from typing import Dict, Any, List, Tuple

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

from app.core.config import settings
from app.schemas.tools import OperationPayload, WhitelistedOp

class ClaudeAgentService:

    @staticmethod
    def get_openrouter_tools() -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "apply_dataset_operations",
                    "description": "Apply whitelisted data cleaning, filtering, pattern extraction, or column transformation operations to the dataset.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "explanation": {
                                "type": "string",
                                "description": "Clear natural language summary of what these operations will accomplish for the user."
                            },
                            "operations": {
                                "type": "array",
                                "description": "List of operations to execute in order.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "tool": {
                                            "type": "string",
                                            "enum": [
                                                "add_column", "drop_column", "rename_column",
                                                "filter_rows", "fillna", "dropna",
                                                "extract_pattern", "bucket_column", "astype",
                                                "merge_columns", "dedupe"
                                            ]
                                        },
                                        "name": {"type": "string", "description": "Column name for add_column or drop_column"},
                                        "old_name": {"type": "string", "description": "Original column name for rename_column"},
                                        "new_name": {"type": "string", "description": "New column name for rename_column"},
                                        "column": {"type": "string", "description": "Target column for fillna or astype"},
                                        "source_column": {"type": "string", "description": "Source column for extract_pattern or bucket_column"},
                                        "new_column": {"type": "string", "description": "New column name for extract_pattern, bucket_column, or merge_columns"},
                                        "condition_column": {"type": "string", "description": "Column for filter_rows condition"},
                                        "operator": {
                                            "type": "string",
                                            "enum": ["==", "!=", ">", "<", ">=", "<=", "contains", "is_null", "not_null"]
                                        },
                                        "value": {"description": "Value to compare against in filter_rows"},
                                        "strategy": {
                                            "type": "string",
                                            "enum": ["mean", "median", "mode", "constant", "ffill", "bfill"]
                                        },
                                        "fill_value": {"description": "Value to fill when strategy is constant"},
                                        "subset": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Columns subset for dropna or dedupe"
                                        },
                                        "how": {"type": "string", "enum": ["any", "all"]},
                                        "pattern_type": {
                                            "type": "string",
                                            "enum": ["regex", "email_username", "email_domain", "digits", "text_before", "text_after"]
                                        },
                                        "pattern": {"type": "string"},
                                        "bins": {"type": "array", "items": {"type": "number"}},
                                        "labels": {"type": "array", "items": {"type": "string"}},
                                        "target_dtype": {
                                            "type": "string",
                                            "enum": ["int64", "float64", "string", "category", "datetime64[ns]", "bool"]
                                        },
                                        "columns": {"type": "array", "items": {"type": "string"}},
                                        "separator": {"type": "string"},
                                        "keep": {"type": "string", "enum": ["first", "last"]},
                                        "expression_type": {"type": "string", "enum": ["formula", "constant", "conditional"]},
                                        "params": {"type": "object"}
                                    },
                                    "required": ["tool"]
                                }
                            }
                        },
                        "required": ["explanation", "operations"]
                    }
                }
            }
        ]

    @staticmethod
    def get_anthropic_tools() -> List[Dict[str, Any]]:
        tool = ClaudeAgentService.get_openrouter_tools()[0]["function"]
        return [{
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool["parameters"]
        }]

    @classmethod
    def _parse_and_build_payload(cls, raw_ops: List[Dict[str, Any]]) -> OperationPayload:
        valid_ops = []
        for op in raw_ops:
            tool_name = op.get("tool")
            if not tool_name:
                continue
            cleaned = {"tool": tool_name}

            if tool_name == "add_column":
                cleaned["name"] = op.get("name") or op.get("new_column") or "new_col"
                cleaned["expression_type"] = op.get("expression_type", "constant")
                cleaned["params"] = op.get("params", {"constant": op.get("value", 0)})
            elif tool_name == "drop_column":
                cleaned["name"] = op.get("name") or op.get("column") or ""
            elif tool_name == "rename_column":
                cleaned["old_name"] = op.get("old_name") or op.get("column") or ""
                cleaned["new_name"] = op.get("new_name") or op.get("new_column") or ""
            elif tool_name == "filter_rows":
                cleaned["condition_column"] = op.get("condition_column") or op.get("column") or ""
                cleaned["operator"] = op.get("operator", "not_null")
                cleaned["value"] = op.get("value", None)
            elif tool_name == "fillna":
                cleaned["column"] = op.get("column") or op.get("source_column") or ""
                cleaned["strategy"] = op.get("strategy", "mean")
                cleaned["fill_value"] = op.get("fill_value", None)
            elif tool_name == "dropna":
                cleaned["subset"] = op.get("subset", None)
                cleaned["how"] = op.get("how", "any")
            elif tool_name == "extract_pattern":
                cleaned["source_column"] = op.get("source_column") or op.get("column") or ""
                cleaned["new_column"] = op.get("new_column") or f"{cleaned['source_column']}_extracted"
                cleaned["pattern_type"] = op.get("pattern_type", "regex")
                cleaned["pattern"] = op.get("pattern", None)
            elif tool_name == "bucket_column":
                cleaned["source_column"] = op.get("source_column") or op.get("column") or ""
                cleaned["new_column"] = op.get("new_column") or f"{cleaned['source_column']}_bucket"
                cleaned["bins"] = op.get("bins", [0, 50, 100])
                cleaned["labels"] = op.get("labels", ["low", "high"])
            elif tool_name == "astype":
                cleaned["column"] = op.get("column") or ""
                cleaned["target_dtype"] = op.get("target_dtype", "string")
            elif tool_name == "merge_columns":
                cleaned["columns"] = op.get("columns", [])
                cleaned["new_column"] = op.get("new_column", "merged_col")
                cleaned["separator"] = op.get("separator", " ")
            elif tool_name == "dedupe":
                cleaned["subset"] = op.get("subset", None)
                cleaned["keep"] = op.get("keep", "first")
            else:
                continue

            valid_ops.append(cleaned)

        return OperationPayload(operations=valid_ops)

    @classmethod
    async def process_user_instruction(
        cls,
        user_prompt: str,
        df_sample: pd.DataFrame
    ) -> Tuple[OperationPayload, str]:

        columns = list(df_sample.columns)
        dtypes = {col: str(df_sample[col].dtype) for col in columns}
        sample_rows = df_sample.head(5).to_dict(orient="records")

        system_prompt = f"""You are the NL Data Wrangling Agent for DataForge AI.
Your task is to convert the user's natural language edit instruction into one or more structured tool operations from the closed whitelisted vocabulary.

CURRENT DATASET CONTEXT:
Columns & Data Types: {json.dumps(dtypes)}
Sample 5 Rows: {json.dumps(sample_rows, default=str)}

RULES:
1. ONLY reference column names that exist in the columns list above.
2. For extracting text patterns (like emails, register numbers, domain names), use 'extract_pattern'.
3. For filling missing values, use 'fillna'.
4. For dropping null rows or filtering, use 'dropna' or 'filter_rows'.
5. For binning numerical values into low/medium/high, use 'bucket_column'.
6. Do NOT invent new tool names. Return only valid tool parameters matching the dataset columns.
"""

        # 1. Try OpenRouter API first if configured
        openrouter_key = settings.OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY", "")
        if openrouter_key and len(openrouter_key) > 5:
            try:
                headers = {
                    "Authorization": f"Bearer {openrouter_key}",
                    "HTTP-Referer": settings.OPENROUTER_SITE_URL,
                    "X-Title": settings.OPENROUTER_SITE_NAME,
                    "Content-Type": "application/json"
                }

                model_name = settings.OPENROUTER_MODEL or "openai/gpt-4o"
                body = {
                    "model": model_name,
                    "max_tokens": 800,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "tools": cls.get_openrouter_tools(),
                    "tool_choice": {"type": "function", "function": {"name": "apply_dataset_operations"}}
                }

                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=body
                    )

                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        message = choices[0].get("message", {})
                        tool_calls = message.get("tool_calls", [])
                        if tool_calls:
                            first_call = tool_calls[0]
                            func_args = first_call.get("function", {}).get("arguments", "{}")
                            if isinstance(func_args, str):
                                input_data = json.loads(func_args)
                            else:
                                input_data = func_args
                            explanation = input_data.get("explanation", "Applying requested operations.")
                            ops_list = input_data.get("operations", [])
                            payload = cls._parse_and_build_payload(ops_list)
                            return payload, explanation
                        
                        # Fallback parsing content if tool_calls missed
                        content = message.get("content", "")
                        if content:
                            match = re.search(r'\{.*\}', content, re.DOTALL)
                            if match:
                                input_data = json.loads(match.group(0))
                                explanation = input_data.get("explanation", "Applying requested operations.")
                                ops_list = input_data.get("operations", [])
                                payload = cls._parse_and_build_payload(ops_list)
                                return payload, explanation
                else:
                    print(f"OpenRouter API error (Status {resp.status_code}): {resp.text}")

            except Exception as e:
                print(f"OpenRouter API call failed, falling back: {e}")

        # 2. Try Anthropic API if configured
        anthropic_key = settings.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY", "")
        if anthropic_key and len(anthropic_key) > 5 and AsyncAnthropic is not None:
            try:
                client = AsyncAnthropic(api_key=anthropic_key)
                response = await client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                    tools=cls.get_anthropic_tools(),
                    tool_choice={"type": "tool", "name": "apply_dataset_operations"}
                )

                for block in response.content:
                    if block.type == "tool_use" and block.name == "apply_dataset_operations":
                        input_data = block.input
                        explanation = input_data.get("explanation", "Applying requested operations.")
                        ops_list = input_data.get("operations", [])
                        payload = cls._parse_and_build_payload(ops_list)
                        return payload, explanation
            except Exception as e:
                print(f"Anthropic API call failed: {e}")

        # 3. Rule-based fallback parser for local offline testing / seed datasets
        return cls._rule_based_fallback(user_prompt, df_sample)

    @classmethod
    def _rule_based_fallback(cls, user_prompt: str, df_sample: pd.DataFrame) -> Tuple[OperationPayload, str]:
        prompt_lower = user_prompt.lower()
        cols = list(df_sample.columns)
        ops = []
        explanation = "Parsed operations based on natural language keywords."

        # Rule 1: extract register number / domain / pattern from email
        if "email" in prompt_lower and ("extract" in prompt_lower or "domain" in prompt_lower or "register" in prompt_lower or "number" in prompt_lower):
            email_col = next((c for c in cols if "email" in c.lower()), None)
            if email_col:
                if "register" in prompt_lower or "number" in prompt_lower:
                    ops.append({
                        "tool": "extract_pattern",
                        "source_column": email_col,
                        "new_column": "register_number",
                        "pattern_type": "digits",
                        "pattern": None
                    })
                    explanation = f"Extracting registration digits from '{email_col}' into new column 'register_number'."
                elif "domain" in prompt_lower:
                    ops.append({
                        "tool": "extract_pattern",
                        "source_column": email_col,
                        "new_column": "email_domain",
                        "pattern_type": "email_domain",
                        "pattern": None
                    })
                    explanation = f"Extracting domain name from '{email_col}' into new column 'email_domain'."

        # Rule 2: drop rows where column is null
        elif "drop" in prompt_lower and ("null" in prompt_lower or "na" in prompt_lower or "empty" in prompt_lower):
            for c in cols:
                if c.lower() in prompt_lower:
                    ops.append({
                        "tool": "dropna",
                        "subset": [c],
                        "how": "any"
                    })
                    explanation = f"Dropping rows where '{c}' contains null values."
                    break

        # Rule 3: bucket column (e.g. salary / age / gpa) into low/medium/high
        elif "bucket" in prompt_lower or "bin" in prompt_lower or ("low" in prompt_lower and "high" in prompt_lower):
            target_num_col = next((c for c in cols if c.lower() in prompt_lower and pd.api.types.is_numeric_dtype(df_sample[c])), None)
            if not target_num_col:
                target_num_col = next((c for c in cols if pd.api.types.is_numeric_dtype(df_sample[c])), None)
            if target_num_col:
                min_v = float(df_sample[target_num_col].min())
                max_v = float(df_sample[target_num_col].max())
                mid_v = (min_v + max_v) / 2.0
                ops.append({
                    "tool": "bucket_column",
                    "source_column": target_num_col,
                    "new_column": f"{target_num_col}_tier",
                    "bins": [min_v - 1, mid_v, max_v + 1],
                    "labels": ["low", "high"]
                })
                explanation = f"Bucketing '{target_num_col}' into low/high tiers as new column '{target_num_col}_tier'."

        # Rule 4: fillna / fill missing
        elif "fill" in prompt_lower or "impute" in prompt_lower:
            for c in cols:
                if c.lower() in prompt_lower:
                    strat = "mean" if pd.api.types.is_numeric_dtype(df_sample[c]) else "mode"
                    ops.append({
                        "tool": "fillna",
                        "column": c,
                        "strategy": strat
                    })
                    explanation = f"Filling missing values in '{c}' using {strat} strategy."
                    break

        # Rule 5: filter rows
        elif "filter" in prompt_lower or "keep" in prompt_lower:
            for c in cols:
                if c.lower() in prompt_lower:
                    ops.append({
                        "tool": "filter_rows",
                        "condition_column": c,
                        "operator": "not_null",
                        "value": None
                    })
                    explanation = f"Filtering rows to keep non-null values in '{c}'."
                    break

        if not ops:
            ops.append({
                "tool": "dedupe",
                "subset": None,
                "keep": "first"
            })
            explanation = "Checking and removing duplicate rows across dataset."

        payload = OperationPayload(operations=ops)
        return payload, explanation

OpenRouterAgentService = ClaudeAgentService
