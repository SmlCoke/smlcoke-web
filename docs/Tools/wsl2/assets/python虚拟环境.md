# Python 虚拟环境

## I. 使用 venv 隔离环境（基础用法）

Python 的内置 `venv` 模块可以帮你创建 **项目独立的 Python 环境**。

假设在 `~/projects/demo` 里开发：

```bash
mkdir -p ~/projects/demo
cd ~/projects/demo

# 创建虚拟环境（名字随意，这里叫 venv）
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 激活后命令行前面会有 (venv) 提示
pip install requests  # 只安装到这个虚拟环境
```

退出虚拟环境：

```bash
deactivate
```

查看虚拟环境 Python 路径：

```bash
which python
```

会显示：

```
/home/你的用户名/projects/demo/venv/bin/python
```

这样不会影响系统的 `/usr/bin/python3`。

## II. 高级环境管理：conda（适合多版本 Python）

**miniconda3 用户级目录安装**

### 2.1 conda 是什么？

`conda` 是一个 **跨平台的包管理 + 环境管理工具**，不仅能管理 Python，**还能管理其他语言的工具包**（C/C++、R、Java 等）。
它最大的特点是：

1. **自带 Python 解释器**（环境是完全独立的）
2. **包安装不依赖系统 `apt`/`pip`**，而是从 `conda` 仓库下载预编译好的二进制包（安装速度快）。当然，在国内建议用 `pip` 安装，`conda` 源速度很慢
3. **依赖管理更稳定**，适合科学计算、大型项目


### 2.2 WSL 中安装 conda（推荐 Miniconda）

在 WSL 里不建议装 Anaconda（太大），推荐安装 **Miniconda**（精简版，自己装需要的包）。

```bash
# 下载 Miniconda 安装脚本（x86_64 版）
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# 运行安装脚本
bash Miniconda3-latest-Linux-x86_64.sh
```

安装时：

* 选择安装路径（默认是 `~/miniconda3`）
* 选择是否自动初始化 `conda`（建议选 `yes`）

如果你选了不自动初始化，可以手动加到 `~/.bashrc`：

```bash
export PATH="$HOME/miniconda3/bin:$PATH"
```

刷新环境变量：

```bash
source ~/.bashrc
```

验证：

```bash
conda --version
```


### 2.3 conda 的基本用法

**(1) 激活conda**
每次使用conda前，需要手动执行：
```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate myenv
```

之后的用法（虚拟环境、安装包等）与 `Anaconda` 操作完全一致。详见：[conda 使用方法](../../conda/conda.md)


### 2.4 conda 环境的位置

默认环境存放在：

```
~/miniconda3/envs/
```

每个环境都是独立的 Python + 包，不会互相污染，也不会影响系统 `/usr/bin/python3`。

