<p align="center">
  <a href="https://smlcoke.com/">
    <img src="docs/assets/branding/options/02-paper-geometry.svg" alt="SmlCoke" width="100%" />
  </a>
</p>

<p align="center"><strong>English</strong> · <a href="README.zh-CN.md">简体中文</a></p>

<p align="center">
  <a href="https://smlcoke.com/">Visit the website</a> ·
  <a href="https://smlcoke.com/blog/">Read the blog</a> ·
  <a href="https://smlcoke.com/lab/">Explore apps</a> ·
  <a href="https://smlcoke.com/comments/">Leave a message</a>
</p>

---

## A place to learn, build, and remember

This is the source repository for **[SmlCoke's personal website](https://smlcoke.com/)**: a growing collection of course notes, engineering experiments, practical guides, and everyday thoughts. Built with MkDocs and Material for MkDocs, written mostly in Chinese.

## Explore

| Section | What you'll find |
| :--- | :--- |
| [Microelectronics](https://smlcoke.com/microelectronics/) | Signals and systems, digital circuits, processors, SoC, HDL, and EDA |
| [Machine learning](https://smlcoke.com/machine-learning/) | Neural network fundamentals, computer vision, and model reading notes |
| [Programming](https://smlcoke.com/programming/) | Rust study notes and Python environments |
| [Tools](https://smlcoke.com/tools/) | AI tools, Git, Docker, Linux, WSL, and technical writing |
| [Blog](https://smlcoke.com/blog/) | Work logs, personal records, and ideas along the way |
| [Apps](https://smlcoke.com/lab/) | Small browser tools, including Rust-powered WebAssembly cryptography |

## Inside the repository

```text
docs/          Articles, images, styles, scripts, and app assets
overrides/     Custom Material templates
scripts/       Content maintenance utilities
mkdocs.yml     Site configuration and navigation
```

The `main` branch holds the source; `gh-pages` holds the published site. Local build output (`site/`) and personal development notes (`dev/`) are excluded from the source branch.

Raster images (WebP, PNG, JPEG, GIF, AVIF, and similar formats) are maintained locally and excluded from `main`; SVG and ICO files remain versioned. MkDocs still copies local images into the published site. Back up these images separately and restore them before building from a fresh clone. The `gh-pages` branch retains only the latest published snapshot, including its images.

To clone only the source without downloading the publication branch: `git clone --single-branch --branch main https://github.com/SmlCoke/smlcoke-web.git`.

Regular notes use `<topic>/index.md`, with images and attachments in a nearby `assets/` directory. Blog posts keep their own dated publishing structure.

## Say hello

**SmlCoke / Jun Feng** · [GitHub](https://github.com/SmlCoke) · [Hugging Face](https://huggingface.co/SmlCoke) · [Email](mailto:j.feng.st05@gmail.com)

Found a broken link or an error in a note? [Open an issue](https://github.com/SmlCoke/smlcoke-web/issues) or stop by the [guestbook](https://smlcoke.com/comments/).

Licensed under the [MIT License](LICENSE).
