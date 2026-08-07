const role = localStorage.getItem("role");
const username = localStorage.getItem("username");
const welcome = document.getElementById("welcomeUser");

if (welcome && username) {
    welcome.innerHTML = `Welcome, ${username} 👋`;
}

if (!role || role !== "admin") {
    alert("Access denied! Admin only.");
    window.location.href = "login.html";
}

const map = L.map('map').setView([17.3850, 78.4867], 7);

// ===============================
// LOGOUT
// ===============================
function logout() {
    localStorage.removeItem("role");
    localStorage.removeItem("username");
    window.location.href = "login.html";
}

// ===============================
// OPENSTREETMAP
// ===============================
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// ===============================
// ICONS
// ===============================
const lowIcon = L.icon({
    iconUrl: 'images/low.png',
    iconSize: [35, 35]
});

const mediumIcon = L.icon({
    iconUrl: 'images/medium.png',
    iconSize: [35, 35]
});

const highIcon = L.icon({
    iconUrl: 'images/high.png',
    iconSize: [35, 35]
});

const criticalIcon = L.icon({
    iconUrl: 'images/critical.png',
    iconSize: [35, 35]
});

const severityIcons = {
    low: lowIcon,
    medium: mediumIcon,
    high: highIcon,
    critical: criticalIcon
};

function mapSeverity(ndmaSeverity) {

    const severity = (ndmaSeverity || "").toLowerCase();

    switch (severity) {

        case "extreme":
            return "critical";

        case "severe":
            return "high";

        case "moderate":
            return "medium";

        case "minor":
            return "low";

        case "critical":
            return "critical";

        case "high":
            return "high";

        case "medium":
            return "medium";

        case "low":
            return "low";

        default:
            return "low";
    }
}

// ===============================
// MARKERS
// ===============================
const markers = [];

// ===============================
// FILTER
// ===============================
let currentFilter = "all";

// ===============================
// SIDEBAR
// ===============================
function updateSidebar(data) {

    const sidebar = document.querySelector(".sidebar-list");
    if (!sidebar) return;

    sidebar.innerHTML = "";

    data.forEach(alert => {

        const item = document.createElement("div");
        item.className = "sidebar-item";

        item.innerHTML = `
            <b>${alert.type || "Unknown"}</b>
            <span> - ${(alert.location || "").toUpperCase()}</span>
        `;

        item.addEventListener("click", () => {

            const lat = alert.latitude;
            const lng = alert.longitude;

            if (lat && lng) {
                map.setView([lat, lng], 10);

                const found = markers.find(m => m.id === alert.id);

                if (found) {
                    found.marker.openPopup();
                }
            }
        });

        sidebar.appendChild(item);
    });
}

// ===============================
// CLOCK
// ===============================
function updateClock() {
    const now = new Date();
    document.getElementById("clock").innerText = now.toLocaleTimeString();
}

updateClock();
setInterval(updateClock, 1000);

// ===============================
// REFRESH UI
// ===============================
function refreshUI() {

    fetch("https://disaster-alert-system-yqp3.onrender.com/alerts")
        .then(res => res.json())
        .then(data => {

            // FILTER
            if (currentFilter !== "all") {
                data = data.filter(alert => {
                    return (
                        (alert.type || "").toLowerCase() === currentFilter ||
                        mapSeverity(alert.severity) === currentFilter
                    );
                });
            }

            // CLEAR MARKERS
            markers.forEach(m => map.removeLayer(m.marker));
            markers.length = 0;

            let total = 0;
            let critical = 0;

            data.forEach(alert => {

                total++;

                if ((alert.severity || "").toLowerCase() === "critical") {
                    critical++;
                }

                const lat = alert.latitude;
                const lng = alert.longitude;

                if (!lat || !lng) return;

                const severity = mapSeverity(alert.severity);

                let icon = severityIcons[severity];

                const marker = L.marker([lat, lng], { icon })
                    .addTo(map)
                    .bindPopup(`
                         <div style="min-width:200px">

                        <h3>${alert.type} Alert</h3>
                        <p>📍 ${alert.location}</p>
                        <p><b>Severity:</b> ${alert.severity}</p>

                        <button onclick="deleteAlert(${alert.id})"
                         style="background:red;color:white;padding:5px;margin-top:5px;cursor:pointer;">
                         Delete
                        </button>

                        </div>
                    `);

                markers.push({
                    id: alert.id,
                    marker
                });
            });

            // STATS
            const statsBox = document.querySelector(".sidebar-stats");
            if (statsBox) {
                statsBox.innerHTML = `
                    <p>Total Alerts: <span>${total}</span></p>
                    <p>Critical Alerts: <span>${critical}</span></p>
                    <p>Safe Zones: <span>12</span></p>
                `;
            }

            updateSidebar(data);

        })
        .catch(error => {
            console.error("Failed to load alerts:", error);
        });
}

// ===============================
// FILTER BUTTONS (SAFE)
// ===============================
const filters = [
    ["allFilter", "all"],
    ["criticalFilter", "critical"],
    ["HighFilter", "high"],
    ["mediumFilter", "medium"],
    ["lowFilter", "low"]
];

filters.forEach(([id, value]) => {
    const btn = document.getElementById(id);
    if (btn) {
        btn.addEventListener("click", () => {
            currentFilter = value;
            refreshUI();
        });
    }
});

// ===============================
// ADD ALERT (ADMIN ONLY)
// ===============================
const addBtn = document.getElementById("addAlertBtn");

if (addBtn) {
    addBtn.addEventListener("click", () => {

        const type = document.getElementById("alertType").value;
        const location = document.getElementById("alertLocation").value;
        const severity = document.getElementById("alertSeverity").value;

        if (!type || !location || !severity) {
            alert("Please fill all fields.");
            return;
        }

        fetch("https://disaster-alert-system-yqp3.onrender.com/alerts", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ type, location, severity })
        })
        .then(res => res.json())
        .then(result => {
            alert(result.message);
            refreshUI();
        })
       .catch(error => {
            console.error(error);
        });
    });
}


function deleteAlert(id) {

    fetch(`https://disaster-alert-system-yqp3.onrender.com/alerts/${id}`, {
        method: "DELETE"
    })
    .then(res => res.json())
    .then(result => {
        alert(result.message);
        refreshUI();   // refresh map instantly
    })
    .catch(error => {
        console.error(error);
    });
}
// ===============================
// INIT
// ===============================
refreshUI();
setInterval(refreshUI, 5000);

