"""
Flask Application for AI-Powered Weather Disaster Early Warning System.
Provides RESTful APIs for live weather data, ML hazard assessments,
scenario simulations, database persistence, and model transparency.
"""

from flask import Flask, render_template, request, jsonify, send_file, Response
from flask_cors import CORS
import os
import io
import csv
import json
from weather_service import search_locations, fetch_weather_data
from ml_engine import risk_engine
from database import save_assessment, get_recent_history, get_recent_alerts, get_city_hazard_stats

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

GLOBAL_HOTSPOTS = [
    {"name": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "climate_desc": "Subtropical / Typhoon Zone"},
    {"name": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777, "climate_desc": "Monsoon / Coastal Flooding"},
    {"name": "Miami", "country": "United States", "lat": 25.7617, "lon": -80.1918, "climate_desc": "Hurricane & Storm Surge Basin"},
    {"name": "London", "country": "United Kingdom", "lat": 51.5074, "lon": -0.1278, "climate_desc": "Temperate Oceanic / Flash Rain"},
    {"name": "Manila", "country": "Philippines", "lat": 14.5995, "lon": 120.9842, "climate_desc": "Tropical Cyclone & Flood Plain"},
    {"name": "Cairo", "country": "Egypt", "lat": 30.0444, "lon": 31.2357, "climate_desc": "Hyper-Arid / Severe Heat Stress"},
    {"name": "Sydney", "country": "Australia", "lat": -33.8688, "lon": 151.2093, "climate_desc": "Subtropical / Heatwave & Bushfire Risk"},
    {"name": "New York", "country": "United States", "lat": 40.7128, "lon": -74.0060, "climate_desc": "Nor'easter Storms & Coastal Flooding"},
    {"name": "Jakarta", "country": "Indonesia", "lat": -6.2088, "lon": 106.8456, "climate_desc": "Equatorial Monsoon & Inundation"},
    {"name": "Houston", "country": "United States", "lat": 29.7604, "lon": -95.3698, "climate_desc": "Gulf Coast Downpours & Flash Floods"}
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/search")
def search():
    query = request.args.get("q", "")
    results = search_locations(query)
    return jsonify({"results": results})

@app.route("/api/weather")
def get_weather_and_risk():
    try:
        lat = float(request.args.get("lat", 0.0))
        lon = float(request.args.get("lon", 0.0))
        city = request.args.get("city", "Selected Location")
        country = request.args.get("country", "")

        # 1. Fetch meteorological observation from Open-Meteo
        weather_data = fetch_weather_data(lat, lon, city, country)
        if not weather_data:
            return jsonify({"error": "Failed to fetch weather data for this location"}), 502

        # 2. Run AI Disaster Risk Engine
        prediction = risk_engine.predict_risk(weather_data)

        # 3. Save to SQLite database
        save_assessment(weather_data, prediction, prediction.get("smart_alerts", []))

        return jsonify({
            "status": "success",
            "weather": weather_data,
            "prediction": prediction
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/simulate", methods=["POST"])
def simulate():
    """Evaluate synthetic hazard parameters in the Disaster Simulation Sandbox."""
    try:
        payload = request.json or {}
        temp = float(payload.get("temperature", 28.0))
        humidity = float(payload.get("humidity", 60.0))
        precip = float(payload.get("precipitation", 10.0))
        wind_gusts = float(payload.get("wind_gusts", 25.0))
        pressure = float(payload.get("pressure", 1010.0))

        synthetic_weather = {
            "city": payload.get("scenario_name", "Sandbox Simulation"),
            "temperature": temp,
            "humidity": humidity,
            "precipitation": precip,
            "wind_speed": wind_gusts * 0.7,
            "wind_gusts": wind_gusts,
            "pressure": pressure,
            "pressure_drop_3h": float(payload.get("pressure_drop_3h", 2.0))
        }

        prediction = risk_engine.predict_risk(synthetic_weather)
        return jsonify({
            "status": "success",
            "simulation": synthetic_weather,
            "prediction": prediction
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/history")
def get_history():
    limit = int(request.args.get("limit", 15))
    history = get_recent_history(limit)
    stats = get_city_hazard_stats()
    return jsonify({"history": history, "stats": stats})

@app.route("/api/alerts")
def get_alerts():
    limit = int(request.args.get("limit", 10))
    alerts = get_recent_alerts(limit)
    return jsonify({"alerts": alerts})

@app.route("/api/metrics")
def get_metrics():
    """Return model performance metrics and explainability parameters."""
    return jsonify({
        "metrics": risk_engine.metrics,
        "models_loaded": risk_engine.models_loaded
    })

@app.route("/api/hotspots")
def get_hotspots():
    """Return preconfigured global disaster monitoring hotspots."""
    return jsonify({"hotspots": GLOBAL_HOTSPOTS})

@app.route("/api/export")
def export_history():
    """Export history as CSV or JSON."""
    fmt = request.args.get("format", "csv").lower()
    records = get_recent_history(limit=100)

    if fmt == "json":
        return Response(
            json.dumps(records, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment;filename=disaster_history.json"}
        )

    # Default CSV
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow([
        "ID", "City", "Country", "Rain Risk", "Heat Risk", "Flood Risk",
        "Overall Risk", "Composite Score", "Temperature (C)", "Precipitation (mm)", "Timestamp"
    ])
    for r in records:
        writer.writerow([
            r.get("id"),
            r.get("city"),
            r.get("country"),
            r.get("rain_risk"),
            r.get("heat_risk"),
            r.get("flood_risk"),
            r.get("overall_risk"),
            r.get("composite_score"),
            r.get("temperature"),
            r.get("precipitation"),
            r.get("created_at")
        ])

    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=weather_disaster_history.csv"}
    )

if __name__ == "__main__":
    print("Starting AI Weather Disaster Early Warning System on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=False)
