"""
GridGuard AI - Features Package
Student 3: AI Engineer 1 (Tabular ML & Grid Diagnostics)
"""

from .transformers import (
    InteractionFeaturesTransformer,
    LeakageFeatureDropper,
    DEFAULT_WEATHER_WEIGHTS,
    LEAKAGE_COLUMNS_TO_DROP,
)
from .feature_builder import (
    build_feature_pipeline,
    prepare_training_data,
    get_feature_column_specs,
    BASE_NUMERICAL_COLS,
    INTERACTION_NUMERICAL_COLS,
    BASE_CATEGORICAL_COLS,
    TARGET_COL,
)

__all__ = [
    "InteractionFeaturesTransformer",
    "LeakageFeatureDropper",
    "DEFAULT_WEATHER_WEIGHTS",
    "LEAKAGE_COLUMNS_TO_DROP",
    "build_feature_pipeline",
    "prepare_training_data",
    "get_feature_column_specs",
    "BASE_NUMERICAL_COLS",
    "INTERACTION_NUMERICAL_COLS",
    "BASE_CATEGORICAL_COLS",
    "TARGET_COL",
]
