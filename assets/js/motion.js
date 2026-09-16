/* Two small scroll-triggered enhancements, both progressive enhancement
   over content that already renders correctly without JS:

   1. Scroll-reveal — elements marked [data-reveal] fade/rise in once as
      they enter the viewport. The "hidden" starting state is only ever
      applied by this script (never in the static CSS), so a visitor with
      JS disabled, or a crawler, always sees the content in place.

   2. Scroll-scrub — paragraphs marked [data-scrub] have been split into
      per-word spans by render.py, and warm from faint to full as the
      paragraph crosses the viewport. The faint starting colour is only ever
      applied by this script, so without JS the words render at normal body
      colour rather than dimmed.

   3. Count-up — the qualifying-section stat numbers count from 0 to their
      real value once, then land on the exact server-rendered text (see
      data-count-final), so there's no risk of the animated version ever
      disagreeing with the number actually being claimed.

   All three no-op under prefers-reduced-motion. */
(function () {
  "use strict";

  var reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function initReveal() {
    if (reducedMotion || !("IntersectionObserver" in window)) return;
    var els = document.querySelectorAll("[data-reveal]");
    if (!els.length) return;
    els.forEach(function (el) { el.classList.add("reveal-init"); });
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("reveal-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );
    els.forEach(function (el) { io.observe(el); });
  }

  function initScrub() {
    if (reducedMotion) return;
    var els = [].slice.call(document.querySelectorAll("[data-scrub]"));
    if (!els.length) return;
    els.forEach(function (el) {
      el.classList.add("scrub-init");
      el._words = [].slice.call(el.querySelectorAll(".w"));
    });

    var ticking = false;

    function update() {
      ticking = false;
      var vh = window.innerHeight;
      els.forEach(function (el) {
        var words = el._words;
        if (!words.length) return;
        var rect = el.getBoundingClientRect();
        // 0 when the paragraph's top is 82% down the viewport, 1 once it has
        // travelled far enough that its last line is comfortably read.
        var start = vh * 0.82;
        var travel = start - vh * 0.3 + rect.height;
        var progress = travel > 0 ? (start - rect.top) / travel : 1;
        if (progress < 0) progress = 0;
        if (progress > 1) progress = 1;
        var lit = Math.round(progress * words.length);
        for (var i = 0; i < words.length; i++) {
          var on = i < lit;
          if (words[i]._on !== on) {
            words[i].classList.toggle("on", on);
            words[i]._on = on;
          }
        }
      });
    }

    function onScroll() {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(update);
      }
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    update();
  }

  function animateCount(el) {
    var target = parseInt(el.getAttribute("data-count-target"), 10);
    var final = el.getAttribute("data-count-final");
    if (!target || isNaN(target) || final == null) return;
    var start = null;
    var duration = 1300;
    function tick(now) {
      if (start === null) start = now;
      var p = Math.min(1, (now - start) / duration);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased).toLocaleString("en-ZA").replace(/,/g, " ");
      if (p < 1) {
        requestAnimationFrame(tick);
      } else {
        el.textContent = final;
      }
    }
    requestAnimationFrame(tick);
  }

  function initCountUp() {
    if (reducedMotion || !("IntersectionObserver" in window)) return;
    var els = document.querySelectorAll("[data-count-target]");
    if (!els.length) return;
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            animateCount(entry.target);
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.6 }
    );
    els.forEach(function (el) { io.observe(el); });
  }

  function init() {
    initReveal();
    initScrub();
    initCountUp();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
