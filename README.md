# Disaster Alert System

## Overview

The Disaster Alert System is a web-based application that displays disaster alerts on an interactive map. It provides role-based access for administrators and users, allowing disaster monitoring with live NDMA alerts.

---

## Features

- User Registration & Login
- Admin and User roles
- Interactive map using Leaflet
- Live NDMA disaster alerts
- Manual alert management by Admin
- Browser notifications
- Alarm for Critical Alerts
- Alert filtering by severity
- MySQL database integration

---

## Technologies Used

### Frontend
- HTML5
- CSS3
- JavaScript
- Leaflet.js

### Backend
- Python
- Flask
- APScheduler

### Database
- MySQL

### APIs
- NDMA RSS Feed

---

## Project Structure

```
disaster-alert-system
│
├── backend
│   ├── app.py
│   ├── fetch_ndma.py
│   ├── ndma_sync.py
│   └── requirements.txt
│
├── frontend
│   ├── admin.html
│   ├── admin.js
│   ├── user.html
│   ├── user.js
│   ├── login.html
│   ├── login.js
│   ├── register.html
│   ├── register.js
│   ├── style.css
│   ├── images/
│   └── sounds/
│
├── .gitignore
└── README.md
```

---

## Installation

### Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend

Open `login.html` in your browser.

---

## Author

**Bhanu Teja Rajana**