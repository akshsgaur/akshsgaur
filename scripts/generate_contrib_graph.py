import requests
import json
import os
from datetime import datetime

USERNAME = "akshsgaur"
TOKEN = os.environ.get("GH_TOKEN", "")

# Amber → Red color scale (0 commits = empty, then amber to bright red)
COLORS = {
    0: "#161b22",   # empty / no commits
    1: "#FFBF00",   # amber - low
    2: "#FF8C00",   # dark orange - medium
    3: "#FF4500",   # orange red - high
    4: "#FF0000",   # bright red - very high
}

CELL_SIZE = 13
CELL_PADDING = 3
CELL_ROUND = 2
LEFT_MARGIN = 40
TOP_MARGIN = 30
DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fetch_contributions():
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
                weekday
              }
            }
          }
        }
      }
    }
    """
    headers = {"Authorization": f"bearer {TOKEN}"}
    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"username": USERNAME}},
        headers=headers,
    )
    data = resp.json()
    calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return calendar


def get_color(count, max_count):
    if count == 0:
        return COLORS[0]
    if max_count == 0:
        return COLORS[0]
    ratio = count / max_count
    if ratio <= 0.25:
        return COLORS[1]
    elif ratio <= 0.50:
        return COLORS[2]
    elif ratio <= 0.75:
        return COLORS[3]
    else:
        return COLORS[4]


def generate_svg(calendar):
    weeks = calendar["weeks"]
    num_weeks = len(weeks)
    total = calendar["totalContributions"]

    # Find max contributions in a single day
    max_count = 0
    for week in weeks:
        for day in week["contributionDays"]:
            if day["contributionCount"] > max_count:
                max_count = day["contributionCount"]

    width = LEFT_MARGIN + num_weeks * (CELL_SIZE + CELL_PADDING) + 20
    height = TOP_MARGIN + 7 * (CELL_SIZE + CELL_PADDING) + 50

    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    svg_parts.append(f'<rect width="{width}" height="{height}" fill="#0d1117" rx="6"/>')

    # Title
    svg_parts.append(f'<text x="{width // 2}" y="18" text-anchor="middle" fill="#FFCB05" font-family="\'Press Start 2P\', monospace" font-size="10">⚡ Tall Grass Activity ⚡</text>')

    # Day labels
    for i, label in enumerate(DAY_LABELS):
        if label:
            y = TOP_MARGIN + i * (CELL_SIZE + CELL_PADDING) + CELL_SIZE - 2
            svg_parts.append(f'<text x="2" y="{y}" fill="#8b949e" font-family="monospace" font-size="10">{label}</text>')

    # Month labels
    month_positions = {}
    for wi, week in enumerate(weeks):
        for day in week["contributionDays"]:
            dt = datetime.strptime(day["date"], "%Y-%m-%d")
            if dt.day <= 7:
                month_key = dt.month
                if month_key not in month_positions:
                    month_positions[month_key] = LEFT_MARGIN + wi * (CELL_SIZE + CELL_PADDING)

    for month_num, x_pos in month_positions.items():
        svg_parts.append(f'<text x="{x_pos}" y="{TOP_MARGIN - 6}" fill="#8b949e" font-family="monospace" font-size="10">{MONTH_NAMES[month_num - 1]}</text>')

    # Contribution cells
    for wi, week in enumerate(weeks):
        for day in week["contributionDays"]:
            count = day["contributionCount"]
            weekday = day["weekday"]
            x = LEFT_MARGIN + wi * (CELL_SIZE + CELL_PADDING)
            y = TOP_MARGIN + weekday * (CELL_SIZE + CELL_PADDING)
            color = get_color(count, max_count)
            svg_parts.append(f'<rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="{CELL_ROUND}" fill="{color}">')
            svg_parts.append(f'<title>{day["date"]}: {count} contributions</title>')
            svg_parts.append('</rect>')

    # Legend
    legend_y = TOP_MARGIN + 7 * (CELL_SIZE + CELL_PADDING) + 15
    svg_parts.append(f'<text x="{LEFT_MARGIN}" y="{legend_y}" fill="#8b949e" font-family="monospace" font-size="10">{total} contributions in the last year</text>')

    legend_x = width - 170
    svg_parts.append(f'<text x="{legend_x - 30}" y="{legend_y}" fill="#8b949e" font-family="monospace" font-size="10">Less</text>')
    for i, level in enumerate([0, 1, 2, 3, 4]):
        lx = legend_x + i * (CELL_SIZE + 3)
        svg_parts.append(f'<rect x="{lx}" y="{legend_y - 10}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="{CELL_ROUND}" fill="{COLORS[level]}"/>')
    svg_parts.append(f'<text x="{legend_x + 5 * (CELL_SIZE + 3) + 2}" y="{legend_y}" fill="#8b949e" font-family="monospace" font-size="10">More</text>')

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


if __name__ == "__main__":
    print("Fetching contribution data...")
    calendar = fetch_contributions()
    print(f"Total contributions: {calendar['totalContributions']}")
    print(f"Weeks: {len(calendar['weeks'])}")

    svg = generate_svg(calendar)
    with open("contrib-graph.svg", "w") as f:
        f.write(svg)
    print("Generated contrib-graph.svg")