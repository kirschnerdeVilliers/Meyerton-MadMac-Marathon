# Midvaal MadMac — landing page

A single-page marketing site for Meyerton Athletics Club's Midvaal MadMac road race. Its only
job is converting visitors into Race Pass entries, with a secondary email capture for people who
aren't ready yet. Full brief context lives with whoever commissioned this build; this README is
the practical "how do I change something" reference.

## Quick start

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

No build step, no `npm install`, no bundler. It's a static folder — deploy it to Netlify,
Cloudflare Pages, or any static host by uploading the directory as-is.

## How this is put together

Race facts live in **one file**, `data/race-config.json`. Two small Python scripts (stdlib only,
nothing to install) turn that config plus the official GPX files into the final static
`index.html`:

```bash
python3 tools/build-routes.py   # GPX -> data/routes/*.json + elevation SVGs + route motif
python3 tools/render.py         # race-config.json + routes -> index.html
```

Why two steps instead of hand-editing `index.html` directly: keeping race facts in one JSON file
(so a non-developer can update fees, dates and collection points without touching markup) while
still shipping fully static, crawlable HTML with zero client-side content templating — good for
SEO and for a site that has to work with no build tooling at deploy time. The *deployed* site is
still just plain files; the render step only runs when someone is updating the content, not on
every visit.

**If you edit `data/race-config.json`, re-run `tools/render.py` and commit the new `index.html`.**
If the GPX files change (a re-measured course, a new distance), run `build-routes.py` first.

### What's genuinely dynamic client-side JS

Everything else in `index.html` is real static markup, but a few things can only be done in the
browser:

- `assets/js/countdown.js` — the live countdown to entries closing
- `assets/js/route.js` — the route tabs and the lazy-loaded Leaflet map (loads Leaflet + OSM tiles
  only once the route section scrolls into view, and only builds each distance's map the first
  time its tab is opened)
- `assets/js/email.js` — client-side email validation and the honest "not connected yet" message
  when no signup endpoint is configured
- `assets/js/analytics.js` — the GA4/Plausible wrapper and outbound-click tracking
- `assets/js/carousel.js` — the prev/next buttons on the photo carousel (the carousel itself is a
  native CSS scroll-snap track and works without JS — this just adds explicit click targets)
- `assets/js/nav.js` — the mobile header hamburger menu (desktop nav is pure CSS, no JS involved)

Section nav links in the header (`NAV_LINKS` in `tools/render.py`) point at five section ids —
add, remove or reorder entries there if the page's section structure changes; the mobile menu is
generated from the same list. The sponsor marquee at the foot of the page (`build_sponsor_marquee`
in `tools/render.py`) reads from the same `sponsors.list` in `race-config.json` as the footer, so
there's still only one place to edit the sponsor roster.

## Updating for the 2027 edition

1. Edit `data/race-config.json` — date, fees, collection points, qualifying windows, entry URL,
   sponsors, whatever changed. The file has inline comments (`_comment`) explaining structure.
2. If the course changed, drop the new GPX files in `data/gpx/` (keep the same naming pattern) and
   update the `gpxFile` / `stravaRouteUrl` fields per distance, then run `build-routes.py`.
3. Run `python3 tools/render.py`.
4. Check the diff in `index.html` looks sane, then commit and redeploy.
5. Regenerate `assets/img/og-madmac-2026.png` if the headline copy changed (see below).

The 2025→2026 edition changed the distance line-up (10km → 11km), the headline sponsor, and every
price — none of that required touching markup, which is the point of this structure.

## Email capture — wiring a real provider

`data/race-config.json` → `emailCapture.endpointUrl` is currently `null`. Until it's set, the form
is fully built and styled but blocks submission with an honest on-page message instead of
pretending a sign-up went anywhere.

To go live, the form (`<form id="email-form" method="post" action="...">` in `index.html`, built
from `build_email()` in `tools/render.py`) works with the plain embed contract of any of these —
set `endpointUrl` to the value noted, re-render, and add any provider-specific hidden fields
directly in `build_email()`:

- **Formspree** — `endpointUrl` = your form's endpoint, e.g. `https://formspree.io/f/xxxxxxx`.
  No extra hidden fields needed.
- **Buttondown** — `endpointUrl` = `https://buttondown.com/api/emails/embed-subscribe/<username>`.
- **Mailchimp** — `endpointUrl` = the embedded form's `action` URL from your audience's signup
  form settings. Mailchimp also requires a honeypot hidden input (name starts with `b_`, specific
  to your audience/list IDs) — copy it from Mailchimp's own embed snippet into `build_email()`.

The form posts with `target="_blank"` so the provider's own confirmation page opens in a new tab
rather than navigating away from the landing page.

**POPIA note:** the form's consent line states Meyerton Athletics Club as the data holder and what
the address is used for. If you swap providers, make sure the new provider's own privacy practices
still match what that line promises.

## Analytics

`data/race-config.json` → `analytics`: set `provider` to `"ga4"` or `"plausible"` and fill in
`ga4Id` or `plausibleDomain`, then re-render. Outbound Race Pass clicks fire an `entry_click` event
tagged with `position` (which section the click came from — hero, qualifier-panel, distance-card,
after-pricing, after-route, qualifying-prose, header) and `distance` where relevant, so you can see
whether the qualifier panel actually outperforms the hero. Email signups fire `email_signup`
separately. Meta Pixel isn't wired yet — add it as its own script block in `build_head()` when
you have an ID.

## Design notes

- Palette and the green→yellow→orange gradient are approximated from the supplied flyer
  screenshots and the race t-shirt design, **not sampled from original vector files** — nobody
  had those at build time. Confirm exact hex values against the real flyer/shirt artwork before
  this becomes the permanent brand reference, and update the CSS custom properties at the top of
  `assets/css/site.css`.
- The recurring route-line graphic (hero background, section dividers, footer) is the *actual*
  42.2km GPX track, projected and normalised by `build_motif()` in `tools/build-routes.py` — not a
  generic decorative squiggle. In the hero specifically it draws itself in on a slow loop (CSS
  `stroke-dashoffset` animation, calibrated against the real path length computed alongside the
  projection), and stops on `prefers-reduced-motion`. The section-divider and footer instances of
  the same motif stay static — animation is scoped to the hero only, via `motif_svg(animate=True)`.
- Fonts are Google Fonts (Big Shoulders Display for headings, Inter for body), loaded with
  `preconnect` + `display=swap`. If self-hosting fonts is preferred later, swap the `<link>` tags
  in `build_head()` for local `@font-face` declarations.

## Regenerating the OG share image

`assets/img/og-madmac-2026.png` (1200×630) was built by rendering a small standalone HTML file
with the same design tokens and screenshotting it with headless Chrome at exact pixel dimensions:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --hide-scrollbars --window-size=1200,630 \
  --screenshot="$(pwd)/assets/img/og-madmac-2026.png" \
  "http://localhost:8000/path-to-a-1200x630-source.html"
```

The headline is the real wordmark image (`assets/img/madmac-wordmark.png`, cropped tight from the
club's own logo file — a plain flat "MIDVAAL MADMAC" with no clown and no sponsor strip, useful
elsewhere too), not typeset text — no font-loading race to worry about if you regenerate it. The
source HTML that composited it isn't kept in the repo (a one-off build step); recreate it from
this doc if the copy changes: same design tokens as `site.css`, `<img class="wordmark">` with
`height: 220px` sized against the wordmark's actual aspect ratio, `align-self: flex-start` inside
the flex column (without it, `align-items: stretch` distorts the image — a real bug hit while
building this).

## Domain

`tools/render.py` has `SITE_URL = "https://midvaalmadmac.co.za"` as a **placeholder** — canonical
URL, OG tags and JSON-LD all derive from it. Update it to the real production domain before launch
and re-render.

## Proof, FAQ and gallery content

The "What runners say" (testimonials + photo carousel) and FAQ sections pull real content, not
placeholders:

- `data/race-config.json` → `testimonials`: rating, review count, and quote cards — sourced from
  Race Pass's public listing page (name, distance, year, quote text; obvious concatenation typos
  in the source, e.g. "reallyenjoyable", were cleaned up, wording otherwise unchanged).
- `data/race-config.json` → `faq`: the six Q&As Race Pass itself publishes (their entry
  cancellation/substitution/transfer policy, number collection, race-number lookup), plus three
  MadMac-specific ones answered from facts already in this config (qualifier status, race-day
  entry, the cut-off-vs-qualifying-standard distinction).
- `data/race-config.json` → `gallery` + `assets/img/gallery/*.jpg`: seven real photos from the
  2025 edition (start line, on-course marshalling, the race MC, finishers, medals), pulled from
  the club's own public Facebook page. The header/footer brand mark (`assets/img/madmac-badge.jpg`)
  and 11 of the 15 sponsor logos (`assets/img/sponsors/`) came from the same source, supplied
  directly rather than scraped — see "Still needed" below for the handful still missing.

To add more photos: drop files in `assets/img/gallery/`, add an entry to `gallery.photos` in
`race-config.json` (file name, alt text, caption), and re-render. To refresh testimonials, repeat
the Race Pass scrape (their reviews and FAQ answers are behind click-to-expand accordions, not
present in the initial HTML — see `git log` / ask for the extraction approach if redoing this).

## Still needed at handover

Blocking honest copy on the page right now:

- **Road surface (tar/gravel split), per distance.** The GPX gives distance and elevation, not
  surface. Nothing on the page currently claims "fast" for this reason — only "flat", which the
  GPX elevation data supports.

Also needed, currently rendered as omitted/placeholder in `race-config.json` → `placeholders`
rather than guessed:

- Temporary ASA licence fee for 2026 (2025 was R120; the 2026 flyer looks like it may have changed
  but is unreadable at the supplied resolution)
- Course measurement certificate number
- What the 11km's 10km timing split is actually used for
- Written confirmation MadMac is on the CMA's 2027 approved-qualifier list and the Two Oceans
  qualifier list (the page states the qualifying standard and windows factually, but doesn't claim
  MadMac's own approved-list status either way)
- Nothing — all 20 sponsors have real logos now, including Midvaal Local Municipality and
  Meyerton Athletics Club (the last two), Switch, AfriGuard, Oasis Water and dabeb-elram (the
  "three more logos on the flyer aren't legible at this resolution" the original brief flagged,
  plus one extra), and Ver-Chem alongside Ver-Bolt once the real logos showed "Uber-Bolt" in the
  brief was a mishearing. All in `assets/img/sponsors/`, referenced from `sponsors.list` in
  `race-config.json`, rendering as images in the marquee and footer.
- Exact flyer/t-shirt hex values, to replace the approximated palette
- The gallery carousel and header/footer badge now use real 2025 MadMac photos, sourced from the
  club's own Facebook page — see `assets/img/gallery/` and README section above. Still worth
  adding: a strong single photo for the hero itself and the OG share image, both of which still
  work typographically.
- Direct URL for the Vaalweekblad/Citizen qualifier-angle coverage referenced in the "Qualifying
  for Comrades 2027 and Two Oceans 2027" section (currently described, not linked)
- Email capture endpoint URL (see above)
- Analytics IDs (GA4/Plausible) and Meta Pixel ID
- Organiser phone / WhatsApp number — email is wired (`midvaalmadmac@gmail.com`, found on the
  club's public Facebook "About" page) and Facebook is linked; phone/WhatsApp still render only if
  present in `race-config.json` → `contact`
- Instagram, if MAC has one
- Bag-drop, parking and spectator-access specifics for the practical info section
- How the R59 crossing is marshalled
- Whether sub-5:00 pacing buses are confirmed for race day — this is one of the more persuasive
  things the qualifier panel could offer and is worth adding the moment it's confirmed

Two things worth doing before this page goes live that are outside this codebase entirely, both
cheap, both higher-value than anything on this page: Race Pass's own listing doesn't mention
Comrades or Two Oceans anywhere despite that being the main reason people enter, and its entry-close
date should be checked against the authoritative 22 September 2026 21:00 used throughout this site.
