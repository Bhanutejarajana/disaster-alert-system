from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import mysql.connector
import requests

from apscheduler.schedulers.background import BackgroundScheduler
from ndma_sync import sync_ndma_alerts

from werkzeug.security import generate_password_hash, check_password_hash

import os
import mysql.connector

db = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST", "localhost"),
    port=int(os.getenv("MYSQL_PORT", "3306")),
    user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", "Bhanu@1827"),
    database=os.getenv("MYSQL_DATABASE", "disaster_alert_db")
)

# TEST CONNECTION
print("MySQL Connected Successfully")

app = Flask(__name__)
CORS(app)

# ----------------------------
# NDMA AUTO SYNC SCHEDULER
# ----------------------------

scheduler = BackgroundScheduler()

scheduler.add_job(
    sync_ndma_alerts,
    trigger="interval",
    minutes=5,
    id="ndma_sync_job",
    replace_existing=True
)

scheduler.start()

print("NDMA Auto Sync Started (Every 5 Minutes)")

# ----------------------------
# GET LATITUDE & LONGITUDE
# ----------------------------
def get_coordinates(location):

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": location + ", India",
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "DisasterAlertSystem/1.0"
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:

        data = response.json()

        if len(data) > 0:

            latitude = float(data[0]["lat"])
            longitude = float(data[0]["lon"])

            return latitude, longitude

    return None, None

# ----------------------------
# LOAD DATA
# ----------------------------

# ----------------------------
# GET ALERTS (READ)
# ----------------------------
@app.route("/alerts", methods=["GET"])
def get_alerts():

    db.reconnect()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM alerts")
    alerts = cursor.fetchall()

    alert_type = request.args.get("type")
    alert_severity = request.args.get("severity")
    alert_location = request.args.get("location")

    filtered_alerts = alerts

    if alert_type:
        filtered_alerts = [
            alert for alert in filtered_alerts
            if alert["type"].lower() == alert_type.lower()
        ]

    if alert_severity:
        filtered_alerts = [
            alert for alert in filtered_alerts
            if alert["severity"].lower() == alert_severity.lower()
        ]

    if alert_location:
        filtered_alerts = [
            alert for alert in filtered_alerts
            if alert["location"].lower() == alert_location.lower()
        ]

    return jsonify(filtered_alerts)
# ----------------------------
# ADD ALERT (CREATE) 🔥 NEW
# ----------------------------
@app.route("/alerts", methods=["POST"])
def add_alert():

    db.reconnect()
    cursor = db.cursor()

    new_alert = request.json

    location = new_alert["location"]

    latitude, longitude = get_coordinates(location)

    if not new_alert.get("type"):
        return jsonify({"message": "Type is required"}), 400

    if not new_alert.get("location"):
        return jsonify({"message": "Location is required"}), 400

    if not new_alert.get("severity"):
        return jsonify({"message": "Severity is required"}), 400

    query = """
    INSERT INTO alerts(type, location, severity, latitude, longitude)
    VALUES (%s, %s, %s, %s, %s)
    """

    values = (
        new_alert["type"],
        new_alert["location"],
        new_alert["severity"],
        latitude,
        longitude
    )

    cursor.execute(query, values)
    db.commit()

    return jsonify({
        "message": "Alert added successfully"
    })
# ----------------------------
# DELETE ALERT 🔥 NEW
# ----------------------------
@app.route("/alerts/<int:alert_id>", methods=["DELETE"])
def delete_alert(alert_id):

    db.reconnect()
    cursor = db.cursor()

    query = "DELETE FROM alerts WHERE id = %s"

    cursor.execute(query, (alert_id,))
    db.commit()

    return jsonify({
        "message": f"Alert {alert_id} deleted successfully"
    })

# ----------------------------
# UPDATE ALERT
# ----------------------------
@app.route("/alerts/<int:alert_id>", methods=["PUT"])
def update_alert(alert_id):

    db.reconnect()
    cursor = db.cursor()

    updated_data = request.json

    query = """
    UPDATE alerts
    SET type = %s,
        location = %s,
        severity = %s
    WHERE id = %s
    """

    values = (
        updated_data["type"],
        updated_data["location"],
        updated_data["severity"],
        alert_id
    )

    cursor.execute(query, values)
    db.commit()

    return jsonify({
        "message": "Alert updated successfully"
    })

# ----------------------------
# REGISTER API
# ----------------------------
@app.route("/register", methods=["POST"])
def register():

    data = request.json

    username = data["username"].strip()
    password = data["password"].strip()

    hashed_password = generate_password_hash(password)

    # Default role

    role = "user"

    db.reconnect()
    cursor = db.cursor(dictionary=True)

    # Check if username already exists
    cursor.execute(
        "SELECT id FROM users WHERE username=%s",
        (username,)
    )

    existing = cursor.fetchone()

    if existing:

        cursor.close()

        return jsonify({
            "message": "Username already exists"
        }), 400

    # Insert new user
    cursor.execute(
        """
        INSERT INTO users(username, password, role)
        VALUES(%s, %s, %s)
        """,
        (username, hashed_password, role)
    )

    db.commit()

    cursor.close()

    return jsonify({
        "message": "Registration successful"
    })

# ----------------------------
# LOGIN API
# ----------------------------
@app.route("/login", methods=["POST"])
def login():

    data = request.json

    username = data["username"]
    password = data["password"]

    db.reconnect()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT * FROM users
        WHERE username = %s
        """,
        (username,)
    )

    user = cursor.fetchone()

    cursor.close()

    if user and check_password_hash(user["password"], password):

        return jsonify({
            "message": "Login successful",
            "role": user["role"]
        })

    return jsonify({
        "message": "Invalid username or password"
    }), 401

# ----------------------------
# RUN SERVER
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)