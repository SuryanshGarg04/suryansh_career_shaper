// Comprehensive Logistics & Fleet Management Platform (P-194)
// Dispatcher Console JavaScript Engine

let map;
let markers = {};
let hubMarkers = {};
let socket;
let eventCount = 0;

// Hub reference nodes
const HUBS = [
  { id: "HUB_DEL", name: "Delhi Hub", lat: 28.6139, lon: 77.2090 },
  { id: "HUB_BOM", name: "Mumbai Hub", lat: 19.0760, lon: 72.8777 },
  { id: "HUB_BLR", name: "Bengaluru Hub", lat: 12.9716, lon: 77.5946 },
  { id: "HUB_HYD", name: "Hyderabad Hub", lat: 17.3850, lon: 78.4867 },
  { id: "HUB_CCU", name: "Kolkata Hub", lat: 22.5726, lon: 88.3639 },
  { id: "HUB_MAA", name: "Chennai Hub", lat: 13.0827, lon: 80.2707 },
  { id: "HUB_AMD", name: "Ahmedabad Hub", lat: 23.0225, lon: 72.5714 },
  { id: "HUB_PNQ", name: "Pune Hub", lat: 18.5204, lon: 73.8567 },
  { id: "HUB_JAI", name: "Jaipur Hub", lat: 26.9124, lon: 75.7873 },
  { id: "HUB_LKO", name: "Lucknow Hub", lat: 26.8467, lon: 80.9462 }
];

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  initWebSocket();
  fetchAnalytics();
  fetchShipments();
  fetchActiveVehicles();

  // Periodic polling fallback
  setInterval(fetchAnalytics, 5000);
  setInterval(fetchShipments, 8000);
});

function initMap() {
  map = L.map('map').setView([21.7679, 78.8718], 5); // Centered on India

  // Dark CartoDB Tiles
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap & CartoDB',
    maxZoom: 18
  }).addTo(map);

  // Plot Logistics Hubs
  HUBS.forEach(hub => {
    const hubIcon = L.divIcon({
      className: 'custom-hub-icon',
      iconSize: [14, 14],
      iconAnchor: [7, 7]
    });

    const marker = L.marker([hub.lat, hub.lon], { icon: hubIcon })
      .bindPopup(`<strong class="text-slate-900">${hub.name} (${hub.id})</strong><br/><span class="text-xs text-slate-700">Distribution Node</span>`)
      .addTo(map);

    hubMarkers[hub.id] = marker;
  });
}

function resetMapView() {
  map.setView([21.7679, 78.8718], 5);
}

function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    document.getElementById('ws-badge').innerHTML = `
      <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
      WebSocket Live
    `;
    document.getElementById('ws-badge').className = "flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-500/30";
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    } catch (e) {
      console.error("Error parsing WS message:", e);
    }
  };

  socket.onclose = () => {
    document.getElementById('ws-badge').innerHTML = `
      <span class="w-2 h-2 rounded-full bg-amber-400"></span>
      Reconnecting...
    `;
    document.getElementById('ws-badge').className = "flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-amber-950/80 text-amber-400 border border-amber-500/30";
    setTimeout(initWebSocket, 3000);
  };
}

function handleWebSocketMessage(msg) {
  eventCount++;
  document.getElementById('feed-count').innerText = `${eventCount} events`;

  if (msg.type === "TELEMETRY_PING") {
    updateVehicleMarker(msg.vehicle_id, msg.lat, msg.lon, msg.speed, msg.fuel, msg.anomaly);
    logEvent(`📍 <strong>${msg.vehicle_id}</strong> ping: ${msg.speed} km/h, Fuel ${msg.fuel}%`, msg.anomaly);
  } else if (msg.type === "SHIPMENT_CREATED") {
    logEvent(`📦 New shipment <strong>${msg.shipment_id}</strong> (${msg.origin} &rarr; ${msg.dest})`, "None");
    fetchShipments();
    fetchAnalytics();
  } else if (msg.type === "SHIPMENT_ASSIGNED") {
    logEvent(`🚚 Vehicle <strong>${msg.vehicle_id}</strong> assigned to <strong>${msg.shipment_id}</strong>`, "None");
    fetchShipments();
    fetchAnalytics();
  } else if (msg.type === "SHIPMENT_TRANSITIONED") {
    logEvent(`🔄 <strong>${msg.shipment_id}</strong> transitioned to <strong>${msg.new_status}</strong>`, "None");
    fetchShipments();
    fetchAnalytics();
  }
}

function updateVehicleMarker(vehicleId, lat, lon, speed, fuel, anomaly) {
  let isAnomaly = anomaly && anomaly !== "None";
  let color = isAnomaly ? '#ef4444' : '#10b981';

  if (!markers[vehicleId]) {
    const vIcon = L.divIcon({
      className: 'custom-vehicle-icon',
      html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid #fff;"></div>`,
      iconSize: [12, 12],
      iconAnchor: [6, 6]
    });

    const marker = L.marker([lat, lon], { icon: vIcon })
      .bindPopup(`
        <div class="text-slate-900 text-xs">
          <strong>${vehicleId}</strong><br/>
          Speed: ${speed} km/h<br/>
          Fuel: ${fuel}%<br/>
          Status: ${isAnomaly ? `<span class="text-red-600 font-bold">${anomaly}</span>` : 'Normal'}
        </div>
      `)
      .addTo(map);

    markers[vehicleId] = marker;
  } else {
    markers[vehicleId].setLatLng([lat, lon]);
    markers[vehicleId].setPopupContent(`
      <div class="text-slate-900 text-xs">
        <strong>${vehicleId}</strong><br/>
        Speed: ${speed} km/h<br/>
        Fuel: ${fuel}%<br/>
        Status: ${isAnomaly ? `<span class="text-red-600 font-bold">${anomaly}</span>` : 'Normal'}
      </div>
    `);
  }
}

function logEvent(html, anomaly) {
  const feed = document.getElementById('alert-feed');
  const now = new Date().toLocaleTimeString();
  const isAnomaly = anomaly && anomaly !== "None";

  const item = document.createElement('div');
  item.className = `p-2.5 rounded-lg border ${
    isAnomaly
      ? 'bg-red-950/40 border-red-500/40 text-red-200'
      : 'bg-slate-900/60 border-slate-700/60 text-slate-300'
  } flex items-start justify-between gap-2 transition-all`;

  item.innerHTML = `
    <div>
      <div>${html}</div>
      ${isAnomaly ? `<div class="text-[11px] font-semibold text-red-400 mt-0.5">⚠️ Alert: ${anomaly}</div>` : ''}
    </div>
    <span class="text-[10px] text-slate-500 whitespace-nowrap font-mono">${now}</span>
  `;

  if (feed.children.length === 1 && feed.children[0].innerText.includes("Waiting")) {
    feed.innerHTML = '';
  }

  feed.insertBefore(item, feed.firstChild);
  if (feed.children.length > 50) {
    feed.removeChild(feed.lastChild);
  }
}

async function fetchAnalytics() {
  try {
    const res = await fetch('/api/v1/analytics/overview');
    const data = await res.json();
    document.getElementById('stat-vehicles').innerText = data.fleet_status.total_vehicles || 250;
    document.getElementById('stat-transit').innerText = data.shipment_pipeline.IN_TRANSIT || 0;

    const slaRes = await fetch('/api/v1/analytics/sla');
    const slaData = await slaRes.json();
    document.getElementById('stat-sla').innerText = `${slaData.sla_compliance_pct}%`;

    const anomaliesCount = Object.values(data.telemetry_stats.active_anomalies_flagged).reduce((a, b) => a + b, 0);
    document.getElementById('stat-anomalies').innerText = `${anomaliesCount} active exceptions`;
  } catch (e) {
    console.error("Error fetching analytics:", e);
  }
}

async function fetchActiveVehicles() {
  try {
    const res = await fetch('/api/v1/telemetry/active');
    const active = await res.json();
    for (const [vehId, data] of Object.entries(active)) {
      updateVehicleMarker(vehId, data.latitude, data.longitude, data.speed_kmh, data.fuel_pct, data.anomaly_flag);
    }
  } catch (e) {
    console.error("Error fetching active telemetry:", e);
  }
}

async function fetchShipments() {
  try {
    const res = await fetch('/api/v1/shipments/?limit=20');
    const shipments = await res.json();
    renderShipmentTable(shipments);
  } catch (e) {
    console.error("Error fetching shipments:", e);
  }
}

function renderShipmentTable(shipments) {
  const tbody = document.getElementById('shipment-tbody');
  if (!shipments || shipments.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-slate-500 italic">No shipments registered yet. Click '+ Create New Shipment' above.</td></tr>`;
    return;
  }

  tbody.innerHTML = shipments.map(s => {
    let statusClass = "bg-slate-700 text-slate-300";
    if (s.status === "CREATED") statusClass = "bg-blue-950 text-blue-300 border border-blue-500/30";
    else if (s.status === "ASSIGNED") statusClass = "bg-purple-950 text-purple-300 border border-purple-500/30";
    else if (s.status === "IN_TRANSIT") statusClass = "bg-amber-950 text-amber-300 border border-amber-500/30";
    else if (s.status === "OUT_FOR_DELIVERY") statusClass = "bg-teal-950 text-teal-300 border border-teal-500/30";
    else if (s.status === "DELIVERED") statusClass = "bg-emerald-950 text-emerald-300 border border-emerald-500/30";
    else if (s.status === "EXCEPTION_FLAGGED") statusClass = "bg-red-950 text-red-300 border border-red-500/30";

    let actionBtn = "";
    if (s.status === "CREATED") {
      actionBtn = `<button onclick="autoAssignVehicle('${s.shipment_id}')" class="px-2 py-1 bg-purple-700 hover:bg-purple-600 rounded text-[11px] text-white">Auto-Assign</button>`;
    } else if (s.status === "ASSIGNED") {
      actionBtn = `<button onclick="transitionShipment('${s.shipment_id}', 'IN_TRANSIT')" class="px-2 py-1 bg-amber-700 hover:bg-amber-600 rounded text-[11px] text-white">Dispatch</button>`;
    } else if (s.status === "IN_TRANSIT") {
      actionBtn = `<button onclick="transitionShipment('${s.shipment_id}', 'DELIVERED')" class="px-2 py-1 bg-emerald-700 hover:bg-emerald-600 rounded text-[11px] text-white">Deliver</button>`;
    } else {
      actionBtn = `<span class="text-slate-500 text-[11px]">—</span>`;
    }

    return `
      <tr class="hover:bg-slate-800/50 transition">
        <td class="py-3 px-4 font-mono font-medium text-purple-400">${s.shipment_id}</td>
        <td class="py-3 px-4">${s.origin_hub_id}</td>
        <td class="py-3 px-4">${s.dest_hub_id}</td>
        <td class="py-3 px-4">${s.weight_kg.toLocaleString()} kg</td>
        <td class="py-3 px-4 font-mono">${s.assigned_vehicle_id || '<span class="text-slate-500 italic">Unassigned</span>'}</td>
        <td class="py-3 px-4"><span class="px-2 py-0.5 rounded-full text-[10px] font-semibold ${statusClass}">${s.status}</span></td>
        <td class="py-3 px-4">${s.current_eta_mins > 0 ? `${s.current_eta_mins} mins` : '—'}</td>
        <td class="py-3 px-4 text-right">${actionBtn}</td>
      </tr>
    `;
  }).join('');
}

function showCreateModal() {
  document.getElementById('create-modal').classList.remove('hidden');
  document.getElementById('create-modal').classList.add('flex');
}

function hideCreateModal() {
  document.getElementById('create-modal').classList.add('hidden');
  document.getElementById('create-modal').classList.remove('flex');
}

async function handleCreateShipment(e) {
  e.preventDefault();
  const payload = {
    origin_hub_id: document.getElementById('input-origin').value,
    dest_hub_id: document.getElementById('input-dest').value,
    weight_kg: parseFloat(document.getElementById('input-weight').value),
    priority: document.getElementById('input-priority').value
  };

  try {
    const res = await fetch('/api/v1/shipments/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      hideCreateModal();
      fetchShipments();
    } else {
      const err = await res.json();
      alert(`Error: ${err.detail || 'Failed to create shipment'}`);
    }
  } catch (err) {
    console.error(err);
  }
}

async function autoAssignVehicle(shipmentId) {
  try {
    const res = await fetch(`/api/v1/shipments/${shipmentId}/assign?auto_find=true`, {
      method: 'POST'
    });
    if (res.ok) {
      fetchShipments();
    } else {
      const err = await res.json();
      alert(`Dispatch Error: ${err.detail}`);
    }
  } catch (err) {
    console.error(err);
  }
}

async function transitionShipment(shipmentId, newStatus) {
  try {
    const res = await fetch(`/api/v1/shipments/${shipmentId}/transition`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_status: newStatus })
    });
    if (res.ok) {
      fetchShipments();
    } else {
      const err = await res.json();
      alert(`FSM Error: ${err.detail}`);
    }
  } catch (err) {
    console.error(err);
  }
}

async function simulateSinglePing() {
  const vehIndex = Math.floor(Math.random() * 50) + 1;
  const vehId = `VEH${String(vehIndex).padStart(3, '0')}`;
  const randomHub = HUBS[Math.floor(Math.random() * HUBS.length)];
  const latOffset = (Math.random() - 0.5) * 1.5;
  const lonOffset = (Math.random() - 0.5) * 1.5;

  const ping = {
    vehicle_id: vehId,
    latitude: randomHub.lat + latOffset,
    longitude: randomHub.lon + lonOffset,
    speed_kmh: Math.round(Math.random() * 50 + 35),
    fuel_pct: Math.round(Math.random() * 80 + 15)
  };

  try {
    await fetch('/api/v1/telemetry/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ping)
    });
  } catch (e) {
    console.error("Error sending simulated ping:", e);
  }
}
