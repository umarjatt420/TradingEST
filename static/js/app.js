/**
 * Trading EST — responsive sidebar & shell
 * Breakpoints align with Bootstrap 5: md 768px, lg 992px
 */
(function () {
  "use strict";

  /**
   * Format money as SAR 1,234.56 (en-US grouping, 2 decimal places).
   */
  window.teFormatSar = function (value) {
    if (value === null || value === undefined || value === "") {
      return "—";
    }
    var n = Number(value);
    if (Number.isNaN(n)) {
      return "—";
    }
    return (
      "SAR " +
      n.toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })
    );
  };

  var STORAGE_MD = "tradingest.sidebar.mdExpanded";

  function width() {
    return window.innerWidth || document.documentElement.clientWidth;
  }

  function isDrawer() {
    return width() < 768;
  }

  function isMini() {
    var w = width();
    return w >= 768 && w < 992;
  }

  function isFull() {
    return width() >= 992;
  }

  function getSidebar() {
    return document.getElementById("teSidebar");
  }

  function getBackdrop() {
    return document.getElementById("teSidebarBackdrop");
  }

  function closeDrawer() {
    document.body.classList.remove("te-sidebar-open");
  }

  function openDrawer() {
    document.body.classList.add("te-sidebar-open");
  }

  function toggleDrawer() {
    document.body.classList.toggle("te-sidebar-open");
  }

  function setMdExpanded(expanded) {
    var el = getSidebar();
    if (!el) return;
    if (expanded) {
      el.classList.add("te-sidebar--expanded");
      document.body.classList.add("te-shell-sidebar-mini-expanded");
    } else {
      el.classList.remove("te-sidebar--expanded");
      document.body.classList.remove("te-shell-sidebar-mini-expanded");
    }
    try {
      localStorage.setItem(STORAGE_MD, expanded ? "1" : "0");
    } catch (e) {}
  }

  function toggleMdExpanded() {
    var el = getSidebar();
    if (!el) return;
    setMdExpanded(!el.classList.contains("te-sidebar--expanded"));
  }

  /**
   * Public API — used by onclick / data attributes
   */
  window.toggleSidebar = function () {
    if (isDrawer()) {
      toggleDrawer();
    } else if (isMini()) {
      toggleMdExpanded();
    }
  };

  function restoreMdState() {
    if (!isMini()) return;
    var el = getSidebar();
    if (!el) return;
    try {
      if (localStorage.getItem(STORAGE_MD) === "1") {
        setMdExpanded(true);
      }
    } catch (e) {}
  }

  function onResize() {
    var w = width();
    if (w >= 992) {
      closeDrawer();
      var sb = getSidebar();
      if (sb) sb.classList.remove("te-sidebar--expanded");
      document.body.classList.remove("te-shell-sidebar-mini-expanded");
    } else if (w >= 768) {
      closeDrawer();
    } else {
      var s2 = getSidebar();
      if (s2) s2.classList.remove("te-sidebar--expanded");
      document.body.classList.remove("te-shell-sidebar-mini-expanded");
    }
    syncShellClass();
  }

  function syncShellClass() {
    var body = document.body;
    body.classList.remove("sidebar-full", "sidebar-mini", "sidebar-overlay");
    if (isFull()) {
      body.classList.add("sidebar-full");
    } else if (isMini()) {
      body.classList.add("sidebar-mini");
    } else {
      body.classList.add("sidebar-overlay");
    }
  }

  function onNavClick(e) {
    if (!isDrawer()) return;
    var a = e.target.closest("a.nav-link");
    if (!a || !a.href) return;
    closeDrawer();
  }

  function onBackdropClick() {
    if (isDrawer() && document.body.classList.contains("te-sidebar-open")) {
      closeDrawer();
      return;
    }
    if (isMini() && getSidebar() && getSidebar().classList.contains("te-sidebar--expanded")) {
      setMdExpanded(false);
    }
  }

  function bindNavClose() {
    var nav = document.querySelector("#teSidebar .te-sidebar-nav");
    if (nav) nav.addEventListener("click", onNavClick);
  }

  function bindOpenButtons() {
    document.querySelectorAll("[data-te-sidebar-open]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        if (isDrawer()) openDrawer();
      });
    });
  }

  function bindExpandButton() {
    var btn = document.getElementById("teSidebarExpandBtn");
    if (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        if (isMini()) toggleMdExpanded();
      });
    }
  }

  function bindCloseButton() {
    var btn = document.getElementById("teSidebarCloseBtn");
    if (btn) btn.addEventListener("click", closeDrawer);
  }

  function bindBackdrop() {
    var bd = getBackdrop();
    if (bd) bd.addEventListener("click", onBackdropClick);
  }

  function onKeydown(e) {
    if (e.key === "Escape") {
      closeDrawer();
      if (isMini()) setMdExpanded(false);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    syncShellClass();
    restoreMdState();
    bindNavClose();
    bindOpenButtons();
    bindExpandButton();
    bindCloseButton();
    bindBackdrop();
    window.addEventListener("resize", function () {
      clearTimeout(window.__teResizeDebounce);
      window.__teResizeDebounce = setTimeout(onResize, 120);
    });
    document.addEventListener("keydown", onKeydown);
  });
})();
