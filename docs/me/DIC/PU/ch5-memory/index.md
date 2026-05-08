# 第五章：Large and Fast: Exploiting Memory Hierarchy
## I. Introduction to Memory Technology
存储系统设计的核心矛盾，是**处理器与内存的性能增长速度存在巨大鸿沟**，这也是现代计算机体系结构中存储层次（Memory Hierarchy）设计的核心动因。

### 1.1 处理器与内存的性能鸿沟
从技术发展趋势来看，处理器与内存的性能差距持续拉大，形成了制约系统性能的「内存墙」问题：

- 处理器性能：以每年约52%的速度持续增长，算力提升速度极快
- DRAM内存延迟：仅以每年约7%的速度缓慢优化，访存延迟的改进远落后于处理器
- 早在1977年的Apple计算机中，CPU周期1000ns，DRAM访问延迟400ns，二者差距极小；而随着半导体技术迭代，二者的性能差距呈指数级扩大。

![](image-1.webp)

### 1.2 三大核心存储技术
2012年主流的三类存储技术，在**访问速度、存储容量、单位成本**上形成了天然的梯度差异，为存储层次结构提供了硬件基础：

| 存储类型 | 典型访问延迟 | 单位容量成本（$, 2012年） | 核心特性与用途 |
| --- | --- | --- | --- |
| 静态随机存储器 SRAM | 0.5ns – 2.5ns | $2000 – $5000 / GB | 速度最快，无需定时刷新，集成度低、成本高，主要用于CPU片内缓存 |
| 动态随机存储器 DRAM | 50ns – 70ns | $20 – $75 / GB | 速度中等，需要定时刷新保持数据，集成度高、成本适中，用作计算机主存 |
| 机械磁盘 Magnetic disk | 5ms – 20ms | $0.20 – $2 / GB | 速度最慢，容量上限极高，单位成本极低，用作系统持久化外存 |

### 1.3 理想内存的设计目标
理想存储系统需要同时满足两个相互制约的核心需求：

1. 访问延迟达到SRAM的极速水平
2. 容量和单位成本达到机械磁盘的水平

**存储层次结构**，正是利用程序的局部性原理，在现有硬件技术条件下，尽可能逼近这一理想目标的核心工程方案。

## II. Memory Hierarchy

### 2.1 Principle of Locality 局部性原理
局部性原理是存储层次结构能够成立的核心理论基础，其核心结论为：**程序在任意运行时刻，只会访问其整个地址空间中的极小一部分**。

!!! note "Memory Hierarchy"
    (1) Store everything on **disk**;
    (2) Copy recently accessed (and nearby) items from disk **to smaller DRAM memory**;
    (3) Copy recently accessed (and nearby) items from DRAM **to smaller SRAM cache**;

局部性分为两大核心类型，二者共同决定了存储层次的效率：

#### 2.1.1 时间局部性（Temporal locality）

- 核心定义：**最近被访问过的内容，在不久的将来大概率会被再次访问**
- 典型场景：循环体中的指令、循环计数的归纳变量、被频繁调用的函数、高频访问的全局变量

#### 2.1.2 空间局部性（Spatial locality）
- 核心定义：**被访问内容的相邻地址数据，在不久的将来大概率会被访问**
- 典型场景：顺序执行的指令流、**数组元素**的连续遍历、结构体成员的批量访问

![](image-2.webp)

### 2.2 Memory Hierarchy Levels
#### 2.2.1 核心设计思想
存储层次结构构建了从CPU到外存的多层存储金字塔，利用局部性原理实现「**速度接近顶层、容量和成本接近底层**」的效果，核心运作逻辑为：

1. 所有数据永久存储在最底层的磁盘中
2. 将**最近被访问、且相邻地址**的数据块，从磁盘复制到容量更小的DRAM主存中
3. 将**更近期被访问、且相邻地址**的数据块，从DRAM主存复制到容量更小、紧邻CPU的SRAM缓存中
4. 最顶层为CPU内的寄存器堆，为执行单元提供单周期极速访问

#### 2.2.2 核心术语定义

| 术语 | 英文全称 | 核心定义 |
| --- | --- | --- |
| **块/行** | **Block / Line** | **存储层次之间数据复制的最小单位**，通常包含多个连续的字 |
| **命中** | **Hit** | 待访问的数据**存在于当前上层存储**中，可直接由上层存储响应访问请求 |
| 命中率 | Hit ratio | 命中访问次数 / 总访问次数，衡量存储层次效率的核心指标 |
| 命中时间 | Hit time | 命中时完成一次访问的总耗时，包括标签检测和数据读取时间 |
| **缺失** | **Miss** | 待访问的数据**不存在于当前上层存储**中，需要从**下层存储调取对应数据块** |
| 缺失率 | Miss ratio | 缺失访问次数 / 总访问次数 = 1 - 命中率 |
| **缺失代价** | **Miss penalty** | 处理**一次缺失的总耗时**，包括从**下层存储替换数据块、向上层传输数据**的完整时间 |
| inclusive | exclusive | 上层存储中的数据**一定存在于下层存储中**，例如 Register File 中的数据一定存在于 SRAM -> DRAM -> Disk 中 |
| exclusive | exclusive | 上层存储中的数据**不一定存在于下层存储中**，例如 Cache 中的数据不一定存在于 DRAM 中 |

**exclusive 的策略比较少，后续情况我们默认考虑 inclusive 情况**

## III. Memory Technology
### 3.1 Register File 寄存器堆
寄存器堆是存储层次结构的最顶层，紧邻CPU执行单元，是整个存储系统中访问速度最快的单元，也是RISC-V等ISA的核心组成部分。

结构图（读逻辑与写逻辑）：

![](image-3.webp)




#### 3.1.1 核心结构与特性
- 典型配置：RISC-V架构标准为32个32位通用整数寄存器
- 读写端口：标准配置为**2个读端口、1个写端口（2R1W）**，支持单周期内同时读取2个寄存器、写入1个寄存器，完美匹配五级流水线的指令执行需求
- 访问特性：寄存器访问延迟为1个时钟周期，无访问缺失，是CPU指令执行的核心数据载体

#### 3.1.2 寄存器堆的Verilog实现示例
```verilog
module registerfile (
    Read1, Read2, WriteReg, WriteData, RegWrite,
    Data1, Data2, clock
);
// 端口定义
input  [5:0]  Read1, Read2, WriteReg; // 读/写寄存器编号
input  [31:0] WriteData;              // 待写入寄存器的数据
input         RegWrite;                // 寄存器写使能信号
input         clock;                   // 时钟信号，写操作同步于上升沿
output [31:0] Data1, Data2;            // 两个读端口的输出数据

// 寄存器堆本体：32个32位通用寄存器
reg [31:0] RF [31:0];

// 组合逻辑读：无时钟延迟，实时输出对应寄存器的值
assign Data1 = RF[Read1];
assign Data2 = RF[Read2];

// 时序逻辑写：仅时钟上升沿、写使能有效时执行写入
always @(posedge clock) begin
    if (RegWrite) begin
        RF[WriteReg] <= WriteData;
    end
end

endmodule
```

### 3.2 SRAM Technology 静态随机存储器
SRAM（Static Random-Access Memory）由于其极高的访问速度，主要用于实现CPU片内的 **Cache（缓存）**。从体系结构的发展来看，SRAM 经历了从片外（Off-chip）向片内（On-chip）集成的过程，极大降低了访存延迟。

#### 3.2.1 SRAM 核心结构与读写机制
标准的 SRAM 存储单元采用 **6T结构（6 Transistors/bit）**，利用交叉耦合的反相器锁存数据。

*   **核心特性**：
    *   只要不断电，数据就能一直保持（Retain bit），**无需刷新**。
    *   保持数据的**静态功耗极低**（Low power to retain bit），但占用硅片面积较大。

![alt text](image-4.webp)

SRAM 的基本读写逻辑依赖于 **字线（Wordline, WL）** 和 **位线对（Bitlines, BL & $\overline{BL}$）** 的协同操作：
*   **Cell read (读操作)**：
    1.  首先将两根位线（Bitlines）**预充（Precharge）** 至高电平（$V_{DD}$）。
    2.  拉高字线（Wordline），打开传输管（Pass transistors）。
    3.  存储单元内部的状态会将其中一根位线的电平**下拉（Pulled down）**，外围的**灵敏放大器**（Sense Amplifier）通过检测两根位线的微小压差来读出 0 或 1。
*   **Cell write (写操作)**：
    1.  由写入驱动器强行将一根位线拉高，另一根位线拉低（代表要写入的数据）。
    2.  拉高字线（Wordline）打开传输管。
    3.  由于**外围驱动器的驱动能力远大于内部的交叉耦合反相器**，位线上的强信号会**覆盖（Overpower）**存储单元内的旧值，完成写入。

#### 3.2.2 SRAM 组织架构与译码逻辑
为了在芯片面积、功耗和访问延迟之间取得平衡，大容量 SRAM 阵列不会采用扁平的单级译码，而是采用 **多路复用（Multiplexing）** 和 **两级译码（2-level decoding）** 结构。

**(1) Multiplexing**

多选一，输入数量极大，再用 Mux ，扇入会很大，造成大量面积和延迟的开销。
这种情况，用**线与/线或**的方式；并且在访问其中某一行时，必须通过**显式的 enable 信号关掉**。

![alt text](image-5.webp)

**(2) Decoder**
**设计案例分析（以一个 4MB SRAM 为例）**：

*   如果不做二维阵列优化，4M 个字（Words）需要 4M 根字线（Word lines），这在物理布线上是极其荒谬且无法实现的。
*   **优化方案**：将其组织成矩形阵列。利用 12-to-4096 的行译码器生成 **4K 根字线（Word lines）**；同时在列方向上配合使用 **1K 的多路选择器（MUX * 8）**。这样不仅大幅缩短了字线和位线的物理长度（降低了RC延迟），还极大地优化了版图面积。

![alt text](image.webp)


### 3.3 DRAM Technology & Organization 动态随机存储器
DRAM（Dynamic Random-Access Memory）由于其极高的存储密度和低廉的成本，是计算机 **Main memory（主存）** 的绝对主力。

#### 3.3.1 DRAM 基本存储单元特性
不同于 SRAM 的 6T 结构，DRAM 采用极简的 **1T1C结构（单管单电容）**：

**数据存储**：数据以电荷（Charge）的形式存储在微小的电容（Capacitor）中。

**数据访问**：由**单个传输管**（Single transistor）作为开关来访问电容中的电荷，通过 **word line** 激活对应的行，**bit line** 传输电荷信号。 

**破坏性读出与刷新（Refresh）**：

- **读出电荷后，原有的电荷会被破坏**，因此必须在读取后将数据**写回（Write back）**。
- 由于电容存在**天然漏电**，DRAM 单元必须**周期性地进行刷新（Periodically be refreshed）**，这也是 "Dynamic" 的由来。刷新操作通常是以**行（Row）**为单位进行的。

![alt text](image-6.webp)

#### 3.3.2 DRAM 阵列组织与访问模式
DRAM 内部的比特位同样被组织成**矩形阵列（Rectangular array）**，核心访问逻辑是分两步走：先**选中整行**，**再挑出特定的列**。

*   **行级访问**：DRAM 每次访问（Access）都会激活一整个 Row，并将其放入行缓冲区（Column latches / Row buffer）中。
*   **Burst mode (突发模式)**：既然一整行的数据已经被读出到了缓冲区中，如果后续请求的地址是连续的，就可以直接从缓冲区中**以极低的延迟连续提供后续字（Supply successive words with reduced latency）**，而无需再次进行缓慢的内部行读取。
    > **更好的方式**是尽量做到一行中存放想要的数据，这样就不需要多次切换不同行的访问。因为每次访问完一行，电容上的电荷都会损失，需要重新充电（Recharged），这会带来额外的访问延迟。
*   **DDR (Double Data Rate) DRAM**：通过在时钟信号的**上升沿和下降沿**同时传输数据，使得数据传输速率翻倍。

![alt text](image-7.webp)

#### 3.3.3 决定 DRAM 性能的核心因素
现代存储系统通过以下三大核心技术来榨干/提升 DRAM 的性能（特别是提升带宽）：
1.  **Row buffer (行缓冲区)**：允许**并行读取**和刷新多个字，是实现**Burst mode**的物理基础。
2.  **Synchronous DRAM (SDRAM, 同步DRAM)**：配合系统时钟，允许连续的**突发访问**（Consecutive accesses in bursts），**无需为每个字单独发送地址（Without needing to send each address）**，大幅提升了总线**带宽（Bandwidth）**。
3.  **DRAM banking (多体交叉/多Bank结构)**：允许同时（Simultaneous access）访问多个不同的 DRAM Bank，通过并行流水线操作掩盖单一 Bank 漫长的内部访问延迟，成倍提升吞吐量。


#### 3.3.4 Increasing Memory Bandwidth 提升内存带宽的系统架构设计
为了缓解「内存墙」问题，系统架构师需要优化 CPU 与主存之间的互连架构。以下通过一个经典的计算模型，对比三种内存组织架构的 **Miss penalty（缺失代价）** 和 **Bandwidth（带宽）**。

!!! note "基础假设 (Assumption)"
    - 发送一次地址耗时：**1 cycle**
    - 每个字（Word）的内部访问耗时：**15 cycles**
    - 在总线上传输返回一个字耗时：**1 cycle**
    - Cache Block（缓存块）大小：**4 words（即 16 bytes）**

![alt text](image-8.webp)

**(1) 单字宽内存架构 (1-word wide memory)**
每次**只能访问并传输 1 个字**，处理 1 个 Cache Block 需要循环 4 次完整的「发地址 -> 访问 -> 传数据」流程。

*   $Miss\ penalty = 4 \times (1 + 15 + 1) = 68\ cycles$
*   $Bandwidth = 16\ bytes\ /\ 68\ cycles = \mathbf{0.24\ B/cycle}$

**(2) 宽总线内存架构 (4-word wide memory)**
将内存和总线宽度直接拓宽为原来的 4 倍，发 1 次地址即可同时访问 4 个字，并一次性传回。

*   $Miss\ penalty = 1\ (发地址) + 15\ (并行访问) + 1\ (并行传回) = 17\ cycles$
*   $Bandwidth = 16\ bytes\ /\ 17\ cycles = \mathbf{0.94\ B/cycle}$
*   *评价：性能最好，但代价极其昂贵（CPU芯片引脚数量和主板布线成本剧增）。*

**(3) 多体交叉内存架构 (4-bank interleaved memory)**
**（性价比最高的工业界主流方案）**
保持标准**单字宽总线**，但将内存划分为 **4 个独立的 Bank**。发 1 次地址后，4 个 Bank 内部**并行**访问各自的字（耗时15周期），然后依次占用总线传回数据（耗时 $4 \times 1$ 周期）。

*   $Miss\ penalty = 1\ (发地址) + 15\ (4个Bank同时访问) + 4 \times 1\ (排队占用总线传回) = 20\ cycles$
*   $Bandwidth = 16\ bytes\ /\ 20\ cycles = \mathbf{0.8\ B/cycle}$
*   *评价：用极小的硬件代价（未拓宽总线）换取了接近宽总线架构的极高带宽。*


#### 3.3.5 DRAM 物理层级组织与存储器分类

**(1) DRAM 物理内存条架构 (DIMM Organization)**
现代计算机的主存呈现出严密的自顶向下的层级组织结构：

1.  **Channel**：处理器内部集成的内存控制器通道，决定了内存条的并发读写上限。
2.  **DIMM (Dual in-line memory module, 双列直插存储模块)**：即我们平时买到的物理内存条实体。
3.  **Rank**：为了凑齐总线的位宽（例如 64-bit），把多个芯片组合在一起协同工作。例如：Rank 0 可以由 8 颗位宽为 8-bit 的芯片（$8 \times 8 = 64$）组成，它们同时响应同一个地址读写命令。
4.  **Chip**：内存条上一颗颗黑色的物理颗粒。
5.  **Bank**：Chip 内部划分的独立存储阵列区域，不同 Bank 之间可以并行操作（对应上一节的 Interleaved memory）。
6.  **Row / Column**：底层 1T1C 单元构成的二维阵列网格。

![alt text](image-9.webp)

**(2) 现代半导体存储器分类体系**

根据断电后数据是否丢失，存储芯片（Memory chips）主要被分为两大阵营：

![alt text](image-10.webp)

**标准 DDR**：用于 PC 和服务器主存。
**移动 DDR (LPDDR)**：用于手机等极低功耗设备。
**图形 DDR (GDDR)**：用于 GPU 的显存，强调极高的突发带宽。
**HBM (High Bandwidth Memory)**：采用 3D 硅穿孔封装技术的现代高端显卡/AI加速器超高带宽显存。




