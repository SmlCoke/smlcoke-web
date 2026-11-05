# Host-Device I/O Fundamentals

## I. FPGA 的 DMA Engine 和 BAR 寄存器到底“长什么样、在哪里”

关键在于理解 FPGA 内部**硬核（Hard IP）区域**与**可编程逻辑（PL, Programmable Logic）区域**的分工。下面用一个具体例子来展开。

### 1.1 FPGA 内部的两层结构

以 Xilinx UltraScale+ 为例，FPGA 内部大致可以分成两类资源：

| 区域 | 物理形态 | 特点 | 典型内容 |
|:---|:---|:---|:---|
| **硬核区域** | 专用硅片电路 | **出厂固定，不可编程修改** | PCIe 硬核（含 PHY、链路层、事务层、配置空间）、GTY/GTM SerDes、DDR 控制器、BRAM/URAM 存储块 |
| **可编程逻辑（PL）** | 查找表（LUT）、触发器（FF）、布线资源 | **由用户 RTL/IP 综合后配置** | 用户逻辑、DMA Engine 软 IP、AXI 互联、自定义寄存器、AXI4-Lite Decoder |

**DMA Engine 属于 PL 区域**——它是一块用 LUT、FF、BRAM 搭建出来的**硬件电路**，但它是**软 IP（Soft IP）**，也就是说，它的功能由你综合进 FPGA 的 RTL 代码决定，可以按需修改、替换或删除。

---

### 1.2 DMA Engine 的存在形式

**它是一块硬件电路，但是一块“可编程配置出来的硬件电路”**，而不是像 PCIe 硬核那样出厂就固化好的。

以 Xilinx 的 **QDMA** 或 **XDMA** 为例：

- 你在 Vivado 中例化一个 QDMA IP 核，设置通道数、队列深度、BAR 大小等参数；
- Vivado 把这些配置综合成**具体的 LUT/FF/BRAM 电路**，布局布线到 FPGA 的 PL 区域；
- 上电加载 bitstream 后，这块电路就“存在”于 FPGA 内部了，CPU 可以通过 BAR 空间读写它的寄存器来控制它；
- 如果修改了 QDMA 的参数或替换成别的 DMA IP，重新综合、重新加载 bitstream，**这块电路的形态就变了**。

所以准确的说法是：

> **DMA Engine 是 PL 区域中的一块软 IP 硬件电路，由 RTL/IP 综合而来，可以通过重新配置 FPGA 改变其功能。**

它不同于 ASIC 中出厂固化的 DMA 控制器，也不同于 CPU 上运行的一段软件程序。

---

### 1.3 BAR 寄存器的位置

BAR 寄存器要分两层来看，这是最容易混淆的地方：

#### (1) BAR 配置寄存器（BAR Configuration Registers）

这些寄存器定义“这个 BAR 有多大、是 MMIO 还是 I/O、是 32 位还是 64 位地址”等信息。它们位于 **PCIe 硬核的配置空间（Configuration Space）** 中，属于**专用硅片**，出厂固定，不可通过 PL 修改。

CPU 在枚举阶段通过配置空间读写这些寄存器，操作系统据此为 BAR 分配 CPU 物理地址范围。

#### (2) BAR 空间中的目标寄存器（BAR Target Registers）

这些是 CPU 通过 MMIO 实际读写的那批寄存器，比如：

- DMA Engine 的控制寄存器（启动、停止、队列基地址、中断使能等）；
- 用户逻辑的状态寄存器、配置寄存器；
- 中断相关寄存器。

这些寄存器**不在 PCIe 硬核内部**，而是由 **PL 区域中的软逻辑**实现的：

- 如果访问的是 DMA Engine 的寄存器，它们位于 **DMA Engine 软 IP 内部**的寄存器组中；
- 如果访问的是用户自定义寄存器，它们位于**用户逻辑模块**中；
- 它们通过 **AXI4-Lite 从接口**暴露给 PCIe 硬核，由 AXI4-Lite Decoder 根据地址路由。

---

### 1.4 Example: A MMIO Operation

假设 FPGA 设计如下：

- PCIe 硬核（Hard IP）位于专用硅片区域；
- PL 区域中例化了 **QDMA IP** 和 **用户逻辑模块**；
- BAR0 映射到用户逻辑的 AXI4-Lite 从接口；
- BAR2 映射到 QDMA 的 AXI4-Lite 从接口。

CPU 执行一次写操作 `write(BAR0_base + 0x10, 0xDEADBEEF)`，流程是：

1. CPU 发出一个 **MemWr TLP**，目标地址是 `BAR0_base + 0x10`；
2. **PCIe 硬核**收到 TLP，命中 BAR0，做地址转换（减去 BAR0 基地址），得到偏移 `0x10`；
3. PCIe 硬核把该写请求转换为 **AXI4-Lite 写事务**，地址为设计映射后的 AXI 地址（例如 `0x8000_0010`）；
4. 该事务进入 PL 区域的 **AXI4-Lite Interconnect/Decoder**，Decoder 根据地址判断目标是从设备“用户逻辑模块”；
5. 用户逻辑模块中的 **AXI4-Lite 从接口**完成握手，将 `0xDEADBEEF` 写入其内部由 `0x10` 偏移指定的**寄存器**。

这个寄存器物理上就是 PL 区域中的一组**触发器（Flip-Flop）**，由用户 RTL 代码定义。

如果 CPU 写的是 `BAR2_base + 0x8`，则第 4 步 Decoder 会把事务路由到 **QDMA IP 的 AXI4-Lite 从接口**，最终写入 QDMA 内部的控制寄存器——这些寄存器同样是 PL 区域中用 LUT/FF 实现的软逻辑寄存器。

---

### 1.5 整体布局示意

![FPGA Inner Layout](./assets/fpga_hw_layout.d2)

## II. Function 与 BDF 编号

### 2.1 Function

PCIe 规范允许多个独立的物理功能（**PCIe-Function**）存在于同一个物理设备（Endpoint）内，这样的设备被称为**多功能设备（Multi-Function Device）**。你可以把一个 FPGA 卡想象成一栋大楼，**Function 就是大楼里一个个独立的“房间”或“公司”**。

每个 Function 在逻辑上都是**完全独立**的：

- **独立的配置空间**：每个 Function 都拥有自己**完整的 4 KiB PCIe 配置空间（Configuration Space）**，用来描述自己的身份（厂商ID、设备ID）和资源需求（BAR）。
- **独立的驱动程序**：操作系统可以为每一个 Function 绑定**不同的设备驱动程序**。这是多功能设计的核心优势——它将 FPGA 内不同用途的逻辑（例如一个 Function 用于 DMA 数据通路，另一个 Function 用于控制管理接口）在软件层面彻底解耦，极大简化了驱动的开发和维护。
- **独立的资源**：每个 Function 可以拥有自己独立的 BAR 地址窗口和中断资源。

一个典型的例子是，一块 FPGA 可以同时实现三个 Function：一个用于控制 GPIO（LED/开关），一个用于 I2C 控制器，另一个用于 MDIO 接口。对于主机操作系统来说，它看到的是三个独立的 PCIe 设备，而非一个复杂的 FPGA。

---

### 2.2 BDF

**BDF（Bus:Device.Function）编号**是 PCIe 拓扑中用于**唯一标识一个 Function** 的地址。它的格式是 `总线号:设备号.功能号`，每个部分都有固定的位宽：

| 组成部分 | 示例值 | 位宽 | 含义 |
|:---|:---|:---|:---|
| **Bus Number (总线号)** | `01` | 8-bit | 该 Function 所在的 PCIe **总线**编号。Root Complex 所在的总线通常为 0。 |
| **Device Number (设备号)** | `00` | 5-bit | 该 Function 所在**设备**在总线上的编号，有时也被称为“槽位号”。 |
| **Function Number (功能号)** | `0` | 3-bit | 该 Function 在**设备内部**的编号。一个多功能设备最多可以有 **8** 个 Function（0~7）。 |

所以，`01:00.0` 的完整含义是：**总线 01 上，设备 00 内部的第 0 号功能**。

> **扩展形式**：有时会看到 `0000:01:00.0`，最前面的 `0000` 是 **PCI Domain** 编号，用于区分大型服务器中的多个 PCIe 主机桥。在普通 PC 中，domain 通常都是 0，因此常被省略。

---

### 2.3 BDF 编号的作用

BDF 并非一个单纯的“显示标签”，它在 PCIe 架构中承担着关键的**寻址与路由**功能。

#### 1. 配置空间访问的“门牌号”

在系统启动时，**Root Complex** 会对 PCIe 拓扑进行**枚举（Enumeration）**。它通过**发送配置读写 TLP 来探测每个可能存在的 BDF**。**如果某个 BDF 对应的 Function 存在，其配置空间的 Vendor ID 寄存器会返回有效值**；如果不存在，则返回 `0xFFFF`。操作系统正是通过遍历 BDF，来发现系统中所有可用的 PCIe Function。

在 **ECAM（Enhanced Configuration Access Mechanism）** 机制下，BDF 被直接编码进内存地址。每个 Function 的 4 KiB 配置空间在 ECAM 窗口中的偏移量，由 `Bus[27:20] + Device[19:15] + Function[14:12]` 共同决定。

#### 2. TLP 路由的“目的地地址”

当 CPU 或设备发起一个 PCIe TLP 时，TLP 的 **Header** 中会携带 **Requester ID** 和/或 **Completer ID**，这些字段的值**就是发起方或目标方的 BDF 编号**。PCIe Switch 和 Root Complex 依靠 TLP 中的 BDF 信息，将数据包精确地路由到目标 Function。

#### 3. 中断与 DMA 的“身份标识”

当 FPGA 中的某个 Function 发起 **MSI/MSI-X 中断或 DMA 请求**时，事务中同样会**嵌入该 Function 的 BDF 作为其身份标识**。IOMMU 可以利用 BDF 来区分不同 Function 的 DMA 访问，实施精细的隔离与保护。
