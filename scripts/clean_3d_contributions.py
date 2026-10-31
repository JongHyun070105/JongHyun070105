#!/usr/bin/env python3
"""Keep only the 3D contribution calendar from the upstream SVG.

The upstream generator includes separate radar, language and total-count groups.
This small post-processing step removes those decorative panels without
changing the dates or heights of the real contribution bars.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
PREFIX = f"{{{SVG_NS}}}"

ROOT = Path("profile-3d-contrib")
THEMES = ("profile-night-rainbow", "profile-season")

for theme in THEMES:
    original = ROOT / f"{theme}.svg"
    output = ROOT / f"{theme}-clean.svg"
    tree = ET.parse(original)
    svg = tree.getroot()
    children = list(svg)

    # Upstream structure: style, background rect, 3D calendar,
    # radar chart, language donut, summary labels.
    if (
        svg.tag != PREFIX + "svg"
        or len(children) != 6
        or [child.tag for child in children[:3]]
        != [PREFIX + "style", PREFIX + "rect", PREFIX + "g"]
        or len(list(children[2])) < 300
    ):
        raise RuntimeError(
            f"Unexpected upstream SVG structure for {original}; "
            "refusing to publish an incorrectly trimmed chart"
        )

    for decorative_group in children[3:]:
        svg.remove(decorative_group)

    # Keep the original viewBox: the complete 3D calendar spans its diagonal.
    svg.set("role", "img")
    svg.set("aria-label", "3D GitHub contribution calendar")
    tree.write(output, encoding="utf-8", xml_declaration=True)
    # Validation: generated image has only the calendar, no auxiliary charts.
    check = ET.parse(output).getroot()
    assert len(check) == 3
    print(f"Generated {output} ({output.stat().st_size:,} bytes)")
