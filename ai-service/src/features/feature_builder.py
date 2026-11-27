"""
GridGuard AI - Feature Pipeline Builder
Student 3: AI Engineer 1 (Tabular ML & Grid Diagnostics)
Lane 2: AI Service (Tabular ML)

Assembles end-to-end scikit-learn feature transformation pipelines,
ensuring strict immutability, interaction feature generation, and leakage-free data splits.
"""

from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, RobustScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split

from .transformers import (
    InteractionFeaturesTransformer,
    LeakageFeatureDropper,
    LEAKAGE_COLUMNS_TO_DROP,
)
from ..data.loader import load_raw_dataset


# Standard telemetry numerical columns
BASE_NUMERICAL_COLS: List[str] = [
    "Capacity_kVA",
    "Temperature",
    "Load_Percentage",
    "Maintenance_Cost",
    "Installation_Year",
]

INTERACTION_NUMERICAL_COLS: List[str] = [
    "Load_Ratio",
    "Thermal_Stress",
    "Weather_Risk_Weight",
]

BASE_CATEGORICAL_COLS: List[str] = [
    "Asset_Type",
    "Manufacturer",
    "Weather_Condition",
    "Region",
    "City",
]

TARGET_COL: str = "Failure_Probability"


def get_feature_column_specs(
    include_health_score: bool = True,
    include_interaction_features: bool = True,
) -> Dict[str, List[str]]:
    """
    Returns column lists configured for numerical and categorical preprocessing pipelines.
    Allows toggling health score and interaction features to support zero-baseline benchmarking.
    """
    numerical = list(BASE_NUMERICAL_COLS)
    categorical = list(BASE_CATEGORICAL_COLS)

    if include_health_score:
        numerical.append("Health_Score")
        categorical.append("Failure_Risk")

    if include_interaction_features:
        numerical.extend(INTERACTION_NUMERICAL_COLS)

    return {
        "numerical": numerical,
        "categorical": categorical,
        "drop": list(LEAKAGE_COLUMNS_TO_DROP),
    }


def build_feature_pipeline(
    include_health_score: bool = True,
    include_interaction_features: bool = True,
    robust_scaling: bool = False,
) -> Pipeline:
    """
    Constructs a scikit-learn Pipeline with:
      1. InteractionFeaturesTransformer (domain interaction features)
      2. ColumnTransformer (imputation, numerical scaling, and one-hot encoding)
    
    Guarantees strict immutability during fitting and transformation.
    """
    col_specs = get_feature_column_specs(
        include_health_score=include_health_score,
        include_interaction_features=include_interaction_features,
    )

    scaler = RobustScaler() if robust_scaling else StandardScaler()

    numerical_subpipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", scaler),
        ]
    )

    categorical_subpipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numerical_subpipe, col_specs["numerical"]),
            ("cat", categorical_subpipe, col_specs["categorical"]),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )

    steps = []
    if include_interaction_features:
        steps.append(("interactions", InteractionFeaturesTransformer()))
    
    steps.append(("preprocessor", preprocessor))

    return Pipeline(steps=steps)


def prepare_training_data(
    file_path: Optional[str] = None,
    test_size: float = 0.2,
    random_state: int = 42,
    target_column: str = TARGET_COL,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Loads raw asset records, isolates pre-incident features from target,
    and performs a leakage-free train/test partition.
    """
    df, _ = load_raw_dataset(file_path=file_path, validate=False)

    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataset.")

    y = df[target_column].astype(float)
    X = df.drop(columns=[target_column])

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
    )

    return X_train, X_test, y_train, y_test
