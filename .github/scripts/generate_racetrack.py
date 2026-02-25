#!/usr/bin/env python3
"""
Generate an SVG racetrack with a car that moves based on GitHub contributions.
"""

import os
import sys
import requests
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import svgwrite

# ---------- Configuration ----------
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = "Etornyo"  # Replace with your GitHub username
OUTPUT_FILE = "racetrack.svg"
TRACK_RADIUS = 150        # pixels
CAR_SIZE = 20
DOT_RADIUS_BASE = 3
MAX_DOT_RADIUS = 8
# -----------------------------------

if not GITHUB_TOKEN:
    print("Error: GITHUB_TOKEN environment variable not set.")
    sys.exit(1)

headers = {"Authorization": f"bearer {GITHUB_TOKEN}"}

def fetch_contributions(username):
    """Fetch contribution calendar from GitHub GraphQL API."""
    query = """
    query($username: String!) {
        user(login: $username) {
            contributionsCollection {
                contributionCalendar {
                    totalContributions
                    weeks {
                        contributionDays {
                            contributionCount
                            date
                        }
                    }
                }
            }
        }
    }
    """
    variables = {"username": username}
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=headers
    )
    if response.status_code != 200:
        raise Exception(f"Query failed: {response.status_code} - {response.text}")
    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL errors: {data['errors']}")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    # Flatten to list of (date, count)
    days = []
    for week in weeks:
        for day in week["contributionDays"]:
            days.append((day["date"], day["contributionCount"]))
    return days

def get_current_day_index(days):
    """Return index (0..364) of today's date in the days list."""
    today_str = date.today().isoformat()
    for i, (d, _) in enumerate(days):
        if d == today_str:
            return i
    # If today not found (e.g., last year's data), return last day
    return len(days) - 1

def angle_from_index(idx, total_days=365):
    """Convert day index to angle in radians (starting at top, clockwise)."""
    # Start at top ( -90° in math coords) and go clockwise
    return (idx / total_days) * 2 * 3.14159 - 3.14159/2

def point_on_circle(center, radius, angle):
    """Return (x, y) for a point on circle at given angle."""
    x = center[0] + radius * cos(angle)
    y = center[1] + radius * sin(angle)
    return (x, y)

# We'll need math.cos and math.sin
from math import cos, sin

def main():
    print("Fetching contributions...")
    days = fetch_contributions(USERNAME)
    if not days:
        print("No contribution data found.")
        sys.exit(1)

    # Assume 365 days; if less (new year), pad with zeros
    total_days = 365
    if len(days) < total_days:
        # Prepend zeros for missing days (e.g., early Jan)
        missing = total_days - len(days)
        days = [("1970-01-01", 0)] * missing + days

    today_idx = get_current_day_index(days)
    print(f"Today's index: {today_idx}")

    # Determine max contribution for scaling dot sizes
    max_count = max(count for _, count in days)

    # Create SVG
    dwg = svgwrite.Drawing(OUTPUT_FILE, size=(500, 500), profile='full')
    center = (250, 250)

    # Draw track (circle)
    dwg.add(dwg.circle(center=center, r=TRACK_RADIUS,
                       stroke="black", stroke_width=3, fill="none"))

    # Draw contribution dots
    for idx, (date_str, count) in enumerate(days):
        angle = angle_from_index(idx)
        x, y = point_on_circle(center, TRACK_RADIUS, angle)
        # Scale dot size
        if max_count > 0:
            r = DOT_RADIUS_BASE + (count / max_count) * (MAX_DOT_RADIUS - DOT_RADIUS_BASE)
        else:
            r = DOT_RADIUS_BASE
        # Color: green (low) to red (high)
        if max_count > 0:
            intensity = count / max_count
            red = int(255 * intensity)
            green = int(255 * (1 - intensity))
            color = f"rgb({red}, {green}, 0)"
        else:
            color = "lightgray"
        dwg.add(dwg.circle(center=(x, y), r=r, fill=color, stroke="none"))

    # Draw car at today's position
    car_angle = angle_from_index(today_idx)
    car_x, car_y = point_on_circle(center, TRACK_RADIUS, car_angle)

    # Simple car shape (a rectangle with two wheels)
    car_group = dwg.g()
    # Car body
    car_group.add(dwg.rect(insert=(car_x - CAR_SIZE/2, car_y - CAR_SIZE/4),
                           size=(CAR_SIZE, CAR_SIZE/2),
                           fill="blue", stroke="black", stroke_width=1))
    # Wheels (circles)
    wheel_offset = CAR_SIZE * 0.3
    car_group.add(dwg.circle(center=(car_x - wheel_offset, car_y - CAR_SIZE/4), r=3, fill="black"))
    car_group.add(dwg.circle(center=(car_x + wheel_offset, car_y - CAR_SIZE/4), r=3, fill="black"))
    car_group.add(dwg.circle(center=(car_x - wheel_offset, car_y + CAR_SIZE/4), r=3, fill="black"))
    car_group.add(dwg.circle(center=(car_x + wheel_offset, car_y + CAR_SIZE/4), r=3, fill="black"))
    dwg.add(car_group)

    # Add a start/finish line marker
    start_angle = angle_from_index(0)
    sx, sy = point_on_circle(center, TRACK_RADIUS, start_angle)
    dwg.add(dwg.line(start=(sx-10, sy-10), end=(sx+10, sy+10),
                     stroke="red", stroke_width=2))
    dwg.add(dwg.line(start=(sx-10, sy+10), end=(sx+10, sy-10),
                     stroke="red", stroke_width=2))

    # Save
    dwg.save()
    print(f"SVG saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()