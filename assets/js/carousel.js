/* Progressive enhancement over a native scroll-snap carousel — the photos
   are already reachable by touch, trackpad, or keyboard (the track itself
   is focusable and scrolls with arrow keys in every major browser). The
   prev/next buttons add an explicit click target; autoplay adds a slow,
   pausable drift so the gallery reads as "alive" without anyone touching it. */
(function () {
  "use strict";

  var AUTOPLAY_MS = 4200;
  var reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function stepAmount(track) {
    var item = track.querySelector(".carousel-item");
    return item ? item.getBoundingClientRect().width + 16 : track.clientWidth * 0.8;
  }

  function initOne(wrap) {
    var track = wrap.querySelector(".carousel");
    var prev = wrap.querySelector(".carousel-prev");
    var next = wrap.querySelector(".carousel-next");
    if (!track) return;

    function step(dir) {
      track.scrollBy({ left: dir * stepAmount(track), behavior: "smooth" });
    }

    if (prev) prev.addEventListener("click", function () { step(-1); restartAutoplay(); });
    if (next) next.addEventListener("click", function () { step(1); restartAutoplay(); });

    // Nothing to autoplay if the track doesn't actually overflow.
    if (reducedMotion || track.scrollWidth <= track.clientWidth + 4) return;

    var timer = null;

    function tick() {
      var atEnd = track.scrollLeft + track.clientWidth >= track.scrollWidth - 4;
      if (atEnd) {
        track.scrollTo({ left: 0, behavior: "smooth" });
      } else {
        track.scrollBy({ left: stepAmount(track), behavior: "smooth" });
      }
    }

    function start() {
      if (!timer) timer = setInterval(tick, AUTOPLAY_MS);
    }
    function stop() {
      if (timer) { clearInterval(timer); timer = null; }
    }
    function restartAutoplay() {
      stop();
      start();
    }

    wrap.addEventListener("mouseenter", stop);
    wrap.addEventListener("mouseleave", start);
    wrap.addEventListener("touchstart", stop, { passive: true });
    wrap.addEventListener("focusin", stop);
    wrap.addEventListener("focusout", start);

    // Only run while the carousel is actually on screen.
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) start(); else stop();
        });
      }, { threshold: 0.3 });
      io.observe(wrap);
    } else {
      start();
    }
  }

  function init() {
    document.querySelectorAll(".carousel-wrap").forEach(initOne);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
