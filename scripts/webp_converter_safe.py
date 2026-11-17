#!/usr/bin/env python3
"""Convert referenced local images to WebP; delete originals only after updating links."""

# 默认安全文件夹，相对于仓库根目录；CLI --safe-dirs 只追加，不能移除默认项。
DEFAULT_SAFE_DIRS = ["docs/assets"]

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from io import BytesIO
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from urllib.parse import unquote, urlsplit

from PIL import Image, ImageOps, features


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
OTHER_SOURCES = {".js", ".css", ".html", ".yml", ".yaml", ".json", ".json5"}
ESCAPE = re.compile(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])")
ATTR = re.compile(r'''(?P<name>[^\s=<>/]+)\s*=\s*(?:"(?P<double>[^"]*)"|'(?P<single>[^']*)'|(?P<bare>[^\s>]+))''')


def within(path, directory):
    return path == directory or directory in path.parents


def protected(path, safe_dirs):
    return any(within(path, directory) for directory in safe_dirs)


def is_link(path):
    # Python 3.10's is_symlink() alone does not detect Windows junctions.
    return path.is_symlink() or bool(
        getattr(path.lstat(), "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def files_under(directory):
    def fail(error):
        raise error

    for current, dirs, names in os.walk(directory, followlinks=False, onerror=fail):
        dirs[:] = sorted(name for name in dirs if not is_link(Path(current) / name))
        for name in sorted(names):
            path = Path(current) / name
            if not is_link(path) and path.is_file():
                yield path


def blank(text):
    return re.sub(r"[^\r\n]", " ", text)


def mask_literals(text, *, indented=True):
    """Keep offsets intact while excluding examples, comments, and raw code elements.

    Indented Markdown is conservatively excluded too: ambiguous constructs are
    left for manual handling rather than rewritten as if they were ordinary links.
    """
    masked = list(text)

    def hide(start, end):
        masked[start:end] = blank(text[start:end])

    for match in re.finditer(r"<!--[\s\S]*?(?:-->|\Z)|<(pre|code|script|style|textarea)\b[^>]*>[\s\S]*?</\1\s*>", text, re.I):
        hide(*match.span())
    offset, fence = 0, None
    for line in text.splitlines(keepends=True):
        visible = "".join(masked[offset:offset + len(line)])
        marker = re.match(r"^[ \t]*(?:>\s*)*(?:[-+*]\s+|\d+[.)]\s+)?(`{3,}|~{3,})", visible)
        if fence:
            hide(offset, offset + len(line))
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                if not visible[marker.end():].strip():
                    fence = None
        elif marker:
            fence = marker[1]
            hide(offset, offset + len(line))
        elif indented and line.startswith(("    ", "\t")):
            hide(offset, offset + len(line))
        offset += len(line)
    value = "".join(masked)
    # A code span closes only with a backtick run of the same length.
    index = 0
    while index < len(value):
        if value[index] == "\\":
            index += 2
            continue
        if value[index] != "`":
            index += 1
            continue
        end = index + 1
        while end < len(value) and value[end] == "`":
            end += 1
        closing = re.search(r"(?<!`)" + re.escape(value[index:end]) + r"(?!`)", value[end:])
        if closing:
            stop = end + closing.end()
            hide(index, stop)
            index = stop
        else:
            index = end
    return "".join(masked)


def destination(text, start):
    """Return the original URL span, handling angle brackets and balanced parentheses."""
    if start >= len(text):
        return None
    if text[start] == "<":
        end = start + 1
        while end < len(text):
            if text[end] == "\\":
                end += 2
            elif text[end] == ">":
                return start + 1, end, end + 1
            elif text[end] in "\r\n":
                return None
            else:
                end += 1
        return None
    end, depth = start, 0
    while end < len(text):
        char = text[end]
        if char == "\\":
            end += 2
            continue
        if char.isspace() or (char == ")" and depth == 0):
            break
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        end += 1
    if depth or end == start:
        return None
    return start, end, end


def closing_bracket(text, start):
    depth, index = 1, start + 1
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == "[":
            depth += 1
        elif text[index] == "]":
            depth -= 1
            if not depth:
                return index
        index += 1
    return None


def label_key(label):
    return " ".join(ESCAPE.sub(r"\1", label).split()).casefold()


class LinkHTMLParser(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.spans = []
        self.offsets = [0]
        for line in text.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))

    def handle_starttag(self, tag, attrs):
        wanted = {"img": "src", "a": "href", "source": "src"}.get(tag)
        if not wanted:
            return
        line, column = self.getpos()
        offset = self.offsets[line - 1] + column
        for match in ATTR.finditer(self.get_starttag_text()):
            if match["name"].lower() == wanted:
                group = next(name for name in ("double", "single", "bare") if match[name] is not None)
                start, end = match.span(group)
                self.spans.append((offset + start, offset + end))

    handle_startendtag = handle_starttag


def link_spans(text):
    """Locate supported destinations without reserializing the Markdown document."""
    visible = mask_literals(text)
    # Front matter is data, not Markdown. Leave it in the unsupported-reference guard.
    front = re.match(r"\A\ufeff?---[ \t]*\r?\n[\s\S]*?\r?\n(?:---|\.\.\.)[ \t]*(?:\r?\n|\Z)", visible)
    if front:
        visible = blank(visible[:front.end()]) + visible[front.end():]
    html = LinkHTMLParser(visible)
    html.feed(visible)
    spans = set(html.spans)
    # Do not parse Markdown-looking text inside HTML attribute values/tags.
    markdown = re.sub(r"</?[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*?)?/?>",
                      lambda match: blank(match[0]), visible)
    definitions = {}
    definition_spans = []
    for match in re.finditer(r"(?m)^[ ]{0,3}\[([^\]\r\n]+)\]:[ \t]*(?:\r?\n[ \t]*)?", markdown):
        result = destination(markdown, match.end())
        if result:
            start, end, _ = result
            definitions.setdefault(label_key(match[1]), (start, end))
            line_end = markdown.find("\n", end)
            definition_spans.append((match.start(), len(markdown) if line_end < 0 else line_end))
    characters = list(markdown)
    for start, end in definition_spans:
        characters[start:end] = blank(markdown[start:end])
    markdown = "".join(characters)
    index = 0
    while index < len(markdown):
        if markdown[index] == "\\":
            index += 2
            continue
        if markdown[index] != "[":
            index += 1
            continue
        end = closing_bracket(markdown, index)
        if end is None:
            index += 1
            continue
        following = end + 1
        if following < len(markdown) and markdown[following] == "(":
            url_start = following + 1
            while url_start < len(markdown) and markdown[url_start].isspace():
                url_start += 1
            result = destination(markdown, url_start)
            if result:
                start, stop, after = result
                tail = markdown[after:]
                if re.match(r'''^[ \t\r\n]*(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\((?:\\.|[^)\\])*\))?[ \t\r\n]*\)''', tail):
                    spans.add((start, stop))
        else:
            label = markdown[index + 1:end]
            if following < len(markdown) and markdown[following] == "[":
                ref_end = closing_bracket(markdown, following)
                if ref_end is not None:
                    label = markdown[following + 1:ref_end] or label
            if label_key(label) in definitions:
                spans.add(definitions[label_key(label)])
        # Nested images inside [![preview](...)](...) must also be visited.
        index += 1
    return sorted(spans), mask_literals(text, indented=False)


@dataclass
class Reference:
    document: "Document"
    start: int
    end: int
    target: Path
    replacement: str

    @property
    def location(self):
        return f"{self.document.path}:{self.document.text.count(chr(10), 0, self.start) + 1}"


@dataclass
class Document:
    path: Path
    original: bytes
    text: str
    current: bytes
    edits: dict = field(default_factory=dict)

    def render(self, edits):
        text = self.text
        for (start, end), value in sorted(edits.items(), reverse=True):
            text = text[:start] + value + text[end:]
        return text.encode("utf-8")


@dataclass
class Report:
    converted: int = 0
    planned: int = 0
    saved: int = 0
    warnings: int = 0
    errors: int = 0
    updated: set = field(default_factory=set)
    skipped: Counter = field(default_factory=Counter)

    def warn(self, reason, message):
        self.warnings += 1
        self.skipped[reason] += 1
        print(f"WARNING [{reason}] {message}", file=sys.stderr)

    def summary(self):
        print(f"SUMMARY converted={self.converted}, planned={self.planned}, "
              f"markdown_updated={len(self.updated)}, saved_bytes={self.saved}, "
              f"warnings={self.warnings}, errors={self.errors}")
        if self.skipped:
            print("DETAIL " + ", ".join(f"{key}={count}" for key, count in sorted(self.skipped.items())))


def resolve_reference(raw, document, docs_dir):
    decoded = ESCAPE.sub(r"\1", unescape(raw))
    url = urlsplit(decoded)
    if url.scheme or url.netloc or not url.path:
        return None
    path = unquote(url.path)
    if Path(path).suffix.lower() not in IMAGE_EXTS:
        return None
    if path.startswith(("/", "\\")) or "\\" in path:
        return None  # These are guarded as unsupported references below.
    lexical = Path(os.path.abspath(document.path.parent / path))
    target = lexical.resolve()
    if not within(target, docs_dir):
        return None
    if lexical != target or (lexical.exists() and is_link(lexical)):
        # Changing the extension of a symlink alias would point at a nonexistent
        # alias.webp, even if the actual target had been converted successfully.
        return target, None
    # Replace only the URL path suffix. Preserve escaping, query, and fragment bytes.
    boundary = re.search(r"[?#]", raw)
    end = boundary.start() if boundary else len(raw)
    replacement, count = re.subn(r"(?i)(?:\.|%2e)(?:png|jpe?g)$", ".webp", raw[:end])
    if not count:
        return None
    return target, replacement + raw[end:]


def scan(docs_dir, target, safe_dirs, report):
    references = defaultdict(list)
    guards = []
    all_files = list(files_under(docs_dir))
    for path in all_files:
        if path.suffix.lower() != ".md":
            continue
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        document = Document(path, raw, text, raw)
        spans, visible = link_spans(text)
        unknown = list(visible)
        for start, end in spans:
            value = text[start:end]
            resolved = resolve_reference(value, document, docs_dir)
            if resolved:
                image, replacement = resolved
                if protected(image, safe_dirs):
                    unknown[start:end] = blank(visible[start:end])
                    continue
                if replacement is None:
                    guards.append((path, image.name.casefold()))
                    continue
                ref = Reference(document, start, end, image, replacement)
                references[image].append(ref)
                if within(path, target):
                    if not image.is_file():
                        report.warn("missing", f"{ref.location}: {value!r} -> {image}")
                    elif not within(image, target):
                        report.warn("outside-path", f"{ref.location}: 图片在 --path 外，保留 {image}")
                unknown[start:end] = blank(visible[start:end])
            else:
                # Remote URLs / non-bitmap URLs are intentionally ignored, not guards.
                url = urlsplit(ESCAPE.sub(r"\1", unescape(value)))
                if url.scheme or url.netloc or Path(unquote(url.path)).suffix.lower() not in IMAGE_EXTS:
                    unknown[start:end] = blank(visible[start:end])
        # YAML metadata and unsupported constructs can still contain image references.
        front = re.match(r"\A\ufeff?---[ \t]*\r?\n[\s\S]*?\r?\n(?:---|\.\.\.)[ \t]*(?:\r?\n|\Z)", text)
        if front:
            unknown[:front.end()] = text[:front.end()]
        guards.append((path, unquote(unescape("".join(unknown))).casefold()))
        for match in re.finditer(r"<(script|style)\b[^>]*>[\s\S]*?</\1\s*>", text, re.I):
            guards.append((path, unquote(unescape(match[0])).casefold()))
    sources = [p for p in all_files if p.suffix.lower() in OTHER_SOURCES]
    if (docs_dir.parent / "mkdocs.yml").is_file():
        sources.append(docs_dir.parent / "mkdocs.yml")
    overrides = docs_dir.parent / "overrides"
    if overrides.is_dir():
        sources.extend(p for p in files_under(overrides) if p.suffix.lower() in OTHER_SOURCES)
    for path in sources:
        guards.append((path, unquote(unescape(path.read_text(encoding="utf-8"))).casefold()))
    return references, guards


def atomic_write(document, data):
    if document.path.read_bytes() != document.current:
        raise OSError(f"扫描后文档发生变化，停止写入：{document.path}")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=document.path.parent, prefix=".webp-md-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, stat.S_IMODE(document.path.stat().st_mode))
        if document.path.read_bytes() != document.current:
            raise OSError(f"写入前文档发生变化，停止写入：{document.path}")
        os.replace(temporary, document.path)
        document.current = data
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def convert(image, refs, quality, lossless, dry_run, report):
    output = image.with_suffix(".webp")
    original = image.read_bytes()
    with Image.open(BytesIO(original)) as source:
        source.load()
        if getattr(source, "n_frames", 1) != 1:
            report.warn("multiframe", f"多帧图片保留：{image}")
            return
        if source.format not in {"PNG", "JPEG"} or source.mode not in {"RGB", "RGBA", "L", "LA", "P"}:
            report.warn("unsupported-image", f"不支持的图像格式/色彩模式 {source.format}/{source.mode}：{image}")
            return
        if source.info.get("icc_profile") and source.mode not in {"RGB", "RGBA"}:
            report.warn("unsupported-image", f"非 RGB 色彩配置需人工处理，保留：{image}")
            return
        if dry_run:
            report.planned += 1
            print(f"PLAN {image} -> {output}")
            for ref in refs:
                print(f"  LINK {ref.location}: {ref.document.text[ref.start:ref.end]} -> {ref.replacement}")
            return
        oriented = ImageOps.exif_transpose(source)
        alpha = "A" in oriented.getbands() or "transparency" in oriented.info
        picture = oriented.convert("RGBA" if alpha else "RGB")
        encoded = BytesIO()
        picture.save(encoded, "WEBP", quality=quality, lossless=lossless, exact=lossless, method=6,
                     icc_profile=source.info.get("icc_profile", b""))
        data = encoded.getvalue()
        with Image.open(BytesIO(data)) as check:
            check.load()
            if check.format != "WEBP" or check.size != picture.size:
                raise OSError(f"WebP 校验失败：{image}")
            if alpha and picture.getchannel("A").getextrema()[0] < 255 and "A" not in check.getbands():
                raise OSError(f"WebP 透明度校验失败：{image}")
    if len(data) >= len(original):
        report.warn("not-smaller", f"WebP 未变小，保留原图：{image} ({len(original)} -> {len(data)} bytes)")
        return
    if image.read_bytes() != original:
        raise OSError(f"编码期间原图发生变化，停止处理：{image}")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=image.parent, prefix=".webp-image-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        # Same-directory hard link publishes a complete file atomically, failing if
        # the destination appeared meanwhile. os.replace() must NOT be used here.
        try:
            os.link(temporary, output)
        except FileExistsError:
            report.warn("exists", f"已有 WebP，原图和链接均保留：{output}")
            return
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    changes = {}
    for ref in refs:
        key = ref.document.path
        if key not in changes:
            changes[key] = (ref.document, dict(ref.document.edits))
        changes[key][1][(ref.start, ref.end)] = ref.replacement
    for document, edits in changes.values():
        atomic_write(document, document.render(edits))
        document.edits = edits
        report.updated.add(document.path)
    if image.read_bytes() != original:
        raise OSError(f"删除前原图发生变化，原图保留：{image}")
    image.unlink()
    report.converted += 1
    report.saved += len(original) - len(data)
    print(f"CONVERTED {image} -> {output} ({len(original)} -> {len(data)} bytes)")


def run(target, *, docs_dir=DOCS_DIR, safe_dirs=(), quality=85, remaining="warn", dry_run=False, lossless=False):
    """Run against one docs tree (explicit docs_dir also supports isolated tests)."""
    report = Report()
    try:
        docs_dir, target = Path(docs_dir).resolve(), Path(target).resolve()
        safe_dirs = tuple(Path(path).resolve() for path in safe_dirs)
        if not target.is_dir() or not within(target, docs_dir):
            raise ValueError("--path 必须是 docs/ 内已存在的文件夹")
        if any(not within(path, docs_dir) for path in safe_dirs):
            raise ValueError("安全文件夹必须位于 docs/ 内（可以尚未创建）")
        if not 0 <= quality <= 100 or remaining not in {"warn", "search-docs"}:
            raise ValueError("无效的 quality 或 remaining 参数")
        print(f"PATH {target}\nMODE {remaining}, quality={quality}, lossless={lossless}, dry_run={dry_run}")
        for path in sorted(set(safe_dirs)):
            print(f"SAFE {path}")
        if protected(target, safe_dirs):
            print("IGNORED --path 位于安全文件夹内，无需处理")
            return report
        references, guards = scan(docs_dir, target, safe_dirs, report)
        images = [path for path in files_under(target)
                  if path.suffix.lower() in IMAGE_EXTS and not protected(path, safe_dirs)]
        outputs = Counter(path.with_suffix(".webp") for path in images)
        local = {image for image in images if any(within(ref.document.path, target) for ref in references[image])}
        # Referenced images first, then remaining physical files (including gitignored images).
        for image in sorted(local) + sorted(set(images) - local):
            refs = references[image]
            output = image.with_suffix(".webp")
            if output.exists() or output.is_symlink():
                report.warn("exists", f"已有 WebP，原图和链接均保留：{output}")
                continue
            if outputs[output] > 1:
                report.warn("collision", f"多个原图会生成同名 WebP，全部保留：{image} -> {output}")
                continue
            if not refs:
                report.warn("unreferenced", f"全站 Markdown 未引用，保留并交由人工处理：{image}")
                continue
            external = [ref for ref in refs if not within(ref.document.path, target)]
            if remaining == "warn" and (image not in local or external):
                locations = ", ".join(ref.location for ref in external)
                report.warn("cross-scope", f"需要修改 --path 外的 Markdown，保留 {image}；引用：{locations}")
                continue
            suspects = [path for path, content in guards if image.name.casefold() in content]
            if suspects:
                report.warn("unsupported-reference", f"发现未支持或非 Markdown 的疑似引用，保留 {image}；位置：" + ", ".join(map(str, suspects)))
                continue
            convert(image, refs, quality, lossless, dry_run, report)
    except (OSError, ValueError, UnicodeError, Image.DecompressionBombError) as error:
        report.errors += 1
        print(f"ERROR {error}\n已发布的 WebP 或部分链接可能已更新；失败图片的原图会保留，请查看差异。", file=sys.stderr)
    finally:
        report.summary()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, required=True, help="递归处理目录；相对当前工作目录，必须位于本仓库 docs 内")
    parser.add_argument("--quality", type=int, default=85, help="WebP quality，0–100，默认 85")
    parser.add_argument("--remaining", choices=("warn", "search-docs"), default="warn",
                        help="warn 保留跨目录/剩余图片；search-docs 允许同步全站 Markdown 引用")
    parser.add_argument("--safe-dirs", nargs="+", action="extend", type=Path, default=[],
                        help="追加安全目录，可传多个值或重复使用；相对当前工作目录，与默认列表取并集")
    parser.add_argument("--dry-run", action="store_true", help="只读取并列出计划，不编码、不写入、不删除")
    parser.add_argument("--lossless", action="store_true", help="无损 WebP；quality 此时控制压缩努力程度")
    args = parser.parse_args(argv)
    if not 0 <= args.quality <= 100:
        parser.error("--quality 必须是 0–100 的整数")
    if not args.path.is_dir() or not within(args.path.resolve(), DOCS_DIR):
        parser.error("--path 必须是本仓库 docs/ 内已存在的文件夹")
    if is_link(args.path):
        parser.error("--path 不能是符号链接或目录联接")
    safe_dirs = {*(ROOT / path for path in DEFAULT_SAFE_DIRS), *args.safe_dirs}
    if any(not within(path.resolve(), DOCS_DIR) for path in safe_dirs):
        parser.error("--safe-dirs 必须位于本仓库 docs/ 内")
    if not features.check("webp"):
        parser.error("当前 Pillow 未启用 WebP 支持")
    return 1 if run(args.path, safe_dirs=safe_dirs, quality=args.quality,
                    remaining=args.remaining, dry_run=args.dry_run, lossless=args.lossless).errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
