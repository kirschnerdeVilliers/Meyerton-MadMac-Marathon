/* Header behaviour: the mobile hamburger/dropdown menu, a small
   compact-on-scroll effect on the sticky header (subtle, functional —
   not decorative motion), and the scroll-spy that marks which section you
   are currently in.

   The spy is progressive enhancement like everything else here: it only ever
   *adds* aria-current to a link that is already a working anchor, so with no
   JS the nav behaves exactly as it did before. */
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

  /* Marks the nav link for the section you are currently reading.

     The page has thirteen sections and five nav links, so most of the time you
     are in a section with no link of its own — #why, #one-lap, #qualifying-2027
     and so on. The right answer there is the last linked section you passed,
     which is what this computes: not "which section is on screen" but "which
     linked section did you most recently enter".

     aria-current="location" rather than a class, because that is exactly what
     this means and it gets announced to a screen reader for free. */
  function initScrollSpy() {
    var links = [].slice.call(
      document.querySelectorAll('.site-nav a[href^="#"], .mobile-nav a[href^="#"]')
    );
    if (!links.length) return;

    var targets = [];
    links.forEach(function (link) {
      var id = link.getAttribute("href").slice(1);
      var section = id && document.getElementById(id);
      if (section) targets.push({ link: link, section: section });
    });
    if (!targets.length) return;

    var header = document.querySelector(".site-header");
    var current = null;
    var last = 0;

    function update() {
      // The sticky header covers the top of the viewport, so a section counts
      // as entered once it passes below the header rather than below zero.
      var line = (header ? header.getBoundingClientRect().height : 0) + window.innerHeight * 0.25;
      var active = null;
      for (var i = 0; i < targets.length; i++) {
        if (targets[i].section.getBoundingClientRect().top <= line) active = targets[i];
      }
      if (active === current) return;
      current = active;
      targets.forEach(function (t) {
        if (active && t.link.getAttribute("href") === active.link.getAttribute("href")) {
          t.link.setAttribute("aria-current", "location");
        } else {
          t.link.removeAttribute("aria-current");
        }
      });
    }

    /* Throttled on a timestamp rather than requestAnimationFrame. rAF is the
       usual choice, but it does not run in a background tab, which would leave
       the spy frozen on whatever section you were in when you switched away —
       and it made this impossible to test headlessly. The work here is ten
       getBoundingClientRect reads and no writes unless the section actually
       changed, so it is cheap enough to run straight off the scroll event. */
    function onScroll() {
      var now = Date.now();
      if (now - last < 100) return;
      last = now;
      update();
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    update();
  }

  function init() {
    initCompactHeader();
    initScrollSpy();
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
