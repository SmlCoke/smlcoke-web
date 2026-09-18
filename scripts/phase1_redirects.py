"""Temporary phase-one URL compatibility. Remove with its JSON map after link cleanup.

No source pages are duplicated. Case-only legacy paths use the existing 404 page
so a Windows build can be published without overwriting canonical lowercase files.
"""
from pathlib import Path
import html
import json
from urllib.parse import quote, urlsplit

from mkdocs.exceptions import PluginError


def _mapping():
    return json.loads(Path(__file__).with_name('phase1-redirects.json').read_text(encoding='utf-8'))


def _target_url(path, base):
    return base + quote(path, safe='/')


def on_post_build(config):
    site = Path(config['site_dir']).resolve()
    redirects = _mapping()
    base = urlsplit(config['site_url']).path.rstrip('/') + '/'
    top_names = {p.name.casefold(): p.name for p in site.iterdir() if p.is_dir()}
    for old, new in redirects.items():
        if old == new or '..' in Path(old).parts or '..' in Path(new).parts:
            raise PluginError(f'Invalid temporary redirect: {old!r} -> {new!r}')
        target = site / new / 'index.html'
        if not target.is_file():
            raise PluginError(f'Temporary redirect target is missing: {new}')
        # Tools and tools cannot coexist on ordinary Windows filesystems.
        first = old.split('/')[0]
        if first.casefold() in top_names and top_names[first.casefold()] != first:
            continue
        dest = (site / old / 'index.html').resolve()
        if not dest.is_relative_to(site) or dest.exists():
            raise PluginError(f'Redirect would overwrite an existing page: {old}')
        url = _target_url(new, base)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            '<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
            '<meta name="robots" content="noindex"><title>页面已迁移</title>'
            f'<link rel="canonical" href="{html.escape(url, quote=True)}">'
            f'<script>location.replace({json.dumps(url)} + location.search + location.hash);</script>'
            f'<p>页面已迁移，请更新书签：<a href="{html.escape(url, quote=True)}">前往新页面</a></p></html>',
            encoding='utf-8',
        )
    # GitHub Pages serves 404.html for case-sensitive legacy URLs not representable
    # in a Windows directory tree. Keep the map inline to avoid base-path ambiguity.
    error_page = site / '404.html'
    content = error_page.read_text(encoding='utf-8')
    data = json.dumps(redirects, ensure_ascii=True).replace('<', '\\u003c')
    script = ('<script id="temporary-phase1-redirects">(()=>{'
              f'const map={data},base={json.dumps(base)};'
              'let path;try{path=decodeURIComponent(location.pathname);}catch{return;}'
              'if(!path.startsWith(base))return;path=path.slice(base.length);'
              'if(path.endsWith("index.html"))path=path.slice(0,-10);'
              'if(!path.endsWith("/"))path+="/";'
              'if(Object.prototype.hasOwnProperty.call(map,path))'
              'location.replace(base+map[path]+location.search+location.hash);'
              '})();</script>')
    error_page.write_text(content.replace('</head>', script + '</head>', 1), encoding='utf-8')
