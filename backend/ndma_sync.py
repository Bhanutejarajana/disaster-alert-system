import feedparser
import mysql.connector
import requests
import re
import time
from bs4 import BeautifulSoup

NDMA_FEED = "https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml"

IGNORE_LOCATIONS = {

    "India",

    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",

    "Delhi",
    "Puducherry",
    "Ladakh",
    "Jammu And Kashmir",
    "Andaman And Nicobar Islands",
    "Lakshadweep",
    "Chandigarh",
    "Dadra And Nagar Haveli",
    "Daman And Diu",

    "Ganga",
    "Yamuna",
    "Godavari",
    "Krishna",
    "Brahmaputra",
    "Narmada",
    "Kaveri"
}

STATE_MAP = {
    "Balrampur": "Uttar Pradesh",
    "Deoria": "Uttar Pradesh",
    "Gorakhpur": "Uttar Pradesh",
    "Kushinagar": "Uttar Pradesh",
    "Maharajganj": "Uttar Pradesh",
    "Siddharth Nagar": "Uttar Pradesh",
    "Siddharthanagar": "Uttar Pradesh"
}

import os

db = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST", "localhost"),
    port=int(os.getenv("MYSQL_PORT", 3306)),
    user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", "Bhanu@1827"),
    database=os.getenv("MYSQL_DATABASE", "disaster_alert_db")
)

cursor = db.cursor(dictionary=True)

coordinate_cache = {}

def get_feed():

    feed = feedparser.parse(NDMA_FEED)

    return feed.entries

def parse_alert(alert):

    try:

        response = requests.get(alert.link, timeout=10)

        # Retry once if NDMA rate-limits us
        if response.status_code == 429:

            print("NDMA rate limit reached. Waiting 5 seconds...")

            time.sleep(5)

            response = requests.get(alert.link, timeout=10)

        if response.status_code != 200:

            print(f"Skipping alert (HTTP {response.status_code})")

            return None

        soup = BeautifulSoup(response.text, "xml")

        identifier = soup.find("identifier")
        info = soup.find("info")

        if identifier is None or info is None:
            print("identifier or info missing")
            return None

        event = info.find("event")
        severity = info.find("severity")
        headline = info.find("headline")
        area = info.find("areaDesc")

        if (
            event is None or
            severity is None or
            headline is None or
            area is None
        ):
            print("Some required tag is missing")
            return None

        return {
            "source_id": identifier.text.strip(),
            "event": event.text.strip(),
            "severity": severity.text.strip(),
            "headline": headline.text.strip(),
            "area": area.text.strip()
        }

    except Exception as e:
        print("Parse Error:", e)
        return None
        
def get_coordinates(location, state="India"):

    key = f"{location},{state}"

    if key in coordinate_cache:
        return coordinate_cache[key]

    headers = {
        "User-Agent": "DisasterAlertSystem/1.0"
    }

    # Different search attempts
    search_queries = [

        f"{location}, {state}, India",

        # Remove Urban/Rural if present
        f"{re.sub(r'\\b(Urban|Rural)\\b', '', location).strip()}, {state}, India",

        # Remove spaces completely (helps some names)
        f"{location.replace(' ', '')}, {state}, India",

        # Only location + India
        f"{location}, India",
    ]

    for query in search_queries:

        params = {
            "q": query,
            "format": "json",
            "limit": 1
        }

        time.sleep(1)

        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            headers=headers
        )

        if response.status_code != 200:
            continue

        data = response.json()

        if data:

            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])

            coordinate_cache[key] = (lat, lon)

            return lat, lon

    coordinate_cache[key] = (None, None)

    return None, None

def alert_exists(source_id, location):

    query = """
    SELECT id
    FROM alerts
    WHERE source_id = %s
    AND location = %s
    """

    cursor.execute(query, (source_id, location))

    return cursor.fetchone() is not None

def source_exists(source_id):

    query = """
    SELECT id
    FROM alerts
    WHERE source_id = %s
    LIMIT 1
    """

    cursor.execute(query, (source_id,))

    return cursor.fetchone() is not None

def save_alert(source_id, event, severity, location, latitude, longitude):

    query = """
    INSERT INTO alerts
    (type, location, severity, latitude, longitude, source_id)
    VALUES (%s,%s,%s,%s,%s,%s)
    """

    values = (
        event,
        location,
        severity,
        latitude,
        longitude,
        source_id
    )

    cursor.execute(query, values)
    db.commit()

def delete_old_alerts(active_source_ids):

    if not active_source_ids:
        print("No active source IDs found. Skipping delete.")
        return

    placeholders = ",".join(["%s"] * len(active_source_ids))

    query = f"""
    DELETE FROM alerts
    WHERE source_id IS NOT NULL
    AND source_id NOT IN ({placeholders})
    """

    cursor.execute(query, tuple(active_source_ids))

    deleted = cursor.rowcount

    db.commit()
    
def extract_state(area):

    area = area.strip()

    # Pattern: "14 districts of Gujarat"
    match = re.search(r'of\s+(.+)', area, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Pattern: "Brahmaputra, Neamatighat, Jorhat, Assam"
    if "," in area:
        return area.split(",")[-1].strip()

    return "India"


def extract_locations(headline, area):

    pattern = r'over (.*?)(?: in next| during next| within| till| today| tomorrow|[.])'

    match = re.search(pattern, headline, re.IGNORECASE)

    # English alert
    if match:
        text = match.group(1)

    # Hindi alert
    elif re.search(r'[\u0900-\u097F]', headline):
        text = headline

    # Fallback
    else:
        text = area

    # Hindi alert handling
    if re.search(r'[\u0900-\u097F]', text):

        # Remove the beginning sentence
        text = re.sub(r'^.*?में', '', text)

        # Remove everything after "में"
        text = re.sub(r'में.*$', '', text)

        # Replace Hindi "and" with comma
        text = text.replace(" और ", ",")

        # Split into locations
        locations = [loc.strip() for loc in text.split(",") if loc.strip()]

        return locations

    text = text.replace(" and ", ",")

    locations = text.split(",")

    cleaned_locations = []

    for loc in locations:

        loc = re.sub(r"^some parts of\s+", "", loc, flags=re.IGNORECASE)
        loc = re.sub(r"^isolated places over\s+", "", loc, flags=re.IGNORECASE)
        loc = re.sub(r"^a few places over\s+", "", loc, flags=re.IGNORECASE)
        loc = re.sub(r"^few places over\s+", "", loc, flags=re.IGNORECASE)
        loc = re.sub(r"^many places over\s+", "", loc, flags=re.IGNORECASE)

        # Remove prefixes like anm-, tpt-, mkp-
        loc = re.sub(r"^[a-z]{2,4}-", "", loc, flags=re.IGNORECASE)

        # Convert xxxurban -> xxx Urban
        loc = re.sub(r"urban$", " Urban", loc, flags=re.IGNORECASE)

        # Convert xxxrural -> xxx Rural
        loc = re.sub(r"rural$", " Rural", loc, flags=re.IGNORECASE)

        # Replace remaining hyphens and underscores with spaces
        loc = loc.replace("-", " ")
        loc = loc.replace("_", " ")

        # Remove words like district, districts, mandal, mandals
        loc = re.sub(r"\bdistricts?\b", "", loc, flags=re.IGNORECASE)
        loc = re.sub(r"\bmandals?\b", "", loc, flags=re.IGNORECASE)

        # Remove anything after "of"
        loc = re.sub(r"\bof\b.*", "", loc, flags=re.IGNORECASE)

        # Trim spaces
        loc = " ".join(loc.split())

        # Convert to Title Case
        loc = loc.title()

        if loc and loc not in IGNORE_LOCATIONS:

            cleaned_locations.append(loc)

    return cleaned_locations

def sync_ndma_alerts():

    alerts = get_feed()[:10]

    active_source_ids = []

    for alert in alerts:

        match = re.search(r'identifier=(.+)', alert.link)

        if not match:
            continue

        source_id = "IN-" + match.group(1)

        if source_exists(source_id):
            print("Already in database. Skipping XML download.")
            active_source_ids.append(source_id)
            continue

        try:

            data = parse_alert(alert)

            if data is None:
                print("Failed to parse:", alert.link)
                continue

            active_source_ids.append(data["source_id"])

            state = extract_state(data["area"])

            locations = extract_locations(
                data["headline"],
                data["area"]
            )

            for location in locations:

                if alert_exists(data["source_id"], location):
                    continue

                state_for_location = state

                if state_for_location == "India":
                    state_for_location = STATE_MAP.get(location, "India")

                latitude, longitude = get_coordinates(location, state_for_location)

                if latitude is None:
                    print(f"Could not geocode: {location}")
                    continue

                save_alert(
                    data["source_id"],
                    data["event"],
                    data["severity"],
                    location,
                    latitude,
                    longitude
                )

        except Exception as e:

            print("Error:", e)

    if len(active_source_ids) > 0:

        delete_old_alerts(active_source_ids)

    else:

        print("Delete skipped because no alerts were successfully parsed.")

    print("\nNDMA Sync Completed.")