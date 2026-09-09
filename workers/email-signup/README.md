# madmac-email-signup

Small Cloudflare Worker that proxies the site's email-capture form to Brevo's real REST API
(`POST /v3/contacts`) instead of Brevo's "Simple HTML" form embed — that embed silently discards
submissions from anything that isn't Brevo's own JS (returns `{"success":true}` but creates no
contact). See the main repo's `README.md` → "Email capture" for the full story. Calling the REST
API directly is Brevo's actual supported way to create a contact server-side, and it lets the site
keep its own styled `<form>` instead of embedding Brevo's hosted widget.

## Before you deploy: create three Brevo contact attributes

**Do this first.** The Worker writes `OPTIN_SCOPE`, `OPTIN_DATE` and `OPTIN_SOURCE`
on every contact. Brevo rejects attributes it does not already know about, so if
these do not exist the API answers `400` and **every sign-up on the site fails**
with a generic error.

In Brevo: **Contacts → Settings → Contact attributes → Add an attribute**

| Attribute      | Type |
| -------------- | ---- |
| `OPTIN_SCOPE`  | Text |
| `OPTIN_DATE`   | Text |
| `OPTIN_SOURCE` | Text |

`OPTIN_SCOPE` is what separates the two consent groups on list 3. Contacts
without it signed up under the old "one reminder before entries close" wording
and have **not** consented to next-year marketing — segment on it before sending
any 2027 campaign. See the privacy notice, which promises exactly this.

## Deploy (run these yourself — the API key is a secret, never handled by Claude)

From this directory:

```bash
npx wrangler login          # only needed once per machine
npx wrangler deploy
npx wrangler secret put BREVO_API_KEY
# paste your Brevo API key when prompted (Brevo dashboard → SMTP & API → API Keys)
```

`wrangler deploy` prints the Worker's URL (`https://madmac-email-signup.<your-subdomain>.workers.dev`).
Send that URL back — it goes into `data/race-config.json` → `emailCapture.endpointUrl`.

## Notes

- `LIST_ID = 3` in `worker.js` is Brevo's "MadMac 2026 Entry Reminders" list. If that list is ever
  recreated (different ID), update this constant and redeploy.
- `ALLOWED_ORIGINS` in `worker.js` is a plain array (not a secret) — add an origin there and
  redeploy if the site ever moves domains or a new local dev port is added.
- If the pasted-in-chat key mentioned in the setup conversation is still the one set here,
  regenerate a fresh one in Brevo and re-run `wrangler secret put BREVO_API_KEY` with that instead
  — a key that was ever pasted into plaintext chat should be treated as exposed.

## Spam protection

The endpoint URL is public — it is in the page source, because the visitor's browser has to
post to it. CORS does **not** protect it: `Access-Control-Allow-Origin` governs what a browser
lets a page read back, not whether this Worker processes the request. Anything posting from
outside a browser ignores it. So `worker.js` runs four checks, cheapest first:

| Check | Configured? | What it catches |
|---|---|---|
| Honeypot (`company` field) | Always on | Bots that fill every field they find |
| Timing (`_elapsed` < 2500ms) | Always on | Instant machine posts |
| Per-IP rate limit | Optional binding | Someone hammering the endpoint |
| Cloudflare Turnstile | Optional secret | Everything else |

All four **fail closed but silent** — a rejected request gets the same `{"success":true}` a real
signup gets. Telling a bot which check caught it is free tuning information for whoever is
running it.

Because of that silence, `test.mjs` asserts on whether the Brevo call actually happened, which
is the only thing that distinguishes a block from a success. Run it before any change here:

```bash
cd workers/email-signup && npm test
```

No install and no network — the Brevo call is stubbed and an unexpected outbound fetch fails
the run.

### Deploying the current version

```bash
cd workers/email-signup && npx wrangler deploy
```

The honeypot and timing checks are live the moment that lands. Nothing else is needed for them,
and `data/race-config.json` needs no change.

### Turning on Turnstile (recommended)

1. Cloudflare dashboard → **Turnstile** → add a widget for `midvaalmadmac.co.za`. You get a
   **site key** (public) and a **secret key** (not public).
2. Put the site key in `data/race-config.json` → `emailCapture.turnstileSiteKey` — or edit it at
   `/admin/` under Email capture, where it is now a field. The widget and its script only render
   once that key is set; until then nothing extra loads.
3. Set the secret on the Worker, yourself — never paste it into a chat:
   ```bash
   npx wrangler secret put TURNSTILE_SECRET
   ```
4. `npx wrangler deploy`, then submit the real form once and confirm the contact lands in Brevo.

Order matters: if the site key goes live before the secret is set, `TURNSTILE_SECRET` is absent
and the Worker skips the check — signups keep working, they are just unprotected. The reverse
order (secret first, no site key) means the browser sends no token and **every signup is
silently discarded**. Set the secret first only if you are deploying both in one go.

### Turning on the rate limit

Uncomment the `[[ratelimits]]` block in `wrangler.toml`, check the syntax against Cloudflare's
current rate-limiting docs (this API has changed shape before), and redeploy. `worker.js`
checks for the binding and skips the check when it is absent, so a wrong or missing binding
degrades to "no rate limit" rather than breaking signups.
