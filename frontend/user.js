
const role = localStorage.getItem("role");
const username = localStorage.getItem("username");
const welcome = document.getElementById("welcomeUser");

if (welcome && username) {
    welcome.innerHTML = `Welcome, ${username} 👋`;
}

const alarmSound = new Audio("sounds/alarm.mp3");

let lastAlertId = 0;

// ===============================
// REQUEST BROWSER NOTIFICATION PERMISSION
// ===============================

if ("Notification" in window) {
    Notification.requestPermission();
}

if (!role) {
    alert("Please login first");
    window.location.href = "login.html";
}

const map = L.map('map').setView([17.3850, 78.4867], 7);

function logout() {
    localStorage.removeItem("role");
    localStorage.removeItem("username");
    window.location.href = "login.html";
}

// ===============================
// OPENSTREETMAP LAYER
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
// MARKERS STORE
// ===============================
const markers = [];

// ===============================
// FILTER
// ===============================
let currentFilter = "all";

// Store previous alert count
let previousAlertCount = 0;

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
// REFRESH MAP
// ===============================
function refreshUI() {

    fetch("https://disaster-alert-system-yqp3.onrender.com/alerts")
        .then(res => res.json())
        .then(data => {


// Check for newest alert
if (data.length > 0) {

    const newestAlert = data[data.length - 1];

    if (lastAlertId === 0) {
        // First load, don't notify
        lastAlertId = newestAlert.id;
    }
    else if (newestAlert.id > lastAlertId) {

        lastAlertId = newestAlert.id;

      const currentTime = new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit"
});

let notificationIcon = "images/low.png";

if (newestAlert.severity.toLowerCase() === "medium") {
    notificationIcon = "images/medium.png";
}
else if (newestAlert.severity.toLowerCase() === "high") {
    notificationIcon = "images/high.png";
}
else if (newestAlert.severity.toLowerCase() === "critical") {
    notificationIcon = "images/critical.png";
}

if (Notification.permission === "granted") {

    new Notification("🚨 DISASTER ALERT", {

        body:
            `🌊 Type: ${newestAlert.type}\n` +
            `📍 Location: ${newestAlert.location}\n` +
            `⚠ Severity: ${newestAlert.severity}\n` +
            `🕒 Time: ${currentTime}`,

        icon: "images/critical.png"

    });
}

if (newestAlert.severity.toLowerCase() === "critical") {

    alarmSound.play();

}

    }

}

// Show notification only if a new alert was added
if (previousAlertCount > 0 && data.length > previousAlertCount) {

    const latestAlert = data[data.length - 1];

    showNotification(latestAlert);
}

// Update count
previousAlertCount = data.length;

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
                        </div>
                    `);

                markers.push({
                    id: alert.id,
                    marker
                });
            });

            // STATS
            const stats = document.querySelector(".sidebar-stats");
            if (stats) {
                stats.innerHTML = `
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
// SAFE FILTER BUTTONS (NO CRASH)
// ===============================

const allBtn = document.getElementById("allFilter");
if (allBtn) {
    allBtn.addEventListener("click", () => {
        currentFilter = "all";
        refreshUI();
    });
}

const criticalBtn = document.getElementById("criticalFilter");
if (criticalBtn) {
    criticalBtn.addEventListener("click", () => {
        currentFilter = "critical";
        refreshUI();
    });
}

const highBtn = document.getElementById("HighFilter");
if (highBtn) {
    highBtn.addEventListener("click", () => {
        currentFilter = "high";
        refreshUI();
    });
}

const mediumBtn = document.getElementById("mediumFilter");
if (mediumBtn) {
    mediumBtn.addEventListener("click", () => {
        currentFilter = "medium";
        refreshUI();
    });
}

const lowBtn = document.getElementById("lowFilter");
if (lowBtn) {
    lowBtn.addEventListener("click", () => {
        currentFilter = "low";
        refreshUI();
    });
}

// ===============================
// SHOW NOTIFICATION
// ===============================
function showNotification(alert) {

    const box = document.getElementById("notification");

    document.getElementById("notifyType").innerHTML =
        "<b>Type:</b> " + alert.type;

    document.getElementById("notifyLocation").innerHTML =
        "<b>Location:</b> " + alert.location;

    document.getElementById("notifySeverity").innerHTML =
        "<b>Severity:</b> " + alert.severity;

    // Show notification
    box.classList.add("show");

    // Hide after 5 seconds
    setTimeout(() => {
        box.classList.remove("show");
    }, 5000);
}

// ===============================
// INIT
// ===============================
refreshUI();

setInterval(refreshUI, 5000);

const menuBtn = document.getElementById("menuBtn");
const closeMenuBtn = document.getElementById("closeMenuBtn");
const sidebar = document.querySelector(".sidebar");

menuBtn.addEventListener("click", () => {
    sidebar.classList.add("open");
});

closeMenuBtn.addEventListener("click", () => {
    sidebar.classList.remove("open");
});

const notificationClose =
    document.getElementById("notificationClose");

if (notificationClose) {
    notificationClose.addEventListener("click", () => {
        document.getElementById("notification")
            .classList.remove("show");
    });
}
