"""
GridGuard AI - Baseline Failure Probability Regressors
Student 3: AI Engineer 1 (Tabular ML & Grid Diagnostics)
Lane 2: AI Service (Tabular ML)

Implements continuous failure probability regression models (Ridge & Random Forest),
manages model serialization with Joblib, and benchmarks raw telemetry vs engineered pipelines.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor

from ..features.feature_builder import build_feature_pipeline
from ..evaluation.metrics import evaluate_model_holdout, format_metrics_comparison_table


DEFAULT_ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "artifacts"


def build_baseline_ridge(alpha: float = 1.0, random_state: int = 42) -> Ridge:
    """
    Constructs a baseline Ridge Regression model with L2 regularization.
    """
    return Ridge(alpha=alpha, random_state=random_state)


def build_baseline_random_forest(
    n_estimators: int = 100,
    max_depth: Optional[int] = 12,
    min_samples_split: int = 5,
    random_state: int = 42,
    n_jobs: int = -1,
) -> RandomForestRegressor:
    """
    Constructs a baseline Random Forest Regressor for non-linear grid asset degradation modeling.
    """
    return RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        random_state=random_state,
        n_jobs=n_jobs,
    )


def build_full_regression_pipeline(
    regressor: Any,
    include_health_score: bool = True,
    include_interaction_features: bool = True,
    robust_scaling: bool = False,
) -> Pipeline:
    """
    Combines feature engineering and preprocessing with an estimator into an end-to-end Pipeline.
    """
    feat_pipe = build_feature_pipeline(
        include_health_score=include_health_score,
        include_interaction_features=include_interaction_features,
        robust_scaling=robust_scaling,
    )
    return Pipeline(steps=[("features", feat_pipe), ("regressor", regressor)])


def train_baseline_suite(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: Optional[pd.DataFrame] = None,
    y_test: Optional[pd.Series] = None,
    artifacts_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Trains the full suite of baseline models specified in Sprint 2:
      1. Raw Telemetry Baseline (Ridge on raw telemetry alone without Health_Score, verifying R² ≈ 0.00)
      2. Feature Engineered Ridge Regressor
      3. Feature Engineered Random Forest Regressor
    
    Optionally evaluates on holdout test set and saves trained artifacts using Joblib.
    """
    results: Dict[str, Any] = {
        "models": {},
        "evaluation_metrics": [],
        "artifacts_paths": {},
    }

    # 1. Raw Telemetry Baseline (No Health_Score, No Interaction Features)
    raw_ridge_pipe = build_full_regression_pipeline(
        regressor=build_baseline_ridge(),
        include_health_score=False,
        include_interaction_features=False,
    )
    raw_ridge_pipe.fit(X_train, y_train)
    results["models"]["raw_telemetry_ridge"] = raw_ridge_pipe

    # 2. Feature Engineered Ridge Regressor (Full Pipeline + Interaction Features)
    eng_ridge_pipe = build_full_regression_pipeline(
        regressor=build_baseline_ridge(),
        include_health_score=True,
        include_interaction_features=True,
    )
    eng_ridge_pipe.fit(X_train, y_train)
    results["models"]["ridge_baseline"] = eng_ridge_pipe

    # 3. Feature Engineered Random Forest Regressor
    eng_rf_pipe = build_full_regression_pipeline(
        regressor=build_baseline_random_forest(),
        include_health_score=True,
        include_interaction_features=True,
    )
    eng_rf_pipe.fit(X_train, y_train)
    results["models"]["rf_baseline"] = eng_rf_pipe

    # Evaluate on test set if provided
    if X_test is not None and y_test is not None:
        metrics_list = []
        metrics_list.append(evaluate_model_holdout(raw_ridge_pipe, X_test, y_test, model_name="Raw Telemetry Baseline (No Health_Score)"))
        metrics_list.append(evaluate_model_holdout(eng_ridge_pipe, X_test, y_test, model_name="Ridge Regressor (Engineered Features)"))
        metrics_list.append(evaluate_model_holdout(eng_rf_pipe, X_test, y_test, model_name="Random Forest Regressor (Engineered Features)"))
        results["evaluation_metrics"] = metrics_list
        results["comparison_table"] = format_metrics_comparison_table(metrics_list)

    # Save artifacts if requested
    target_dir = Path(artifacts_dir) if artifacts_dir else DEFAULT_ARTIFACTS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    # Save the standalone feature pipeline
    feature_pipeline = build_feature_pipeline(include_health_score=True, include_interaction_features=True)
    feature_pipeline.fit(X_train)
    feat_path = target_dir / "feature_pipeline.joblib"
    joblib.dump(feature_pipeline, feat_path)
    results["artifacts_paths"]["feature_pipeline"] = str(feat_path)

    # Save trained baseline models
    ridge_path = target_dir / "ridge_baseline.joblib"
    rf_path = target_dir / "rf_baseline.joblib"
    raw_path = target_dir / "raw_telemetry_baseline.joblib"

    joblib.dump(eng_ridge_pipe, ridge_path)
    joblib.dump(eng_rf_pipe, rf_path)
    joblib.dump(raw_ridge_pipe, raw_path)

    results["artifacts_paths"]["ridge_baseline"] = str(ridge_path)
    results["artifacts_paths"]["rf_baseline"] = str(rf_path)
    results["artifacts_paths"]["raw_telemetry_baseline"] = str(raw_path)

    return results


def load_model_artifacts(artifacts_dir: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Loads saved model pipelines and feature transformers from disk.
    """
    target_dir = Path(artifacts_dir) if artifacts_dir else DEFAULT_ARTIFACTS_DIR
    if not target_dir.exists():
        raise FileNotFoundError(f"Artifacts directory '{target_dir}' does not exist.")

    loaded: Dict[str, Any] = {}
    for artifact_name in ["feature_pipeline", "ridge_baseline", "rf_baseline", "raw_telemetry_baseline"]:
        file_path = target_dir / f"{artifact_name}.joblib"
        if file_path.exists():
            loaded[artifact_name] = joblib.load(file_path)

    return loaded
