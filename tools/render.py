#!/usr/bin/env python3
"""
Renders index.html from data/race-config.json (+ the precomputed
data/routes/*.json, assets/img/elevation-*.svg and route-motif.json from
build-routes.py).

This keeps race facts in one JSON file — as the brief's deliverable
requires — while still shipping a fully static, SEO-crawlable index.html
with zero client-side content templating and no runtime dependency on the
config file. Deployment stays "upload the folder": there is no bundler,
no node_modules, nothing to install. Updating the site for 2027 means
editing race-config.json and re-running this script.

    python3 tools/build-routes.py   # only if the GPX files changed
    python3 tools/render.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "data" / "race-config.json").read_text())
MOTIF = json.loads((ROOT / "assets" / "img" / "route-motif.json").read_text())

SITE_URL = "https://midvaalmadmac.co.za"  # placeholder production domain — see README


# ---------------------------------------------------------------- helpers --

def rand(n):
    """R1,234 style currency, no cents."""
    if n is None:
        return "—"
    return "R{:,.0f}".format(n).replace(",", " ")


def esc(s):
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def dist_by_id(dist_id):
    return next(d for d in CONFIG["distances"] if d["id"] == dist_id)


def route_json_for(dist_id):
    return (ROOT / "data" / "routes" / f"{dist_id}.json").read_text()


def elevation_svg_for(dist_id):
    return (ROOT / "assets" / "img" / f"elevation-{dist_id}.svg").read_text()


def cta(label, position, distance=None, classes="btn btn-primary"):
    dist_attr = f' data-cta-distance="{esc(distance)}"' if distance else ""
    return (
        f'<a class="{classes}" href="{esc(CONFIG["entries"]["entryUrl"])}" '
        f'target="_blank" rel="noopener" data-cta="{esc(position)}"{dist_attr}>{esc(label)}</a>'
    )


def motif_svg(extra_class="", stroke_width="2"):
    return (
        f'<svg viewBox="{MOTIF["viewBox"]}" preserveAspectRatio="xMidYMid meet" '
        f'class="{extra_class}" aria-hidden="true">'
        f'<defs><linearGradient id="motifGradient" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="#2fae6a"/><stop offset="52%" stop-color="#f5c518"/>'
        f'<stop offset="100%" stop-color="#ef6a1f"/></linearGradient></defs>'
        f'<polyline points="{MOTIF["points"]}" fill="none" stroke="url(#motifGradient)" '
        f'stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"/>'
        f"</svg>"
    )


# ------------------------------------------------------------------ head --

def build_head():
    ed = CONFIG["edition"]
    entries = CONFIG["entries"]
    title = "Midvaal MadMac 2026 — Single-Lap Comrades & Two Oceans Qualifier, Meyerton, 4 October"
    description = (
        "Midvaal MadMac, 4 October 2026: a single-lap Comrades and Totalsports Two Oceans "
        "Marathon qualifier in Meyerton, Gauteng. 42.2km, 22km, 11km and 5km, R100 000 total "
        "prize money. Online entries close 22 September 2026."
    )
    canonical = f"{SITE_URL}/"
    og_image = f"{SITE_URL}/assets/img/og-madmac-2026.png"

    event_jsonld = {
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "name": "Midvaal MadMac 2026",
        "description": description,
        "startDate": f"{ed['date']}T06:00:00+02:00",
        "endDate": f"{ed['date']}T12:30:00+02:00",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "eventStatus": "https://schema.org/EventScheduled",
        "location": {
            "@type": "Place",
            "name": f"{ed['venueName']}, {ed['venueAddress']}",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": ed["venueAddress"],
                "addressLocality": "Meyerton",
                "addressRegion": "Gauteng",
                "addressCountry": "ZA",
            },
            "geo": {
                "@type": "GeoCoordinates",
                "latitude": ed["coordinates"]["lat"],
                "longitude": ed["coordinates"]["lng"],
            },
        },
        "organizer": {
            "@type": "Organization",
            "name": ed["organiser"],
            "url": CONFIG["facebook"]["pageUrl"],
        },
        "image": [og_image],
        "url": entries["entryUrl"],
        "offers": [
            {
                "@type": "Offer",
                "name": f"{d['label']} entry — early bird",
                "price": d["fees"]["earlyBird"],
                "priceCurrency": "ZAR",
                "availability": "https://schema.org/InStock",
                "validThrough": f"{CONFIG['entries']['lateFeeStartDate'][:10]}",
                "url": entries["entryUrl"],
            }
            for d in CONFIG["distances"]
        ],
    }

    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">

<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_ZA">
<meta property="og:site_name" content="Midvaal MadMac">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{og_image}">

<link rel="icon" href="data:image/svg+xml,{quote_svg_favicon()}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:ital,wght@1,700;1,800;1,900&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/site.css">

<script type="application/ld+json">{json.dumps(event_jsonld, indent=0)}</script>
"""


def quote_svg_favicon():
    # hand-encoded (# -> %23) — this is inlined directly into a data: URI
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0%" stop-color="%232fae6a"/><stop offset="52%" stop-color="%23f5c518"/>'
        '<stop offset="100%" stop-color="%23ef6a1f"/></linearGradient></defs>'
        '<rect width="32" height="32" rx="8" fill="%230f1836"/>'
        '<rect x="4" y="4" width="24" height="24" rx="6" fill="url(%23g)"/></svg>'
    )
    return svg


# ---------------------------------------------------------------- header --

NAV_LINKS = [
    ("#qualifiers", "Qualifiers"),
    ("#distances", "Distances"),
    ("#route", "Route"),
    ("#prizes", "Prizes"),
    ("#faq", "FAQ"),
]


def build_header():
    desktop_links = "".join(f'<a href="{href}">{label}</a>' for href, label in NAV_LINKS)
    mobile_links = "".join(f'<a href="{href}" class="mobile-nav-link">{label}</a>' for href, label in NAV_LINKS)

    return f"""<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="container header-row">
    <a class="brand" href="#top">
      <span class="brand-mark" aria-hidden="true"></span>
      Midvaal MadMac
    </a>
    <nav class="site-nav" aria-label="Section">{desktop_links}</nav>
    <div class="header-cta">
      {cta("Enter now", "header")}
      <button type="button" class="nav-toggle" aria-expanded="false" aria-controls="mobile-nav">
        <span class="visually-hidden">Menu</span>
        <span class="nav-toggle-bars" aria-hidden="true"></span>
      </button>
    </div>
  </div>
  <nav id="mobile-nav" class="mobile-nav" aria-label="Section" hidden>{mobile_links}</nav>
</header>
"""


# ------------------------------------------------------------------ hero --

def build_hero():
    ed = CONFIG["edition"]
    entries = CONFIG["entries"]
    flagship = dist_by_id("42_2km")

    return f"""<section class="hero" id="top">
  <div class="route-motif" aria-hidden="true">{motif_svg("route-motif-line")}</div>
  <div class="container hero-inner">
    <div>
      <p class="eyebrow">{ed["dateDisplay"]} &middot; Meyerton, Gauteng</p>
      <h1>Midvaal <span class="accent">MadMac</span></h1>
      <div class="hero-badges">
        <span class="badge"><strong>Single-lap</strong>&nbsp;Comrades &amp; Two&nbsp;Oceans qualifier</span>
        <span class="badge">R{ed["totalPrizeMoney"]//1000} 000 prize money</span>
        <span class="badge">4 distances</span>
      </div>
      <p class="hero-sub lede">
        A single-lap marathon through the Randvaal countryside south of Johannesburg —
        genuinely flat, chip-timed, and positioned early in both the Comrades centenary and
        Two Oceans 2027 qualifying windows. Four distances run from the same start line at
        Café du Cirque, so a whole club or a whole family can enter one morning.
      </p>
      <div class="hero-facts">
        <span><span class="dot"></span>{ed["dateDisplay"]}</span>
        <span><span class="dot"></span>{ed["venueName"]}, Daleside</span>
        <span><span class="dot"></span>42.2 &middot; 22 &middot; 11 &middot; 5&nbsp;km</span>
      </div>
      <div class="hero-actions">
        {cta("Enter now", "hero")}
        <a class="btn btn-ghost" href="#route">See the route</a>
      </div>
    </div>

    <div class="countdown-card">
      <p class="eyebrow">Online entries close</p>
      <div class="countdown-grid" data-countdown-target="{entries['onlineCloseDate']}">
        <div class="countdown-unit"><span class="num" data-unit="days">00</span><span class="lbl">Days</span></div>
        <div class="countdown-unit"><span class="num" data-unit="hours">00</span><span class="lbl">Hours</span></div>
        <div class="countdown-unit"><span class="num" data-unit="minutes">00</span><span class="lbl">Mins</span></div>
        <div class="countdown-unit"><span class="num" data-unit="seconds">00</span><span class="lbl">Secs</span></div>
        <p class="visually-hidden" data-closed-note hidden>Online entries have closed.</p>
      </div>
      <p class="countdown-note">
        Online entries close <strong>{entries['onlineCloseDisplay']}</strong>.
        Early bird pricing ends {entries['lateFeeStartDisplay']} — late fees apply from
        1&nbsp;September until close.
      </p>
    </div>
  </div>
</section>
"""


# ---------------------------------------------------------- qualifier panel --

def build_qualifier_panel():
    q = CONFIG["qualifiers"]
    comrades = q["comrades"]
    two_oceans = q["twoOceans"]
    flagship = dist_by_id("42_2km")

    return f"""<section class="qualifier-panel section-pad" id="qualifiers">
  <div class="container">
    <p class="eyebrow">Qualifying for 2027</p>
    <h2>Built for the sub-5:00 chase</h2>
    <p class="lede mt-6 max-narrow">
      MadMac exists in the calendar exactly where the two biggest qualifier races need it to.
      Here's what actually matters if you're chasing a marathon qualifying time.
    </p>

    <div class="qualifier-grid">
      <div class="qual-card">
        <div class="qual-icon">1</div>
        <h3>Single lap</h3>
        <p>{q['singleLapNote']}</p>
      </div>
      <div class="qual-card">
        <div class="qual-icon">2</div>
        <h3>Sub-5:00 standard</h3>
        <p>{q['standard']} qualifies for both the Comrades centenary and Two Oceans 2027.
        MadMac's own cut-off is generous — see the note below.</p>
      </div>
      <div class="qual-card">
        <div class="qual-icon">3</div>
        <h3>Chip-timed and GPX-verified</h3>
        <p>Mat-to-mat chip timing with checkpoints on route. The marathon measures 42.24km
        against the official GPX — within normal route-drawing tolerance of the standard
        42.195km marathon distance.</p>
      </div>
      <div class="qual-card">
        <div class="qual-icon">4</div>
        <h3>Early in the window</h3>
        <p>{comrades['dateDisplay'].split()[-1]} qualifying opens {comrades['qualifyingWindowDisplay']}
        for Comrades and {two_oceans['qualifyingWindowDisplay']} for Two Oceans. MadMac falls near the
        start of both — get it done in October and you've still got months in hand if the day
        doesn't go your way.</p>
      </div>
    </div>

    <div class="qual-caveat">
      <p><strong>{flagship['cutoffDisplay']} is the MadMac cut-off. {q['standard']} is the qualifying
      standard.</strong> {q['cutoffCaveat']}</p>
    </div>

    <div class="cta-strip">
      {cta("Enter the 42.2km", "qualifier-panel", "42_2km")}
    </div>
  </div>
</section>
"""


# --------------------------------------------------------- why run this one --

def build_why():
    reasons = [
        (
            "One lap, not three",
            "A lot of qualifier marathons in Gauteng are two or three laps of a short circuit, "
            "and runners actively dislike them. MadMac's marathon runs single lap — out to Karee "
            "Road, across the R59 into the Randvaal smallholdings, and home through Daleside "
            "village, with no repeated loop.",
        ),
        (
            "R100 000, paid equally",
            "Men's and women's prize money is equal across every distance and every age category "
            "— not just the open field. Paid electronically, by EFT, within seven days.",
        ),
        (
            "Four distances, one morning",
            "42.2km, 22km, 11km and 5km, all starting and finishing at Café du Cirque. A club or "
            "a family can enter one event together, from age 9 up.",
        ),
        (
            "Five collection points, not one",
            "Number collection runs at Sportsmans Warehouse branches in Cresta, East Rand Mall, "
            "Fourways and Vanderbijlpark before race week, plus the venue itself — no drive to "
            "Meyerton required before race day.",
        ),
    ]
    cards = "".join(
        f"""<div class="reason-card">
      <div class="reason-num">{i:02d}</div>
      <h3>{esc(title)}</h3>
      <p>{esc(body)}</p>
    </div>"""
        for i, (title, body) in enumerate(reasons, start=1)
    )
    return f"""<section class="section-pad" id="why">
  <div class="container">
    <p class="eyebrow">Why run this one</p>
    <h2>Four reasons, no adjectives</h2>
    <div class="reasons-grid">{cards}</div>
  </div>
</section>
"""


# --------------------------------------------------------- distances & fees --

def build_distances():
    distances = CONFIG["distances"]
    entries = CONFIG["entries"]

    cards = []
    for d in distances:
        flag_cls = " flagship" if d["flagship"] else ""
        flag_tag = '<span class="flag-tag">Flagship</span>' if d["flagship"] else ""
        shirts = (
            f"Free shirt to first {d['freeShirtsFirst']} entrants"
            if d["freeShirtsFirst"]
            else "R90 flat, no late fee"
        )
        cards.append(f"""<div class="distance-card{flag_cls}">
      <div class="distance-card-head">
        <span class="dist-label">{d['label']}</span>
        {flag_tag}
      </div>
      <div class="dist-fee-row"><span class="lbl">Early bird</span><span class="val">{rand(d['fees']['earlyBird'])}</span></div>
      <div class="dist-fee-row"><span class="lbl">Grandmaster</span><span class="val">{rand(d['fees']['grandmaster'])}</span></div>
      <div class="dist-fee-row"><span class="lbl">Late (after {entries['lateFeeStartDisplay'].replace('after ', '')})</span><span class="val late">{rand(d['fees']['late'])}</span></div>
      <div class="dist-meta">
        <span>Start {d['startTime']}</span>
        <span>Min age {d['minAge']}+</span>
        <span>Cut-off {d['cutoffDisplay']}</span>
      </div>
      <p style="margin-top: 0.75rem; font-size: 0.82rem; color: var(--text-faint);">{shirts}</p>
      {cta("Enter now", "distance-card", d['id'], "btn btn-primary btn-block btn-sm")}
    </div>""")

    thead_cols = "".join(
        f'<th class="{"flagship-col" if d["flagship"] else ""}">{d["label"]}</th>' for d in distances
    )

    def row(label, key, late=False):
        cells = "".join(
            f'<td class="{"late" if late else ""}">{rand(d["fees"][key])}</td>' for d in distances
        )
        return f"<tr><th scope=\"row\">{label}</th>{cells}</tr>"

    def meta_row(label, values):
        cells = "".join(f"<td>{v}</td>" for v in values)
        return f"<tr><th scope=\"row\">{label}</th>{cells}</tr>"

    table = f"""<div class="distance-table-wrap">
      <table class="distance-table">
        <thead><tr><th scope="col"></th>{thead_cols}</tr></thead>
        <tbody>
          {row("Early bird entry fee", "earlyBird")}
          {row("Grandmaster", "grandmaster")}
          {row(f"Late (after {entries['lateFeeStartDisplay'].replace('after ', '')})", "late", late=True)}
          {meta_row("Start time", [d['startTime'] for d in distances])}
          {meta_row("Minimum age", [f"{d['minAge']}+" for d in distances])}
          {meta_row("Cut-off", [d['cutoffDisplay'] for d in distances])}
        </tbody>
      </table>
    </div>"""

    return f"""<section class="section-pad" id="distances">
  <div class="container">
    <p class="eyebrow">Distances &amp; entry fees</p>
    <h2>Pick your distance</h2>
    <p class="lede mt-6 max-narrow">
      All four distances start and finish at Café du Cirque.
    </p>

    <div class="deadline-strip">
      <div class="deadline-box">
        <span class="date">31 Aug</span>
        <p>Early bird pricing ends. Late fees apply on every distance except the 5km, which
        stays flat at R90.</p>
      </div>
      <div class="deadline-box">
        <span class="date">22 Sep</span>
        <p>Online entries close at 21:00. After that, manual entries only, at collection points,
        subject to availability. None on race day.</p>
      </div>
    </div>

    <div class="distance-cards">{''.join(cards)}</div>
    {table}

    <div class="cta-strip">
      {cta("Enter now", "after-pricing")}
    </div>
  </div>
</section>
"""


# ------------------------------------------------------------------ route --

def build_route():
    distances = CONFIG["distances"]

    tabs = "".join(
        f"""<button class="route-tab" role="tab" id="tab-{d['id']}"
      aria-selected="{'true' if i == 0 else 'false'}" aria-controls="panel-{d['id']}"
      tabindex="{'0' if i == 0 else '-1'}" data-dist="{d['id']}">{d['label']}</button>"""
        for i, d in enumerate(distances)
    )

    panels = []
    for i, d in enumerate(distances):
        route_data = route_json_for(d["id"])
        elevation_svg = elevation_svg_for(d["id"])
        ascent_key = "totalAscentM"
        panels.append(f"""<div class="route-panel" id="panel-{d['id']}" role="tabpanel"
    aria-labelledby="tab-{d['id']}" data-dist="{d['id']}" {"" if i == 0 else "hidden"}>
      <div class="route-layout">
        <div class="route-map" data-dist="{d['id']}">
          <div class="map-placeholder">Map loads as you scroll to it</div>
        </div>
        <div class="route-stats">
          <div class="route-stat-grid">
            <div class="route-stat"><div class="num">{d['gpxDistanceKm']:.2f}km</div><div class="lbl">GPX distance</div></div>
            <div class="route-stat"><div class="num">{d['elevationMinM']}–{d['elevationMaxM']}m</div><div class="lbl">Elevation range</div></div>
            <div class="route-stat"><div class="num">~{d[ascent_key]}m</div><div class="lbl">Total ascent (approx.)</div></div>
            <div class="route-stat"><div class="num">{d['cutoffDisplay']}</div><div class="lbl">Cut-off</div></div>
          </div>
          <div class="elevation-profile">{elevation_svg}</div>
          <p class="route-caveat">* Elevation from Strava's terrain model, not a survey — indicative, not to the metre.</p>
          <p class="route-desc">{esc(d['routeDescription'])}</p>
          <p class="route-desc">{esc(d['profileSummary'])}</p>
          <div class="route-links">
            <a class="btn btn-ghost btn-sm" href="data/gpx/{d['gpxFile']}" download>Download GPX</a>
            <a class="btn btn-ghost btn-sm" href="{esc(d['stravaRouteUrl'])}" target="_blank" rel="noopener">Open in Strava</a>
          </div>
        </div>
      </div>
      <script type="application/json" class="route-data" data-dist="{d['id']}">{route_data}</script>
    </div>""")

    return f"""<section class="section-pad" id="route">
  <div class="container">
    <p class="eyebrow">The route</p>
    <h2>Four routes, one start line</h2>
    <p class="lede mt-6 max-narrow">
      The marathon rolls gently to halfway, climbs once around 20km, then drops away over the
      final two kilometres into the finish. The 22km front-loads its climbing early and descends
      home. The 11km stays closest to the village, in the suburban streets short of the
      smallholding grid the 22km reaches. The 5km barely leaves the flat — 13m of vertical spread
      across the whole loop.
    </p>

    <div class="route-tabs" role="tablist" aria-label="Select a distance to view its route">{tabs}</div>
    {''.join(panels)}

    <div class="cta-strip">
      {cta("Enter now", "after-route")}
    </div>
  </div>
</section>
"""


# ------------------------------------------------------- qualifying prose --

def build_qualifying_prose():
    q = CONFIG["qualifiers"]
    comrades = q["comrades"]
    two_oceans = q["twoOceans"]
    flagship = dist_by_id("42_2km")

    stats = [
        (f"{comrades['entryCap']:,}", f"Comrades centenary entries — up from {comrades['previousCap']:,}"),
        (f"{two_oceans['entryCap']:,}", f"Two Oceans Ultra entries — up from {two_oceans['previousCap']:,}"),
        ("~49 000", "runners chasing a sub-5:00 marathon in this window"),
        ("100th", f"Comrades edition — {comrades['edition'].split('—')[-1].strip()}"),
    ]
    stat_cards = "".join(
        f"""<div class="stat-card"><div class="stat-num">{esc(val)}</div><div class="stat-lbl">{esc(lbl)}</div></div>"""
        for val, lbl in stats
    )

    return f"""<section class="qualifying-prose section-pad" id="qualifying-2027">
  <div class="container container--narrow">
    <p class="eyebrow">For qualifier hunters</p>
    <h2>Qualifying for Comrades 2027 and Two Oceans 2027</h2>

    <p class="lede mt-6">
      2027 is a big year for both of South Africa's major ultramarathons, and that is why MadMac's
      October date matters more than usual.
    </p>

    <div class="stat-grid">{stat_cards}</div>

    <div class="qual-caveat" style="margin-top: 2rem;">
      <p><strong>MadMac's online entries close 22 September 2026 at 21:00 — the same day the
      Comrades centenary ballot closes.</strong> Two qualifier-shaped decisions, one week, one date.</p>
    </div>

    <h3>Comrades Marathon 2027 — the centenary</h3>
    <p>
      The {comrades['edition']}, run {comrades['dateDisplay']}. Qualifying window:
      {comrades['qualifyingWindowDisplay']}, standard: a 42.2km marathon under 4:59:59.
    </p>

    <h3>Totalsports Two Oceans Marathon 2027</h3>
    <p>
      The {two_oceans['raceType']}, run {two_oceans['dateDisplay']}. Qualifiers run
      {two_oceans['qualifyingWindowDisplay']} count, and {two_oceans['seedingNote'].lower()}
    </p>

    <h3>Is MadMac fast enough for that standard?</h3>
    <p>
      Yes: about {flagship['totalAscentM']}m of total ascent across {flagship['gpxDistanceKm']:.2f}km,
      computed from the official GPX — the same territory as a fast big-city marathon.
      {flagship['profileSummary']} The downhill finish is a real asset if you're chasing a time.
    </p>

    <h3>What "single lap" actually means here</h3>
    <p>
      The marathon does not repeat a circuit — the thing runners actually object to in multi-lap
      qualifier races. It does include out-and-back sections, visible on the map above; "single
      lap" means no repeated loop, not that the course never doubles back on itself.
    </p>

    <ul>
      <li><strong>The standard:</strong> {q['standard']}, for both Comrades and Two Oceans seeding.</li>
      <li><strong>MadMac's cut-off:</strong> {flagship['cutoffDisplay']} — generous, but not the same number as the qualifying standard.</li>
      <li><strong>Altitude:</strong> the course sits at roughly {CONFIG['course']['altitudeApprox']}m.
      Most of the field is Gauteng-based and acclimatised; if you're travelling from the coast to
      chase a qualifier, budget for that.</li>
    </ul>

    <p style="margin-top: 1.5rem; font-size: 0.85rem; color: var(--text-faint);">
      MadMac's qualifier positioning for 2026/2027 was covered by Vaalweekblad and The Citizen in
      August 2026, alongside other Vaal-region marathons offering early centenary qualifying
      opportunities.
    </p>

    <div class="cta-strip">
      {cta("Enter the 42.2km", "qualifying-prose", "42_2km")}
    </div>
  </div>
</section>
"""


# -------------------------------------------------------------- prize money --

def build_prizes():
    prize = CONFIG["prizeMoney"]
    masters_categories = {"Veteran 40+", "Master 50+", "Grandmaster 60+"}

    rows = []
    for row in prize["categories"]:
        cls = "masters-row" if row["category"] in masters_categories else ""
        vals = "".join(
            f'<td class="num">{rand(row[k]) if isinstance(row[k], (int, float)) or row[k] is None else row[k]}</td>'
            for k in ("42_2km", "22km", "11km")
        )
        rows.append(f'<tr class="{cls}"><td>{esc(row["category"])}</td><td>{esc(row["place"])}</td>{vals}</tr>')

    return f"""<section class="section-pad" id="prizes">
  <div class="container">
    <p class="eyebrow">Prize money</p>
    <h2>R{prize['totalR']//1000} 000, paid equally</h2>

    <div class="prize-highlight">
      <div>
        <div class="total">{rand(prize['totalR'])}</div>
        <p style="margin-top: 0.25rem;">total prize money across every distance</p>
      </div>
      <p style="max-width: 40ch; color: var(--ink-100);">{prize['equalGenderStatement']}</p>
    </div>

    <p class="mt-6" style="max-width: none;">
      The MadMac field is well spread across the age categories, and the prize money is spread to
      match — the highlighted rows below pay down to second and third place in every masters
      category, not just the open field.
    </p>

    <div class="prize-table-wrap">
      <table class="prize-table">
        <thead><tr><th>Category</th><th>Place</th><th>42.2km</th><th>22km</th><th>11km</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    <p class="prize-footnote">* {prize['paymentNote']}</p>
  </div>
</section>
"""


# ------------------------------------------------------------------- proof --

def build_proof():
    t = CONFIG["testimonials"]
    gallery = CONFIG["gallery"]

    quote_cards = "".join(
        f"""<figure class="quote-card">
      <blockquote>&ldquo;{esc(q['quote'])}&rdquo;</blockquote>
      <figcaption>{esc(q['name'])} &middot; {esc(q['distance'])} &middot; {q['year']}</figcaption>
    </figure>"""
        for q in t["quotes"]
    )

    carousel_items = "".join(
        f"""<figure class="carousel-item">
      <img src="assets/img/gallery/{esc(p['file'])}" alt="{esc(p['alt'])}" loading="lazy" width="1000" height="667">
      <figcaption>{esc(p['caption'])}</figcaption>
    </figure>"""
        for p in gallery["photos"]
    )

    return f"""<section class="section-pad" id="proof">
  <div class="container">
    <p class="eyebrow">What runners say</p>
    <h2>{t['rating']} stars, {t['reviewCount']} reviews</h2>
    <p class="lede mt-6 max-narrow">
      Via <a class="link" href="{esc(t['sourceUrl'])}" target="_blank" rel="noopener">Race Pass</a>,
      from runners who've actually finished.
    </p>

    <div class="quote-grid">{quote_cards}</div>

    <div class="carousel-wrap">
      <div class="carousel" tabindex="0" aria-label="Photos from previous MadMac editions">
        <div class="carousel-track">{carousel_items}</div>
      </div>
      <div class="carousel-nav">
        <button type="button" class="btn btn-ghost btn-sm carousel-prev" aria-label="Previous photo">&larr;</button>
        <button type="button" class="btn btn-ghost btn-sm carousel-next" aria-label="Next photo">&rarr;</button>
      </div>
    </div>
  </div>
</section>
"""


# -------------------------------------------------------------------- faq --

def build_faq():
    faqs = CONFIG["faq"]
    items = "".join(
        f"""<details class="faq-item">
      <summary>{esc(item['q'])}</summary>
      <p>{esc(item['a'])}</p>
    </details>"""
        for item in faqs
    )
    return f"""<section class="section-pad" id="faq">
  <div class="container container--narrow">
    <p class="eyebrow">FAQ</p>
    <h2>Questions people actually ask</h2>
    <div class="faq-list mt-6">{items}</div>
  </div>
</section>
"""


# --------------------------------------------------------------- what you get --

def build_what_you_get():
    perks = CONFIG["perks"]
    rules = CONFIG["raceRules"]

    shirt_lines = "".join(
        f"<li>First {d['freeShirtsFirst']} {d['label']} entrants</li>"
        for d in CONFIG["distances"] if d["freeShirtsFirst"]
    )

    return f"""<section class="section-pad" id="what-you-get">
  <div class="container">
    <p class="eyebrow">What you get</p>
    <h2>Medal, shirt, timing, refreshments</h2>

    <div class="perks-grid">
      <div class="perk-card">
        <h3>Race t-shirt</h3>
        <p>{esc(perks['tshirt'])}</p>
      </div>
      <div class="perk-card">
        <h3>Finisher medal</h3>
        <p>{esc(perks['medal'])}</p>
      </div>
      <div class="perk-card">
        <h3>Timing &amp; results</h3>
        <p>{esc(rules['timing'])} Distance boards {esc(rules['distanceBoards']).lower()}, waterpoints
        {esc(rules['waterpoints']).lower()} Results published on
        <a class="link" href="https://{esc(rules['resultsPublishedOn'])}" target="_blank" rel="noopener">{esc(rules['resultsPublishedOn'])}</a>.</p>
      </div>
      <div class="perk-card">
        <h3>Free race shirts</h3>
        <ul style="margin-top: 0.5rem; display: grid; gap: 0.25rem; font-size: 0.9rem; color: var(--text-muted); padding-left: 1.1rem; list-style: disc;">
          {shirt_lines}
        </ul>
        <p style="margin-top: 0.5rem;">Additional shirts available at R{perks['extraShirtFeeR']}.</p>
      </div>
      <div class="perk-card">
        <h3>Goodie bags</h3>
        <p>{perks['goodieBags']:,} goodie bags for the field.</p>
      </div>
      <div class="perk-card plato-card">
        <h3>Platō Meyerton discount</h3>
        <p>{esc(perks['platoOffer']['discount'])} at {esc(perks['platoOffer']['venue'])} —
        {esc(perks['platoOffer']['condition'])}</p>
      </div>
    </div>
  </div>
</section>
"""


# ---------------------------------------------------------------- practical --

def build_practical():
    collection = CONFIG["numberCollection"]
    rules = CONFIG["raceRules"]
    course = CONFIG["course"]
    amenities = CONFIG["amenities"]

    rows = "".join(
        f"""<tr class="{'race-day' if c.get('raceDay') else ''}">
      <td>{esc(c['dateDisplay'])}</td><td>{esc(c['time'])}</td><td>{esc(c['venue'])}</td>
    </tr>"""
        for c in collection
    )

    return f"""<section class="section-pad" id="practical">
  <div class="container">
    <p class="eyebrow">Practical info</p>
    <h2>Number collection &amp; race-day logistics</h2>
    <p class="lede mt-6 max-narrow">
      Five collection points across Johannesburg and the Vaal before race week — a genuine
      convenience, not just admin.
    </p>

    <div class="collection-table-wrap">
      <table class="collection-table">
        <thead><tr><th>Date</th><th>Time</th><th>Venue</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <div class="practical-notes">
      <div class="practical-note">
        <strong>On site</strong>
        {', '.join(amenities)}, confirmed on Race Pass.
      </div>
      <div class="practical-note">
        <strong>Start &amp; finish</strong>
        Start and finish are about 200m apart at Café du Cirque, so expect separate start and
        finish chutes.
      </div>
      <div class="practical-note">
        <strong>Licences</strong>
        {esc(rules['licenceNote'])}
      </div>
      <div class="practical-note">
        <strong>On course</strong>
        {esc(rules['prohibited'])}
      </div>
      <div class="practical-note">
        <strong>Age &amp; prize giving</strong>
        {esc(rules['ageCategoryNote'])}
      </div>
      <div class="practical-note">
        <strong>Appeals</strong>
        {esc(rules['appeals'])}
      </div>
    </div>

    <p style="margin-top: 1.5rem; font-size: 0.85rem; color: var(--text-faint); max-width: none;">
      Detailed bag-drop, parking and spectator-access instructions for the 2026 edition will be
      published closer to race day. The course sits at roughly {course['altitudeApprox']}m —
      worth knowing if you're travelling up from the coast.
    </p>
  </div>
</section>
"""


# ------------------------------------------------------------ email capture --

def build_email():
    ec = CONFIG["emailCapture"]
    configured = "true" if ec.get("endpointUrl") else "false"
    action = esc(ec.get("endpointUrl") or "#")

    return f"""<section class="email-section section-pad" id="stay-updated">
  <div class="container">
    <div class="email-card">
      <p class="eyebrow" style="justify-content: center;">Not ready to enter yet?</p>
      <h2>We'll remind you before entries close</h2>
      <p class="mx-auto mt-6" style="text-align: center;">
        One email, before online entries close on {CONFIG['entries']['onlineCloseDisplay']}.
        No spam, and never shared with anyone else.
      </p>

      <form id="email-form" class="email-form" method="post" action="{action}"
        target="_blank" rel="noopener" data-configured="{configured}">
        <div class="email-form-fields">
          <label for="email-input" class="visually-hidden">Email address</label>
          <input id="email-input" name="{esc(ec.get('fieldName') or 'email')}" type="email" required
            class="email-input" placeholder="you@example.com" autocomplete="email">
          <button type="submit" class="btn btn-primary">Notify me</button>
        </div>
        <p class="email-status" role="status" aria-live="polite"></p>
      </form>

      <p class="email-consent">
        Your email is collected by Meyerton Athletics Club under POPIA solely to send you a
        reminder before entries close. It is not shared with sponsors or third parties, and you
        can unsubscribe at any time. See our
        <a href="#footer">contact details</a> to opt out.
      </p>
    </div>
  </div>
</section>
"""


# ------------------------------------------------------------- sponsor marquee --

def build_sponsor_marquee():
    sponsors = CONFIG["sponsors"]["list"]
    # duplicated once so the CSS animation can loop seamlessly from -50%
    item_html = "".join(f'<span class="marquee-item">{esc(s)}</span>' for s in sponsors)
    return f"""<section class="sponsor-marquee" aria-hidden="true">
  <p class="marquee-label">Proudly supported by</p>
  <div class="marquee-viewport">
    <div class="marquee-track">
      <div class="marquee-set">{item_html}</div>
      <div class="marquee-set">{item_html}</div>
    </div>
  </div>
</section>
"""


# ------------------------------------------------------------------ footer --

def build_footer():
    contact = CONFIG["contact"]
    sponsors = CONFIG["sponsors"]["list"]
    fb = CONFIG["facebook"]

    contact_items = []
    if contact.get("email"):
        contact_items.append(f'<li><a href="mailto:{esc(contact["email"])}">{esc(contact["email"])}</a></li>')
    if contact.get("phone"):
        contact_items.append(f'<li><a href="tel:{esc(contact["phone"])}">{esc(contact["phone"])}</a></li>')
    if contact.get("whatsapp"):
        contact_items.append(f'<li><a href="https://wa.me/{esc(contact["whatsapp"])}" target="_blank" rel="noopener">WhatsApp</a></li>')
    contact_items.append(f'<li><a href="{esc(fb["pageUrl"])}" target="_blank" rel="noopener">Facebook</a></li>')
    if contact.get("instagram"):
        contact_items.append(f'<li><a href="{esc(contact["instagram"])}" target="_blank" rel="noopener">Instagram</a></li>')

    sponsor_chips = "".join(f'<span class="sponsor-chip">{esc(s)}</span>' for s in sponsors)

    return f"""<footer class="site-footer" id="footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-col">
        <div class="footer-brand">
          <span class="brand-mark" aria-hidden="true"></span>
          <strong style="font-family: var(--font-display); font-style: italic; color: var(--ink-0);">Midvaal MadMac</strong>
        </div>
        <p style="font-size: 0.85rem;">Organised by {esc(CONFIG['edition']['organiser'])}.</p>
        <p class="footer-clown">Finishing at Café du Cirque — yes, that clown is the club mascot.</p>
      </div>
      <div class="footer-col">
        <h4>Contact</h4>
        <ul>{''.join(contact_items)}</ul>
      </div>
      <div class="footer-col">
        <h4>Results &amp; entries</h4>
        <ul>
          <li><a href="{esc(CONFIG['entries']['entryUrl'])}" target="_blank" rel="noopener">Enter on Race Pass</a></li>
          <li><a href="https://{esc(CONFIG['resultsUrl'].replace('https://','').replace('http://',''))}" target="_blank" rel="noopener">Past results (finishtime.co.za)</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Sponsors</h4>
        <div class="sponsor-wall">{sponsor_chips}</div>
      </div>
    </div>

    <div class="footer-bottom">
      <span>&copy; {CONFIG['edition']['year']} {esc(CONFIG['edition']['organiser'])}. All rights reserved.</span>
      <span>By entering you agree to the race rules above and Race Pass's terms of entry.</span>
    </div>
  </div>
</footer>
"""


# --------------------------------------------------------------- assembly --

def divider():
    return f'<div class="section-divider">{motif_svg("", "1.5")}</div>'


def build_body_scripts():
    ec = CONFIG["emailCapture"]
    analytics = CONFIG["analytics"]
    body_attrs = (
        f'data-analytics-provider="{esc(analytics.get("provider") or "none")}" '
        f'data-analytics-ga4="{esc(analytics.get("ga4Id") or "")}" '
        f'data-analytics-plausible="{esc(analytics.get("plausibleDomain") or "")}"'
    )
    return body_attrs


def main():
    body_attrs = build_body_scripts()

    body = "\n".join([
        build_header(),
        '<main id="main">',
        build_hero(),
        build_qualifier_panel(),
        divider(),
        build_why(),
        build_distances(),
        divider(),
        build_route(),
        build_qualifying_prose(),
        build_prizes(),
        divider(),
        build_proof(),
        build_what_you_get(),
        build_practical(),
        build_faq(),
        build_email(),
        "</main>",
        build_sponsor_marquee(),
        build_footer(),
    ])

    html = f"""<!doctype html>
<html lang="en-ZA">
<head>
{build_head()}</head>
<body {body_attrs}>
{body}
<script src="assets/js/nav.js" defer></script>
<script src="assets/js/countdown.js" defer></script>
<script src="assets/js/route.js" defer></script>
<script src="assets/js/carousel.js" defer></script>
<script src="assets/js/email.js" defer></script>
<script src="assets/js/analytics.js" defer></script>
</body>
</html>
"""

    out_path = ROOT / "index.html"
    out_path.write_text(html)
    print(f"wrote {out_path.relative_to(ROOT)} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
