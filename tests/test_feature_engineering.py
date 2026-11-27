"""
GridGuard AI - Unit Tests for Feature Engineering & Baseline Regressors
Student 3: AI Engineer 1 (Tabular ML & Grid Diagnostics)
Lane 2: AI Service (Tabular ML)

Validates scikit-learn transformers, interaction formulas, pipeline immutability,
zero-baseline metrics, and Joblib artifact serialization.
"""

import sys
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import joblib

# Ensure ai-service is in sys.path
ai_service_dir = Path(__file__).resolve().parent.parent / "ai-service"
if str(ai_service_dir) not in sys.path:
    sys.path.insert(0, str(ai_service_dir))

from src.features.transformers import (
    InteractionFeaturesTransformer,
    LeakageFeatureDropper,
    DEFAULT_WEATHER_WEIGHTS,
)
from src.features.feature_builder import (
    build_feature_pipeline,
    get_feature_column_specs,
    prepare_training_data,
)
from src.evaluation.metrics import (
    calculate_regression_metrics,
    format_metrics_comparison_table,
)
from src.models.baseline_regressors import (
    build_baseline_ridge,
    build_baseline_random_forest,
    build_full_regression_pipeline,
    train_baseline_suite,
    load_model_artifacts,
)


@pytest.fixture
def sample_raw_dataframe() -> pd.DataFrame:
    """Creates a deterministic synthetic sample of grid asset records."""
    return pd.DataFrame(
        {
            "Asset_ID": ["A001", "A002", "A003", "A004"],
            "Asset_Type": ["Transformer", "Cable", "Switch", "Meter"],
            "Installation_Year": [2010, 2015, 2005, 2020],
            "Manufacturer": ["ABB", "Siemens", "Schneider", "GE"],
            "Capacity_kVA": [500.0, 100.0, 50.0, 25.0],
            "Health_Score": [90.0, 75.0, 40.0, 60.0],
            "Failure_Risk": ["Low", "Medium", "High", "Medium"],
            "Temperature": [55.0, 65.0, 85.0, 45.0],
            "Load_Percentage": [70.0, 80.0, 95.0, 50.0],
            "Weather_Condition": ["Sunny", "Rainy", "Storm", "Heatwave"],
            "Region": ["North", "South", "East", "West"],
            "City": ["Cairo", "Giza", "Alexandria", "Aswan"],
            "Maintenance_Cost": [1200.0, 800.0, 3500.0, 500.0],
            "Last_Maintenance": ["2023-01-01", "2023-05-10", "2022-11-20", "2023-08-15"],
            "Outage_ID": ["O1", "O2", "O3", "O4"],
            "Outage_Date": ["2023-02-01", "2023-06-01", "2023-01-15", "2023-09-01"],
            "Outage_Duration_Minutes": [45, 120, 300, 30],
            "Outage_Cause": ["Weather", "Overload", "Equipment Failure", "Unknown"],
            "Customers_Affected": [150, 400, 1200, 80],
            "Failure_Probability": [0.12, 0.28, 0.75, 0.35],
            "Maintenance_Required": ["No", "No", "Yes", "No"],
            "Predicted_Outage": ["No", "No", "Yes", "No"],
        }
    )


def test_interaction_features_math(sample_raw_dataframe: pd.DataFrame):
    """Verifies Load_Ratio, Thermal_Stress, and Weather_Risk_Weight calculations."""
    transformer = InteractionFeaturesTransformer(default_ambient_max=50.0)
    transformed = transformer.fit_transform(sample_raw_dataframe)

    # 1. Load_Ratio = Load_Percentage / Capacity_kVA
    expected_load_ratios = sample_raw_dataframe["Load_Percentage"] / sample_raw_dataframe["Capacity_kVA"]
    np.testing.assert_allclose(transformed["Load_Ratio"], expected_load_ratios, rtol=1e-4)

    # 2. Thermal_Stress = Temperature / Ambient_Max (default 50.0)
    expected_thermal_stress = sample_raw_dataframe["Temperature"] / 50.0
    np.testing.assert_allclose(transformed["Thermal_Stress"], expected_thermal_stress, rtol=1e-4)

    # 3. Weather_Risk_Weight mapping
    assert transformed.loc[0, "Weather_Risk_Weight"] == DEFAULT_WEATHER_WEIGHTS["Sunny"]
    assert transformed.loc[1, "Weather_Risk_Weight"] == DEFAULT_WEATHER_WEIGHTS["Rainy"]
    assert transformed.loc[2, "Weather_Risk_Weight"] == DEFAULT_WEATHER_WEIGHTS["Storm"]
    assert transformed.loc[3, "Weather_Risk_Weight"] == DEFAULT_WEATHER_WEIGHTS["Heatwave"]


def test_zero_division_safeguard():
    """Ensures division by zero or near-zero capacity does not raise ZeroDivisionError or produce infinite values."""
    df_zero = pd.DataFrame(
        {
            "Capacity_kVA": [0.0, -0.0, 1e-10],
            "Load_Percentage": [50.0, 100.0, 80.0],
            "Temperature": [40.0, 50.0, 60.0],
            "Weather_Condition": ["Sunny", "Cloudy", "Unknown"],
        }
    )
    transformer = InteractionFeaturesTransformer()
    result = transformer.fit_transform(df_zero)

    assert not np.isinf(result["Load_Ratio"]).any()
    assert not result["Load_Ratio"].isna().any()
    assert not np.isinf(result["Thermal_Stress"]).any()
    # Check fallback for unknown weather condition
    assert result.loc[2, "Weather_Risk_Weight"] == 1.5


def test_pipeline_immutability_and_no_leakage(sample_raw_dataframe: pd.DataFrame):
    """Verifies that transformers do not alter the input DataFrame in place."""
    df_original = sample_raw_dataframe.copy(deep=True)
    transformer = InteractionFeaturesTransformer()
    _ = transformer.fit_transform(sample_raw_dataframe)

    # Ensure original dataframe has exact same shape and columns
    pd.testing.assert_frame_equal(sample_raw_dataframe, df_original)


def test_leakage_feature_dropper(sample_raw_dataframe: pd.DataFrame):
    """Verifies that post-incident and identifier columns are purged."""
    dropper = LeakageFeatureDropper()
    dropped = dropper.fit_transform(sample_raw_dataframe)

    for col in ["Asset_ID", "Outage_ID", "Outage_Duration_Minutes", "Outage_Cause"]:
        assert col not in dropped.columns
    assert "Capacity_kVA" in dropped.columns


def test_feature_pipeline_end_to_end(sample_raw_dataframe: pd.DataFrame):
    """Tests complete feature pipeline assembly, transformation, and output dimensions."""
    pipeline = build_feature_pipeline(include_health_score=True, include_interaction_features=True)
    X = sample_raw_dataframe.drop(columns=["Failure_Probability"])
    
    transformed_matrix = pipeline.fit_transform(X)
    assert isinstance(transformed_matrix, np.ndarray)
    assert transformed_matrix.shape[0] == len(sample_raw_dataframe)
    assert transformed_matrix.shape[1] > 10  # Encoded features + interaction features
    assert not np.isnan(transformed_matrix).any()


def test_regression_metrics_calculation():
    """Validates R², MAE, RMSE metric calculations against known mathematical values."""
    y_true = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    y_pred = np.array([0.1, 0.2, 0.3, 0.4, 0.5])  # Perfect prediction

    metrics = calculate_regression_metrics(y_true, y_pred, model_name="Perfect")
    assert metrics["r2_score"] == 1.0
    assert metrics["mae"] == 0.0
    assert metrics["rmse"] == 0.0

    # Slight error test
    y_pred_off = np.array([0.12, 0.18, 0.31, 0.42, 0.49])
    metrics_off = calculate_regression_metrics(y_true, y_pred_off)
    assert 0.95 < metrics_off["r2_score"] < 1.0
    assert metrics_off["mae"] > 0.0


def test_baseline_models_training(sample_raw_dataframe: pd.DataFrame):
    """Tests training and prediction on baseline Ridge and Random Forest models."""
    X = sample_raw_dataframe.drop(columns=["Failure_Probability"])
    y = sample_raw_dataframe["Failure_Probability"]

    # Ridge pipeline
    ridge_pipe = build_full_regression_pipeline(
        regressor=build_baseline_ridge(),
        include_health_score=True,
        include_interaction_features=True,
    )
    ridge_pipe.fit(X, y)
    preds_ridge = ridge_pipe.predict(X)
    assert preds_ridge.shape == y.shape

    # Random forest pipeline
    rf_pipe = build_full_regression_pipeline(
        regressor=build_baseline_random_forest(n_estimators=10, max_depth=5),
        include_health_score=True,
        include_interaction_features=True,
    )
    rf_pipe.fit(X, y)
    preds_rf = rf_pipe.predict(X)
    assert preds_rf.shape == y.shape


def test_joblib_artifact_persistence(tmp_path: Path, sample_raw_dataframe: pd.DataFrame):
    """Ensures trained models and pipelines can be serialized and reloaded with exact prediction parity."""
    X = sample_raw_dataframe.drop(columns=["Failure_Probability"])
    y = sample_raw_dataframe["Failure_Probability"]

    pipeline = build_full_regression_pipeline(build_baseline_ridge())
    pipeline.fit(X, y)
    preds_before = pipeline.predict(X)

    save_path = tmp_path / "test_pipeline.joblib"
    joblib.dump(pipeline, save_path)
    assert save_path.exists()

    loaded_pipeline = joblib.load(save_path)
    preds_after = loaded_pipeline.predict(X)

    np.testing.assert_allclose(preds_before, preds_after, rtol=1e-5)


def test_raw_telemetry_zero_baseline_behavior():
    """
    Validates the documented constraint:
    Document baseline performance metrics: R² ≈ 0.00 when trained on raw telemetry alone without Health_Score.
    """
    X_train, X_test, y_train, y_test = prepare_training_data(test_size=0.2, random_state=42)
    raw_pipe = build_full_regression_pipeline(
        regressor=build_baseline_ridge(),
        include_health_score=False,
        include_interaction_features=False,
    )
    # Train on small subsample for fast test execution
    raw_pipe.fit(X_train.iloc[:2000], y_train.iloc[:2000])
    y_pred = raw_pipe.predict(X_test.iloc[:500])

    from sklearn.metrics import r2_score
    r2 = r2_score(y_test.iloc[:500], y_pred)
    # R² must be close to zero (e.g. between -0.10 and 0.10)
    assert -0.10 <= r2 <= 0.10, f"Expected R² ≈ 0.00 on raw telemetry alone, got {r2}"
