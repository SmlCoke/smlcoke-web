# 维护脚本

本目录保存站点自己的小型维护脚本。D2、Node.js 和 npm 依赖安装在仓库外，不在这里存放第三方工具源码或生成图片。

命令均从仓库根目录执行，使用已有 Conda `web` 环境：

```powershell
conda activate web
$env:PYTHONUTF8 = '1'
```

也可用 `& D:\Anaconda\envs\web\python.exe` 代替下面的 `python`。

## mkdocs_diagrams.py

由 `mkdocs.yml` 的 `hooks` 自动加载的构建钩子。

- 接管 `d2`、`wavedrom` 代码块，保留 SuperFences 对列表、标签页、提示框的支持。
- 将 Markdown 图片引用中的本地 `.d2`、`.json5` 文件作为图源；`docs/` 中的 `.json5` 保留作 WaveDrom 图源使用。
- 一份图源生成浅色、深色两个独立 SVG，通过 `<img>` 引用，不内嵌 HTML。
- 使用 MkDocs 内存文件 API，只向实际构建目录写产物，不写回 `docs/`。
- 代码块支持 `width="850"` / `width="90%"` 单图宽度；独立图源引用支持同名图片属性。未设置时等比例限制在 760×320px，明确设置后覆盖自动尺寸框，仍随内容栏缩小。
- D2 代码块与独立图源引用都支持 `layout`、`sketch`、`pad`。Markdown 显式参数覆盖图源的 `vars.d2-config`，未指定时保留图源配置，再回退到站点布局、24 留白及非 sketch 默认值。
- 不保存跨构建渲染缓存；每次重新读取 D2 导入文件。仅在单次构建内复用相同输入。
- 源码错误、工具缺失、无效 SVG 或渲染超时使构建失败，不静默显示代码或复用旧图。

日常直接运行原有命令，无需先导图：

```powershell
python -m mkdocs serve
python -m mkdocs build --clean --strict
```

工具自检会在内存中渲染并验证四张 SVG，不写图片文件：

```powershell
python scripts/mkdocs_diagrams.py --check
```

默认工具：

| 工具 | 路径 / 版本 |
| --- | --- |
| D2 | `D:\Tools\diagramming\d2\d2-v0.9.0\bin\d2.exe`，v0.9.0 |
| WaveDrom | `D:\Tools\diagramming\wavedrom\node_modules\wavedrom`，3.7.0 |
| JSON5 / ONML | 同一个外部 `node_modules`，2.2.3 / 2.1.0 |
| Node.js | 从 PATH 查找；本机为 `D:\Nodejs\node.exe` |

`mkdocs.yml` 的 `extra.diagrams` 定义工具根目录、布局、深浅主题及超时。`SMLCOKE_DIAGRAM_TOOLS` 环境变量可替换工具根目录；`D2_EXECUTABLE`、`NODE_EXECUTABLE` 可覆盖可执行文件路径。更换 D2 版本时同步调整调用路径及 MPE 的机器级 `d2Path`。

## requirements-web.txt

记录现有构建环境的兼容版本，供重建环境或修复依赖时使用，不是每次构建前的安装步骤：

```powershell
python -m pip install -r scripts/requirements-web.txt
python -m pip check
```

特别固定 Click 8.2.1：MkDocs 1.6.1 与 Click 8.3+ 配合时，普通 `mkdocs serve` 会默认关闭热重载。本机已修复为兼容版本，因此无需改变日常 serve 命令。上游问题见 [MkDocs #4032](https://github.com/mkdocs/mkdocs/issues/4032)。

## render_wavedrom.cjs

由 Python 钩子调用的 Node.js 辅助脚本。从标准输入读取 WaveJSON/JSON5，标准输出只返回 SVG；错误写标准错误并返回非零状态。

使用自带的 `default` / `dark` 皮肤，自动选择深浅色。当前接入对象是包含非空 `signal` 数组的数字时序图。无需每份图源指定皮肤，也不需要 PNG 渲染依赖。

独立调用示例（输出为 SVG 文本，通常交给构建钩子处理）：

```powershell
Get-Content -Raw -Encoding UTF8 docs/某篇文章/assets/timing.json5 |
    node scripts/render_wavedrom.cjs --modules D:/Tools/diagramming/wavedrom/node_modules --theme light
```

`--theme dark` 返回同一份波形的深色版本。不依赖仓库根目录中的 `node_modules`。

## test_mkdocs_diagrams.py

使用真实工具和临时最小 MkDocs 项目的集成测试，覆盖独立 SVG 引用、中文、嵌套代码块、代码示例不被误执行、D2 导入更新、单图宽度、布局/文件头优先级，以及无效参数和错误图源阻止构建。结束后自动清理临时目录。

```powershell
python scripts/test_mkdocs_diagrams.py
```

修改绘图钩子或升级工具后运行，日常写文章不必执行。

## webp_converter_safe.py（推荐）

手工运行的图片压缩与引用维护工具，依赖现有 `web` 环境中的 Pillow，不参与 MkDocs 构建。它是新增的独立脚本；旧版 `webp_converter.py` 保持不变。

先预览计划，再执行。以下相对路径均以当前工作目录为准，示例从仓库根目录运行：

```powershell
# 预览：不编码、不生成文件、不修改文档、不删除原图
python scripts/webp_converter_safe.py --path docs/microelectronics --quality 85 --dry-run

# 执行默认 warn 模式
python scripts/webp_converter_safe.py --path docs/microelectronics --quality 85

# 允许同步修改 docs 内其他目录的 Markdown，处理跨目录引用
python scripts/webp_converter_safe.py --path docs/microelectronics --remaining search-docs --quality 85

# 在默认安全目录之外，追加多个安全目录；重复参数也会累加
python scripts/webp_converter_safe.py --path docs --safe-dirs docs/lab docs/comments --safe-dirs docs/tools/writing --dry-run

# 文字截图等需要无损时使用；仍只保留比原图更小的转换结果
python scripts/webp_converter_safe.py --path docs/microelectronics --lossless

python scripts/webp_converter_safe.py --help
```

也可以直接调用环境解释器：

```powershell
& D:\Anaconda\envs\web\python.exe -X utf8 scripts/webp_converter_safe.py --path docs --dry-run
```

### 命令行参数

| 参数 | 默认值 | 实际行为 |
| --- | --- | --- |
| `--path PATH` | 必填 | 递归处理的目录，必须是本仓库 `docs/` 内已存在的文件夹。决定允许转换的图片范围；不会因为引用而扩大图片范围。 |
| `--quality N` | `85` | `0–100` 的整数。有损模式控制质量；`100` 也不代表无损。无损模式下控制压缩努力程度。 |
| `--remaining warn` | `warn` | 仅转换有本目录 Markdown 引用、且无需修改目录外 Markdown 的图片。跨目录引用、剩余图片只警告并保留。 |
| `--remaining search-docs` | — | 允许同步修改整个 `docs/` 中引用候选图片的 Markdown。也可处理仅被目录外 Markdown 引用的剩余图片；全站仍无 Markdown 引用时继续保留并警告。 |
| `--safe-dirs DIR [DIR ...]` | 不额外追加 | 一次传入多个安全目录，也可重复使用参数；与脚本顶部的默认安全目录取**并集**，不能取消默认保护。相对路径基于当前工作目录，必须位于 `docs/` 内；允许目录尚未创建。 |
| `--dry-run` | 关闭 | 只读取文件、检查条件并输出候选转换/链接修改计划。不会编码或写入；因此计划不保证实际压缩后更小，也不预估节省体积。 |
| `--lossless` | 关闭 | 使用无损 WebP，适合需要保留像素的截图。关闭时使用有损压缩；两种模式都要求转换结果比原图小。 |

### 安全文件夹

默认列表位于脚本头部，默认保护站点公共资源：

```python
DEFAULT_SAFE_DIRS = ["docs/assets"]
```

默认列表中的相对路径以**仓库根目录**为基准，不受运行位置影响；CLI 追加目录以当前工作目录为基准。两者解析为绝对路径后取并集。例如默认有 `docs/a`、`docs/b`，命令行再给出 `docs/c`，最终同时忽略这三个目录。

安全目录及其所有子目录中的图片直接忽略，不参与转换、链接改写或剩余图片警告，也不检查其中被引用但缺失的图片。保护按真实目录边界判断，`docs/a` 不会误伤 `docs/abc`。若 `--path` 本身就在安全目录内，脚本直接正常结束。例如默认配置下 `--path docs/assets` 不会处理任何图片；追加目录无法解除这一保护。

安全列表保护的是**图片**。为判断其他图片是否被共享，全站 Markdown 仍可能被只读扫描；`search-docs` 也可更新安全目录中的 Markdown 对安全目录外候选图片的引用。

### 扫描与处理顺序

1. 只读扫描全站 Markdown，建立引用清单。以 Markdown 所在目录解析本地相对路径，支持 `.png`、`.jpg`、`.jpeg`，扩展名不区分大小写。缺图警告包含文档路径、行号、原始链接和解析后的路径；链接保持不变。当前目录文章引用了 `--path` 外的图片时也只警告，不转换该图片。
2. 优先处理目标目录 Markdown 引用的图片。`warn` 遇到任何目录外 Markdown 引用时跳过整张图；`search-docs` 才同步改写这些引用。相同文件只编码一次，所有已识别引用一起改写。
3. 再检查目标目录剩余的 PNG/JPG/JPEG，包括被 Git 忽略、仅保存在本地的图片。仅被目录外 Markdown 引用时按上述模式处理；全站 Markdown 均未引用时**保留并警告，绝不转换或删除**。

链接支持普通 Markdown 图片、指向图片的普通链接、引用式/折叠式/简写式链接、HTML `<img src>`、`<a href>`、`<source src>`，以及嵌套的预览图/原图链接。支持平衡括号、Markdown 转义、URL 编码、中文、查询参数和锚点；含未编码空格的 Markdown 路径应使用 `<路径>` 包裹。只替换 URL 路径中的图片扩展名，保留标题、查询参数、锚点和其他文本。

远程网址、`data:` 图片、WebP/SVG/D2/JSON5 等不处理。代码围栏、行内代码、HTML 注释与 `<pre>/<code>/<textarea>` 中的示例不改写。缩进 Markdown 的语义可能依赖列表、提示框等上下文，本版保守地不改写缩进内容；若它疑似引用待转换图片，则整张图片跳过并警告。

对于尚未支持的引用形式（例如 `srcset`、YAML 元数据、站点根路径），以及 JS/CSS/HTML/JSON/YAML 中的可能引用，脚本会做候选文件名筛查；发现时**保留原图、跳过链接改写并警告**。检查范围包括 `docs/`、根目录 `mkdocs.yml` 和 `overrides/`；不会自动重写 JS/CSS 等源文件。筛查采用保守匹配，同名文件或正文中的文件名也可能触发警告；动态拼接的资源路径不保证能被发现，运行后仍需检查变更与预览。首页背景图由 JS 使用，默认安全目录可直接保护它们。

### 写入、重名与失败行为

- **已有同名 WebP 时，原图和全部链接都保持不变，输出 warning；没有强制覆盖选项。** 即使已有 WebP 内容无效，也不覆盖。两个源文件（例如 `a.png`、`a.jpg`）会产生同名输出时，两张都跳过。
- WebP 先编码到内存并重新解码验证尺寸/透明度；没有更小时保留原图和引用。支持常见 RGB、灰度、调色板和透明图片；处理 EXIF 方向并保留适用的 ICC 配置。多帧图、CMYK 等特殊模式以及非 RGB 图的 ICC 配置先警告跳过。
- 图片经同目录临时文件生成，再通过不覆盖目标的硬链接发布；即使运行过程中才出现同名 WebP，也会停止该图并警告。需要目标文件系统支持硬链接（本机 NTFS 支持）；不支持时报告错误并保留原图。
- 相关 Markdown 使用临时文件替换，保留 UTF-8 BOM、原有换行符和其他内容；写入前核对文档是否被其他程序修改。符号链接/Windows 目录联接不遍历，引用别名也不会被直接改写。
- **全部相关 Markdown 写入成功后，最后删除原图，不制作备份。** 编码或写入失败时保留原图；若部分文档已写入，则同时保留已发布的 WebP，确保新旧引用都有图片可用。此时需要人工查看差异，不会自动回滚或覆盖你的编辑；后续运行也会遵守“已有 WebP 不覆盖”。

输出使用 `PLAN`、`CONVERTED`、`WARNING`、`ERROR` 和 `SUMMARY` 标记，汇总转换/计划数量、改写文档数、节省字节数、各类跳过原因与错误数。退出码 `0` 表示正常结束（可以包含 warning）；`1` 表示实际读取、编码或写入失败；`2` 表示命令行参数无效。发生实际错误后停止后续处理。

### 测试

测试在系统临时目录构造独立 `docs/`，不会转换仓库中的图片：

```powershell
python -X utf8 -B scripts/test_webp_converter_safe.py
```

覆盖重名不覆盖、输出冲突、默认/追加安全目录并集、两种模式、跨目录共享引用、缺图、无引用图片保留、dry-run、链接语法与 BOM/换行保留、编码/部分写入失败、并发出现的 WebP、透明度、无损像素与 EXIF 方向。

## webp_converter.py（旧版，保留）

手工运行的位图维护工具，依赖 Pillow。它与绘图构建相互独立，构建时不会自动执行。

- 默认递归处理 `docs/self-cultivation/`，路径相对于脚本计算。
- 将 `.png`、`.jpg`、`.jpeg` 转为质量 85 的 WebP。
- 成功转换后**删除原始图片**。
- 批量改写该目录内 Markdown 图片和 HTML `<img src>` 中对应的扩展名。

建议使用上面的新版。旧版运行前需备份图片，并检查脚本顶部的 `DOCS_DIR`、`IMAGE_EXTS`、`WEBP_QUALITY`。

```powershell
python -m pip show Pillow
python scripts/webp_converter.py
```

同名不同扩展名图片可能产生输出重名；转换失败后也需核对链接。脚本用正则替换，不校验每个远程地址或转换结果；运行后检查文件差异及本地预览。不要用它处理 SVG。

用户操作手册见本地 `dev/runbooks/01-deploy.md`；机制说明见 `dev/reference/07-diagram-toolchain.md`。`dev/` 不受 Git 版本控制，需另行备份。
