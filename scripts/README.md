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

使用真实工具和临时最小 MkDocs 项目的 10 项集成测试，覆盖独立 SVG 引用、中文、嵌套代码块、代码示例不被误执行、D2 导入更新、单图像素/百分比宽度，以及无效参数和错误图源阻止构建。结束后自动清理临时目录。

```powershell
python scripts/test_mkdocs_diagrams.py
```

修改绘图钩子或升级工具后运行，日常写文章不必执行。

## webp_converter.py

手工运行的位图维护工具，依赖 Pillow。它与绘图构建相互独立，构建时不会自动执行。

- 默认递归处理 `docs/self-cultivation/`，路径相对于脚本计算。
- 将 `.png`、`.jpg`、`.jpeg` 转为质量 85 的 WebP。
- 成功转换后**删除原始图片**。
- 批量改写该目录内 Markdown 图片和 HTML `<img src>` 中对应的扩展名。

运行前备份图片，检查脚本顶部的 `DOCS_DIR`、`IMAGE_EXTS`、`WEBP_QUALITY`。脚本没有命令行目录参数或 dry-run 模式：

```powershell
python -m pip show Pillow
python scripts/webp_converter.py
```

同名不同扩展名图片可能产生输出重名；转换失败后也需核对链接。脚本用正则替换，不校验每个远程地址或转换结果；运行后检查文件差异及本地预览。不要用它处理 SVG。

用户操作手册见本地 `dev/runbooks/01-deploy.md`；机制说明见 `dev/reference/07-diagram-toolchain.md`。`dev/` 不受 Git 版本控制，需另行备份。
