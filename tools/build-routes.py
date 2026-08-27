#!/usr/bin/env python3
"""
Preprocess the official MadMac GPX exports into compact route JSON and
standalone elevation-profile SVGs, so the page never parses raw GPX at
runtime and the profile paints instantly (inlined in index.html).

Run once (or whenever the GPX files change):
    python3 tools/build-routes.py

Inputs:  data/gpx/midvaal-madmac-2026-<dist>.gpx
Outputs: data/routes/<dist>.json           (compact: coords + distance + elevation)
         assets/img/elevation-<dist>.svg   (standalone profile graphic —
                                             also the "elevation profile"
                                             asset for the posting playbook)
"""
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GPX_DIR = ROOT / "data" / "gpx"
ROUTES_DIR = ROOT / "data" / "routes"
SVG_DIR = ROOT / "assets" / "img"
NS = "{http://www.topografix.com/GPX/1/1}"

DISTANCES = [
    ("42_2km", "midvaal-madmac-2026-42.2km.gpx", "#e8531f"),  # marathon: orange (flagship)
    ("22km", "midvaal-madmac-2026-22km.gpx", "#2a9d5c"),
    ("11km", "midvaal-madmac-2026-11km.gpx", "#2a9d5c"),
    ("5km", "midvaal-madmac-2026-5km.gpx", "#2a9d5c"),
]


def haversine_m(a, b):
    r = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dphi = p2 - p1
    dlambda = math.radians(b[1] - a[1])
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def parse_gpx(path):
    root = ET.parse(path).getroot()
    pts = []
    for trkpt in root.iter(f"{NS}trkpt"):
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        ele_el = trkpt.find(f"{NS}ele")
        ele = float(ele_el.text) if ele_el is not None else 0.0
        pts.append((lat, lon, ele))
    return pts


def cumulative_distances(pts):
    dist = [0.0]
    for i in range(1, len(pts)):
        dist.append(dist[-1] + haversine_m(pts[i - 1][:2], pts[i][:2]) / 1000.0)
    return dist


def smoothed_elevations(eles, window=3):
    n = len(eles)
    out = []
    half = window // 2
    for i in range(n):
        lo, hi = max(0, i - half), min(n, i + half + 1)
        out.append(sum(eles[lo:hi]) / (hi - lo))
    return out


def total_ascent(eles):
    return sum(max(0.0, eles[i + 1] - eles[i]) for i in range(len(eles) - 1))


def build_elevation_svg(dist_km, eles, accent, width=900, height=220):
    """Self-contained SVG elevation profile, theme-aware via currentColor
    for text and a fixed accent fill for the area (works standalone as a
    downloadable asset, and inline in the page)."""
    pad_l, pad_r, pad_t, pad_b = 44, 16, 16, 28
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    emin, emax = min(eles), max(eles)
    erange = max(emax - emin, 1.0)
    dmax = dist_km[-1]

    def x(d):
        return pad_l + (d / dmax) * plot_w

    def y(e):
        return pad_t + plot_h - ((e - emin) / erange) * plot_h

    pts_line = " ".join(f"{x(d):.1f},{y(e):.1f}" for d, e in zip(dist_km, eles))
    area = (
        f"{x(0):.1f},{y(eles[0]):.1f} "
        + pts_line
        + f" {x(dmax):.1f},{y(eles[-1]):.1f}"
        + f" {pad_l + plot_w:.1f},{pad_t + plot_h:.1f}"
        + f" {pad_l:.1f},{pad_t + plot_h:.1f}"
    )

    # gridlines every ~10km (or every 1km for the 5km route) with elevation labels
    step = 10 if dmax > 15 else (5 if dmax > 8 else 1)
    gridlines = []
    d = 0.0
    while d <= dmax + 0.001:
        gx = x(d)
        gridlines.append(
            f'<line x1="{gx:.1f}" y1="{pad_t}" x2="{gx:.1f}" y2="{pad_t + plot_h}" '
            f'class="grid-line"/>'
            f'<text x="{gx:.1f}" y="{height - 8}" class="axis-label" text-anchor="middle">{d:.0f}</text>'
        )
        d += step

    # elevation axis labels (min/max)
    axis_labels = (
        f'<text x="{pad_l - 8}" y="{y(emax):.1f}" class="axis-label" text-anchor="end" dominant-baseline="middle">{emax:.0f}m</text>'
        f'<text x="{pad_l - 8}" y="{y(emin):.1f}" class="axis-label" text-anchor="end" dominant-baseline="middle">{emin:.0f}m</text>'
    )

    svg = f'''<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Elevation profile">
<style>
  .grid-line {{ stroke: currentColor; stroke-opacity: 0.12; stroke-width: 1; }}
  .axis-label {{ font: 11px/1 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: currentColor; opacity: 0.55; }}
  .profile-line {{ fill: none; stroke: {accent}; stroke-width: 2.5; stroke-linejoin: round; stroke-linecap: round; }}
  .profile-area {{ fill: {accent}; opacity: 0.16; }}
</style>
{"".join(gridlines)}
{axis_labels}
<polygon class="profile-area" points="{area}"/>
<polyline class="profile-line" points="{pts_line}"/>
</svg>'''
    return svg


def main():
    ROUTES_DIR.mkdir(parents=True, exist_ok=True)
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    summary = []

    for dist_id, gpx_name, accent in DISTANCES:
        path = GPX_DIR / gpx_name
        pts = parse_gpx(path)
        dist_km = cumulative_distances(pts)
        eles_raw = [p[2] for p in pts]
        eles_smooth = smoothed_elevations(eles_raw)

        total_km = dist_km[-1]
        emin, emax = min(eles_raw), max(eles_raw)
        ascent_smooth = total_ascent(eles_smooth)
        start_finish_gap_m = haversine_m(pts[0][:2], pts[-1][:2])

        # Downsample coordinates for the route JSON (map polyline) — every
        # point for short routes, thinned for longer ones. Keeps first/last.
        n = len(pts)
        stride = max(1, n // 400)
        coords = [[round(p[0], 6), round(p[1], 6)] for p in pts[::stride]]
        if coords[-1] != [round(pts[-1][0], 6), round(pts[-1][1], 6)]:
            coords.append([round(pts[-1][0], 6), round(pts[-1][1], 6)])

        # Elevation series thinned to ~150 points for a light-weight JSON
        # profile (the SVG is pre-rendered separately at full resolution).
        estride = max(1, n // 150)
        profile = [
            {"d": round(dist_km[i], 3), "e": round(eles_raw[i], 1)}
            for i in range(0, n, estride)
        ]
        if profile[-1]["d"] != round(total_km, 3):
            profile.append({"d": round(total_km, 3), "e": round(eles_raw[-1], 1)})

        route_json = {
            "id": dist_id,
            "distanceKm": round(total_km, 2),
            "elevationMinM": round(emin),
            "elevationMaxM": round(emax),
            "totalAscentApproxM": round(ascent_smooth),
            "startFinishGapM": round(start_finish_gap_m),
            "start": [round(pts[0][0], 6), round(pts[0][1], 6)],
            "finish": [round(pts[-1][0], 6), round(pts[-1][1], 6)],
            "coords": coords,
            "profile": profile,
        }
        out_path = ROUTES_DIR / f"{dist_id}.json"
        out_path.write_text(json.dumps(route_json, separators=(",", ":")))

        svg = build_elevation_svg(dist_km, eles_raw, accent)
        svg_path = SVG_DIR / f"elevation-{dist_id}.svg"
        svg_path.write_text(svg)

        summary.append(
            f"{dist_id:8s} dist={total_km:6.2f}km  ele={emin:.0f}-{emax:.0f}m  "
            f"ascent≈{ascent_smooth:.0f}m  gap={start_finish_gap_m:.0f}m  "
            f"coords={len(coords)} profile_pts={len(profile)}  -> {out_path.relative_to(ROOT)}"
        )

    print("\n".join(summary))


def build_motif(gpx_path, out_path, view_w=1000, view_h=400, pad=24):
    """Project the real 42.2km route to a normalised, north-up polyline for
    reuse as the site's recurring signature graphic (hero backdrop, section
    dividers, footer mark) — the single-lap route itself, not a generic
    abstract line."""
    pts = parse_gpx(gpx_path)
    lats = [p[0] for p in pts]
    lons = [p[1] for p in pts]
    mean_lat_rad = math.radians(sum(lats) / len(lats))
    # simple equirectangular projection, x scaled by cos(latitude) so shape
    # isn't stretched east-west at this latitude
    xs = [lon * math.cos(mean_lat_rad) for lon in lons]
    ys = lats
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    rangex = max(maxx - minx, 1e-9)
    rangey = max(maxy - miny, 1e-9)
    # fit into viewbox preserving aspect ratio, centred, north-up
    avail_w, avail_h = view_w - 2 * pad, view_h - 2 * pad
    scale = min(avail_w / rangex, avail_h / rangey)
    drawn_w, drawn_h = rangex * scale, rangey * scale
    off_x = pad + (avail_w - drawn_w) / 2
    off_y = pad + (avail_h - drawn_h) / 2

    def proj(x, y):
        sx = off_x + (x - minx) * scale
        sy = off_y + (maxy - y) * scale  # flip so north (higher lat) is up
        return sx, sy

    stride = max(1, len(pts) // 300)
    idxs = list(range(0, len(pts), stride))
    if idxs[-1] != len(pts) - 1:
        idxs.append(len(pts) - 1)
    coords = [proj(xs[i], ys[i]) for i in idxs]
    points_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)

    out_path.write_text(json.dumps({
        "viewBox": f"0 0 {view_w} {view_h}",
        "points": points_str,
    }))
    return points_str


if __name__ == "__main__":
    main()
    motif = build_motif(
        GPX_DIR / "midvaal-madmac-2026-42.2km.gpx",
        ROOT / "assets" / "img" / "route-motif.json",
    )
    print(f"route-motif  -> assets/img/route-motif.json ({len(motif)} chars of point data)")
