"""Integration checks using the real local D2 and WaveDrom renderers."""

from pathlib import Path
import os
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

from mkdocs.commands.build import build
from mkdocs.config import load_config
import yaml


ROOT = Path(__file__).resolve().parents[1]


class DiagramIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="smlcoke-diagram-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        previous_cwd = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous_cwd)
        self.docs = self.root / "docs"
        (self.docs / "guide" / "assets").mkdir(parents=True)
        (self.docs / "index.md").write_text("# Home\n", encoding="utf-8")
        self.config_path = self.root / "mkdocs.yml"
        settings = {
            "site_name": "Diagram test", "site_url": "https://example.test/",
            "hooks": [str(ROOT / "scripts" / "mkdocs_diagrams.py")],
            "markdown_extensions": ["attr_list", "admonition", "pymdownx.details",
                                    "pymdownx.superfences", "pymdownx.tabbed"],
            "strict": True,
        }
        self.config_path.write_text(yaml.safe_dump(settings), encoding="utf-8")

    def write(self, name, text):
        (self.docs / "guide" / name).write_text(text, encoding="utf-8")

    def build(self):
        build(load_config(str(self.config_path)))
        return (self.root / "site" / "guide" / "index.html").read_text(encoding="utf-8")

    def test_fences_files_nested_blocks_and_literal_examples(self):
        self.write("assets/cpu.d2", "alu: 运算单元\n")
        self.write("assets/arch.d2", "cpu: @cpu\ncpu -> memory: 数据\n")
        self.write("assets/ready.json5", "{signal:[{name:'ready',wave:'01..'}]}\n")
        self.write("index.md", '''# Diagrams

```d2 alt="处理器结构"
CPU -> Memory: 数据
```

```wavedrom
{signal:[{name:'clk',wave:'p...'}]}
```

![独立架构](assets/arch.d2)

![独立波形](assets/ready.json5){as="wavedrom"}

!!! note "Nested"

    ```d2
    A -> B
    ```

=== "Timing"

    ```wavedrom
    {signal:[{name:'valid',wave:'01..'}]}
    ```

- Nested list:

    ```d2
    X -> Y
    ```

````markdown
```d2
THIS IS AN EXAMPLE AND MUST NOT BE RENDERED: {
```
![example](assets/does-not-exist.d2)
````
''')
        output = self.build()
        self.assertEqual(output.count('class="diagram-pair"'), 7)
        self.assertIn('alt="处理器结构"', output)
        self.assertNotIn('data:image/svg', output)
        for pair in re.findall(r'<span class="diagram-pair">(.*?)</span>', output, re.S):
            self.assertNotIn('<svg', pair)
            self.assertIn('diagram-light', pair)
            self.assertIn('diagram-dark', pair)
        images = re.findall(r'<img[^>]+src="([^"]+\.svg)"', output)
        self.assertEqual(len(images), 14)
        # Explicit geometry prevents responsive SVGs being normalized to the
        # browser fallback width of 300px, and bounds their article footprint.
        for tag in re.findall(r'<img[^>]+class="[^"]*diagram-(?:light|dark)[^"]*"[^>]*>', output):
            self.assertRegex(tag, r'width="\d+"')
            self.assertRegex(tag, r'height="\d+"')
            self.assertLessEqual(int(re.search(r'width="(\d+)"', tag)[1]), 760)
            self.assertLessEqual(int(re.search(r'height="(\d+)"', tag)[1]), 320)
        for uri in images:
            path = (self.root / 'site' / 'guide' / unquote(urlsplit(uri).path)).resolve()
            self.assertTrue(path.is_file(), path)
            self.assertTrue(ET.parse(path).getroot().tag.endswith('}svg'))
        self.assertFalse(list(self.docs.rglob('*.svg')))
        self.assertFalse(list((self.root / 'site').rglob('*.d2')))
        self.assertFalse(list((self.root / 'site').rglob('*.json5')))
        # A dark waveform must remain readable as a standalone SVG, not only
        # when displayed on a particular HTML background.
        wave_dark = [p for p in (self.root / 'site' / 'assets' / 'diagrams').glob('*.dark.svg')
                     if 'WaveDrom' in p.read_text(encoding='utf-8')]
        self.assertTrue(wave_dark)
        for path in wave_dark:
            self.assertIn('fill:#111827', path.read_text(encoding='utf-8'))

    def test_import_changes_are_rendered_on_next_build(self):
        self.write('assets/part.d2', 'value: BEFORE\n')
        self.write('assets/main.d2', 'cpu: @part\n')
        self.write('index.md', '# Imported\n\n![CPU](assets/main.d2)\n')
        first = self.build()
        self.write('assets/part.d2', 'value: AFTER\n')
        second = self.build()
        self.assertNotEqual(re.findall(r'assets/diagrams/[^" ]+', first),
                            re.findall(r'assets/diagrams/[^" ]+', second))
        self.assertTrue(any('AFTER' in p.read_text(encoding='utf-8')
                            for p in (self.root / 'site' / 'assets' / 'diagrams').glob('*.svg')))

    def test_per_diagram_width_for_both_fences_and_source_images(self):
        self.write('assets/cpu.d2', 'CPU -> Cache\n')
        self.write('assets/clock.json5', "{signal:[{name:'clk',wave:'p...'}]}\n")
        self.write('index.md', '''# Width controls

```d2 width="850px" layout="tala" alt="Pixels"
CPU -> Cache
```

```wavedrom width="90%" alt="Percent"
{signal:[{name:'clk',wave:'p...'}]}
```

![File pixels](assets/cpu.d2){width="640"}

![File percent](assets/clock.json5){as="wavedrom" width="75%"}
''')
        output = self.build()
        pairs = re.findall(r'<span class="diagram-pair">(.*?)</span>', output, re.S)
        self.assertEqual(len(pairs), 4)
        for pair, expected in zip(pairs, (850, '90%', 640, '75%')):
            for tag in re.findall(r'<img[^>]+>', pair):
                img = ET.fromstring(tag[:-1] + ' />')
                if isinstance(expected, int):
                    self.assertEqual(int(img.get('width')), expected)
                    path = (self.root / 'site' / 'guide' / img.get('src')).resolve()
                    vb = list(map(float, ET.parse(path).getroot().get('viewBox').split()))
                    self.assertAlmostEqual(int(img.get('height')), expected * vb[3] / vb[2], delta=1)
                else:
                    self.assertIn('width:' + expected, img.get('style'))
                    self.assertGreater(int(img.get('width')), 0)
                    self.assertGreater(int(img.get('height')), 0)

    def test_invalid_width_fails_for_fences_and_source_images(self):
        self.write('assets/cpu.d2', 'CPU -> Cache\n')
        for width in ('0', '-10', '101%', '0%', 'wide', '50%;display:none'):
            for markup in (f'```d2 width="{width}"\nCPU -> Cache\n```',
                           f'![CPU](assets/cpu.d2){{width="{width}"}}'):
                with self.subTest(width=width, markup=markup):
                    self.write('index.md', '# Bad width\n\n' + markup + '\n')
                    with self.assertRaises(Exception) as raised:
                        self.build()
                    error = raised.exception
                    while error.__context__ is not None:
                        error = error.__context__
                    self.assertIn('width', str(error))

    def check_d2_rendering(self, source, header, flags, expected_flags, default_layout='elk'):
        """Compare both Markdown entry points with a direct native D2 render."""
        settings = yaml.safe_load(self.config_path.read_text(encoding='utf-8'))
        settings['extra'] = {'diagrams': {'layout': default_layout}}
        self.config_path.write_text(yaml.safe_dump(settings), encoding='utf-8')
        self.write('assets/cpu.d2', source)
        self.write('index.md', f'''# D2 parameters

```d2 {header}
{source}```

![CPU](assets/cpu.d2){{{header} width="85%"}}
''')
        # Capture the real renderer calls as well as checking the output, so a
        # silently discarded option or a leaked environment default is caught.
        with patch.dict(os.environ, {'D2_LAYOUT': 'dagre', 'D2_PAD': '999',
                                     'D2_SKETCH': 'true'}):
            with patch('subprocess.run', wraps=subprocess.run) as calls:
                output = self.build()
        renders = [call for call in calls.call_args_list
                   if str(call.args[0][0]).lower().endswith('d2.exe')]
        self.assertTrue(renders)
        for call in renders:
            args = call.args[0]
            for name in ('--layout', '--pad'):
                self.assertEqual(name in args, name in flags)
                if name in flags:
                    self.assertEqual(args[args.index(name) + 1], flags[flags.index(name) + 1])
            self.assertEqual([x for x in args if x.startswith('--sketch=')],
                             [x for x in flags if x.startswith('--sketch=')])
            self.assertNotIn('D2_LAYOUT', call.kwargs['env'])
            self.assertNotIn('D2_PAD', call.kwargs['env'])
            self.assertNotIn('D2_SKETCH', call.kwargs['env'])

        exe = renders[0].args[0][0]
        expected_env = dict(os.environ)
        for name in ('D2_LAYOUT', 'D2_PAD', 'D2_SKETCH'):
            expected_env.pop(name, None)
        images = re.findall(r'<img[^>]+class="diagram-(?:light|dark)"[^>]*>', output)
        self.assertEqual(len(images), 4)
        for tag in images:
            img = ET.fromstring(tag[:-1] + ' />')
            self.assertNotIn('layout', img.attrib)
            self.assertNotIn('sketch', img.attrib)
            self.assertNotIn('pad', img.attrib)
            mode = img.get('class').removeprefix('diagram-')
            expected = subprocess.run(
                [exe, '--theme', '0' if mode == 'light' else '200',
                 '--dark-theme', '-1', *expected_flags, '-', '-'],
                input=source, text=True, encoding='utf-8', capture_output=True,
                check=True, cwd=self.docs / 'guide' / 'assets', env=expected_env,
            ).stdout
            path = (self.root / 'site' / 'guide' / img.get('src')).resolve()
            actual_root, expected_root = ET.parse(path).getroot(), ET.fromstring(expected)
            self.assertEqual(actual_root.get('viewBox'), expected_root.get('viewBox'))
            def labels(root):
                return [(x.get('x'), x.get('y'), ''.join(x.itertext()))
                        for x in root.iter() if x.tag.endswith('}text')]
            self.assertEqual(labels(actual_root), labels(expected_root))
        self.assertEqual(output.count('class="diagram-pair"'), 2)

    def test_image_and_fence_markdown_options_override_source_header(self):
        source = ('vars: { d2-config: { layout-engine: elk; pad: 60; sketch: true } }\n'
                  'direction: right\nCPU <-> RAM: Link\n')
        self.check_d2_rendering(
            source, 'layout="tala" sketch="false" pad="8"',
            ['--layout', 'tala', '--sketch=false', '--pad', '8'],
            ['--layout', 'tala', '--sketch=false', '--pad', '8'],
        )

    def test_source_header_overrides_site_defaults(self):
        source = ('vars: { d2-config: { layout-engine: tala; pad: 40; sketch: true } }\n'
                  'direction: right\nCPU <-> RAM: Link\n')
        self.check_d2_rendering(source, '', [],
                                ['--layout', 'tala', '--pad', '40', '--sketch=true'])

    def test_unconfigured_source_keeps_site_defaults(self):
        self.check_d2_rendering('direction: right\nCPU <-> RAM: Link\n', '', [],
                                ['--layout', 'elk', '--pad', '24', '--sketch=false'])

    def test_invalid_render_options_fail_for_fences_and_source_images(self):
        self.write('assets/cpu.d2', 'CPU -> RAM\n')
        for name, value in (('layout', 'unknown'), ('sketch', 'maybe'), ('pad', '-1')):
            for markup in (f'```d2 {name}="{value}"\nCPU -> RAM\n```',
                           f'![CPU](assets/cpu.d2){{{name}="{value}"}}'):
                with self.subTest(option=name, markup=markup):
                    self.write('index.md', '# Invalid option\n\n' + markup + '\n')
                    with self.assertRaises(Exception) as raised:
                        self.build()
                    error = raised.exception
                    while error.__context__ is not None:
                        error = error.__context__
                    self.assertIn(name, str(error))

    def test_bad_d2_fails_build_instead_of_showing_code(self):
        self.write('index.md', '# Bad\n\n```d2\nbroken: {\n```\n')
        with self.assertRaises(Exception):
            self.build()

    def test_non_index_markdown_uses_final_page_url(self):
        self.write('index.md', '# Guide\n')
        self.write('assets/cpu.d2', 'CPU -> RAM\n')
        self.write('diagram.md', '# Diagram\n\n![CPU](assets/cpu.d2)\n')
        self.build()
        page = self.root / 'site' / 'guide' / 'diagram' / 'index.html'
        images = re.findall(r'<img[^>]+src="([^"]+\.svg)"', page.read_text(encoding='utf-8'))
        self.assertEqual(len(images), 2)
        for uri in images:
            self.assertTrue((page.parent / uri).resolve().is_file(), uri)

    def test_blog_post_and_excerpt_have_working_asset_urls(self):
        settings = yaml.safe_load(self.config_path.read_text(encoding='utf-8'))
        settings.update({'theme': {'name': 'material'}, 'plugins': ['search', 'blog']})
        self.config_path.write_text(yaml.safe_dump(settings), encoding='utf-8')
        posts = self.docs / 'blog' / 'posts'
        (posts / 'assets').mkdir(parents=True)
        (self.docs / 'blog' / 'index.md').write_text('# Blog\n', encoding='utf-8')
        (posts / 'assets' / 'cpu.d2').write_text('CPU -> Cache\n', encoding='utf-8')
        (posts / 'test.md').write_text('''---
date: 2020-01-01
---
# Diagram post

![CPU](assets/cpu.d2)

<!-- more -->

```wavedrom
{signal:[{name:'clk',wave:'p...'}]}
```
''', encoding='utf-8')
        build(load_config(str(self.config_path)))
        checked = 0
        for page in (self.root / 'site' / 'blog').rglob('*.html'):
            for uri in re.findall(r'<img[^>]+src="([^"]*assets/diagrams/[^" ]+\.svg)"',
                                  page.read_text(encoding='utf-8')):
                self.assertTrue((page.parent / uri).resolve().is_file(), (page, uri))
                checked += 1
        self.assertGreaterEqual(checked, 6)  # post pair + excerpt pair + waveform pair

    def test_default_serve_enables_live_reload(self):
        from click.testing import CliRunner
        from unittest.mock import patch
        from mkdocs.__main__ import cli

        with patch('mkdocs.commands.serve.serve') as serve:
            result = CliRunner().invoke(cli, ['serve'])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(serve.call_args.kwargs['livereload'])

    def test_bad_wavejson_fails_build(self):
        self.write('index.md', '# Bad\n\n```wavedrom\n{signal: [\n```\n')
        with self.assertRaises(Exception):
            self.build()

    def test_missing_source_fails_build(self):
        self.write('index.md', '# Missing\n\n![missing](assets/missing.d2)\n')
        with self.assertRaises(Exception):
            self.build()


if __name__ == '__main__':
    unittest.main(verbosity=2)
