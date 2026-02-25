# Claude Code 使用日志

## I. 安装与环境配置

### 1.1 Node.js 环境
Claude Code 需要 Node.js 环境。
从[https://nodejs.org/zh-cn](https://nodejs.org/zh-cn)下载了 Windows 版本。
自动激活环境变量，命令行中可以使用 `npm`。

!!! note `npm`工具简介
    `npm` 是 Node.js 的包管理工具，可以用来安装、更新和管理 JavaScript 包和工具。它类似于 Python 的 `pip` 和 Rust 的 `cargo`，但专门用于 JavaScript 生态系统.

### 1.2 安装 Claude Code
在命令行中执行：
```bash
npm install -g claude-code --prefix = D:\claude-env
```
将`D:\claude-env`添加到环境变量中，命令行中可以直接使用 `claude-code` 命令。

### 1.3 环境配置
在国内无法使用 Claude 官方模型，但是可以在 Claude Code 中调用其他国内大模型的 API，例如 MiniMax-M2.5。
但是这里要设置一系列环境变量，以下：
```bash
$env:ANTHROPIC_BASE_URL="https://api.minimaxi.com/anthropic"
$env:ANTHROPIC_API_KEY=""
$env:ANTHROPIC_AUTH_TOKEN="<API Key>"
$env:ANTHROPIC_MODEL="MiniMax-M2.5"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL="MiniMax-M2.5"
$env:ANTHROPIC_DEFAULT_SONNET_MODEL="MiniMax-M2.5"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL="MiniMax-M2.5"
$env:CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1"
```

同时还要在 `C:\Users\YourUsername\.claude.json` 中添加：
```json
"hasCompletedOnboarding": true
```
写入 `"hasCompletedOnboarding": true` 后，Claude Code 启动时会**跳过 api.anthropic.com 的握手检测**，直接进入工作流状态。在工作流状态下，它就会老老实实地读取你设置的 `ANTHROPIC_BASE_URL`，把请求发给 `MiniMax`，从而完美实现国内大模型的接入。


## II. 使用笔记

### 2.1 基础功能

命令行输入
```bash
claude
``` 
进入交互界面

`shift + Tab` 切换输入模式：
- `? for shortcuts`：默认模式，每次创建/修改文件询问用户
- `Plan mode on`：规划模式，只讨论不修改，适合构思
- `accept edits on`：自动模式，自动修改文件

输入`!` 进入 `bash` 模式，可以直接执行命令行指令，例如 `ls`、`cat` 等。

* **换行输入**：在终端输入框中按 `Shift + Enter` 进行换行。
* **使用现代编辑器编写 Prompt**：按 `Ctrl + g`，Claude Code 会打开一个 VS Code 标签页。在里面编辑长篇需求后，保存并关闭标签页，内容会自动同步回终端输入框，按回车即可提交。

### 2.2 终端与后台任务管理

1. **后台挂起任务**：当让 Claude 运行阻塞型命令（如启动 `npm run dev` 服务器）时，按 `Ctrl + b` 可以将该服务置于后台运行，避免阻塞 Claude 的后续对话。
2. **任务管理**：输入 `/tasks` 可查看后台正在运行的任务列表。在查看界面按 `k` 键可以结束当前选中的服务。
3. **危险越权模式（高危但高效）**：
在启动时附带参数：`claude --dangerously-skip-permissions`
   * **效果**：跳过所有的终端操作权限检查（如创建文件夹、安装依赖、删除文件等均不再询问）。
   * **风险**：模型将拥有与你相同的完整终端控制权，仅建议在完全信任的项目环境中使用以提升全自动开发效率。



### 2.3 会话与上下文控制

1. **退出与恢复**：
   * 连按两下 `Ctrl + c` 退出 Claude Code。
   * 输入 `/resume` 会列出历史对话记录供选择恢复。
   * 或者直接使用 `claude -c` 启动，可自动恢复上一次的对话。
   * 对话的记录保存在`C:\Users\YourUsername\.claude\`目录下，以时间戳命名的文件中。


2. **回滚操作 (/rewind)**：连按两下 `Esc` 键或输入 `/rewind` 可进入回滚时间线，能够将代码和会话退回到之前的指定节点。
    > **注意**：Claude Code 的回滚**仅对它自己写入的文件生效**。如果是它通过执行终端命令（如 `mkdir` 或 `npm install`）生成的文件/目录，无法被自动撤销，需要手动删除。

3. **上下文管理**：
* `/compact`：压缩当前上下文中的冗余信息和调用日志，大幅节省后续操作的 Token 消耗。
* `/crtl + o`: 查看上下文
* `/clear`：**彻底清空当前会话的所有上下文记忆**.

### 2.4 外部工具集成 (MCP)

* **MCP (Model Context Protocol)**：大模型与外界深度沟通的桥梁：输入 `/mcp` 可以管理、安装和认证外部服务器（例如 Figma Server）。


### 2.5 项目配置与自动化

* **记忆预设 (CLAUDE.md)**：
  * **创建**：输入 `/init` 自动生成 `CLAUDE.md` 文件。
  * **编辑**：输入 `/memory` 快捷调出并编辑（分为当前项目级和全局用户级）。
  * **作用**：写在这里的内容（如项目架构说明、固定的代码风格要求、必定输出的后缀等）**每次启动都会被读取，充当隐式的 System Prompt。**


* **自动化钩子 (/hooks)**：
  * 输入 `/hooks` 进入配置。
  * 可在工具执行前/后触发自定义的本地脚本。
  * **实战应用**：设定在 Claude 执行 `Write/Edit` (修改代码) 操作之后，自动运行 `Prettier` 脚本来格式化代码文件，保证产出代码的排版美观。



### 2.6 高级代理与扩展能力

1. **Agent Skills 技能预设 (/skills)**：
  * 相当于给大模型看的一份“说明书”或动态 Prompt 模板。在 `~/.claude-skills/` 目录下创建 `skill.md` 进行配置（包含 Name、Description 和具体要求）。
  * **特点**：大模型会根据意图自动调用（或用户输入 `/技能名` 主动触发），**共享当前主对话的上下文**，适合处理常规工作流（如一键生成符合特定格式的每日代码总结）。


2. **Sub-agent 子代理 (/agent)**：
   * 输入 `/agent` 创建，可自定义模型、可用工具和执行准则。
   * **核心区别**：拥有**完全独立的上下文**。
   * **最佳场景**：代码审查 (Code Review) 等繁重任务。子代理在后台新开独立窗口默默看成千上万行代码，繁杂的中间分析过程不会撑爆你的主对话，它查完后只会把最终报告递交给你，主对话依然保持清爽。


3. **Plugin 插件系统 (/plugin)**：
   * 全家桶级别的能力扩展。输入 `/plugin` 进入插件市场。
   * 将**上述的 Skill、Hook、MCP、Sub-agent 打包在一起一键安装**（例如安装官方的 `front-end design` 插件，能瞬间赋予模型一套极为现代、高级的前端 UI 审美直觉）.


!!! warning "对比：Agent Skills VS Sub-agent"
    **Agent Skills：** **共享主对话上下文**，适合常规、轻量的工作流自动化。

    **Sub-agent**：**完全独立上下文**，适合复杂、资源密集型的任务（如代码审查），避免主对话被大量中间分析信息干扰。**避免浪费 Tokens !!!**