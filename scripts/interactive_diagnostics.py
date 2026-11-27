"""
GridGuard AI - Live Asset Failure Probability Interactive Simulator
Student 3: AI Engineer 1 (Tabular ML & Grid Diagnostics)
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure ai-service is in sys.path
sys.path.insert(0, os.path.abspath("ai-service"))
from src.models.baseline_regressors import load_model_artifacts

def run_diagnostic_demo():
    print("=" * 70)
    print("⚡ GRIDGUARD AI - LIVE ASSET FAILURE PREDICTION ENGINE")
    print("   Models Loaded: Ridge Regressor (R²=0.9228) & Random Forest (R²=0.9214)")
    print("=" * 70)

    artifacts = load_model_artifacts()
    ridge = artifacts["ridge_baseline"]
    rf = artifacts["rf_baseline"]

    scenarios = [
        {
            "name": "Scenario 1: Brand New 500kVA Transformer (Optimal Conditions)",
            "data": {
                "Asset_ID": "DEMO-001",
                "Asset_Type": "Transformer",
                "Installation_Year": 2023,
                "Manufacturer": "ABB",
                "Capacity_kVA": 500.0,
                "Health_Score": 96.0,
                "Failure_Risk": "Low",
                "Temperature": 38.0,
                "Load_Percentage": 55.0,
                "Weather_Condition": "Sunny",
                "Region": "North",
                "City": "Cairo",
                "Maintenance_Cost": 450.0,
                "Last_Maintenance": "2024-01-10",
                "Outage_ID": "NONE",
                "Outage_Date": "NONE",
                "Outage_Duration_Minutes": 0,
                "Outage_Cause": "None",
                "Customers_Affected": 0,
                "Maintenance_Required": "No",
                "Predicted_Outage": "No"
            }
        },
        {
            "name": "Scenario 2: Aging 50kVA Distribution Pole (Moderate Wear in Rain)",
            "data": {
                "Asset_ID": "DEMO-002",
                "Asset_Type": "Pole",
                "Installation_Year": 2008,
                "Manufacturer": "Siemens",
                "Capacity_kVA": 50.0,
                "Health_Score": 68.0,
                "Failure_Risk": "Medium",
                "Temperature": 52.0,
                "Load_Percentage": 78.0,
                "Weather_Condition": "Rainy",
                "Region": "Central",
                "City": "Giza",
                "Maintenance_Cost": 1850.0,
                "Last_Maintenance": "2023-06-15",
                "Outage_ID": "NONE",
                "Outage_Date": "NONE",
                "Outage_Duration_Minutes": 0,
                "Outage_Cause": "None",
                "Customers_Affected": 0,
                "Maintenance_Required": "No",
                "Predicted_Outage": "No"
            }
        },
        {
            "name": "Scenario 3: Overloaded 25kVA Switch in Severe Storm (CRITICAL ALARM)",
            "data": {
                "Asset_ID": "DEMO-003",
                "Asset_Type": "Switch",
                "Installation_Year": 1999,
                "Manufacturer": "Schneider",
                "Capacity_kVA": 25.0,
                "Health_Score": 32.0,
                "Failure_Risk": "High",
                "Temperature": 88.0,
                "Load_Percentage": 145.0,
                "Weather_Condition": "Storm",
                "Region": "East",
                "City": "Suez",
                "Maintenance_Cost": 4200.0,
                "Last_Maintenance": "2021-04-10",
                "Outage_ID": "NONE",
                "Outage_Date": "NONE",
                "Outage_Duration_Minutes": 0,
                "Outage_Cause": "None",
                "Customers_Affected": 0,
                "Maintenance_Required": "Yes",
                "Predicted_Outage": "Yes"
            }
        }
    ]

    for sc in scenarios:
        df = pd.DataFrame([sc["data"]])
        pred_ridge = float(ridge.predict(df)[0])
        pred_rf = float(rf.predict(df)[0])

        load_ratio = sc["data"]["Load_Percentage"] / sc["data"]["Capacity_kVA"]
        thermal_stress = sc["data"]["Temperature"] / 50.0

        print(f"\n🔹 {sc['name']}")
        print(f"   [Input Telemetry] Capacity: {sc['data']['Capacity_kVA']} kVA | Temp: {sc['data']['Temperature']}°C | Load: {sc['data']['Load_Percentage']}% | Weather: {sc['data']['Weather_Condition']}")
        print(f"   [Interaction Features] Load_Ratio: {load_ratio:.3f} | Thermal_Stress: {thermal_stress:.2f}x | Health_Score: {sc['data']['Health_Score']}%")
        print(f"   ➡️  Ridge Predicted Failure Probability:         {pred_ridge * 100:.2f}%")
        print(f"   ➡️  Random Forest Predicted Failure Probability: {pred_rf * 100:.2f}%")

        if pred_rf >= 0.70:
            status = "🚨 CRITICAL RISK - IMMEDIATE TRIP / DISPATCH REQUIRED"
        elif pred_rf >= 0.40:
            status = "⚠️  ELEVATED RISK - SCHEDULE OTI/WTI INSPECTION"
        else:
            status = "✅ NORMAL - OPTIMAL OPERATING STABILITY"
        print(f"   [Assessment] {status}")

    print("\n" + "=" * 70)
    print("Demo execution completed successfully!")

if __name__ == "__main__":
    run_diagnostic_demo()
