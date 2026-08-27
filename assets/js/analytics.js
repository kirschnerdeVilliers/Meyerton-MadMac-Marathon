/* Provider-agnostic analytics wrapper. No-ops until an ID is supplied in
   race-config.json (see the data-analytics-* attributes on <body>, filled
   in by tools/render.py). Exposes window.madmacTrack(name, params) used by
   route.js and email.js, and wires outbound Race Pass clicks itself so
   every CTA is tagged by position + distance without extra markup work. */
(function () {
  "use strict";

  var body = document.body;
  var provider = body.getAttribute("data-analytics-provider") || "none";
  var ga4Id = body.getAttribute("data-analytics-ga4");
  var plausibleDomain = body.getAttribute("data-analytics-plausible");

  function track(eventName, params) {
    params = params || {};
    if (provider === "ga4" && typeof window.gtag === "function") {
      window.gtag("event", eventName, params);
    } else if (provider === "plausible" && typeof window.plausible === "function") {
      window.plausible(eventName, { props: params });
    } else {
      // No provider configured yet — surface events in the console so this
      // is easy to verify once GA4/Plausible IDs are added.
      if (window.console && window.location.hostname === "localhost") {
        console.info("[madmac analytics:noop]", eventName, params);
      }
    }
  }
  window.madmacTrack = track;

  function initProviderScripts() {
    if (provider === "ga4" && ga4Id) {
      var s = document.createElement("script");
      s.async = true;
      s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(ga4Id);
      document.head.appendChild(s);
      window.dataLayer = window.dataLayer || [];
      window.gtag = function () { window.dataLayer.push(arguments); };
      window.gtag("js", new Date());
      window.gtag("config", ga4Id);
    } else if (provider === "plausible" && plausibleDomain) {
      var p = document.createElement("script");
      p.defer = true;
      p.setAttribute("data-domain", plausibleDomain);
      p.src = "https://plausible.io/js/script.js";
      document.head.appendChild(p);
    }
  }

  function wireCtaTracking() {
    document.querySelectorAll("[data-cta]").forEach(function (link) {
      link.addEventListener("click", function () {
        track("entry_click", {
          position: link.getAttribute("data-cta"),
          distance: link.getAttribute("data-cta-distance") || "all",
        });
      });
    });
  }

  function init() {
    initProviderScripts();
    wireCtaTracking();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
