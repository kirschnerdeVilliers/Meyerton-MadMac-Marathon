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
