/* Progressive enhancement over a plain HTML form (method="post",
   action=<endpoint>). Without JS the form still works as a real POST —
   the endpoint (a small Cloudflare Worker, see workers/email-signup/)
   accepts both a JSON body and plain form-urlencoded, precisely so this
   fallback keeps functioning. With JS, submission is upgraded to a
   fetch() call so the page can show a truthful success/error message
   instead of just assuming the native POST worked — the Worker's own
   response is what confirms Brevo actually accepted the signup.

   If no endpoint has been configured yet (race-config.json
   emailCapture.endpointUrl is null), the form's action is left as "#" and
   this script blocks submission with an honest status message instead of
   pretending the sign-up went anywhere. */
(function () {
  "use strict";

  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function setStatus(form, message, kind) {
    var status = form.querySelector(".email-status");
    if (!status) return;
    status.textContent = message;
    status.className = "email-status" + (kind ? " " + kind : "");
  }

  function init() {
    var form = document.getElementById("email-form");
    if (!form) return;
    var input = form.querySelector(".email-input");
    var button = form.querySelector("button[type=submit]");
    var configured = form.getAttribute("data-configured") === "true";

    form.addEventListener("submit", function (evt) {
      evt.preventDefault();
      var value = (input.value || "").trim();

      if (!EMAIL_RE.test(value)) {
        setStatus(form, "That doesn't look like a valid email address.", "error");
        input.focus();
        return;
      }

      if (!configured) {
        setStatus(
          form,
          "Sign-ups aren't connected yet — add an endpoint in data/race-config.json (see README).",
          "error"
        );
        return;
      }

      if (button) button.disabled = true;
      setStatus(form, "Sending…", "");

      var payload = {};
      payload[input.name || "email"] = value;
      fetch(form.action, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then(function (res) {
          return res.json().then(function (data) {
            return { ok: res.ok && data.success, data: data };
          });
        })
        .then(function (result) {
          if (button) button.disabled = false;
          if (result.ok) {
            if (typeof window.madmacTrack === "function") {
              window.madmacTrack("email_signup");
            }
            setStatus(form, "Thanks — you're on the list.", "success");
            form.reset();
          } else {
            setStatus(form, "Couldn't save that — please try again.", "error");
          }
        })
        .catch(function () {
          if (button) button.disabled = false;
          setStatus(form, "Couldn't reach the sign-up service — please try again.", "error");
        });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
