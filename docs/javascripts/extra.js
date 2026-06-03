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
    copy: '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>',
  };

  let heroTimer = null;
  let resizeBound = false;

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
    button.dataset.side = kind;
    button.innerHTML = `${icons[kind]}<span class="reader-layout-toggle__text">${kind === "toc" ? "目录" : "导航"}</span>`;
    button.setAttribute("aria-label", label);
    button.setAttribute("title", label);
    button.setAttribute("aria-pressed", "false");
    return button;
  }

  function ensureReaderControls() {
    let controls = document.querySelector(".reader-layout-controls");
    if (!controls) {
      controls = document.createElement("div");
      controls.className = "reader-layout-controls";
      controls.setAttribute("aria-label", "阅读布局控制");
      controls.append(
        createToggleButton("nav", "展开或隐藏左侧导航"),
        createToggleButton("toc", "展开或隐藏右侧目录")
      );
      document.body.append(controls);
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

  function getSidebar(side) {
    const selector = side === "toc" ? ".md-sidebar--secondary" : ".md-sidebar--primary";
    const sidebar = document.querySelector(selector);
    return sidebar && !sidebar.hasAttribute("hidden") ? sidebar : null;
  }

  function positionReaderAffordances() {
    const nav = getSidebar("nav");
    const toc = getSidebar("toc");
    const navOpen = document.body.classList.contains("reader-nav-open");
    const tocOpen = document.body.classList.contains("reader-toc-open");
    const navButton = document.querySelector(".reader-layout-toggle--nav");
    const tocButton = document.querySelector(".reader-layout-toggle--toc");
    const navResizer = document.querySelector(".reader-sidebar-resizer--nav");
    const tocResizer = document.querySelector(".reader-sidebar-resizer--toc");

    if (navButton) navButton.style.left = "";
    if (tocButton) tocButton.style.right = "";

    positionSidebarResizer(navResizer, nav, navOpen, "nav");
    positionSidebarResizer(tocResizer, toc, tocOpen, "toc");
  }

  function positionSidebarResizer(handle, sidebar, isOpen, side) {
    if (!handle) return;

    if (!sidebar || !isOpen) {
      handle.hidden = true;
      return;
    }

    const rect = sidebar.getBoundingClientRect();
    const top = Math.max(rect.top + 10, 96);
    const bottom = Math.min(rect.bottom - 10, window.innerHeight - 18);
    const height = Math.max(bottom - top, 120);
    const left = side === "toc" ? rect.left - 7 : rect.right - 7;

    handle.hidden = false;
    handle.style.left = `${Math.round(left)}px`;
    handle.style.top = `${Math.round(top)}px`;
    handle.style.height = `${Math.round(height)}px`;
  }

  function applyReaderState() {
    const controls = ensureReaderControls();
    const navAvailable = Boolean(getSidebar("nav"));
    const tocAvailable = Boolean(getSidebar("toc"));
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

    window.requestAnimationFrame(positionReaderAffordances);
  }

  function installSidebarResizer(side) {
    if (document.querySelector(`.reader-sidebar-resizer--${side}`)) return;

    const handle = document.createElement("div");
    handle.className = `reader-sidebar-resizer reader-sidebar-resizer--${side}`;
    handle.dataset.side = side;
    handle.setAttribute("role", "separator");
    handle.setAttribute("aria-orientation", "vertical");
    handle.setAttribute("tabindex", "0");
    handle.setAttribute("title", side === "toc" ? "拖动调整右侧目录宽度" : "拖动调整左侧导航宽度");
    document.body.append(handle);

    handle.addEventListener("pointerdown", function (event) {
      const sidebar = getSidebar(side);
      if (!sidebar) return;

      event.preventDefault();
      handle.setPointerCapture?.(event.pointerId);

      const startX = event.clientX;
      const startWidth = sidebar.getBoundingClientRect().width;
      document.body.classList.add("reader-sidebar-resizing");

      function onPointerMove(moveEvent) {
        const delta = moveEvent.clientX - startX;
        const nextWidth = side === "toc" ? startWidth - delta : startWidth + delta;
        setSidebarWidth(side, nextWidth);
        positionReaderAffordances();
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

      const sidebar = getSidebar(side);
      if (!sidebar) return;

      event.preventDefault();
      const currentWidth = sidebar.getBoundingClientRect().width;
      const delta = event.key === "ArrowRight" ? 16 : -16;
      setSidebarWidth(side, side === "toc" ? currentWidth - delta : currentWidth + delta);
      positionReaderAffordances();
    });
  }

  function initReaderLayout() {
    restoreSidebarWidths();
    applyReaderState();
    installSidebarResizer("nav");
    installSidebarResizer("toc");

    if (!resizeBound) {
      resizeBound = true;
      window.addEventListener("resize", function () {
        restoreSidebarWidths();
        positionReaderAffordances();
        normalizeArticleImages();
      });
      window.addEventListener("scroll", positionReaderAffordances, { passive: true });
    }
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

  function getCodeLanguage(block) {
    const classList = Array.from(block.classList || []);
    const languageClass = classList.find(function (className) {
      return className.startsWith("language-");
    });

    if (!languageClass) return "";
    return languageClass.replace(/^language-/, "").trim();
  }

  function normalizeLanguageName(language) {
    const aliases = {
      c: "C",
      cpp: "C++",
      cxx: "C++",
      js: "JavaScript",
      ts: "TypeScript",
      py: "Python",
      sh: "Shell",
      shell: "Shell",
      bash: "bash",
      yml: "YAML",
      yaml: "YAML",
      html: "HTML",
      css: "CSS",
      json: "JSON",
      md: "Markdown",
      markdown: "Markdown",
      rust: "Rust",
      rs: "Rust",
      verilog: "Verilog",
      systemverilog: "SystemVerilog",
      sv: "SystemVerilog",
    };

    return aliases[language.toLowerCase()] || language;
  }

  function copyText(text, button) {
    function markCopied() {
      button.dataset.copied = "true";
      button.querySelector(".reader-code-copy__text").textContent = "已复制";
      window.setTimeout(function () {
        button.dataset.copied = "false";
        button.querySelector(".reader-code-copy__text").textContent = "复制";
      }, 1400);
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(markCopied).catch(function () {
        fallbackCopyText(text);
        markCopied();
      });
      return;
    }

    fallbackCopyText(text);
    markCopied();
  }

  function fallbackCopyText(text) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.append(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }

  function enhanceCodeBlocks() {
    document.querySelectorAll(".md-typeset .highlight").forEach(function (block) {
      if (block.dataset.readerEnhanced === "true") return;

      const pre = block.querySelector("pre");
      const code = block.querySelector("code");
      if (!pre || !code) return;

      const language = getCodeLanguage(block);
      const header = document.createElement("div");
      header.className = "reader-code-header";

      const languageLabel = document.createElement("div");
      languageLabel.className = "reader-code-language";
      languageLabel.textContent = language ? normalizeLanguageName(language) : "";

      const copyButton = document.createElement("button");
      copyButton.type = "button";
      copyButton.className = "reader-code-copy";
      copyButton.innerHTML = `${icons.copy}<span class="reader-code-copy__text">复制</span>`;
      copyButton.setAttribute("aria-label", "复制代码");
      copyButton.setAttribute("title", "复制代码");
      copyButton.addEventListener("click", function () {
        copyText(code.textContent || "", copyButton);
      });

      header.append(languageLabel, copyButton);
      block.insertBefore(header, pre);
      block.dataset.readerEnhanced = "true";
    });
  }

  function normalizeArticleImages() {
    document.querySelectorAll(".md-typeset img").forEach(function (img) {
      if (img.closest(".hero-container, .section-hero, .note-card, .card-grid, .giscus")) return;
      if (img.classList.contains("twemoji") || img.classList.contains("emoji")) return;
      if (img.hasAttribute("width") || img.style.width) return;

      function applySize() {
        const content = img.closest(".md-content__inner") || img.closest(".md-typeset");
        if (!content || !img.naturalWidth) return;

        const contentWidth = content.getBoundingClientRect().width;
        const minWidth = Math.min(300, contentWidth * 0.68);
        const maxWidth = Math.min(760, contentWidth * 0.84);
        const comfortableWidth = Math.min(680, contentWidth * 0.76);
        let displayWidth = img.naturalWidth;

        if (displayWidth > comfortableWidth) {
          displayWidth = comfortableWidth;
        } else if (displayWidth < minWidth) {
          displayWidth = minWidth;
        }

        displayWidth = Math.max(120, Math.min(displayWidth, maxWidth));
        img.classList.add("reader-normalized-image");
        img.style.setProperty("--reader-image-width", `${Math.round(displayWidth)}px`);
      }

      if (img.complete) {
        applySize();
      } else {
        img.addEventListener("load", applySize, { once: true });
      }
    });
  }

  onPageReady(function () {
    initReaderLayout();
    initHeroBackground();
    enhanceCodeBlocks();
    openPdfLinksInNewTab();
    normalizeArticleImages();
  });
})();
