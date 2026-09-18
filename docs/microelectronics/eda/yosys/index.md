# Yosys 配置笔记/记录

`Yosys` 是一个开源的数字综合工具，支持 Verilog HDL 的综合和优化。以下是从源码编译安装 Yosys 的详细步骤，以及相关的环境配置说明。

## I. Clang 工具介绍

* **Clang** 是 LLVM 项目的一部分，是一个现代 C/C++/Objective-C 编译器。
* **作用**：

  * 替代 GCC 编译 C/C++ 程序
  * 编译速度快，错误信息清晰
  * 与 Yosys 编译兼容性好，源码推荐使用 Clang

## II. 从源码编译安装 Yosys（系统级 `/usr/local/bin`）

### 3.1 步骤 A：安装编译依赖

在 WSL Ubuntu 22.04 下执行：

```bash
sudo apt update
sudo apt install -y build-essential clang bison flex \
    libreadline-dev gawk tcl-dev libffi-dev git \
    graphviz xdot pkg-config python3 libboost-system-dev \
    libboost-python-dev libboost-filesystem-dev zlib1g-dev
```

解释：

* `build-essential`：基础编译工具（gcc、make 等）
* `clang`：C/C++ 编译器
* `bison flex`：语法分析器工具，Yosys 源码需要
* `libreadline-dev gawk tcl-dev libffi-dev`：Yosys 依赖库
* `graphviz xdot`：可视化工具
* `libboost-*`：Boost 库
* `git`：克隆源码

### 3.2 步骤 B：克隆 Yosys 源码

```bash
cd ~
git clone --recurse-submodules https://github.com/YosysHQ/yosys.git
cd yosys
```

### 3.3 步骤 C：选择编译配置

推荐使用 Clang 编译：

```bash
make config-clang
```

如果想用 GCC，可以改为：

```bash
make config-gcc
```


### 3.4 步骤 D：编译 Yosys

```bash
make -j$(nproc)
```

* `-j$(nproc)` 会使用 CPU 所有核心并行编译，加快速度


### 3.5 步骤 E：系统级安装

```bash
sudo make install
```

* 会把 `yosys` 安装到 `/usr/local/bin`
* 系统中所有用户都可以直接使用 `yosys` 命令

### 3.6 步骤 F：验证安装

```bash
yosys -V
```

如果看到类似：

```
Yosys 0.xx (git sha1 ...) ...
```

说明安装成功。


💡 **小贴士**

1. 安装完成后，`/usr/local/bin` 默认在 PATH 中，直接运行 `yosys` 即可。
2. 如果需要更新 Yosys，只需在源码目录执行：

```bash
git pull
git submodule update --init --recursive
make clean
make -j$(nproc)
sudo make install
```





