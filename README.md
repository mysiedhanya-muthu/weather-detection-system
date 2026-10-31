# 🌩️ ClimaShield AI — Weather Disaster Early Warning System

An intelligent, AI-powered weather disaster risk assessment and early warning platform designed to help the public, farmers, travelers, and emergency planners detect and prepare for hazardous weather events.

---

## 🌟 Key Features

1. **Live Weather Dashboard**:
   - Real-time meteorological data powered by **Open-Meteo** (no API key required).
   - Global search with debounced autocomplete and quick-select disaster hotspot pills (*Tokyo, Mumbai, Miami, London, Manila, Cairo, Sydney, New York, Jakarta, Houston*).
   - Real-time temperature, heat index, 24h precipitation, wind velocity, humidity, barometric pressure, and soil saturation estimation.

2. **AI-Based Multi-Hazard Risk Assessment Engine**:
   - Trained **Scikit-Learn Machine Learning models**:
     - **Heavy Rainfall Risk Classifier**: Random Forest (99.8% Accuracy).
     - **Extreme Heat Risk Classifier**: Random Forest (100.0% Accuracy).
     - **Flood Risk Exploration Classifier**: Gradient Boosting (97.8% Accuracy).
   - Composite Disaster Threat Index (0–100 scale: Low, Moderate, High, Severe).
   - Transparent AI Explainability: Factor contribution weighting and natural language rationale.
   - Rule-based meteorological fallback when parameters exceed calibrated bounds.

3. **Dynamic Climate Imagery & Atmospheric Theming**:
   - High-impact environmental photos that adapt automatically based on current weather conditions:
     - Clear Sunny Day (`weather_clear.jpg`)
     - Torrential Heavy Rain (`weather_rain.jpg`)
     - Supercell Thunderstorm (`weather_thunderstorm.jpg`)
     - Inundation Flood Hazard (`weather_flood.jpg`)
     - Scorching Heatwave (`weather_heatwave.jpg`)
     - Blizzard Winter Hazard (`weather_snow.jpg`)
     - Low-Visibility Mist & Fog (`weather_fog.jpg`)
   - Ambient dynamic background that seamlessly reflects the weather state.

4. **Interactive Weather Risk Map**:
   - Dark-mode cartography via **Leaflet.js**.
   - Pulsating hazard markers color-coded by threat level.
   - Click to inspect or jump directly to any monitored city.

5. **Disaster Simulation Sandbox ("What-If" Scenario Simulator)**:
   - Interactive sliders for Temperature, Humidity, 24h Rainfall, and Wind Gusts.
   - Test extreme presets (*Extreme Heatwave, Monsoon Inundation, Superstorm Cyclone, Mild Spring*).
   - Observe real-time Scikit-Learn decision boundaries update as you slide!

6. **Actionable Persona-Adaptive Safety Guidance**:
   - Tailored checklists for:
     - 👥 **General Public** (emergency packs, flood guidelines)
     - 🌾 **Farmers & Agriculture** (furrow drainage, livestock protection, irrigation)
     - 🚗 **Travelers & Commuters** (transit disruptions, hydroplaning precautions)
     - 🎒 **Students & Community Leaders** (school advisories, neighborhood safety)

7. **Smart Alert Broadcast & Web Audio Siren**:
   - Visual pulsing banner for High/Severe risks.
   - Synthesized emergency tone chime via Web Audio API.

8. **SQL Database Persistence (SQLite)**:
   - Automatically logs weather observations, AI predictions, and active alerts.
   - Instant export to **CSV** or **JSON**.

---

## 🚀 Quick Start Guide

### 1. Requirements
- Python 3.10+
- Flask & Flask-CORS
- Scikit-learn
- Pandas & NumPy
- Requests

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Run Model Training (Optional, pre-trained models included)
```bash
python train_model.py
```

### 4. Start the Application
```bash
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## 📁 Project Architecture

```
weather-detecting-system/
├── app.py                      # Flask backend API & static router
├── ml_engine.py                # Scikit-learn risk inference & explainability engine
├── database.py                 # SQLite database models & query logging
├── weather_service.py          # Open-Meteo geocoding & forecast integration
├── train_model.py              # ML training pipeline & meteorological dataset generation
├── requirements.txt            # Python dependencies (Render compatible)
├── static/
│   ├── css/
│   │   └── style.css           # Glassmorphism, animations, responsive design
│   ├── js/
│   │   ├── app.js              # Core UI orchestration & Web Audio synthesizer
│   │   ├── charts.js           # Chart.js hourly & 7-day outlook visualizations
│   │   ├── map.js              # Leaflet.js interactive hazard map
│   │   └── simulator.js        # What-If scenario sandbox
│   └── images/                 # Realistic climate environmental photos
│       ├── weather_clear.jpg
│       ├── weather_rain.jpg
│       ├── weather_heatwave.jpg
│       ├── weather_flood.jpg
│       ├── weather_thunderstorm.jpg
│       ├── weather_snow.jpg
│       └── weather_fog.jpg
├── templates/
│   └── index.html              # Modern single-page web application dashboard
└── models/
    ├── weather_hazard_models.pkl # Serialized Scikit-learn classifiers
    └── metrics.json            # Model evaluation metrics & validation report
```

---

## 🌐 Deploy to Render

This repository is ready for deployment on [Render](https://render.com):
- **Build Command**: `pip install -r requirements.txt && python train_model.py`
- **Start Command**: `gunicorn app:app`
- **Environment**: Python 3
