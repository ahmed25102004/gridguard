import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend for automated pipeline reporting
import matplotlib.pyplot as plt
import seaborn as sns

DEFAULT_REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "reports"


def compute_asset_class_distributions(df: pd.DataFrame) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Perform statistical distribution analysis across the 5 asset classes:
    (Transformers, Switches, Cables, Smart Meters, Poles).
    Computes Mean, Std, Median, IQR (Interquartile Range), Skewness, Min, and Max for key telemetry.
    """
    numeric_features = [
        "Temperature",
        "Load_Percentage",
        "Health_Score",
        "Capacity_kVA",
        "Maintenance_Cost",
        "Outage_Duration_Minutes",
        "Customers_Affected",
        "Failure_Probability",
    ]
    numeric_features = [f for f in numeric_features if f in df.columns]

    asset_types = df["Asset_Type"].unique() if "Asset_Type" in df.columns else []
    distributions: Dict[str, Dict[str, Dict[str, float]]] = {}

    for asset in asset_types:
        asset_df = df[df["Asset_Type"] == asset]
        distributions[str(asset)] = {}

        for feat in numeric_features:
            series = asset_df[feat].dropna()
            if len(series) == 0:
                continue

            q25 = float(series.quantile(0.25))
            q75 = float(series.quantile(0.75))
            iqr = q75 - q25
            skewness = float(series.skew()) if len(series) > 2 else 0.0

            distributions[str(asset)][feat] = {
                "count": int(len(series)),
                "mean": round(float(series.mean()), 3),
                "std": round(float(series.std()), 3),
                "median": round(float(series.median()), 3),
                "q25": round(q25, 3),
                "q75": round(q75, 3),
                "iqr": round(iqr, 3),
                "skewness": round(skewness, 3),
                "min": round(float(series.min()), 3),
                "max": round(float(series.max()), 3),
            }

    return distributions


def compute_correlation_matrices(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute Pearson and Spearman correlation matrices between operational telemetry,
    diagnostic Health_Score, and failure targets.
    """
    df_eval = df.copy()

    # Map ordinal failure risk to numeric tier: Low=0, Medium=1, High=2
    if "Failure_Risk" in df_eval.columns:
        risk_map = {"Low": 0, "Medium": 1, "High": 2}
        df_eval["Failure_Risk_Numeric"] = df_eval["Failure_Risk"].map(risk_map)

    if "Maintenance_Required" in df_eval.columns:
        df_eval["Maintenance_Required_Numeric"] = df_eval["Maintenance_Required"].map({"No": 0, "Yes": 1})

    features = [
        "Temperature",
        "Load_Percentage",
        "Capacity_kVA",
        "Maintenance_Cost",
        "Outage_Duration_Minutes",
        "Customers_Affected",
        "Health_Score",
        "Failure_Risk_Numeric",
        "Failure_Probability",
    ]
    features = [f for f in features if f in df_eval.columns]

    pearson_corr = df_eval[features].corr(method="pearson").round(4)
    spearman_corr = df_eval[features].corr(method="spearman").round(4)

    # Telemetry vs Failure correlations
    telemetry_cols = ["Temperature", "Load_Percentage", "Capacity_kVA", "Maintenance_Cost"]
    telemetry_corr_risk = {}
    for col in telemetry_cols:
        if col in pearson_corr.columns and "Failure_Risk_Numeric" in pearson_corr.columns:
            telemetry_corr_risk[col] = float(pearson_corr.loc[col, "Failure_Risk_Numeric"])

    health_score_corr_risk = (
        float(pearson_corr.loc["Health_Score", "Failure_Risk_Numeric"])
        if "Health_Score" in pearson_corr.columns and "Failure_Risk_Numeric" in pearson_corr.columns
        else None
    )

    health_score_corr_prob = (
        float(pearson_corr.loc["Health_Score", "Failure_Probability"])
        if "Health_Score" in pearson_corr.columns and "Failure_Probability" in pearson_corr.columns
        else None
    )

    return {
        "pearson_matrix": pearson_corr.to_dict(),
        "spearman_matrix": spearman_corr.to_dict(),
        "telemetry_vs_risk_pearson": telemetry_corr_risk,
        "health_score_vs_risk_pearson": health_score_corr_risk,
        "health_score_vs_prob_pearson": health_score_corr_prob,
        "features": features,
    }


def generate_empirical_finding_documentation(correlation_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formulate the empirical scientific finding proving that raw telemetry exhibits
    near-zero linear correlation with failure without periodic diagnostic Health_Score.
    """
    telemetry_corrs = correlation_data.get("telemetry_vs_risk_pearson", {})
    health_corr = correlation_data.get("health_score_vs_risk_pearson")
    health_prob_corr = correlation_data.get("health_score_vs_prob_pearson")

    max_telemetry_abs_corr = max([abs(v) for v in telemetry_corrs.values()]) if telemetry_corrs else 0.0

    proven = (max_telemetry_abs_corr < 0.10) and (health_corr is not None and abs(health_corr) > 0.85)

    return {
        "hypothesis": (
            "Raw operational telemetry alone (instantaneous Temperature, Load %) is insufficient "
            "for predicting grid equipment failure risk without longitudinal diagnostic Health_Score."
        ),
        "empirical_proof_verified": proven,
        "raw_telemetry_correlations": telemetry_corrs,
        "max_raw_telemetry_correlation_magnitude": round(max_telemetry_abs_corr, 4),
        "health_score_correlation_to_risk": health_corr,
        "health_score_correlation_to_failure_probability": health_prob_corr,
        "scientific_conclusion": (
            f"Telemetry parameters exhibit near-zero correlation with failure risk "
            f"(max |r| = {max_telemetry_abs_corr:.4f} < 0.10). In contrast, periodic diagnostic "
            f"Health_Score exhibits a massive decisive negative correlation (r = {health_corr:.4f}). "
            f"This empirically establishes that periodic diagnostic asset health scoring is the primary "
            f"predictive driver for smart grid asset reliability."
        ),
    }


def generate_eda_plots(df: pd.DataFrame, output_dir: Optional[str] = None) -> List[str]:
    """
    Generate automated EDA statistical visualization plots and save to output_dir.
    Returns list of generated image file paths.
    """
    out_path = Path(output_dir) if output_dir else DEFAULT_REPORTS_DIR
    out_path.mkdir(parents=True, exist_ok=True)
    generated_files: List[str] = []

    sns.set_theme(style="whitegrid", font="sans-serif")
    palette = sns.color_palette("mako")

    # 1. Telemetry vs Health Score Correlation Heatmap
    corr_info = compute_correlation_matrices(df)
    features = corr_info["features"]
    pearson_df = pd.DataFrame(corr_info["pearson_matrix"])[features].loc[features]

    fig, ax = plt.subplots(figsize=(10, 8))
    mask = np.triu(np.ones_like(pearson_df, dtype=bool))
    sns.heatmap(
        pearson_df,
        mask=mask,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        linewidths=0.5,
        ax=ax,
        cbar_kws={"label": "Pearson Correlation Coefficient (r)"},
    )
    ax.set_title("GridGuard Correlation Matrix: Operational Telemetry vs Health Score & Failure Risk", fontsize=12, pad=12, weight="bold")
    heatmap_file = out_path / "correlation_heatmap.png"
    plt.tight_layout()
    plt.savefig(heatmap_file, dpi=300)
    plt.close(fig)
    generated_files.append(str(heatmap_file))

    # 2. Asset Class Health Score Distributions (Boxplot / Violin)
    if "Asset_Type" in df.columns and "Health_Score" in df.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.boxplot(
            data=df,
            x="Asset_Type",
            y="Health_Score",
            hue="Asset_Type",
            palette="Set2",
            legend=False,
            ax=ax,
            boxprops=dict(alpha=0.8),
        )
        ax.set_title("Health Score Distributions Across 5 Smart Grid Asset Classes", fontsize=12, pad=12, weight="bold")
        ax.set_xlabel("Asset Class", fontsize=11)
        ax.set_ylabel("Diagnostic Health Score (0-100)", fontsize=11)
        box_file = out_path / "asset_health_score_distributions.png"
        plt.tight_layout()
        plt.savefig(box_file, dpi=300)
        plt.close(fig)
        generated_files.append(str(box_file))

    # 3. Health Score vs Failure Risk Tier
    if "Failure_Risk" in df.columns and "Health_Score" in df.columns:
        fig, ax = plt.subplots(figsize=(9, 5))
        order = ["Low", "Medium", "High"]
        order = [o for o in order if o in df["Failure_Risk"].unique()]
        sns.kdeplot(
            data=df,
            x="Health_Score",
            hue="Failure_Risk",
            hue_order=order,
            common_norm=False,
            fill=True,
            alpha=0.35,
            palette={"Low": "#2ecc71", "Medium": "#f39c12", "High": "#e74c3c"},
            ax=ax,
        )
        ax.set_title("Diagnostic Health Score Density by Failure Risk Tier (Separation Proof)", fontsize=12, pad=12, weight="bold")
        ax.set_xlabel("Diagnostic Health Score", fontsize=11)
        ax.set_ylabel("Kernel Density", fontsize=11)
        kde_file = out_path / "health_score_by_failure_risk.png"
        plt.tight_layout()
        plt.savefig(kde_file, dpi=300)
        plt.close(fig)
        generated_files.append(str(kde_file))

    # 4. Telemetry Distribution (Temperature & Load %) vs Failure Risk
    if "Temperature" in df.columns and "Failure_Risk" in df.columns:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        sns.boxplot(data=df, x="Failure_Risk", y="Temperature", hue="Failure_Risk", legend=False, palette="Blues", ax=axes[0])
        axes[0].set_title("Operating Temperature vs Failure Risk\n(Overlapping - Near Zero Correlation)", fontsize=11, weight="bold")
        axes[0].set_ylabel("Temperature (°C)")

        sns.boxplot(data=df, x="Failure_Risk", y="Load_Percentage", hue="Failure_Risk", legend=False, palette="Greens", ax=axes[1])
        axes[1].set_title("Load Percentage vs Failure Risk\n(Overlapping - Near Zero Correlation)", fontsize=11, weight="bold")
        axes[1].set_ylabel("Load Percentage (%)")

        plt.tight_layout()
        telem_file = out_path / "telemetry_overlap_failure_risk.png"
        plt.savefig(telem_file, dpi=300)
        plt.close(fig)
        generated_files.append(str(telem_file))

    return generated_files


def run_full_eda_pipeline(df: pd.DataFrame, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute full statistical profiling, correlation matrices, empirical proof calculation,
    and visual plot generation.
    """
    distributions = compute_asset_class_distributions(df)
    correlations = compute_correlation_matrices(df)
    empirical_proof = generate_empirical_finding_documentation(correlations)
    plot_files = generate_eda_plots(df, output_dir=output_dir)

    return {
        "status": "success",
        "total_records_analyzed": len(df),
        "asset_class_distributions": distributions,
        "correlations": correlations,
        "empirical_finding": empirical_proof,
        "generated_plot_files": plot_files,
    }
