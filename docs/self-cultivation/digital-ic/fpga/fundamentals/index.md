# FPGA Fundamentals

## I. Concepts

### 1.1 Programmable Logic

#### (1) Logic Cells


Logic Cell(LC, 或者也叫做 System Logic Cell/SLC)是一个行业标准化的等效容量单位，**不是芯片上一个真实、独立的硬件原语**。它的标准定义：**1 个 4 输入 LUT + 1 个配套触发器 FF，再加内部进位多路选择器等附属电路**。
> LUT、DSP、BRAM 是**真实硬件资源**；Logic Cell 是**归一化后的等效计数单位**，主要用来跨厂商对比FPGA规模。

即行业约定：**1 LC = 1×LUT4 + 1×FF + carry/mux**

哪怕芯片内部实际是 LUT6(Xilinx), ALM(Intel), PFU(Lattice)，厂商都要把自己真实资源折算成这个标准 LC 数字写在datasheet，方便客户横向对比容量。此外，这个指标代表整个器件的通用逻辑 Fabric 总等效容量，**不含 DSP、Block RAM、硬核IP**。

### 1.2 Memory

> *Note: 以下仅针对 AMD/Xilinx FPGA，尤其是以 2026-11-21 调研的 Versal 架构系列*。

**FPGA Resources 案例（AMD Versal Premium Series Gen2 系列）**

![alt text](assets/image.webp)

##### (1) Total PL Memory

“Total PL Memory”指的是**可编程逻辑（PL）区域内部集成的、用于构建自定义硬件逻辑的静态存储器（SRAM）资源**。它不是用于运行操作系统或存储大容量数据的“主存”，而是 FPGA 架构中实现数据缓冲、查找表、FIFO 等功能的基石。

AMD 官方文档明确给出了它的构成公式：

> **Total PL Memory = 分布式RAM (Distributed RAM) + 块 RAM (Block RAM) + 超大容量 RAM (UltraRAM)**

这三种存储器的特点如下：

- **Distributed RAM**：分布在逻辑单元之间，粒度最细，灵活但容量小。
- **Block RAM**：独立的存储块，容量适中，是 PL 中最常用的存储资源。
- **UltraRAM**：Versal 架构特有的高密度存储块，提供大容量、高带宽的片上缓冲。

因此，“Total PL Memory”反映的是**芯片内部可供硬件设计使用的存储资源总量**，单位是**兆位（Mb）**，与外部 DRAM 或封装内存是完全不同的概念。

##### (2) Integrated Memory on Package

“Integrated Memory on Package”（封装内集成内存，简称**MoP**）则完全不同。它指的是 AMD 将**LPDDR5X DRAM芯片直接集成到了自适应SoC的封装内部**，而非作为PL逻辑资源存在。

MoP方案的核心特点是：

- **本质是外部主内存**：它提供的是系统运行所需的大容量、高带宽 DRAM，容量可达**32 GB**，带宽预计高达**288 GB/s**。
- **消除板级设计复杂度**：由于内存已在封装内完成集成和验证，用户无需在电路板上进行高速内存布线，可节省高达**60%**的板级面积，并降低设计风险。
- **面向特定型号**：MoP 并非所有 Versal Premium Gen 2 型号的标配，而是专门为型号后缀带“**22**”的器件（如2VP3422、2VP3522、2VP3622）提供的选项。

##### (3) 板载独立 DRAM

不同于 MoP，Versal Premium Gen 2 标准型号的“主存”**并非来自芯片内部，而是依赖于板级设计**：通过在 PCB 上布置**独立的 DDR5/LPDDR5X 内存芯片**，并连接到 Versal 芯片的**硬核 DDR 内存控制器**来实现。

##### (4) OCM

图中 Processing System 栏目的 256KB 存储器是**片上存储器（On-Chip Memory, OCM）**，它是一块集成在芯片内部、带有 **ECC（纠错码）** 功能的小容量高速 SRAM。

与之前的“Total PL Memory”（PL 内部的块 RAM 等）不同，是**专门服务于处理器系统（PS）** 的紧耦合存储资源。它的核心作用包括：

*   **极低延迟的暂存区**：为 PS 提供**访问速度远快于外部 DDR 的数据暂存空间**，用于存放关键代码、中断向量表或临时数据，以减少访问延迟。
*   **确定性的实时数据缓冲**：对于 RPU 处理的硬实时任务，OCM 可以提供**时序高度确定**的数据缓冲，避免因访问外部共享内存而产生的不可预测延迟。
*   **核间通信的共享内存**：APU 和 RPU 都可以访问这块 OCM，因此它常被用作两个异构处理单元之间进行低延迟数据交换的“共享信箱”。
*   **ECC 保障可靠性**：集成的 ECC 功能可以自动检测并纠正单比特错误，这对于在工业、汽车等对可靠性要求高的场景中运行关键代码至关重要。

所以，这 256KB 是 PS 内部一个**小而快、且高度可靠**的“贴身”存储层，与用于扩展容量的外部 DRAM 在角色上完全不同。

### 1.3 Connect

- PS 外设接口：`EtherNet`, `SPI`, `I2C`, `UART`, `CAN`, `USB`等。这些接口通常用于**连接低速、控制类的器件**（如传感器、调试串口、存储卡等），其控制器硬核集成在 PS 附近，通过 MIO（多功能 I/O）等引脚直接引出。
- 系统级高速接口：`PCIe`, `CXL` 等，用于连接 GPU、加速卡、NVMe 存储或 CXL 内存扩展模块等**高带宽、对延迟敏感的设备**，其数据通路需要直接对接芯片的 CPM6 硬核和专用的高速收发器（GTM2），而非通过 PS 的通用外设总线。
