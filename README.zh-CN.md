<p align="center">
  <a href="https://smlcoke.com/">
    <img src="docs/assets/branding/options/02-paper-geometry.svg" alt="SmlCoke" width="100%" />
  </a>
</p>

<p align="center"><a href="README.md">English</a> · <strong>简体中文</strong></p>

<p align="center">
  <a href="https://smlcoke.com/">访问网站</a> ·
  <a href="https://smlcoke.com/blog/">阅读博客</a> ·
  <a href="https://smlcoke.com/lab/">体验应用</a> ·
  <a href="https://smlcoke.com/comments/">留言交流</a>
</p>

---

## 记录所学、所想与所做

这里是 **[SmlCoke 个人网站](https://smlcoke.com/)** 的源码仓库，收录课程笔记、工程实践、工具指南，以及学习与生活中的零散思考。网站基于 MkDocs 与 Material for MkDocs 构建，正文以中文为主，持续积累与完善。

## 内容导航

| 分区 | 你可以找到 |
| :--- | :--- |
| [微电子](https://smlcoke.com/microelectronics/) | 信号与系统、数字集成电路、处理器、SoC、HDL 与 EDA |
| [机器学习](https://smlcoke.com/machine-learning/) | 神经网络基础、计算机视觉与模型阅读笔记 |
| [编程](https://smlcoke.com/programming/) | Rust 学习记录与 Python 环境管理 |
| [工具](https://smlcoke.com/tools/) | AI 工具、Git、Docker、Linux、WSL 与技术写作 |
| [博客](https://smlcoke.com/blog/) | 工作记录、日常随笔与阶段性的思考 |
| [应用](https://smlcoke.com/lab/) | 浏览器小工具，包括基于 Rust 与 WebAssembly 的加解密应用 |

## 仓库结构

```text
docs/          正文、图片、样式、脚本与应用资源
overrides/     Material 主题模板定制
scripts/       内容维护工具
mkdocs.yml     网站配置与导航
```

`main` 分支保存源码，`gh-pages` 分支保存发布产物。本地构建目录 `site/` 与个人开发笔记 `dev/` 不进入源码分支。

普通知识文章采用 `<topic>/index.md`，图片和附件放在就近的 `assets/` 目录；博客保留独立的日期发布结构。

## 联系与反馈

**SmlCoke / Jun Feng** · [GitHub](https://github.com/SmlCoke) · [Hugging Face](https://huggingface.co/SmlCoke) · [邮件](mailto:j.feng.st05@gmail.com)

发现链接失效或笔记有误，欢迎[提交 Issue](https://github.com/SmlCoke/smlcoke-web/issues)，也可以在[留言板](https://smlcoke.com/comments/)交流。

本项目采用 [MIT 许可证](LICENSE)。
