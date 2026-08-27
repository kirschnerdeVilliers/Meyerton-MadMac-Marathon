/* Header behaviour: the mobile hamburger/dropdown menu, and a small
   compact-on-scroll effect on the sticky header (subtle, functional —
   not decorative motion). Desktop nav itself is pure CSS, no JS involved. */
(function () {
  "use strict";

  function initCompactHeader() {
    var header = document.querySelector(".site-header");
    if (!header) return;
    var THRESHOLD = 40;
    function onScroll() {
      header.classList.toggle("is-scrolled", window.scrollY > THRESHOLD);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  function init() {
    initCompactHeader();
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
