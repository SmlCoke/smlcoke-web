let cryptoModulePromise = null;

function getCryptoModuleUrl() {
  return new URL("rust/pkg/ciphery.js", __md_scope).href;
}

function loadCryptoModule() {
  // Cache the dynamic import so repeated page visits don't re-fetch the module.
  if (!cryptoModulePromise) {
    cryptoModulePromise = import(getCryptoModuleUrl());
  }

  return cryptoModulePromise;
}

function showStatus(statusNode, message) {
  if (!statusNode) {
    return;
  }

  statusNode.textContent = message;
  statusNode.style.display = "block";
}

function hideStatus(statusNode) {
  if (!statusNode) {
    return;
  }

  statusNode.style.display = "none";
}

async function initCryptoApp(root) {
  const app = root.querySelector("#crypto-app");
  if (!app || app.dataset.cryptoReady === "true" || app.dataset.cryptoReady === "loading") {
    return;
  }

  app.dataset.cryptoReady = "loading";

  const encryptBtn = app.querySelector("#encryptBtn");
  const decryptBtn = app.querySelector("#decryptBtn");
  const inputText = app.querySelector("#inputText");
  const outputText = app.querySelector("#outputText");
  const algo = app.querySelector("#algo");
  const key = app.querySelector("#key");
  const statusNode = app.querySelector("#cryptoStatus");

  try {
    const module = await loadCryptoModule();
    const init = module.default;
    const { wasm_encrypt, wasm_decrypt } = module;

    await init();

    // Keep the click wiring local to this page instance so instant navigation
    // can tear it down by replacing the DOM and then rebuild it on revisit.
    const runCipher = (handler) => {
      hideStatus(statusNode);

      try {
        outputText.value = handler(algo.value, inputText.value, key.value);
      } catch (error) {
        console.error("Cipher action failed:", error);
        showStatus(statusNode, "加密工具运行失败，请检查输入后重试。");
      }
    };

    encryptBtn.addEventListener("click", () => runCipher(wasm_encrypt));
    decryptBtn.addEventListener("click", () => runCipher(wasm_decrypt));

    app.dataset.cryptoReady = "true";
  } catch (error) {
    console.error("Failed to initialize crypto app:", error);
    delete app.dataset.cryptoReady;
    showStatus(statusNode, "加密工具初始化失败，请刷新页面后重试。");
  }
}

document$.subscribe(({ body }) => {
  initCryptoApp(body);
});
