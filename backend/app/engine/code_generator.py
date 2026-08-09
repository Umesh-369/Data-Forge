import json
from typing import Dict, Any, List, Optional, Tuple

class CodeGeneratorEngine:
    """
    Transpiles Dataset Version lineage and AutoML model specifications
    into standalone executable Python scripts (.py) or Jupyter Notebooks (.ipynb v4 format).
    """

    @staticmethod
    def _op_to_python(op: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
        """
        Converts a single whitelisted operation dict to Python code using pandas.
        Returns (code_snippet, error_if_excluded)
        """
        op_type = op.get("op_type") or op.get("name") or op.get("type")
        
        if op_type == "add_column":
            col_name = op.get("name")
            expr_type = op.get("expression_type")
            params = op.get("params", {})
            if expr_type == "constant":
                val = repr(params.get("constant", ""))
                return f"df['{col_name}'] = {val}", None
            elif expr_type == "formula":
                expr = params.get("expression", "")
                return f"df['{col_name}'] = df.eval('{expr}')", None
            elif expr_type == "conditional":
                cond_col = params.get("column")
                operator = params.get("operator", "==")
                val = repr(params.get("value"))
                true_val = repr(params.get("true_val"))
                false_val = repr(params.get("false_val"))
                return f"df['{col_name}'] = np.where(df['{cond_col}'] {operator} {val}, {true_val}, {false_val})", None
            else:
                return None, {"operation": "add_column", "reason": f"Unsupported expression type '{expr_type}'"}

        elif op_type == "drop_column":
            col_name = op.get("name")
            return f"df = df.drop(columns=['{col_name}'], errors='ignore')", None

        elif op_type == "rename_column":
            old_name = op.get("old_name")
            new_name = op.get("new_name")
            return f"df = df.rename(columns={{'{old_name}': '{new_name}'}})", None

        elif op_type == "filter_rows":
            col = op.get("condition_column")
            operator = op.get("operator")
            val = op.get("value")
            if operator == "is_null":
                return f"df = df[df['{col}'].isna()]", None
            elif operator == "not_null":
                return f"df = df[df['{col}'].notna()]", None
            elif operator in ["==", "!=", ">", "<", ">=", "<="]:
                val_expr = repr(val) if isinstance(val, str) else str(val)
                return f"df = df[df['{col}'] {operator} {val_expr}]", None
            elif operator == "contains":
                val_expr = repr(str(val))
                return f"df = df[df['{col}'].astype(str).str.contains({val_expr}, case=False, na=False)]", None
            else:
                return None, {"operation": f"filter_rows ({operator})", "reason": f"Unsupported filter operator '{operator}'"}

        elif op_type == "fill_na":
            col = op.get("column")
            strat = op.get("strategy")
            fill_val = op.get("fill_value")
            if strat == "constant":
                return f"df['{col}'] = df['{col}'].fillna({repr(fill_val)})", None
            elif strat == "mean":
                return f"df['{col}'] = df['{col}'].fillna(df['{col}'].mean())", None
            elif strat == "median":
                return f"df['{col}'] = df['{col}'].fillna(df['{col}'].median())", None
            elif strat == "mode":
                return f"df['{col}'] = df['{col}'].fillna(df['{col}'].mode().iloc[0] if not df['{col}'].mode().empty else '')", None
            elif strat in ["ffill", "bfill"]:
                return f"df['{col}'] = df['{col}'].{strat}()", None
            else:
                return None, {"operation": "fill_na", "reason": f"Unsupported fillna strategy '{strat}'"}

        elif op_type == "drop_na":
            subset = op.get("subset")
            how = op.get("how", "any")
            if subset:
                return f"df = df.dropna(subset={repr(subset)}, how='{how}')", None
            return f"df = df.dropna(how='{how}')", None

        elif op_type == "extract_pattern":
            src = op.get("source_column")
            new_col = op.get("new_column")
            ptype = op.get("pattern_type")
            pattern = op.get("pattern", "")
            if ptype == "regex" and pattern:
                return f"df['{new_col}'] = df['{src}'].astype(str).str.extract(r'{pattern}', expand=False)", None
            elif ptype == "email_username":
                return f"df['{new_col}'] = df['{src}'].astype(str).str.extract(r'([^@]+)@', expand=False)", None
            elif ptype == "email_domain":
                return f"df['{new_col}'] = df['{src}'].astype(str).str.extract(r'@([^@]+)', expand=False)", None
            elif ptype == "digits":
                return f"df['{new_col}'] = df['{src}'].astype(str).str.extract(r'(\\d+)', expand=False)", None
            elif ptype == "text_before" and pattern:
                return f"df['{new_col}'] = df['{src}'].astype(str).str.extract(rf'^(.*?){pattern}', expand=False)", None
            elif ptype == "text_after" and pattern:
                return f"df['{new_col}'] = df['{src}'].astype(str).str.extract(rf'{pattern}(.*)$', expand=False)", None
            else:
                return f"df['{new_col}'] = df['{src}']", None

        elif op_type == "bucket_column":
            src = op.get("source_column")
            new_col = op.get("new_column")
            bins = op.get("bins", 5)
            labels = op.get("labels")
            return f"df['{new_col}'] = pd.cut(df['{src}'], bins={bins}, labels={repr(labels)}, include_lowest=True).astype(str)", None

        elif op_type == "as_type":
            col = op.get("column")
            target_dtype = op.get("target_dtype")
            return f"df['{col}'] = df['{col}'].astype('{target_dtype}')", None

        elif op_type == "merge_columns":
            cols = op.get("columns", [])
            new_col = op.get("new_column")
            sep = op.get("separator", " ")
            return f"df['{new_col}'] = df[{repr(cols)}].astype(str).agg({repr(sep)}.join, axis=1)", None

        elif op_type == "dedupe":
            subset = op.get("subset")
            keep = op.get("keep", "first")
            if subset:
                return f"df = df.drop_duplicates(subset={repr(subset)}, keep='{keep}')", None
            return f"df = df.drop_duplicates(keep='{keep}')", None

        elif op:
            return None, {"operation": str(op_type or "unknown_op"), "reason": f"Custom unverified operation formula or step '{op_type}' is not safely exportable"}

        return None, None

    @classmethod
    def generate_code(
        cls,
        version_number: int,
        dataset_name: str,
        lineage_ops: List[Dict[str, Any]],
        target_column: Optional[str] = None,
        algorithm: Optional[str] = None,
        format_type: str = "py"
    ) -> Tuple[str, List[Dict[str, str]]]:
        """
        Generates Python script code or Jupyter Notebook JSON string.
        """
        cleaning_lines = []
        excluded_ops = []

        for op in lineage_ops:
            code_line, error = cls._op_to_python(op)
            if code_line:
                cleaning_lines.append(code_line)
            elif error:
                excluded_ops.append(error)

        is_classification = algorithm and ("Classifier" in algorithm or "Logistic" in algorithm)
        is_regression = algorithm and ("Regressor" in algorithm or "Ridge" in algorithm or not is_classification)

        if format_type == "ipynb":
            return cls._build_notebook_json(
                version_number, dataset_name, cleaning_lines, target_column, algorithm, is_classification, excluded_ops
            ), excluded_ops

        return cls._build_py_script(
            version_number, dataset_name, cleaning_lines, target_column, algorithm, is_classification, excluded_ops
        ), excluded_ops

    @staticmethod
    def _build_py_script(
        version_number: int,
        dataset_name: str,
        cleaning_lines: List[str],
        target_column: Optional[str],
        algorithm: Optional[str],
        is_classification: bool,
        excluded_ops: List[Dict[str, str]]
    ) -> str:
        lines = [
            f"# DataForge Sky AI - Standalone ML Pipeline Code",
            f"# Dataset: {dataset_name} (Version #{version_number})",
            f"# Standard Libraries: pandas, scikit-learn, numpy",
            "",
            "import pandas as pd",
            "import numpy as np",
        ]

        if target_column and algorithm:
            lines.extend([
                "from sklearn.model_selection import train_test_split",
                "from sklearn.impute import SimpleImputer",
                "from sklearn.preprocessing import StandardScaler, OneHotEncoder",
                "from sklearn.compose import ColumnTransformer",
                "from sklearn.pipeline import Pipeline",
            ])
            if "Random Forest Classifier" in algorithm:
                lines.append("from sklearn.ensemble import RandomForestClassifier")
            elif "Gradient Boosting Classifier" in algorithm:
                lines.append("from sklearn.ensemble import GradientBoostingClassifier")
            elif "Logistic Regression" in algorithm:
                lines.append("from sklearn.linear_model import LogisticRegression")
            elif "Random Forest Regressor" in algorithm:
                lines.append("from sklearn.ensemble import RandomForestRegressor")
            elif "Gradient Boosting Regressor" in algorithm:
                lines.append("from sklearn.ensemble import GradientBoostingRegressor")
            elif "Ridge" in algorithm:
                lines.append("from sklearn.linear_model import Ridge")

            if is_classification:
                lines.append("from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report")
            else:
                lines.append("from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error")

        lines.extend([
            "",
            "def run_pipeline(data_path: str = 'dataset.csv'):",
            "    print(f'Loading dataset from {data_path}...')",
            "    df = pd.read_csv(data_path)",
            "    print(f'Initial shape: {df.shape}')",
            ""
        ])

        # Step 2: Data Cleaning & Preprocessing
        lines.append("    # Step 1: Lineage Data Cleaning & Preprocessing")
        if cleaning_lines:
            for c_line in cleaning_lines:
                lines.append(f"    {c_line}")
        else:
            lines.append("    # No custom transformations required for this version")
        lines.append("    print(f'Transformed dataset shape: {df.shape}')")
        lines.append("")

        # Step 3: AutoML Model Training
        if target_column and algorithm:
            lines.extend([
                f"    # Step 2: Model Training ({algorithm})",
                f"    target_col = '{target_column}'",
                "    if target_col not in df.columns:",
                "        raise ValueError(f\"Target column '{target_col}' not found in dataset.\")",
                "",
                "    df_clean = df.dropna(subset=[target_col]).copy()",
                "    X = df_clean.drop(columns=[target_col])",
                "    y = df_clean[target_col]",
                "",
                "    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()",
                "    categorical_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()",
                "",
                "    numeric_transformer = Pipeline(steps=[",
                "        ('imputer', SimpleImputer(strategy='median')),",
                "        ('scaler', StandardScaler())",
                "    ])",
                "",
                "    categorical_transformer = Pipeline(steps=[",
                "        ('imputer', SimpleImputer(strategy='most_frequent')),",
                "        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))",
                "    ])",
                "",
                "    preprocessor = ColumnTransformer(",
                "        transformers=[",
                "            ('num', numeric_transformer, numeric_cols),",
                "            ('cat', categorical_transformer, categorical_cols)",
                "        ]",
                "    )",
                ""
            ])

            if algorithm == "Random Forest Classifier":
                model_code = "RandomForestClassifier(n_estimators=100, random_state=42)"
            elif algorithm == "Gradient Boosting Classifier":
                model_code = "GradientBoostingClassifier(n_estimators=100, random_state=42)"
            elif algorithm == "Logistic Regression":
                model_code = "LogisticRegression(random_state=42)"
            elif algorithm == "Random Forest Regressor":
                model_code = "RandomForestRegressor(n_estimators=100, random_state=42)"
            elif algorithm == "Gradient Boosting Regressor":
                model_code = "GradientBoostingRegressor(n_estimators=100, random_state=42)"
            else:
                model_code = "Ridge(random_state=42)"

            lines.extend([
                f"    model = {model_code}",
                "    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('model', model)])",
                "",
                "    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)",
                "    print(f'Training {algorithm} on {len(X_train)} rows...')",
                "    pipeline.fit(X_train, y_train)",
                "    y_pred = pipeline.predict(X_test)",
                "",
                "    # Step 3: Evaluation Metrics",
            ])

            if is_classification:
                lines.extend([
                    "    acc = accuracy_score(y_test, y_pred)",
                    "    prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted', zero_division=0)",
                    "    print('\\n--- Model Performance ---')",
                    "    print(f'Accuracy:  {acc:.4f}')",
                    "    print(f'Precision: {prec:.4f}')",
                    "    print(f'Recall:    {rec:.4f}')",
                    "    print(f'F1 Score:  {f1:.4f}')",
                    "    print('\\nClassification Report:')",
                    "    print(classification_report(y_test, y_pred))",
                ])
            else:
                lines.extend([
                    "    r2 = r2_score(y_test, y_pred)",
                    "    mse = mean_squared_error(y_test, y_pred)",
                    "    rmse = np.sqrt(mse)",
                    "    mae = mean_absolute_error(y_test, y_pred)",
                    "    print('\\n--- Model Performance ---')",
                    "    print(f'R2 Score: {r2:.4f}')",
                    "    print(f'RMSE:     {rmse:.4f}')",
                    "    print(f'MAE:      {mae:.4f}')",
                ])

            lines.extend([
                "",
                "    return pipeline, df_clean"
            ])
        else:
            lines.extend([
                "    print('Data cleaning complete. Returned transformed DataFrame.')",
                "    return df"
            ])

        lines.extend([
            "",
            "if __name__ == '__main__':",
            "    run_pipeline()"
        ])

        return "\n".join(lines)

    @staticmethod
    def _build_notebook_json(
        version_number: int,
        dataset_name: str,
        cleaning_lines: List[str],
        target_column: Optional[str],
        algorithm: Optional[str],
        is_classification: bool,
        excluded_ops: List[Dict[str, str]]
    ) -> str:
        cells = []

        def add_md(text: str):
            cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": [line + "\n" for line in text.split("\n")]
            })

        def add_code(text: str):
            cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [line + "\n" for line in text.split("\n")]
            })

        # Header Markdown
        add_md(f"# DataForge Sky AI - Standalone ML Pipeline Notebook\n**Dataset**: `{dataset_name}` (Version #{version_number})\n\nThis notebook runs standalone with `pandas` and `scikit-learn`.")

        # Imports Code
        imports_lines = [
            "import pandas as pd",
            "import numpy as np"
        ]
        if target_column and algorithm:
            imports_lines.extend([
                "from sklearn.model_selection import train_test_split",
                "from sklearn.impute import SimpleImputer",
                "from sklearn.preprocessing import StandardScaler, OneHotEncoder",
                "from sklearn.compose import ColumnTransformer",
                "from sklearn.pipeline import Pipeline"
            ])
            if "Random Forest Classifier" in algorithm:
                imports_lines.append("from sklearn.ensemble import RandomForestClassifier")
            elif "Gradient Boosting Classifier" in algorithm:
                imports_lines.append("from sklearn.ensemble import GradientBoostingClassifier")
            elif "Logistic Regression" in algorithm:
                imports_lines.append("from sklearn.linear_model import LogisticRegression")
            elif "Random Forest Regressor" in algorithm:
                imports_lines.append("from sklearn.ensemble import RandomForestRegressor")
            elif "Gradient Boosting Regressor" in algorithm:
                imports_lines.append("from sklearn.ensemble import GradientBoostingRegressor")
            elif "Ridge" in algorithm:
                imports_lines.append("from sklearn.linear_model import Ridge")

            if is_classification:
                imports_lines.append("from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report")
            else:
                imports_lines.append("from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error")

        add_md("## 1. Environment & Library Imports")
        add_code("\n".join(imports_lines))

        # Data Load
        add_md("## 2. Load Dataset")
        add_code("# Load raw dataset CSV\ndf = pd.read_csv('dataset.csv')\nprint('Initial shape:', df.shape)\ndf.head()")

        # Data Cleaning
        add_md("## 3. Data Cleaning & Transformation Lineage")
        if cleaning_lines:
            add_code("\n".join(cleaning_lines) + "\nprint('Transformed shape:', df.shape)\ndf.head()")
        else:
            add_code("# No custom transformations needed\nprint('Transformed shape:', df.shape)")

        # AutoML Pipeline
        if target_column and algorithm:
            add_md(f"## 4. AutoML Model Building ({algorithm})\nTarget column: `{target_column}`")

            if algorithm == "Random Forest Classifier":
                model_code = "RandomForestClassifier(n_estimators=100, random_state=42)"
            elif algorithm == "Gradient Boosting Classifier":
                model_code = "GradientBoostingClassifier(n_estimators=100, random_state=42)"
            elif algorithm == "Logistic Regression":
                model_code = "LogisticRegression(random_state=42)"
            elif algorithm == "Random Forest Regressor":
                model_code = "RandomForestRegressor(n_estimators=100, random_state=42)"
            elif algorithm == "Gradient Boosting Regressor":
                model_code = "GradientBoostingRegressor(n_estimators=100, random_state=42)"
            else:
                model_code = "Ridge(random_state=42)"

            train_code_lines = [
                f"target_col = '{target_column}'",
                "df_clean = df.dropna(subset=[target_col]).copy()",
                "X = df_clean.drop(columns=[target_col])",
                "y = df_clean[target_col]",
                "",
                "numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()",
                "categorical_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()",
                "",
                "numeric_transformer = Pipeline(steps=[",
                "    ('imputer', SimpleImputer(strategy='median')),",
                "    ('scaler', StandardScaler())",
                "])",
                "",
                "categorical_transformer = Pipeline(steps=[",
                "    ('imputer', SimpleImputer(strategy='most_frequent')),",
                "    ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))",
                "])",
                "",
                "preprocessor = ColumnTransformer(",
                "    transformers=[",
                "        ('num', numeric_transformer, numeric_cols),",
                "        ('cat', categorical_transformer, categorical_cols)",
                "    ]",
                ")",
                "",
                f"model = {model_code}",
                "pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('model', model)])",
                "",
                "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)",
                "pipeline.fit(X_train, y_train)",
                "y_pred = pipeline.predict(X_test)"
            ]
            add_code("\n".join(train_code_lines))

            add_md("## 5. Model Evaluation Metrics")
            if is_classification:
                eval_lines = [
                    "acc = accuracy_score(y_test, y_pred)",
                    "prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted', zero_division=0)",
                    "print(f'Accuracy:  {acc:.4f}')",
                    "print(f'Precision: {prec:.4f}')",
                    "print(f'Recall:    {rec:.4f}')",
                    "print(f'F1 Score:  {f1:.4f}')",
                    "print('\\nClassification Report:')",
                    "print(classification_report(y_test, y_pred))"
                ]
            else:
                eval_lines = [
                    "r2 = r2_score(y_test, y_pred)",
                    "mse = mean_squared_error(y_test, y_pred)",
                    "rmse = np.sqrt(mse)",
                    "mae = mean_absolute_error(y_test, y_pred)",
                    "print(f'R2 Score: {r2:.4f}')",
                    "print(f'RMSE:     {rmse:.4f}')",
                    "print(f'MAE:      {mae:.4f}')"
                ]
            add_code("\n".join(eval_lines))

        nb_dict = {
            "cells": cells,
            "metadata": {
                "language_info": {
                    "name": "python",
                    "version": "3.10"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 2
        }

        return json.dumps(nb_dict, indent=2)
