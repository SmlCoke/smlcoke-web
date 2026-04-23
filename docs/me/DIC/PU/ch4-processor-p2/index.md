# 第四章：处理器架构与流水线设计

## VII. Exceptions and Interrupts

"Unexpected" events requiring change in flow of control. Different ISAs use the terms differently.

最典型的有两种：

1. Exception/Trap: 发生在 CPU 内部的事件，如除零错误、MEM 比特翻转等。
2. Interrupt: 发生在外部设备，例如键盘输入、网络数据到达等。

### 7.1 ISA 与异常 (ISA and Exception)
不同的高级语言对异常（如算术溢出）的处理方式不同：

**(1) 忽略溢出的语言（如 C 语言）**：RISC-V 默认的 `add`, `addi`, `sub` 等指令**不会**因为溢出而产生异常。
**(2) 抛出异常的语言（如 Ada, Fortran）**：如果需要检测溢出，RISC-V 并不提供专用的带溢出检测的加法指令，而是通过**额外的分支指令（Branch）**由软件来实现检测。

**1. 无符号数加法**：`addu t0, t1, t2` 后，接 `bltu t0, t1, overflow` (若和小于任一加数，说明进位溢出)。
**2. 有符号数加法**：判断逻辑更复杂，需要判断符号位是否发生异常翻转（如正+正=负，负+负=正）。例如：

```assembly
add t0, t1, t2
slti t3, t2, 0  # t3 = (t2<0)
slt t4, t0, t1  # t4 = (t1+t2<t1)
bne t3, t4, overflow  # 如果 t2<0 且 t1+t2>=t1，或 t2>=0 且 t1+t2<t1，则发生溢出
```

### 7.2 异常/中断的处理机制 (Handling Exceptions)
为了让操作系统（OS）能够接管并处理异常，硬件必须自动完成以下操作：

**(1) 保存现场**：
   
   - 记录发生异常/被中断的指令的 PC 值。在 RISC-V 中，保存在 **SEPC (Supervisor Exception Program Counter)** 寄存器中。`SEPC` 是专用寄存器，软件无法控制。
   - 记录异常发生的原因。在 RISC-V 中，保存在 **SCAUSE (Supervisor Exception Cause)** 寄存器中。

**(2) 跳转到处理程序 (Handler)**：

   - **向量中断 (Vectored Interrupts)**：根据不同的异常原因，直接跳转到对应的地址（例如：未定义操作码跳转到 `C000 0000`，溢出跳转到 `C000 0020`）。
   - **单一入口点 (Single entry point)**：所有异常跳到同一个基地址（如 `1C090000`），然后由软件读取 SCAUSE 寄存器，再利用 `switch-case` 跳转到具体的处理函数。

!!! note "处理程序 (Handler) 的执行动作"
    (1) 读取 SCAUSE 确定原因并执行相应动作。
    (2) **如果是可恢复的 (Restartable)**：处理完毕后，利用 SEPC 寄存器的值返回原程序，重新取指（Refetch）并从头执行该指令。
    (3) **如果是不可恢复的 (Otherwise)**：终止程序，并利用 SEPC 和 SCAUSE 报告错误（如常见的段错误 Segfault）。

### 7.3 流水线中的异常处理硬件实现 (Exception in Pipeline)


假设在 EX 阶段的 `add` 指令发生了异常：

1. **硬件冲刷 (Flush)**：硬件会发出 `IF.Flush`, `ID.Flush`, `EX.Flush` 信号，将该指令以及正在 IF、ID 阶段跟随它的后续指令全部清空，替换为气泡（Bubble / nop）。同时将**异常指令的 PC 值保存到 SEPC 寄存器中**，将**异常原因保存到 SCAUSE 寄存器中**。
2. **重定向 PC**：硬件强制将 PC 的多路选择器（MUX）切换，把下一条指令的取指地址指向 Exception Handler 的入口地址（如 `1C090000`）。
3. 之前已经进入 MEM 和 WB 阶段的指令（处于故障指令之前的指令）允许正常执行完毕，保证机器状态的精确性（Precise Exception）。

<div class="media-frame">

![](image-42.webp)

<div class="figure-caption">图 1. 异常处理机制示意图</div>

</div>


## VIII. 指令级并行 (Instruction-Level Parallelism, ILP)
为了进一步提升 CPU 性能（降低 CPI），必须挖掘指令级并行。

* **时间并行 (Temporal Parallelism)**：**加深流水线**（Deeper pipeline）。每级流水线的工作量变少，时钟频率（Clock rate）可以更高。但**代价**是：**控制冒险和异常带来的冲刷惩罚**（Penalty）变得更大。
* **空间并行 (Spatial Parallelism)**：增加多个功能单元（Multiple function units），例如设计多个 ALU。

### 8.1 多发射技术 (Multiple Issue)
结合空间与时间并行，允许在**同一个时钟周期内启动多条指令**。**此时 CPI < 1**，因此通常使用 **IPC (Instructions Per Cycle)** 来衡量性能。多发射面临严重的数据依赖挑战，主要分为两派：

1. **静态多发射 (Static multiple issue)**：依赖**编译器 (Compiler)**。编译器负责检测冒险，并将没有依赖关系的指令打包在一起（Issue packet）。这种架构常被称为 **VLIW (Very Long Instruction Word，超长指令字)**。
2. **动态多发射 (Dynamic multiple issue)**：依赖 **CPU 硬件 (HW)**。CPU 在运行时动态检查指令流，决定每个周期发射哪些指令。硬件利用**乱序执行**（Out-of-Order）、**重命名**等高级技术在运行时**解决冒险**（超标量 Superscalar 架构通常用此方法）。

### 8.2 RISC-V 静态双发射架构设计 (RISC-V Static Dual Issue)

#### 8.2.1 Architecture

以一种简单的 VLIW 思想实现的 RISC-V 双发射为例，该双发射为**一条 `ALU/Branch` 指令和一条` Load/Store` 指令的组合**。流水线架构图：

<div class="media-frame">

![](image-43.webp)

<div class="figure-caption">图 2. RISC-V 双发射架构示意图</div>

</div>

* **发射包 (Issue Packet)**：64-bit 对齐（包含 2 条 32-bit 指令）。
* **组合限制**：为了简化译码器和发射逻辑，严格规定一条是 `ALU/Branch` 指令，另一条是 `Load/Store` 指令。如果某类指令缺失，必须用 `nop` (气泡) 填充。

**硬件架构的修改**：
为了支持双发射，数据通路（Datapath）需要付出额外的硬件成本：
1. **寄存器堆 (Register File, RF) 端口增加**：两条指令同时读取和写入，RF 需要增加到**额外的读端口和写端口**（例如需要 4个读端口，2个写端口）。
2. **增加额外的 ALU**：原本五级流水线中**唯一的 ALU 不能同时处理数据运算和内存地址计算**，必须为 `Load/Store` 流水线单独增加一个**用于地址计算**的 ALU/Adder。

#### 8.2.2 Hazards in the Dual-Issue RISC-V

双发射架构中，更多的指令并行执行，此时冒险的情况更复杂，主要有以下几类：

**(1) EX data hazard**

单发射中通过 fwd 结构可以解决如下 stall 的问题：

```assembly
add x11, x12, x13
load x20, 0(x11)  # 需要 x11 的值，但 x11 在 EX 阶段才计算出来
```

这种情况必须切分为两个指令包，因此会产生 stall /

**(2) Load-use hazard**

Still **one cycle use latency**, but now **two instructions** are affected.

**(3) More aggressive scheduling required**