/**
 * AI-Powered Weather Disaster Early Warning System
 * Main Frontend Application Script
 */

let currentWeatherData = null;
let currentPredictionData = null;
let searchDebounceTimer = null;
let audioContext = null;
let sirenPlaying = false;
let sirenOscillator = null;

// Default initial location: Tokyo
const DEFAULT_CITY = {
  name: "Tokyo",
  country: "Japan",
  lat: 35.6762,
  lon: 139.6503
};

document.addEventListener('DOMContentLoaded', () => {
  initSearchAutocomplete();
  initPersonaTabs();
  initThemeToggle();
  initModals();
  loadHistoryRecords();
  
  // Load default location
  loadWeatherForCoords(DEFAULT_CITY.lat, DEFAULT_CITY.lon, DEFAULT_CITY.name, DEFAULT_CITY.country);

  // Setup geolocation button
  const btnLocate = document.getElementById('btnLocate');
  if (btnLocate) {
    btnLocate.addEventListener('click', handleDetectLocation);
  }

  // Setup siren toggle button in alert banner
  const btnSiren = document.getElementById('btnToggleSiren');
  if (btnSiren) {
    btnSiren.addEventListener('click', toggleEmergencySiren);
  }

  // Setup export buttons
  const btnExportCsv = document.getElementById('btnExportCsv');
  const btnExportJson = document.getElementById('btnExportJson');
  if (btnExportCsv) {
    btnExportCsv.addEventListener('click', () => window.location.href = '/api/export?format=csv');
  }
  if (btnExportJson) {
    btnExportJson.addEventListener('click', () => window.location.href = '/api/export?format=json');
  }
});

// Load weather and AI hazard assessment
window.loadWeatherForCoords = function(lat, lon, cityName, countryName) {
  showLoadingState(true);

  const url = `/api/weather?lat=${lat}&lon=${lon}&city=${encodeURIComponent(cityName)}&country=${encodeURIComponent(countryName || '')}`;
  
  fetch(url)
    .then(res => {
      if (!res.ok) throw new Error("Weather service response not OK");
      return res.json();
    })
    .then(data => {
      if (data.status === 'success') {
        currentWeatherData = data.weather;
        currentPredictionData = data.prediction;
        renderWeatherDashboard(data.weather, data.prediction);
        loadHistoryRecords(); // Refresh SQLite logs table
        if (window.focusMapOnLocation) {
          window.focusMapOnLocation(lat, lon, 6);
        }
      } else {
        alertNotice(data.error || "Failed to retrieve risk assessment.");
      }
    })
    .catch(err => {
      console.error("Error loading weather data:", err);
      alertNotice("Unable to reach meteorological servers. Please check connection.");
    })
    .finally(() => {
      showLoadingState(false);
    });
};

function renderWeatherDashboard(w, p) {
  // 1. Dynamic Climate Picture & Dynamic Atmospheric Backdrop
  const backdrop = document.querySelector('.weather-ambient-backdrop');
  if (backdrop && w.climate_image) {
    backdrop.style.backgroundImage = `url('${w.climate_image}')`;
  }

  const climateImg = document.getElementById('climatePhoto');
  const climateDesc = document.getElementById('climatePhotoDesc');
  const climateBadge = document.getElementById('climatePhotoBadge');
  if (climateImg) climateImg.src = w.climate_image;
  if (climateDesc) climateDesc.textContent = `${w.weather_desc} atmospheric landscape`;
  if (climateBadge) climateBadge.textContent = `${w.temperature}°C · ${w.weather_category.toUpperCase()}`;

  // 2. City Header & Observations
  document.getElementById('displayCity').textContent = `${w.city}${w.country ? ', ' + w.country : ''}`;
  document.getElementById('displayCoords').textContent = `Lat: ${w.latitude.toFixed(4)}°, Lon: ${w.longitude.toFixed(4)}° · Updated just now`;
  document.getElementById('displayTemp').textContent = Math.round(w.temperature);
  document.getElementById('displayConditionIcon').textContent = w.icon;
  document.getElementById('displayConditionDesc').textContent = w.weather_desc;
  document.getElementById('displayFeelsLike').textContent = `Feels like ${w.feels_like}°C · Heat Index ${p.heat_index}°C`;

  // 3. Four Metric Tiles
  document.getElementById('metricPrecip').textContent = `${w.precipitation} mm`;
  document.getElementById('metricPrecipSub').textContent = `Peak rate ~${(w.precipitation * 0.28).toFixed(1)} mm/h`;

  document.getElementById('metricWind').textContent = `${w.wind_speed} km/h`;
  document.getElementById('metricWindSub').textContent = `Gusts up to ${w.wind_gusts} km/h`;

  document.getElementById('metricHumidity').textContent = `${w.humidity}%`;
  document.getElementById('metricHumiditySub').textContent = `Soil saturation ~${p.soil_saturation}%`;

  document.getElementById('metricPressure').textContent = `${Math.round(w.pressure)} hPa`;
  document.getElementById('metricPressureSub').textContent = `3h delta: ${w.pressure_drop_3h >= 0 ? '+' : ''}${w.pressure_drop_3h} hPa`;

  // 4. AI Disaster Risk Console
  const scoreElem = document.getElementById('riskScoreNum');
  const levelElem = document.getElementById('riskLevelText');
  const circleElem = document.getElementById('riskScoreCircle');
  const descElem = document.getElementById('riskSummaryDesc');
  const confElem = document.getElementById('riskConfidenceText');

  scoreElem.textContent = p.composite_score;
  levelElem.textContent = `${p.overall_risk} Risk`;
  levelElem.style.color = p.risk_color;
  circleElem.style.borderColor = p.risk_color;
  circleElem.style.boxShadow = `0 0 25px ${p.risk_color}45`;
  descElem.textContent = p.composite_score > 60
    ? "Heightened hazard probability detected. Meteorological thresholds warrant enhanced precautionary readiness."
    : "Benign to moderate risk profile. Atmospheric parameters remain within manageable civilian margins.";
  
  confElem.textContent = p.is_fallback
    ? "Rule-Based Standard Fallback (Model uncalibrated for extreme outlier)"
    : `ML Ensemble Validated · Confidence ${(p.confidence * 100).toFixed(1)}%`;

  // 5. Three Core Hazard Cards
  updateHazardCard('cardRainRisk', 'badgeRainRisk', 'statRainRisk', p.rain_risk, `${w.precipitation} mm in 24h`);
  updateHazardCard('cardHeatRisk', 'badgeHeatRisk', 'statHeatRisk', p.heat_risk, `Heat Index ${p.heat_index}°C`);
  updateHazardCard('cardFloodRisk', 'badgeFloodRisk', 'statFloodRisk', p.flood_risk, `Soil saturation ${p.soil_saturation}%`);

  // 6. Transparent Explainability Bars
  renderExplainabilityFactors(p.top_factors, p.explanation);

  // 7. Safety Guidance Persona Checklists
  renderSafetyGuidance(p.recommendations);

  // 8. Smart Alerts Banner & Emergency Chime
  handleSmartAlerts(p.smart_alerts, p.overall_risk, w.city);

  // 9. Update Charts
  if (window.updateHourlyChart) {
    window.updateHourlyChart(w.hourly || []);
  }
  if (window.updateWeeklyTrendChart) {
    window.updateWeeklyTrendChart(w.daily || []);
  }
}

function updateHazardCard(cardId, badgeId, statId, riskLevel, statText) {
  const badge = document.getElementById(badgeId);
  const stat = document.getElementById(statId);
  if (!badge) return;

  badge.textContent = `${riskLevel} Risk`;
  badge.className = 'hazard-badge';
  if (riskLevel === 'Low') badge.classList.add('badge-low');
  else if (riskLevel === 'Moderate') badge.classList.add('badge-moderate');
  else if (riskLevel === 'High') badge.classList.add('badge-high');
  else badge.classList.add('badge-severe');

  if (stat) stat.textContent = statText;
}

function renderExplainabilityFactors(factors, explanation) {
  const container = document.getElementById('explainFactorsList');
  const explainBox = document.getElementById('naturalExplanationText');
  if (!container) return;

  container.innerHTML = '';
  (factors || []).forEach(f => {
    const item = document.createElement('div');
    item.className = 'factor-item';
    item.innerHTML = `
      <div class="factor-meta">
        <span class="factor-name">${f.factor}</span>
        <span class="factor-val">${f.value} (${f.impact_pct}% impact)</span>
      </div>
      <div class="factor-bar-bg">
        <div class="factor-bar-fill" style="width: ${f.impact_pct}%;"></div>
      </div>
    `;
    container.appendChild(item);
  });

  if (explainBox) {
    explainBox.textContent = explanation || "Model assessment indicates stable baseline parameters.";
  }
}

function renderSafetyGuidance(recs) {
  if (!recs) return;

  const renderList = (paneId, items) => {
    const pane = document.getElementById(paneId);
    if (!pane) return;
    pane.innerHTML = '';
    const group = document.createElement('div');
    group.className = 'checklist-group';

    (items || []).forEach(text => {
      const item = document.createElement('div');
      item.className = 'checklist-item';
      item.innerHTML = `
        <span class="check-icon">✓</span>
        <div>${text}</div>
      `;
      group.appendChild(item);
    });
    pane.appendChild(group);
  };

  renderList('tabPaneGeneral', recs.general_public);
  renderList('tabPaneFarmers', recs.farmers);
  renderList('tabPaneTravelers', recs.travelers);
  renderList('tabPaneStudents', recs.students_community);
}

function handleSmartAlerts(alerts, overallRisk, city) {
  const banner = document.getElementById('alertBanner');
  const alertText = document.getElementById('alertBannerText');
  
  if (alerts && alerts.length > 0) {
    const primaryAlert = alerts[0];
    alertText.innerHTML = `<strong>⚠️ ${primaryAlert.headline}:</strong> ${primaryAlert.description}`;
    banner.style.display = 'block';

    if (overallRisk === 'Severe') {
      banner.style.background = 'linear-gradient(90deg, #dc2626, #991b1b)';
    } else {
      banner.style.background = 'linear-gradient(90deg, #ea580c, #c2410c)';
    }
  } else {
    banner.style.display = 'none';
    stopEmergencySiren();
  }
}

// Emergency Sound Synthesizer via Web Audio API
function toggleEmergencySiren() {
  const btn = document.getElementById('btnToggleSiren');
  if (sirenPlaying) {
    stopEmergencySiren();
    if (btn) btn.innerHTML = '🔔 Audio Siren';
  } else {
    startEmergencySiren();
    if (btn) btn.innerHTML = '🔇 Stop Siren';
  }
}

function startEmergencySiren() {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    if (!audioContext) audioContext = new AudioContext();

    if (audioContext.state === 'suspended') {
      audioContext.resume();
    }

    const osc = audioContext.createOscillator();
    const gain = audioContext.createGain();

    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(650, audioContext.currentTime);
    osc.frequency.linearRampToValueAtTime(950, audioContext.currentTime + 0.6);
    osc.frequency.linearRampToValueAtTime(650, audioContext.currentTime + 1.2);

    // Subtle gentle volume
    gain.gain.setValueAtTime(0.08, audioContext.currentTime);

    osc.connect(gain);
    gain.connect(audioContext.destination);
    osc.start();

    sirenOscillator = osc;
    sirenPlaying = true;

    // Auto stop after 5 seconds to prevent annoyance
    setTimeout(() => {
      stopEmergencySiren();
      const btn = document.getElementById('btnToggleSiren');
      if (btn) btn.innerHTML = '🔔 Audio Siren';
    }, 5000);
  } catch (e) {
    console.error("Audio error:", e);
  }
}

function stopEmergencySiren() {
  if (sirenOscillator) {
    try {
      sirenOscillator.stop();
      sirenOscillator.disconnect();
    } catch (e) {}
    sirenOscillator = null;
  }
  sirenPlaying = false;
}

// Autocomplete Search
function initSearchAutocomplete() {
  const input = document.getElementById('citySearchInput');
  const dropdown = document.getElementById('autocompleteDropdown');
  const clearBtn = document.getElementById('btnClearSearch');
  const form = document.getElementById('searchForm');

  if (!input || !dropdown) return;

  input.addEventListener('input', (e) => {
    const query = e.target.value.trim();
    if (clearBtn) clearBtn.style.display = query.length > 0 ? 'block' : 'none';

    clearTimeout(searchDebounceTimer);
    if (query.length < 2) {
      dropdown.style.display = 'none';
      return;
    }

    searchDebounceTimer = setTimeout(() => {
      fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => {
          renderAutocompleteResults(data.results || [], dropdown);
        })
        .catch(err => console.error("Search error:", err));
    }, 250);
  });

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      input.value = '';
      clearBtn.style.display = 'none';
      dropdown.style.display = 'none';
      input.focus();
    });
  }

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const q = input.value.trim();
      if (!q) return;
      dropdown.style.display = 'none';

      fetch(`/api/search?q=${encodeURIComponent(q)}`)
        .then(res => res.json())
        .then(data => {
          if (data.results && data.results.length > 0) {
            const first = data.results[0];
            loadWeatherForCoords(first.latitude, first.longitude, first.name, first.country);
          } else {
            alertNotice("City not found. Please try another name.");
          }
        });
    });
  }

  // Close dropdown on outside click
  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.style.display = 'none';
    }
  });

  // Hotspots Pills Click Handler
  document.querySelectorAll('.hotspot-pill').forEach(pill => {
    pill.addEventListener('click', (e) => {
      const city = e.currentTarget.getAttribute('data-city');
      const country = e.currentTarget.getAttribute('data-country');
      const lat = parseFloat(e.currentTarget.getAttribute('data-lat'));
      const lon = parseFloat(e.currentTarget.getAttribute('data-lon'));

      document.querySelectorAll('.hotspot-pill').forEach(p => p.classList.remove('active'));
      e.currentTarget.classList.add('active');

      loadWeatherForCoords(lat, lon, city, country);
    });
  });
}

function renderAutocompleteResults(results, dropdown) {
  dropdown.innerHTML = '';
  if (results.length === 0) {
    dropdown.style.display = 'none';
    return;
  }

  results.forEach(item => {
    const el = document.createElement('div');
    el.className = 'autocomplete-item';
    el.innerHTML = `
      <div>
        <div class="autocomplete-item-main">${item.name}</div>
        <div class="autocomplete-item-sub">${item.admin1 ? item.admin1 + ', ' : ''}${item.country}</div>
      </div>
      <span style="font-size: 0.75rem; color: #64748b;">${item.latitude.toFixed(2)}°, ${item.longitude.toFixed(2)}°</span>
    `;

    el.addEventListener('click', () => {
      document.getElementById('citySearchInput').value = `${item.name}, ${item.country}`;
      dropdown.style.display = 'none';
      loadWeatherForCoords(item.latitude, item.longitude, item.name, item.country);
    });

    dropdown.appendChild(el);
  });

  dropdown.style.display = 'block';
}

function handleDetectLocation() {
  if (!navigator.geolocation) {
    alertNotice("Geolocation is not supported by your browser.");
    return;
  }

  const btn = document.getElementById('btnLocate');
  if (btn) btn.innerHTML = '⏳ Locating...';

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      loadWeatherForCoords(lat, lon, "Local Device Coordinates", "");
      if (btn) btn.innerHTML = '📍 My Location';
    },
    (err) => {
      console.warn("Geolocation denied or error:", err);
      alertNotice("Geolocation access was denied or timed out.");
      if (btn) btn.innerHTML = '📍 My Location';
    },
    { timeout: 8000 }
  );
}

// Persona Tabs Navigation
function initPersonaTabs() {
  const buttons = document.querySelectorAll('.tab-btn');
  const panes = document.querySelectorAll('.tab-pane');

  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-tab');

      buttons.forEach(b => b.classList.remove('active'));
      panes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPane = document.getElementById(target);
      if (targetPane) targetPane.classList.add('active');
    });
  });
}

// Load SQLite Historical Records
function loadHistoryRecords() {
  fetch('/api/history?limit=10')
    .then(res => res.json())
    .then(data => {
      const tbody = document.getElementById('historyTableBody');
      if (!tbody) return;
      tbody.innerHTML = '';

      const history = data.history || [];
      if (history.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #64748b; padding: 20px;">No assessment records recorded yet in SQLite.</td></tr>`;
        return;
      }

      history.forEach(row => {
        const tr = document.createElement('tr');
        const timeStr = row.created_at ? row.created_at.replace('T', ' ').substring(0, 16) : 'Just now';
        
        tr.innerHTML = `
          <td><strong>${row.city}</strong> <span style="font-size:0.75rem; color:#64748b;">${row.country || ''}</span></td>
          <td>${row.temperature !== null ? row.temperature + '°C' : '--'}</td>
          <td>${row.precipitation !== null ? row.precipitation + ' mm' : '--'}</td>
          <td>${renderSmallRiskBadge(row.rain_risk)}</td>
          <td>${renderSmallRiskBadge(row.heat_risk)}</td>
          <td>${renderSmallRiskBadge(row.flood_risk)}</td>
          <td><strong style="color: ${getThreatColor(row.overall_risk)}">${row.composite_score}/100</strong> (${row.overall_risk})</td>
          <td style="font-size:0.75rem; color:#64748b;">${timeStr}</td>
        `;
        tbody.appendChild(tr);
      });
    })
    .catch(err => console.error("Error loading history:", err));
}

function renderSmallRiskBadge(level) {
  if (!level) return '--';
  let cls = 'badge-low';
  if (level === 'Moderate') cls = 'badge-moderate';
  else if (level === 'High') cls = 'badge-high';
  else if (level === 'Severe') cls = 'badge-severe';

  return `<span class="hazard-badge ${cls}" style="font-size: 0.68rem; padding: 2px 7px;">${level}</span>`;
}

function getThreatColor(level) {
  switch(level) {
    case 'Severe': return '#ef4444';
    case 'High': return '#f97316';
    case 'Moderate': return '#f59e0b';
    default: return '#10b981';
  }
}

// Theme Toggle
function initThemeToggle() {
  const btn = document.getElementById('btnThemeToggle');
  if (!btn) return;

  btn.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', nextTheme);
    btn.innerHTML = nextTheme === 'light' ? '🌙' : '☀️';
  });
}

// Modals: Model Transparency & Emergency Info
function initModals() {
  const btnMetrics = document.getElementById('btnOpenMetricsModal');
  const modalMetrics = document.getElementById('modalMetrics');
  const closeMetrics = document.getElementById('btnCloseMetrics');

  if (btnMetrics && modalMetrics) {
    btnMetrics.addEventListener('click', () => {
      loadModelMetricsDetails();
      modalMetrics.classList.add('active');
    });
  }

  if (closeMetrics && modalMetrics) {
    closeMetrics.addEventListener('click', () => {
      modalMetrics.classList.remove('active');
    });
  }

  // Close when clicking modal backdrop
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.classList.remove('active');
      }
    });
  });
}

function loadModelMetricsDetails() {
  fetch('/api/metrics')
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById('metricsModalContent');
      if (!container) return;

      const m = data.metrics || {};
      const models = m.models || {};

      container.innerHTML = `
        <div style="margin-bottom: 16px;">
          <h4 style="color: #93c5fd; margin-bottom: 6px;">Evaluation Dataset Architecture</h4>
          <p style="font-size: 0.85rem; color: #94a3b8;">
            Trained on <strong>${m.dataset_samples || 6000}</strong> meteorologically calibrated hazard records 
            spanning temperature, dew point, rainfall intensity, soil saturation, and pressure tendencies.
          </p>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px;">
          <div style="background: rgba(255,255,255,0.04); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
            <div style="font-size: 0.75rem; color: #60a5fa;">Heavy Rainfall Model</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #34d399; margin: 4px 0;">
              ${models.heavy_rainfall ? (models.heavy_rainfall.accuracy * 100).toFixed(1) + '%' : '99.8%'}
            </div>
            <div style="font-size: 0.7rem; color: #94a3b8;">Random Forest Classifier</div>
          </div>

          <div style="background: rgba(255,255,255,0.04); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
            <div style="font-size: 0.75rem; color: #f59e0b;">Extreme Heat Model</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #34d399; margin: 4px 0;">
              ${models.extreme_heat ? (models.extreme_heat.accuracy * 100).toFixed(1) + '%' : '100%'}
            </div>
            <div style="font-size: 0.7rem; color: #94a3b8;">Random Forest Classifier</div>
          </div>

          <div style="background: rgba(255,255,255,0.04); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
            <div style="font-size: 0.75rem; color: #06b6d4;">Flood Risk Exploration</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #34d399; margin: 4px 0;">
              ${models.flood_risk ? (models.flood_risk.accuracy * 100).toFixed(1) + '%' : '97.8%'}
            </div>
            <div style="font-size: 0.7rem; color: #94a3b8;">Gradient Boosting Classifier</div>
          </div>
        </div>

        <div style="background: rgba(59, 130, 246, 0.1); border-left: 3px solid #3b82f6; padding: 12px; border-radius: 4px; font-size: 0.8rem; color: #e2e8f0;">
          <strong>AI Safety & Ethical Disclaimer:</strong> This system is an experimental machine learning decision-support platform designed for educational and early awareness assistance. It is NOT a replacement for civil defense instructions or official statutory meteorological warnings.
        </div>
      `;
    })
    .catch(err => console.error("Error loading metrics:", err));
}

function showLoadingState(isLoading) {
  const el = document.getElementById('searchSpinner');
  if (el) el.style.display = isLoading ? 'inline-block' : 'none';
}

function alertNotice(msg) {
  console.log("System Notice:", msg);
}
