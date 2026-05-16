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


## III. Register File 寄存器堆
寄存器堆是存储层次结构的最顶层，紧邻CPU执行单元，是整个存储系统中访问速度最快的单元，也是RISC-V等ISA的核心组成部分。

结构图（读逻辑与写逻辑）：

![](image-3.webp)




### 3.1 核心结构与特性
- 典型配置：RISC-V架构标准为32个32位通用整数寄存器
- 读写端口：标准配置为**2个读端口、1个写端口（2R1W）**，支持单周期内同时读取2个寄存器、写入1个寄存器，完美匹配五级流水线的指令执行需求
- 访问特性：寄存器访问延迟为1个时钟周期，无访问缺失，是CPU指令执行的核心数据载体

### 3.2 寄存器堆的Verilog实现示例
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

## IV. SRAM Technology 静态随机存储器
SRAM（Static Random-Access Memory）由于其极高的访问速度，主要用于实现CPU片内的 **Cache（缓存）**。从体系结构的发展来看，SRAM 经历了从片外（Off-chip）向片内（On-chip）集成的过程，极大降低了访存延迟。

### 4.1 SRAM 核心结构与读写机制
标准的 SRAM 存储单元采用 **6T结构（6 Transistors/bit）**，利用交叉耦合的反相器锁存数据。

*   **核心特性**：
    *   只要不断电，数据就能一直保持（Retain bit），**无需刷新**。
    *   保持数据的**静态功耗极低**（Low power to retain bit），但占用硅片面积较大。

![alt text](image-4.webp)

SRAM 的基本读写逻辑依赖于 **字线（Wordline, WL）** 和 **位线对（Bitlines, BL & $\overline{BL}$）** 的协同操作：
**Cell read (读操作)**：

1.  首先将两根位线（Bitlines）**预充（Precharge）** 至高电平（$V_{DD}$）。
2.  拉高字线（Wordline），打开传输管（Pass transistors）。
3.  存储单元内部的状态会将其中一根位线的电平**下拉（Pulled down）**，外围的**灵敏放大器**（Sense Amplifier）通过检测两根位线的微小压差来读出 0 或 1。

**Cell write (写操作)**：

1.  由写入驱动器强行将一根位线拉高，另一根位线拉低（代表要写入的数据）。
2.  拉高字线（Wordline）打开传输管。
3.  由于**外围驱动器的驱动能力远大于内部的交叉耦合反相器**，位线上的强信号会**覆盖（Overpower）**存储单元内的旧值，完成写入。

### 4.2 SRAM 组织架构与译码逻辑
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


## V. DRAM Technology & Organization 动态随机存储器
DRAM（Dynamic Random-Access Memory）由于其极高的存储密度和低廉的成本，是计算机 **Main memory（主存）** 的绝对主力。

### 5.1 DRAM 基本存储单元特性
不同于 SRAM 的 6T 结构，DRAM 采用极简的 **1T1C结构（单管单电容）**：

**数据存储**：数据以电荷（Charge）的形式存储在微小的电容（Capacitor）中。

**数据访问**：由**单个传输管**（Single transistor）作为开关来访问电容中的电荷，通过 **word line** 激活对应的行，**bit line** 传输电荷信号。 

**破坏性读出与刷新（Refresh）**：

- **读出电荷后，原有的电荷会被破坏**，因此必须在读取后将数据**写回（Write back）**。
- 由于电容存在**天然漏电**，DRAM 单元必须**周期性地进行刷新（Periodically be refreshed）**，这也是 "Dynamic" 的由来。刷新操作通常是以**行（Row）**为单位进行的。

![alt text](image-6.webp)

### 5.2 DRAM 阵列组织与访问模式
DRAM 内部的比特位同样被组织成**矩形阵列（Rectangular array）**，核心访问逻辑是分两步走：先**选中整行**，**再挑出特定的列**。

*   **行级访问**：DRAM 每次访问（Access）都会激活一整个 Row，并将其放入行缓冲区（Column latches / Row buffer）中。
*   **Burst mode (突发模式)**：既然一整行的数据已经被读出到了缓冲区中，如果后续请求的地址是连续的，就可以直接从缓冲区中**以极低的延迟连续提供后续字（Supply successive words with reduced latency）**，而无需再次进行缓慢的内部行读取。
    > **更好的方式**是尽量做到一行中存放想要的数据，这样就不需要多次切换不同行的访问。因为每次访问完一行，电容上的电荷都会损失，需要重新充电（Recharged），这会带来额外的访问延迟。
*   **DDR (Double Data Rate) DRAM**：通过在时钟信号的**上升沿和下降沿**同时传输数据，使得数据传输速率翻倍。

![alt text](image-7.webp)

### 5.3 决定 DRAM 性能的核心因素
现代存储系统通过以下三大核心技术来榨干/提升 DRAM 的性能（特别是提升带宽）：
1.  **Row buffer (行缓冲区)**：允许**并行读取**和刷新多个字，是实现**Burst mode**的物理基础。
2.  **Synchronous DRAM (SDRAM, 同步DRAM)**：配合系统时钟，允许连续的**突发访问**（Consecutive accesses in bursts），**无需为每个字单独发送地址（Without needing to send each address）**，大幅提升了总线**带宽（Bandwidth）**。
3.  **DRAM banking (多体交叉/多Bank结构)**：允许同时（Simultaneous access）访问多个不同的 DRAM Bank，通过并行流水线操作掩盖单一 Bank 漫长的内部访问延迟，成倍提升吞吐量。


### 5.4 Increasing Memory Bandwidth 提升内存带宽的系统架构设计
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


### 5.5 DRAM 物理层级组织与存储器分类

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


## VI. Cache Technology

### 5.1 Cache 基础概念与直接映射机制 (Cache Basics & Direct Mapped Cache)

作为距离 CPU 最近的存储层级，Cache 的核心目标是利用**程序的局部性（Locality）**来弥合 CPU 计算速度与主存（DRAM）读取速度之间的巨大鸿沟。在任何层级的存储器体系中，都需要解决以下四个核心问题：
1. **Block placement（块放置）**：数据块应该放在 Cache 的什么位置？
2. **Finding a block（查找块）**：如何判断数据块是否在 Cache 中？
3. **Replacement on a miss（缺失替换）**：当 Cache 满了且发生 Miss 时，替换掉哪个块？
4. **Write policy（写策略）**：发生写操作时，如何保证 Cache 与**主存**的数据一致性？

#### 5.1.1 直接映射缓存 (Direct Mapped Cache)
直接映射是**块放置（Block placement）**策略中最简单的一种：主存中的每一个数据块，在 Cache 中都有且仅有一个确定的位置可以放置（Only one choice）。

*   **映射规则**：`Cache Index = (Block address) modulo (#Blocks in cache)`
*   **硬件优化**：在实际设计中，为了避免复杂的求余（Modulo）运算，Cache 的块数（#Blocks）通常会被设计为 2 的幂次方。这样求余操作可以直接简化为**截取物理地址的低位（low-order address bits）**作为索引。
*   **特性**：多个主存块会被映射到同一个 Cache 块上（多对一关系）。

#### 5.1.2 标记 (Tag) 与 有效位 (Valid Bit)
由于多个主存块对应同一个 Cache 位置，当 CPU 访问某个 Cache 行时，需要知道当前存储的到底是哪一个主存块，这就是 **Tag（标记）**的作用。

*   **Tag（标记）**：地址的**高位部分（High-order bits）**。将地址的高位与 Cache 行中存储的 Tag 进行比较，**匹配**则说明命中目标主存块。
*   **Valid Bit（有效位）**：1 bit，用于指示当前 Cache 行中**是否包含有效数据**（1 = present, 0 = not present）。上电初始化时，所有的 Valid bit 都应清零。

#### 5.1.3 地址划分与硬件逻辑 (Address Subdivision)
当 CPU 发出一个物理地址时，该地址会被硬件划分为三个字段：

*   **Tag（标记位）**：用于和 Cache 内部存储的 Tag 比对。
*   **Index（索引位）**：用于直接寻址（选中）特定的 Cache 行。它的位宽决定了 Cache 有多少个 Block（例如 6 bit 对应 64 个 Blocks）。
*   **Offset（偏移位）**：包含 Byte offset 和 Block offset，用于确定所需的数据在当前 Block 的具体哪个字节。它的位宽取决于 Block 的大小（例如 **16 bytes/block** 需要 **4 bit** 作为 offset，因为 $2^4 = 16$）。

!!! note "例子分析"
    64 Blocks, 16 Bytes/block 的直接映射 Cache
    假设 CPU 访问十进制地址 `1200`（二进制 `1 001011 0000`）：
    * Offset：16 Bytes 需要 4 bit，所以低 4 位 `0000` 是 Offset。
    * Index：64 个 Block 需要 6 bit，所以紧接着的 `001011`（十进制 11）是 Index。
    * Tag：剩余的高位 `1` 是 Tag。

#### 5.1.4 Miss and Hit

**(1) Hit (命中)**：CPU 去 Cache 中找数据，发现**数据在里面**（硬件判断标准：对应位置的 Valid 位为 1，并且 Cache 里存的 Tag 和 CPU 发出的地址的 Tag 完全一致）。此时 CPU 可以全速继续运行。
**(2) Miss (缺失)**：CPU 去 Cache 中找数据，发现**数据不在里面**（硬件判断标准：对应位置 Valid 为 0，**或者**虽然 Valid 为 1，但存的 Tag 跟 CPU 请求的 Tag 不一样）。此时 Cache 必须去主存搬运数据，CPU 必须停顿等待（Stall）。

对于 8 blocks, 1 word/block 的 Cache

1. 上电前，所有 block 的 **valid** 都是 **N** ；
2. 写入 $22(10110_2)$ 时（冷启动缺失，Cold miss），将 Cache 的第 **110** 个 block 写入地址 **22** 的数据；
3. 写入 $26(11010_2)$ 时（冷启动缺失，Cold miss），将 Cache 的第 **010** 个 block 写入地址 **26** 的数据；
4. 写入 $18(10010_2)$ 时（冷启动缺失，Cold miss），valid = Y，Cache 的第 **010** 个 block 已经存在了地址 **26** 的数据，该数据会被更新为地址 **18** 的数据
5. 访问 $22(10110_2)$ 时，Cache 的第 **110** 个 block 存在数据，**Valid = Y** 且 **tag 成功匹配**，缓存给命中（hit）
6. 访问 $26(11010_2)$ 时，Cache 的第 **010** 个 block 存在数据，**Valid = Y** 但 **tag 不匹配**，**miss**。此时会发生**替换**（replacement），将地址 **18** 的数据替换为地址 **26** 的数据。
7. 访问 $10(01010_2)$ 时，Cache 的第 **010** 个 block 存在数据，**Valid = Y** 但 **tag 不匹配**，**miss**。此时会发生**替换**（replacement），将地址 **26** 的数据替换为地址 **10** 的数据。


#### 5.1.5 Cache Block Size（块大小的权衡）
改变每个 Cache Block 的大小会对性能（Miss rate）产生显著影响，这是一个经典的体系结构 Trade-off：

**增大 Block Size 的好处**：
   - **降低 Miss rate**：能够更好地利用**空间局部性（Spatial Locality）**。因为当你访问地址 A 时，地址 A 附近的数据大概率也会被访问到，**较大的块会一次性将它们全部预取进来**。

**增大 Block Size 的代价（在 Cache 总容量固定的前提下）**：
   -  **增加竞争（More competition）**：块变大了，Cache 能容纳的**块数（Blocks）就会减少**，导致冲突增加，反而可能**提高 Miss rate**。
   -  **缓存污染与伪共享（Pollution & False sharing）**：可能会取来大量根本用不到的数据占用宝贵的 Cache 空间；在多核架构中还会引发缓存一致性问题（False sharing）。
   -  **增加缺失惩罚（Larger miss penalty）**：发生 Miss 时，从主存搬运一整个大块的数据需要花费更长的时间。

**对应的硬件缓解策略**：
   -  **Early restart**：只要 CPU 需要的那个字（Word）到了，就立马恢复 CPU 执行，不等待整个 Block 搬运完成。
   -  **Critical-word-first**：要求内存控制器优先回传 CPU 触发 Miss 的那一个字。


### 5.2 Cache 读写机制与一致性策略 (Cache Misses & Write Policies)

在 Cache 的操作中，“读”相对简单，只会改变 CPU 的流水线状态；而“写”操作因为会改变数据，必须妥善处理 Cache 与底层主存（DRAM）之间的数据一致性（Data Consistency）问题。

#### 5.2.1 缓存读操作 (Cache Read)
**Read Hit（读命中）**：所需数据在 Cache 中，CPU 直接读取数据，全速流水线执行。

**Read Miss（读缺失）**：所需数据不在 Cache 中。
   1. CPU 流水线必须**暂停（Stall）**。
   2. 通知下一级存储（下级 Cache 或主存）将包含该地址的**整个数据块（Block）**搬运到当前 Cache 中。
   3. 数据就位后，CPU 重新启动执行（如果是指令缺失则重启取指，数据缺失则完成数据访问）。

#### 5.2.2 缓存写操作 (Cache Write)
写操作需要分别考虑**写命中（Write Hit）**和**写缺失（Write Miss）**的情况。

##### (1) 写命中 (Write Hit) 的两种策略
当 CPU 要写的数据刚好在 Cache 中时，修改了 Cache 的数据就会导致它与主存的数据不一致。硬件上有两种核心解决流派：

1.  **Write-Through（写通 / 直写）**
    **机制**：每次写 Cache 的同时，也**同步写回主存**，保证上下层数据绝对一致。
    **痛点**：主存写入速度极慢，每次写操作都会严重拖慢 CPU。
    **硬件补救**：引入 **Write Buffer（写缓冲）**。CPU 将数据**同时丢给 Cache 和 Write Buffer** 后即可继续执行下一条指令，Write Buffer 负责在后台将数据慢慢写入主存。（**仅当 Buffer 满时 CPU 才需要 Stall**）。
2.  **Write-Back（写回）**
    **机制**：CPU **只更新 Cache 中的数据**，不马上同步主存。只有当这个 Cache 块**因为冲突被 “踢出（Evict/Replace）” 时，才将它写回主存**。
    **硬件实现**：在 Cache 行中增加一个 **Dirty Bit（脏位）**。数据**被修改时设为 1（Dirty）**。发生替换时，如果 **Dirty=1 则写回主存**；如果 Dirty=0 则直接丢弃当前 Cache 块即可。
    **优点**：极大地节省了内存带宽，适合被频繁修改的局部变量。

##### 2.2 写缺失 (Write Miss) 的两种策略
当 CPU 要写的数据不在 Cache 中时：

1.  **Write-Allocate（写分配）**：先把**包含该地址的整个 Block** 从**主存捞到 Cache 里**，然后再在 **Cache 中对它进行写修改**。
2.  **No Write-Allocate（不写分配）**：直接绕过当前 Cache，将**新数据送到 Write Buffer 最终写入主存**。不把这个 Block 读进 Cache。

---

#### 5.2.3 架构师视角的“黄金搭档” (Typical Combinations)

在实际的 CPU 微架构设计中，上述策略通常按以下两种方式进行固定搭配：

**搭档 1：Write-Back（写回）通常搭配 Write-Allocate（写分配）**

*   **架构师视角的理由**：**利用局部性原理（Locality）**。
*   **场景举例**：比如计算 `x = a + b` 并写入变量 `x` 时发生了 Write Miss。程序在接下来的一小段时间内，极大概率会再次读取或修改这个 `x`。如果趁着这次 Miss 直接把 `x` 捞进 Cache（写分配）并标为脏数据，那么接下来对 `x` 以及它相邻数据的几百次读写，全部都会变成极其快速的 Cache Hit，收益极高。

**搭档 2：Write-Through（写通）通常搭配 No Write-Allocate（不写分配）**
*   **架构师视角的理由**：**避免缓存污染（Cache Pollution）与带宽浪费**。
*   **场景举例**：比如进行大数组的初始化 `for(int i=0; i<100; i++) A[i] = 0;`。此时 CPU 只是无脑向内存塞入初始数据，短时间内并不会去读取它们。如果采用写分配，**不仅每次都要浪费带宽把毫无用处的旧块从内存读出来，还会把 Cache 里原本存着的其他高频热点数据给“挤掉”（缓存污染）**。因此，既然 Write-Through 无论如何都要把数据打向主存，直接绕过 Cache 丢进主存（No Write-Allocate）显然是最明智、最不影响 Cache 命中率的选择。


### 5.3 组相联缓存与降低冲突缺失 (Set Associative Cache)

在直接映射（Direct Mapped）Cache 中，不同的主存地址如果映射到同一个 Index（索引），就会发生频繁的相互驱逐（冲突缺失 Conflict Miss），导致 Cache 性能暴跌（即“缓存颠簸 Thrashing”）。为了解决这一问题，引入了**相联机制**。

![alt text](image-11.webp)

#### 5.3.1 Cache 组织结构的进化史
假设 Cache 总容量固定（例如 8 个 Blocks）：

*   **直接映射 (Direct Mapped / 1-way)**
    **规则**：1 个组（Set）里只有 1 个空位（Block）。总共有 8 个 Set。
    **查找方式**：根据 Index 找到唯一的固定坑位，只进行 **1 次** Tag 比较。
    **特点**：冲突极为严重。
*   **组相联 (Set Associative / N-way)**
    **规则**：将几个 Block 绑在一起作为一个“组”。例如“2路组相联（2-way）”表示 1 个 Set 里有 2 个空位。总 Set 数量缩减为 4 个。
    **地址变化**：因为 Set 数量减半，所以用于寻址的 Index 位宽减少（例如 3位变2位），省下来的位变成了 Tag 的一部分。
    **查找方式**：根据 Index 找到对应的 Set 包厢，然后**并行（同时）使用 2 个比较器**，比对包厢里 2 个 Block 的 Tag。
    **破局点**：之前冲突的数据（例如 18 和 26 映射到同一个 Set），现在可以和谐地共存在这 2 个空位中，完美化解冲突。
*   **全相联 (Fully Associative)**
    **规则**：干脆取消“分组（Set）”的概念。整个 Cache 就是一个拥有 8 个空位的大池子，任何主存数据可以放在**任意空位**。
    **地址变化**：没有 Index，地址除了 Offset 之外，剩下全部是 Tag。
    **查找方式**：由于不知道数据在哪里，必须**并行调用 8 个比较器**，同时对所有 Cache 行进行 Tag 比对。

#### 5.3.2 架构师视角的终极权衡 (The Architectural Trade-off)

选择哪种 Cache 组织方式，是微架构设计中最经典的 Trade-off。这并不是拍脑袋决定的，而是依靠大量的 **软件仿真 (Simulation)**，运行标准基准测试集（如 SPEC CPU）跑出来的综合最优解：

*   **硬件成本与功耗 (Hardware Cost & Power)**：直接映射最低，组相联居中，全相联最高（需要大量并行并行的比较电路）。
*   **查找延迟 (Hit Latency)**：直接映射最快（可以直接选中数据），全相联最慢（需要极其复杂的电路来选通匹配的那一路数据）。
*   **缺失率 (Miss Rate)**：全相联最低（只要 Cache 没满就不发生冲突），组相联居中，直接映射最高。

**最终工业界结论**：

*   **L1/L2/L3 Cache**：绝大多数采用 **N路组相联（Set Associative）**（通常 N = 4, 8, 16），在硬件复杂度和命中率之间取得最佳平衡（Sweet Spot）。
*   **全相联**：由于硬件开销和延迟太大，绝不能用于数据 Cache，仅用于容量极小但极其关键的组件中（如内存管理单元的 TLB 缓存）。


!!! question "多字节block"
    以上我们没有提到的是**多字节block**的写入、读出情况，详见：[多字节block的读写详情](./multi-bytes_block.md)

#### 5.3.3 Associative Caches

**(1) Fully Associative**

- 与直接映射相比的另一个极端
- 允许给定 block 放入任意缓存 entry 中
- 需要同时搜索所有 entry
- 每个 entry 均需比较器（成本较高）

**(2) Set Associative**

- 每个 set 包含 n 个 entry
- block number 决定所属集合  
   - block number %（set 数 in cache）  
   - block address % (block 数 in cache)  
- 同时搜索给定 set 中的所有 entry  
- n 个比较器（成本较低）

案例：

![alt text](image-12.webp)

256 个 sets ，每个 block 1 个 word
因此 address[9:2] 是 block number, address[1:0] 是 block offset, 每一个 block 4 way。
其余 address[31:10] 是 tag。

#### 5.3.4 Replacement Policy 替换策略

- Direct Mapped：没有选择，只有一个 entry 可用
- Set Associative：需要选择一个 entry 进行替换

Set Associative Cache 的替换策略：

- 有没有空的 entry？如果有，直接放入空 entry
- 如果没有空 entry，选择一个 entry 进行替换
   - Random：**随机选择**一个 entry 替换
   - Least Recently Used (LRU)：替换**最近最少**使用的 entry
   - First In First Out (FIFO)：替换**最早进入 cache 的 entry**

**Example**

4-block Cache, three method:

- Direct Map
- 2-way Set Associative
- Fully Associative

Address Seq: 0, 8, 0, 6, 8

**Direct Mapped**

| Address | Cache index | Miss/Hit | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | Miss | <span style="color: red;">Mem[0]</span> |   |   |   |
| 8 | 2 | Miss | <span style="color: red;">Mem[8]</span> |   |  |   |
| 0 | 0 | Hit | <span style="color: red;">Mem[0]</span> |   |  |   |
| 6 | 1 | Miss | Mem[0] | | Mem[6] |   |
| 8 | 2 | Hit | <span style="color: red;">Mem[8]</span> | |  Mem[6] |   |

**2-way Set Associative**

| Address | Cache index | Miss/Hit | set 0-0 | set 0-1 | set1-0 | set1-1 |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | Miss | <span style="color: red;">Mem[0]</span> |  |   |   |
| 8 | 2 | Miss | Mem[0] | <span style="color: red;">Mem[8]</span> |  |   |
| 0 | 0 | Hit | <span style="color: green;">Mem[0]</span> | Mem[8] |  |   |
| 6 | 1 | Miss | Mem[0] | <span style="color: red;">Mem[6]</span> |  |   |
| 8 | 2 | Miss | <span style="color: red;">Mem[8]</span> | |  Mem[6] |   |

**Fully Associative**

| Address | Cache index | Miss/Hit |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | Miss | <span style="color: red;">Mem[0]</span> |  |   |   |
| 8 | 2 | Miss | Mem[0] | <span style="color: red;">Mem[8]</span> |  |   |
| 0 | 0 | Hit | <span style="color: green;">Mem[0]</span> | Mem[8] |  |   |
| 6 | 1 | Miss | Mem[0] | Mem[8] | Mem[6] |   |
| 8 | 2 | Hit | Mem[0] | <span style="color: green;">Mem[8]</span> | Mem[6] |   |

更高的关联度确实能降低缺失率，但**收益呈现递减趋势**

Simulation of a system with 64KB D-cache, 16-word blocks, SPEC2000

- 1-way: 10.3%
- 2-way: 8.6%
- 4-way: 8.3%
- 8-way: 8.1%

### 5.4 Sources of Miss

- Compulsory misses (aka cold start misses) （强制性确实/确实）
  - 首次访问某数据块时发生
  - 当然，如果 block 是多个 word 的话，再次访问同一 block 内的其他 word 时就不会了，因为可以一开始就 load 整个 block 进 cache
- Capacity misses
  - 由**缓存容量有限**导致，典型就是 Fully Associative Cache 满了 
  - 被替换出的数据块后续再次被访问
- Conflict misses (aka collision misses)
  - 发生在**非Fully Associative**中
  - 由**set 内 entry 竞争引发**
  - 在总容量相同的Fully Associative中不会出现

### 5.5 Cache 性能量化分析 (Measuring Cache Performance)

在体系结构设计中，我们不能仅仅凭直觉说“这个 Cache 很快”，而必须用严谨的数学公式将其对 CPU 整体性能的影响量化出来。

#### 5.5.1 CPU 执行时间的拆解 (Components of CPU time)
在引入了 Cache 之后，程序在 CPU 上运行的总时间被拆分成了两部分：
*   **程序执行周期 (Program execution cycles)**：CPU 正常流水线工作的时间。这里面其实**已经包含了 Cache Hit Time（命中时间）**，因为只要命中，CPU 就能全速运行，不需要额外停顿。
*   **内存停顿周期 (Memory stall cycles)**：CPU 因为 Cache Miss 而被迫停下来等待底层数据搬运所消耗的时间。这是拖慢系统性能的核心罪魁祸首。

#### 5.5.2 核心量化公式
为了计算**内存停顿周期 (Memory stall cycles)**，架构师通常使用以下两种等价的计算公式：

**基于访存次数的公式**：

$$\text{Memory stall cycles} = \frac{\text{Memory\ accesses}}{\text{Program}} \times \text{Miss\ rate} \times \text{Miss\ penalty}$$

*(程序的总访存次数 × 缺失率 × 每次缺失带来的惩罚周期数)*

**基于指令数的公式**：
    
$$\text{Memory stall cycles} = \frac{\text{Instructions}}{\text{Program}} \times \frac{\text{Misses}}{\text{Instruction}} \times \text{Miss\ penalty}$$

*(程序的总指令数 × 每条指令产生的平均 Miss 数 × 每次缺失带来的惩罚周期数)*

#### 5.5.3 平均内存访问时间 (AMAT, Average Memory Access Time)
这是评价存储器层级系统性能**最重要、最核心的指标**。它综合了 Hit 和 Miss 的情况，反映了存储系统的平均响应速度。

**AMAT 公式：**

$$\text{AMAT} = \text{Hit\ time} + \text{Miss\ rate} \times \text{Miss\ penalty}$$

*   **Hit time (命中时间)**：去 Cache 中**查找并返回数据的时间**（不管命不命中，这个检查时间都必须花）。
*   **Miss rate (缺失率)**：需要去底层存储找数据的概率（反映了 Cache 结构的抗冲突能力）。
*   **Miss penalty (缺失惩罚)**：一旦 Miss，从**底层存储把 Block 搬运到 Cache 所需的额外时间**（反映了底层 DRAM 的延迟和总线带宽）。

#### 5.5.4 为什么 Cache 性能越来越重要？ (Amdahl's Law 的体现)
随着半导体工艺的发展，CPU 的计算性能在不断飙升，这反而凸显了 Cache 的重要性（即著名的“内存墙 Memory Wall”问题）：

*   **基础 CPI 降低 (Decreasing base CPI)**：随着流水线、超标量等技术的发展，**CPU 自身的 CPI 越来越低**（算得越来越快），这使得“**内存停顿时间**”在总执行时间中所占的**比例变得越来越大**。
*   **时钟频率提升 (Increasing clock rate)**：主频越高，意味着一个时钟周期越短。由于底层主存 DRAM 的绝对物理延迟（以纳秒 ns 计）很难降低，这就导致相同的一次 Miss 请求，在过去可能只惩罚 50 个周期，在现代高频 CPU 中可能会**折算成几百个 CPU 周期的停顿惩罚**。

**结论**：在评估现代计算机系统性能时，绝对不能忽略 Cache 的行为表现。**Cache 哪怕提升了 1% 的命中率，对整体性能的拉动也是极其巨大的**。


### 5.6 多级缓存架构 (Multilevel Caches)

随着 CPU 时钟频率的不断攀升，由于主存（DRAM）的访问延迟难以大幅降低，**单层 Cache 的 Miss Penalty（缺失惩罚）变得极其昂贵（动辄几百个时钟周期）**。为了缓解内存墙问题，现代处理器全面走向了**多级缓存架构**。

#### 5.6.1 各级 Cache 的角色与定位 (Roles of Multilevel Caches)
在多级架构中，不同层级的 Cache 承担着截然不同的历史使命，其设计侧重点也完全不同：

*   **L1 Cache (Primary Cache / 一级缓存)**
    *   **物理位置**：紧贴 CPU 核心。
    *   **架构形态**：通常分为独立的**指令缓存**（L1I）和**数据缓存**（L1D），以支持 CPU 的并行取指和访存。
    *   **设计核心目标**：**极小化命中时间 (Focus on minimal hit time)**。为了让 CPU 全速运行，L1 必须足够快（通常 1~4 个周期），因此它的**容量通常较小**，且**相联度不能太高**（以降低比较电路的延迟）。
*   **L2 Cache (二级缓存)**
    *   **架构形态**：通常为统一缓存（Unified L2 cache），即**指令和数据共享**。
    *   **设计核心目标**：**极小化缺失率 (Focus on low miss rate)**。它的任务是充当主存前的最后一道坚固防线，避免请求掉入龟速的主存中。因此它**容量更大**，且通常采用 **高相联度（Higher associativity）** 以减少冲突缺失。L2 的 Hit time 相对较慢对全局性能影响不大。
*   **L3 Cache 及主存**
    *   高端系统还会引入 L3 Cache。如果请求在 L2 依然 Miss，则由 L3 或主存（Main Memory）来服务。

#### 5.6.2 多级 Cache 性能计算实例 (Performance Example)
我们可以通过一个具体的计算例子，直观感受 L2 Cache 带来的巨大性能收益：

*   **系统预设参数**：CPU 基础 CPI = 1，主频 = 4GHz（1 个周期 = 0.25ns），主存访问延迟 = 100ns（折合 400 个时钟周期）。

**场景 A：只有 L1 Cache**
*   假设 L1 的 Miss rate = 2%。
*   Miss penalty = 100ns / 0.25ns = 400 cycles。
*   **Effective CPI** = **Base CPI + (Miss rate × Miss penalty)** = 1 + (0.02 × 400) = **9.0**

*(原本 CPI 为 1 的 CPU，因为 2% 的缓存缺失，速度直接慢了 9 倍！)*

**场景 B：加入 L2 Cache**

*   假设 L2 的访问延迟 = 5ns（折合 20 个周期）。引入 L2 后，全局缺失率（Global miss rate to main memory，即 L1 和 L2 都没命中的概率）降为 0.5%。
*   **此时的惩罚分为两级**：
    1. L1 Miss 但 L2 Hit 的惩罚 = 20 cycles
    2. L1 Miss 且 L2 也 Miss 的额外惩罚 = 400 cycles
*   **Effective CPI** = **Base CPI + (L1 Miss Rate × L2 Hit Penalty) + (Global Miss Rate × Main Memory Penalty)** 
    = 1 + (0.02 × 20) + (0.005 × 400) = 1 + 0.4 + 2.0 = **3.4**

**结论**：仅仅加入了一个延迟为 5ns 的 L2 Cache，就让整个 CPU 的性能提升了 **2.6 倍 (9.0 / 3.4)**！这就是多级 Cache 的威力。

#### 5.6.3 架构设计探讨 (Considerations)
基于多级体系，微架构师还需要决定：

*   **Block Size 差异**：L1 和 L2 的 Block size 是否应该一样？通常 L2 的 Block size 会更大，以利用空间局部性。
*   **包含策略 (Inclusive or not)**：
    *   *Inclusive（包含）*：L1 中的数据必须同时也存在于 L2 中（L2 是 L1 的超集）。
    *   *Exclusive（排他）*：L1 和 L2 的数据互不重叠，L1 踢出的脏数据会被塞进 L2，以**最大化总有效容量**。


### 5.4 Interactions with Advanced CPUs

- **cache miss 期间的乱序执行 (Out-of-order execute during cache miss)**
  - 待处理存储指令 (Pending store) 保留在 load/store unit 中
  - 相关指令 (Dependent instructions) 在 reservation stations 中等待
  - **无关指令 (Independent instructions) 继续执行**
- **非阻塞缓存 (Non-blocking cache)**
  - 支持 `Hit under miss` 或 `Miss under miss`
- **支持多发射 (Supporting multiple issue)**
  - 多体缓存 (Multi-banked caches)：在无存储体冲突 (bank conflicts) 的情况下，每个周期支持多次访问
- **数据预取 (Data prefetching)**
- **缓存失效的影响取决于程序数据流 (Effect of miss depends on program data flow)**
  - 分析难度大幅提升
  - 需使用系统仿真 (system simulation) 进行评估


### 5.5 Example: Software Optimization via Blocking

典型案例：矩阵乘法

- 常用于科学计算、机器学习等领域
- 适合用硬件和软件优化，而其他算子很难用硬件优化

矩阵乘法：

$$X=YZ$$

$X[i][j]$ 需要用到 $Y[i]$ 行与 $Z[j]$ 列的所有元素进行计算，因此访问模式具有**空间局部性**，适合 Cache 优化。

但是，如果内存是按照行存储矩阵的话，那么：

- 访问 $Y[i]$ 行具有空间局部性，Cache **命中率高**
- 访问 $Z[j]$ 列没有空间局部性，Cache **命中率低**

因此导致矩阵计算的时候，会有大量 miss，性能极差。

**解决方法**：**Blocking（分块）**
![alt text](image-14.webp)

分块，每一块的元素都很少，可以**完全放入 Cache 中，充分利用空间局部性，极大提升性能**。

![alt text](image-15.webp)