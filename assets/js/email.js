/* Progressive enhancement over a plain HTML form (method="post",
   action=<provider endpoint>). Works with the normal embed contract of
   Mailchimp, Buttondown or Formspree unmodified — see README for the
   provider-specific hidden fields each one needs.

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
    var configured = form.getAttribute("data-configured") === "true";

    form.addEventListener("submit", function (evt) {
      var value = (input.value || "").trim();

      if (!EMAIL_RE.test(value)) {
        evt.preventDefault();
        setStatus(form, "That doesn't look like a valid email address.", "error");
        input.focus();
        return;
      }

      if (!configured) {
        evt.preventDefault();
        setStatus(
          form,
          "Sign-ups aren't connected yet — add an endpoint in data/race-config.json (see README).",
          "error"
        );
        return;
      }

      // Endpoint is configured and the form is valid — let the native POST
      // proceed (target="_blank" per the markup, so the provider's own
      // confirmation opens in a new tab rather than navigating away from
      // the page). Track the attempt and give immediate local feedback.
      if (typeof window.madmacTrack === "function") {
        window.madmacTrack("email_signup");
      }
      setStatus(form, "Thanks — check the tab that just opened to confirm.", "success");
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
