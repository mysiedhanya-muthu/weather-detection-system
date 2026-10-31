/**
 * Disaster Simulation Sandbox ("What-If" Scenario Simulator)
 * Allows users and evaluators to interactively slide meteorological values
 * and observe the Scikit-learn AI model evaluate risk transitions in real-time.
 */

let simulationDebounceTimer = null;

function initSimulator() {
  const tempSlider = document.getElementById('simTemp');
  const humiditySlider = document.getElementById('simHumidity');
  const precipSlider = document.getElementById('simPrecip');
  const windSlider = document.getElementById('simWind');

  if (!tempSlider) return;

  // Bind input events to update displayed badge and trigger simulation
  [tempSlider, humiditySlider, precipSlider, windSlider].forEach(slider => {
    slider.addEventListener('input', () => {
      updateSliderBadges();
      triggerDebouncedSimulation();
    });
  });

  // Preset buttons
  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const preset = e.target.getAttribute('data-preset');
      applySimulatorPreset(preset);
    });
  });

  // Run initial simulation
  updateSliderBadges();
  runSimulation();
}

function updateSliderBadges() {
  const temp = document.getElementById('simTemp').value;
  const humidity = document.getElementById('simHumidity').value;
  const precip = document.getElementById('simPrecip').value;
  const wind = document.getElementById('simWind').value;

  document.getElementById('simTempVal').textContent = `${temp} °C`;
  document.getElementById('simHumidityVal').textContent = `${humidity} %`;
  document.getElementById('simPrecipVal').textContent = `${precip} mm`;
  document.getElementById('simWindVal').textContent = `${wind} km/h`;
}

function applySimulatorPreset(preset) {
  const t = document.getElementById('simTemp');
  const h = document.getElementById('simHumidity');
  const p = document.getElementById('simPrecip');
  const w = document.getElementById('simWind');

  if (preset === 'heatwave') {
    t.value = 43; h.value = 45; p.value = 0; w.value = 18;
  } else if (preset === 'monsoon') {
    t.value = 28; h.value = 95; p.value = 145; w.value = 42;
  } else if (preset === 'cyclone') {
    t.value = 25; h.value = 90; p.value = 110; w.value = 115;
  } else if (preset === 'calm') {
    t.value = 22; h.value = 50; p.value = 2; w.value = 15;
  }

  updateSliderBadges();
  runSimulation();
}

function triggerDebouncedSimulation() {
  clearTimeout(simulationDebounceTimer);
  simulationDebounceTimer = setTimeout(() => {
    runSimulation();
  }, 180);
}

function runSimulation() {
  const temp = parseFloat(document.getElementById('simTemp').value);
  const humidity = parseFloat(document.getElementById('simHumidity').value);
  const precip = parseFloat(document.getElementById('simPrecip').value);
  const wind = parseFloat(document.getElementById('simWind').value);

  const payload = {
    temperature: temp,
    humidity: humidity,
    precipitation: precip,
    wind_gusts: wind,
    pressure: 1013 - (precip * 0.1)
  };

  fetch('/api/simulate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success') {
        renderSimulationResults(data.prediction);
      }
    })
    .catch(err => console.error("Simulation error:", err));
}

function renderSimulationResults(pred) {
  const scoreElem = document.getElementById('simScoreNum');
  const levelElem = document.getElementById('simRiskLevel');
  const circleElem = document.getElementById('simScoreCircle');
  const rainBadge = document.getElementById('simRainBadge');
  const heatBadge = document.getElementById('simHeatBadge');
  const floodBadge = document.getElementById('simFloodBadge');
  const explainElem = document.getElementById('simExplanation');

  if (scoreElem) scoreElem.textContent = pred.composite_score;
  if (levelElem) {
    levelElem.textContent = `${pred.overall_risk} Risk`;
    levelElem.style.color = pred.risk_color;
  }
  if (circleElem) {
    circleElem.style.borderColor = pred.risk_color;
    circleElem.style.boxShadow = `0 0 20px ${pred.risk_color}40`;
  }

  updateBadgeClass(rainBadge, pred.rain_risk);
  updateBadgeClass(heatBadge, pred.heat_risk);
  updateBadgeClass(floodBadge, pred.flood_risk);

  if (explainElem) {
    explainElem.textContent = pred.explanation;
  }
}

function updateBadgeClass(elem, risk) {
  if (!elem) return;
  elem.textContent = risk;
  elem.className = 'hazard-badge';
  if (risk === 'Low') elem.classList.add('badge-low');
  else if (risk === 'Moderate') elem.classList.add('badge-moderate');
  else if (risk === 'High') elem.classList.add('badge-high');
  else elem.classList.add('badge-severe');
}

document.addEventListener('DOMContentLoaded', initSimulator);
