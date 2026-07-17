(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.ARRP_CONTEXT_URLS = api;
}(typeof window !== "undefined" ? window : globalThis, function () {
  "use strict";

  function isArrpContextUrl(candidate) {
    if (candidate.protocol !== "https:" || candidate.username || candidate.password) return false;
    if (candidate.hostname === "thorncrag.github.io") return candidate.pathname === "/ARRP/" || candidate.pathname.startsWith("/ARRP/");
    return candidate.hostname === "github.com" && (candidate.pathname === "/Thorncrag/ARRP" || candidate.pathname.startsWith("/Thorncrag/ARRP/"));
  }

  function sanitizeContextUrl(value) {
    try {
      const candidate = new URL(String(value || "").trim());
      return isArrpContextUrl(candidate) ? candidate.href : "";
    } catch (_) {
      return "";
    }
  }

  return { sanitizeContextUrl };
}));
