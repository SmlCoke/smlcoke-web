"""Build D2/WaveDrom SVG assets without writing generated files into docs/."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
from types import SimpleNamespace
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from mkdocs.exceptions import PluginError
from mkdocs.structure.files import File
from mkdocs.utils import get_relative_url
from pymdownx.superfences import SuperFencesException


LOG = logging.getLogger("mkdocs.plugins.diagrams")
SCRIPT_DIR = Path(__file__).resolve().parent
SVG_NS = "http://www.w3.org/2000/svg"


def _parse_width(value):
    """Accept a pixel width or a percentage of the article, never raw CSS."""
    if value is None:
        return None
    value = str(value).strip()
    if re.fullmatch(r"[1-9]\d*(?:px)?", value):
        return int(value.removesuffix("px"))
    if re.fullmatch(r"\d+(?:\.\d+)?%", value) and 0 < float(value[:-1]) <= 100:
        return value
    raise PluginError("绘图 width 必须是正整数像素（如 850、850px）或 0% 到 100% 之间的百分比（不含 0%）")


class DiagramBuilder:
    def __init__(self, config):
        self.config = config
        self.docs_dir = Path(config.docs_dir).resolve()
        settings = config.extra.get("diagrams", {})
        tools = Path(os.environ.get("SMLCOKE_DIAGRAM_TOOLS", settings.get(
            "tools_dir", "D:/Tools/diagramming"
        )))
        self.d2 = os.environ.get("D2_EXECUTABLE", str(
            tools / "d2" / "d2-v0.9.0" / "bin" / "d2.exe"
        ))
        self.node = os.environ.get("NODE_EXECUTABLE", shutil.which("node") or "node")
        self.modules = str(tools / "wavedrom" / "node_modules")
        self.layout = settings.get("layout", "elk")
        self.light_theme = int(settings.get("light_theme", 0))
        self.dark_theme = int(settings.get("dark_theme", 200))
        self.timeout = int(settings.get("timeout", 90))
        self.reset()

    def reset(self):
        # Only deduplicate within this build. Imports are re-read on every build.
        self.assets = {}
        self.rendered = {}
        self.page = None

    def bind_markdown(self, md):
        # Material re-renders blog excerpts later, without on_page_markdown.
        # Its relpath processor keeps the original source and current view URL.
        file = md.treeprocessors["relpath"].file
        self.page = SimpleNamespace(file=file, url=file.url)

    def run(self, args, source=None, cwd=None):
        try:
            result = subprocess.run(
                args, input=source, capture_output=True, text=True,
                encoding="utf-8", errors="replace", cwd=cwd, timeout=self.timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PluginError(f"绘图工具无法运行：{args[0]} ({exc})") from exc
        if result.returncode:
            detail = (result.stderr or result.stdout).strip()[:2000]
            raise PluginError(f"绘图失败 ({Path(args[0]).name}): {detail}")
        return result.stdout

    def render(self, language, source, options=None, source_path=None):
        if self.page is None:
            raise PluginError("绘图缺少当前 Markdown 页面上下文")
        options = options or {}
        cwd = Path(self.page.file.abs_src_path).parent
        if source_path is not None:
            cwd = source_path.parent
        layout = options.get("layout", self.layout)
        if layout not in {"dagre", "elk", "tala"}:
            raise PluginError(f"不支持的 D2 layout: {layout}")
        sketch = str(options.get("sketch", "false")).lower()
        if sketch not in {"true", "false"}:
            raise PluginError("sketch 必须是 true 或 false")
        key = (language, source, str(source_path or cwd), layout, sketch)
        if key in self.rendered:
            return self.rendered[key]
        targets = []
        for mode, theme in (("light", self.light_theme), ("dark", self.dark_theme)):
            if language == "d2":
                svg = self.run([
                    self.d2, "--layout", layout, "--theme", str(theme),
                    "--dark-theme", "-1", "--pad", "24", f"--sketch={sketch}",
                    str(source_path) if source_path else "-", "-",
                ], source=None if source_path else source, cwd=cwd)
            else:
                svg = self.run([
                    self.node, str(SCRIPT_DIR / "render_wavedrom.cjs"),
                    "--modules", self.modules, "--theme", mode,
                ], source=source, cwd=cwd)
            try:
                root = ET.fromstring(svg)
                if root.tag != f"{{{SVG_NS}}}svg":
                    raise ValueError("输出不是 SVG")
            except (ET.ParseError, ValueError) as exc:
                raise PluginError(f"{language} 输出的 SVG 无效: {exc}") from exc
            digest = hashlib.sha256(svg.encode("utf-8")).hexdigest()[:24]
            target = f"assets/diagrams/{digest}.{mode}.svg"
            self.assets[target] = svg
            targets.append(target)
        self.rendered[key] = targets
        return targets

    def pair(self, language, source, options=None, source_path=None, attributes=None):
        options = options or {}
        attrs = dict(attributes or {})
        requested_width = _parse_width(options.get("width", attrs.get("width")))
        targets = self.render(language, source, options, source_path)
        outer = ET.Element("span", {"class": "diagram-pair"})
        attrs.pop("src", None)
        attrs.setdefault("alt", options.get("alt", f"{language} diagram"))
        if options.get("title"):
            attrs["title"] = options["title"]
        for mode, target in zip(("light", "dark"), targets):
            image_attrs = dict(attrs)
            image_attrs.update({
                "src": get_relative_url(target, self.page.url),
                "class": (attrs.get("class", "") + f" diagram-{mode}").strip(),
                "loading": "lazy", "decoding": "async",
            })
            # Explicit geometry bypasses the site's 300px SVG fallback. Only
            # automatic sizing uses the 760x320 box; an author width overrides
            # that box, while CSS still fits the image to its article column.
            viewbox = ET.fromstring(self.assets[target]).get("viewBox", "").split()
            if len(viewbox) == 4:
                width, height = float(viewbox[2]), float(viewbox[3])
                if width > 0 and height > 0:
                    if isinstance(requested_width, int):
                        scale = requested_width / width
                    elif requested_width is None:
                        scale = min(1, 760 / width, 320 / height)
                    else:
                        scale = 1
                        style = image_attrs.get("style", "").rstrip("; ")
                        image_attrs["style"] = f"{style};width:{requested_width}".lstrip(";")
                    image_attrs["width"] = str(max(1, round(width * scale)))
                    image_attrs["height"] = str(max(1, round(height * scale)))
            ET.SubElement(outer, "img", image_attrs)
        return outer

    def image_source(self, src):
        parsed = urlsplit(src)
        suffix = Path(unquote(parsed.path)).suffix.lower()
        if suffix not in {".d2", ".json5"}:
            return None
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
            raise PluginError("绘图图源必须是无查询参数的本地相对路径")
        path = (Path(self.page.file.abs_src_path).parent / unquote(parsed.path)).resolve()
        if not path.is_relative_to(self.docs_dir):
            raise PluginError(f"绘图图源必须位于 docs/ 内: {src}")
        if not path.is_file():
            raise PluginError(f"绘图图源不存在: {src} ({self.page.file.src_uri})")
        return ("d2" if suffix == ".d2" else "wavedrom", path)


class DiagramImages(Treeprocessor):
    def __init__(self, md, builder):
        super().__init__(md)
        self.builder = builder

    def run(self, root):
        # Work on parsed images: examples inside code fences are never executed.
        self.builder.bind_markdown(self.md)
        for parent in list(root.iter()):
            for index, child in list(enumerate(parent)):
                if child.tag != "img":
                    continue
                match = self.builder.image_source(child.get("src", ""))
                if match:
                    language, path = match
                    pair = self.builder.pair(
                        language, path.read_text(encoding="utf-8-sig"),
                        source_path=path, attributes=child.attrib,
                    )
                    # URLs already use the final page URL (including blog URLs).
                    # Do not let MkDocs reinterpret them as Markdown-source URLs.
                    images = "".join(ET.tostring(img, encoding="unicode", method="html")
                                     for img in pair)
                    for img in list(pair):
                        pair.remove(img)
                    pair.text = self.md.htmlStash.store(images)
                    pair.tail = child.tail
                    parent[index] = pair


class DiagramImageExtension(Extension):
    def __init__(self, builder):
        self.builder = builder
        super().__init__()

    def extendMarkdown(self, md):
        # attr_list (priority 8) must attach width/style to source images first.
        md.treeprocessors.register(DiagramImages(md, self.builder), "diagram_images", 7)


def _validate(language, inputs, options, attrs, md):
    allowed = {"alt", "title", "width"}
    if language == "d2":
        allowed.update({"layout", "sketch"})
    unknown = set(inputs) - allowed
    if unknown:
        raise SuperFencesException(f"不支持的 {language} 代码块选项: {sorted(unknown)}")
    options.update(inputs)
    return True


def on_config(config):
    global _builder
    _builder = DiagramBuilder(config)
    sf_config = config.mdx_configs.setdefault("pymdownx.superfences", {})
    custom = sf_config.setdefault("custom_fences", [])
    # on_config also runs on each live-reload rebuild.
    custom[:] = [item for item in custom if item.get("name") not in {"d2", "wavedrom"}]

    def formatter(source, language, class_name, options, md, **kwargs):
        try:
            _builder.bind_markdown(md)
            element = _builder.pair(language, source, options)
            return ET.tostring(element, encoding="unicode", method="html")
        except Exception as exc:
            # SuperFences otherwise swallows ordinary formatter exceptions.
            raise SuperFencesException(str(exc)) from exc

    for language in ("d2", "wavedrom"):
        custom.append({"name": language, "class": language, "format": formatter,
                       "validator": _validate})
    config.markdown_extensions[:] = [
        ext for ext in config.markdown_extensions
        if not isinstance(ext, DiagramImageExtension)
    ]
    config.markdown_extensions.append(DiagramImageExtension(_builder))
    return config


def on_pre_build(config):
    _builder.reset()


def on_files(files, config):
    # These are diagram sources, not downloadable website assets.
    for file in list(files):
        if Path(file.src_uri).suffix.lower() in {".d2", ".json5"}:
            files.remove(file)
    return files


def on_page_markdown(markdown, page, config, files):
    _builder.page = page
    return markdown


def on_env(env, config, files):
    # Markdown rendering precedes static-file copying. Register in-memory SVGs
    # now so MkDocs writes them to its actual output directory, including serve.
    for uri, svg in _builder.assets.items():
        if files.get_file_from_path(uri):
            raise PluginError(f"生成的绘图路径与已有文件冲突: {uri}")
        files.append(File.generated(config, uri, content=svg))
    LOG.info("Diagrams: %d source(s), %d standalone SVG(s)",
             len(_builder.rendered), len(_builder.assets))
    return env


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True,
                        help="check tools and render both sample themes in memory")
    args = parser.parse_args()
    from mkdocs.config import load_config

    config = load_config(str(SCRIPT_DIR.parent / "mkdocs.yml"))
    builder = DiagramBuilder(config)
    builder.page = SimpleNamespace(
        file=SimpleNamespace(abs_src_path=str(builder.docs_dir / "index.md")), url=""
    )
    print("D2:", builder.run([builder.d2, "version"]).strip())
    print("Node:", builder.run([builder.node, "--version"]).strip())
    builder.render("d2", "CPU -> Memory: 数据\n")
    builder.render("wavedrom", "{signal:[{name:'clk',wave:'p...'}, {name:'valid',wave:'01..'}]}")
    print(f"OK: {len(builder.assets)} SVGs validated in memory; no output files written.")
