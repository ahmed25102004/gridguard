import os
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder

DEFAULT_PROCESSED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed"
RANDOM_SEED = 42

DEFAULT_NUMERIC_FEATURES = [
    "Temperature",
    "Load_Percentage",
    "Capacity_kVA",
    "Maintenance_Cost",
    "Outage_Duration_Minutes",
    "Customers_Affected",
    "Health_Score",
    "Installation_Year",
]

DEFAULT_CATEGORICAL_FEATURES = [
    "Asset_Type",
    "Manufacturer",
    "Weather_Condition",
    "Region",
    "Outage_Cause",
]

TARGET_COLUMN = "Failure_Risk"
TARGET_MAPPING = {"Low": 0, "Medium": 1, "High": 2}


class GridGuardDataPreprocessor:
    """
    Automated, reproducible data preprocessing pipeline for GridGuard Tabular ML.
    Enforces strict 0% data leakage by fitting transformers strictly on training splits.
    Supports Joblib serialization for seamless inference in production.
    """

    def __init__(
        self,
        numeric_features: Optional[List[str]] = None,
        categorical_features: Optional[List[str]] = None,
        target_column: str = TARGET_COLUMN,
        random_state: int = RANDOM_SEED,
    ):
        self.numeric_features = numeric_features or DEFAULT_NUMERIC_FEATURES
        self.categorical_features = categorical_features or DEFAULT_CATEGORICAL_FEATURES
        self.target_column = target_column
        self.random_state = random_state
        self.pipeline: Optional[ColumnTransformer] = None
        self.feature_names_: List[str] = []
        self.target_mapping_ = TARGET_MAPPING
        self.is_fitted: bool = False

    def build_transformer(self) -> ColumnTransformer:
        """
        Construct Scikit-learn ColumnTransformer with median imputation and scaling for numericals,
        and most_frequent imputation and OneHotEncoding for categoricals.
        """
        numeric_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )

        categorical_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]
        )

        transformer = ColumnTransformer(
            transformers=[
                ("num", numeric_transformer, self.numeric_features),
                ("cat", categorical_transformer, self.categorical_features),
            ],
            remainder="drop",
        )
        return transformer

    def split_data(
        self,
        df: pd.DataFrame,
        test_size: float = 0.20,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Perform stratified train-test split with fixed random seed and verify 0% leakage.
        """
        # Ensure target column exists
        if self.target_column not in df.columns:
            raise KeyError(f"Target column '{self.target_column}' not found in DataFrame.")

        # Verify all feature columns exist
        missing_feats = [
            f for f in (self.numeric_features + self.categorical_features) if f not in df.columns
        ]
        if missing_feats:
            raise KeyError(f"Expected feature columns missing from DataFrame: {missing_feats}")

        # Features and Target
        X = df[self.numeric_features + self.categorical_features].copy()
        y = df[self.target_column].copy()

        # Map ordinal targets if applicable
        if y.dtype == object and set(y.unique()).issubset(set(self.target_mapping_.keys())):
            y = y.map(self.target_mapping_)

        # Stratified train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=self.random_state,
            stratify=y,
        )

        # Verification of 0% Data Leakage: Index intersection must be strictly 0
        overlap = set(X_train.index).intersection(set(X_test.index))
        if len(overlap) > 0:
            raise RuntimeError(f"Data leakage detected: {len(overlap)} samples overlap between train and test!")

        return X_train, X_test, y_train, y_test

    def fit(self, X_train: pd.DataFrame, y_train: Optional[pd.Series] = None) -> "GridGuardDataPreprocessor":
        """
        Fit preprocessing pipeline exclusively on training data to prevent any data leakage.
        """
        self.pipeline = self.build_transformer()
        self.pipeline.fit(X_train)

        # Extract generated feature names
        try:
            self.feature_names_ = list(self.pipeline.get_feature_names_out())
        except Exception:
            self.feature_names_ = [f"f_{i}" for i in range(self.transform(X_train).shape[1])]

        self.is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Transform features using the fitted pipeline.
        """
        if not self.is_fitted or self.pipeline is None:
            raise RuntimeError("Preprocessor must be fitted before transforming data.")
        return self.pipeline.transform(X)

    def fit_transform(self, X_train: pd.DataFrame, y_train: Optional[pd.Series] = None) -> np.ndarray:
        """
        Fit on training features and return transformed array.
        """
        return self.fit(X_train, y_train).transform(X_train)

    def save(self, filepath: Optional[str] = None) -> str:
        """
        Serialize the fitted preprocessor pipeline to disk using joblib.
        """
        if not self.is_fitted:
            raise RuntimeError("Cannot save unfitted preprocessor.")

        save_path = Path(filepath) if filepath else DEFAULT_PROCESSED_DIR / "preprocessor.joblib"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, save_path)
        return str(save_path.resolve())

    @classmethod
    def load(cls, filepath: Optional[str] = None) -> "GridGuardDataPreprocessor":
        """
        Load a serialized GridGuardDataPreprocessor pipeline from disk.
        """
        load_path = Path(filepath) if filepath else DEFAULT_PROCESSED_DIR / "preprocessor.joblib"
        if not load_path.exists():
            raise FileNotFoundError(f"Serialized preprocessor not found at '{load_path}'.")
        instance = joblib.load(load_path)
        if not isinstance(instance, cls):
            raise TypeError(f"Loaded object is not an instance of {cls.__name__}.")
        return instance


def run_preprocessing_pipeline(
    df: pd.DataFrame,
    output_dir: Optional[str] = None,
    test_size: float = 0.20,
) -> Dict[str, Any]:
    """
    Execute full reproducible preprocessing workflow:
    1. Stratified train/test split.
    2. Fit preprocessor on train only (0% leakage).
    3. Transform train and test.
    4. Save preprocessor.joblib and processed datasets.
    """
    out_dir = Path(output_dir) if output_dir else DEFAULT_PROCESSED_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    preprocessor = GridGuardDataPreprocessor()
    X_train, X_test, y_train, y_test = preprocessor.split_data(df, test_size=test_size)

    # Fit exclusively on X_train (Zero Data Leakage)
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)

    # Save fitted preprocessor
    joblib_path = preprocessor.save(str(out_dir / "preprocessor.joblib"))

    # Convert to DataFrames and save processed files
    feature_cols = preprocessor.feature_names_
    df_train_proc = pd.DataFrame(X_train_processed, columns=feature_cols)
    df_train_proc["target"] = y_train.values

    df_test_proc = pd.DataFrame(X_test_processed, columns=feature_cols)
    df_test_proc["target"] = y_test.values

    train_file = out_dir / "train_processed.parquet"
    test_file = out_dir / "test_processed.parquet"
    train_csv = out_dir / "train_processed.csv"
    test_csv = out_dir / "test_processed.csv"

    # Save as both Parquet (if pyarrow available) and CSV
    try:
        df_train_proc.to_parquet(train_file, index=False)
        df_test_proc.to_parquet(test_file, index=False)
        saved_train = str(train_file)
        saved_test = str(test_file)
    except Exception:
        df_train_proc.to_csv(train_csv, index=False)
        df_test_proc.to_csv(test_csv, index=False)
        saved_train = str(train_csv)
        saved_test = str(test_csv)

    return {
        "status": "success",
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "feature_count_original": len(preprocessor.numeric_features) + len(preprocessor.categorical_features),
        "feature_count_processed": len(feature_cols),
        "data_leakage_overlap_count": len(set(X_train.index).intersection(set(X_test.index))),
        "preprocessor_joblib_path": joblib_path,
        "train_processed_path": saved_train,
        "test_processed_path": saved_test,
        "feature_names": feature_cols,
    }
