/* Route section: accessible tabs + lazy-loaded Leaflet map per distance.
   Route coordinates are inlined as JSON in each panel at build time (see
   tools/render.py) — no runtime GPX parsing, no fetch, works over file://
   for local review too. Leaflet itself is only pulled in once the route
   section scrolls into view, and each map is only constructed the first
   time its tab is shown, so the section never costs anything until a
   visitor actually reaches it. */
(function () {
  "use strict";

  var LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
  var LEAFLET_CSS_INTEGRITY = "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=";
  var LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
  var LEAFLET_JS_INTEGRITY = "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=";

  var leafletLoadPromise = null;
  var mapsById = {};

  function loadLeaflet() {
    if (leafletLoadPromise) return leafletLoadPromise;
    leafletLoadPromise = new Promise(function (resolve, reject) {
      if (window.L) { resolve(window.L); return; }
      var link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = LEAFLET_CSS;
      link.integrity = LEAFLET_CSS_INTEGRITY;
      link.crossOrigin = "";
      document.head.appendChild(link);

      var script = document.createElement("script");
      script.src = LEAFLET_JS;
      script.integrity = LEAFLET_JS_INTEGRITY;
      script.crossOrigin = "";
      script.onload = function () { resolve(window.L); };
      script.onerror = reject;
      document.head.appendChild(script);
    });
    return leafletLoadPromise;
  }

  function readRouteData(panel) {
    var script = panel.querySelector(".route-data");
    if (!script) return null;
    try {
      return JSON.parse(script.textContent);
    } catch (e) {
      return null;
    }
  }

  function initMap(panel, distId) {
    if (mapsById[distId]) return;
    var mapEl = panel.querySelector(".route-map");
    if (!mapEl) return;
    var data = readRouteData(panel);
    if (!data || !data.coords || !data.coords.length) return;

    loadLeaflet().then(function (L) {
      var placeholder = mapEl.querySelector(".map-placeholder");
      if (placeholder) placeholder.remove();

      var map = L.map(mapEl, {
        scrollWheelZoom: false,
        attributionControl: true,
      });

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
      }).addTo(map);

      var latlngs = data.coords.map(function (c) { return [c[0], c[1]]; });
      var line = L.polyline(latlngs, { color: "#ef6a1f", weight: 4, opacity: 0.9 }).addTo(map);

      var startIcon = L.divIcon({ className: "route-marker route-marker-start", html: "", iconSize: [14, 14] });
      var finishIcon = L.divIcon({ className: "route-marker route-marker-finish", html: "", iconSize: [14, 14] });
      L.marker(latlngs[0], { icon: startIcon, alt: "Start" }).addTo(map).bindTooltip("Start");
      L.marker(latlngs[latlngs.length - 1], { icon: finishIcon, alt: "Finish" }).addTo(map).bindTooltip("Finish");

      map.fitBounds(line.getBounds(), { padding: [24, 24] });

      // re-enable scroll-zoom only once the visitor has deliberately
      // interacted with the map, so page-scroll isn't hijacked by accident
      map.once("click focus", function () { map.scrollWheelZoom.enable(); });

      mapsById[distId] = map;
    }).catch(function () {
      var mapEl2 = panel.querySelector(".route-map");
      if (mapEl2) {
        mapEl2.innerHTML = '<div class="map-placeholder">Map couldn\'t load — try the GPX download or Strava link below.</div>';
      }
    });
  }

  function invalidateVisibleMap(distId) {
    if (mapsById[distId]) {
      // Leaflet needs a nudge after its container becomes visible again
      setTimeout(function () { mapsById[distId].invalidateSize(); }, 50);
    }
  }

  // Draws the elevation line in once per panel (stroke-dashoffset, calibrated
  // in tools/build-routes.py). Re-adding the class on an already-revealed
  // panel is a harmless no-op, so this is safe to call on every tab switch.
  function revealElevation(panel) {
    if (!panel) return;
    panel.querySelectorAll(".elevation-draw").forEach(function (el) {
      el.classList.add("elevation-visible");
    });
  }

  function activateTab(tabs, panels, tab) {
    tabs.forEach(function (t) {
      var selected = t === tab;
      t.setAttribute("aria-selected", selected ? "true" : "false");
      t.tabIndex = selected ? 0 : -1;
    });
    var targetId = tab.getAttribute("aria-controls");
    panels.forEach(function (panel) {
      panel.hidden = panel.id !== targetId;
    });
    var distId = tab.getAttribute("data-dist");
    var targetPanel = document.getElementById(targetId);
    initMap(targetPanel, distId);
    invalidateVisibleMap(distId);
    revealElevation(targetPanel);
  }

  function initTabs() {
    var tablist = document.querySelector('[role="tablist"].route-tabs');
    if (!tablist) return;
    var tabs = Array.prototype.slice.call(tablist.querySelectorAll('[role="tab"]'));
    var panels = Array.prototype.slice.call(document.querySelectorAll(".route-panel"));

    tabs.forEach(function (tab, i) {
      tab.addEventListener("click", function () { activateTab(tabs, panels, tab); });
      tab.addEventListener("keydown", function (evt) {
        var next = null;
        if (evt.key === "ArrowRight") next = tabs[(i + 1) % tabs.length];
        if (evt.key === "ArrowLeft") next = tabs[(i - 1 + tabs.length) % tabs.length];
        if (next) { evt.preventDefault(); next.focus(); activateTab(tabs, panels, next); }
      });
    });

    // lazy-init: only touch the network/Leaflet once the route section is
    // actually approaching the viewport
    var section = document.getElementById("route");
    var activeTab = tabs.find(function (t) { return t.getAttribute("aria-selected") === "true"; }) || tabs[0];
    if (section && "IntersectionObserver" in window) {
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var activePanel = document.getElementById(activeTab.getAttribute("aria-controls"));
            initMap(activePanel, activeTab.getAttribute("data-dist"));
            revealElevation(activePanel);
            observer.disconnect();
          }
        });
      }, { rootMargin: "200px" });
      observer.observe(section);
    } else if (activeTab) {
      var activePanelFallback = document.getElementById(activeTab.getAttribute("aria-controls"));
      initMap(activePanelFallback, activeTab.getAttribute("data-dist"));
      revealElevation(activePanelFallback);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTabs);
  } else {
    initTabs();
  }
})();
