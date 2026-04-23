# MkDocs 站点开发笔记

这页是这次视觉重构的维护说明。以后你要继续调站点，不需要重新猜整套结构，直接看这里就行。

## 1. 这次主要改了什么

- `mkdocs.yml`
  - 补了亮色 / 暗色 palette
  - 打开了搜索建议、搜索高亮、目录跟随、标签页联动、代码复制等功能
  - 增加了更适合知识库写作的 Markdown 扩展
- `docs/stylesheets/extra.css`
  - 从零整理成一套变量化设计系统
  - 统一了正文、代码块、公式块、卡片、导航、侧栏、搜索框、hero
- `docs/Tools/markdown/writing_style_guide.md`
  - 给后续写文章留了规范

## 2. 以后优先改哪里

### 颜色

先改 `docs/stylesheets/extra.css` 顶部两组变量：

- `:root` 是浅色模式
- `[data-md-color-scheme="slate"]` 是深色模式

最关键的变量是：

- `--site-accent`
- `--site-accent-strong`
- `--site-panel`
- `--site-border`
- `--site-code-bg`
- `--site-math-bg`

如果只想整体换风格，优先改这些，不要先去下面逐个组件里硬改颜色。

### 字体

正文现在用的是：

```css
font-family: "Inter", "MiSans", "PingFang SC", "Noto Sans SC", "Microsoft YaHei", ...
```

代码字体保留：

```css
font-family: "Maple Mono", ...
```

如果以后想继续换中文字体，只改正文栈，不要碰 `Maple Mono` 那一行。

### 正文层级

标题层级主要在这些选择器里：

- `.md-typeset h1`
- `.md-typeset h2`
- `.md-typeset h3`
- `.md-typeset h4`

其中 `h4` 是这次特别增强过的，因为你的课程笔记里很多关键结论都放在四级标题。

### 代码块和公式块

代码块看：

- `.md-typeset pre`
- `.md-typeset .highlight`
- `.md-typeset .highlight pre`

公式块看：

- `.md-typeset div.arithmatex`
- `.md-typeset span.arithmatex`

如果只是想微调“框感”和“科技感”，通常改边框、背景、阴影就够了，不必动 KaTeX 脚本。

## 3. 新增了哪些可复用类

这些类是给你以后写文章时直接复用的：

- `chapter-summary`
- `term-grid`
- `term-card`
- `term-card__title`
- `media-frame`
- `figure-caption`
- `note-card`
- `section-hero`

前 6 个主要给正文内容使用；后 2 个主要给首页和栏目导航页使用。

## 4. 推荐维护方式

1. 先改 `mkdocs.yml` 里的主题能力，再改 CSS。
2. 改颜色先改变量，不要直接全局查找替换十几处十六进制色值。
3. 新增正文样式时，先想“是不是能复用现有 class”，再决定要不要造新类。
4. 写文章尽量吃标准 Markdown + admonition + tabs，少依赖太碎的 HTML。

## 5. 本地验证

最稳妥的是每次改完都跑一次：

```powershell
mkdocs build
```

如果要本地预览：

```powershell
mkdocs serve
```

重点看这几类页面有没有被改坏：

- 首页 `docs/index.md`
- 栏目页，例如 `docs/me/DIC/VLSI/index.md`
- 公式密集页，例如 `docs/me/DIC/PU/ch1-the_software_hardware_interface/note.md`
- 工具说明页，例如 `docs/Tools/...`
- 图片密集页，例如 `docs/me/verilog/Study_note.md`

## 6. 这次我刻意保留的边界

- 没换掉 `Material for MkDocs`
- 没批量重写你现有 Markdown 内容
- 没引入新的复杂模板体系
- KaTeX 继续保留，只改表现层

所以后面继续维护时，思路也尽量保持一致：优先用配置和样式解决问题，只有确实需要时再改内容结构。
