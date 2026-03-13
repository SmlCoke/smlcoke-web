# Windows 11 环境下 Docker 安装与数据迁移

## 一、Docker

1. **什么是 Docker？**
   Docker 可以被完美比喻为软件界的“**标准集装箱**”。在传统开发中，代码在 A 电脑上能跑，换到 B 电脑上可能因为系统版本、环境变量、依赖库不同而报错（所谓“依赖地狱”）。
   Docker 通过将代码、运行环境、依赖库打包成一个完全独立的“镜像（Image）”，确保它在任何电脑上运行时的内部环境绝对一致。
2. **为什么 Windows 上要用 Docker？**
   很多针对嵌入式、AI 芯片交叉编译的工具链（如 Ubuntu 20.04、特定的 GCC 版本）只能在 Linux 下运行。使用 Docker，我们可以在 Windows 电脑中瞬间启动一个配置完美的纯净 Linux 编译环境，且不会污染原本的 Windows 系统。
3. **Docker 与 WSL2 的关系**
   Docker 是一项基于 Linux 内核（Namespaces 和 Cgroups）的技术。为了在 Windows 11 上运行 Docker，**Docker Desktop 会在后台悄悄调用 Windows 的 WSL2（Windows Subsystem for Linux 2）虚拟机引擎**。在这个 WSL2 的微型 Linux 环境里，Docker 才能真正运作。


## 二、 Docker 的安装与迁移 D 盘步骤

> **前提条件**：Windows 11 系统已开启并安装好 WSL2 组件（此处略过 WSL2 安装步骤）。
> 这里顺便记录我首次配置安装时的相关 config

### 步骤 1：下载与初始安装
1. 去 Docker 官网下载 **Docker Desktop for Windows** 安装程序。
2. 双击运行安装，保持默认勾选 **“Use WSL 2 instead of Hyper-V”**（使用基于 WSL2 的引擎）。
3. 安装完成后，在开始菜单启动 Docker Desktop。
4. 接受用户协议，同时用 Goolge 账号登录，Docker 用户名：SmlCoke。
5. 等待主界面左下角显示绿色的 `Engine running`，这表示 Docker 已完成初始化。

### 步骤 2：彻底关闭 Docker
初始化完成后，必须彻底退出软件才能进行迁移：
**不要只点窗口右上角的 `X`**。在 Windows 右下角任务栏托盘中，找到 Docker 的小鲸鱼图标。
**右键点击 -> 选择 `Quit Docker Desktop`**，等待图标完全消失。

### 步骤 3：准备 D 盘目标文件夹
文件结构目录：
```text
D:\Docker
├── app     # 用于存放 Docker 自身的少量运行数据
└── data    # 用于存放未来的所有镜像、大模型等巨型数据
```

### 步骤 4：使用官方 GUI 工具“一键迁移”虚拟磁盘
较新版本的 Docker 提供了图形化界面的磁盘路径修改功能，比命令行更安全：
1. 重新打开 Docker Desktop，等待左下角变绿。
2. 点击右上角的 **⚙️ (齿轮图标)** 进入 Settings（设置）。
3. 在左侧菜单栏选择 **`Resources` (资源) -> `Advanced`**。
4. 找到 **"Disk image location"** 选项，点击旁边的 **`Browse`** 按钮。
5. 浏览并选择刚才建好的目录：`D:\Docker\data`。
6. 点击右下角的 **`Apply & restart`**。
   *(此时，Docker 会自动将原本在 C 盘的巨型 `.vhdx` 虚拟磁盘文件剪切并移动到 D 盘中)*。

### 步骤 5：验证
迁移并重启完成后，打开 Windows 的 PowerShell 终端，输入：
```powershell
docker run hello-world
```
如果终端成功去云端拉取了镜像，并最终打印出 `Hello from Docker!` 及相关成功提示，则证明安装与迁移大获成功！

## 三、 安装与迁移后的文件分布清单

**为什么把数据移到了 D 盘，C 盘还是少了 2~3 GB 空间？**
这是因为**程序的运行本体（起重机）必须在 C 盘，而数据仓库（集装箱）已经移到了 D 盘**。以下是具体的文件分布清单：

### 1. 留在 C 盘的文件（约 2~3 GB，正常现象，不可移动）
这些是维持 Docker 软件和图形界面运行的“本体”，**未来基本不会大幅度膨胀**：
*   **Docker 软件本体及执行文件**：
    `C:\Program Files\Docker\Docker\` (包含 Docker Desktop 的 `.exe` 和底层守护进程)
*   **用户的轻量级配置文件、日志与缓存**：
    `C:\Users\<用户名>\AppData\Local\Docker\`
    `C:\Users\<用户名>\AppData\Roaming\Docker\`
*   *(注：开启 WSL2 时，Windows 本身也会在 C 盘占用几百兆来维持 Linux 子系统的运转。)*

### 2. 迁移到 D 盘的文件（无底洞，核心迁移目标）
这里存放着 Docker 的“命根子”——虚拟磁盘文件。以后用 `docker pull` 拉取的几个 G 的交叉编译环境、训练数据集、转换出来的模型，**全部都会被“吸”进这两个 `.vhdx` 文件中，安全地在 D 盘膨胀，彻底解放 C 盘！**

以本次操作为例，完整的目录结构与文件分布如下：

```text
D:\Docker
│
├── app\  # (预留文件夹，部分版本的系统数据可导出至此)
│
└── data\ # (核心数据区，也是在 GUI 里指定的路径)
    └── DockerDesktopWSL\
        ├── disk\
        │   └── docker_data.vhdx  (约 1.5GB+) 👉 核心数据盘！所有的镜像(Image)和容器(Container)都在这里面！
        │
        └── main\
            └── ext4.vhdx         (约 100MB+) 👉 核心系统盘！存放了极少量的 WSL 发行版系统基础文件。
```

> **总结**：只要 `docker_data.vhdx` 老老实实待在 D 盘，就可以放心大胆地在 Docker 里折腾任何庞大的 AI 编译环境！

