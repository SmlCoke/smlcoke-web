# 文件系统目录
## I. 系统级目录
```bash
g++ 
make 
clang 
python3 
pip3
graphviz
git
vim
```
## II. 用户级目录
```bash
miniconda3 
python3.11.4
```

## III. `usr/local/bin` 与 `/usr/bin`

### 3.1 系统级可执行程序目录`usr/loacl/bin`

- 存放 **系统管理员安装的可执行文件或脚本**，不属于系统自带软件包
- **所有用户**都可以直接在 shell 中调用这些程序

**常见内容**：
* 自己编译的工具（如 Yosys 源码安装）
* 脚本或二进制程序（例如 Python 虚拟环境里的命令可软链接到这里）

### 3.2 `/usr/bin`

- `/usr/bin`：系统自带或由包管理器安装的程序
- `/usr/local/bin`：管理员/用户手动安装的软件，优先级高于 `/usr/bin`（PATH 顺序中靠前）


### 3.3 `~/.bashrc`与环境变量


#### 1️⃣ `~/.bashrc`

**全称**：Bourne Again Shell Resource Configuration
**位置**：每个用户家目录下都有一个隐藏文件：`~/.bashrc`，例子：`/home/fj/.bashrc`
**作用**：

1. 每次打开一个 **交互式 Bash shell**（也就是终端窗口）时，都会自动执行这个文件里的命令。
2. 典型内容：
   * 设置 **环境变量**（比如 `PATH`、`PYTHONPATH`）
   * 配置命令别名（比如 `alias ll='ls -al'`）
   * 初始化工具（比如 `conda`、`pyenv`）

> 每个用户都有自己的 `.bashrc`，用户之间互相独立。root 用户有自己的 `/root/.bashrc`。


#### 2️⃣ `source` 命令

**作用**：让当前 shell 执行指定文件里的命令，而不是新开一个子 shell。

例子：

```bash
source ~/.bashrc
```

**效果就是：**
1. 立刻加载 `.bashrc` 里的所有配置，比如环境变量、别名等。
2. 对当前终端有效，不需要重新打开终端。

> 注意：直接运行 `.bashrc` 文件 `bash ~/.bashrc` 会开一个子 shell，环境变量不会影响当前 shell。

#### 3️⃣ 环境变量

**概念**：存储在内存中的一组键值对，用来影响程序的行为。
**常见用途**：
  * `PATH`：系统查找可执行程序的路径
  * `PYTHONPATH`：Python 查找模块的路径
  * `http_proxy` / `https_proxy`：网络代理配置

**查看所有环境变量**：
```bash
printenv
```

**设置环境变量**：

```bash
export MYVAR="hello"
```

!!! note 永久生效
    写入 `~/.bashrc`：

    ```bash
    echo 'export MYVAR="hello"' >> ~/.bashrc
    source ~/.bashrc
    ```

✅ **应用案例**

安装 `conda` 后执行：

```bash
source ~/miniconda3/etc/profile.d/conda.sh
```

就是把 `conda` 命令加载到当前 shell 的环境变量里。

想**每次开终端都自动加载** → 把上面这行写入 `~/.bashrc`。