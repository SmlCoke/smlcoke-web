"""Destructive-operation checks run exclusively inside disposable docs trees."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

import webp_converter_safe as converter


class ConverterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="smlcoke-webp-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.docs = self.root / "docs"
        self.target = self.docs / "article"
        self.target.mkdir(parents=True)
        self.stdout, self.stderr = StringIO(), StringIO()

    def write(self, relative, text):
        path = self.docs / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        return path

    def image(self, relative="article/assets/a.png", *, mode="RGB", size=(256, 256)):
        path = self.docs / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        values = random.Random(2).randbytes(size[0] * size[1])
        picture = Image.frombytes("L", size, values).convert(mode)
        if mode == "RGBA":
            picture.putalpha(Image.frombytes("L", size, random.Random(3).randbytes(size[0] * size[1])))
        picture.save(path)
        return path

    def run_converter(self, **kwargs):
        with redirect_stdout(self.stdout), redirect_stderr(self.stderr):
            return converter.run(self.target, docs_dir=self.docs, **kwargs)

    def snapshot(self):
        return {path.relative_to(self.root): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file()}

    def test_success_preserves_bom_crlf_and_all_supported_link_forms(self):
        image = self.image("article/assets/示例 (1).PNG")
        text = ('\ufeff# Example\r\n'
                '![标题](<assets/示例 (1).PNG> "保持标题")\r\n'
                '[原图](assets/示例%20%281%29.PNG?q=1&x=2#detail)\r\n'
                '![引用][pic]\r\n'
                '[pic]: <assets/示例 (1).PNG> "参考标题"\r\n'
                '<img alt="图" src="assets/示例 (1).PNG?q=1&amp;x=2">\r\n'
                '<a href=assets/示例%20%281%29.PNG>open</a>\r\n'
                '![escaped](assets/示例%20\\(1\\).PNG)\r\n')
        md = self.write("article/index.md", text)
        result = self.run_converter()
        self.assertEqual(result.errors, 0, self.stderr.getvalue())
        self.assertEqual(result.converted, 1, self.stderr.getvalue())
        self.assertFalse(image.exists())
        self.assertTrue(image.with_suffix(".webp").is_file())
        self.assertEqual(md.read_bytes(), text.replace(".PNG", ".webp").encode("utf-8"))

    def test_image_is_converted_once_and_nested_preview_download_both_change(self):
        image = self.image()
        first = self.write("article/index.md", '[![图](assets/a.png)](assets/a.png)\n')
        second = self.write("article/other.md", '![图](assets/a.png)\n')
        report = self.run_converter()
        self.assertEqual(report.converted, 1)
        self.assertEqual(len(report.updated), 2)
        self.assertNotIn("a.png", first.read_text(encoding="utf-8"))
        self.assertIn("a.webp", second.read_text(encoding="utf-8"))
        self.assertFalse(image.exists())

    def test_shortcut_and_collapsed_reference_images(self):
        self.image()
        md = self.write("article/index.md", '![pic]\n![pic][]\n[pic]: assets/a.png\n')
        self.assertEqual(self.run_converter().converted, 1, self.stderr.getvalue())
        self.assertIn("[pic]: assets/a.webp", md.read_text(encoding="utf-8"))

    def test_existing_webp_never_overwritten_or_relinked(self):
        image = self.image()
        output = image.with_suffix(".webp")
        output.write_bytes(b"existing content, even if not a valid image")
        self.write("article/index.md", '![图](assets/a.png)\n')
        before = self.snapshot()
        result = self.run_converter(remaining="search-docs")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(result.skipped["exists"], 1)
        self.assertEqual(result.errors, 0)

    def test_output_collision_skips_every_source(self):
        self.image()
        self.image("article/assets/a.jpg")
        self.write("article/index.md", '![a](assets/a.png) ![b](assets/a.jpg)\n')
        before = self.snapshot()
        result = self.run_converter()
        self.assertEqual(result.skipped["collision"], 2)
        self.assertEqual(before, self.snapshot())

    def test_missing_warning_contains_source_line_and_resolved_path(self):
        md = self.write("article/index.md", '# Title\n\n![missing](assets/missing.png)\n')
        result = self.run_converter()
        self.assertEqual(result.errors, 0)
        self.assertEqual(result.skipped["missing"], 1)
        self.assertIn(f"{md}:3", self.stderr.getvalue())
        self.assertIn(str(self.target / "assets/missing.png"), self.stderr.getvalue())

    def test_warn_preserves_shared_image_and_every_document(self):
        self.image()
        self.write("article/index.md", '![local](assets/a.png)\n')
        self.write("outside/index.md", '![outside](../article/assets/a.png)\n')
        before = self.snapshot()
        result = self.run_converter()
        self.assertEqual(result.skipped["cross-scope"], 1)
        self.assertEqual(before, self.snapshot())

    def test_search_docs_updates_shared_image_and_every_document(self):
        self.image()
        self.write("article/index.md", '![local](assets/a.png)\n')
        outside = self.write("outside/index.md", '![outside](../article/assets/a.png)\n')
        result = self.run_converter(remaining="search-docs")
        self.assertEqual(result.converted, 1)
        self.assertIn("a.webp", outside.read_text(encoding="utf-8"))

    def test_remaining_image_referenced_only_outside_requires_search_docs(self):
        image = self.image()
        md = self.write("outside/index.md", '![outside](../article/assets/a.png)\n')
        self.assertEqual(self.run_converter().converted, 0)
        self.assertTrue(image.exists())
        self.assertEqual(self.run_converter(remaining="search-docs").converted, 1)
        self.assertIn("a.webp", md.read_text(encoding="utf-8"))

    def test_unreferenced_images_never_converted_or_deleted_in_either_mode(self):
        self.image()
        before = self.snapshot()
        for mode in ("warn", "search-docs"):
            result = self.run_converter(remaining=mode)
            self.assertEqual(result.skipped["unreferenced"], 1)
            self.assertEqual(before, self.snapshot())

    def test_safe_directory_excludes_every_descendant_and_missing_reference(self):
        self.image("article/protected/nested/a.png")
        self.write("article/index.md", '![a](protected/nested/a.png)\n![b](protected/missing.jpg)\n')
        before = self.snapshot()
        for mode in ("warn", "search-docs"):
            result = self.run_converter(safe_dirs=[self.target / "protected"], remaining=mode)
            self.assertEqual((result.converted, result.warnings, result.errors), (0, 0, 0))
            self.assertEqual(before, self.snapshot())

    def test_target_inside_safe_directory_immediately_ignored(self):
        self.image()
        self.write("article/index.md", '![a](assets/a.png)\n')
        with patch.object(converter, "scan", side_effect=AssertionError("must not scan")):
            self.assertEqual(self.run_converter(safe_dirs=[self.docs]).errors, 0)
        self.assertIn("IGNORED", self.stdout.getvalue())

    def test_safe_cli_union_multiple_values_repeated_flags_and_defaults(self):
        with patch.object(converter, "ROOT", self.root), patch.object(converter, "DOCS_DIR", self.docs), \
             patch.object(converter, "DEFAULT_SAFE_DIRS", ["docs/a", "docs/b"]), \
             patch.object(converter, "run", return_value=converter.Report()) as run:
            converter.main(["--path", str(self.target), "--safe-dirs", str(self.docs / "c"),
                            str(self.docs / "d"), "--safe-dirs", str(self.docs / "e")])
        actual = {path.resolve() for path in run.call_args.kwargs["safe_dirs"]}
        self.assertEqual(actual, {self.docs / name for name in "abcde"})

    def test_safe_sibling_prefix_is_not_excluded(self):
        self.image("article/safe-other/a.png")
        self.write("article/index.md", '![a](safe-other/a.png)\n')
        result = self.run_converter(safe_dirs=[self.target / "safe"])
        self.assertEqual(result.converted, 1)

    def test_dry_run_has_zero_filesystem_changes(self):
        self.image()
        self.write("article/index.md", '![a](assets/a.png)\n')
        before = self.snapshot()
        with patch.object(Image.Image, "save", side_effect=AssertionError("must not encode")):
            result = self.run_converter(dry_run=True)
        self.assertEqual(result.planned, 1)
        self.assertEqual(result.converted, 0)
        self.assertEqual(before, self.snapshot())

    def test_external_images_non_bitmap_sources_and_code_examples_untouched(self):
        self.image()
        text = ('![local](assets/a.png)\n![remote](https://example.test/a.png)\n'
                '![data](data:image/png;base64,AAAA)\n'
                '![webp](assets/already.webp) ![svg](a.svg) ![D2](a.d2) ![wave](a.json5)\n'
                '`![inline](assets/a.png)`\n'
                '```markdown\n![example](assets/a.png)\n```\n'
                '<!-- ![comment](assets/a.png) -->\n'
                '<pre>![pre](assets/a.png)</pre>\n')
        md = self.write("article/index.md", text)
        result = self.run_converter()
        self.assertEqual(result.converted, 1, self.stderr.getvalue())
        self.assertEqual(md.read_text(encoding="utf-8"), text.replace("![local](assets/a.png)", "![local](assets/a.webp)"))

    def test_non_markdown_and_unsupported_references_protect_source(self):
        for kind, content in [("script", "const image = 'article/assets/a.png';"),
                              ("frontmatter", '---\nimage: assets/a.png\n---\n'),
                              ("srcset", '<img srcset="assets/a.png 1x, assets/b.webp 2x">\n'),
                              ("indented", '!!! note\n    ![图](assets/a.png)\n'),
                              ("inline-script", '<script>image.src="assets/a.png";</script>\n')]:
            with self.subTest(kind=kind):
                self.image()
                self.write("article/index.md", '![图](assets/a.png)\n' + (content if kind != "script" else ""))
                js = self.docs / "script.js"
                if kind == "script":
                    self.write("script.js", content)
                elif js.exists():
                    js.unlink()
                before = self.snapshot()
                result = self.run_converter(remaining="search-docs")
                self.assertEqual(result.skipped["unsupported-reference"], 1)
                self.assertEqual(self.snapshot(), before)

    def test_no_conversion_of_images_outside_path(self):
        self.image("outside/a.png")
        self.write("article/index.md", '![图](../outside/a.png)\n')
        before = self.snapshot()
        result = self.run_converter(remaining="search-docs")
        self.assertEqual(result.skipped["outside-path"], 1)
        self.assertEqual(self.snapshot(), before)

    def test_larger_webp_keeps_original_and_link(self):
        image = self.image(size=(1, 1))
        self.write("article/index.md", '![图](assets/a.png)\n')
        before = self.snapshot()
        original_save = Image.Image.save

        def padded_save(picture, stream, *args, **kwargs):
            original_save(picture, stream, *args, **kwargs)
            stream.write(b"padding" * 100)

        with patch.object(Image.Image, "save", new=padded_save):
            result = self.run_converter()
        self.assertEqual(result.skipped["not-smaller"], 1)
        self.assertTrue(image.exists())
        self.assertEqual(before, self.snapshot())

    def test_encode_failure_keeps_original_and_link(self):
        self.image()
        self.write("article/index.md", '![图](assets/a.png)\n')
        before = self.snapshot()
        with patch.object(Image.Image, "save", side_effect=OSError("encode failed")):
            result = self.run_converter()
        self.assertEqual(result.errors, 1)
        self.assertEqual(before, self.snapshot())

    def test_partial_markdown_write_failure_keeps_original_and_new_webp(self):
        image = self.image()
        first = self.write("article/1.md", '![图](assets/a.png)\n')
        second = self.write("article/2.md", '![图](assets/a.png)\n')
        write = converter.atomic_write

        def fail_second(document, data):
            if document.path == second:
                raise OSError("write failed")
            write(document, data)

        with patch.object(converter, "atomic_write", side_effect=fail_second):
            result = self.run_converter()
        self.assertEqual(result.errors, 1)
        self.assertTrue(image.exists())
        self.assertTrue(image.with_suffix(".webp").is_file())
        self.assertIn("a.webp", first.read_text(encoding="utf-8"))
        self.assertIn("a.png", second.read_text(encoding="utf-8"))

    def test_output_appearing_during_publish_is_never_overwritten(self):
        image = self.image()
        md = self.write("article/index.md", '![图](assets/a.png)\n')

        def race(source, output):
            output.write_bytes(b"someone else's file")
            raise FileExistsError(output)

        with patch.object(converter.os, "link", side_effect=race):
            result = self.run_converter()
        self.assertEqual(result.skipped["exists"], 1)
        self.assertTrue(image.exists())
        self.assertEqual(image.with_suffix(".webp").read_bytes(), b"someone else's file")
        self.assertIn("a.png", md.read_text(encoding="utf-8"))

    def test_transparent_output_retains_alpha(self):
        image = self.image(mode="RGBA")
        self.write("article/index.md", '![图](assets/a.png)\n')
        self.assertEqual(self.run_converter().converted, 1, self.stderr.getvalue())
        with Image.open(image.with_suffix(".webp")) as output:
            self.assertIn("A", output.getbands())

    def test_lossless_transparency_preserves_hidden_rgb_and_alpha(self):
        image = self.image(mode="RGBA")
        with Image.open(image) as original:
            pixels = original.tobytes()
        self.write("article/index.md", '![图](assets/a.png)\n')
        report = self.run_converter(lossless=True)
        self.assertEqual(report.converted, 1, self.stderr.getvalue())
        with Image.open(image.with_suffix(".webp")) as output:
            self.assertEqual(output.convert("RGBA").tobytes(), pixels)

    def test_multiple_images_in_same_document_keep_correct_source_offsets(self):
        self.image()
        self.image("article/assets/long-name.jpg")
        text = '![一](assets/a.png) 和 ![二](assets/long-name.jpg)\n![三](assets/a.png)\n'
        md = self.write("article/index.md", text)
        report = self.run_converter(quality=30)
        self.assertEqual(report.converted, 2, self.stderr.getvalue())
        self.assertEqual(md.read_text(encoding="utf-8"), text.replace(".png", ".webp").replace(".jpg", ".webp"))

    def test_multiframe_png_is_skipped(self):
        image = self.image()
        with Image.open(image) as first:
            first.save(image, save_all=True, append_images=[Image.new("RGB", first.size, "red")], duration=100)
        self.write("article/index.md", '![图](assets/a.png)\n')
        before = self.snapshot()
        self.assertEqual(self.run_converter().skipped["multiframe"], 1)
        self.assertEqual(self.snapshot(), before)

    def test_changing_markdown_during_conversion_is_not_overwritten(self):
        image = self.image()
        md = self.write("article/index.md", '![图](assets/a.png)\n')
        original_link = converter.os.link

        def user_edit(source, output):
            original_link(source, output)
            md.write_bytes(b"user changes during conversion")

        with patch.object(converter.os, "link", side_effect=user_edit):
            result = self.run_converter()
        self.assertEqual(result.errors, 1)
        self.assertTrue(image.exists())
        self.assertEqual(md.read_bytes(), b"user changes during conversion")

    def test_cli_validation_and_help_never_run_conversion(self):
        script = Path(converter.__file__)
        for args, expected in [(["--help"], 0), ([], 2),
                               (["--path", str(script.parent.parent / "docs"), "--quality", "101"], 2),
                               (["--path", str(self.root)], 2)]:
            with self.subTest(args=args):
                result = subprocess.run([sys.executable, "-X", "utf8", "-B", str(script), *args],
                                        capture_output=True, encoding="utf-8")
                self.assertEqual(result.returncode, expected, result.stderr)

    def test_lossless_output_retains_every_pixel(self):
        image = self.image()
        with Image.open(image) as original:
            pixels = original.convert("RGB").tobytes()
        self.write("article/index.md", '![图](assets/a.png)\n')
        report = self.run_converter(lossless=True)
        self.assertEqual(report.converted, 1, self.stderr.getvalue())
        with Image.open(image.with_suffix(".webp")) as output:
            self.assertEqual(output.convert("RGB").tobytes(), pixels)

    def test_jpeg_exif_orientation_is_applied(self):
        image = self.image("article/assets/a.jpg", size=(256, 128))
        with Image.open(image) as source:
            picture = source.copy()
        exif = Image.Exif()
        exif[274] = 6
        picture.save(image, quality=98, exif=exif)
        self.write("article/index.md", '![图](assets/a.jpg)\n')
        report = self.run_converter(quality=50)
        self.assertEqual(report.converted, 1, self.stderr.getvalue())
        with Image.open(image.with_suffix(".webp")) as output:
            self.assertEqual(output.size, (128, 256))

    def test_symlink_alias_reference_protects_actual_image(self):
        image = self.image()
        alias = image.with_name("alias.png")
        try:
            alias.symlink_to(image)
        except OSError:
            self.skipTest("symlink creation unavailable")
        self.write("article/index.md", '![图](assets/a.png)\n![别名](assets/alias.png)\n')
        result = self.run_converter()
        self.assertEqual(result.converted, 0)
        self.assertEqual(result.skipped["unsupported-reference"], 1)
        self.assertTrue(image.is_file())

    def test_invalid_scope_and_safe_directory_cannot_mutate_files(self):
        self.image()
        self.write("article/index.md", '![图](assets/a.png)\n')
        before = self.snapshot()
        self.assertEqual(self.run_converter(safe_dirs=[self.root]).errors, 1)
        with redirect_stdout(self.stdout), redirect_stderr(self.stderr):
            result = converter.run(self.root, docs_dir=self.docs)
        self.assertEqual(result.errors, 1)
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
