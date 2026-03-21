# Symbiyosys, boolector, z3 工具链配置笔记

## I. 配置 Symbiyosys 

`sby` 本质上是 Yosys formal flow 的前端驱动程序；它会调用后端的 SMT 求解器（如 boolector、z3）来执行形式验证任务。

通过**源码配置方法**：

### 1.1 安装基础依赖
```bash
sudo apt update
sudo apt install -y python3 python3-pip git make
```

### 1.2 克隆 Symbiyosys 仓库并安装
```bash
cd ~
git clone https://github.com/YosysHQ/sby.git
cd sby
sudo make install
```

此后，`sby` 工具应该会被安装到系统路径`usr/local/bin/`中，可以直接在终端使用。

### 1.3 检测安装是否成功：
```bash
which sby
# 应该输出: /usr/local/bin/sby

sby --version
# 应该输出类似于: sby X.Y.Z ...
```

## II. 配置 boolector (SMT 求解器) 

### 2.1 安装编译依赖
```bash
sudo apt update
sudo apt install -y build-essential cmake git python3 curl
```

### 2.2 克隆 boolector 仓库并编译安装
```bash
cd ~
git clone https://github.com/Boolector/boolector.git
cd boolector
```

### 2.3 准备依赖
最常见的是配 `btor2tools` + `CaDiCaL`。
```bash
./contrib/setup-btor2tools.sh
./contrib/setup-cadical.sh
```

### 2.4 编译并安装 boolector
```bash
./configure.sh
cd build
make -j"$(nproc)"
```

编译完成后，可执行文件在：
```bash
~/boolector/build/bin/boolector
```


### 2.5 将 boolector 添加到系统路径
直接软链接到 `/usr/local/bin/` 后，就可以在任何地方直接使用 `boolector` 命令了：
```bash
sudo ln -sf ~/dev/boolector/build/bin/boolector /usr/local/bin/boolector
hash -r
```

### 2.6 验证安装
```bash
which boolector
boolector --version
type -a boolector
```
因为 `/usr/local/bin` 通常比 `/usr/bin` 优先，所以这能保证系统优先用源码版。

## III. 配置 z3 (SMT 求解器)

### 3.1 安装编译依赖
```bash
sudo apt update
sudo apt install -y build-essential python3 git
```

### 3.2 克隆 z3 仓库并编译安装
```bash
cd ~
git clone https://github.com/Z3Prover/z3.git
cd z3
```

### 3.3 用官方推荐脚本生成 Makefile 并编译

#### 3.3.1 默认编译命令
```bash
python3 scripts/mk_make.py --prefix=/usr/local
cd build
make -j"$(nproc)"
sudo make install
```

注意：Z3 当前源码用了 C++20 的 `<format>`，而 Ubuntu 22.04 默认常见的 g++ 11 / libstdc++ 11 对这个头支持不完整，所以如果直接编译，会报 `fatal error: format: No such file or directory`。

#### 3.3.2 修复办法
**安装 g++ 12 环境**：
```bash
sudo apt update
sudo apt install -y gcc-12 g++-12 libstdc++-12-dev
```

**重新编译**
注意先得清楚默认安装产生的 build 目录，删除它重新生成 Makefile：
```bash
cd ~/z3
rm -rf build
python3 scripts/mk_make.py --prefix=/usr/local
cd build
make CXX=g++-12 CC=gcc-12 -j"$(nproc)"
sudo make install
```

这会把可执行文件安装到 `/usr/local/bin/z3`，库安装到 `/usr/local/lib`。官方说明里写得很清楚：默认会把 z3 装到 `PREFIX/bin`，库到 `PREFIX/lib`，头文件到 `PREFIX/include`；`--prefix=` 可以改安装前缀。

### 3.4 验证安装
```bash
which z3
z3 --version
readlink -f "$(which z3)"
```
