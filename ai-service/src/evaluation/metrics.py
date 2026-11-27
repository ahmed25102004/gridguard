"""
GridGuard AI - Evaluation Metrics & Regression Harness
Student 3: AI Engineer 1 (Tabular ML & Grid Diagnostics)
Lane 2: AI Service (Tabular ML)

Provides standardized evaluation metrics (R2, MAE, RMSE) and cross-validation
utilities for smart grid continuous failure probability prediction.
"""

from typing import Dict, List, Optional, Union, Any
import numpy as np
import pandas as pd
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error,
    explained_variance_score,
    max_error,
)
from sklearn.model_selection import KFold, cross_val_score


def calculate_regression_metrics(
    y_true: Union[pd.Series, np.ndarray],
    y_pred: Union[pd.Series, np.ndarray],
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Computes standard regression performance metrics:
      - R² Score (Coefficient of Determination)
      - Mean Absolute Error (MAE)
      - Root Mean Squared Error (RMSE)
      - Max Error
      - Explained Variance Score
    """
    y_t = np.asarray(y_true).ravel()
    y_p = np.asarray(y_pred).ravel()

    r2 = float(r2_score(y_t, y_p))
    mae = float(mean_absolute_error(y_t, y_p))
    rmse = float(np.sqrt(mean_squared_error(y_t, y_p)))
    m_err = float(max_error(y_t, y_p))
    exp_var = float(explained_variance_score(y_t, y_p))

    metrics = {
        "r2_score": round(r2, 4),
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "max_error": round(m_err, 4),
        "explained_variance": round(exp_var, 4),
        "sample_count": len(y_t),
    }

    if model_name:
        metrics["model_name"] = model_name

    return metrics


def evaluate_model_holdout(
    model: Any,
    X_test: Union[pd.DataFrame, np.ndarray],
    y_test: Union[pd.Series, np.ndarray],
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates predictions on holdout test set and evaluates performance.
    """
    y_pred = model.predict(X_test)
    return calculate_regression_metrics(y_true=y_test, y_pred=y_pred, model_name=model_name)


def cross_validate_pipeline(
    pipeline: Any,
    X: pd.DataFrame,
    y: Union[pd.Series, np.ndarray],
    cv: int = 5,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Performs leakage-free k-fold cross-validation across the complete pipeline.
    """
    kf = KFold(n_splits=cv, shuffle=True, random_state=random_state)
    
    r2_scores = cross_val_score(pipeline, X, y, cv=kf, scoring="r2", n_jobs=-1)
    neg_mae_scores = cross_val_score(pipeline, X, y, cv=kf, scoring="neg_mean_absolute_error", n_jobs=-1)
    neg_rmse_scores = cross_val_score(pipeline, X, y, cv=kf, scoring="neg_root_mean_squared_error", n_jobs=-1)

    return {
        "cv_folds": cv,
        "r2_mean": round(float(np.mean(r2_scores)), 4),
        "r2_std": round(float(np.std(r2_scores)), 4),
        "mae_mean": round(float(np.mean(-neg_mae_scores)), 4),
        "mae_std": round(float(np.std(-neg_mae_scores)), 4),
        "rmse_mean": round(float(np.mean(-neg_rmse_scores)), 4),
        "rmse_std": round(float(np.std(-neg_rmse_scores)), 4),
    }


def format_metrics_comparison_table(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Formats a list of metric dictionaries into a comparative summary table.
    """
    df = pd.DataFrame(results)
    preferred_order = ["model_name", "r2_score", "mae", "rmse", "max_error", "explained_variance", "sample_count"]
    cols = [c for c in preferred_order if c in df.columns] + [c for c in df.columns if c not in preferred_order]
    return df[cols]
