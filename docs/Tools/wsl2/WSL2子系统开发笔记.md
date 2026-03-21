# WSL2 子系统开发笔记



## I. Linux基础

WSL2 环境：Ubuntu 22.04，无图形化界面

[系统目录结构、环境变量配置说明文档](./assets/文件系统目录.md)

WSL2 启动方式：`wsl -d Ubuntu-22.04`（或者 VSCode 直接连接）
WSL2 关断方式：`wsl --shutdown`

**WSL2 使用日志**：
- 2025-10-05：卸载snap，并设置了防止自动安装的偏好文件：`/etc/apt/preferences.d/nosnap.pref`
- 2025-10-05：安装了cmake 3.22.1
- 2025-10-05：配置了 SAT 工具: kissat。利用 github 源码编译。在根目录下。如需同步最新版本：`cd ~/kissat && cd build && make`

## II. python虚拟环境管理工具venv

**WSL2 使用日志**：
`miniconda` 配置在路径：`~/miniconda3/` 中，虚拟环境路径：`~/miniconda3/envs/`。
`conda` 启动方法：`source ~/miniconda3/etc/profile.d/conda.sh`
**配置步骤**：[venv 与 conda 配置方法文档](./assets/python虚拟环境.md)


## III. 代理

**WSL2 使用日志**：
  **配置方法步骤**：[代理配置方法文档](./assets/代理配置.md)


## IV. Yosys安装笔记

**WSL2 使用日志**：
从 GitHub 上克隆了 Yosys 源码，配置在 `~` 目录下，使用 `Clang` 进行编译，安装在系统级目录 `/usr/local/bin` 中。因此可以在任何位置直接使用 `yosys` 调用。
**配置方法步骤**：[Yosys 配置方法文档](./assets/yosys配置.md)

## V. Symbiyosys, boolector, z3 工具链配置笔记

**WSL2 使用日志**：
**2026-03-20** 配置了 Symbiyosys、boolector 和 z3 工具链。
- `Symbiyosys` 源码目录：`~`，安装到了系统路径``/usr/local/bin/``中。
- `boolector` 源码目录：`~`，编译安装可执行文件路径`~/boolector/build/bin/`，软链接到了系统路径`/usr/local/bin/`中。
- `z3` 源码目录：`~`，安装到了系统路径``/usr/local/bin/``中。

**配置方法步骤**：[Symbiyosys, boolector, z3 配置方法文档](./assets/symbiyosys配置.md)


注意，编译 `z3` 工具时，遇到了 `g++` 版本过低的问题(Ubuntu 22.04 默认 C++ 环境是 11)，解决方法是安装 `g++ 12` 环境。

如果后续想要将 `g++ 12` 设置为默认版本，可以使用 `update-alternatives` 工具进行管理：

```bash
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 120
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-12 120
sudo update-alternatives --config gcc
sudo update-alternatives --config g++
```