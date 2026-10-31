"""
Database module for AI-Powered Weather Disaster Early Warning System.
Uses SQLite for persistent storage of weather observations, AI hazard predictions,
and emergency alert logs.
"""

import sqlite3
import json
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "weather_disaster.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Weather observations log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weather_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        country TEXT,
        latitude REAL,
        longitude REAL,
        temperature REAL,
        feels_like REAL,
        humidity REAL,
        precipitation REAL,
        wind_speed REAL,
        pressure REAL,
        weather_code INTEGER,
        weather_desc TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. AI Disaster Risk Predictions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        country TEXT,
        latitude REAL,
        longitude REAL,
        rain_risk TEXT,
        heat_risk TEXT,
        flood_risk TEXT,
        overall_risk TEXT,
        composite_score INTEGER,
        confidence REAL,
        top_factors TEXT,
        explanation TEXT,
        is_fallback INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. Smart Disaster Alerts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        country TEXT,
        alert_type TEXT,
        severity TEXT,
        headline TEXT,
        description TEXT,
        recommendations TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def save_assessment(weather_data, prediction_data, alert_data=None):
    """Save live weather observation, ML prediction, and alerts to SQLite."""
    conn = get_connection()
    cursor = conn.cursor()

    # Insert weather log
    cursor.execute("""
    INSERT INTO weather_logs (
        city, country, latitude, longitude, temperature, feels_like,
        humidity, precipitation, wind_speed, pressure, weather_code, weather_desc
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        weather_data.get("city", "Unknown"),
        weather_data.get("country", ""),
        weather_data.get("latitude"),
        weather_data.get("longitude"),
        weather_data.get("temperature"),
        weather_data.get("feels_like"),
        weather_data.get("humidity"),
        weather_data.get("precipitation"),
        weather_data.get("wind_speed"),
        weather_data.get("pressure"),
        weather_data.get("weather_code"),
        weather_data.get("weather_desc")
    ))

    # Insert prediction
    cursor.execute("""
    INSERT INTO predictions (
        city, country, latitude, longitude, rain_risk, heat_risk,
        flood_risk, overall_risk, composite_score, confidence,
        top_factors, explanation, is_fallback
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        weather_data.get("city", "Unknown"),
        weather_data.get("country", ""),
        weather_data.get("latitude"),
        weather_data.get("longitude"),
        prediction_data.get("rain_risk"),
        prediction_data.get("heat_risk"),
        prediction_data.get("flood_risk"),
        prediction_data.get("overall_risk"),
        prediction_data.get("composite_score"),
        prediction_data.get("confidence", 0.95),
        json.dumps(prediction_data.get("top_factors", [])),
        prediction_data.get("explanation", ""),
        1 if prediction_data.get("is_fallback") else 0
    ))

    # Insert alerts if any
    if alert_data and isinstance(alert_data, list):
        for alt in alert_data:
            cursor.execute("""
            INSERT INTO alerts (
                city, country, alert_type, severity, headline, description, recommendations
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                weather_data.get("city", "Unknown"),
                weather_data.get("country", ""),
                alt.get("alert_type"),
                alt.get("severity"),
                alt.get("headline"),
                alt.get("description"),
                json.dumps(alt.get("recommendations", []))
            ))

    conn.commit()
    conn.close()

def get_recent_history(limit=15):
    """Retrieve recent risk assessments."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT p.id, p.city, p.country, p.rain_risk, p.heat_risk, p.flood_risk,
           p.overall_risk, p.composite_score, p.created_at, w.temperature,
           w.precipitation, w.weather_desc
    FROM predictions p
    LEFT JOIN weather_logs w ON p.city = w.city AND DATE(p.created_at) = DATE(w.created_at)
    ORDER BY p.id DESC
    LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_recent_alerts(limit=10):
    """Retrieve recent smart disaster alerts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, city, country, alert_type, severity, headline, description,
           recommendations, created_at
    FROM alerts
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))
    rows = []
    for r in cursor.fetchall():
        item = dict(r)
        try:
            item["recommendations"] = json.loads(item["recommendations"])
        except Exception:
            item["recommendations"] = []
        rows.append(item)
    conn.close()
    return rows

def get_city_hazard_stats():
    """Retrieve summarized disaster risk stats grouped by city."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT city, country,
           COUNT(*) as query_count,
           AVG(composite_score) as avg_risk_score,
           MAX(composite_score) as max_risk_score,
           MAX(created_at) as last_assessed
    FROM predictions
    GROUP BY city, country
    ORDER BY query_count DESC
    LIMIT 10
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

# Initialize on module import
init_db()
