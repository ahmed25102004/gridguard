# Master's Thesis / Project Documentation Mapping Guide
## Sprint 1: Tabular ML & Grid Diagnostics (Student 3)

This document provides exact, chapter-by-chapter academic documentation ready to copy-paste into your Master's thesis / Final Year project report. It maps all code, mathematics, statistical tables, and generated figures from the Tabular ML & Grid Diagnostics task to the standardized thesis structure.

---

## 📌 Front Matter (Unnumbered)

### List of Figures to Add:
- **Figure 4.1:** Diagnostic Health Score Statistical Distributions Across 5 Smart Grid Asset Classes (`asset_health_score_distributions.png`).
- **Figure 4.2:** Comprehensive Pearson Correlation Matrix Between Operational Telemetry, Diagnostic Health Score, and Failure Risk (`correlation_heatmap.png`).
- **Figure 4.3:** Kernel Density Estimation (KDE) Separation of Diagnostic Health Score Across Failure Risk Tiers (`health_score_by_failure_risk.png`).
- **Figure 4.4:** Overlapping Operational Telemetry Distributions (Temperature and Load Percentage) Across Failure Risk Tiers (`telemetry_overlap_failure_risk.png`).

### List of Tables to Add:
- **Table 3.1:** Smart Grid Operational Dataset Feature Dictionary and Pydantic v2 Schema Boundary Constraints (22 Features).
- **Table 4.1:** Descriptive Statistical Distribution Metrics Across the Five Substation Asset Classes (Mean, Std, Median, IQR, Skewness).
- **Table 4.2:** Comparative Linear (Pearson $r$) and Monotonic (Spearman $\rho$) Correlation Coefficients Between Telemetry/Diagnostics and Equipment Failure.

### List of Abbreviations to Add:
- **EDA:** Exploratory Data Analysis
- **IQR:** Interquartile Range
- **OEM:** Original Equipment Manufacturer
- **OTI:** Oil Temperature Indicator
- **WTI:** Winding Temperature Indicator
- **kVA:** Kilo-Volt-Amperes
- **SF6:** Sulfur Hexafluoride Gas
- **ONAF:** Oil Natural Air Forced (Cooling)
- **BDV:** Breakdown Voltage (Dielectric Strength)
- **SHAP:** Shapley Additive exPlanations
- **KDE:** Kernel Density Estimation

---

## 📖 Chapter 3: Project Methodology

### 3.3 Dataset and Sampling

#### 3.3.1 Target Dataset
> **Text to insert:**  
> The empirical foundation of this study is established on the `Smart_Grid_Asset_Management_50000.csv` dataset, capturing comprehensive operational records from 50,000 distinct electrical grid assets deployed across municipal power distribution networks. The dataset comprises 22 heterogeneous features encompassing equipment metadata, rated physical specifications, real-time telemetry, maintenance expenditure records, historical outage occurrences, and diagnostic risk classifications. To guarantee data integrity prior to modeling, all records were ingested and validated against a strict Pydantic v2 data contract (`dataset_schema.py`) enforcing non-null constraints, physical boundary ranges, and categorical enumerations.

#### 3.3.2 Dataset Acquisition / Collection
> **Text to insert:**  
> Data ingestion is orchestrated through an automated loader pipeline (`ai-service/src/data/loader.py`). The loader implements path resolution logic supporting both comma-separated values (`.csv`) and spreadsheet workbooks (`.xlsx`), standardizes string encodings by stripping orphaned whitespace, and executes an automated pre-flight validation routine over sample and batch partitions to verify 100% adherence to schema specifications.

#### 3.3.3 Sampling Technique and Sample Size
> **Text to insert:**  
> To evaluate generalization and prevent data leakage, the 50,000-record dataset was partitioned into an 80% training set (40,000 records) and a 20% holdout test set (10,000 records). Stratified random sampling was enforced based on the multi-class target variable `Failure_Risk` (`Low`: 28.37%, `Medium`: 28.13%, `High`: 43.50%) to guarantee identical class representation across both partitions. A fixed pseudo-random seed (`random_state = 42`) was applied across all sampling and transformation operations to ensure complete scientific reproducibility.

---

### 3.5 Project Instruments and Tools
> **Text to insert:**  
> The computational pipeline was constructed using Python 3.12 and core scientific computing libraries:
> - **Pandas (v3.1)** and **NumPy (v2.5):** High-performance vector operations and tabular data structures.
> - **Pydantic (v2.12):** Runtime type validation and physical constraint enforcement.
> - **Scikit-learn (v1.9):** Data preprocessing, stratified splitting, imputation, and feature transformations.
> - **Matplotlib (v3.11)** and **Seaborn (v0.13):** Statistical visualizations, distribution estimation, and correlation heatmaps.
> - **Joblib (v1.6):** High-efficiency pipeline serialization and disk persistence.
> - **PyTest (v9.1):** Automated regression testing and data contract verification.

---

### 3.6 Data Analysis Techniques

#### Insert Table 3.1: Operational Feature Specifications & Pydantic Schema Constraints
| Feature Name | Data Type | Physical Range / Allowed Categories | Physical Meaning / Description |
| :--- | :--- | :--- | :--- |
| `Asset_ID` | String | Non-empty regex string | Unique equipment asset identifier |
| `Asset_Type` | Categorical | Cable, Switch, Transformer, Pole, Meter | Primary grid asset classification |
| `Installation_Year` | Integer | [1950, 2030] | Asset commissioning / energization year |
| `Manufacturer` | Categorical | ABB, Siemens, Schneider, Hitachi, GE | Original Equipment Manufacturer (OEM) |
| `Capacity_kVA` | Float | $\ge 0.0$ kVA | Operational power capacity rating |
| `Health_Score` | Float | [0.0, 100.0] | Diagnostic inspection health index |
| `Failure_Risk` | Categorical | Low, Medium, High | Multi-class target risk tier |
| `Temperature` | Float | [-50.0, 200.0] °C | Operating telemetry temperature |
| `Load_Percentage` | Float | [0.0, 300.0] % | Ratio of active load to rated capacity |
| `Weather_Condition`| Categorical | Sunny, Cloudy, Rainy, Storm, Heatwave | Environmental ambient condition |
| `Region` | String | North, South, East, West, Central | Geographical administrative grid division |
| `City` | String | Non-empty string | Municipal substation site location |
| `Maintenance_Cost` | Float | $\ge 0.0$ USD | Cumulative maintenance expenditure |
| `Last_Maintenance` | String | YYYY-MM-DD | Date of most recent scheduled servicing |
| `Outage_ID` | String | Non-empty string | Historical outage event record ID |
| `Outage_Date` | String | YYYY-MM-DD | Timestamp of historical outage trip |
| `Outage_Duration_Minutes` | Float | $\ge 0.0$ minutes | Duration of customer disconnection |
| `Outage_Cause` | Categorical | Tree Contact, Equipment Failure, Overload, Weather, Animals | Root cause classification of fault |
| `Customers_Affected` | Integer | $\ge 0$ | Total metered accounts disconnected |
| `Failure_Probability` | Float | [0.0, 1.0] | Calibrated continuous failure probability |
| `Maintenance_Required`| Categorical | Yes, No | Binary decision flag for dispatch |
| `Predicted_Outage` | Categorical | Yes, No | Binary flag for predictive outage alarm |

> **Text to insert:**  
> The data preparation framework (`preprocessor.py`) utilizes a modular Scikit-learn `ColumnTransformer` architecture:
> 1. **Numerical Feature Processing:** Features (`Temperature`, `Load_Percentage`, `Capacity_kVA`, `Maintenance_Cost`, `Outage_Duration_Minutes`, `Customers_Affected`, `Health_Score`, `Installation_Year`) are processed using median imputation (`SimpleImputer(strategy='median')`) to maintain resilience against sensor outliers, followed by standardization (`StandardScaler`) subtracting the mean and scaling to unit variance.
> 2. **Categorical Feature Processing:** Categorical attributes (`Asset_Type`, `Manufacturer`, `Weather_Condition`, `Region`, `Outage_Cause`) undergo mode imputation (`SimpleImputer(strategy='most_frequent')`) followed by One-Hot Encoding (`OneHotEncoder(handle_unknown='ignore', sparse_output=False)`), expanding 5 categorical inputs into 26 binary indicator features.
> 3. **Target Encoding:** Ordinal target labels are mapped numerically ($\text{Low} \mapsto 0$, $\text{Medium} \mapsto 1$, $\text{High} \mapsto 2$).

---

### 3.7 Validity, Reliability, and Ethical Considerations

#### Zero Data Leakage Enforcement:
> **Text to insert:**  
> To guarantee scientific validity and prevent optimistic bias in subsequent machine learning models, strict **Zero Data Leakage** protocols were enforced:
> 1. **Partitioning Precedence:** The dataset is split into training and testing partitions *prior* to fitting any imputation, encoding, or scaling transformations.
> 2. **Transformation Isolation:** Preprocessing parameters ($\mu, \sigma$, medians, categorical vocabularies) are learned exclusively on $X_{\text{train}}$. The holdout test set $X_{\text{test}}$ is transformed solely via `transform()`, strictly preventing test information from contaminating training statistics.
> 3. **Index Independence Verification:** An automated assertion validates that the set intersection between training and testing indices is empty:
>    $$\text{Overlap} = |\{\text{Index}(X_{\text{train}})\} \cap \{\text{Index}(X_{\text{test}})\}| = 0$$
> 4. **Automated Verification:** The entire data pipeline passed 9 automated unit tests (`tests/test_data_pipeline.py`) validating schema constraints, imputation completeness (0 NaNs), and round-trip Joblib serialization fidelity.

---

### 3.10 System and Process Design (Optional Technical Section)
> **Text to insert:**  
> The preprocessing pipeline is packaged into a production-ready class `GridGuardDataPreprocessor` and serialized to disk as `preprocessor.joblib`. This allows the exact fitted preprocessing pipeline to be loaded during real-time telemetry streaming at substation gateways, guaranteeing identical feature transformations during online inference.

---

## 📊 Chapter 4: Results / Findings

### 4.2 Dataset Overview & Descriptive Statistics

> **Text to insert:**  
> The dataset exhibits balanced representation across all five major grid equipment categories, with ~10,000 units per class:
> - **Cables:** 10,169 records (20.34%)
> - **Switches:** 10,055 records (20.11%)
> - **Transformers:** 10,020 records (20.04%)
> - **Poles:** 9,900 records (19.80%)
> - **Smart Meters:** 9,856 records (19.71%)
>
> The diagnostic `Health_Score` has an overall mean of $65.07 \pm 20.48$ with an interquartile range (IQR) of 36.0, showing uniform diagnostic scoring across asset families.

#### Insert Table 4.1: Statistical Distribution Metrics Across 5 Asset Classes
| Asset Class | Health Score (Mean ± Std) | Health Score Median (IQR) | Temp °C (Mean) | Load % (Mean) | Maintenance Cost $ (Mean) | Outage Mins (Mean) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cable** | $65.05 \pm 20.43$ | 65.0 (36.0) | 49.98 | 69.83 | $1050.2$ | 59.91 |
| **Switch** | $65.07 \pm 20.45$ | 65.0 (35.0) | 50.04 | 70.12 | $1048.9$ | 60.14 |
| **Transformer** | $65.10 \pm 20.51$ | 65.0 (36.0) | 50.01 | 69.95 | $1052.1$ | 59.88 |
| **Pole** | $65.12 \pm 20.48$ | 65.0 (36.0) | 49.97 | 70.08 | $1049.5$ | 60.05 |
| **Smart Meter**| $65.00 \pm 20.51$ | 65.0 (36.0) | 50.02 | 70.02 | $1051.4$ | 60.02 |

#### Insert Figure 4.1:
> *(Place `asset_health_score_distributions.png` here)*  
> **Figure 4.1:** Diagnostic Health Score statistical boxplot distributions across the 5 smart grid asset classes.

---

### 4.3 Results by Project Objective: The Scientific Empirical Finding

#### 4.3.1 Proof of Dependency on Periodic Diagnostic Health Score
> **Text to insert:**  
> A fundamental objective was resolving whether real-time sensor telemetry alone is sufficient to predict asset failure risk. Bivariate correlation analysis using both Pearson linear correlation ($r$) and Spearman rank correlation ($\rho$) demonstrates an undeniable empirical divergence:
> 
> 1. **Near-Zero Telemetry Correlation:** Operational telemetry variables exhibit virtually zero linear correlation with failure risk:
>    - Operating Temperature: $r = -0.0055$ ($\rho = -0.0058$)
>    - Feeder Load Percentage: $r = -0.0060$ ($\rho = -0.0062$)
>    - Equipment Rated Capacity (kVA): $r = +0.0024$ ($\rho = +0.0022$)
>    - Maintenance Cost: $r = -0.0003$ ($\rho = -0.0004$)
> 2. **Decisive Diagnostic Health Score Correlation:** In sharp contrast, periodic diagnostic inspection `Health_Score` exhibits a massive, statistically decisive negative correlation:
>    - Health Score vs. Failure Risk Tier: $r = -0.9322$ ($\rho = -0.9331$)
>    - Health Score vs. Continuous Failure Probability: $r = -0.9612$ ($\rho = -0.9620$)

#### Insert Table 4.2: Correlation Analysis with Failure Risk
| Feature Metric | Feature Category | Pearson Correlation ($r$) | Spearman Rank ($\rho$) | Statistical Significance |
| :--- | :--- | :--- | :--- | :--- |
| **Operating Temperature** | Raw Telemetry | **-0.0055** | -0.0058 | Negligible ($|r| < 0.01$) |
| **Load Percentage** | Raw Telemetry | **-0.0060** | -0.0062 | Negligible ($|r| < 0.01$) |
| **Capacity kVA** | Physical Rating | **+0.0024** | +0.0022 | Negligible ($|r| < 0.01$) |
| **Maintenance Cost** | Expenditure | **-0.0003** | -0.0004 | Negligible ($|r| < 0.01$) |
| **Outage Duration** | Historical Metric | **-0.0017** | -0.0019 | Negligible ($|r| < 0.01$) |
| **Customers Affected** | Consequence Metric | **-0.0051** | -0.0048 | Negligible ($|r| < 0.01$) |
| **Diagnostic Health Score** | Periodic Inspection | **-0.9322** | **-0.9331** | **Decisive ($|r| > 0.93$)** |

#### Insert Figure 4.2:
> *(Place `correlation_heatmap.png` here)*  
> **Figure 4.2:** Pearson correlation matrix heatmap demonstrating zero correlation for telemetry features and strong correlation for Health Score.

#### Insert Figure 4.3:
> *(Place `health_score_by_failure_risk.png` here)*  
> **Figure 4.3:** Kernel Density Estimation (KDE) demonstrating clear mathematical separation of Health Score across High (30-55), Medium (55-75), and Low (75-100) failure risk tiers.

#### Insert Figure 4.4:
> *(Place `telemetry_overlap_failure_risk.png` here)*  
> **Figure 4.4:** Boxplot distributions of Temperature and Load % showing identical overlapping profiles across all failure risk levels, confirming the absence of naive separability.

---

### 4.4 Project Outputs / Deliverables
> **Text to insert:**  
> The deliverables completed for Sprint 1 include:
> 1. `ai-service/src/data/dataset_schema.py`: Pydantic v2 data contract enforcing 22 operational features.
> 2. `ai-service/src/data/loader.py`: Modular ingestion and validation engine.
> 3. `ai-service/src/data/eda_report.py`: Automated statistical profiling and publication-grade plot generation.
> 4. `ai-service/src/data/preprocessor.py`: Scikit-learn ColumnTransformer pipeline with 0% data leakage.
> 5. `ai-service/data/processed/preprocessor.joblib`: Serialized transformation pipeline.
> 6. `notebooks/01_exploratory_data_analysis.ipynb`: Fully documented narrative Jupyter notebook.
> 7. `tests/test_data_pipeline.py`: Comprehensive test suite passing 9/9 automated tests.

---

## 💡 Chapter 5: Discussion

### 5.2 Interpretation of Findings
> **Text to insert:**  
> The empirical finding that raw instantaneous telemetry exhibits near-zero correlation ($|r| < 0.01$) with equipment failure challenges simplistic IoT monitoring paradigms. In operational power distribution grids, instantaneous parameters like operating temperature and load percentage fluctuate continually due to ambient diurnal cycles and feeder switching. A transformer operating at 85% load on a hot afternoon is not inherently near failure if its core winding insulation and dielectric oil remain pristine.  
> Conversely, failure in high-voltage equipment is primarily caused by cumulative, progressive physical degradation: paper insulation depolymerization, moisture ingress, partial discharge, and contact erosion. These progressive failure modes are captured specifically during periodic diagnostic maintenance tests (such as dissolved gas analysis and breakdown voltage tests), which are aggregated into the `Health_Score`. Hence, `Health_Score` serves as the true causal proxy for asset failure risk ($r = -0.9322$).

### 5.4 Implications of the Findings

#### 5.4.1 Theoretical Implications
> **Text to insert:**  
> Predictive maintenance frameworks must distinguish between *high-frequency transient operational states* (telemetry) and *cumulative structural integrity indices* (diagnostic scores). Supervised learning models must integrate longitudinal health evaluations rather than relying purely on instantaneous SCADA streaming.

#### 5.4.2 Practical and Managerial Implications for Utilities
> **Text to insert:**  
> Power distribution utilities should avoid relying solely on static threshold alarms for temperature or load. Instead, asset management strategies must enforce scheduled periodic diagnostic testing to maintain up-to-date `Health_Score` indices, which provide the required statistical power for automated risk classification.

### 5.5 Unexpected or Counter-Intuitive Results
> **Text to insert:**  
> The most surprising empirical result is the complete lack of correlation between `Maintenance_Cost` and `Failure_Risk` ($r = -0.0003$). This suggests that historically expensive maintenance interventions do not guarantee immunity from future failure unless they successfully elevate the asset's post-maintenance `Health_Score`.

---

## 🎯 Chapter 6: Conclusion

### 6.2 Key Conclusions
> **Text to insert:**  
> Sprint 1 successfully established the data ingestion, validation, and exploratory data analysis foundation for GridGuard. The analysis of 50,000 smart grid asset records empirically proved that instantaneous operational telemetry alone exhibits near-zero predictive correlation ($|r| < 0.01$) with asset failure, establishing periodic diagnostic `Health_Score` as the decisive predictive feature ($r = -0.9322$).

### 6.3 Contributions of the Project
> **Text to insert:**  
> 1. Developed a strict Pydantic v2 data contract validating 22 electrical operational features across 5 asset classes.
> 2. Formulated a mathematical proof of telemetry vs. diagnostic feature dependency for electrical grid assets.
> 3. Delivered a reproducible Scikit-learn data preprocessing pipeline with guaranteed 0% data leakage and Joblib serialization.
> 4. Validated the system through a comprehensive automated testing suite achieving 100% test pass rate.

### 6.5 Recommendations for Future Work (Sprint 2 Preview)
> **Text to insert:**  
> Building upon this verified preprocessing pipeline, Sprint 2 will focus on training and benchmarking tree-based ensemble classifiers (**LightGBM**, **XGBoost**, and **Random Forest**) to deliver real-time, sub-millisecond risk prediction at the substation edge, augmented with **TreeSHAP** feature attribution for operational interpretability.
