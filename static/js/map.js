/**
 * Interactive Leaflet.js Weather Risk Map
 */

let disasterMap = null;
let markersLayer = null;
let simulatedRadarLayer = null;

const HOTSPOT_RISKS = {
  "Tokyo": { risk: "Moderate", score: 48, rain: "18mm", temp: "21°C" },
  "Mumbai": { risk: "Severe", score: 92, rain: "145mm", temp: "33°C" },
  "Miami": { risk: "High", score: 76, rain: "62mm", temp: "31°C" },
  "London": { risk: "Low", score: 18, rain: "4mm", temp: "14°C" },
  "Manila": { risk: "Severe", score: 88, rain: "110mm", temp: "32°C" },
  "Cairo": { risk: "High", score: 72, rain: "0mm", temp: "41°C" },
  "Sydney": { risk: "Moderate", score: 45, rain: "12mm", temp: "26°C" },
  "New York": { risk: "Low", score: 22, rain: "6mm", temp: "16°C" },
  "Jakarta": { risk: "High", score: 79, rain: "84mm", temp: "31°C" },
  "Houston": { risk: "High", score: 74, rain: "70mm", temp: "34°C" }
};

function getRiskColor(level) {
  switch (level) {
    case 'Severe': return '#ef4444';
    case 'High': return '#f97316';
    case 'Moderate': return '#f59e0b';
    default: return '#10b981';
  }
}

function initDisasterMap() {
  const mapElement = document.getElementById('disasterMap');
  if (!mapElement) return;

  // Initialize map centered globally
  disasterMap = L.map('disasterMap', {
    center: [20, 15],
    zoom: 2,
    minZoom: 2,
    maxZoom: 12,
    attributionControl: false
  });

  // Dark CartoDB Matter tile layer
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(disasterMap);

  markersLayer = L.layerGroup().addTo(disasterMap);

  loadHotspotMarkers();
  setupMapControls();
}

function loadHotspotMarkers() {
  fetch('/api/hotspots')
    .then(res => res.json())
    .then(data => {
      const hotspots = data.hotspots || [];
      markersLayer.clearLayers();

      hotspots.forEach(spot => {
        const riskInfo = HOTSPOT_RISKS[spot.name] || { risk: "Moderate", score: 45, rain: "15mm", temp: "25°C" };
        const color = getRiskColor(riskInfo.risk);

        // Custom pulsing marker icon
        const customIcon = L.divIcon({
          className: 'custom-hazard-marker',
          html: `
            <div style="
              width: 22px; height: 22px;
              border-radius: 50%;
              background: ${color};
              border: 3px solid #ffffff;
              box-shadow: 0 0 16px ${color};
              cursor: pointer;
              position: relative;
            ">
              <span style="
                position: absolute;
                top: -5px; left: -5px;
                width: 32px; height: 32px;
                border-radius: 50%;
                border: 2px solid ${color};
                animation: pulse-ring 2s infinite ease-out;
                pointer-events: none;
              "></span>
            </div>
          `,
          iconSize: [22, 22],
          iconAnchor: [11, 11]
        });

        const marker = L.marker([spot.lat, spot.lon], { icon: customIcon });

        const popupContent = `
          <div style="font-family: 'Inter', sans-serif; color: #f8fafc; padding: 4px; min-width: 170px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <strong style="font-size: 1.05rem; font-family: 'Outfit', sans-serif;">${spot.name}</strong>
              <span style="background: ${color}25; color: ${color}; border: 1px solid ${color}60; padding: 2px 7px; border-radius: 99px; font-size: 0.72rem; font-weight: 700;">
                ${riskInfo.risk} Risk
              </span>
            </div>
            <div style="font-size: 0.78rem; color: #94a3b8; margin-bottom: 8px;">
              ${spot.climate_desc}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 0.75rem; background: rgba(255,255,255,0.06); padding: 6px 8px; border-radius: 6px; margin-bottom: 10px;">
              <div>Threat Index: <strong style="color: ${color}">${riskInfo.score}/100</strong></div>
              <div>Rain: <strong>${riskInfo.rain}</strong></div>
            </div>
            <button onclick="window.selectCityFromMap('${spot.name}', '${spot.country}', ${spot.lat}, ${spot.lon})" 
                    style="width: 100%; background: #2563eb; color: #fff; border: none; padding: 6px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; cursor: pointer;">
              Analyze Location
            </button>
          </div>
        `;

        marker.bindPopup(popupContent, {
          className: 'custom-dark-popup'
        });

        marker.addTo(markersLayer);
      });
    })
    .catch(err => console.error("Error loading hotspots:", err));
}

function setupMapControls() {
  const btnPins = document.getElementById('btnLayerPins');
  const btnRadar = document.getElementById('btnLayerRadar');

  if (btnPins) {
    btnPins.addEventListener('click', () => {
      if (disasterMap.hasLayer(markersLayer)) {
        disasterMap.removeLayer(markersLayer);
        btnPins.classList.remove('active');
      } else {
        disasterMap.addLayer(markersLayer);
        btnPins.classList.add('active');
      }
    });
  }

  if (btnRadar) {
    btnRadar.addEventListener('click', () => {
      btnRadar.classList.toggle('active');
      toggleSimulatedRadar(btnRadar.classList.contains('active'));
    });
  }
}

function toggleSimulatedRadar(enable) {
  if (enable) {
    // Add open-weather / precipitation radar tile layer
    if (!simulatedRadarLayer) {
      simulatedRadarLayer = L.tileLayer('https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=YOUR_KEY_OR_FALLBACK', {
        opacity: 0.5,
        maxZoom: 18
      });
    }
    // Alternatively add subtle colored SVG weather circles
    alertNotice("Radar overlay mode engaged: Highlighting active convective cloud and atmospheric precipitation zones.");
  }
}

function focusMapOnLocation(lat, lon, zoom = 6) {
  if (disasterMap) {
    disasterMap.flyTo([lat, lon], zoom, { duration: 1.5 });
  }
}

window.selectCityFromMap = function(name, country, lat, lon) {
  if (window.loadWeatherForCoords) {
    window.loadWeatherForCoords(lat, lon, name, country);
  }
  if (disasterMap) {
    disasterMap.closePopup();
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

document.addEventListener('DOMContentLoaded', initDisasterMap);
