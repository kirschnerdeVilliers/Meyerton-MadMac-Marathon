/* Mobile header nav: toggles the collapsed section menu. Desktop shows the
   full nav inline (pure CSS, no JS involved); this only runs the
   hamburger/dropdown behaviour below the 900px breakpoint. */
(function () {
  "use strict";

  function init() {
    var toggle = document.querySelector(".nav-toggle");
    var menu = document.getElementById("mobile-nav");
    if (!toggle || !menu) return;

    function close() {
      toggle.setAttribute("aria-expanded", "false");
      menu.hidden = true;
    }
    function open() {
      toggle.setAttribute("aria-expanded", "true");
      menu.hidden = false;
    }

    toggle.addEventListener("click", function () {
      var expanded = toggle.getAttribute("aria-expanded") === "true";
      if (expanded) close(); else open();
    });

    menu.querySelectorAll(".mobile-nav-link").forEach(function (link) {
      link.addEventListener("click", close);
    });

    document.addEventListener("keydown", function (evt) {
      if (evt.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
        close();
        toggle.focus();
      }
    });

    document.addEventListener("click", function (evt) {
      if (toggle.getAttribute("aria-expanded") !== "true") return;
      if (!menu.contains(evt.target) && evt.target !== toggle && !toggle.contains(evt.target)) {
        close();
      }
    });

    // collapse back to the desktop layout without leaving the menu stuck open
    window.addEventListener("resize", function () {
      if (window.innerWidth >= 900) close();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
