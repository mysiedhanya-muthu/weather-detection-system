"""
AI Risk Assessment and Machine Learning Inference Engine.
Loads trained models (RandomForest and GradientBoosting) to evaluate:
- Heavy Rainfall Risk
- Extreme Heat Risk
- Flood Risk Exploration
- Composite Disaster Threat Score (0-100)
- AI Feature Explainability and Persona-specific Safety Guidance.
"""

import os
import joblib
import json
import numpy as np
from typing import Dict, Any, List

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "weather_hazard_models.pkl")
METRICS_PATH = os.path.join(os.path.dirname(__file__), "models", "metrics.json")
RISK_LEVELS = ["Low", "Moderate", "High", "Severe"]

def compute_heat_index(temp_c: float, rh: float) -> float:
    temp_f = (temp_c * 9/5) + 32
    if temp_f < 80:
        hi_f = 0.5 * (temp_f + 61.0 + ((temp_f - 68.0) * 1.2) + (rh * 0.094))
    else:
        hi_f = (-42.379 + 2.04901523 * temp_f + 10.14333127 * rh
                - 0.22475541 * temp_f * rh - 0.00683783 * temp_f**2
                - 0.05481717 * rh**2 + 0.00122874 * temp_f**2 * rh
                + 0.00085282 * temp_f * rh**2 - 0.00000199 * temp_f**2 * rh**2)
    return (hi_f - 32) * 5/9

class DisasterRiskEngine:
    def __init__(self):
        self.models_loaded = False
        self.rain_model = None
        self.heat_model = None
        self.flood_model = None
        self.feature_cols = []
        self.metrics = {}
        self._load_artifacts()

    def _load_artifacts(self):
        try:
            if os.path.exists(MODEL_PATH):
                bundle = joblib.load(MODEL_PATH)
                self.rain_model = bundle.get("rain_model")
                self.heat_model = bundle.get("heat_model")
                self.flood_model = bundle.get("flood_model")
                self.feature_cols = bundle.get("feature_cols", [])
                self.models_loaded = True
            
            if os.path.exists(METRICS_PATH):
                with open(METRICS_PATH, "r") as f:
                    self.metrics = json.load(f)
        except Exception as e:
            print(f"Error loading ML models: {e}. Fallback rules will be activated.")
            self.models_loaded = False

    def predict_risk(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features, run ML models, compute composite score,
        generate transparent feature attribution and safety guidance.
        """
        temp = float(weather_data.get("temperature", 22.0))
        humidity = float(weather_data.get("humidity", 50.0))
        precip_24h = float(weather_data.get("precipitation", 0.0))
        wind_speed = float(weather_data.get("wind_speed", 10.0))
        wind_gusts = float(weather_data.get("wind_gusts", wind_speed * 1.3))
        pressure = float(weather_data.get("pressure", 1013.0))
        pressure_drop_3h = float(weather_data.get("pressure_drop_3h", 0.0))

        heat_index = compute_heat_index(temp, humidity)
        precip_rate_max = precip_24h * 0.28
        soil_saturation = min(100.0, max(15.0, 30.0 + (precip_24h * 0.5)))

        features = [
            temp, humidity, heat_index, precip_24h,
            precip_rate_max, soil_saturation, wind_speed,
            wind_gusts, pressure, pressure_drop_3h
        ]

        is_fallback = False

        if self.models_loaded:
            try:
                import pandas as pd
                X = pd.DataFrame([features], columns=self.feature_cols)
                
                # Predictions & probabilities
                rain_class_idx = int(self.rain_model.predict(X)[0])
                rain_proba = self.rain_model.predict_proba(X)[0]
                rain_conf = float(np.max(rain_proba))

                heat_class_idx = int(self.heat_model.predict(X)[0])
                heat_proba = self.heat_model.predict_proba(X)[0]
                heat_conf = float(np.max(heat_proba))

                flood_class_idx = int(self.flood_model.predict(X)[0])
                flood_proba = self.flood_model.predict_proba(X)[0]
                flood_conf = float(np.max(flood_proba))

                rain_risk = RISK_LEVELS[rain_class_idx]
                heat_risk = RISK_LEVELS[heat_class_idx]
                flood_risk = RISK_LEVELS[flood_class_idx]
                avg_confidence = round(float((rain_conf + heat_conf + flood_conf) / 3.0), 3)

            except Exception as e:
                print(f"Inference error: {e}, using rule-based indicator fallback.")
                is_fallback = True
                rain_risk, heat_risk, flood_risk, avg_confidence = self._rule_based_risk(
                    temp, heat_index, precip_24h, soil_saturation
                )
        else:
            is_fallback = True
            rain_risk, heat_risk, flood_risk, avg_confidence = self._rule_based_risk(
                temp, heat_index, precip_24h, soil_saturation
            )

        # Composite disaster threat index (0-100)
        risk_weights = {"Low": 8, "Moderate": 35, "High": 70, "Severe": 95}
        composite_score = int(
            (risk_weights[rain_risk] * 0.35) +
            (risk_weights[heat_risk] * 0.30) +
            (risk_weights[flood_risk] * 0.35)
        )
        composite_score = min(100, max(0, composite_score))

        if composite_score < 25:
            overall_risk = "Low"
            risk_color = "#10b981"  # Emerald
        elif composite_score < 55:
            overall_risk = "Moderate"
            risk_color = "#f59e0b"  # Amber
        elif composite_score < 80:
            overall_risk = "High"
            risk_color = "#f97316"  # Orange
        else:
            overall_risk = "Severe"
            risk_color = "#ef4444"  # Red / Crimson

        # Transparent Explainability & Contributing Factors
        top_factors = self._explain_prediction(
            temp, humidity, heat_index, precip_24h, soil_saturation, wind_speed, wind_gusts
        )

        explanation = self._build_natural_explanation(
            overall_risk, rain_risk, heat_risk, flood_risk, top_factors, weather_data.get("city", "Location")
        )

        recommendations = self._build_safety_guidance(rain_risk, heat_risk, flood_risk, overall_risk)
        smart_alerts = self._generate_smart_alerts(
            weather_data.get("city", "Location"), rain_risk, heat_risk, flood_risk, overall_risk,
            temp, heat_index, precip_24h, wind_gusts
        )

        return {
            "rain_risk": rain_risk,
            "heat_risk": heat_risk,
            "flood_risk": flood_risk,
            "overall_risk": overall_risk,
            "risk_color": risk_color,
            "composite_score": composite_score,
            "confidence": avg_confidence,
            "is_fallback": is_fallback,
            "heat_index": round(heat_index, 1),
            "soil_saturation": round(soil_saturation, 1),
            "top_factors": top_factors,
            "explanation": explanation,
            "recommendations": recommendations,
            "smart_alerts": smart_alerts
        }

    def _rule_based_risk(self, temp, heat_index, precip_24h, soil_saturation):
        """Rule-based verification fallback according to meteorological standards."""
        # Rain
        if precip_24h < 15:
            rain_risk = "Low"
        elif precip_24h < 45:
            rain_risk = "Moderate"
        elif precip_24h < 95:
            rain_risk = "High"
        else:
            rain_risk = "Severe"

        # Heat
        if heat_index < 28:
            heat_risk = "Low"
        elif heat_index < 36:
            heat_risk = "Moderate"
        elif heat_index < 45:
            heat_risk = "High"
        else:
            heat_risk = "Severe"

        # Flood
        runoff = (precip_24h * 0.5) + (soil_saturation * 0.4)
        if runoff < 35:
            flood_risk = "Low"
        elif runoff < 65:
            flood_risk = "Moderate"
        elif runoff < 105:
            flood_risk = "High"
        else:
            flood_risk = "Severe"

        return rain_risk, heat_risk, flood_risk, 0.88

    def _explain_prediction(self, temp, humidity, heat_index, precip_24h, soil_saturation, wind_speed, wind_gusts):
        """Quantify factor contributions to hazard levels."""
        factors = []
        if precip_24h > 10:
            impact = min(98, int((precip_24h / 120.0) * 100))
            factors.append({
                "factor": "24h Accumulated Rainfall",
                "value": f"{precip_24h:.1f} mm",
                "impact_pct": max(15, impact),
                "severity": "high" if precip_24h > 50 else "moderate",
                "detail": "Elevates surface runoff and rapid drainage saturation."
            })
        if heat_index >= 32:
            impact = min(99, int(((heat_index - 26) / 20.0) * 100))
            factors.append({
                "factor": "Biometeorological Heat Index",
                "value": f"{heat_index:.1f} °C",
                "impact_pct": max(20, impact),
                "severity": "high" if heat_index > 40 else "moderate",
                "detail": "High combined heat & humidity hinders body's cooling via perspiration."
            })
        if soil_saturation >= 65:
            impact = min(95, int((soil_saturation / 100.0) * 90))
            factors.append({
                "factor": "Estimated Soil Moisture Saturation",
                "value": f"{soil_saturation:.0f}%",
                "impact_pct": max(10, impact),
                "severity": "high" if soil_saturation > 80 else "moderate",
                "detail": "Pre-saturated ground significantly amplifies flash flood potential."
            })
        if wind_gusts > 45:
            impact = min(95, int((wind_gusts / 100.0) * 85))
            factors.append({
                "factor": "Peak Wind Gusts",
                "value": f"{wind_gusts:.1f} km/h",
                "impact_pct": max(15, impact),
                "severity": "high" if wind_gusts > 75 else "moderate",
                "detail": "High kinetic wind shear increases structural and travel hazards."
            })

        if not factors:
            factors.append({
                "factor": "Atmospheric Equilibrium",
                "value": "Normal parameters",
                "impact_pct": 10,
                "severity": "low",
                "detail": "Current observations remain well within benign climatological limits."
            })

        factors.sort(key=lambda x: x["impact_pct"], reverse=True)
        return factors[:4]

    def _build_natural_explanation(self, overall_risk, rain_risk, heat_risk, flood_risk, top_factors, city):
        """Generate clear, non-technical natural language explanation for users."""
        primary_drivers = [f["factor"] for f in top_factors if f["severity"] in ["high", "moderate"]]
        drivers_str = ", ".join(primary_drivers) if primary_drivers else "stable meteorological observations"
        
        return (
            f"The AI Hazard Model assessed an overall {overall_risk.upper()} risk for {city}. "
            f"Key contributing factors include {drivers_str}. "
            f"Specific hazard breakdown: Heavy Rainfall is evaluated as {rain_risk}, "
            f"Extreme Heat as {heat_risk}, and Flood Risk exploration as {flood_risk}."
        )

    def _build_safety_guidance(self, rain_risk, heat_risk, flood_risk, overall_risk):
        """Provide persona-tailored safety guidance for farmers, travellers, general public, students."""
        guidance = {
            "general_public": [],
            "farmers": [],
            "travelers": [],
            "students_community": []
        }

        # General Public
        if rain_risk in ["High", "Severe"] or flood_risk in ["High", "Severe"]:
            guidance["general_public"].append("Keep emergency disaster kit, battery flashlight, and charged power banks accessible.")
            guidance["general_public"].append("Never walk or drive through flowing water; remember 'Turn Around, Don't Drown'.")
            guidance["general_public"].append("Move critical electrical appliances and documents above potential ground flood lines.")
        elif heat_risk in ["High", "Severe"]:
            guidance["general_public"].append("Drink at least 2.5 - 3 liters of water throughout the day; avoid direct midday sunlight (11:00 - 16:00).")
            guidance["general_public"].append("Check closely on elderly neighbors, young children, and outdoor pets.")
        else:
            guidance["general_public"].append("Conditions are currently manageable. Maintain standard situational awareness and check daily forecast updates.")

        # Farmers & Agriculture
        if rain_risk in ["High", "Severe"] or flood_risk in ["High", "Severe"]:
            guidance["farmers"].append("Inspect field drainage furrows to prevent root inundation and crop waterlogging.")
            guidance["farmers"].append("Move livestock and grazing herds to elevated ground away from ravines and streams.")
            guidance["farmers"].append("Postpone fertilizer and pesticide spraying to prevent chemical runoff into local waterways.")
        elif heat_risk in ["High", "Severe"]:
            guidance["farmers"].append("Irrigate crops during early morning or evening hours to minimize evaporative loss.")
            guidance["farmers"].append("Provide shaded ventilation and fresh hydration troughs for livestock.")
        else:
            guidance["farmers"].append("Good conditions for seasonal fieldwork and scheduled agricultural operations.")

        # Travelers & Commuters
        if rain_risk in ["High", "Severe"] or flood_risk in ["High", "Severe"]:
            guidance["travelers"].append("Expect potential flight delays, subway waterlogging, or blocked highway underpasses.")
            guidance["travelers"].append("Double your following distance on slick asphalt; inspect tire tread and wipers.")
        elif heat_risk in ["High", "Severe"]:
            guidance["travelers"].append("Never leave passengers or animals in parked vehicles, even for a few minutes with windows cracked.")
            guidance["travelers"].append("Carry chilled hydration containers when using public transit or driving long distances.")
        else:
            guidance["travelers"].append("Commute corridors and transport hubs operating under standard conditions.")

        # Students & Community Leaders
        if overall_risk in ["High", "Severe"]:
            guidance["students_community"].append("Verify school administration notifications regarding remote learning or early dismissal.")
            guidance["students_community"].append("Establish neighborhood contact trees and help elderly neighbors clear storm drains.")
        else:
            guidance["students_community"].append("Conduct routine disaster preparedness drills and inspect emergency supplies.")

        return guidance

    def _generate_smart_alerts(self, city, rain_risk, heat_risk, flood_risk, overall_risk, temp, heat_index, precip_24h, wind_gusts):
        """Construct structured smart alert objects when hazards are detected."""
        alerts = []
        if rain_risk in ["High", "Severe"]:
            alerts.append({
                "alert_type": "HEAVY_RAINFALL_WARNING",
                "severity": rain_risk.upper(),
                "headline": f"Heavy Rainfall Warning for {city}",
                "description": f"Forecast rainfall of {precip_24h:.1f} mm exceeds critical drainage thresholds. Rapid accumulation and localized ponding expected.",
                "recommendations": [
                    "Avoid flood-prone basements and underpasses",
                    "Monitor regional drainage authority updates"
                ]
            })

        if heat_risk in ["High", "Severe"]:
            alerts.append({
                "alert_type": "EXTREME_HEAT_ADVISORY",
                "severity": heat_risk.upper(),
                "headline": f"Extreme Heatwave Advisory for {city}",
                "description": f"Heat Index reaching dangerous {heat_index:.1f}°C. Prolonged outdoor exposure can induce heat cramps, exhaustion, or stroke.",
                "recommendations": [
                    "Limit strenuous outdoor activity to morning hours",
                    "Stay in air-conditioned or well-ventilated areas"
                ]
            })

        if flood_risk in ["High", "Severe"]:
            alerts.append({
                "alert_type": "FLASH_FLOOD_WATCH",
                "severity": flood_risk.upper(),
                "headline": f"Flash Flood Alert in {city} Vicinity",
                "description": f"Hydrological runoff index indicates high saturation and elevated flood hazard.",
                "recommendations": [
                    "Secure outdoor property and prepare essential emergency bags",
                    "Do not attempt to ford flooded roads"
                ]
            })

        return alerts

# Singleton instance
risk_engine = DisasterRiskEngine()
