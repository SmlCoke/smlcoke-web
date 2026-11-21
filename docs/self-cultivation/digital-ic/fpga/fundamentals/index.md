# FPGA Fundamentals

## I. Concepts

#### 1. Logic Cells


Logic Cell(LC, 或者也叫做 System Logic Cell/SLC)是一个行业标准化的等效容量单位，**不是芯片上一个真实、独立的硬件原语**。它的标准定义：**1 个 4 输入 LUT + 1 个配套触发器 FF，再加内部进位多路选择器等附属电路**。
> LUT、DSP、BRAM 是**真实硬件资源**；Logic Cell 是**归一化后的等效计数单位**，主要用来跨厂商对比FPGA规模。

即行业约定：**1 LC = 1×LUT4 + 1×FF + carry/mux**

哪怕芯片内部实际是 LUT6(Xilinx), ALM(Intel), PFU(Lattice)，厂商都要把自己真实资源折算成这个标准 LC 数字写在datasheet，方便客户横向对比容量。此外，这个指标代表整个器件的通用逻辑 Fabric 总等效容量，**不含 DSP、Block RAM、硬核IP**。