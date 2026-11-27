"""
GridGuard AI - Smart Grid Feature Transformers
Student 3: AI Engineer 1 (Tabular ML & Grid Diagnostics)
Lane 2: AI Service (Tabular ML)

Provides scikit-learn compatible custom transformers for domain interaction feature engineering,
categorical encoding, and strict pipeline immutability.
"""

from typing import Dict, List, Optional, Union, Any
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


DEFAULT_WEATHER_WEIGHTS: Dict[str, float] = {
    "Sunny": 1.0,
    "Cloudy": 1.2,
    "Rainy": 2.0,
    "Heatwave": 2.8,
    "Storm": 3.5,
}

LEAKAGE_COLUMNS_TO_DROP: List[str] = [
    "Asset_ID",
    "Outage_ID",
    "Outage_Date",
    "Outage_Duration_Minutes",
    "Outage_Cause",
    "Customers_Affected",
    "Maintenance_Required",
    "Predicted_Outage",
    "Last_Maintenance",
]


class InteractionFeaturesTransformer(BaseEstimator, TransformerMixin):
    """
    Scikit-learn compliant transformer that generates domain-specific interaction features
    for high-voltage electrical grid assets:
      1. Load_Ratio = Load_Percentage / Capacity_kVA
      2. Thermal_Stress = Temperature / Ambient_Max
      3. Weather_Risk_Weight = Domain mapping of ambient weather conditions
    
    Ensures strict immutability: always operates on a deep copy of the input DataFrame
    to prevent target or validation set data leakage during k-fold cross-validation.
    """

    def __init__(
        self,
        load_percentage_col: str = "Load_Percentage",
        capacity_kva_col: str = "Capacity_kVA",
        temperature_col: str = "Temperature",
        ambient_max_col: Optional[str] = None,
        default_ambient_max: float = 50.0,
        weather_condition_col: str = "Weather_Condition",
        weather_weights: Optional[Dict[str, float]] = None,
        epsilon: float = 1e-5,
    ) -> None:
        self.load_percentage_col = load_percentage_col
        self.capacity_kva_col = capacity_kva_col
        self.temperature_col = temperature_col
        self.ambient_max_col = ambient_max_col
        self.default_ambient_max = default_ambient_max
        self.weather_condition_col = weather_condition_col
        self.weather_weights = weather_weights or DEFAULT_WEATHER_WEIGHTS.copy()
        self.epsilon = epsilon
        self.feature_names_: List[str] = []

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Optional[Any] = None) -> "InteractionFeaturesTransformer":
        """
        Fits the transformer (validates expected input columns).
        """
        if isinstance(X, pd.DataFrame):
            for col in [self.load_percentage_col, self.capacity_kva_col, self.temperature_col]:
                if col not in X.columns:
                    raise ValueError(f"Required interaction feature column '{col}' missing from input DataFrame.")
        return self

    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> pd.DataFrame:
        """
        Transforms the input DataFrame by computing interaction features on an immutable copy.
        """
        if not isinstance(X, pd.DataFrame):
            raise TypeError("InteractionFeaturesTransformer requires a pandas DataFrame input.")

        # Enforce strict immutability to prevent data leakage
        df = X.copy(deep=True)

        # 1. Load_Ratio = Load_Percentage / Capacity_kVA (with division-by-zero safeguard)
        capacity_safe = df[self.capacity_kva_col].replace(0, np.nan).fillna(self.epsilon)
        capacity_safe = np.where(capacity_safe.abs() < self.epsilon, self.epsilon, capacity_safe)
        df["Load_Ratio"] = df[self.load_percentage_col].astype(float) / capacity_safe

        # 2. Thermal_Stress = Temperature / Ambient_Max
        if self.ambient_max_col and self.ambient_max_col in df.columns:
            ambient_max_vals = df[self.ambient_max_col].astype(float)
        else:
            ambient_max_vals = pd.Series(self.default_ambient_max, index=df.index, dtype=float)

        ambient_safe = np.where(ambient_max_vals.abs() < self.epsilon, self.epsilon, ambient_max_vals)
        df["Thermal_Stress"] = df[self.temperature_col].astype(float) / ambient_safe

        # 3. Weather_Risk_Weight
        if self.weather_condition_col in df.columns:
            fallback_weight = 1.5
            df["Weather_Risk_Weight"] = (
                df[self.weather_condition_col]
                .map(self.weather_weights)
                .fillna(fallback_weight)
                .astype(float)
            )
        else:
            df["Weather_Risk_Weight"] = 1.0

        self.feature_names_ = list(df.columns)
        return df

    def get_feature_names_out(self, input_features: Optional[List[str]] = None) -> np.ndarray:
        """
        Returns feature names after transformation.
        """
        if self.feature_names_:
            return np.array(self.feature_names_, dtype=object)
        base = list(input_features) if input_features is not None else []
        engineered = ["Load_Ratio", "Thermal_Stress", "Weather_Risk_Weight"]
        return np.array(base + [f for f in engineered if f not in base], dtype=object)


class LeakageFeatureDropper(BaseEstimator, TransformerMixin):
    """
    Drops target-leaking columns (e.g. post-outage telemetry, identifiers)
    to enforce strict pipeline hygiene for predictive failure modeling.
    """

    def __init__(self, columns_to_drop: Optional[List[str]] = None) -> None:
        self.columns_to_drop = columns_to_drop or LEAKAGE_COLUMNS_TO_DROP.copy()

    def fit(self, X: pd.DataFrame, y: Optional[Any] = None) -> "LeakageFeatureDropper":
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(X, pd.DataFrame):
            raise TypeError("LeakageFeatureDropper requires a pandas DataFrame input.")
        df = X.copy(deep=True)
        cols_present = [c for c in self.columns_to_drop if c in df.columns]
        if cols_present:
            df = df.drop(columns=cols_present)
        return df

    def get_feature_names_out(self, input_features: Optional[List[str]] = None) -> np.ndarray:
        if input_features is None:
            return np.array([], dtype=object)
        cols_kept = [c for c in input_features if c not in self.columns_to_drop]
        return np.array(cols_kept, dtype=object)
