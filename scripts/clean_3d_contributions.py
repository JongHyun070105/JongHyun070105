#!/usr/bin/env python3
"""Build a concise 3D contribution SVG from upstream's real GitHub data.

Preserve the 3D calendar and contribution radar. Remove the language pie,
date caption, and default footer; replace them with four compact live metrics.
No counts are hard-coded. The input remains the upstream-generated SVG.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
Q = lambda name: f"{{{NS}}}{name}"

ROOT = Path("profile-3d-contrib")
THEMES = ("profile-night-rainbow", "profile-season")


def parse_metrics(radar, summary):
    activity = {}
    for element in radar.iter(Q("text")):
        label = (element.text or "").strip()
        if label not in {"Commit", "PullReq", "Issue", "Review", "Repo"}:
            continue
        title = element.find(Q("title"))
        if title is None or not (title.text or "").strip().isdigit():
            raise ValueError(f"Missing GitHub activity value: {label}")
        activity[label] = int(title.text.strip())

    if len(activity) != 5:
        raise ValueError("The upstream radar has changed unexpectedly.")

    labels = summary.findall(Q("text"))
    if len(labels) != 4 or (labels[1].text or "").strip() != "contributions":
        raise ValueError("The upstream contribution summary has changed.")

    def number(node):
        value = (node.text or "").strip().replace(",", "")
        if not value.isdigit():
            raise ValueError(f"Unexpected numeric value: {value!r}")
        return int(value)

    return (
        ("Contributions", number(labels[0])),
        ("Commits", activity["Commit"]),
        ("Pull requests", activity["PullReq"]),
        ("Stars", number(labels[2])),
    )


def add_live_metrics(svg, metrics):
    group = ET.SubElement(svg, Q("g"), {"id": "activity-metrics"})
    # The upper left is intentionally left open by the original 3D layout.
    positions = ((66, 66), (310, 66), (66, 174), (310, 174))
    for (label, value), (x, y) in zip(metrics, positions):
        title = ET.SubElement(group, Q("text"), {
            "x": str(x),
            "y": str(y),
            "class": "fill-weak",
            "style": "font-size: 17px; font-weight: 500;",
        })
        title.text = label.upper()
        count = ET.SubElement(group, Q("text"), {
            "x": str(x),
            "y": str(y + 45),
            "class": "fill-strong" if label == "Contributions" else "fill-fg",
            "style": "font-size: 38px; font-weight: 700;",
        })
        count.text = format(value, ",")
        tooltip = ET.SubElement(count, Q("title"))
        tooltip.text = f"{value:,} {label.lower()} in the contribution period"


expected_metrics = None
for theme in THEMES:
    source = ROOT / f"{theme}.svg"
    output = ROOT / f"{theme}-clean.svg"
    svg = ET.parse(source).getroot()
    items = list(svg)

    # Upstream: CSS, background, 3D bars, radar, languages, footer.
    if (svg.tag != Q("svg") or len(items) != 6 or
        [node.tag for node in items] !=
        [Q("style"), Q("rect"), Q("g"), Q("g"), Q("g"), Q("g")] or
        len(items[2]) < 300):
        raise ValueError(f"Unexpected 3D SVG layout: {source}")

    metrics = parse_metrics(items[3], items[5])
    if expected_metrics is not None and metrics != expected_metrics:
        raise ValueError("Dark and light contribution totals do not match")
    expected_metrics = metrics

    svg.remove(items[4])  # Languages donut
    svg.remove(items[5])  # Original summary including stars, forks and dates
    add_live_metrics(svg, metrics)

    svg.set("role", "img")
    svg.set("aria-label", "GitHub 3D contribution calendar, activity radar and real activity counts")
    ET.ElementTree(svg).write(output, encoding="utf-8", xml_declaration=True)

    verified = ET.parse(output).getroot()
    if len(verified) != 5 or verified[-1].get("id") != "activity-metrics":
        raise ValueError(f"Invalid final SVG structure: {output}")
    print(f"{output}: " + ", ".join(f"{key}={value:,}" for key, value in metrics))
