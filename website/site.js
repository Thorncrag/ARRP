(function () {
  "use strict";

  const feedbackAddress = "smith.benjamin.j@icloud.com";

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
      const subject = encodeURIComponent("ARRP feedback: " + title);
      const body = encodeURIComponent(
        "Page: " + title + "\n" +
        "URL: " + window.location.href + "\n\n" +
        "Feedback, correction, source, or review:\n"
      );
      link.href = "mailto:" + feedbackAddress + "?subject=" + subject + "&body=" + body;
    });
  }

  document.addEventListener("DOMContentLoaded", initializePageActions);
  if (typeof document$ !== "undefined") {
    document$.subscribe(initializePageActions);
  }
})();
