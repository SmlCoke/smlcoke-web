# Rust 环境配置方法
> 针对 Windows 用户，使用 msys2 project 配置 Rust 环境的方法。

## I. MSYS2

MSYS2 是一个 Windows 上的类 Unix 环境，提供了一个包管理器 `pacman`，可以方便地安装各种开发工具和库。
安装 MSYS2 的方法很简单，直接访问官网 [https://www.msys2.org/](https://www.msys2.org/) 下载并安装即可。

## II. Rust 环境配置
以下操作在 `MSYS2-Clang64` 终端中进行：
```bash
export RUSTUP_HOME="/clang64/.rustup"
export CARGO_HOME="/clang64/.cargo"
mkdir -p /clang/.rustup
mkdir -p /clang/.cargo
curl https://sh.rustup.rs -sSf | sh -s -- -y --no-modify-path
```

然后在~/.bashrc中设置了：
```bash
export RUSTUP_HOME="/clang64/.rustup"
export CARGO_HOME="/clang64/.cargo"
export PATH="/clang64/.cargo/bin:$PATH"
```

.bashrc的目录在：`msys2/home/21035`