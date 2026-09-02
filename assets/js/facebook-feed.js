/* Facebook Page Plugin, lazy-loaded — same pattern as route.js's Leaflet
   loading. The plugin markup (#fb-root + .fb-page, see build_facebook_feed()
   in tools/render.py) sits in the page from the start since it's just a div;
   the actual cost — Facebook's JS SDK and the timeline iframe it builds — is
   only pulled in once the "Follow along" section approaches the viewport,
   so it never affects first paint/LCP. The static fallback link inside
   .fb-page (marked fb-xfbml-parse-ignore) stays visible for anyone the SDK
   never loads for — blocked, no JS, or offline. */
(function () {
  "use strict";

  var SDK_SRC = "https://connect.facebook.net/en_US/sdk.js#xfbml=1&version=v21.0";

  function loadSdk() {
    if (document.getElementById("facebook-jssdk")) return;
    var script = document.createElement("script");
    script.id = "facebook-jssdk";
    script.src = SDK_SRC;
    script.async = true;
    script.defer = true;
    script.crossOrigin = "anonymous";
    document.body.appendChild(script);
  }

  function init() {
    var section = document.getElementById("follow");
    if (!section) return;

    if ("IntersectionObserver" in window) {
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            loadSdk();
            observer.disconnect();
          }
        });
      }, { rootMargin: "200px" });
      observer.observe(section);
    } else {
      loadSdk();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
