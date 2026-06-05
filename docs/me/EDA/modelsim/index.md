# Modelsim 使用笔记

## I. ModelSim 简介

### 1.1 Modelsim 是用什么语言编写的？

*   **仿真内核（底层计算部分）**：**C/C++**。由于仿真本质上是极大规模的并发计算，为了追求极致的执行速度和内存管理效率，工业级的仿真器内核（包括 ModelSim、VCS、Xcelium）都是用 C/C++ 编写的。
*   **交互界面与脚本引擎**：**Tcl/Tk (Tool Command Language)**。。ModelSim 的 GUI 界面是用 Tcl/Tk 画出来的，它所有的用户交互动作（如点击按钮、拖拽波形）最终都会被翻译成 Tcl 命令送给底层。
*   **扩展接口（DPI/PLI/VPI）**：ModelSim 支持使用 C/C++ 编写扩展函数，直接与 Verilog/SystemVerilog 交互，这在工业界的复杂 Testbench（如涉及底层驱动、参考模型 C Model 时）非常常见。

### 1.2 ModelSim 的工具组成（执行流拆解）

`iverilog` 是一步到位生成一个可执行文件（比如用 `vvp` 跑）。ModelSim 的工作流更贴近真实的编译原理，它由几个独立的可执行程序组成，分布在其安装目录的 `bin` 文件夹下：

1.  **`vlib` (Library Management)**：用于**创建库**。在 ModelSim 中，所有编译后的中间文件必须放在一个“逻辑库”中（最常用的是默认库 `work`）。
2.  **`vmap` (Library Mapping)**：用于**映射库**。将逻辑库名称映射到物理目录，常用于关联厂商提供的底层元件库（比如你想在 ModelSim 里仿真 Xilinx 的 IP，就需要用到这个）。
3.  **`vlog` (Verilog/SystemVerilog Compiler)**：**编译器**。把你写的 `.v` 或 `.sv` 源代码编译成 ModelSim 自定义的二进制中间格式，存入 `work` 库中。
4.  **`vcom` (VHDL Compiler)**：同理，用于编译 VHDL 文件。（ModelSim 是工业界最早也是最优秀的混合语言仿真器之一）。
5.  **`vsim` (Simulator)**：**仿真器内核**。这是 ModelSim 的灵魂。它负责加载编译好的设计库，建立仿真拓扑结构，然后随着时间推移执行仿真。GUI 界面也是由 `vsim` 启动的。

### 1.3 底层运作方式：它是如何工作的？

当你调用这些工具时，ModelSim 实际上在后台经历了三个核心阶段：

**(1) 阶段一：编译（Compilation - `vlog`）**
ModelSim 并不是解释型执行的脚本语言，而是**编译型仿真器**。`vlog` 会对你的 Verilog 代码进行词法分析、语法分析，并将其转换为一种**中间表示（Intermediate Representation, IR）**（机器码级别的二进制文件）。这个过程会进行很多语法层面的死代码消除和逻辑优化。

**(2) 阶段二：细化 / 展开（Elaboration - `vsim` 启动时）**
当你输入 `vsim work.tb_top` 时，仿真器开始工作。在真正跑出波形前，它会先做一件大事：**Elaboration**。

*   它会从顶层模块（`tb_top`）开始，递归地把所有例化的子模块（比如你的 RV32I ALU、Register File、Control Unit）像展开一棵大树一样在内存里建立起**层次化的数据结构**。
*   它会计算所有的 `defparam`（参数传递），解析模块间的连线（wire/logic）。
*   最终生成一个巨大的、扁平化的仿真拓扑网络。

**(3) 阶段三：事件驱动仿真（Event-Driven Simulation - `vsim` 运行时）**

这是 ModelSim 运作的底层数学模型。它内部维护着一个 **“时间轮”（Time Wheel）** 或叫事件队列。

1.  **事件（Event）**：某根线（信号）的值从 0 变 1，就是一个事件。
2.  **触发（Trigger）**：这个事件发生后，会触发所有对这个信号敏感的 `always` 块。
3.  **调度（Scheduling）**：ModelSim 的内核会在当前时间点（Current Time）计算这些 `always` 块里的逻辑结果。如果是阻塞赋值（`=`），立刻更新；如果是非阻塞赋值（`<=`），它会把更新结果打包成一个新的事件，挂在当前时间步的末尾（NBA Region，非阻塞赋值区）。
4.  **时间推进（Time Advance）**：当当前时间点的所有事件都被处理完毕，且没有新事件产生时，ModelSim 就会转动“时间轮”，把虚拟仿真时间往前推移，直到遇到下一个有事件的时间点。

### 1.4 核心功能

*   **多层次调试能力**：不仅仅是看波形（像 gtkwave 那样），它还能直接在源代码里打断点（Breakpoints）、单步执行（Step Over/Into）、查看当前时刻各个寄存器/存储器阵列（Memory）的内部数据。
*   **代码覆盖率（Coverage）**：它可以统计你的 Testbench 跑完后，你的 CPU RTL 代码里有多少行（Statement）、多少分支（Branch，比如 `if-else`）、多少条件（Condition）、甚至多少信号跳变（Toggle）是被真正触发过的。这是工业界判断验证是否完成的硬指标。
*   **高效率的命令行（CLI）模式**：不需要消耗内存去画波形图，纯跑数据，验证效率极高（通常使用 `vsim -c` 参数进入）。

---

## II. Quick Start Guideline

### 2.1 Debug Mode: Open GUI

在工业界，虽然每天的常态是用脚本在后台批量跑数以千计的测试用例（Regression Test），但一旦某个测试用例报错，工程师就会立刻打开 GUI 界面进行深度调试（Debug）。
因此，工业界使用 ModelSim GUI 的核心目的不是“为了运行而运行”，而是 **“为了找 Bug”**。例如 RV32I CPU RTL 如果遇到某条指令执行结果不对，利用 GUI 的高阶调试功能将比你干瞪眼看代码或到处加 $display 打印高效百倍。
以下以 RV32I CPU 的 Testbench 为例，演示一下 ModelSim GUI 的基本使用流程和工业级调试细节：

#### Step 1: 创建工程与工作区 (Create Project)
在工业界，规范的文件管理是第一步。

1. **打开软件**：启动 ModelSim。
2. **新建工程**：点击菜单栏 `File` → `New` → `Project...`。
3. **配置参数**：
    * **Project Name**：起个名字，比如 `rv32i_cpu_sim`。
    * **Project Location**：选择你的工作目录。
    * **Default Library Name**：保持默认的 `work` 即可。（这就对应了我上文提到的 `vlib work` 动作）。
4. 点击 OK 后，ModelSim 的左侧窗口会从 `Library` 标签页自动切换到 `Project` 标签页。

#### Step 2: 添加源文件与编译 (Add Files & Compile)

1. **添加代码**：在弹出的窗口选择 `Add Existing File`，把所有 `.v`/`.sv` 文件以及 Testbench 文件添加进来。
2. **执行编译**：
    * 在左侧 Project 窗口中，你可以看到所有文件旁边都有一个蓝色的问号（表示未编译）。
    * 点击菜单栏 `Compile` → `Compile All`（或者右键点击空白处选 Compile All）。
3. **检查结果**：
    * 成功：文件旁边的图标会变成**绿色的对号**。
    * 失败：变成**红色的叉号**。此时你需要看底部最大的 **Transcript 窗口**（控制台窗口），双击红色的报错信息，ModelSim 会自动打开内置的代码编辑器并高亮标出语法错误的行。

#### Step 3: 启动仿真与实例化 (Start Simulation)
这里是关键，你要告诉 ModelSim 哪一个是你的顶层 Testbench。

1. 点击菜单栏 `Simulate` → `Start Simulation...`。
2. 在弹出的窗口中，展开 `work` 库。
3. 找到你的顶层 Testbench 模块（比如叫 `tb_top`），选中它。
4. **【避坑警告/工业级细节】**：在该窗口的 `Optimization Options` 中，**请务必注意是否开启了优化（Enable optimization）**。
    * 现代的 ModelSim/QuestaSim 默认会开启高强度优化，为了追求速度，它会把设计中没有对外输出的中间信号（比如你 CPU 内部的 ALU 中间节点）全部“优化掉”，导致你在波形里看不到这些信号。
    * **调试阶段**，建议点击 `Optimization Options`，取消勾选优化，或者在某些版本中勾选 “Apply full visibility to all modules”（确保所有信号可见）。
5. 点击 `OK`，ModelSim 会进入**仿真模式（Simulate Mode）**。此时界面的窗口布局会发生巨大变化，出现 `sim`（拓扑结构树）和 `Objects`（当前模块下的所有信号）窗口。

#### Step 4: 配置波形窗口 (Configure Waveform)

1. **调出波形窗口**：如果没看到 Wave 窗口，点击菜单栏 `View` → `Wave`。
2. **添加信号**：
    * 在 `sim` 窗口（Instance 树）中，点击你的顶层或内部模块（比如 `tb_top` → `u_rv32i_core`）。
    * 此时 `Objects` 窗口会显示该模块下所有的线网（wire）和寄存器（reg）。
    * 选中你关心的信号（如 `clk`, `rst_n`, `pc`, `instr`, `alu_out`），右键 → `Add to` → `Wave` → `Selected Signals`。（或者直接把信号拖拽进 Wave 窗口）。
3. **整理波形（让它看起来像工程师的波形）**：
    * **加分割线**：在 Wave 窗口左侧信号列表空白处右键 → `Add Divider`，可以给信号分类，比如命名为 "Control Signals", "Datapath", "RegFile"。
    * **改进制 (Radix)**：CPU 里的 PC 和指令通常看十六进制更直观。选中信号，右键 → `Radix` → 选择 `Hexadecimal`。有些状态机的状态可以设置为 `ASCII` 或自定义的枚举名。

#### Step 5: 运行与观察 (Run Simulation)
在软件顶部的工具栏，有几个控制仿真的按钮：

1. **Run 100ns**：点击一次，仿真时间往前推进你设定的步长（默认通常是 100ns）。可以用来一步步看时钟翻转。
2. **Run -all**：一直运行仿真，直到 Testbench 中遇到 `$finish` 或者你手动点击红色的 **Stop** 按钮。（在 CPU 测试集验证中，通常是点击这个）。
3. **波形缩放**：运行后，Wave 窗口会画出波形。使用键盘的 `I` (Zoom In) 和 `O` (Zoom Out)，或者点击工具栏的放大镜图标，按 `F` 键（Zoom Full）看全局。此时你就可以对照着时钟沿，看 PC 值和指令数据对不对了。

#### Step 6: 工业级进阶调试功能 (Advanced Debugging - 核心亮点)
这也是 ModelSim 远超 gtkwave 的地方，对于 Debug 极度有用：

1. **源码断点调试 (Source Debug)**：
    * 在 `sim` 窗口双击某个模块，打开 Source 窗口（Verilog 代码）。
    * 在某行代码（比如 `always` 块里某个 `if` 分支）左侧的行号处点击一下，会出现一个红点（断点）。
    * 点击 `Run -all`，当仿真执行到这行代码时，整个仿真会暂停。你可以像调试 C 语言（GDB/VS Code）一样，查看此时刻各个变量的值，甚至用 `Step` 按钮单步执行代码！
2. **追线神器 (Dataflow Window)**：
    * 你发现 CPU 跑着跑着，`alu_result` 突然变成了红色的 `X`（未知态）。
    * 在 Wave 窗口选中这个变 `X` 的信号，右键 → `Explore` → `Dataflow`。
    * ModelSim 会弹出一个类似电路图的窗口，自动把你选中的信号作为中心，左边画出是哪些寄存器/逻辑门驱动了它（Drivers），右边画出它又连到了哪里（Receivers）。顺藤摸瓜，秒定位是哪根线没接好或逻辑写错。
3. **内存/寄存器查看器 (Memory Window)**：
    * 例如 RV32I CPU 有 32 个通用寄存器（RegFile）和指令/数据存储器（SRAM）。
    * 菜单栏 `View` → `Memory List`。双击你的寄存器数组实例。
    * 会弹出一个矩阵表格，实时显示每个地址里存的数据。不用把 32 个寄存器全拉到波形里，直接在这个表里看，哪条指令写错了寄存器一目了然。

#### Step 7: 保存现场 (Save Format)
你辛辛苦苦添加了几十个信号，分好了组，改好了十六进制。如果关掉软件，下次再跑又要重来一次，太痛苦了。

1. 在 Wave 窗口中，点击菜单栏 `File` → `Save Format...`。
2. 保存为一个 `.do` 文件（例如 `wave.do`）。
3. 下次你重新启动仿真时，只需要在底部 Transcript 命令行输入 `do wave.do`，你精心排版的所有波形信号就会瞬间恢复。


!!! success "GUI 流程总结"
    工程创建 → `Compile All` (查语法 Bug) → `Start Simulation` (查拓扑 Bug) → 拖拽信号 → `Run` → `Debug (波形/断点/追线)` → 修复代码重来 → 保存 `wave.do`。

--- 

### 2.2 Batch Mode: Run CLI

在工业界的日常开发中，尤其是面对 CPU 这种包含成百上千个测试集（ISA Tests）的项目，工程师不可能每次都打开 GUI 界面去点击鼠标编译、运行。他们通常会使用 **“脚本化（Script-based）工作流”**——即在终端后台静默、高速地完成仿真，只输出一份 Pass/Fail 的报告，或者在出错时生成波形文件供事后查看。

以下是 ModelSim CLI 模式的基本流程和核心概念：

#### 2.2.1 核心概念：GUI 操作的底层其实都是命令

在 ModelSim GUI 界面里所有的鼠标点击（新建工程、编译、启动仿真、Run），最终都被翻译成了 **Tcl (Tool Command Language)** 命令，并输出在了底部那个 Transcript 控制台里。

CLI 模式的本质，就是**跳过鼠标点击，直接在操作系统的终端（Terminal/CMD/PowerShell）里敲入这些底层命令，或者把命令写成一个脚本让工具批量执行**。

#### 2.2.2 CLI 模式下的核心命令拆解

与 `iverilog` + `vvp` 类似，ModelSim 在命令行下有一套严格对应的三步曲命令（这些执行文件都在 ModelSim 的 `bin` 目录下）：

##### Step 1. 建库 (对应 GUI 的 Create Project)

```bash
vlib work
```

*作用*：在当前目录下生成一个名为 `work` 的文件夹，作为默认的编译库。

##### Step 2. 编译 (对应 GUI 的 Compile)

```bash
vlog -sv -work work ../src/*.v ../tb/riscv_soc_tb.sv
```

*作用*：调用编译器 `vlog`。`-sv` 表示支持 SystemVerilog 语法，`-work work` 表示编译到刚刚创建的 work 库里。后面跟着的是你所有的源代码和 Testbench 路径。

##### Step 3. 仿真与运行 (对应 GUI 的 Start Simulation + Run)

```bash
vsim -c work.riscv_soc_tb -do "run -all; quit"
```

*作用*：这是最核心的一句。

*   **`-c` (Crucial Parameter!)**：这个参数告诉 ModelSim **“不要启动 GUI 界面”**，直接在命令行（Console）模式下运行。这就是 CLI 的灵魂。
*   `work.riscv_soc_tb`：告诉仿真器顶层模块是谁。
*   `-do "run -all; quit"`：执行 Tcl 命令。跑完所有测试（直到遇到 `$finish`），然后立刻退出仿真器。

#### 2.2.3 工业界标准做法：使用 `.do` / `.tcl` 脚本
虽然可以直接在终端敲命令，但命令太长了。工业界的做法是把仿真内部需要执行的命令写进一个文件里，通常后缀为 `.do`（ModelSim 专属命名习惯，本质就是 Tcl 脚本），例如创建一个 `run_sim.do` 文件：

```tcl
# Create or refresh the working library.
if {[file exists work]} {
    vdel -lib work -all
}
vlib work
vmap work work

# Compile RTL and testbench.
# 如需编译 rtl/ 下嵌套子目录中的 .v 文件，改用 files.f 文件列表方式（见下方说明）
vlog -sv -work work ../rtl/*.v ../tb/riscv_soc_tb.v

# Start simulation.
vsim -voptargs=+acc work.riscv_soc_tb

# Record all signals for command-line runs too.
log -r /*

# Run until the testbench stops, then exit ModelSim.
onbreak {quit -f}
run -all
quit -f
```

然后在操作系统的终端里，只需**一键执行**：

```bash
cd project/sim
vmap -c
vsim -modelsimini ./modelsim.ini -c -do run_sim.do
```

> 上述命令的详细介绍含义见 [3.1 节](#section-31)

ModelSim 就会在后台飞速完成建库、编译、仿真、写波形、退出。几秒钟后，你在终端里就能看到 `$display` 打印出来的 `"Test Passed!"`。

!!! note "`files.f` 文件列表"
    `vlog` 的通配符 `*` 不支持递归，无法自动编译 `rtl/` 下嵌套子目录中的 `.v` 文件。
    工业界的标准做法是使用 `-f` 选项传入一个文件列表（通常命名为 `files.f`），在其中逐行列出所有需要编译的源文件路径：

    ```tcl
    # files.f
    ../rtl/top.v
    ../rtl/core/alu.v
    ../rtl/core/regfile.v
    ../rtl/core/control.v
    ../rtl/peripherals/uart.v
    ../rtl/peripherals/spi.v
    ../tb/riscv_soc_tb.v
    ```

    然后编译命令简化为：

    ```tcl
    vlog -sv -work work -f files.f
    ```

    在大型项目中，`files.f` 通常由脚本（Makefile / Python）自动生成，维护方便且跨平台兼容。

#### 2.2.4 没有 GUI，如何看波形呢？ (CLI 模式下的 Debug)
这是很多人刚接触 CLI 时的疑惑：不打开 GUI，怎么看波形抓 Bug？

1. **导出波形文件**：在 CLI 模式下运行时，可以通过命令（或者在 Verilog 代码里写 `$dumpfile("wave.vcd"); $dumpvars(0, riscv_soc_tb);`）将波形导出为 **VCD** 格式，或者 ModelSim 专属的 **WLF** 格式压缩波形。
2. **事后查看（Post-Processing Debug）**：仿真结束后，你可以拿着生成的波形文件，单独用 `gtkwave wave.vcd` 打开，或者用 ModelSim 仅打开波形文件：`vsim -view vsim.wlf`。
3. 这种做法叫 **“离线调试”**。在跑几十个测试用例时，只有 FAILED 的那个用例，工程师才会去打开它对应的波形文件慢慢看。

## III. Advanced Usage

### 3.1 `modelsim.ini`、逻辑库与物理库 <a id="section-31"></a>

#### 3.1.1 `modelsim.ini` 配置文件

`modelsim.ini` 是 ModelSim/Questa 在启动、编译、仿真时读取的 **初始化配置文件**。官方手册明确说，ModelSim 启动时会访问 `modelsim.ini`，其中包含初始工具设置；它还会根据一定优先级寻找应该使用哪一个 `modelsim.ini`。([ref: modelsim_user_2024_2][1])

可以这样理解：

> `modelsim.ini` 就是 ModelSim 的“工程环境配置表”。
> 它告诉 `vlog/vcom/vsim/vmap`：有哪些逻辑库、逻辑库对应哪个物理目录、编译器默认行为是什么、仿真器默认行为是什么、波形文件默认怎么保存等。

ModelSim 的库有两个层次：

| 概念   | 含义                | 例子                            |
| ---- | ----------------- | ----------------------------- |
| 逻辑库名 | HDL 代码/仿真**命令中使用**的库名 | `work`, `unisim`, `altera_mf` |
| 物理目录 | 磁盘上**真实存放编译产物**的文件夹   | `./work`, `./sim_lib/unisim`  |

`vlib` 负责创建物理库目录，例如：

```tcl
vlib work
```

官方文档说明，创建库后目录中会包含 `_info` 文件，**用来标识这是一个 ModelSim 设计库**，而不是普通文件夹；因此不可直接用系统命令手动 mkdir 来代替 `vlib`。([ref: modelsim_user_2024_2][1])

`vmap` 则负责把逻辑库名映射到物理目录，例如：

```tcl
vmap work work
vmap unisim ./sim_lib/unisim
```

官方文档明确说明，`vmap <logical_name> <directory_pathname>` 会把映射关系添加到 `modelsim.ini` 的 library section 中；也可以手动在 `[Library]` 下面写入 `<logical_name> = <directory_pathname>`。([ref: modelsim_user_2024_2][1])

也就是说：`vmap work work` 本质上是在 `modelsim.ini` 里写入类似：

```ini
[Library]
work = work
```

所以 `modelsim.ini` 最核心、最常见的作用就是：**保存 “逻辑库名 → 物理库目录” 的映射关系**。

#### 3.1.2 逻辑库与物理库

`modelsim.ini` 最核心、最常见的作用是建立逻辑库与物理库的库映射。那么什么是逻辑库与物理库呢？

**物理库**就是 ModelSim 在文件系统中创建的一个特殊目录，用来存放编译后的设计单元。例如执行 `vlib work` 后，当前目录下会生成一个名为 `work` 的文件夹，这就是一个**物理库**。这里的 `work` 是磁盘上真实存在的物理目录，因此称为物理库。在用 `vlog` 编译时，源文件和 testbench 的编译产物就会被存放在这个 `work` 目录下。 

**逻辑库**是 ModelSim/HDL 世界里使用的“库名”，它不一定等于磁盘目录名。例如：

```tcl
vlog -sv -work work ../rtl/*.v
vsim work.riscv_soc_tb
```

这里的 `-work work`, `work.riscv_soc_tb` 中的 `work` 就是逻辑库名。它告诉 ModelSim：**在编译和仿真时，使用名为 `work` 的逻辑库**。

例如，`modelsim.ini` 文件中

```ini
[library]
work = work
```

意思是逻辑库名 `work` 映射到物理目录：当前文件夹下的 `work`。

而：

```ini
[library]
work = ./sim_lib/my_work
```

意思是逻辑库名 `work` 映射到物理目录 `./sim_lib/my_work`。

**为什么要区分逻辑库和物理库呢？**

比如脚本的命令可以固定为：

```tcl
vlog -work work ...
vsim work.tb_top
```

但是实际物理目录可以是：

```ini
[library]
work = work
```

也可以是：

```ini
[library]
work = ./sim_lib/my_work
```

再比如厂商库：

```ini
[Library]
unisim = D:/Xilinx/Vivado/2023.2/data/simmodels/modelsim/unisim
altera_mf = D:/intelFPGA_lite/20.1/modelsim_ase/altera/verilog/altera_mf
```

仿真脚本或 HDL 代码里只需要引用 `unisim`, `altera_mf` 这些逻辑库名，而不用到处写一长串真实路径。

`vlib, vmap, vlog, vsim` 这些命令在执行时关于逻辑库/物理库的行为如下：

| 命令                    | 作用                                    | 影响对象                      |
| --------------------- | ------------------------------------- | ------------------------- |
| `vlib work`           | 创建 ModelSim 设计库目录                     | 创建物理库                     |
| `vmap work work`      | 把逻辑库名 `work`(前) 映射到物理目录 `work`(后)           | 修改库映射，通常**写入** `modelsim.ini` |
| `vlog -work work ...` | 把 Verilog/SystemVerilog 编译进逻辑库 `work` | 编译产物进入 `work` 对应的物理库      |
| `vsim work.tb_top`    | 从逻辑库 `work` 中加载 `tb_top`              | 根据映射找到真实物理库               |

显然，这四条命令中与 `modelsim.ini`、逻辑库/物理库关系最密切的就是 `vmap`:

```tcl
vmap <logical_name> <directory_pathname>
```

这行命令完成的功能为：

1. 将逻辑库 `<logical_name>` 映射到物理目录 `<directory_pathname>`。
2. 将上述映射关系写入**工作目录的** `modelsim.ini` 文件的 `[Library]` 部分。

所以，我们也可以直接在 `modelsim.ini` 的 `[Library]` 部分手动写入：

```ini
[Library]
<logical_name> = <directory_pathname>
```

#### 3.1.3 Modelsim 运行时的 `modelsim.ini` 与逻辑库/物理库行为

当我们启动 Modelsim GUI 模式时，`modelsim.ini` 由 Modelsim 自动管理，逻辑库和物理库的映射关系也会自动写入。

但是当我们用 CLI 模式运行时，需要特别注意 `modelsim.ini` 与逻辑库/物理库的映射关系，下面是简要介绍。

当我们运行 `vmap`, `vlog`, `vsim` 这些命令时，ModelSim 会按照以下优先级寻找 `modelsim.ini`：

1. 如果**命令行参数**显示指明 `-modelsimini <ini_filepath>`，优先使用这个文件；
2. 否则使用**环境变量** `MODELSIM` 指定的 `modelsim.ini`；
3. 否则尝试工作目录相关路径，例如 `./modelsim.ini`；
4. 再尝试**安装目录**下的 `modelsim.ini`；
5. 如果都找不到，路径会退回到 `./modelsim.ini`。([ref: modelsim_user_2024_2][1])

例如，下面几条命令会找到不同的 `modelsim.ini`: 

```bash
# 情况 1：当前目录有 modelsim.ini
vsim -c work.tb_top

# 情况 2：环境变量 MODELSIM 指向某个 ini
$env:MODELSIM = "D:/proj/sim/modelsim.ini"
vsim -c work.tb_top

# 情况 3：命令行强制指定 ini
vsim -modelsimini D:/proj/sim/modelsim.ini -c work.tb_top
vlog -modelsimini D:/proj/sim/modelsim.ini -work work rtl/top.sv
```

也就是说，如果我们使用 `vmap` 命令时，既没有指定 `-modelsimini`，也没有设置环境变量 `MODELSIM`，也没有在当前目录下放置 `modelsim.ini`，那么 `vmap` 就会在安装目录下寻找 `modelsim.ini`，并**尝试**把库映射关系写入那里。如果安装目录下的 `modelsim.ini` 是**只读**的（**通常是的**），那么工具会自动将起复制到工作目录下，后续的 `vmap`、`vlog`、`vsim` 命令就会在工作目录下的 `modelsim.ini` 里读写库映射关系。

当然，更加安全的方式是我们在使用 `vmap` 命令时，如果当前工作目录才刚刚建好，还没有 `modelsim.ini`，我们可以加上参数 `-c` 手动从安装目录复制一份 `modelsim.ini` 到当前目录：

```bash
vmap -c
```

#### 3.1.4 更推荐的 Python 自动化集成

Python 自动化时，最关键的是：每一次调用 `vmap`/`vlog`/`vsim` 都应该明确使用同一份 `modelsim.ini`。最推荐的方式是：**每一行命令都通过命令行参数显示指明该写/用哪个 `modelsim.ini`**、

即：

```python
run(["vmap", "-modelsimini", str(modelsim_ini_path), "work", "work"])
run(["vlog", "-modelsimini", str(modelsim_ini_path), "-sv", "-work", "work", "../rtl/alu.sv"])
run(["vsim", "-modelsimini", str(modelsim_ini_path), "-c", "work.tb_top", "-do", "run -all; quit -f"])
```

在利用 Python 集成自动化仿真时，它**最显式、最不容易受用户环境变量污染**，是最推荐的方式。

工程目录格式推荐：

```text
project/
├─ rtl/
├─ tb/
├─ sim/
│  ├─ modelsim.ini
│  └─ work/
└─ scripts/
   └─ run_modelsim.py
```


[1]: https://ww1.microchip.com/downloads/aemDocuments/documents/FPGA/swdocs/modelsim/modelsim_user_2024_2.pdf "ModelSim® User's Manual"

