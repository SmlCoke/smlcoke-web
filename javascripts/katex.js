function stripMathDelimiters(source) {
  const text = source.trim();
  const pairs = [
    ["$$", "$$"],
    ["\\[", "\\]"],
    ["$", "$"],
    ["\\(", "\\)"],
  ];

  for (const [left, right] of pairs) {
    if (text.startsWith(left) && text.endsWith(right)) {
      return text.slice(left.length, text.length - right.length).trim();
    }
  }

  return text;
}

function cacheMathSource(root) {
  root.querySelectorAll(".arithmatex").forEach((node) => {
    if (!node.dataset.mathSource) {
      node.dataset.mathSource = stripMathDelimiters(node.textContent || "");
    }
  });
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (_) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "absolute";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    document.body.removeChild(textarea);
    return copied;
  }
}

function enhanceDisplayMath(root) {
  root.querySelectorAll("div.arithmatex").forEach((node) => {
    if (node.querySelector(".math-copy-button")) {
      return;
    }

    const button = document.createElement("button");
    button.type = "button";
    button.className = "math-copy-button";
    button.setAttribute("aria-label", "复制公式源码");
    button.setAttribute("title", "复制公式源码");
    button.textContent = "⧉";

    button.addEventListener("click", async () => {
      const copied = await copyText(node.dataset.mathSource || "");
      button.textContent = copied ? "✓" : "!";
      button.dataset.copied = copied ? "true" : "false";
      window.setTimeout(() => {
        button.textContent = "⧉";
        delete button.dataset.copied;
      }, 1400);
    });

    node.appendChild(button);
  });
}

document$.subscribe(({ body }) => {
  cacheMathSource(body);
  renderMathInElement(body, {
    delimiters: [
      { left: "$$", right: "$$", display: true },
      { left: "$", right: "$", display: false },
      { left: "\\(", right: "\\)", display: false },
      { left: "\\[", right: "\\]", display: true },
    ],
  });
  enhanceDisplayMath(body);
});
