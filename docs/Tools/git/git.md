# VCS Tool: Git & GitHub

## I. Git 与 GitHub 基础命令

> 涵盖 90% 的日常开发工作流

### 1.1 初始配置化
首次配置时记录好即可。
1. 配置用户名：`git config --global user.name "Your Name"`
2. 配置邮箱：`git config --global user.email "your.email@example.com"`
3. 查看当前配置：`git config --list`

### 1.2 日常工作流
#### 1.2.1 自建仓库版

1. 初始化仓库：`git init`
2. 在 GitHub 上创建一个新的空仓库，不要勾选 README、.gitignore 等选项。复制仓库 URL。
3. **关联远程仓库**：`git remote add origin <github-url>`
4. 添加文件：`git add <file>` 或 `git add .`（添加所有修改）
5. 提交修改：`git commit -m "Commit message"`
6. 首次推送：`git push -u origin main`，注意首次推送时要带上 `-u` 参数绑定分支。
7. 后续推送：`git push`
8. 拉取远程更新：`git pull`

#### 1.2.2 克隆仓库版
1. 克隆仓库：`git clone <github-url>`
2. 进入项目目录：`cd <repo-name>`
3. 添加/修改文件，提交并推送同上。

!!! tip 仓库推送权限
    如果该仓库是别人的仓库，想要提交修改需要先 Fork 到自己的 GitHub 账号下，然后克隆自己的 Fork 仓库，修改后推送到自己的仓库，再通过 GitHub 发起 Pull Request 给原仓库。
    如果该仓库是自己的仓库，直接克隆后修改提交推送即可。

### 1.3. 分支管理
1. 查看所有分支：`git branch` （带 `*` 的是当前分支）
2. 创建新分支：`git branch <branch-name>`
3. 切换分支：`git switch <branch-name>` （旧版使用 `git checkout <branch-name>`）
4. 创建并直接切换分支：`git switch -c <branch-name>`
5. 合并分支：`git merge <branch-name>` （将指定分支合并到**当前**分支）
6. 删除本地分支：`git branch -d <branch-name>`

!!! note 分支与推送/拉取
    `git push/pull`：默认操作当前分支，即将本地/远程的**当前分支**与**远程/本地对应分支**进行同步。
    `git push/pull origin <branch-name>`：操纵**指定分支** `<branch-name>`，即将本地/远程的 `<branch-name>` 分支与**远程/本地对应分支**进行同步。


## II. Git 与 GitHub 高级操作

> 在基础版之上，用于解决代码冲突、版本回退、历史重写及复杂项目管理。
> **待更新**

### 2.1 VS Code 集成终端

VS Code 中 **ctrl + `** 默认启动终端为：
- powershell（Windows）
- bash（Linux/Mac）

一般来说不建议直接在 powershell 中使用 git 命令，建议切换到 Git 工具安装时默认提供的 `GitBash`，在 VS Code 中点击 `+` 新建终端时可以选择 `GitBash` 打开，在`GitBash`中管理 Git 仓库。

GitBash 提供了更完整的 Git 命令支持和更友好的命令行体验（例如自带 `vim` 工具），尤其在处理复杂的 Git 操作时更为方便。

### 2.2 `.gitignore`

在使用 Git 管理项目时，通常会有一些文件或文件夹不希望被提交到版本库中，例如数据集、`.vscode/`、编译产物等。这时候就需要使用 `.gitignore` 文件来告诉 Git 哪些文件或目录应该被忽略。

直接新建 `.gitignore` 文件在其中写入不希望跟踪的文件/文件夹即可，支持正则匹配。

如果我们**不小心提交了某些文件进入版本库，后续又不想跟踪此文件**时，可以使用以下命令将其从版本库中移除：
1. **从版本库中移除文件**：`git rm --cached <file>`
2. 提交修改：`git commit -m "移除不需要跟踪的文件"`
3. 在`.gitignore`中添加该文件或文件夹的路径，确保后续不再被跟踪。
4. 推送修改

### 2.3 远程仓库变更

当远程仓库名字变更时，需要更新本地仓库的远程地址：
1. 查看当前远程仓库地址：`git remote -v`
2. **更新远程仓库地址**：`git remote set-url origin <new-github-url>`
3. 再次查看确认：`git remote -v`

### 2.4 大文件管理: LFS（Large File Storage）

在 Git 的世界里，纯文本代码的管理可以说是如鱼得水，但如果你的项目里包含了大型二进制文件（音视频 .mp4、压缩包 .zip、或者动辄几个 G 的机器学习数据集和模型文件），Git 就会变得极其臃肿和缓慢。

Git LFS 采用了一种“狸猫换太子”的策略：
它把真正的大文件**存在一个专门的 LFS 服务器上**。在你的本地 Git 仓库历史中，只保留一个体积不到 100 字节的**文本指针**。只有当你 `checkout` 到具体的某个分支/提交时，LFS 才会根据指针去下载那个特定版本的大文件实体。历史版本的庞大文件不再强制塞进每个人的电脑里。

使用 Git LFS 的步骤：
1. **安装 Git LFS**：`git lfs install`（一般来说，安装 Git 时会一并安装 LFS）
2. **跟踪大文件类型**：`git lfs track "*.mp4"`（以 mp4 为例，其他类型同理）
    
    !!! note 注意
        此行命令过后，Git 会在仓库根目录生成或修改一个 `.gitattributes` 文件，里面会增加这一句：
        `*.mp4 filter=lfs diff=lfs merge=lfs -text`
        `.gitattributes` 文件是 Git 中的属性配置文件，它告诉 Git 哪些文件要被特殊对待以及如何特殊对待。
3. **保存配置并提交**
   
   ```bash
   git add .gitattributes
   git commit -m "配置 LFS 追踪大文件"
   ```
4. **正常添加和提交大文件**
   
   ```bash
   git add video.mp4
   git commit -m "添加宣传视频"
   git push origin main
   ```

### 2.5 Huggingface Hub 集成

一般来说，即便有 lfs 工具帮助我们处理大文件，像机器学习数据集、模型参数文件也不建议直接放在 GitHub 仓库里。

**更推荐的做法是将这些大文件上传到 [Huggingface Hub](https://huggingface.co/) 这样的专门平台**上，而 `git` 工具作为一个通用的版本控制系统，可以直接 `clone` Huggingface 仓库以及推送提交。
例如：
1. `clone` Huggingface 模型仓库：
   `git clone https://huggingface.co/username/repo-name`
2. `clone` Huggingface 数据集仓库：
   `git clone https://huggingface.co/datasets/username/dataset-name`
3. 在本地修改后提交并推送到 Huggingface 仓库：
   
   ```bash
   git add .
   git commit -m "更新模型参数"
   git push origin main
   ```
   注意，这里推送时会涉及到 Huggingface 访问令牌，需要输入 Access Token 进行身份验证。

### 2.6 Tag
**Tag（标签）** 是 Git 中用于**标记特定提交**的工具，常用于标记版本发布点。Tag 可以分为两种类型：轻量级标签（lightweight tag）和附注标签（annotated tag）。轻量级标签只是一个指向特定提交的指针，而附注标签则包含了更多的信息，如作者、日期和标签信息。

使用 annotated tag 可以很方便的管理版本发布，其他用户很容易看出当前版本的关键版本信息，方便下载对应版本的代码。

发布 tag 的方式如下：
1. **确保与远程仓库同步**
2. **创建 tag**
   - Method 1: `git tag v1.0`，这是创建一个轻量级标签
   - Method 2: `git tag -a v1.0 -m "Release version 1.0"`，这里 `-a` 表示创建一个附注标签，`-m` 后面跟的是标签信息
   - Method 3: `git tag -a v1.0 `，在 `GitBash` 中执行后默认进入 `vim` 编辑器，在其中输入标签信息，`ESC + :wq`保存退出即可。
3. **推送 tag 到远程仓库**：`git push origin v1.0`，之后即可在 GitHub 仓库的 `tags` 页面看到这个版本标签。

!!! tip tag的命名方式
    一般来说，tag 的命名方式会遵循语义化版本控制（Semantic Versioning）的规范，例如 `v1.0.0`、`v2.1.3` 等，这样可以清晰地表达版本之间的关系和更新内容。`vx.y.z` 中，修改 `z` 表示小修小补的 **bug 修复**，修改 `y` 表示**增加了新功能**但不破坏兼容性，修改 `x` 则表示**有重大更新可能会破坏兼容性**。
    此外，也可以根据项目需求使用其他命名方式，但建议保持一致性和可读性。尤其是要写好**标签信息**。

### 2.7 版本回退

#### 2.7.0 撤回暂存区
有时候我们不小心 `git add` 了某些文件到暂存区，但又不想提交它们了，这时候可以使用以下命令将它们从暂存区撤回：
```bash
git reset <file>
```

如果想要撤回所有文件，可以使用：
```bash
git reset
```

#### 2.7.1 回到上一个 commit

有时候我们 commit 了一个版本后，又做了一些修改，然后发现当前修改把项目改坏了，想要强制恢复到上一个commit版本，完全舍弃当前所有修改，可以这样做：

**(1) 抹除所有以追踪的文件的修改（包括add到暂存区的）**
```bash
git reset --hard HEAD
```
`HEAD` 代表当前分支的最后一次 `commit`。`--hard` 是一个威力巨大的参数，它会**强行把工作区和暂存区全部拉回 `HEAD` 的状态**，刚才写坏的代码会瞬间**灰飞烟灭**。

**(2) 清理所有未追踪的新文件/新文件夹（可选）**
如果在改废代码的过程中，还新建了一些文件或文件夹（这些文件还没被 Git 追踪过），上面的 `reset` 是管不到它们的。还需要加一条：
```bash
git clean -fd
```
`-f` 表示强制删除，`-d` 表示同时删除未追踪的文件夹。

执行完这两部，当前分支就完全回退到上一个 `commit` 的状态了，之前的修改和新建的文件都不见了。

!!! warning 警告
      这个操作非常危险，`reset --hard` 和 `clean -fd` 属于 Git 中少有的不可逆操作！
      一旦敲下回车，改坏的那些代码将**永远从硬盘上消失**，连 Git 也救不回来（因为**它们根本还没进入 Git 的版本库**）<br>
      所以无论当前的修改是否真的损坏了项目代码，都建议在执行此命令前将当前整个仓库备份一下，这是绝对稳妥的保底策略。<br>
      Git 最大的设计哲学之一就是“**去中心化**”和“**一切皆在本地**”。项目里的所有历史版本、分支信息、甚至与 GitHub 的远程绑定关系（origin），都在项目根目录下一个名为 .git 的隐藏文件夹里。当我们连同这个 `.git/` 文件夹一起复制时，我们**不仅复制了代码，还原封不动地复制了整个 Git 数据库**。只要 `.git/`还在，就算整个仓库的代码被扬了，Git 也能救回来，这就是 Git 带来的强大安心感。