# DRAM Structure Organization

## I. Introduction

从软件看来，Memory 是一个类似：

```text
Memory[0]
Memory[1]
Memory[2]
...
```

的一维线性空间。但真实 DRAM 更接近：

```text
Channel
 └── DIMM
      └── Rank
           └── Chip
                └── Bank
                     └── Row
                          └── Column
```

也就是说，我们在 CPU 那里看到的：`PA=0x12345678`，最终可能被映射成：

```text
Channel = 1
Rank    = 0
Bank    = 5
Row     = 0x1234
Column  = 0x38
```

所以软件空间地址与物理 DRAM 地址之间存在 Address Mapping。

接下来，我们从最底层的 DRAM Cell 开始，逐步向上分析 DRAM 的层次结构。

## II. DRAM 的层次结构

### 2.1 DRAM Cell

一个 DRAM bit 的经典结构是：1 Transistor + 1 Capacitor，如图：

![DRAM Bit Cell](./assets/image-1.webp)

Capacitor 是否存储电荷表示 `1` 或 `0`。

电容会漏电，因此**需要定期 Refresh（刷新）**——这就是 DRAM 名称中 **Dynamic** 的来源之一。

### 2.2 按 Row 和 Column 的组织

假设有一大片 DRAM Cell: 

```
          Column
       0 1 2 3 4 ...
Row 0  □ □ □ □ □
Row 1  □ □ □ □ □
Row 2  □ □ □ □ □
Row 3  □ □ □ □ □
...
```

它不是每次只访问一个 bit，实际访问过程可以粗略理解为：

1. 先选一整行 Row
2. 整行数据进入 Sense Amplifier / Row Buffer
3. 再从 Row Buffer 中选择 Column

之所以会有这样的访问方式，是因为 DRAM Cell 的 Row & Column 组织方式：

DRAM Cell 的 **Word Line (字线)** 与 **Row (行)** 对应，**Bit Line (位线)** 与 **Column (列)** 对应。具体来说：

#### Word line 与 Row

Word Line 是横向贯穿存储阵列的控制线，**每一根 Word Line 唯一对应一个 Row**。

- **物理连接**：同一个 Row 上所有 DRAM Cell 的 **访问晶体管栅极（Gate）** 都连接到同一根 Word Line。当这根 Word Line 被 **激活（施加高电压）** 时，该行上所有 Cell 的晶体管会同时导通。
- **操作粒度**：DRAM 的激活操作是**以 Row 为单位**的。**Row Decoder** 根据行地址选中并驱动一根 Word Line，从而j激活整行。

正因为一根 Word Line 能一次性激活一整行的所有存储单元，所以“共享同一根 Word Line 的 Cell 集合”就被定义为一个 **DRAM Row**。

#### Bit Line 与 Column

Bit Line 是纵向贯穿存储阵列的数据线，**每一根（或每一对）Bit Line 唯一对应一个 Column**。

- **物理连接**：同一个 Column 上所有 DRAM Cell 的**访问晶体管漏极（Drain）**都连接到同一根 Bit Line。当某行的 Word Line 激活后，栅极处于高电平，晶体管导通，该行 Cell 内的电容电荷就会与各自所在列的 Bit Line 发生**电荷共享**，从而被读出。
- **数据通路**：Bit Line 负责将存储电容中的微弱信号送往**灵敏放大器（Sense Amplifier）**进行放大，最终输出为数字 0 或 1。
- **列选择**：虽然激活是整行发生的，但数据输出时，**Column Decoder** 会通过**列选择信号（CSL）**，从被激活的整行中，仅**选中所需要的那一列（或几列）**的 Bit Line 数据送到 I/O 总线上。

> 在现代 DRAM 的层次化结构中，为了降低功耗和延迟，上述“Word Line 对 Row、Bit Line 对 Column”的关系在子阵列（Subarray）层面依然严格成立，只是命名上可能演化为 **Local Word Line / Local Bit Line** 等变体。

所以 DRAM 访问天然具有**两阶段性质**：**Active Row → Access Column**。

并且，我们不难注意到上述访问方式有一个**严重限制**：**不能同时激活多行**！

!!! Warning "不能同时激活多行"
    一列的所有 DRAM Cell 是共享同一根 bit line 的吗？如果是这样，那么**一次访问开启多行的时候，然后读取同一列的数据？是否会出现错乱？还是说不允许这种操作？**

    ——没错，就是不允许这种操作！这确实是 DRAM 架构中一个关键的限制。**一列的所有 DRAM Cell 确实共享同一根 Bit Line，但同时激活多行并读取同一列是绝对不允许的**，这会直接导致数据错乱。

    在同一个 DRAM Bank 内，每一列只有一根（或一对差分）Bit Line，垂直贯穿整个阵列，连接着该列上所有 Row 的 DRAM Cell。当一行被激活时，该行所有 Cell 的电荷会同时“共享”到各自连接的 Bit Line 上，这个过程称为 **Charge Sharing**。**Sense Amplifier** 随即检测 **Bit Line 上微小的电压变化**，并将其**放大**为完整的逻辑电平。

    如果尝试在同一 Bank 中同时激活两行，那么这两行位于同一列的 Cell 会**同时向同一根 Bit Line 放电**——Bit Line 上的最终电压将取决于两个 DRAM Cell 电荷的“竞争”结果。
            
    - 如果两个 Cell 存储的值相同（都是 1 或都是 0），Bit Line 的电压可能勉强能被正确识别；
    - 但如果一个存 1、一个存 0，它们会相互中和，导致 Bit Line 的电压处于一个模糊的中间态。**灵敏放大器无法判断这个中间电压代表的是 0 还是 1，读出的数据就是随机的、错误的**。     

    正因为这种物理上的冲突，**DRAM 的基本协议从架构上就禁止这种操作**。

!!! Attention "Precharge 与访问完整物理流程"
    从外部看，“行激活”只是给Word Line（字线）一个高电平，但在器件物理层面，这个高电平是一系列精密物理过程的触发器。而 **Precharge（预充电）** 正是为这个触发过程搭建一个确定、可复现的初始物理状态。

    我们考虑如下这一场景：存储电容为 $C_s$，**行激活前**电压 $V_{\text{cell}}$; 位线电容为 $C_{BL}$，**行激活前**电压：$V_{BL}$。我们假设晶体管是理想晶体管，导通电阻为 0，那么**行激活后**，两个电容达到相同电压：

    $$V=\frac{C_{s}V_{\text{cell}}+C_{BL}V_{\text{pre}}}{C_{s}+C_{BL}}$$

    那么位线电容的电压变化为：

    $$\Delta V_{BL}=\frac{V_{\text{cell}}-V_{\text{pre}}}{1+C_{BL}/C_{s}}$$

    通常来说，位线电容 $C_{BL}$ 远大于存储电容 $C_s$，所以 $\Delta V_{BL}$ 会相对较小。这个电压变化极其微弱，**通常只有几十到一百多毫伏**。这就是为什么单纯的“高电平”远远不够，必须要有后续的 **Sense Amplifier** 来将这个微小差异放大成完整的逻辑电平。

    **Precharge** 的核心目的，就是为上述微弱的电荷共享过程，创造一个确定、均匀且已知的**初始条件**。**简单来说，就是提供一个稳定的、确定的 $V_{\text{BL}}$**。如果没有Precharge，位线电压将处于不可预测的浮动状态，**微弱的信号将完全被噪声淹没**。

    **Precharge 的物理过程**可以总结为：通过 Precharge电路，将**一对互补位线（BL和/BL）短接**，使它们的**电位强制相等**，通常为：$V_{DD}/2$，这是一个**精妙的平衡**。无论电容存储的是**高电平（接近 $V_{DD}$）**还是**低电平（接近0V）**，电荷共享后，位线电压都会从 $V_{DD}/2$ 这个“中点”**向两个方向产生对称的偏移**。这能**最大化灵敏放大器可检测的初始电压差**。

    结合上述物理过程，一次DRAM读取在器件层面的完整图景是：

    1.  **Precharge**：位线对（BL, /BL）被均衡并预充到 \(V_{DD}/2\)。此时，字线处于关闭状态，存储电容 \(C_S\) **与外界隔离**，保持着数据电荷。
    2.  **行激活与电荷共享**：字线被拉至高电平，该行所有存取晶体管导通。每个存储电容 \(C_S\) 与自己的位线 \(C_{BL}\) 发生**电荷共享**，导致位线电压产生一个微小的、依赖存储数据的偏移（高于或低于\(V_{DD}/2\)）。
    3.  **灵敏放大**：灵敏放大器被激活，它本质上是一个**正反馈锁存器**。它检测到BL和/BL之间微小的电压差，通过正反馈迅速将这个差异**放大并锁存**：电压稍高的一侧被拉至 \(V_{DD}\)，稍低的一侧被拉至地（GND）。
    4.  **数据再生**：在灵敏放大过程中，被拉至满幅（\(V_{DD}\)或GND）的位线电压会**反过来给存储电容\(C_S\)充电或放电**，将其**电荷状态恢复到读取前的水平，补偿了电荷共享造成的损失**。这正是DRAM“破坏性读出”后“再生”的物理机制。


#### Row Buffer

假设 Bank 中存在 `Row 100`, `Row 101`, `Row 102` ...

当前已经打开 `Row 100`，它的数据已经被放入 **row buffer**。

这时访问 `Row 100, Column 10`，然后又访问 `Row 100, Column 20`，**第二次访问就相对快**。这称为：**Row Hit**。因为当前需要的 row 已经是 **open row**。

如果访问 `Row 101`，那么通常需要：

> *关闭 Row 100 → **Precharge** → Activate Row 101 → Access Column*

这种情况称为：**Row Conflict**。

所以 Row Hit 通常明显快于 Row Miss / Row Conflict，这也是为什么 DRAM **访问延迟并不是一个完全固定的数字**。

### 2.3 Bank

上述 Row 和 Column 的组织方式决定了一块区域不能同时激活多个 Row，否则会出现 bit line 紊乱。

如果整个 DRAM 只有一个大 Row Buffer，那么就会出现这种情况

> Access Row A → Waiting →
> Access Row B → Waiting →
> Access Row C → Waiting ...

**并行性非常差**，所以 DRAM 被进一步划分成多个 **Bank**。

例如：

```
DRAM
 ├── Bank 0
 ├── Bank 1
 ├── Bank 2
 ├── Bank 3
 ├── Bank 4
 ├── Bank 5
 ├── Bank 6
 └── Bank 7
```

每个 Bank 有自己的 Row Buffer。因此可以做到：

- Bank 0 正在 activate
- Bank 1 正在传输数据
- Bank 2 正在 **precharge**
- Bank 3 正在等待

这就是：**Bank 级并行（Bank-Level Parallelism, BLP）**


!!! Note "Latency 与 Bandwidth"
    Bank 数量增加，**并不意味着单次访问延迟变短**。它主要提高并行处理多个 memory requests 的能力。也即 **Latency 和 Bandwidth** 的区别。
    多 Bank、多 Channel 主要是在提高带宽。
    假设一个 memory request：`load A` 需要 80ns。

    如果只能串行：`Access A -> Access B -> Access B`，吞吐量会很低。

    但是如果存在多个 Bank，就可以：

    - Bank 0: Access A
    - Bank 1: Access B
    - Bank 2: Access C
            
    很多访问就可以 overlap，于是**单次 latency 依旧很高，但是总 Throughput 会提高**。

### 2.4 DRAM Chip

一个 DRAM Chip 通常包含多个 Bank，每个 Bank 有自己的 Row Buffer 和 Column 结构。

所以到目前为止的层次化结构为：`chip -> bank -> row -> column`。

但是**一个 DRAM Chip 并不一定一次提供完整的 64 bit CPU memory bus 数据**。

例如很多 DRAM 芯片可能是：`x4`, `x8`, `x16` ... 这里的 `x8` 表示一个 DRAM Chip **每次提供 8 bit 数据**。

于是需要多个 DRAM chip 并行工作，例如 8 × `x8` chips 可以形成 64-bit 的数据宽度。

### 2.5 Rank

**上述共同工作的**、**一次给出完整数据**的多个 DRAM chips 称为一个 **Rank**。

概念上：

```
Rank 0
Chip0 Chip1 Chip2 Chip3 Chip4 Chip5 Chip6 Chip7
  │     │     │     │     │     │     │     │
  └─────┴─────┴─────┴─────┴─────┴─────┴─────┘
                  64-bit
```

因此 **Rank 是一组同时响应同一组 memory command、共同提供一个完整数据宽度的 DRAM chips**。

!!! Question "x8 的 8bit 来自几个 Bank、来自几个 ROW？"
    比如 CPU load A 想要一个 64bit 的数据，那么其中分配给 DRAM chip 0 的是 A[0:7]，那么：

    1. 这 8 个 bit 是**由多个 Bank 给出的还是一个 Bank 给出的**？
    2. 如果是一个 Bank ，那么**是一个 Row 同时给出 8bit 还是多个 Row 共同给出 8bit**？

    结论是：对于一次64位的 CPU Load，分配给单个 x8 DRAM 芯片的那 8 位数据，**通常来自该芯片内部的一个Bank**，并且是在**一次行激活**后，从同一行中通过**突发传输（Burst）连续**读出的。

    更具体地来说：

    在现代 DRAM 中，一个Bank内部**一次列访问**产生的数据量**通常是64位（或128位）**。例如 x8 芯片对外的**数据引脚（DQ）是 8 位宽**，但其**内部存储阵列（Bank）到 I/O 逻辑的数据通路**要宽得多（64bit）。
    这种设计被称为 **8n 预取架构**。以 DDR3 x8 为例，芯片内部一次性从存储阵列中**并行读出 64 位数据**，然后通过一个**多路复用器**，将这64位数据**拆分成8个连续的8位块**，在外部时钟的驱动下，通过**8 根 DQ 引脚依次串行输出**。

### 2.6 DIMM

DIMM, Dual In-line Memory Module，双列直插内存模块。是一种**将多个 DRAM chips 安装在 PCB 上，并带有金手指接口的内存模块**。一个 DIMM 可以有多个 Rank，例如：

- DIMM
    - Rank 0
    - Rank 1

物理上，DIMM 包含：

```
DIMM
 ├── DRAM Chips
 ├── SPD EEPROM
 ├── PCB
 └── 其他电气结构
```

其本质就是把多颗 DRAM 芯片组织成标准化内存模块。

### 2.7 Channel

现在来到了 Memory Controller 级别，一个 Memory Controller 可以有多个 Memory Channel，每个 Channel 通常拥有相对独立的数据传输资源。

```
Memory Controller

Channel 0 ── DIMM
Channel 1 ── DIMM
Channel 2 ── DIMM
Channel 3 ── DIMM
```

多个 Channel 可以并行工作，例如：

- Channel 0: Access A
- Channel 1: Access B
- Channel 2: Access C
- Channel 3: Access D

这就是**通道级并行（Channel-Level Parallelism, CLP）**。


## III. Memory Controller

Memory Controller (MC) 是 CPU 与 DRAM 之间的核心枢纽，它负责将 CPU 发出的**64位物理地址**翻译成 DRAM 能理解的 **Channel → Rank → Bank → Row → Column** 命令序列，并高效地调度这些命令。

Memory Controller 的主要功能包括：

1. **地址解码**：MC 内部有可编程的地址映射逻辑，负责将统一的物理地址空间“切分”成不同的位段，分别对应 Channel、Rank、Bank、Row 和 Column。
2. **命令调度与重排序**：MC 维护一个**命令队列 (Command Queue)**，它会根据 DRAM 的时序约束（如 tRAS, tRP, tCAS 等）和当前 Bank 状态（Row Buffer 是否命中），对读写请求进行**重排序 (Re-ordering)**，以最大化吞吐量、最小化延迟。
3. **刷新管理**：DRAM 电容会漏电，MC 内的**刷新逻辑** 会周期性地生成自动刷新命令，在后台维持数据完整性，无需 CPU 干预。
4. **多核仲裁**：当多个 CPU 核心同时请求内存时，MC 中的**仲裁器 (Arbiter)** 负责在命令队列和刷新逻辑之间进行选择，公平且高效地分配内存带宽。

这里我们着重介绍**物理地址解码功能**。

### 3.1 物理地址解码

物理地址解码是将一个 64 位的线性地址，按照**从低位到高位**的顺序，切分成若干段，每一段对应 DRAM 层次结构中的一个特定组件。

一个典型的解码层次结构如下（从低位到高位）：

**Byte Offset → Column → Bank (Group) → Rank → Row**

*   **Byte Offset (字节偏移)**：地址的最低几位用于在**一个数据总线宽度**（如64位=8字节）内定位具体字节。对于64位总线，最低 **3 位**（\(2^3=8\)）就是字节偏移。
*   **Column (列地址)**：接下来的一段用于选择 Bank 内的列。列地址位宽决定了**每个 Row 中有多少个可寻址的“数据块”**。
*   **Bank (Bank 地址)**：Bank 地址位用于在 Rank 内选择具体的 Bank。其位宽由 Rank 内 Bank 的数量决定（例如，8 个 Bank需要 **3 位**）。
*   **Rank (Rank 地址)**：如果系统有多个 Rank，还需要一段地址来选择目标 Rank。
*   **Row (行地址)**：剩余的最高位地址段用于选择 Bank 内的 Row（页面）。这是地址中**位宽最宽**的部分，决定了每个 Bank 有多少行。

> **注意**：这个切分顺序并非绝对固定。**Column 地址有时会被拆分成高、低两部分，分别放在 Bank 地址的两侧**，以实现更精细的交错策略。

!!! Question "为什么地址解码中，没有 DRAM Chip 层级？"
    因为**同一个 Rank 内的所有 DRAM Chip 是并行、同时被选中**的—— Rank，本身就是一组 DRAM Chip。

    例如，**8 颗 x8 DRAM Chip 组成一个 64-bit Rank**。

    当 CPU 请求一个 64 位数据时：

    1. **命令与地址广播**：内存控制器向这个 Rank 发出**同一套** Command、Bank Address、Row Address、Column Address 信号。这 8 颗 Chip 的**地址引脚是并联**的，它们**同时收到完全相同的地址**。
    2. **同时激活**：8 颗 Chip 各自**在自己的对应 Bank 中激活对应的 Row**，同时进行电荷共享和灵敏放大。
    3. **各贡献 8 位**：每颗 Chip 通过自己的 8 根 DQ 引脚输出 8 位数据。
    4. **硬连线拼接**：在 PCB 或 DIMM 上，Chip 0 的 8 根 DQ 连接到数据总线的 **DQ[7:0]**，Chip 1 连接到 **DQ[15:8]**，……，Chip 7 连接到 **DQ[63:56]**。这个映射是**物理布线固定死的，不需要任何地址位来“选择”哪颗 Chip 输出哪一段**。

    所以，**Chip 之间的分工是由数据总线的物理走线决定的，而不是由地址解码决定的**。地址解码只负责在 **Channel、Rank、Bank、Row、Column** 这些维度上做选择；一旦 Rank 被选中，Rank 内所有 Chip 就作为一个整体同时工作。

!!! Question "Channel 层级为什么通常不会放在地址最高位？"
    这是体系结构中一个很漂亮的设计思想。
    假设：

    - `0x00000000` ~ `0x3FFFFFFF` → Channel 0
    - `0x40000000` ~ `0x7FFFFFFF` → Channel 1
    
    那么连续数组：`A[0], A[1], A[2], A[3]...` 它们的 PA 的高位地址通常是相同的，因此 CPU 很可能长期只访问：Channel 0，**这会浪费其他并行 Channel 的带宽**。

    因此 Memory Controller 通常会做：**Memory Interleaving**，将连续的地址**映射到不同的 Channel** 上，从而**充分利用多通道并行性**。

#### 地址映射的灵活性与交错策略

上面的例子展示的是一种**物理布局**。但在真实系统中，MC 的地址映射是**高度可配置**的，其核心目的是优化**并行性**。这通过**交错 (Interleaving)** 技术实现：

* **Channel Interleaving**：例如上述例子。
*   **Cache-line Interleaving**：将连续的 Cache Line 分散到**不同的 Bank** 中。这样，CPU 连续访问相邻地址时，请求**会并行地发往多个 Bank**，从而隐藏单个 Bank 的**行激活延迟**，提升带宽。
*   **Row Interleaving**：将连续的地址映射到**不同的 Bank 的相同 Row** 中，这同样是为了并行化访问。

此外，现代 MC 还会使用**XOR 加密/散列**的方式，将部分高位地址位（如 Row 位）与低位地址位（如 Bank 位）进行异或运算，来生成最终的 Bank 地址。这可以**打散**规律性的访问模式，避免“Bank 冲突”（多个请求同时命中同一个 Bank），是一种更高级的交错技术。

### 3.2 请求调度

MC 不会严格按照 Memory 访问请求的到来顺序进行处理，而是会考虑 Re-ordering。

例如 CPU 依次发出如下访问请求：

- Req A → Bank0 Row10
- Req B → Bank0 Row10
- Req C → Bank0 Row11
- Req D → Bank0 Row10

如果严格按照顺序处理，那么：A 和 B 会开启 Row 10，但是 C **会关闭 Row 10，开启 Row 11**，这又会涉及到 Precharge → Activate → Access Column 的完整流程，**延迟会很高**。Memory Controller 完全可以重排序为：

- Req A → Bank0 Row10
- Req B → Bank0 Row10
- Req D → Bank0 Row10
- Req C → Bank0 Row11

这样就可以增加：**row buffer hit rate**，掩盖 **row activation latency**，提高吞吐量。

一个经典的调度策略就是 **FR-FCFS（First Ready -  First Come First Serve）**，粗略理解是：

- 优先选择**已经 Ready** 的 Row hit
- 其次再考虑**到达时间**

这样可能可以提高这样提高 memory throughput，代价是可能带来 fairness 的问题，例如某些 Bank 的请求**可能会被长期延迟**。

## Appendix

1. Cache Hierarchy 要求发生 miss 时从 Memory 一次性读取一个 Cache Line 的数据。这个 Cache Line 通常不一定是一个字（例如 64bit），可能包含多个字（例如 4 个）。那么这总共多个字（例如 256 bit 的数据）如何“一次性”由 DRAM 给出？一个 Rank 一次不是只能提供 64bit 的数据吗？
2. 什么叫做按照 Cache Line 的粒度，组织 Memory？