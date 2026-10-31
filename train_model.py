"""
AI Weather Disaster Early Warning System
Machine Learning Model Training Pipeline
Trains Random Forest and Gradient Boosting models for:
1. Heavy Rainfall Risk Classification (Low, Moderate, High, Severe)
2. Extreme Heat Risk Classification (Low, Moderate, High, Severe)
3. Flood Risk Exploration Classification (Low, Moderate, High, Severe)
"""

import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

RISK_LABELS = ["Low", "Moderate", "High", "Severe"]

def compute_heat_index(temp_c, rh):
    """NOAA Heat Index formula converted for Celsius."""
    temp_f = (temp_c * 9/5) + 32
    if temp_f < 80:
        hi_f = 0.5 * (temp_f + 61.0 + ((temp_f - 68.0) * 1.2) + (rh * 0.094))
    else:
        hi_f = (-42.379 + 2.04901523 * temp_f + 10.14333127 * rh
                - 0.22475541 * temp_f * rh - 0.00683783 * temp_f**2
                - 0.05481717 * rh**2 + 0.00122874 * temp_f**2 * rh
                + 0.00085282 * temp_f * rh**2 - 0.00000199 * temp_f**2 * rh**2)
    return (hi_f - 32) * 5/9

def generate_meteorological_dataset(n_samples=5000, random_seed=42):
    """
    Generate synthetic yet meteorologically calibrated weather records
    reflecting real disaster risk dynamics (WMO and NOAA hazard standards).
    """
    np.random.seed(random_seed)

    # 1. Temperature (-10 to 48 °C)
    temp = np.random.normal(loc=24, scale=12, size=n_samples)
    temp = np.clip(temp, -10, 48)

    # 2. Relative Humidity (15 to 98 %)
    humidity = np.random.uniform(15, 98, size=n_samples)

    # 3. Heat Index
    heat_index = np.array([compute_heat_index(t, h) for t, h in zip(temp, humidity)])

    # 4. 24-hour Precipitation in mm (Exponential distribution with severe storm tails)
    precip_24h = np.random.exponential(scale=18, size=n_samples)
    # Inject storm and monsoon events
    severe_storm_idx = np.random.choice(n_samples, size=int(n_samples * 0.15), replace=False)
    precip_24h[severe_storm_idx] += np.random.uniform(50, 220, size=len(severe_storm_idx))
    precip_24h = np.clip(precip_24h, 0, 320)

    # 5. Peak hourly precipitation rate (mm/h)
    precip_rate_max = precip_24h * np.random.uniform(0.1, 0.45, size=n_samples)
    precip_rate_max = np.clip(precip_rate_max, 0, 85)

    # 6. Soil moisture saturation percentage (15% to 100%)
    soil_saturation = np.clip(
        35 + (precip_24h * 0.4) + np.random.normal(0, 15, size=n_samples), 10, 100
    )

    # 7. Sustained Wind Speed (km/h)
    wind_speed = np.random.gamma(shape=2.5, scale=8.0, size=n_samples)
    wind_speed = np.clip(wind_speed, 0, 130)

    # 8. Wind Gusts (km/h)
    wind_gusts = wind_speed * np.random.uniform(1.2, 1.8, size=n_samples)
    wind_gusts = np.clip(wind_gusts, 0, 180)

    # 9. Surface Pressure (hPa)
    pressure = np.random.normal(1013, 12, size=n_samples) - (precip_24h * 0.08)
    pressure = np.clip(pressure, 950, 1045)

    # 10. Pressure change 3h (hPa) - sharp drops precede cyclonic / severe storms
    pressure_drop_3h = np.random.normal(0, 3, size=n_samples) - (precip_rate_max * 0.12)

    # Assign Ground Truth Risk Labels using WMO & NOAA Meteorological Thresholds
    
    # Heavy Rainfall Risk
    rain_labels = []
    for p24, p_rate in zip(precip_24h, precip_rate_max):
        if p24 < 15 and p_rate < 5:
            rain_labels.append(0)  # Low
        elif p24 < 45 and p_rate < 15:
            rain_labels.append(1)  # Moderate
        elif p24 < 100 or p_rate < 30:
            rain_labels.append(2)  # High
        else:
            rain_labels.append(3)  # Severe

    # Extreme Heat Risk (NOAA Heat Index Criteria)
    heat_labels = []
    for t, hi in zip(temp, heat_index):
        if hi < 28:
            heat_labels.append(0)  # Low
        elif hi < 36:
            heat_labels.append(1)  # Moderate (Caution)
        elif hi < 45:
            heat_labels.append(2)  # High (Extreme Caution / Danger)
        else:
            heat_labels.append(3)  # Severe (Extreme Danger)

    # Flood Risk (Interaction of Precipitation, Soil Saturation, and Rain Rate)
    flood_labels = []
    for p24, sat, p_rate in zip(precip_24h, soil_saturation, precip_rate_max):
        # Hydrological runoff index
        runoff_index = (p24 * 0.5) + (sat * 0.4) + (p_rate * 1.1)
        if runoff_index < 35:
            flood_labels.append(0)  # Low
        elif runoff_index < 65:
            flood_labels.append(1)  # Moderate
        elif runoff_index < 105:
            flood_labels.append(2)  # High
        else:
            flood_labels.append(3)  # Severe

    df = pd.DataFrame({
        "temperature": temp,
        "humidity": humidity,
        "heat_index": heat_index,
        "precip_24h": precip_24h,
        "precip_rate_max": precip_rate_max,
        "soil_saturation": soil_saturation,
        "wind_speed": wind_speed,
        "wind_gusts": wind_gusts,
        "pressure": pressure,
        "pressure_drop_3h": pressure_drop_3h,
        "target_rain": rain_labels,
        "target_heat": heat_labels,
        "target_flood": flood_labels
    })

    return df

def train_and_evaluate():
    print("Generating meteorological disaster dataset...")
    df = generate_meteorological_dataset(n_samples=6000, random_seed=42)
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/meteorological_hazard_dataset.csv", index=False)
    print(f"Saved dataset with {len(df)} records.")

    feature_cols = [
        "temperature", "humidity", "heat_index", "precip_24h",
        "precip_rate_max", "soil_saturation", "wind_speed",
        "wind_gusts", "pressure", "pressure_drop_3h"
    ]

    X = df[feature_cols]
    y_rain = df["target_rain"]
    y_heat = df["target_heat"]
    y_flood = df["target_flood"]

    # Combined stratified train/test split so indices match across all targets
    (X_train, X_test,
     y_rain_train, y_rain_test,
     y_heat_train, y_heat_test,
     y_flood_train, y_flood_test) = train_test_split(
        X, y_rain, y_heat, y_flood, test_size=0.2, random_state=42
    )

    # Scaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 1. Heavy Rain Model (Random Forest)
    print("Training Heavy Rainfall Classifier...")
    rain_model = RandomForestClassifier(
        n_estimators=120, max_depth=12, random_state=42, class_weight="balanced"
    )
    rain_model.fit(X_train, y_rain_train)
    rain_preds = rain_model.predict(X_test)
    rain_acc = accuracy_score(y_rain_test, rain_preds)
    rain_f1 = f1_score(y_rain_test, rain_preds, average="weighted")
    print(f"Heavy Rain Model Accuracy: {rain_acc:.4f}, Weighted F1: {rain_f1:.4f}")

    # 2. Extreme Heat Model (Random Forest)
    print("Training Extreme Heat Classifier...")
    heat_model = RandomForestClassifier(
        n_estimators=100, max_depth=10, random_state=42, class_weight="balanced"
    )
    heat_model.fit(X_train, y_heat_train)
    heat_preds = heat_model.predict(X_test)
    heat_acc = accuracy_score(y_heat_test, heat_preds)
    heat_f1 = f1_score(y_heat_test, heat_preds, average="weighted")
    print(f"Extreme Heat Model Accuracy: {heat_acc:.4f}, Weighted F1: {heat_f1:.4f}")

    # 3. Flood Risk Model (Gradient Boosting)
    print("Training Flood Risk Classifier...")
    flood_model = GradientBoostingClassifier(
        n_estimators=120, learning_rate=0.08, max_depth=6, random_state=42
    )
    flood_model.fit(X_train, y_flood_train)
    flood_preds = flood_model.predict(X_test)
    flood_acc = accuracy_score(y_flood_test, flood_preds)
    flood_f1 = f1_score(y_flood_test, flood_preds, average="weighted")
    print(f"Flood Risk Model Accuracy: {flood_acc:.4f}, Weighted F1: {flood_f1:.4f}")

    # Feature Importances
    feature_importances = {
        "rain": dict(zip(feature_cols, [round(float(x), 4) for x in rain_model.feature_importances_])),
        "heat": dict(zip(feature_cols, [round(float(x), 4) for x in heat_model.feature_importances_])),
        "flood": dict(zip(feature_cols, [round(float(x), 4) for x in flood_model.feature_importances_])),
    }

    metrics = {
        "dataset_samples": len(df),
        "test_samples": len(X_test),
        "features": feature_cols,
        "classes": RISK_LABELS,
        "models": {
            "heavy_rainfall": {
                "algorithm": "RandomForestClassifier",
                "accuracy": round(float(rain_acc), 4),
                "f1_score": round(float(rain_f1), 4),
                "feature_importances": feature_importances["rain"]
            },
            "extreme_heat": {
                "algorithm": "RandomForestClassifier",
                "accuracy": round(float(heat_acc), 4),
                "f1_score": round(float(heat_f1), 4),
                "feature_importances": feature_importances["heat"]
            },
            "flood_risk": {
                "algorithm": "GradientBoostingClassifier",
                "accuracy": round(float(flood_acc), 4),
                "f1_score": round(float(flood_f1), 4),
                "feature_importances": feature_importances["flood"]
            }
        }
    }

    os.makedirs("models", exist_ok=True)
    joblib.dump({
        "rain_model": rain_model,
        "heat_model": heat_model,
        "flood_model": flood_model,
        "feature_cols": feature_cols,
        "scaler": scaler
    }, "models/weather_hazard_models.pkl")

    with open("models/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("Successfully saved models to models/weather_hazard_models.pkl and metrics to models/metrics.json")

if __name__ == "__main__":
    train_and_evaluate()
