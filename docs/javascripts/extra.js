(function () {
  const storageKeys = {
    navOpen: "smlcoke.reader.navOpen",
    tocOpen: "smlcoke.reader.tocOpen",
    navWidth: "smlcoke.reader.navWidth",
    tocWidth: "smlcoke.reader.tocWidth",
  };

  const icons = {
    nav: '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="6" height="16" rx="1.6"></rect><path d="M13 7h8"></path><path d="M13 12h8"></path><path d="M13 17h5"></path></svg>',
    toc: '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M6 5h12"></path><path d="M6 12h9"></path><path d="M6 19h6"></path><circle cx="3.5" cy="5" r=".8"></circle><circle cx="3.5" cy="12" r=".8"></circle><circle cx="3.5" cy="19" r=".8"></circle></svg>',
  };

  let heroTimer = null;

  function onPageReady(callback) {
    if (window.document$ && typeof window.document$.subscribe === "function") {
      window.document$.subscribe(callback);
      return;
    }

    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback);
    } else {
      callback();
    }
  }

  function readStorage(key, fallback) {
    try {
      const value = window.localStorage.getItem(key);
      return value === null ? fallback : value;
    } catch (_) {
      return fallback;
    }
  }

  function writeStorage(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch (_) {
      // Storage can be unavailable in strict privacy modes.
    }
  }

  function readBool(key) {
    return readStorage(key, "0") === "1";
  }

  function setBool(key, value) {
    writeStorage(key, value ? "1" : "0");
  }

  function clampWidth(width, side) {
    const min = side === "toc" ? 176 : 192;
    const maxBySide = side === "toc" ? 420 : 520;
    const maxByViewport = Math.max(min, Math.floor(window.innerWidth * 0.42));
    return Math.min(Math.max(width, min), Math.min(maxBySide, maxByViewport));
  }

  function readWidth(key, side) {
    const value = Number.parseInt(readStorage(key, ""), 10);
    return Number.isFinite(value) ? clampWidth(value, side) : null;
  }

  function setSidebarWidth(side, width) {
    const key = side === "toc" ? storageKeys.tocWidth : storageKeys.navWidth;
    const cssVar = side === "toc" ? "--reader-toc-width" : "--reader-nav-width";
    const clamped = clampWidth(width, side);
    document.documentElement.style.setProperty(cssVar, `${clamped}px`);
    writeStorage(key, String(clamped));
  }

  function restoreSidebarWidths() {
    const navWidth = readWidth(storageKeys.navWidth, "nav");
    const tocWidth = readWidth(storageKeys.tocWidth, "toc");

    if (navWidth) {
      document.documentElement.style.setProperty("--reader-nav-width", `${navWidth}px`);
    }

    if (tocWidth) {
      document.documentElement.style.setProperty("--reader-toc-width", `${tocWidth}px`);
    }
  }

  function createToggleButton(kind, label) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `reader-layout-toggle reader-layout-toggle--${kind}`;
    button.innerHTML = icons[kind];
    button.setAttribute("aria-label", label);
    button.setAttribute("title", label);
    button.setAttribute("aria-pressed", "false");
    return button;
  }

  function ensureReaderControls() {
    const header = document.querySelector(".md-header__inner");
    if (!header) return null;

    let controls = header.querySelector(".reader-layout-controls");
    if (!controls) {
      controls = document.createElement("div");
      controls.className = "reader-layout-controls";
      controls.append(
        createToggleButton("nav", "展开或隐藏左侧导航"),
        createToggleButton("toc", "展开或隐藏右侧目录")
      );

      const title = header.querySelector(".md-header__title");
      if (title) {
        title.after(controls);
      } else {
        header.append(controls);
      }
    }

    const navButton = controls.querySelector(".reader-layout-toggle--nav");
    const tocButton = controls.querySelector(".reader-layout-toggle--toc");

    if (navButton && !navButton.dataset.bound) {
      navButton.dataset.bound = "true";
      navButton.addEventListener("click", function () {
        setBool(storageKeys.navOpen, !document.body.classList.contains("reader-nav-open"));
        applyReaderState();
      });
    }

    if (tocButton && !tocButton.dataset.bound) {
      tocButton.dataset.bound = "true";
      tocButton.addEventListener("click", function () {
        setBool(storageKeys.tocOpen, !document.body.classList.contains("reader-toc-open"));
        applyReaderState();
      });
    }

    return controls;
  }

  function applyReaderState() {
    const controls = ensureReaderControls();
    const nav = document.querySelector(".md-sidebar--primary");
    const toc = document.querySelector(".md-sidebar--secondary");
    const navAvailable = Boolean(nav && !nav.hasAttribute("hidden"));
    const tocAvailable = Boolean(toc && !toc.hasAttribute("hidden"));
    const navOpen = navAvailable && readBool(storageKeys.navOpen);
    const tocOpen = tocAvailable && readBool(storageKeys.tocOpen);

    document.body.classList.toggle("reader-nav-open", navOpen);
    document.body.classList.toggle("reader-toc-open", tocOpen);

    if (controls) {
      const navButton = controls.querySelector(".reader-layout-toggle--nav");
      const tocButton = controls.querySelector(".reader-layout-toggle--toc");

      controls.hidden = !navAvailable && !tocAvailable;

      if (navButton) {
        navButton.hidden = !navAvailable;
        navButton.setAttribute("aria-pressed", navOpen ? "true" : "false");
      }

      if (tocButton) {
        tocButton.hidden = !tocAvailable;
        tocButton.setAttribute("aria-pressed", tocOpen ? "true" : "false");
      }
    }
  }

  function installSidebarResizer(sidebar, side) {
    if (!sidebar || sidebar.querySelector(".reader-sidebar-resizer")) return;

    const handle = document.createElement("div");
    handle.className = `reader-sidebar-resizer reader-sidebar-resizer--${side}`;
    handle.setAttribute("role", "separator");
    handle.setAttribute("aria-orientation", "vertical");
    handle.setAttribute("tabindex", "0");
    handle.setAttribute("title", side === "toc" ? "拖动调整右侧目录宽度" : "拖动调整左侧导航宽度");
    sidebar.append(handle);

    handle.addEventListener("pointerdown", function (event) {
      event.preventDefault();

      const startX = event.clientX;
      const startWidth = sidebar.getBoundingClientRect().width;
      document.body.classList.add("reader-sidebar-resizing");

      function onPointerMove(moveEvent) {
        const delta = moveEvent.clientX - startX;
        const nextWidth = side === "toc" ? startWidth - delta : startWidth + delta;
        setSidebarWidth(side, nextWidth);
      }

      function onPointerUp() {
        document.body.classList.remove("reader-sidebar-resizing");
        window.removeEventListener("pointermove", onPointerMove);
        window.removeEventListener("pointerup", onPointerUp);
      }

      window.addEventListener("pointermove", onPointerMove);
      window.addEventListener("pointerup", onPointerUp, { once: true });
    });

    handle.addEventListener("keydown", function (event) {
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;

      event.preventDefault();
      const currentWidth = sidebar.getBoundingClientRect().width;
      const delta = event.key === "ArrowRight" ? 16 : -16;
      setSidebarWidth(side, currentWidth + delta);
    });
  }

  function initReaderLayout() {
    restoreSidebarWidths();
    applyReaderState();
    const nav = document.querySelector(".md-sidebar--primary:not([hidden])");
    const toc = document.querySelector(".md-sidebar--secondary:not([hidden])");
    installSidebarResizer(nav, "nav");
    installSidebarResizer(toc, "toc");
  }

  function initHeroBackground() {
    const hero = document.querySelector(".hero-container");
    if (heroTimer) {
      window.clearInterval(heroTimer);
      heroTimer = null;
    }

    if (!hero) return;

    const images = [
      "assets/homepage/bg1.jpg",
      "assets/homepage/bg2.jpg",
      "assets/homepage/bg3.png",
      "assets/homepage/bg4.jpg",
      "assets/homepage/bg5.jpg",
      "assets/homepage/bg6.jpg",
      "assets/homepage/bg7.jpg",
    ];

    images.forEach(function (src) {
      const img = new Image();
      img.src = src;
    });

    let currentIndex = 0;
    hero.style.backgroundImage = `url('${images[currentIndex]}')`;

    heroTimer = window.setInterval(function () {
      currentIndex = (currentIndex + 1) % images.length;
      hero.style.backgroundImage = `url('${images[currentIndex]}')`;
    }, 5000);
  }

  function openPdfLinksInNewTab() {
    document.querySelectorAll("a[href$='.pdf']").forEach(function (link) {
      link.setAttribute("target", "_blank");
      link.setAttribute("rel", "noopener");
    });
  }

  onPageReady(function () {
    initReaderLayout();
    initHeroBackground();
    openPdfLinksInNewTab();
  });
})();
