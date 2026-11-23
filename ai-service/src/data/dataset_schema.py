from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import pandas as pd


AssetType = Literal["Cable", "Switch", "Transformer", "Pole", "Meter"]
ManufacturerType = Literal["ABB", "Siemens", "Schneider", "Hitachi", "GE"]
FailureRiskType = Literal["Low", "Medium", "High"]
WeatherConditionType = Literal["Sunny", "Cloudy", "Rainy", "Storm", "Heatwave"]
BinaryChoiceType = Literal["Yes", "No"]


class SmartGridAssetRecord(BaseModel):
    """
    Strict Pydantic v2 schema validating a single row of the Smart Grid Asset Management dataset.
    Validates all 22 operational features, data types, physical constraints, and enum categories.
    """
    model_config = ConfigDict(extra="ignore")

    # Asset Identification & Metadata
    Asset_ID: str = Field(..., description="Unique equipment asset identifier")
    Asset_Type: AssetType = Field(..., description="Equipment asset classification")
    Installation_Year: int = Field(..., ge=1950, le=2030, description="Asset commissioning year")
    Manufacturer: str = Field(..., description="OEM equipment manufacturer")
    Capacity_kVA: float = Field(..., ge=0.0, description="Rated operational capacity in kVA")

    # Diagnostic & Health Metrics
    Health_Score: float = Field(..., ge=0.0, le=100.0, description="Periodic diagnostic inspection score (0-100)")
    Failure_Risk: FailureRiskType = Field(..., description="Categorical failure risk tier")

    # Operational Telemetry Features
    Temperature: float = Field(..., ge=-50.0, le=200.0, description="Operating temperature in Celsius")
    Load_Percentage: float = Field(..., ge=0.0, le=300.0, description="Current operational load percentage")
    Weather_Condition: WeatherConditionType = Field(..., description="Ambient weather condition at inspection")
    Region: str = Field(..., description="Geographical grid zone")
    City: str = Field(..., description="Substation municipal location")

    # Maintenance & Outage History
    Maintenance_Cost: float = Field(..., ge=0.0, description="Recorded maintenance expenditure in USD")
    Last_Maintenance: str = Field(..., description="Date of last scheduled maintenance (YYYY-MM-DD)")
    Outage_ID: str = Field(..., description="Historical outage incident identifier")
    Outage_Date: str = Field(..., description="Date of recorded outage incident (YYYY-MM-DD)")
    Outage_Duration_Minutes: float = Field(..., ge=0.0, description="Duration of outage in minutes")
    Outage_Cause: str = Field(..., description="Root cause classification of outage")
    Customers_Affected: int = Field(..., ge=0, description="Number of metered customers impacted by outage")

    # Target & Actionable Diagnostic Labels
    Failure_Probability: float = Field(..., ge=0.0, le=1.0, description="Estimated failure probability score")
    Maintenance_Required: BinaryChoiceType = Field(..., description="Immediate maintenance intervention flag")
    Predicted_Outage: BinaryChoiceType = Field(..., description="Predictive outage indicator flag")

    @field_validator("Asset_ID", "Outage_ID")
    @classmethod
    def validate_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Identifier must not be empty")
        return v.strip()


class DatasetValidationSummary(BaseModel):
    """
    Summary metrics and diagnostic output of dataset batch validation.
    """
    total_records: int
    valid_records: int
    invalid_records: int
    is_valid: bool
    asset_class_counts: Dict[str, int] = Field(default_factory=dict)
    failure_risk_counts: Dict[str, int] = Field(default_factory=dict)
    validation_errors: List[str] = Field(default_factory=list)


def validate_dataframe(df: pd.DataFrame, sample_size: Optional[int] = None) -> DatasetValidationSummary:
    """
    Validate a pandas DataFrame against the SmartGridAssetRecord Pydantic v2 schema.
    Optionally validates a representative sample or the entire batch.
    """
    target_df = df if sample_size is None else df.sample(n=min(sample_size, len(df)), random_state=42)
    records = target_df.to_dict(orient="records")

    valid_count = 0
    invalid_count = 0
    errors: List[str] = []

    for i, record in enumerate(records):
        try:
            SmartGridAssetRecord.model_validate(record)
            valid_count += 1
        except Exception as e:
            invalid_count += 1
            if len(errors) < 10:  # Capture first 10 errors for concise diagnostics
                errors.append(f"Row {i} [Asset: {record.get('Asset_ID', 'UNKNOWN')}]: {str(e)}")

    asset_counts = df["Asset_Type"].value_counts().to_dict() if "Asset_Type" in df.columns else {}
    risk_counts = df["Failure_Risk"].value_counts().to_dict() if "Failure_Risk" in df.columns else {}

    return DatasetValidationSummary(
        total_records=len(target_df),
        valid_records=valid_count,
        invalid_records=invalid_count,
        is_valid=(invalid_count == 0),
        asset_class_counts=asset_counts,
        failure_risk_counts=risk_counts,
        validation_errors=errors,
    )
