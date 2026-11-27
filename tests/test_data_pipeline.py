import os
import sys
from pathlib import Path
import tempfile
import pytest
import numpy as np
import pandas as pd
from pydantic import ValidationError

# Ensure ai-service is in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_AI_SERVICE_DIR = _PROJECT_ROOT / "ai-service"
if str(_AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_SERVICE_DIR))

from src.data.dataset_schema import (
    SmartGridAssetRecord,
    validate_dataframe,
    DatasetValidationSummary,
)
from src.data.loader import (
    load_raw_dataset,
    get_feature_types,
    get_dataset_diagnostics,
    resolve_dataset_path,
)
from src.data.eda_report import (
    compute_asset_class_distributions,
    compute_correlation_matrices,
    generate_empirical_finding_documentation,
)
from src.data.preprocessor import (
    GridGuardDataPreprocessor,
    run_preprocessing_pipeline,
)


@pytest.fixture
def sample_valid_record_dict():
    return {
        "Asset_ID": "A000001",
        "Asset_Type": "Transformer",
        "Installation_Year": 2010,
        "Manufacturer": "ABB",
        "Capacity_kVA": 500.0,
        "Health_Score": 75.0,
        "Failure_Risk": "Low",
        "Temperature": 45.0,
        "Load_Percentage": 60.0,
        "Weather_Condition": "Sunny",
        "Region": "North",
        "City": "Dhaka",
        "Maintenance_Cost": 1200.0,
        "Last_Maintenance": "2024-01-15",
        "Outage_ID": "O000001",
        "Outage_Date": "2024-06-20",
        "Outage_Duration_Minutes": 35.0,
        "Outage_Cause": "Weather",
        "Customers_Affected": 250,
        "Failure_Probability": 0.15,
        "Maintenance_Required": "No",
        "Predicted_Outage": "No",
    }


def test_pydantic_schema_valid_record(sample_valid_record_dict):
    """Verify that a valid dictionary adheres to the Pydantic dataset schema."""
    record = SmartGridAssetRecord.model_validate(sample_valid_record_dict)
    assert record.Asset_ID == "A000001"
    assert record.Asset_Type == "Transformer"
    assert record.Health_Score == 75.0
    assert record.Failure_Risk == "Low"


def test_pydantic_schema_invalid_record_raises():
    """Verify that Pydantic rejects invalid physical values and unknown asset categories."""
    invalid_dict = {
        "Asset_ID": "",  # Empty ID rejected by validator
        "Asset_Type": "NuclearReactor",  # Unknown category
        "Installation_Year": 1800,  # Below ge=1950
        "Manufacturer": "Unknown",
        "Capacity_kVA": -50.0,  # Negative capacity rejected
        "Health_Score": 150.0,  # Score > 100 rejected
        "Failure_Risk": "ExtremeDanger",  # Invalid enum
    }
    with pytest.raises(ValidationError):
        SmartGridAssetRecord.model_validate(invalid_dict)


def test_validate_dataframe_sample():
    """Verify batch validation across a DataFrame sample."""
    df, _ = load_raw_dataset(validate=False)
    summary = validate_dataframe(df, sample_size=500)
    assert isinstance(summary, DatasetValidationSummary)
    assert summary.total_records == 500
    assert summary.valid_records == 500
    assert summary.invalid_records == 0
    assert summary.is_valid is True


def test_load_raw_dataset_dimensions_and_features():
    """Verify that raw dataset loads all 50,000 records and 22 operational features."""
    df, summary = load_raw_dataset(sample_validation_size=100)
    assert len(df) == 50000
    assert len(df.columns) == 22
    assert summary is not None
    assert summary.is_valid is True

    diagnostics = get_dataset_diagnostics(df)
    assert diagnostics["total_records"] == 50000
    assert diagnostics["total_missing_values"] == 0


def test_feature_classification():
    """Verify that get_feature_types correctly categorizes all 22 columns."""
    df, _ = load_raw_dataset(validate=False)
    types_dict = get_feature_types(df)
    assert "Asset_ID" in types_dict["identifiers"]
    assert "Health_Score" in types_dict["diagnostic_features"]
    assert "Temperature" in types_dict["numeric_telemetry"]
    assert "Asset_Type" in types_dict["categorical_features"]
    assert "Failure_Risk" in types_dict["targets"]


def test_eda_asset_class_distributions():
    """Verify statistical distribution calculation across the 5 asset classes."""
    df, _ = load_raw_dataset(validate=False)
    distributions = compute_asset_class_distributions(df)
    
    expected_assets = {"Cable", "Switch", "Transformer", "Pole", "Meter"}
    assert set(distributions.keys()) == expected_assets

    for asset in expected_assets:
        metrics = distributions[asset]
        assert "Health_Score" in metrics
        assert "Temperature" in metrics
        assert metrics["Health_Score"]["count"] > 9000
        assert metrics["Health_Score"]["mean"] > 0
        assert metrics["Health_Score"]["iqr"] > 0


def test_scientific_empirical_finding_proof():
    """
    CRITICAL EMPIRICAL PROOF TEST:
    Verifies that raw operational telemetry alone has near-zero correlation with failure risk,
    while periodic diagnostic Health_Score exhibits massive decisive correlation.
    """
    df, _ = load_raw_dataset(validate=False)
    corr_data = compute_correlation_matrices(df)
    doc = generate_empirical_finding_documentation(corr_data)

    assert doc["empirical_proof_verified"] is True

    # 1. Raw telemetry correlation magnitude must be near-zero (< 0.05)
    telemetry_corrs = doc["raw_telemetry_correlations"]
    for feat, corr_val in telemetry_corrs.items():
        assert abs(corr_val) < 0.05, f"Raw telemetry feature '{feat}' has unexpectedly high correlation: {corr_val}"

    # 2. Diagnostic Health_Score must exhibit massive negative correlation (|r| > 0.85)
    health_corr = doc["health_score_correlation_to_risk"]
    assert health_corr is not None
    assert health_corr < -0.85, f"Health_Score correlation to failure risk is not decisively negative: {health_corr}"

    prob_corr = doc["health_score_correlation_to_failure_probability"]
    assert prob_corr is not None
    assert prob_corr < -0.90, f"Health_Score correlation to failure probability is weak: {prob_corr}"


def test_preprocessor_zero_data_leakage():
    """
    Verify strict 0% data leakage: train and test indices have zero overlap.
    """
    df, _ = load_raw_dataset(validate=False)
    preprocessor = GridGuardDataPreprocessor()
    X_train, X_test, y_train, y_test = preprocessor.split_data(df, test_size=0.20)

    # 0% index leakage
    overlap = set(X_train.index).intersection(set(X_test.index))
    assert len(overlap) == 0

    # Split sizes match 80/20
    assert len(X_train) == 40000
    assert len(X_test) == 10000


def test_preprocessor_pipeline_transformation_and_serialization():
    """
    Verify that the preprocessor cleans data, scales features, encodes categoricals,
    and accurately round-trips via Joblib.
    """
    df, _ = load_raw_dataset(validate=False)
    sample_df = df.sample(n=1000, random_state=42)

    with tempfile.TemporaryDirectory() as tmp_dir:
        res = run_preprocessing_pipeline(sample_df, output_dir=tmp_dir, test_size=0.20)
        assert res["status"] == "success"
        assert res["train_samples"] == 800
        assert res["test_samples"] == 200
        assert res["data_leakage_overlap_count"] == 0

        # Load serialized pipeline
        joblib_path = res["preprocessor_joblib_path"]
        assert os.path.exists(joblib_path)
        loaded = GridGuardDataPreprocessor.load(joblib_path)
        assert loaded.is_fitted is True

        # Test inference on test partition
        X_test = sample_df.drop(columns=["Failure_Risk"]).iloc[:5]
        transformed = loaded.transform(X_test)
        assert isinstance(transformed, np.ndarray)
        assert transformed.shape[0] == 5
        assert not np.isnan(transformed).any()
