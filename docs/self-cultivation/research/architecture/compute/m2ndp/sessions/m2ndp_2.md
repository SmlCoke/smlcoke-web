你现在的困惑非常具体，而且确实暴露了这篇论文在叙述上的一个问题：它大量使用了 forward reference。比如 scratchpad 在 III-D 已经用于解释 GPU 对比，到 III-E/F/G 才逐渐说明它究竟是什么；`mapped address/offset` 也是先作为抽象概念出现，后面才说明它们进入 x1/x2；Virtual Memory 更是直到 III-H 才把前面的地址语义补全。

所以这次不适合只按原文逐段复述。我会按 E → F → G → H 顺序讲，但把你问到的“这东西在真实硬件中究竟是什么”一并补齐。需要特别区分两类信息：

- “论文明确说了什么”：我会以原文为准；
- “为了让硬件路径完整，我补充的 RISC-V/计算机体系结构背景或推断”：会明确标出来，尤其是论文没有写清楚的地方。

先给你一张现在应该拥有的完整系统图：

```text
Host CPU
┌──────────────────────────────────┐
│ User Process                     │
│ ndpLaunchKernel(...)             │
└───────────────┬──────────────────┘
                │ CXL.mem
================│=========================================
                ▼
CXL Memory Expander
┌─────────────────────────────────────────────────────────┐
│ CXL Controller                                          │
│   Packet Filter → NDP Controller                        │
│                      │                                  │
│                      │ launch kernel                    │
│                      ▼                                  │
│              ┌─────────────────┐                        │
│              │   NDP Unit 0    │                        │
│              │                 │                        │
│ kernel code →│ I-cache         │                        │
│              │ µthread slots   │                        │
│              │ Register File   │                        │
│              │ Scalar/Vector   │                        │
│              │ ALU / LSU       │                        │
│              │                 │                        │
│              │ L1D / Scratchpad│ ← 本轮重要             │
│              │ TLB             │ ← 本轮重要             │
│              └────────┬────────┘                        │
│                       │                                 │
│                 On-chip Crossbar                        │
│                       │                                 │
│             Memory-side L2 Cache                        │
│                       │                                 │
│               Memory Controllers                       │
│                       │                                 │
│               LPDDR / DRAM                             │
│                                                         │
│   DRAM中还保留一小片区域：DRAM-TLB ← 本轮重要           │
└─────────────────────────────────────────────────────────┘
```

III-E 到 III-H，实际上就是开始把这张图的下面半截填完整。

---

# 一、III-E：NDP Unit Microarchitecture——µthread 最终落到什么硬件上执行？

前面 III-D 一直在讲：

```text
µthread
FGMT
轻量线程
地址驱动
```

到 III-E 作者终于回答：

> **这些 µthread 到底在哪些硬件模块上运行？**

答案就是 Fig. 7。

一个 NDP Unit 是一个真正的硬件处理器单元，而不是一个抽象概念。它内部有多个 NDP sub-core，每个 sub-core 保存多个 µthread context，并共享真正的 ALU/LSU/vector execution units。论文说明，一个 µthread slot 保存 PC、CSR、当前指令相关状态、INT/FP/vector register 的 base ID 等信息；µthread 创建后为它分配寄存器，其逻辑寄存器号通过 base ID 映射到实际 physical register。Low-Overhead_General-Purpose_Ne…

所以硬件关系不是：

```text
一个 µthread
=
一套独立 ALU + Register File + LSU
```

而是：

```text
很多 µthread contexts
         │
         ▼
少数真正的 execution units
```

和 GPU SM 中很多 resident warp/thread 共享执行单元的思想相同。

论文评估中的具体配置是：

```text
1 个 CXL Memory Expander
        │
        ├── 32 个 NDP Units
        │
        └── 每个 NDP Unit：
              4 个 sub-core

每个 sub-core：
16 个 µthread slots
2 scalar ALUs
1 scalar SFU
1 scalar LSU
1 vector ALU
1 vector SFU
1 vector LSU

所以：
每个 NDP Unit 最多保存
4 × 16 = 64 个 µthread contexts
```

另外每个 NDP Unit 配有 register file、instruction cache、128 KB 可在 scratchpad/L1D 间配置的存储，以及 I/D TLB。Low-Overhead_General-Purpose_Ne…

注意这是论文实验采用的一个具体 configuration，不意味着 M²NDP 定义上必须恰好是 32 Unit × 4 Sub-core × 16 slot。

---

## 1. 单个 µthread 怎么运行？

假设：

```text
µthread 7
PC = kernel_body + 0x10
```

它这一拍发出：

```text
VLE64.V
```

于是产生 memory request。

然后它可能要等几十、上百个 cycle。

作者不做复杂 OoO：

```text
µthread 7:
load
↓
等待
```

此时硬件转而让：

```text
µthread 8
µthread 15
µthread 23
...
```

继续发指令。

论文明确说：

> 单个 µthread 的指令是 serial/in-order 地执行，而不同 µthreads 通过 FGMT 独立发射。

因此不需要传统 OoO CPU 中复杂的 dependency checking、wake-up/select、forwarding 等逻辑。只要同时驻留足够多的 µthreads，就可以用线程级并发隐藏 memory latency。Low-Overhead_General-Purpose_Ne…

这就是 M² µthread 在真实 RTL 中最终变成的东西：

```text
µthread abstraction
        ↓
µthread slot/state
+
register allocation
+
scheduler / dispatch
+
shared execution units
```

---

## 2. 为什么要多个 sub-core？

论文的理由比较简单：

> 与其设计一个很大的 monolithic core，不如分成多个较小 sub-core，使 dispatch 简化。

然后 µthread 会以 memory-access granularity 交错分配到不同 NDP Unit，避免出现：

```text
NDP Unit 0:
64 个 active µthreads

NDP Unit 1:
0

NDP Unit 2:
0
```

这种严重不均衡。一个 µthread 获得 slot 后，PC 被初始化成相应 kernel code 的入口地址，然后开始执行。Low-Overhead_General-Purpose_Ne…

这正是前面 Fig. 4：

```text
µthread0 → NDP Unit0
µthread1 → NDP Unit1
µthread2 → NDP Unit2
...
```

那种 interleaving 的硬件原因。

---

# 二、先把 Scratchpad Memory 彻底讲明白

这是你第一个问题，而且确实应该在前面就解释。

Scratchpad Memory，简称 SPM，可以理解成：

> **NDP Unit 内部的一块由软件显式管理的高速片上 SRAM。**

它不是 DRAM。

也不是传统 Cache。

大致在：

```text
                 NDP Unit
┌─────────────────────────────────┐
│ µthreads                        │
│    │                            │
│    ├── Register File            │
│    │                            │
│    ├── Scratchpad SRAM ← 这里   │
│    │                            │
│    └── L1 Data Cache            │
└─────────────────────────────────┘
                │
               L2
                │
              DRAM
```

论文明确说，同一个 NDP Unit 上执行的所有 µthreads 都可以共享这个 scratchpad，并且给它配有支持 atomic operation 的 load/store unit。Low-Overhead_General-Purpose_Ne…

---

## 3. Scratchpad 和 Cache 最大区别是什么？

Cache 是：

> 硬件自动管理。

程序：

```asm
LD x1, (x2)
```

你不知道：

```text
L1 hit？
L1 miss？
哪个 cache line 被替换？
```

Cache Controller 自己决定。

Scratchpad 则是：

> 软件显式管理。

例如论文把 scratchpad 映射到一个预留 Virtual Address：

```text
0x10000000
```

于是 kernel：

```asm
SD x0, 0(x3)
```

其中：

```text
x3 = 0x10000000
```

就明确访问这块片上 SRAM。

所以 scratchpad 没有“我希望它 cache 住”这种不确定性，而是：

```text
这个地址
→ 就是片上 scratchpad
```

这是一个很重要的体系结构区别。

---

## 4. 为什么 NDP 需要 Scratchpad？

主要有三个用途。

第一，µthreads 之间共享临时数据。

例如 reduction：

```text
µthread0 local sum ─┐
µthread1 local sum ─┤
µthread2 local sum ─┤
                   ▼
             scratchpad sum
```

这比每次都写回 DRAM 再读回来便宜很多。

第二，保存 kernel arguments。

论文明确说，kernel launch 后，kernel arguments 会被放入每个 NDP Unit 的 on-chip scratchpad，这样这个 Unit 上的多个 µthreads 可以高效共享参数。Low-Overhead_General-Purpose_Ne…

例如：

```text
B_base
C_base
matrix_size
stride
...
```

没必要每个 µthread 都去 DRAM 重新取。

第三，减少 Global Memory Traffic。

这里的：

```text
Global Memory
≈ CXL Memory背后的DRAM
```

而 scratchpad 是片上。

所以：

```text
DRAM
  ↕                 慢/昂贵
NDP Unit

vs.

Scratchpad ↔ µthread
            很近
```

论文还专门拿这个和 CUDA Shared Memory 比较：CUDA shared memory 的 scope 受 thread block 限制，而论文让同一个 NDP Unit 上所有 µthreads 都共享 scratchpad，因此可以减少 global/scratchpad traffic。Low-Overhead_General-Purpose_Ne…

---

## 5. Scratchpad 是作者发明的吗？

不是。

Scratchpad memory 是成熟的计算机体系结构概念。

GPU shared memory、本地 SRAM、很多 DSP/AI accelerator 的 local memory 都属于相似思想。

M²NDP 的特别之处主要是：

> 把 scratchpad 的共享 scope 定义到整个 NDP Unit，而不是 CUDA Thread Block。

---

## 6. Scratchpad 和 M² func region 千万不要混淆

这是本文两个非常容易混的“memory-mapped region”。

M² func region：

```text
Host 看到的一段 CXL Memory address

用途：
Host → NDP Controller
发控制命令

例如：
LaunchKernel
PollStatus
```

Scratchpad mapped region：

```text
NDP kernel 自己看到的一段 Virtual Address

用途：
µthreads访问NDP Unit内部的片上SRAM
```

两者完全不是一个东西。

可以记成：

```text
M² func region
= Host控制接口

Scratchpad region
= NDP内部工作内存
```

---

# 三、III-F：Cache Hierarchy——NDP Unit 怎么访问数据而又不把 coherence 搞复杂？

这一节非常短，但对硬件设计很重要。

作者的原则是：

> **尽量不要在几十个 NDP Unit 的 private L1 之间再造一套复杂的 CPU-style cache coherence。**

因此采用类似 GPU 的层次：

```text
µthread
  │
  ▼
L1 D-cache       ← 每个NDP Unit附近
  │
  ▼
Memory-side L2   ← 放在Memory Controller之前
  │
  ▼
DRAM
```

并且：

```text
L1 D-cache:
write-through
```

也就是写 L1 时继续向下传播，而不是让 dirty data 长期只存在 private L1 中。

论文明确说这是为了避免复杂 cache coherence，并把 L2 放在 Memory Controller 前；global memory atomic 也由这个 memory-side L2 来完成。Low-Overhead_General-Purpose_Ne… Low-Overhead_General-Purpose_Ne…

这里要稍微谨慎：

> 论文说“通过这套层次避免 cache coherence complexity”，但并没有在这一段给出一个完整的 formal coherence protocol。

所以不能从这几句话推出：

> “write-through L1 本身自动解决了一切多核一致性问题”。

论文真正的架构选择更接近：

```text
尽量减少private L1中dirty/shared mutable state
+
global atomic集中在L2
+
共享临时数据尽量放scratchpad
```

从而避免做 CPU 那种全功能 MESI coherence。

---

## 1. L1D 和 Scratchpad 的硬件关系

论文有一个很有意思的设计：

> L1 Data Cache capacity 可以在普通 L1 cache 与 scratchpad 之间配置。

Low-Overhead_General-Purpose_Ne…

实验中写的是：

```text
128 KB scratchpad / L1D cache
```

Low-Overhead_General-Purpose_Ne…

你可以理解成一组片上 SRAM bank：

```text
128 KB SRAM
    │
    ├── 某些bank配置成hardware-managed L1 cache
    │
    └── 某些bank配置成software-managed scratchpad
```

具体 SRAM bank 如何切分，论文没有给 RTL 细节，但概念上就是可配置 partition。

---

## 2. Instruction Cache 为什么很小？

作者认为目标 workload：

```text
memory-bound
data-parallel
```

通常：

```text
数据很多
kernel代码却很短
```

比如：

```text
load
compare
add
store
loop
```

所以 instruction working set 很小，不需要 CPU 那样大的 I-cache。

而 kernel unregister 时会 flush Instruction Cache，避免之后执行 stale code。Low-Overhead_General-Purpose_Ne…

这也第一次告诉你一个重要事实：

> NDP kernel 不是某块固定组合逻辑；它真的是被取指、译码、执行的一段 RISC-V 程序。

---

# 四、III-G：Programming Model——Kernel 究竟是什么？

这一节实际上是作者终于正式回答：

> “如果我要给这颗 NDP processor 编程，一份 NDP program 长什么样？”

论文规定一个 NDP kernel 可以由：

```text
Initializer

      ↓

Kernel Body 0

      ↓ barrier

Kernel Body 1

      ↓ barrier

Kernel Body 2
      ...

      ↓

Finalizer
```

组成。Low-Overhead_General-Purpose_Ne…

这也是你觉得最莫名其妙的“multiple kernel bodies”。

---

# 五、Kernel 到底是硬件还是软件？

现在可以彻底定性：

> **Kernel 是软件。更具体地说，是要在 NDP Unit 上执行的一段 RISC-V/RVV machine code。**

论文说 M² µthread 的 kernel 可以使用 `RV64IMAFDV` 或其中的子集，只是不支持依赖 OS 的指令，例如 ECALL。Low-Overhead_General-Purpose_Ne…

所以关系是：

```text
NDP Unit
= processor hardware

Kernel
= program / machine instructions

µthread
= kernel的一次执行实例
```

类比 CPU：

```text
CPU Core
= hardware

function foo()
= code

Thread
= execution context
```

类比 GPU：

```text
GPU SM
= hardware

CUDA kernel
= program

CUDA thread
= one execution instance
```

---

# 六、Kernel 在哪里存？

这里我要明确区分“论文写明的”和“合理推断”。

论文明确给了：

```text
ndpRegisterKernel(
    codeLoc,
    scratchpadMemSize,
    numIntRegs,
    numFloatRegs,
    numVectorRegs
)
```

也就是说注册时会告诉 NDP：

> kernel code location 在哪里。

同时论文明确说 NDP Unit 有 instruction cache，并在 kernel unregister 时 flush，以避免 stale code。Low-Overhead_General-Purpose_Ne…

但是：

> **本文 A–H 并没有把 kernel binary 的完整物理存储和搬运流程写清楚。**

它没有明确告诉你：

```text
RegisterKernel 时是否把整个binary复制到某块DRAM？
还是仅记录codeLoc？
code metadata格式是什么？
多个body的entry point又怎么编码？
```

这些细节本文确实缺失。

从 `codeLoc + instruction cache` 的设计，最自然的理解是：

```text
kernel machine code
存放在 NDP 可访问的 memory/HDM 中

NDP Unit通过PC取指
↓
I-cache
↓
decode
↓
scalar/vector execution unit执行
```

但“RegisterKernel 内部究竟 copy 代码还是只记 pointer”属于本文没有明确规定的实现细节，不能冒充原文结论。

---

# 七、Initializer / Body / Finalizer 到底是什么意思？

把它想成 GPU kernel 可能反而不容易。

更好的类比是一个：

> bulk-synchronous parallel program。

例如对超大数组求和。

程序可以分三阶段：

```text
阶段0：
初始化共享local_sum = 0

阶段1：
大量µthreads并行处理输入
并累加local_sum

阶段2：
所有线程都完成后
把local_sum写入最终global_sum
```

于是：

```text
Initializer
= 每次kernel launch只做一次初始化

Kernel Body
= 针对µthread pool中的所有data并行执行

Finalizer
= 全部body完成以后做一次收尾
```

原文也是这样定义的。Low-Overhead_General-Purpose_Ne…

---

# 八、“Multiple Kernel Bodies”到底是什么鬼？

这个其实有合理的体系结构含义，只是论文说得太快。

例如一个算法存在两个 phase：

```text
Phase 1：
每个µthread计算 histogram局部结果

Phase 2：
所有Phase 1必须全部完成
然后才能根据完整histogram继续计算
```

那你需要：

```text
所有µthread完成Body 1
        ↓
       Barrier
        ↓
所有µthread重新生成
执行Body 2
```

论文的模型正是：

> 一个 body 对所有 µthreads 执行完成以后，µthread generator 再重新为下一 body 生成所有 µthreads。

Low-Overhead_General-Purpose_Ne…

所以“multiple bodies”不是：

> 一段 C 函数神秘地长出多个 body。

更准确的抽象是：

```text
一个NDP kernel job
可以由多个并行计算phase组成

每个phase
= 一个kernel body

phase之间
= implicit global barrier
```

因此原文：

> useful for synchronization of µthreads across different phases of a kernel

意思就是：

假设：

```text
Body 1
µthread A ───────┐
µthread B ─────────────┐
µthread C ──┐          │
            ▼          ▼
不能有人提前进入Body2

必须等：
A finished
B finished
C finished
        │
        ▼
     Barrier
        │
        ▼
重新生成µthreads
执行Body2
```

这样 Body 2 看到的数据保证已经是 Body 1 全部完成后的状态。

如果没有这个 barrier：

```text
µthread C:
Body1完得快
→ 已经读Body2数据

µthread B:
Body1还没写完
```

C 就可能读到不完整数据。

所以 multiple bodies 本质上给了一个非常便宜的：

> kernel-wide phase synchronization mechanism。

---

# 九、Fig. 8 到底在干什么？

Fig. 8 是：

> 对一个很大的数据集做 Reduction Sum。

也就是：

```text
sum = A[0] + A[1] + ... + A[N-1]
```

它用三阶段：

```text
Initializer
↓
把本NDP Unit的local_sum清零

Kernel Body
↓
每个µthread读取自己的一段input
做vector reduction
atomic add到local_sum

Finalizer
↓
读取local_sum
atomic add到最终global_sum
```

图中约定：

```text
Scratchpad base = 0x10000000

Scratchpad + 0:
local sum

Scratchpad + 8:
最终global result的地址
```

论文图注明确说明最终结果位置的地址被存放在 scratchpad `0x10000008`。Low-Overhead_General-Purpose_Ne…

---

# 十、逐条拆 Fig. 8 指令

下面关于指令本身的部分是 RISC-V ISA 背景，不是本文自己定义的。我用官方 RISC-V ISA 解释。

Fig. 8 一共有这些指令：

| 指令 | 来源 | 作用 |
|---|---|---|
| `LI` | assembler pseudo-instruction | 把立即数装入整数寄存器 |
| `SD` | RV64I | store 64-bit doubleword |
| `LD` | RV64I | load 64-bit doubleword |
| `VLE64.V` | RVV | 连续加载若干 64-bit vector elements |
| `VMV.V.I` | RVV | 把一个小立即数广播到所有 active vector elements |
| `VREDSUM.VS` | RVV | 把一个 vector 内所有元素做 reduction sum |
| `VMV.X.S` | RVV | 把 vector register 的 element 0 移到整数寄存器 |
| `AMOADD.D` | RV64A | 对 64-bit memory location 做 atomic add |

下面逐条解释。

---

## 1. `LI x3, 0x1000...000`

`LI` 不是一条真正有独立 opcode 的 RISC-V machine instruction。

它是 assembler pseudo-instruction：

```asm
li rd, immediate
```

意思是：

```text
rd = immediate
```

assembler 会根据数值大小展开成：

```asm
ADDI
```

或者：

```asm
LUI
ADDI
```

甚至更多条指令。

所以你问“LI 的编码格式是什么”时，严格答案是：

> **没有单一编码格式，因为 LI 不是基础 ISA 中真正的 instruction。**

例如这里就是：

```text
x3 = scratchpad base address
```

---

## 2. `SD x0, (x3)`

RV64I：

```asm
sd rs2, imm(rs1)
```

语义：

```text
Memory[rs1 + imm] = rs2[63:0]
```

这里：

```text
rs2 = x0 = 永远为0
rs1 = x3 = scratchpad address
imm = 0
```

所以：

```text
Scratchpad[local_sum] = 0
```

这正是 Initializer。

它是 S-type：

```text
31       25 24    20 19    15 14 12 11       7 6       0
+----------+--------+--------+-----+-----------+---------+
| imm[11:5]|  rs2   |  rs1   | 011 | imm[4:0] |0100011 |
+----------+--------+--------+-----+-----------+---------+
```

其中 `funct3=011` 表示 64-bit doubleword store。RISC-V 基础 ISA 的 load/store 使用标准 I/S 型格式。[RISC-V 文檔](https://docs.riscv.org/reference/isa/unpriv/rv-32-64g.html?utm_source=chatgpt.com)

---

## 3. `VLE64.V v2, (x1)`

这是 RISC-V Vector Extension 的：

> 64-bit element unit-stride vector load。

语义类似：

```text
v2[0] = Mem[x1 + 0×8]
v2[1] = Mem[x1 + 1×8]
v2[2] = Mem[x1 + 2×8]
...
```

究竟加载多少 element，不直接写死在指令里，而取决于 RVV 的：

```text
vl
vtype / SEW / LMUL
```

这里：

```text
x1
```

就是前面 M² µthread 创建时硬件放入的：

> mapped address。

也就是：

```text
这个µthread负责的数据块起始地址
```

所以这条指令实际上是：

> “把这个 µthread 所对应的那段输入数据加载进 v2。”

RVV vector load/store 使用 `LOAD-FP/STORE-FP` major opcode space，指令中包含 destination vector register、base integer register、mask 和 vector-memory addressing mode 等字段；`vle64.v` 是 unit-stride 64-bit load。[RISC-V 文檔](https://docs.riscv.org/reference/isa/unpriv/v-st-ext?utm_source=chatgpt.com)

---

## 4. `VMV.V.I v1, 0`

意思是：

```text
v1[0] = 0
v1[1] = 0
v1[2] = 0
...
```

即 immediate broadcast/splat。

后面 reduction 需要一个初始 accumulator：

```text
initial value = 0
```

因此把 v1 清零。

这类 RVV arithmetic 指令采用 `OP-V` major opcode `1010111₂`；`vmv.v.i` 属于 vector-immediate 类，和 vector merge 共享 encoding，使用 `vm=1` 且特定 source field 表示 move。[RISC-V 文檔](https://docs.riscv.org/reference/isa/v20240411/_attachments/riscv-unprivileged.pdf?utm_source=chatgpt.com)

---

## 5. `VREDSUM.VS v3, v2, v1`

这条是整段代码最关键的 vector instruction。

标准语义：

```text
v3[0] =
v1[0]
+
v2[0]
+
v2[1]
+
...
+
v2[vl-1]
```

也就是：

```text
vd[0] = vs1[0] + sum(vs2[*])
```

官方 RVV 正是这样定义 `vredsum.vs`。[RISC-V 文檔](https://docs.riscv.org/reference/isa/v20240411/_attachments/riscv-unprivileged.pdf?utm_source=chatgpt.com)

这里：

```text
v1[0] = 0
```

所以实际上：

```text
v3[0] = sum(v2所有有效元素)
```

假设 v2 中刚加载：

```text
3, 5, 7, 2
```

那么：

```text
v3[0] = 17
```

编码属于 OP-V arithmetic 类，`vredsum` 的 `funct6=000000`，属于 reduction/vector-scalar 类。[RISC-V 文檔](https://docs.riscv.org/reference/isa/v20250508/unpriv/vector-crypto.html?utm_source=chatgpt.com)

---

## 6. `VMV.X.S x4, v3`

意思是：

```text
x4 = v3[0]
```

即：

> 把 vector register element 0 搬到 scalar integer register。

所以刚才：

```text
v3[0] = 本µthread处理的数据的sum
```

现在变成：

```text
x4 = 本µthread的local reduction result
```

RVV 官方定义就是：

```text
vmv.x.s rd, vs2
→ x[rd] = vs2[0]
``` :chatgpt-content-reference{index="23"}


---

## 7. `LI x3, 0x1000...000`

再次把：

```text
scratchpad local_sum address
```

装进 x3。

---

## 8. `AMOADD.D x4, x4, (x3)`

这一条你要特别理解。

RISC-V atomic memory operation：

```asm
amoadd.d rd, rs2, (rs1)
```

语义近似：

```c
old = Memory[rs1];
Memory[rs1] = old + rs2;
rd = old;
```

整个 read-modify-write 是 atomic 的。

所以这里：

```text
rs1 = x3
→ scratchpad local_sum address

rs2 = x4
→ 当前µthread算出的sum
```

硬件完成：

```text
scratchpad_local_sum += x4
```

原来的 memory value 会返回 x4，但这里之后并不关心返回的 old value。

`AMOADD.D` 属于 RV64A，使用 R-type/AMO encoding：

```text
funct5 = 00000
aq
rl
rs2
rs1
funct3 = 011
rd
opcode = 0101111
```

`.D` 表示操作 64-bit doubleword。[RISC-V 文檔](https://docs.riscv.org/reference/isa/unpriv/rv-32-64g.html?utm_source=chatgpt.com)

为什么要 atomic？

因为：

```text
µthread0:
sum += 17

µthread1:
sum += 31
```

可能同时更新同一个 scratchpad local_sum。

如果普通：

```text
load
add
store
```

就会 race。

Atomic add 保证不会丢失更新。

---

# 十一、所以 Kernel Body 整体做的事情非常简单

把它翻译成伪代码：

```c
void body(mapped_address)
{
    vector v2 = load_vector(mapped_address);

    long partial =
        reduce_sum(v2);

    atomic_add(
        scratchpad.local_sum,
        partial
    );
}
```

这才是 Fig. 8(b)。

---

# 十二、Finalizer 又在干什么？

Fig. 8(c)：

```asm
LI x3, SCRATCHPAD_BASE

LD x4, 0(x3)
LD x5, 8(x3)

AMOADD.D x4, x4, (x5)
```

逐句就是：

```text
x3 = scratchpad base

x4 = scratchpad[0]
   = 本NDP Unit的local sum

x5 = scratchpad[8]
   = 最终global result的地址

atomic:
Memory[x5] += x4
```

也就是：

```text
每个NDP Unit内部：
很多µthreads
      ↓
local scratchpad sum

所有body完成
      ↓

Finalizer:
local sum
      ↓
atomic add
      ↓
最终global sum
```

现在整个 reduction 结构就是：

```text
          µthread0 ─┐
          µthread1 ─┤
          µthread2 ─┤
                    ▼
           NDP Unit 0 local sum
                    │
                    │
                    ├────┐
                         │
          µthread...     │
                    ▼    │
           NDP Unit 1    │
           local sum ────┤
                         ▼
                   Global Sum
```

---

# 十三、III-H：为什么突然要 Virtual Memory？

你问到的是这一节最关键的问题。

先看 passive CXL Memory：

```text
Process Virtual Address
        │
        ▼
Host CPU MMU
        │
        ▼
Host Physical Address (HPA)
        │
        ▼
CXL.mem request
        │
        ▼
CXL Memory
```

注意：

> CXL Memory 收到 request 时，Host CPU 已经完成 VA → PA translation。

所以普通 passive CXL Memory：

```text
只看到Physical Address
```

它自己根本不需要：

```text
MMU
TLB
page table walk
```

这就是原文：

> host uses physical addresses for normal CXL.mem requests, address translation is not needed in passive CXL memory

的真正意思。Low-Overhead_General-Purpose_Ne…

---

# 十四、为什么有 NDP 后情况突然变了？

因为现在：

> **不是 Host CPU 在执行 load/store 了。**

而是：

```text
NDP Unit
```

自己在执行：

```asm
LD
VLE64.V
SD
...
```

例如 Host process 原代码：

```c
foo(A);
```

A 是用户进程里的 pointer：

```text
A = Virtual Address
```

如果 NDP kernel 也希望能够使用 Host application 的 pointer/数据结构，就会得到：

```text
Virtual Address
```

而不是 CPU MMU 已经翻译好的单个 physical address。

因此：

```text
NDP processor执行load/store
           ↓
它自己也必须：
VA → PA
```

所以 NDP Unit 需要 TLB。

论文直接规定，µthread pool region 和 kernel 的 load/store 使用 virtual addresses。Low-Overhead_General-Purpose_Ne…

---

# 十五、“轻量 processor 又不跑 Linux，为什么还需要 VM？”

因为：

> Virtual Memory ≠ “这颗处理器自己必须跑 Linux”。

GPU 就是非常典型的例子。

GPU SM 并不在每个 SM 上跑 Linux process，但 GPU kernel 仍然执行用户进程提供的 virtual pointer，所以 GPU 有：

```text
GPU TLB
IOMMU / ATS
address translation
```

M²NDP 同理。

而且别忘了：

> M²NDP 本来就可以同时为多个 Host process 服务。

前面 M² func 已经有：

```text
ASID
per-process M²func region
```

所以 NDP 很可能同时面对：

```text
Process A:
VA 0x1000

Process B:
VA 0x1000
```

两个完全不同的物理对象。

必须利用：

```text
ASID + VPN
```

区分。

因此 VM 的需求来自：

```text
Host process address space semantics
```

而不是来自：

```text
NDP自己运行操作系统
```

这一点非常重要。

---

# 十六、NDP 到底能访问多大的 Memory 范围？

论文这里说得其实很明确：

> NDP kernel 可以访问系统中任意 HDM memory，包括 peer CXL.mem device 中的 HDM。

Low-Overhead_General-Purpose_Ne…

也就是说：

```text
NDP Unit
   │
   ├── 自己这个CXL Memory的HDM
   │
   └── 其他CXL Memory的HDM
          （通过P2P / interconnect）
```

但是：

> **不能仅仅通过 CXL.mem 直接访问 Host 自己的 local DRAM。**

论文明确说：

> host-side memory cannot be directly accessed from an NDP kernel using CXL.mem

Low-Overhead_General-Purpose_Ne…

所以目前本文 baseline mental model 应该是：

```text
                  Host Local DRAM
                       ✕
                       │
                       │ CXL.mem不能直接这么访问
                       │
NDP Unit ────── CXL HDM
   │
   └────────── Peer CXL HDM
```

作者补充说，可以借鉴 GPU 的 PCIe + Host Driver/Runtime page-fault handling 等机制扩展 host-side memory 访问，但那不是本文 M²NDP 基础机制本身。Low-Overhead_General-Purpose_Ne…

---

# 十七、为什么普通 on-chip TLB 不够？

想一下 NDP 针对的数据：

```text
LLM weights
Embedding table
Graph
Database
```

可能：

```text
几十GB
几百GB
```

甚至更多。

假设：

```text
Page = 4 KB
```

256 GB Memory 有：

```text
256 GB / 4 KB
≈ 67 million pages
```

而论文一个 NDP Unit 的 on-chip D-TLB 只有：

```text
256 entries
```

Low-Overhead_General-Purpose_Ne…

显然覆盖范围很小：

```text
256 × 4 KB
= 1 MB TLB reach
```

一旦访问几十 GB dataset：

```text
TLB miss
TLB miss
TLB miss
...
```

如果每一次 TLB miss 都去 Host 做：

```text
ATS
+
Host page table walk
```

论文前面已经说过可能是 µs-scale，非常昂贵。

于是作者需要一个：

> 比 on-chip TLB 大很多、但比每次去 Host ATS 便宜的中间层。

这就是：

# DRAM-TLB

---

# 十八、DRAM-TLB 到底是什么硬件？

这个名字确实很容易误导。

传统 TLB：

```text
CPU MMU旁边
小型SRAM/CAM
几十~几千entries
```

而论文的 DRAM-TLB：

> **不是把一块传统 CAM 型 TLB 电路“塞进 DRAM 芯片”。**

它实际上是：

> 从 CXL Memory 的 DRAM 容量里划出一块区域，用来存大量 `VA page → PA page` translation entries。

论文说每个 DRAM-TLB entry 为 16 Bytes，存：

```text
ASID
tag
physical page number
permission bits / attributes
```

Low-Overhead_General-Purpose_Ne…

所以物理结构可以理解为：

```text
CXL DRAM
┌─────────────────────────────┐
│ Normal application data     │
│                             │
│                             │
├─────────────────────────────┤
│ Reserved DRAM-TLB region    │
│ Entry0: ASID, tag, PPN,...  │
│ Entry1: ASID, tag, PPN,...  │
│ Entry2: ASID, tag, PPN,...  │
│ ...                         │
└─────────────────────────────┘
```

这就是为什么名字里有：

```text
DRAM-TLB
```

它是：

> translation cache stored in DRAM。

而不是传统片上 TLB SRAM。

---

# 十九、那访问一次 Virtual Address 的完整路径是什么？

可以建立三级翻译系统：

```text
NDP kernel
   |
   | Virtual Address
   v
+----------------+
| On-chip TLB    |
+----------------+
   |
   | hit
   +------------------------→ Physical Address
   |
   | miss
   v
+----------------+
| DRAM-TLB       |
| 存在CXL DRAM   |
+----------------+
   |
   | hit
   +------------------------→ PPN
   |                           ↓
   |                        refill on-chip TLB
   |
   | miss
   v
ATS / Host address translation
   |
   v
Host page tables
```

最后一层的精确 refill protocol 本文这一段没有完全展开；论文明确说采用 DRAM-TLB 是为了增加 TLB reach 并降低 on-chip TLB miss penalty，同时 ATS 本身可能具有较高延迟。Low-Overhead_General-Purpose_Ne…

所以这里最合理的理解就是：

```text
L1 translation cache:
On-chip TLB

L2-ish translation cache:
DRAM-TLB

最终权威translation:
Host / ATS
```

其中“L2-ish”是帮助你理解的类比，不是论文正式命名。

---

# 二十、“根据 VPN 和 ASID hash 算 DRAM-TLB entry 地址”是什么意思？

传统 on-chip TLB 可以做：

```text
VPN
 ↓
CAM / Set Associative lookup
 ↓
查出PPN
```

但 DRAM 不适合：

```text
把几百万个entry全部并行CAM比较
```

所以作者让 entry 的存放位置是 deterministic 的：

```text
index = hash(VPN, ASID)

DRAM_address
=
DRAM_TLB_base
+
index × entry_size
```

这是为了说明机制的示意公式；论文原文说具体 location 由：

```text
Virtual Page Number
+
ASID
+
每个CXL Memory的base address
```

的 hash/地址计算得到。Low-Overhead_General-Purpose_Ne…

例如：

```text
Process A:
ASID = 7

VA:
0x12345678

VPN:
0x12345

hash(0x12345, 7)
= index 39184

DRAM_TLB_base + 39184×16
```

直接去那个 DRAM 地址读 16 Byte entry。

然后检查：

```text
tag是否匹配？
ASID是否匹配？
```

如果匹配：

```text
得到PPN
```

---

# 二十一、为什么所有 NDP Unit 能共享同一个 DRAM-TLB？

现在这句话就很好理解了。

如果 NDP Unit 0 和 NDP Unit 17 都要翻译：

```text
ASID = 7
VPN = 0x12345
```

它们分别计算：

```text
hash(VPN, ASID)
```

得到同一个 index。

所以：

```text
Unit0 ─┐
       │
Unit1 ─┤
       ├──→ 同一个DRAM-TLB entry
...    │
Unit31─┘
```

不需要：

```text
每个NDP Unit
自己复制几GB的translation table
```

这就是论文说：

> all NDP units within the same CXL memory can share them

的意思。Low-Overhead_General-Purpose_Ne…

---

# 二十二、为什么 16 B/page 的开销只有 0.4%？

如果：

```text
1 page = 4096 B

每页translation metadata = 16 B
```

那么：

```text
16 / 4096
≈ 0.003906
≈ 0.39%
```

也就是：

```text
≈ 0.4%
```

论文明确给出了这个数字；如果使用 2 MB huge page，比例就更小，几乎可以忽略。Low-Overhead_General-Purpose_Ne…

例如 256 GB CXL Memory，如果真的按 4 KB page 全覆盖：

```text
256 GB × 0.4%
≈ 1 GB
```

拿约 1 GB DRAM 换取几乎覆盖整片 256 GB 的 translation cache。

对于一个：

```text
256 GB Memory Expander
```

来说，作者认为这个容量代价是可以接受的。

---

# 二十三、Page Mapping 变了怎么办？

这个问题也很重要。

假设：

```text
VA page A
原来 → PA 100

后来OS修改：
VA page A → PA 200
```

那：

```text
On-chip TLB
DRAM-TLB
```

里的旧 translation 都必须失效。

所以需要：

> TLB shootdown。

论文说如果 page mapping 改变，就需要对所有 CXL-M²NDP 做 TLB shootdown；不过它假设这些 in-memory datasets 很少 swapping，因此这种事情不频繁。Low-Overhead_General-Purpose_Ne…

这也是 Table II 里面为什么会有：

```text
ndpShootdownTlbEntry(...)
```

这个 privileged M² func。

你现在终于可以把它和前面的 M² func 连起来了。

---

# 二十四、把 E/F/G/H 最终连在一起

到这里，这四节已经不是四堆孤立概念。

整个过程是：

```text
Host:
ndpLaunchKernel()
       │
       ▼
M² func
       │
       ▼
NDP Controller
       │
       ▼
µthread Generator
       │
       ├── µthread0
       ├── µthread1
       ├── µthread2
       ...
       │
       ▼
NDP Unit / Sub-core
       │
       ├── PC
       ├── Register Context
       ├── Scalar/Vector ALU
       ├── LSU
       │
       ├── Scratchpad
       │      ↑
       │      ├── kernel arguments
       │      ├── shared local data
       │      └── reduction intermediates
       │
       └── Kernel load/store
              │
              │ Virtual Address
              ▼
           On-chip TLB
              │
           miss│
              ▼
           DRAM-TLB
              │
           miss│
              ▼
             ATS
              │
              ▼
       Physical Address / HDM
              │
              ▼
           L1 / L2
              │
              ▼
             DRAM
```

然后 Kernel 本身：

```text
Initializer
    │
    │ 初始化scratchpad
    ▼
Body 0
    │
    │ 所有µthreads完成
    ▼
Barrier
    │
Body 1
    │
    │ 所有µthreads完成
    ▼
Barrier
    │
   ...
    │
Finalizer
    │
    ▼
最终结果写回DRAM
```

因此 E-H 四节其实分别回答了四个非常明确的问题：

| Section | 真正回答的问题 |
|---|---|
| III-E | µthread 最终落在什么处理器硬件上跑？ |
| III-F | µthread 的数据 Cache / local memory 怎么组织，怎样尽量避免 coherence 复杂度？ |
| III-G | NDP 程序究竟怎么写、怎么分 phase、怎么使用 scratchpad？ |
| III-H | NDP 自己执行 load/store 后，Virtual Address 怎么翻译？ |

你现在还需要特别记住一个事实：**论文在 III-G/H 才把前面很多抽象真正“落地”**。所以你前面第一次读 III-D 时觉得 `scratchpad`、`mapped address`、`kernel argument` 都像突然冒出来，并不是你的理解出了问题；它的 exposition 确实要求读者默认已经熟悉 GPU/NDP/virtual-memory 系统，再在后文补实现细节。

到这里，III-A 到 III-H 已经基本形成了一套完整的软件→控制→执行→存储的数据通路。下一步如果继续 III-I/J，其实已经不会再引入这么多基础概念，主要变成“多个 CXL-M²NDP 怎么 scale”和“NDP 计算逻辑是否一定要绑在每个 Memory Expander 上”。