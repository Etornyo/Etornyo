import os
import requests
import datetime

# ---------- Configuration ----------
USERNAME = "Zekhz"  # Your GitHub Username
OUTPUT_FILE = "racetrack.svg"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def fetch_contributions(username):
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
    headers = {"Authorization": f"bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    try:
        response = requests.post("https://api.github.com/graphql", 
                                 json={"query": query, "variables": {"username": username}}, 
                                 headers=headers)
        if response.status_code == 200 and "errors" not in response.json():
            return response.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    except Exception as e:
        pass
    return None

def main():
    # Fetch data to determine car speed and draw grid
    calendar = fetch_contributions(USERNAME)
    if calendar:
        total = calendar["totalContributions"]
        weeks = calendar["weeks"]
    else:
        # Fallback
        total = 0
        weeks = []
        for w in range(53):
            days = [{"contributionCount": 0} for _ in range(7)]
            weeks.append({"contributionDays": days})
    
    # Calculate duration: Base 20s, reduces as you contribute (min 4s)
    duration = max(4, 20 - (total // 10))

    # SVG Settings
    box_size = 14
    box_spacing = 3
    # Calculate total width of grid to center it
    grid_width = len(weeks) * (box_size + box_spacing) - box_spacing
    grid_height = 7 * (box_size + box_spacing) - box_spacing
    
    svg_width = 1000
    svg_height = 400
    
    start_x = (svg_width - grid_width) // 2
    start_y = (svg_height - grid_height) // 2 + 20 # slighly offset down

    # Generate Grid
    grid_svg = ""
    for week_idx, week in enumerate(weeks):
        x = start_x + week_idx * (box_size + box_spacing)
        for day_idx, day in enumerate(week["contributionDays"]):
            y = start_y + day_idx * (box_size + box_spacing)
            count = day["contributionCount"]
            
            # Map counts to dark theme colors
            if count == 0:
                fill = "#161b22"
            elif count < 3:
                fill = "#0e4429"
            elif count < 6:
                fill = "#006d32"
            elif count < 10:
                fill = "#26a641"
            else:
                fill = "#39d353"
                
            grid_svg += f'    <rect x="{x}" y="{y}" width="{box_size}" height="{box_size}" rx="2" fill="{fill}" />\n'

    svg_content = f"""<svg viewBox="0 0 {svg_width} {svg_height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{svg_width}" height="{svg_height}" fill="#0d1117" rx="10"/>

  <!-- GitHub Contribution Grid -->
  <g id="contribution-grid">
{grid_svg}
  </g>

  <!-- Track overlay -->
  <path id="fuji-track" 
        d="M 150,320 L 850,320 Q 920,320 930,280 L 910,240 Q 890,200 830,210 L 750,230 Q 700,240 680,200 L 650,120 Q 630,70 580,80 L 450,120 Q 400,130 380,170 L 350,230 Q 330,280 280,270 L 180,250 Q 120,240 100,280 Z" 
        fill="none" stroke="#ef4444" stroke-width="5" stroke-linejoin="round" stroke-linecap="round" opacity="0.8">
    <animate attributeName="stroke-opacity" values="0.8;0.3;0.8" dur="3s" repeatCount="indefinite" />
  </path>

  <line x1="250" y1="310" x2="250" y2="330" stroke="white" stroke-width="3" opacity="0.8" />
  <text x="50" y="50" fill="white" font-family="sans-serif" font-weight="bold" font-size="20" opacity="0.6">FUJI SPEEDWAY | {total} COMMITS</text>

  <!-- Car over track -->
  <g id="car">
    <rect x="-12" y="-5" width="24" height="10" rx="2" fill="#ef4444" />
    <rect x="8" y="-8" width="4" height="16" fill="#1e293b" />
    <rect x="-14" y="-7" width="3" height="14" fill="#1e293b" />
    <circle cx="0" cy="0" r="3" fill="#ffffff" />
    <circle cx="0" cy="0" r="2" fill="#334155" />
    <rect x="6" y="-9" width="5" height="3" rx="1" fill="#000" /> 
    <rect x="6" y="6" width="5" height="3" rx="1" fill="#000" /> 
    <rect x="-10" y="-10" width="6" height="4" rx="1" fill="#000" /> 
    <rect x="-10" y="6" width="6" height="4" rx="1" fill="#000" /> 
    <animateMotion dur="{duration}s" repeatCount="indefinite" rotate="auto">
      <mpath href="#fuji-track" />
    </animateMotion>
  </g>
</svg>"""

    with open(OUTPUT_FILE, "w") as f:
        f.write(svg_content)

if __name__ == "__main__":
    main()