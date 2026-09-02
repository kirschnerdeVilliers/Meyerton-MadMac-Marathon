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
 */

const ALLOWED_ORIGINS = [
  "https://midvaalmadmac.co.za",
  "https://kirschnerdevilliers.github.io",
  "http://localhost:4611",
  "http://localhost:4612",
];

const LIST_ID = 3; // Brevo list "MadMac 2026 Entry Reminders"
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

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
    try {
      const contentType = request.headers.get("Content-Type") || "";
      if (contentType.includes("application/json")) {
        const body = await request.json();
        email = (body.email || "").trim();
      } else {
        const form = await request.formData();
        email = (form.get("email") || "").trim();
      }
    } catch {
      return json({ success: false, error: "bad_request" }, 400, origin);
    }

    if (!EMAIL_RE.test(email)) {
      return json({ success: false, error: "invalid_email" }, 400, origin);
    }

    const brevoRes = await fetch("https://api.brevo.com/v3/contacts", {
      method: "POST",
      headers: {
        "api-key": env.BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      body: JSON.stringify({ email, listIds: [LIST_ID], updateEnabled: true }),
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
