/* Live countdown to online entries close. Reads the target ISO datetime
   from the element's data-target attribute (filled from race-config.json
   by tools/render.py), so the date lives in one place. */
(function () {
  "use strict";

  function pad(n) { return String(n).padStart(2, "0"); }

  function render(el, target) {
    var diffMs = target.getTime() - Date.now();
    var unitsEl = {
      days: el.querySelector('[data-unit="days"]'),
      hours: el.querySelector('[data-unit="hours"]'),
      minutes: el.querySelector('[data-unit="minutes"]'),
      seconds: el.querySelector('[data-unit="seconds"]'),
    };
    if (diffMs <= 0) {
      el.querySelectorAll(".countdown-unit .num").forEach(function (n) { n.textContent = "00"; });
      var closedNote = el.querySelector('[data-closed-note]');
      if (closedNote) closedNote.hidden = false;
      return false;
    }
    var totalSeconds = Math.floor(diffMs / 1000);
    var days = Math.floor(totalSeconds / 86400);
    var hours = Math.floor((totalSeconds % 86400) / 3600);
    var minutes = Math.floor((totalSeconds % 3600) / 60);
    var seconds = totalSeconds % 60;
    if (unitsEl.days) unitsEl.days.textContent = pad(days);
    if (unitsEl.hours) unitsEl.hours.textContent = pad(hours);
    if (unitsEl.minutes) unitsEl.minutes.textContent = pad(minutes);
    if (unitsEl.seconds) unitsEl.seconds.textContent = pad(seconds);
    return true;
  }

  function init() {
    var els = document.querySelectorAll("[data-countdown-target]");
    els.forEach(function (el) {
      var iso = el.getAttribute("data-countdown-target");
      if (!iso) return;
      var target = new Date(iso);
      if (isNaN(target.getTime())) return;
      var tick = function () {
        var stillRunning = render(el, target);
        if (!stillRunning && interval) clearInterval(interval);
      };
      tick();
      var interval = setInterval(tick, 1000);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
