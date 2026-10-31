/**
 * Chart.js Visualizations for AI Weather Disaster Early Warning System
 */

let hourlyChartInstance = null;
let trendChartInstance = null;

function initCharts() {
  const chartFont = {
    family: "'Inter', sans-serif",
    size: 11
  };
  Chart.defaults.color = '#94a3b8';
  Chart.defaults.font = chartFont;
}

function updateHourlyChart(hourlyData) {
  const ctx = document.getElementById('hourlyForecastChart');
  if (!ctx || !hourlyData || hourlyData.length === 0) return;

  const labels = hourlyData.map(h => h.time);
  const temps = hourlyData.map(h => h.temp);
  const precips = hourlyData.map(h => h.precip);

  if (hourlyChartInstance) {
    hourlyChartInstance.destroy();
  }

  hourlyChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Temperature (°C)',
          data: temps,
          borderColor: '#38bdf8',
          backgroundColor: 'rgba(56, 189, 248, 0.1)',
          fill: true,
          tension: 0.4,
          yAxisID: 'y'
        },
        {
          label: 'Precipitation (mm)',
          data: precips,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.5)',
          type: 'bar',
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          position: 'top',
          labels: { boxWidth: 12, color: '#cbd5e1' }
        },
        tooltip: {
          backgroundColor: '#111827',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          padding: 10
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { maxTicksLimit: 8 }
        },
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          title: { display: true, text: 'Temp (°C)', color: '#38bdf8' }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          grid: { drawOnChartArea: false },
          title: { display: true, text: 'Precip (mm)', color: '#3b82f6' }
        }
      }
    }
  });
}

function updateWeeklyTrendChart(dailyData) {
  const ctx = document.getElementById('dailyTrendChart');
  if (!ctx || !dailyData || dailyData.length === 0) return;

  const labels = dailyData.map(d => {
    const parts = d.date.split('-');
    return `${parts[1]}/${parts[2]}`;
  });
  const maxTemps = dailyData.map(d => d.temp_max);
  const minTemps = dailyData.map(d => d.temp_min);
  const precipSums = dailyData.map(d => d.precip_sum);

  if (trendChartInstance) {
    trendChartInstance.destroy();
  }

  trendChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Max Temp (°C)',
          data: maxTemps,
          backgroundColor: '#f59e0b',
          borderRadius: 4
        },
        {
          label: 'Min Temp (°C)',
          data: minTemps,
          backgroundColor: '#60a5fa',
          borderRadius: 4
        },
        {
          label: 'Rain Total (mm)',
          data: precipSums,
          backgroundColor: '#06b6d4',
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { boxWidth: 12, color: '#cbd5e1' }
        },
        tooltip: {
          backgroundColor: '#111827',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1
        }
      },
      scales: {
        x: { grid: { color: 'rgba(255, 255, 255, 0.05)' } },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          title: { display: true, text: 'Values (°C / mm)' }
        }
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', initCharts);
