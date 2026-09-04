/* Live countdown to online entries close, and the switch that flips the
   whole page from "enter this year" to "join the list for next year" the
   moment that time passes.

   Those two jobs live together on purpose: the countdown reaching zero IS
   the flip event, and this file already owns the target datetime and
   already ticks every second.

   render.py writes a build-time data-entry-phase onto <html> and renders
   BOTH phases into the HTML; CSS shows whichever matches. That build-time
   value goes stale as soon as it's deployed, so setting the attribute here
   is what actually gets real visitors the right page — a nightly rebuild
   is only a backstop for crawlers and the few visitors without JS. See
   "Entries open/closed" in README.md. */
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
      closeEntries();
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

  function closeEntries() {
    document.documentElement.setAttribute("data-entry-phase", "closed");
    // Sits outside the phase blocks so it survives the swap. Without it a
    // screen-reader user on the page at the close time gets no signal that
    // the hero just changed under them.
    var closedNote = document.querySelector("[data-closed-note]");
    if (closedNote) closedNote.hidden = false;
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

  function boot() {
    // Run before init(): in the closed phase the countdown card is
    // display:none, so its own tick loop can't be relied on to flip the
    // page. Read the target off the element regardless of visibility.
    var el = document.querySelector("[data-countdown-target]");
    if (el) {
      var target = new Date(el.getAttribute("data-countdown-target"));
      if (!isNaN(target.getTime()) && target.getTime() <= Date.now()) {
        closeEntries();
      }
    }
    init();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
