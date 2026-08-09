import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, r2_score, mean_squared_error, mean_absolute_error


def fill_text_na(x):
    if isinstance(x, pd.DataFrame):
        return x.iloc[:, 0].fillna('').astype(str).values
    elif isinstance(x, pd.Series):
        return x.fillna('').astype(str).values
    else:
        return pd.Series(np.ravel(x)).fillna('').astype(str).values


class AutoMLEngine:

    @staticmethod
    def auto_detect_target(df: pd.DataFrame) -> Tuple[str, str]:
        """
        Auto-detects the target column using column name heuristics, cardinality/type rules,
        or fallback to the last column.
        Returns (target_column_name, detection_reason_string)
        """
        if df.empty or len(df.columns) == 0:
            raise ValueError("Dataset is empty; cannot detect target column.")

        # Keywords commonly used for targets
        target_keywords = ["target", "label", "class", "category", "outcome", "y", "survived", "status", "price", "salary", "rating", "score", "total", "language"]
        
        # Priority 1: Check column names for exact or substring match
        for col in df.columns:
            col_lower = str(col).strip().lower()
            if col_lower in target_keywords or any(kw == col_lower for kw in target_keywords):
                return str(col), f"Auto-detected target column '{col}' based on standard target naming convention."

        for col in df.columns:
            col_lower = str(col).strip().lower()
            if any(kw in col_lower for kw in target_keywords):
                return str(col), f"Auto-detected target column '{col}' matching target pattern '{col_lower}'."

        # Priority 2: Low unique count discrete/categorical column (classification candidate)
        for col in reversed(df.columns):
            unique_cnt = df[col].nunique()
            if 2 <= unique_cnt <= 15 and not pd.api.types.is_float_dtype(df[col]):
                return str(col), f"Auto-detected target column '{col}' based on discrete target distribution ({unique_cnt} unique values)."

        # Priority 3: Fallback to last column
        last_col = str(df.columns[-1])
        return last_col, f"Auto-detected target column '{last_col}' as the final column of dataset."

    @staticmethod
    def auto_clean_and_preprocess(df: pd.DataFrame, target_column: str) -> Tuple[pd.DataFrame, List[str], List[Dict[str, Any]]]:
        """
        Auto-cleans the dataset:
        1. Removes missing target rows.
        2. Drops non-informative high-cardinality ID columns (while retaining text features).
        3. Imputes missing values for numeric (median) and categorical (mode) features.
        Returns (cleaned_df, audit_logs_list, operations_for_code_export)
        """
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in dataset.")

        df_clean = df.copy()
        logs: List[str] = []
        ops: List[Dict[str, Any]] = []

        # 1. Target column missing values check
        missing_target_count = int(df_clean[target_column].isna().sum())
        if missing_target_count > 0:
            df_clean = df_clean.dropna(subset=[target_column]).copy()
            logs.append(f"Dropped {missing_target_count} rows with missing values in target column '{target_column}'.")
            ops.append({"op_type": "drop_na", "subset": [target_column]})

        # 2. Identify & drop uninformative ID columns
        n_rows = len(df_clean)
        cols_to_drop = []
        id_keywords = ["id", "key", "guid", "uuid", "index", "hash", "row_id", "user_id", "patient_id", "employee_id"]

        predictor_cols = [c for c in df_clean.columns if c != target_column]

        if len(predictor_cols) == 0:
            raise ValueError(f"Dataset contains no feature columns to train on (only target column '{target_column}' found).")

        for col in predictor_cols:
            unique_cnt = int(df_clean[col].nunique())
            unique_ratio = unique_cnt / n_rows if n_rows > 0 else 0
            col_lower = str(col).lower()

            is_id_name = any(kw in col_lower for kw in id_keywords)
            is_non_numeric = not pd.api.types.is_numeric_dtype(df_clean[col])

            sample_vals = df_clean[col].dropna().astype(str).head(100)
            has_spaces = any(' ' in val for val in sample_vals)

            # Drop ONLY if it is explicitly an ID column, NOT a free text column
            if is_id_name and unique_cnt > 0.8 * n_rows:
                cols_to_drop.append((col, unique_cnt, unique_ratio))
            elif is_non_numeric and unique_ratio > 0.98 and unique_cnt > 50 and not has_spaces and is_id_name:
                cols_to_drop.append((col, unique_cnt, unique_ratio))

        # Guardrail: Do NOT drop all predictor features
        if len(cols_to_drop) >= len(predictor_cols):
            cols_to_drop.sort(key=lambda x: x[2])
            cols_to_drop = cols_to_drop[:-1]

        for col, u_cnt, u_ratio in cols_to_drop:
            df_clean = df_clean.drop(columns=[col])
            logs.append(f"Dropped high-cardinality ID-like column '{col}' ({u_cnt} unique values, {u_ratio*100:.1f}% unique).")
            ops.append({"op_type": "drop_column", "name": col})

        # 3. Impute missing values for predictor features
        for col in df_clean.columns:
            if col == target_column:
                continue

            missing_cnt = int(df_clean[col].isna().sum())
            if missing_cnt > 0:
                if pd.api.types.is_numeric_dtype(df_clean[col]):
                    median_val = float(df_clean[col].median()) if not df_clean[col].dropna().empty else 0.0
                    df_clean[col] = df_clean[col].fillna(median_val)
                    logs.append(f"Imputed {missing_cnt} missing values in numeric column '{col}' with median ({median_val:.2f}).")
                    ops.append({"op_type": "fill_na", "column": col, "strategy": "median", "fill_value": median_val})
                else:
                    mode_series = df_clean[col].mode()
                    mode_val = str(mode_series.iloc[0]) if not mode_series.empty else "Unknown"
                    df_clean[col] = df_clean[col].fillna(mode_val)
                    logs.append(f"Imputed {missing_cnt} missing values in categorical column '{col}' with mode ('{mode_val}').")
                    ops.append({"op_type": "fill_na", "column": col, "strategy": "mode", "fill_value": mode_val})

        if not logs:
            logs.append("Dataset passed validation checks with zero missing values and clean feature columns.")

        return df_clean, logs, ops

    @staticmethod
    def analyze_dataset_and_recommend(df: pd.DataFrame, target_column: str) -> Dict[str, Any]:
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in dataset.")

        target_series = df[target_column].dropna()
        n_rows = len(df)
        predictor_cols = [c for c in df.columns if c != target_column]
        n_features = len(predictor_cols)

        if n_features == 0:
            raise ValueError("Dataset has no predictor features (excluding target column).")

        unique_vals = int(target_series.nunique())
        if unique_vals < 2:
            val_str = f"'{target_series.iloc[0]}'" if unique_vals == 1 else "none"
            raise ValueError(f"Target column '{target_column}' contains only {unique_vals} unique value ({val_str}). Machine learning requires at least 2 distinct target class values.")

        # Separate feature types
        numeric_preds = [c for c in predictor_cols if pd.api.types.is_numeric_dtype(df[c])]
        cat_preds = [c for c in predictor_cols if c not in numeric_preds]
        num_count = len(numeric_preds)
        cat_count = len(cat_preds)

        num_ratio = num_count / max(1, n_features)
        cat_ratio = cat_count / max(1, n_features)
        has_mixed = num_count > 0 and cat_count > 0

        # Detect problem type
        is_numeric = pd.api.types.is_numeric_dtype(target_series) and not pd.api.types.is_bool_dtype(target_series)

        if is_numeric and unique_vals > 10:
            problem_type = "regression"
            class_balance = None
        else:
            problem_type = "classification"
            val_counts = target_series.value_counts(normalize=True).to_dict()
            class_balance = {str(k): round(float(v), 4) for k, v in val_counts.items()}

        candidates = []

        if problem_type == "classification":
            min_class_freq = min(class_balance.values()) if class_balance else 1.0

            # Dynamic score 1: Random Forest Classifier
            rf_score = 0.85
            if has_mixed: rf_score += 0.05
            if n_features >= 5: rf_score += 0.03
            if n_rows >= 100: rf_score += 0.02
            if min_class_freq < 0.2: rf_score += 0.03
            rf_score = round(min(0.97, max(0.62, rf_score)), 2)

            rf_reasoning = [
                f"Evaluates dataset with {n_rows} rows and {n_features} features ({num_count} numeric, {cat_count} categorical/text).",
                f"Target '{target_column}' has {unique_vals} discrete classes.",
                "Handles non-linear relationships and feature interactions robustly without requiring scale normalization."
            ]
            if min_class_freq < 0.2:
                rf_reasoning.append(f"Minority class frequency is {min_class_freq*100:.1f}%. Random Forest handles mild class imbalance well.")

            candidates.append({
                "algorithm": "Random Forest Classifier",
                "score": rf_score,
                "reasoning": rf_reasoning,
                "recommended": False
            })

            # Dynamic score 2: Gradient Boosting Classifier
            gb_score = 0.82
            if n_rows >= 300: gb_score += 0.07
            if has_mixed: gb_score += 0.04
            if n_features >= 8: gb_score += 0.04
            if n_rows < 50: gb_score -= 0.08
            gb_score = round(min(0.96, max(0.58, gb_score)), 2)

            gb_reasoning = [
                f"Sequential boosting optimizes decision boundaries across {n_features} feature splits.",
                f"Evaluates residual minimization for {n_rows} dataset instances.",
                "Ideal for tabular dataset structure with mixed numeric/categorical feature types."
            ]
            candidates.append({
                "algorithm": "Gradient Boosting Classifier",
                "score": gb_score,
                "reasoning": gb_reasoning,
                "recommended": False
            })

            # Dynamic score 3: Logistic Regression
            lr_score = 0.68
            if num_ratio >= 0.75: lr_score += 0.15
            if unique_vals == 2: lr_score += 0.08
            if cat_ratio >= 0.5: lr_score -= 0.10
            if n_features > 15: lr_score -= 0.06
            lr_score = round(min(0.94, max(0.50, lr_score)), 2)

            lr_reasoning = [
                f"Linear decision boundary serving as a fast interpretable baseline across {num_count} numeric predictors.",
                f"Optimizes log-loss for {unique_vals} target classes.",
                "Requires scaled numerical inputs and one-hot encoded categorical variables; may underfit complex non-linear interactions."
            ]
            candidates.append({
                "algorithm": "Logistic Regression",
                "score": lr_score,
                "reasoning": lr_reasoning,
                "recommended": False
            })

        else:
            target_std = float(target_series.std()) if len(target_series) > 1 else 0.0

            # Dynamic score 1: Random Forest Regressor
            rf_score = 0.86
            if has_mixed: rf_score += 0.05
            if n_rows >= 100: rf_score += 0.04
            if n_features >= 5: rf_score += 0.03
            rf_score = round(min(0.97, max(0.62, rf_score)), 2)

            rf_reasoning = [
                f"Target '{target_column}' is continuous (std dev: {target_std:.2f}).",
                f"Evaluates non-linear splits across {n_features} predictors ({num_count} numeric, {cat_count} categorical/text).",
                "Resilient against outliers in numerical feature distributions."
            ]
            candidates.append({
                "algorithm": "Random Forest Regressor",
                "score": rf_score,
                "reasoning": rf_reasoning,
                "recommended": False
            })

            # Dynamic score 2: Gradient Boosting Regressor
            gb_score = 0.83
            if n_rows >= 250: gb_score += 0.08
            if n_features >= 8: gb_score += 0.04
            if n_rows < 50: gb_score -= 0.06
            gb_score = round(min(0.95, max(0.58, gb_score)), 2)

            gb_reasoning = [
                f"Gradient boosted decision trees minimize squared error iteratively across {n_rows} rows.",
                "High capacity model suitable for tabular continuous targets."
            ]
            candidates.append({
                "algorithm": "Gradient Boosting Regressor",
                "score": gb_score,
                "reasoning": gb_reasoning,
                "recommended": False
            })

            # Dynamic score 3: Ridge Regressor
            ridge_score = 0.66
            if num_ratio >= 0.75: ridge_score += 0.16
            if cat_ratio >= 0.5: ridge_score -= 0.12
            if n_features <= 10: ridge_score += 0.04
            ridge_score = round(min(0.92, max(0.48, ridge_score)), 2)

            ridge_reasoning = [
                f"L2-regularized linear regression baseline across {num_count} numeric predictors.",
                "Fast training time; useful for checking linear correlation with target."
            ]
            candidates.append({
                "algorithm": "Ridge Linear Regression",
                "score": ridge_score,
                "reasoning": ridge_reasoning,
                "recommended": False
            })

        # Sort candidates by match score descending and set top candidate as recommended
        candidates.sort(key=lambda c: c["score"], reverse=True)
        if candidates:
            candidates[0]["recommended"] = True

        return {
            "target_column": target_column,
            "problem_type": problem_type,
            "class_balance": class_balance,
            "feature_count": n_features,
            "candidates": candidates
        }

    @staticmethod
    def train_model(df: pd.DataFrame, target_column: str, selected_algorithm: str) -> Dict[str, Any]:
        df_clean = df.dropna(subset=[target_column]).copy()
        X = df_clean.drop(columns=[target_column])
        y = df_clean[target_column]

        if len(X.columns) == 0:
            raise ValueError("No feature columns available to train model after cleaning.")

        # Separate numeric, categorical, and text features
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        non_numeric_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()

        categorical_cols = []
        text_cols = []

        for col in non_numeric_cols:
            sample_vals = X[col].dropna().astype(str).head(100)
            has_spaces = any(' ' in val for val in sample_vals)
            unique_cnt = int(X[col].nunique())
            if has_spaces or unique_cnt > 30:
                text_cols.append(col)
            else:
                categorical_cols.append(col)

        # Build Preprocessor
        transformers = []
        if numeric_cols:
            numeric_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='median')),
                ('scaler', StandardScaler())
            ])
            transformers.append(('num', numeric_transformer, numeric_cols))

        if categorical_cols:
            categorical_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='most_frequent')),
                ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
            ])
            transformers.append(('cat', categorical_transformer, categorical_cols))

        for t_col in text_cols:
            text_transformer = Pipeline(steps=[
                ('fill', FunctionTransformer(fill_text_na, feature_names_out='one-to-one')),
                ('tfidf', TfidfVectorizer(max_features=100, stop_words='english'))
            ])
            transformers.append((f'text_{t_col}', text_transformer, t_col))

        preprocessor = ColumnTransformer(transformers=transformers)

        # Determine model object
        is_classification = "Classifier" in selected_algorithm or "Logistic" in selected_algorithm
        problem_type = "classification" if is_classification else "regression"

        if selected_algorithm == "Random Forest Classifier":
            model = RandomForestClassifier(n_estimators=100, random_state=42)
        elif selected_algorithm == "Gradient Boosting Classifier":
            model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        elif selected_algorithm == "Logistic Regression":
            model = LogisticRegression(random_state=42)
        elif selected_algorithm == "Random Forest Regressor":
            model = RandomForestRegressor(n_estimators=100, random_state=42)
        elif selected_algorithm == "Gradient Boosting Regressor":
            model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        else:
            model = Ridge(random_state=42)

        clf = Pipeline(steps=[('preprocessor', preprocessor), ('model', model)])

        # Split data
        if len(X) > 10:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        else:
            X_train, X_test, y_train, y_test = X, X, y, y

        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)

        metrics = {}
        conf_matrix = None
        residual_data = None

        if problem_type == "classification":
            acc = float(accuracy_score(y_test, y_pred))
            prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted', zero_division=0)
            metrics = {
                "accuracy": round(acc, 4),
                "precision": round(float(prec), 4),
                "recall": round(float(rec), 4),
                "f1_score": round(float(f1), 4)
            }
            try:
                cm = confusion_matrix(y_test, y_pred)
                conf_matrix = cm.tolist()
            except Exception:
                conf_matrix = None
        else:
            r2 = float(r2_score(y_test, y_pred))
            mse = float(mean_squared_error(y_test, y_pred))
            rmse = float(np.sqrt(mse))
            mae = float(mean_absolute_error(y_test, y_pred))
            metrics = {
                "r2_score": round(r2, 4),
                "rmse": round(rmse, 4),
                "mae": round(mae, 4)
            }
            # Residuals plot sample
            residuals = (y_test - y_pred).tolist()
            residual_data = [{"actual": float(act), "predicted": float(pred), "residual": float(res)}
                             for act, pred, res in zip(y_test.head(20), y_pred[:20], residuals[:20])]

        # Extract Feature Importances if available
        feature_importances = {}
        try:
            feat_names = [str(f).split('__')[-1] for f in preprocessor.get_feature_names_out()]
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                for name, imp in zip(feat_names, importances):
                    feature_importances[name] = round(float(imp), 4)
            elif hasattr(model, 'coef_'):
                coefs = np.abs(model.coef_).flatten() if hasattr(model.coef_, 'flatten') else np.abs(model.coef_[0])
                for name, coef in zip(feat_names, coefs[:len(feat_names)]):
                    feature_importances[name] = round(float(coef), 4)
        except Exception:
            feature_importances = {}

        return {
            "status": "completed",
            "problem_type": problem_type,
            "metrics": metrics,
            "confusion_matrix": conf_matrix,
            "feature_importances": feature_importances,
            "residual_plot_data": residual_data
        }

    @classmethod
    def run_auto_pipeline(cls, df: pd.DataFrame, target_column: str = None) -> Dict[str, Any]:
        """
        Executes the entire end-to-end automated pipeline:
        1. Auto-detect target column if not provided.
        2. Auto-clean & preprocess dataset.
        3. Compute dynamic match scores for candidates.
        4. Auto-select top-scoring candidate and train model.
        5. Return full unified payload for UI rendering.
        """
        # Step 1: Target Auto-Detection
        if not target_column:
            target_column, detection_reason = cls.auto_detect_target(df)
        else:
            detection_reason = f"Target column '{target_column}' specified by user."

        # Step 2: Auto-Clean & Preprocess
        df_cleaned, cleaning_logs, lineage_ops = cls.auto_clean_and_preprocess(df, target_column)

        # Step 3: Analyze & Recommend Algorithm Candidates (with real dynamic scores)
        recommendations = cls.analyze_dataset_and_recommend(df_cleaned, target_column)

        # Step 4: Auto-select winner (top candidate) & Train
        top_candidate = recommendations["candidates"][0] if recommendations["candidates"] else None
        if not top_candidate:
            raise ValueError("No viable algorithm candidates found for this dataset.")

        winning_algorithm = top_candidate["algorithm"]
        train_results = cls.train_model(df_cleaned, target_column, winning_algorithm)

        return {
            "target_column": target_column,
            "target_detection_reason": detection_reason,
            "cleaning_logs": cleaning_logs,
            "lineage_ops": lineage_ops,
            "problem_type": recommendations["problem_type"],
            "class_balance": recommendations["class_balance"],
            "feature_count": recommendations["feature_count"],
            "candidates": recommendations["candidates"],
            "selected_algorithm": winning_algorithm,
            "training_results": train_results,
            "cleaned_row_count": len(df_cleaned),
            "cleaned_col_count": len(df_cleaned.columns)
        }

