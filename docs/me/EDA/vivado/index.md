# Vivado 使用笔记

## I. Vivado 简介

### 1.1 Vivado 是用什么语言编写的？

与 ModelSim 类似，EDA 工具的语言栈高度分化：

1. **核心算法引擎（底层）**：**C/C++**。Vivado 内部包含了极其复杂的综合算法、时序分析（STA）算法、以及布局布线（Place & Route）算法（本质上是超大规模图论计算和模拟退火等最优化问题），这些部分全是由 `C/C++` 编写，以压榨 CPU 和内存的极限性能。
2. **交互界面与外壳（GUI）**：主要使用 **Java**（部分结合 C++ 的图形库）。所以在启动 Vivado 时，常常会看到它极其吃内存，且界面带有典型的 Java 应用程序特征。
3. **脚本与胶水层（核心操控语言）**：**纯 Tcl (Tool Command Language)**。Vivado **100% 是一套基于 Tcl 的原生系统**。在 GUI 上点击的每一个按钮，底层统统会翻译成标准的 Tcl 命令执行。
4. **约束语言**：**XDC (Xilinx Design Constraints)**。它是 Tcl 的一个子集，且完全兼容 Synopsys 的 SDC 工业标准（这与 Design Compiler 的约束是同一套体系）。


### 1.2 底层运作方式：Vivado 的“统一数据模型”

#### 1.2.1 Unified Data Model

以前的旧版工具（如 Xilinx ISE 或 Altera Quartus II 早期版本）是“串行链式”的：综合工具吐出一个网表文件，布局工具读入网表再吐出一个文件，布线工具再读入……不同工具之间互不相通。每个工具都使用**不同的数据模型，输出格式各异**，导致设计数据在不同阶段“走样”。**综合的中间结果无法直接被下一阶段的布局布线工具理解，约束文件也需要反复转换**，这就像是不同部门说着不同的语言。

**Vivado 的底层运作机制是革命性的：“In-Memory 统一数据模型（Unified Data Model）”**。

1. 加载 RTL 后，Vivado 会在**内存**中建立一个巨大的、包含所有逻辑门和连线的数据结构（Netlist Database）。
2. 接下来的所有步骤——时序约束、布局（Placement）、物理优化（Phys_Opt）、布线（Routing），都是**对内存中这个同一份数据**进行反复修改和附加属性。约束、网表、布局布线等信息都以统一格式存储和访问，无需转换。

#### 1.2.2 Design Checkpoint (DCP)

要实现上述理念，需要一个具体的文件格式作为载体，这就是 **Design Checkpoint (DCP)**。`.dcp` 文件将某一阶段所有必要设计信息打包为一个整体。它不仅是一个**超集**，也是设计流程的核心载体，**在每个主要步骤后都会生成**。

`.dcp` 文件包含：

*   **网表**：描述了当前设计的逻辑连接关系。
*   **约束**：所有的 `.xdc` 约束文件都已被读入并解析。
*   **布局布线结果**：在布局、布线后生成的DCP会包含这些信息，实现“反标”。
*   **器件信息**：包含了目标FPGA器件的所有信息，如资源、引脚等。 

有了DCP文件，Vivado的设计流程（以 **Non-Project Mode, 非工程模式**为例）变得非常高效。

传统的ISE流程各阶段文件格式不一，而 Vivado 非工程模式流程**高度依赖 DCP 文件进行状态保存和传递**：

1.  **综合 (Synth_design)** $\rightarrow$ `synth.dcp`
2.  **逻辑优化 (Opt_design)** $\rightarrow$ `opt.dcp`
3.  **布局 (Place_design)** $\rightarrow$ `place.dcp`
4.  **布线 (Route_design)** $\rightarrow$ `route.dcp`
5.  **生成比特流 (Write_bitstream)** $\rightarrow$ `.bit`

> **注**：
> **IP 的 DCP**: IP会提供预综合的 `.dcp` 文件，这被称为OOC（Out-of-Context）综合。在顶层设计中，这些IP会被当作“黑盒子”，从而显著加快整体综合速度。
> **版本兼容性**：DCP 文件与 Vivado 版本之间不是完全兼容的，**较新的版本通常无法被旧版软件打开**。因此，在团队协作或归档时，保留原始RTL代码和约束文件依然非常重要。
> **共享与安全**：DCP文件是一种**加密**的二进制格式，可以在**不泄露原始 RTL 代码**的前提下，安全地分享设计信息

### 1.3 Vivado 工具栈

Vivado 远不止“综合→布局布线→生成比特流”，它内部集成了多个极其强大的独立子系统。我们可以把它拆分为 **6 大核心板块**：

1. **内置仿真器：Vivado Simulator (XSim)**
    * **功能**：它是 Xilinx 自带的混合语言仿真器，用来替代 ModelSim/VCS。
    * **底层机制**：与 ModelSim 非常像，XSim 也是**编译型仿真器**。在 CLI 模式下，它对应的底层命令是：
        * `xvlog` / `xvhdl`：编译 Verilog/VHDL 代码。
        * `xelab`：细化（Elaboration），将编译好的代码链接并生成可执行的仿真快照（Snapshot）。
        * `xsim`：运行仿真内核，产生波形（`.wdb` 文件）。
2. **IP 目录与封装器 (IP Catalog & IP Packager)**
    * **工业界痛点**：Xilinx 提供了数以千计的**成熟 IP 核心**，从简单的 FIFO、BRAM，到复杂的 PCIe 接口、DDR4 控制器、Ethernet MAC 等等。
    * **功能**：可以在 IP Catalog 中像查字典一样调用它们，配置参数，Vivado 会自动生成加密的底层网表和仿真模型。也可以用 IP Packager 把自己写的模块打包成一个标准 IP（带有 AXI4 总线接口），供别人使用。
3. **块设计/系统集成器：IP Integrator (IPI / Block Design)**
    * **功能**：这是现代 SoC 芯片设计的利器。它提供了一个**图形化的“连线画布”**（Block Design，生成 `.bd` 文件）。
    * **场景**：当需要把自己写的 CPU、Xilinx 的 DDR 控制器、UART 串口 IP 组合在一起时，不需要写长篇累牍的 Verilog 顶层例化代码。只需在画布上把这些 IP 拖出来，让 Vivado 自动连线（尤其是 AXI 总线，它可以一键自动匹配地址和连接几十根线）。这是开发 Zynq（ARM + FPGA 混合架构）的绝对主力工具。
4. **高级综合引擎：Vitis HLS (High-Level Synthesis)**
    * **功能**：将 **C/C++ 算法代码直接转换为 RTL (Verilog/VHDL) 代码**。
    * **为什么重要？** 比如 CNN 加速器或 OFDM 通信算法，如果用 Verilog 写状态机和流水线会极其痛苦。利用 HLS，可以用 C++ 写出卷积循环或者 FFT 算法，加上几行 `#pragma` 编译指示（如 `PIPELINE`, `UNROLL`），HLS 引擎就能自动生成几千行带流水线的 Verilog 代码，并直接打包成 IP 导入到 Vivado 中使用。
5. **硬件调试管理器：Hardware Manager & ILA**
    * **功能**：板级联调的“终极杀手锏”。当把比特流（Bitstream）下载到真实的 FPGA 芯片后，如果芯片行为不对，怎么办？真实芯片里可没有 ModelSim 让你看波形。
    * **ILA (Integrated Logic Analyzer, 集成逻辑分析仪)**：Vivado 允许在 RTL 代码里插入一个 ILA IP，或者直接在综合后的网表上“抓线”。它会消耗一部分芯片内部的 BRAM（存储器），在芯片高速运行时**实时抓取真实信号波形**，并通过 JTAG 下载线传回 Vivado 的 GUI 界面显示出来。**这是 FPGA 工程师最重要的 Debug 技能**。
6. **静态时序分析器：Timing Analyzer**
    * **功能**：它不靠跑数据来判断对不对，而是靠严密的数学计算。它会分析设计模块里任意两个触发器之间的组合逻辑延迟，告诉你当前系统能不能跑在 100MHz 甚至 500MHz，有没有发生 Setup Time（建立时间）或 Hold Time（保持时间）违例。

## II. Quick Start Guide

### 2.1 Project Mode

Project Mode (工程模式)，也就是 GUI 模式，是 Vivado 最直观、最适合初学者的使用方式。它把整个设计流程（从创建工程、添加源文件、综合、布局布线，到生成比特流）用一个统一的图形界面封装了起来。通过点击鼠标建立 `.xpr` 工程，Vivado 会**自动在后台管理所有文件的状态和依赖关系**。

#### Step 1: 创建工程与选型 (Create Project)

1. 在欢迎界面点击 **Create Project**。
2. **Project Type**：选择 **RTL Project**（记得勾选“Do not specify sources at this time”，我们稍后再加文件，这样更清晰）。
3. **Default Part（关键步骤）**：这里与纯前端仿真不同，必须选择一款**真实的 FPGA 芯片型号**。
    * *工业视角*：这一步决定了 Vivado 内部综合和布线时使用的物理资源库。不同的芯片，其内部包含的查找表（LUT）、触发器（FF）、块RAM（BRAM）数量和时序模型完全不同。

![alt text](./assets_create_project.webp)

#### Step 2: 管理源文件 (Add Sources & Constraints)

进入主界面后，在 **Sources** 窗口中，需要添加三类文件：

1. **Design Sources**：Design 的所有 `.v`/`.sv` 文件。
2. **Simulation Sources**：Testbench。Vivado 会自行把 Testbench 和设计文件在界面上以层次化的树状图展现出来。
3. **Constraints (XDC 文件)**：添加或新建一个 `.xdc` 约束文件。
    * XDC（Xilinx Design Constraints）在时序约束部分**完全等同于 Synopsys 的 SDC**。需要在这里定义时钟周期（`create_clock`），并绑定芯片引脚（`set_property PACKAGE_PIN ...`）。


#### Step 3: RTL 级分析 (RTL Analysis)
在左侧 Flow Navigator 点击 **Open Elaborated Design**。

* **功能**：这是在跑综合之前的“语法树展开”阶段。Vivado 会把你的代码画成一张宏观的**门级原理图 (Schematic)**。
* **找 Bug 神器**：你可以在图上直观地看到你的 ALU 模块、寄存器堆（RegFile）模块是如何连线的。如果某条总线悬空或者位宽不匹配，在这一步就能一眼看出来，无需等到漫长的综合跑完。