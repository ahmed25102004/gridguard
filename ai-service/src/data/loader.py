import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import pandas as pd
from .dataset_schema import validate_dataframe, DatasetValidationSummary

DEFAULT_RAW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
FALLBACK_RAW_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "raw"
DEFAULT_FILENAME = "Smart_Grid_Asset_Management_50000.csv"


def resolve_dataset_path(provided_path: Optional[str] = None) -> Path:
    """
    Resolve the absolute path to the Smart Grid dataset file.
    Searches provided path, standard ai-service/data/raw, and root data/raw directories,
    supporting both .csv and .xlsx formats.
    """
    if provided_path:
        p = Path(provided_path)
        if p.exists():
            return p.resolve()

    candidate_locations = [
        DEFAULT_RAW_DIR / DEFAULT_FILENAME,
        DEFAULT_RAW_DIR / "Smart_Grid_Asset_Management_50000.xlsx",
        FALLBACK_RAW_DIR / DEFAULT_FILENAME,
        FALLBACK_RAW_DIR / "Smart_Grid_Asset_Management_50000.xlsx",
    ]

    for cand in candidate_locations:
        if cand.exists():
            return cand.resolve()

    # Search dynamically in raw directories
    for search_dir in [DEFAULT_RAW_DIR, FALLBACK_RAW_DIR]:
        if search_dir.exists():
            for f in search_dir.glob("*50000*"):
                if f.suffix.lower() in [".csv", ".xlsx", ".xls"]:
                    return f.resolve()

    raise FileNotFoundError(
        f"Smart Grid dataset not found. Checked: {[str(c) for c in candidate_locations]}. "
        f"Please place 'Smart_Grid_Asset_Management_50000.csv' in '{DEFAULT_RAW_DIR}'."
    )


def load_raw_dataset(
    file_path: Optional[str] = None,
    validate: bool = True,
    sample_validation_size: Optional[int] = 2000,
) -> Tuple[pd.DataFrame, Optional[DatasetValidationSummary]]:
    """
    Load raw Smart Grid asset telemetry and outage dataset into pandas DataFrame.
    Validates operational features against strict Pydantic dataset schema.
    """
    resolved = resolve_dataset_path(file_path)

    if resolved.suffix.lower() == ".csv":
        df = pd.read_csv(resolved)
    elif resolved.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(resolved)
    else:
        raise ValueError(f"Unsupported file format: {resolved.suffix}. Expected .csv or .xlsx")

    # Clean whitespace in string columns
    for col in df.select_dtypes(include=["object", "str"]).columns:
        df[col] = df[col].astype(str).str.strip()

    summary: Optional[DatasetValidationSummary] = None
    if validate:
        summary = validate_dataframe(df, sample_size=sample_validation_size)

    return df, summary


def get_feature_types(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Classify dataset features into operational telemetry, diagnostic targets, identifiers, and categories.
    """
    identifiers = ["Asset_ID", "Outage_ID"]
    date_columns = ["Last_Maintenance", "Outage_Date"]
    targets = ["Failure_Risk", "Failure_Probability", "Maintenance_Required", "Predicted_Outage"]
    
    numeric_telemetry = [
        "Capacity_kVA",
        "Temperature",
        "Load_Percentage",
        "Maintenance_Cost",
        "Outage_Duration_Minutes",
        "Customers_Affected",
    ]
    
    diagnostic_features = ["Health_Score", "Installation_Year"]
    
    categorical_features = [
        "Asset_Type",
        "Manufacturer",
        "Weather_Condition",
        "Region",
        "City",
        "Outage_Cause",
    ]

    return {
        "identifiers": [c for c in identifiers if c in df.columns],
        "date_columns": [c for c in date_columns if c in df.columns],
        "targets": [c for c in targets if c in df.columns],
        "numeric_telemetry": [c for c in numeric_telemetry if c in df.columns],
        "diagnostic_features": [c for c in diagnostic_features if c in df.columns],
        "categorical_features": [c for c in categorical_features if c in df.columns],
    }


def get_dataset_diagnostics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate diagnostic statistics for the ingested dataset.
    """
    missing_counts = df.isnull().sum().to_dict()
    total_missing = sum(missing_counts.values())

    return {
        "total_records": len(df),
        "total_features": len(df.columns),
        "memory_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
        "total_missing_values": total_missing,
        "features_with_missing": {k: v for k, v in missing_counts.items() if v > 0},
        "asset_class_breakdown": df["Asset_Type"].value_counts().to_dict() if "Asset_Type" in df.columns else {},
        "failure_risk_breakdown": df["Failure_Risk"].value_counts().to_dict() if "Failure_Risk" in df.columns else {},
    }
