/* Sticky mobile CTA bar.

   Desktop keeps both primary actions in the sticky header, but below
   900px that header collapses to a hamburger — so from the moment the
   hero scrolls away there is no call to action on screen at all, for
   roughly ten thousand pixels of route maps, prize tables and gallery.
   This puts the same two actions back at the bottom of the viewport.

   It is deliberately NOT shown while the hero is still visible: the hero
   already carries both buttons full-width, and stacking a duplicate pair
   over them just eats the fold. The bar is revealed once the hero's own
   action row has scrolled out of view, and hidden again when the visitor
   scrolls back up to it or reaches the mailing-list section (where the
   form itself is the action, and a floating "Stay in touch" pointing at
   the section you are already in is noise).

   The markup ships in the HTML with the bar already hidden, and CSS
   confines it to <900px, so with JS disabled it simply never appears —
   which is the correct degradation, not a broken half-state. */
(function () {
  "use strict";

  function init() {
    var bar = document.querySelector(".mobile-cta-bar");
    if (!bar) return;
    if (!("IntersectionObserver" in window)) return;

    var hero = document.querySelector(".hero-actions");
    var listSection = document.getElementById("stay-updated");
    if (!hero) return;

    var heroVisible = true;
    var listVisible = false;

    function sync() {
      var show = !heroVisible && !listVisible;
      bar.classList.toggle("is-visible", show);
      /* aria-hidden as well as the class: the bar is a duplicate of
         controls that already exist elsewhere in the document, so while
         it is off-screen it should be out of the accessibility tree
         rather than read twice by a screen reader. */
      bar.setAttribute("aria-hidden", show ? "false" : "true");
    }

    new IntersectionObserver(function (entries) {
      heroVisible = entries[0].isIntersecting;
      sync();
    }, { rootMargin: "0px 0px -20% 0px" }).observe(hero);

    if (listSection) {
      new IntersectionObserver(function (entries) {
        listVisible = entries[0].isIntersecting;
        sync();
      }, { rootMargin: "0px" }).observe(listSection);
    }

    sync();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
