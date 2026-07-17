(function () {
  "use strict";

  const participationUrl = "https://arrp-public-intake.vercel.app/";

  function pageTitle() {
    const heading = document.querySelector("article h1");
    if (!heading) return document.title;

    const copy = heading.cloneNode(true);
    copy.querySelectorAll(".headerlink").forEach(function (link) {
      link.remove();
    });
    return copy.textContent.trim();
  }

  function initializePageActions() {
    document.querySelectorAll("[data-arrp-print]").forEach(function (button) {
      if (button.dataset.arrpReady) return;
      button.dataset.arrpReady = "true";
      button.addEventListener("click", function () {
        window.print();
      });
    });

    document.querySelectorAll("[data-arrp-feedback]").forEach(function (link) {
      const title = pageTitle();
      const destination = new URL(participationUrl);
      destination.searchParams.set("mode", "contact");
      destination.searchParams.set("page_title", title);
      destination.searchParams.set("page", window.location.href);
      destination.searchParams.set("subject", "ARRP feedback: " + title);
      link.href = destination.toString();
    });
  }

  document.addEventListener("DOMContentLoaded", initializePageActions);
  if (typeof document$ !== "undefined") {
    document$.subscribe(initializePageActions);
  }
})();
