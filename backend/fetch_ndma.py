import feedparser
import requests
from bs4 import BeautifulSoup

# NDMA RSS Feed
url = "https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml"

feed = feedparser.parse(url)

print("Feed Title:", feed.feed.get("title"))
print("Number of Alerts:", len(feed.entries))
print("-" * 60)

# Read first alert
first_alert = feed.entries[0]

# Download XML
response = requests.get(first_alert.link)

# Parse XML
soup = BeautifulSoup(response.text, "xml")

# First English info block
info = soup.find("info")

event = info.find("event").text if info.find("event") else "N/A"
severity = info.find("severity").text if info.find("severity") else "N/A"
headline = info.find("headline").text if info.find("headline") else "N/A"

area = info.find("area")
area_desc = area.find("areaDesc").text if area else "N/A"

print("Event     :", event)
print("Severity  :", severity)
print("Area      :", area_desc)
print("Headline  :", headline)