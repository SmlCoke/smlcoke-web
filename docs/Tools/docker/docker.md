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

## 四、Docker 的使用

两个关键点：
1. Docker 的一切拉取镜像、运行容器等数据操作全部在 `docker_data.vhdx` 里进行，**这个文件就是 Docker 的“数据仓库”**。
2. 运行 Docker 时，必须保持 Docker Desktop 的主界面左下角显示绿色的 `Engine running`，**这表示 Docker 的引擎正在正常运行**。

### 4.1 Demo

- 验证安装/显示版本号：`docker --version`
- 测试镜像：`docker run hello-world`

#### 镜像与容器
1. 镜像(Image)：镜像是一个静态的、只读的模板，包含了运行某个应用所需的代码、库、环境变量等。就像一个预先打包好的“软件安装包”。
2. 容器(Container)：容器是镜像的一个运行实例，是一个动态的、可读写的环境。当你运行一个镜像时，Docker 会创建一个容器来执行这个镜像中的应用。容器是隔离的，互相之间不会干扰，就像在不同的“沙箱”里运行一样。

### 4.2 常用命令

#### 4.2.1 与镜像有关的指令


**(1) 拉取镜像**
```bash
docker pull <registry>/<namespace>/<image>:<tag>
```

- `registry`：镜像仓库地址（如 Docker Hub、阿里云等），`docker.io` 是默认的 Docker Hub。
- `namespace`：镜像的命名空间，通常是用户名或组织名。`library` 是 Docker Hub 的官方镜像命名空间。其他用户上传的镜像会在自己的命名空间下，如 `SmlCoke`。
- `image`：镜像名称。
- `tag`：镜像标签，用于区分同一镜像的不同版本。

!!! tip "可选参数"
    (1) `--platform`：指定平台架构，如 `linux/amd64`、`linux/arm64` 等，确保拉取与当前系统兼容的镜像。应用场景：嵌入式开发设备


**(2) 列出本地镜像**
```bash
docker images
```

**(3) 删除镜像**
```bash
docker rmi <image_id>
```

#### 4.2.2 与容器有关的指令
**(1) 运行容器**
带有最常用参数的运行指令如下：
```bash
docker run -d -p <host_port>:<container_port> -v <host_path>:<container_path> --name <container_name> <image_name>
```

- `-d`：detach mode, 后台运行容器。
- `-p`：端口映射，将容器内的 `<container_port>` 映射到主机的 `<host_port>`。
- `-v`：卷挂载，将主机的 `<host_path>` 挂载到容器内的 `<container_path>`，实现数据持久化。
- `--name`：为容器指定一个名字，方便管理和识别。注意，容器名称必须唯一。
- `<image_name>`：要运行的镜像名称，可以带标签，如 `myapp:latest`。

**什么是端口映射？**
端口映射是将容器内部的端口映射到主机的端口，使得外部可以通过主机的端口访问容器内部的服务。
例如，`-p 8080:80` 表示将容器内的 80 端口映射到主机的 8080 端口，这样访问 `http://localhost:8080` **就相当于访问容器内的 80 端口。**

**什么是卷挂载？**
卷挂载是将主机的目录或文件挂载到容器内，使得容器内的应用可以直接访问主机上的数据。
例如，`-v D:\data:/app/data` 表示将主机的 `D:\data` 目录挂载到容器内的 `/app/data` 目录，这样容器内的应用就可以访问 `D:\data` 中的数据。

!!! note "相对路径与绝对路径"
    在使用 `-v` 参数时，可以使用相对路径或绝对路径。相对路径是**相对于 Docker 命令执行目录的路径**，而绝对路径是完整的文件系统路径。

**(2) 列出容器**
列出正在运行的容器：
```bash
docker ps
```

列出所有容器（包括未运行的）：
```bash
docker ps -a
```

**(3) 停止与启动容器**
停止容器：
```bash
docker stop <container_id>
```

启动容器：
```bash
docker start <container_id>
```

注意，停止然后再次启动后，**之前启动时设定的可选参数仍然有效**。

**(4) 删除容器**
```bash
docker rm <container_id>
```


**(5) 运行交互式容器**

```bash
docker run -it ubuntu bash
```
- `-i`: 交互式模式（Interactive）。
- `-t`: 分配一个伪终端（TTY）。
- `ubuntu`: 使用 Ubuntu 官方镜像。
- `bash`: 进入容器后执行的命令。

## 4.3 进阶命令

### 4.3.1 进入正在后台运行的容器
```bash
docker exec -it <container_id> bash
```

> 注：如果镜像里没有 bash，可以尝试换成 sh

### 4.3.2 查看容器日志
如果你的代码在容器里崩溃了，或者你想看 Web 服务器的访问记录，看日志是第一步。
```bash
# 打印历史日志
docker logs my-nginx

# 持续滚动查看日志（类似 Linux 的 tail -f）
docker logs -f my-nginx
```

### 4.3.3 “永不宕机”
```bash
docker run -d --name <container_name> --restart always <image_name>
```

- `--restart always` 参数会让 Docker 在容器崩溃或 Docker 重启后自动重新启动容器，确保你的服务始终在线。

### 4.3.4 空间清理
使用 Docker 一段时间后，你会发现下载了较多的镜像、生成了无数停止的容器，宿主机磁盘空间减少。Docker 提供了一键清理功能：
```bash
# 清理所有停止的容器、无用的网络和悬空镜像 (安全操作)
docker system prune

# 终极清理：不仅清理上述内容，还会把你下载的、当前没有被任何容器使用的镜像统统删掉！
docker system prune -a
```