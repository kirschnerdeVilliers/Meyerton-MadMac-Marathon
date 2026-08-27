/* Progressive enhancement over a native scroll-snap carousel — the photos
   are already reachable by touch, trackpad, or keyboard (the track itself
   is focusable and scrolls with arrow keys in every major browser). These
   buttons just add an explicit click target for people who want one. */
(function () {
  "use strict";

  function init() {
    document.querySelectorAll(".carousel-wrap").forEach(function (wrap) {
      var track = wrap.querySelector(".carousel");
      var prev = wrap.querySelector(".carousel-prev");
      var next = wrap.querySelector(".carousel-next");
      if (!track || !(prev || next)) return;

      function step(dir) {
        var item = track.querySelector(".carousel-item");
        var amount = item ? item.getBoundingClientRect().width + 16 : track.clientWidth * 0.8;
        track.scrollBy({ left: dir * amount, behavior: "smooth" });
      }

      if (prev) prev.addEventListener("click", function () { step(-1); });
      if (next) next.addEventListener("click", function () { step(1); });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
