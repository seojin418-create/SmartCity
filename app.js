// app.js - Advanced GeoJSON Vector Map with Dong Filtering

const SONGPA_CENTER = [37.5145, 127.1050];
const ZOOM_LEVEL = 13;

const colorMap = {
  '단독주택': '#fcf4a3', '교육연구시설': '#00e5ff', '노유자시설': '#81d4fa',
  '운동시설': '#b39ddb', '업무시설': '#2962ff', '숙박시설': '#f50057',
  '위락시설': '#84ffff', '공동주택': '#ffb300', '자동차관련시설': '#651fff',
  '제1종근린생활시설': '#ffea00', '제2종근린생활시설': '#ffc400', '문화및집회시설': '#8c9eff',
  '기타': '#64748b'
};

// Use Canvas for high performance (30k+ polygons)
const map = L.map("map", {
  center: SONGPA_CENTER,
  zoom: ZOOM_LEVEL,
  zoomControl: false,
  preferCanvas: true
});

L.control.zoom({ position: 'bottomright' }).addTo(map);

// Light Base Map
const baseMap = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
  maxZoom: 19
}).addTo(map);

// State
let geojsonLayer = null;
let maskLayer = null;
let chartInstance = null;
let currentOpacity = 0.8;
let currentDong = "전체";
let currentTab = "주용도";

const tabPropertyMap = {
  '주용도': 'Category',
  '용도지역': 'Zoning',
  '지목': 'LandCategory'
};

function getRandomColor(str) {
  if (!str) return '#cccccc';
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  let color = '#';
  for (let i = 0; i < 3; i++) {
    let value = (hash >> (i * 8)) & 0xFF;
    color += ('00' + value.toString(16)).substr(-2);
  }
  return color;
}

const tooltipEl = document.getElementById('map-tooltip');

// Track mouse position for tooltip
document.addEventListener('mousemove', (e) => {
  if (!tooltipEl.classList.contains('hidden')) {
    tooltipEl.style.left = e.clientX + 'px';
    tooltipEl.style.top = e.clientY + 'px';
  }
});

function init() {
  try {
    // 1. Boundary Masking using 'boundaryData' loaded via <script>
    if (typeof boundaryData !== 'undefined') {
      const worldPoly = turf.polygon([[[-180,-90], [180,-90], [180,90], [-180,90], [-180,-90]]]);
      const mask = turf.difference(worldPoly, boundaryData.features[0]);
      
      // Draw Red Line for boundary
      L.geoJSON(boundaryData, {
        style: { color: '#ff2a2a', weight: 3, fillOpacity: 0 },
        interactive: false
      }).addTo(map);

      maskLayer = L.geoJSON(mask, {
        style: { fillColor: '#000000', fillOpacity: 0.7, color: 'transparent', weight: 0 },
        interactive: false
      }).addTo(map);
    }

    // 2. Load Vector Parcels using 'parcelData' loaded via <script>
    if (typeof parcelData !== 'undefined') {
      setupDongSelector(parcelData.features);
      renderData(currentDong);
    } else {
      console.error("parcelData is not defined. Ensure data_parcels.js is loaded.");
    }

    setupControls();

  } catch (err) {
    console.error("Initialization error:", err);
  }
}

function setupDongSelector(features) {
  const dongs = new Set();
  features.forEach(f => {
    if (f.properties.Dong) dongs.add(f.properties.Dong);
  });

  const selector = document.getElementById('dong-selector');
  const sortedDongs = Array.from(dongs).sort();
  
  sortedDongs.forEach(dong => {
    const opt = document.createElement('option');
    opt.value = dong;
    opt.textContent = dong;
    selector.appendChild(opt);
  });

  selector.addEventListener('change', (e) => {
    currentDong = e.target.value;
    renderData(currentDong);
  });
}

function renderData(selectedDong) {
  // Filter Data
  const features = parcelData.features.filter(f => {
    return selectedDong === "전체" || f.properties.Dong === selectedDong;
  });

  // Calculate Stats
  const propName = tabPropertyMap[currentTab] || 'Category';
  const stats = {};
  let totalParcels = 0;
  let totalArea = 0;

  features.forEach(f => {
    const p = f.properties;
    const val = p[propName] || '기타';
    const area = p.Area || 0;
    
    if (!stats[val]) {
      stats[val] = { Area: 0, Parcels: 0, Color: colorMap[val] || getRandomColor(val) };
    }
    stats[val].Area += area;
    stats[val].Parcels += 1;
    totalParcels++;
    totalArea += area;
  });

  const statsArr = Object.entries(stats)
    .map(([cat, val]) => ({ Category: cat, ...val }))
    .sort((a, b) => b.Area - a.Area);

  statsArr.forEach(s => {
    s.Ratio = ((s.Area / totalArea) * 100).toFixed(1);
  });

  updateUI(statsArr, totalParcels, totalArea);

  // Update Map
  if (geojsonLayer) {
    map.removeLayer(geojsonLayer);
  }

  geojsonLayer = L.geoJSON(features, {
    style: function(feature) {
      const val = feature.properties[propName] || '기타';
      return {
        fillColor: colorMap[val] || getRandomColor(val),
        fillOpacity: currentOpacity,
        color: 'transparent',
        weight: 0
      };
    },
    onEachFeature: function(feature, layer) {
      layer.on({
        mouseover: (e) => {
          const p = feature.properties;
          tooltipEl.innerHTML = `
            필지: <span class="tooltip-highlight">${p.PNU}</span><br/>
            법정동: ${p.Dong}<br/>
            주용도: <span class="tooltip-highlight">${p.Category || '-'}</span><br/>
            용도지역: <span class="tooltip-highlight">${p.Zoning || '-'}</span><br/>
            지목: <span class="tooltip-highlight">${p.LandCategory || '-'}</span><br/>
            연면적: ${Math.round(p.Area).toLocaleString()} m²
          `;
          tooltipEl.classList.remove('hidden');
          
          layer.setStyle({ color: '#ffffff', weight: 2 });
          layer.bringToFront();
        },
        mouseout: (e) => {
          tooltipEl.classList.add('hidden');
          geojsonLayer.resetStyle(layer);
        }
      });
    }
  }).addTo(map);
  
  // Optionally fit bounds to the selected dong
  if (selectedDong !== "전체" && geojsonLayer.getBounds().isValid()) {
    map.fitBounds(geojsonLayer.getBounds(), { padding: [50, 50] });
  } else if (selectedDong === "전체") {
    map.setView(SONGPA_CENTER, ZOOM_LEVEL);
  }
}

function updateUI(stats, totalParcels, totalArea) {
  // Summary
  document.getElementById('total-parcels').textContent = `${totalParcels.toLocaleString()} 필지`;
  document.getElementById('total-area').textContent = `${Math.round(totalArea).toLocaleString()} m² 연면적`;

  // Left Legend
  const legendBox = document.getElementById('legend-container');
  legendBox.innerHTML = '';
  
  // Table
  const tbody = document.getElementById('table-body');
  tbody.innerHTML = '';

  stats.forEach(s => {
    // Legend
    const div = document.createElement('div');
    div.className = 'legend-item';
    div.innerHTML = `
      <div style="display:flex; align-items:center;">
        <span class="legend-color-box" style="background-color: ${s.Color};"></span>
        <span class="legend-label">${s.Category}</span>
      </div>
      <span class="legend-value">${s.Ratio}%</span>
    `;
    legendBox.appendChild(div);

    // Table
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="legend-td"><span class="legend-color-box" style="background-color: ${s.Color};"></span>${s.Category}</td>
      <td>${s.Parcels.toLocaleString()}</td>
      <td>${Math.round(s.Area).toLocaleString()}</td>
      <td>${s.Ratio}%</td>
    `;
    tbody.appendChild(tr);
  });

  // Chart
  const ctx = document.getElementById('pie-chart').getContext('2d');
  
  if (chartInstance) {
    chartInstance.destroy();
  }

  // Center Text Plugin
  const centerTextPlugin = {
    id: 'centerText',
    beforeDraw: function(chart) {
      if (chart.config.data.datasets.length > 0 && stats.length > 0) {
        const ctx = chart.ctx;
        ctx.save();
        const width = chart.width;
        const height = chart.height;
        const text1 = stats[0].Category;
        const text2 = stats[0].Ratio + '%';
        
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        ctx.fillStyle = '#e2e8f0';
        ctx.font = '500 14px Pretendard';
        ctx.fillText(text1, width / 2, height / 2 - 10);
        
        ctx.fillStyle = '#94a3b8';
        ctx.font = '400 12px Pretendard';
        ctx.fillText(text2, width / 2, height / 2 + 10);
        
        ctx.restore();
      }
    }
  };

  chartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: stats.map(s => s.Category),
      datasets: [{
        data: stats.map(s => s.Area),
        backgroundColor: stats.map(s => s.Color),
        borderWidth: 0,
        cutout: '70%'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => {
              const row = stats[context.dataIndex];
              return `${row.Category}: ${row.Ratio}%`;
            }
          }
        }
      }
    },
    plugins: [centerTextPlugin]
  });
}

function setupControls() {
  const slider = document.getElementById('opacity-slider');
  const valLabel = document.getElementById('opacity-val');
  
  slider.addEventListener('input', (e) => {
    const val = e.target.value;
    valLabel.textContent = `${val}%`;
    currentOpacity = val / 100;
    
    if (geojsonLayer) {
      geojsonLayer.setStyle(() => ({
        fillOpacity: currentOpacity
      }));
    }
  });

  document.getElementById('chk-boundary').addEventListener('change', (e) => {
    if (e.target.checked) maskLayer.addTo(map);
    else map.removeLayer(maskLayer);
  });

  document.getElementById('chk-parcels').addEventListener('change', (e) => {
    if (e.target.checked) geojsonLayer.addTo(map);
    else map.removeLayer(geojsonLayer);
  });

  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      tabs.forEach(t => t.classList.remove('active'));
      e.target.classList.add('active');
      currentTab = e.target.textContent.trim();
      renderData(currentDong);
    });
  });
}

// Start
init();
