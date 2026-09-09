/* madmac-email-signup — Cloudflare Worker
 *
 * Proxies the site's own email-capture form to Brevo's real REST API
 * (POST /v3/contacts), rather than Brevo's documented "Simple HTML" form
 * embed — that embed silently discards non-JS submissions (returns
 * {"success":true} but creates no contact; see README.md "Email capture"
 * in the main repo for how this was confirmed). Calling the REST API
 * directly is Brevo's actual supported way to create a contact
 * server-side, and it lets the site keep its own styled <form> instead of
 * embedding Brevo's hosted widget.
 *
 * The Brevo API key is a secret — set with `wrangler secret put
 * BREVO_API_KEY`, never committed here and never hardcoded.
 *
 * Abuse handling. This endpoint is public by necessity — its URL is in
 * the page source, because the visitor's browser has to post to it — and
 * CORS does not protect it: an Access-Control-Allow-Origin header governs
 * what a browser will let a page READ back, not whether this Worker
 * processes the request. Anything posting from outside a browser ignores
 * it entirely. So there are four independent checks below, cheapest
 * first, and each one rejects before the Brevo call rather than after:
 *
 *   1. honeypot   — a field no human sees; non-empty means a bot
 *   2. timing     — submitted implausibly fast after page load
 *   3. rate limit — per-IP, when the binding is configured
 *   4. Turnstile  — real challenge, when TURNSTILE_SECRET is set
 *
 * 3 and 4 are optional and inert until configured, so this file deploys
 * and behaves correctly with neither of them present. 1 and 2 are always
 * on and cost nothing. See README.md in this directory to switch the
 * other two on.
 *
 * All four fail CLOSED but SILENT: a rejected request gets the same
 * {"success":true} shape a real signup gets. Telling a bot which check
 * caught it is free tuning information for whoever is running it, and
 * the only cost of lying is that a human who somehow trips a check does
 * not learn why — which is the right trade for a race mailing list.
 */

const ALLOWED_ORIGINS = [
  "https://midvaalmadmac.co.za",
  "https://kirschnerdevilliers.github.io",
  "http://localhost:4611",
  "http://localhost:4612",
];

// Brevo list 3, originally created as "MadMac 2026 Entry Reminders". From
// September 2026 the site's form is an ongoing race mailing list rather
// than a one-off reminder, and it keeps writing to this same list — so the
// contacts in it were gathered under TWO different promises. OPTIN_SCOPE
// below is what tells them apart: any contact WITHOUT it signed up under
// the old reminder-only wording and has not consented to next-year
// marketing. Segment on that before sending a 2027 campaign.
const LIST_ID = 3;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Fastest a real person plausibly submits: they have to read the consent
// paragraph above the field and type an address. Deliberately generous —
// this is meant to catch instant machine posts, not hurried humans, and a
// false positive here silently loses a real signup.
const MIN_ELAPSED_MS = 2500;

function corsHeaders(origin) {
  const allowed = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allowed,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

function json(body, status, origin) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders(origin) },
  });
}

// A rejection that looks exactly like a success. See the "fail CLOSED but
// SILENT" note at the top of this file for why.
function silentlyDiscard(origin) {
  return json({ success: true }, 200, origin);
}

async function turnstilePassed(env, token, ip) {
  if (!env.TURNSTILE_SECRET) return true; // not configured — check skipped
  if (!token) return false;
  const form = new FormData();
  form.append("secret", env.TURNSTILE_SECRET);
  form.append("response", token);
  if (ip) form.append("remoteip", ip);
  try {
    const res = await fetch(
      "https://challenges.cloudflare.com/turnstile/v0/siteverify",
      { method: "POST", body: form }
    );
    const data = await res.json();
    return data.success === true;
  } catch {
    // Turnstile itself being unreachable must not take the signup form
    // down with it — the other three checks still apply.
    return true;
  }
}

async function withinRateLimit(env, ip) {
  if (!env.RATE_LIMITER || !ip) return true; // binding not configured
  try {
    const { success } = await env.RATE_LIMITER.limit({ key: ip });
    return success;
  } catch {
    return true;
  }
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders(origin) });
    }
    if (request.method !== "POST") {
      return json({ success: false, error: "method_not_allowed" }, 405, origin);
    }

    // Accepts either a JSON body (the JS-enhanced fetch() path) or a plain
    // form-urlencoded POST (the no-JS fallback — the site's <form> still
    // has a real method/action so it keeps working with JS disabled).
    let email;
    let honeypot = "";
    let elapsed = null;
    let turnstileToken = "";
    try {
      const contentType = request.headers.get("Content-Type") || "";
      let get;
      if (contentType.includes("application/json")) {
        const body = await request.json();
        get = (k) => body[k];
      } else {
        const form = await request.formData();
        get = (k) => form.get(k);
      }
      email = (get("email") || "").trim();
      honeypot = (get("company") || "").trim();
      turnstileToken = (get("cf-turnstile-response") || "").trim();
      const raw = get("_elapsed");
      // Absent or non-numeric means the no-JS path, which cannot stamp a
      // time. That is a legitimate submission and skips the timing check.
      if (raw !== null && raw !== undefined && String(raw).trim() !== "") {
        const n = Number(raw);
        if (Number.isFinite(n)) elapsed = n;
      }
    } catch {
      return json({ success: false, error: "bad_request" }, 400, origin);
    }

    // 1. Honeypot. No human fills a field they cannot see.
    if (honeypot !== "") return silentlyDiscard(origin);

    // 2. Timing.
    if (elapsed !== null && elapsed < MIN_ELAPSED_MS) return silentlyDiscard(origin);

    if (!EMAIL_RE.test(email)) {
      return json({ success: false, error: "invalid_email" }, 400, origin);
    }

    const ip = request.headers.get("CF-Connecting-IP") || "";

    // 3. Per-IP rate limit, when the binding is configured.
    if (!(await withinRateLimit(env, ip))) return silentlyDiscard(origin);

    // 4. Turnstile, when the secret is configured.
    if (!(await turnstilePassed(env, turnstileToken, ip))) return silentlyDiscard(origin);

    const brevoRes = await fetch("https://api.brevo.com/v3/contacts", {
      method: "POST",
      headers: {
        "api-key": env.BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      // These three attributes must already exist in Brevo (Contacts ->
      // Settings -> Contact attributes) or Brevo answers 400 and every
      // signup fails with a generic error. updateEnabled:true means a
      // returning address gets them written too, which is right — they
      // have just re-consented under the current wording.
      body: JSON.stringify({
        email,
        listIds: [LIST_ID],
        updateEnabled: true,
        attributes: {
          OPTIN_SCOPE: "race-news",
          OPTIN_DATE: new Date().toISOString().slice(0, 10),
          OPTIN_SOURCE: "midvaalmadmac.co.za",
        },
      }),
    });

    // 201 = new contact created; 204 = existing contact updated (already
    // subscribed) — both are a genuine success from the visitor's side.
    if (brevoRes.status === 201 || brevoRes.status === 204) {
      return json({ success: true }, 200, origin);
    }

    // Brevo returns 400 duplicate_parameter for some already-subscribed
    // cases too — also a success, not a real error.
    const errBody = await brevoRes.json().catch(() => ({}));
    if (brevoRes.status === 400 && errBody.code === "duplicate_parameter") {
      return json({ success: true }, 200, origin);
    }

    return json({ success: false, error: "brevo_error" }, 502, origin);
  },
};
