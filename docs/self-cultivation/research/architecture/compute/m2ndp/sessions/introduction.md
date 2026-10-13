可以。先不要逐句硬啃 Introduction。对你现在这个阶段，更有效的方法是先把它还原成作者在讲的一个“工程故事”。你读懂这个故事以后，再回去看原文，每句话就会有位置。

这篇论文的 Introduction 实际上只在回答 4 个问题：

> 1. 为什么要有 CXL Memory？  
> 2. CXL Memory 有什么性能问题？  
> 3. 为什么想到在 CXL Memory 旁边放计算单元，也就是 NDP？  
> 4. 现有 NDP 又有什么问题，所以作者提出 M²NDP？

下面我完全围绕论文 Introduction 来拆。

---

## 1. 第一幕：CPU 内存不够，所以出现 CXL Memory Expander

先想一个服务器：

```text
CPU
 |
DDR5 Controller
 |
Local DRAM
```

CPU 自己可能只能挂有限数量的 DDR 通道和 DIMM，内存容量有限。

但现在很多应用非常吃容量，比如：

- KVStore
- LLM
- Recommendation Model
- Graph Analytics
- OLAP

于是希望：

```text
             Local DRAM
                 |
CPU -------------+
 |
CXL
 |
CXL Memory Expander
 |
大量额外 DRAM
```

这块挂在 CXL 后面的内存，就是论文一直说的：

> CXL memory

或者：

> CXL memory expander

这里最重要的是：

**它不是“PCIe FPGA 上的一块 buffer”。**

CPU 可以通过 CXL.mem，用普通 load/store 的方式访问这块内存。论文 Introduction 明确说，CXL.mem 提供 memory semantics，CPU 可以直接用 load/store 访问远端 CXL memory，而且它的协议延迟显著低于传统 PCIe，并接近跨 Socket NUMA memory 的量级。Low-Overhead_General-Purpose_Ne…

你可以暂时把它想成：

```c
int x = array[i];
```

CPU 程序还是普通 load。

区别只在于这个地址对应的数据可能实际在：

```text
Local DRAM
```

也可能在：

```text
CXL Memory Expander 里的 DRAM
```

这就是它所谓的“memory expansion”。

---

# 2. 那既然 CPU 可以直接 load/store CXL Memory，问题解决了吗？

没有。

这就是 Introduction 的核心矛盾。

假设：

```text
CPU
 |
 | CXL Link
 |
CXL Memory
```

CXL Memory 后面的 DRAM 本身带宽可能非常高。

但是 CPU 真正访问它时，中间必须经过 CXL Link。

于是出现：

```text
CXL Memory内部DRAM
       ↓
   很高带宽

但是

CPU ←→ CXL Memory
       ↓
   CXL Link带宽有限
```

这就像：

> 一个仓库内部有 32 条高速流水线，但是仓库和工厂之间只有一条公路。

仓库内部再快没用，你每次都要把数据拉回 CPU。

论文指出，CXL link 的带宽明显低于 CXL memory 内部 DRAM bandwidth，所以对于 bandwidth-intensive workload，CXL link 会成为瓶颈。把这类程序的数据放到 CXL memory 中，性能甚至可能下降到最多约 9.9×。Low-Overhead_General-Purpose_Ne…

这就是 Fig. 1(a) 想告诉你的事情。

---

# 3. Fig. 1(a) 其实不用看懂 Roofline，也能理解

第一页右上角那个图你现在不用管 Roofline Model 的所有理论。

只需要知道横轴：

> Operational Intensity

大概可以理解成：

> 每搬一个 Byte 数据，能做多少计算。

比如：

```text
A[i] = B[i] + C[i]
```

读很多数据，只做一个加法。

这种：

```text
计算少
访存多
```

Operational Intensity 很低。

这种程序称：

> memory-bound

而论文研究的恰恰主要就是这种 workload。

比如：

```text
扫描数据库
访问 KVStore
稀疏矩阵
Graph
Embedding lookup
```

它们经常：

```text
读一大堆数据
↓
做一点计算
↓
继续读数据
```

如果数据都在 CXL memory：

```text
CPU
 ↑
 │ 大量数据
 │
CXL Link
 ↑
 │
CXL Memory
```

那么瓶颈自然就在 CXL Link。

所以第一页 Fig. 1(a) 本质上就是：

> 对 memory-bound 程序，把数据从 Local Memory 搬到 CXL Memory 后，会因为 CXL 链路限制而明显变慢。

论文特别强调的就是 latency-sensitive 和 bandwidth-intensive 两类 memory-bound 应用都会受到影响。Low-Overhead_General-Purpose_Ne…

---

# 4. Fig. 1(b)：除了带宽，还有 latency 问题

还有另一类程序不是连续扫 100 GB 数组，而是：

```text
读一个地址
↓
根据结果决定下一个地址
↓
再读
↓
再决定
```

比如 KVStore 的 pointer chasing。

这种程序的问题可能不是：

```text
GB/s 不够
```

而是：

```text
每次 load 要等多久？
```

这就是 latency-sensitive。

论文给出的典型 CXL memory load-to-use latency 可以低到约 150–175 ns，但具体实现中也可能更高；而更长的 CXL memory latency 会明显恶化 KVStore 的 P95 tail latency。Low-Overhead_General-Purpose_Ne…

所以作者此时已经建立了第一个问题：

```text
CXL Memory
优点：
容量大、便宜、CPU可以load/store

但是：
① CXL link BW 是瓶颈
② CXL access latency 比 local memory 高
```

---

# 5. 作者于是提出最自然的想法：那我为什么非要把数据搬回 CPU 算？

这就是：

> NDP — Near-Data Processing

你可以把它理解成一句话：

> **数据在哪，就尽量在哪附近算。**

传统做法：

```text
CXL Memory
    |
    | 100 GB data
    ↓
 CXL Link
    |
    ↓
   CPU
    |
 computation
```

NDP：

```text
        CXL Memory
        +--------+
        | DRAM   |
        |        |
        | NDP    | ← 小计算单元
        +--------+
             |
             | 只有命令、少量结果
             ↓
            CPU
```

假设有 10 GB 数据：

```c
sum = 0;
for(i=0;i<N;i++)
    sum += A[i];
```

传统 CPU：

```text
10 GB A[]
CXL Memory
     ↓
   CXL link
     ↓
    CPU
```

要把大量数据跨 CXL 搬过去。

NDP：

```text
CXL Memory内部：
A[]
 ↓
NDP计算sum
 ↓
只返回8 Byte结果
```

这就是 Near-Data Processing 的根本价值：

> **减少跨 CXL link 的 data movement。**

所以论文说，已有很多工作都提出在 CXL memory 中通过 NDP 加速 memory-bound workload。Low-Overhead_General-Purpose_Ne…

到这里，Introduction 前半部分其实非常顺：

```text
需要大内存
 ↓
CXL Memory
 ↓
但是访问 CXL Memory 慢
 ↓
原因：数据必须跨 CXL Link
 ↓
那就在 Memory 旁边计算
 ↓
NDP
```

---

# 6. 可是作者说：现有 NDP 方案也不好

这里 Introduction 开始进入论文真正的创新 Motivation。

作者认为已有方案主要有两个大问题。

你可以把它们分成：

```text
问题 A：
NDP里面“放什么计算硬件”？

问题 B：
CPU怎么“叫这个NDP开始工作”？
```

这两个问题最后分别对应：

```text
M² μthread
M² func
```

这是整篇论文最重要的结构。

---

# 7. 问题 A：在 CXL Memory 里面到底放什么计算硬件？

最简单的想法：

> 每一种应用放一个专用加速器。

比如：

```text
CXL Memory
 ├─ Graph accelerator
 ├─ DLRM accelerator
 ├─ KVStore accelerator
 ├─ Sparse Matrix accelerator
 └─ LLM accelerator
```

这样当然可以快。

但是现实中：

> CXL Memory 是一个通用内存产品。

它未来可能被：

```text
Database
LLM
Graph
Recommendation
Scientific computing
...
```

各种程序使用。

如果每个 workload 都塞一个专用 ASIC：

```text
面积 ↑
功耗 ↑
设计复杂度 ↑
NRE ↑
```

而且新 workload 出现还得重新设计。

论文明确批评已有 CXL NDP 工作通常使用 domain-specific hardware，目标 workload 很有限，而把很多种专用硬件同时塞进 CXL memory 也会带来高面积和 NRE 成本。Low-Overhead_General-Purpose_Ne… Low-Overhead_General-Purpose_Ne…

所以作者想要：

> General-purpose NDP

也就是：

```text
不是只会Graph
不是只会DLRM
不是只会某一种算法

而是一种可编程的小处理器
```

---

# 8. 那直接放 CPU 不就好了？

这是你很自然会问的问题。

例如：

```text
CXL Memory
 |
 +--- RISC-V CPU cores
```

作者说：

> 可以，但是不划算。

为什么？

因为 CPU 是为了通用程序设计的。

现代 CPU 里有大量东西：

```text
OoO execution
复杂 branch prediction
大 Cache
复杂 scheduler
大 Register File
复杂 control logic
```

这些硬件是为了：

> 高性能执行各种复杂程序。

但是作者研究的 NDP workload 是：

```text
memory-bound
arithmetic intensity低
data reuse少
```

也就是说：

```text
load
load
load
简单算一点
load
load
```

计算根本不复杂。

你花大量面积造一个复杂 OoO CPU：

```text
面积：100
```

最后：

```text
ALU大部分时间在等memory
```

显然不经济。

论文 Introduction 明确说，现有 CPU/GPU core 用作 NDP 时 performance-per-cost 不够好，因为它们并不是针对这种 memory-bound workload 优化的。Low-Overhead_General-Purpose_Ne…

---

# 9. 那 GPU 呢？

GPU 看起来比 CPU 合理很多：

```text
大量线程
高并行
高 Memory Level Parallelism
```

所以确实有人拿 GPU-like core 做 NDP。

但作者仍然觉得 GPU 太重。

原因 Introduction 暂时只点到为止，后面 Section III 才详细展开。

当前只需要知道作者的观点：

> NDP 最重要的工作不是堆 FLOPS，而是用较低成本产生很多并发 memory accesses，把 DRAM bandwidth 吃满。

因此它需要：

```text
便宜
大量并发
可编程
适合 memory-bound
```

而不是：

```text
超强计算
大量 Tensor Core
复杂 GPU SM
```

这就是为什么作者没有简单说：

> 我在 CXL Memory 里塞几个 GPU SM。

---

# 10. FPGA 行不行？

论文也提到了。

FPGA 的优势：

```text
programmable
可以适应不同 workload
```

问题：

```text
programmability 很差
```

也就是说：

> 硬件能变，但不是普通软件工程师拿 C/CUDA/RISC-V 程序就能直接跑。

作者希望的是：

```text
general-purpose programmable processor-like NDP
```

而不是每个 workload 都：

```text
RTL
HLS
place & route
bitstream
```

论文对此也直接指出 FPGA 虽然具有 workload adaptability，但存在显著的 programmability challenge。Low-Overhead_General-Purpose_Ne…

---

# 11. 所以作者第一个设计目标出来了

他们希望 CXL Memory 里面的计算单元：

```text
不是 ASIC：
太专用

不是 CPU：
太复杂、面积/功耗贵

不是 GPU：
针对 memory-bound 不够 cost-efficient

不是 FPGA：
不好编程
```

而是：

> 一个很轻量、通用、能够产生大量 memory-level parallelism 的 NDP processor。

这就是后面的：

# M² μthread

但 Introduction 这里先不要管它内部如何实现。

你暂时只记：

```text
M² μthread
=
解决“NDP计算核心应该长什么样”
```

---

# 12. 第二个问题反而更容易被忽略：CPU 怎么告诉 NDP “开始算”？

假设 CXL Memory 里面已经有 NDP：

```text
CPU

 ↓

CXL Memory
┌──────────────┐
│ DRAM         │
│ NDP Processor│
└──────────────┘
```

现在 CPU 想说：

> “帮我执行 VectorAdd kernel。”

这件事情叫：

> NDP offloading

和 GPU 很像。

CPU 调 GPU：

```c
kernel<<<...>>>(...);
```

表面一行代码。

底下实际上要：

```text
CPU
 ↓
runtime
 ↓
driver
 ↓
command queue / ring buffer
 ↓
PCIe
 ↓
GPU
 ↓
launch kernel
```

NDP 也一样。

所以：

```text
NDP计算本身
```

很快还不够。

还有：

```text
CPU → NDP
发命令

NDP → CPU
返回状态
```

的 communication overhead。

---

# 13. 传统 CXL.io / PCIe offload 为什么很慢？

这里是论文 Introduction 非常重要的一句话：

> existing CXL.io/PCIe-based mechanisms incur μs-scale latency

也就是：

```text
微秒级
```

而 CXL.mem：

```text
约百ns量级
```

差一个数量级左右。

论文指出，传统 ring buffer 和 MMIO-based NDP offloading 基于 CXL.io/PCIe，会受到复杂软件/协议路径以及 host kernel-mode switching 等开销影响，因此对于 fine-grained NDP 来说太慢。Low-Overhead_General-Purpose_Ne…

为什么 fine-grained 特别怕？

举个极端例子：

```text
NDP kernel 本身运行：
2 µs

launch overhead：
4 µs
```

那么你：

```text
为了计算2 µs
先花4 µs告诉它开始算
```

完全不值。

就像：

> 你为了让旁边的人帮你算一道 10 秒的算术题，先花了一分钟填审批单。

---

# 14. 那为什么不用 CXL.mem 发命令？

这就是作者最关键的灵感。

CXL.mem 很快：

```text
CPU
 ↓
load/store
 ↓
CXL Memory
```

但是标准 CXL.mem 原本只负责：

```text
Read Memory
Write Memory
```

它并没有定义：

```text
LaunchKernel
RegisterKernel
PollKernelStatus
```

这种 command。

所以出现一个非常有意思的问题：

```text
CXL.io:
什么命令都能搞
但是慢

CXL.mem:
快
但是本来只会读写内存
```

作者就想：

> 能不能“伪装成普通 memory access”，实际上是在调用 NDP function？

这就是：

# Memory-Mapped Function
# M² func

---

# 15. M² func 的核心思想，现在只需要理解到这个程度

假设作者预留：

```text
0x10000 → Register Kernel
0x10020 → Unregister Kernel
0x10040 → Launch Kernel
0x10060 → Poll Status
```

那么 CPU：

```c
store  arguments -> 0x10040
```

表面：

```text
CXL.mem write
```

但 CXL Memory Controller 看到：

```text
Address == 0x10040
```

就不真的把数据写进 DRAM。

而是解释成：

> Launch NDP kernel.

也就是：

```text
memory access
      ↓
 function call
```

所以叫：

> Memory-Mapped Function

论文 Introduction 对它的概括就是：把 NDP management command/function call 封装在对预先指定地址的 CXL.mem request 中，通过 packet filter 检查地址并触发对应 NDP function，从而避免传统 CXL.io/PCIe offload 的高开销。Low-Overhead_General-Purpose_Ne…

这和你学过的：

```text
MMIO
```

思想非常像。

---

# 16. 到这里论文题目已经能看懂一半了

论文叫：

> Low-overhead General-purpose Near-Data Processing in CXL Memory Expanders

拆开：

### Near-Data Processing

```text
在 CXL Memory 附近计算
减少数据跨 CXL 搬运
```

### General-purpose

```text
不要为每个 workload 做专用 ASIC
让一个可编程 NDP unit 跑各种 kernel
```

主要靠：

```text
M² μthread
```

### Low-overhead

```text
CPU启动NDP kernel时不要走慢吞吞的CXL.io/PCIe路径
```

主要靠：

```text
M² func
```

所以整篇论文的核心结构其实就是：

```text
              M² NDP
                 |
        +--------+---------+
        |                  |
     M² func            M² μthread
        |                  |
解决Host-NDP           解决NDP内部
通信开销               计算架构
        |                  |
Low-overhead        General-purpose
```

这张图你最好牢牢记住。

---

# 17. M² μthread 到底是什么？Introduction 只给了预告

作者观察到：

> memory-bound workload 通常不需要很多寄存器。

这是很合理的。

例如：

```c
for(i...)
    C[i] = A[i] + B[i];
```

一个线程可能只需要：

```text
addr A
addr B
addr C
少数临时变量
```

不像复杂 compute kernel：

```text
大量中间变量
大量累加器
大量寄存器
```

所以作者提出：

> 不要给每个 thread 一整套很重的 architectural context。

而是：

```text
µthread
=
lightweight thread
```

只分配这个 kernel 真正需要的一小部分 registers。

这样相同面积里可以保存更多 thread context：

```text
Thread0
Thread1
Thread2
...
Thread63
```

当 Thread0 等 DRAM：

```text
Thread0: load → 等待
Thread1: execute
Thread2: execute
Thread3: execute
```

靠很多线程隐藏 memory latency。

论文 Introduction 描述的正是这个思想：µthread 使用较少 architectural registers，因此可以低成本地运行很多并发 µthreads，并通过 Fine-Grained Multithreading 隐藏 DRAM latency。Low-Overhead_General-Purpose_Ne…

这个和 GPU 的：

```text
warp A等memory
→ 执行warp B
```

精神非常相似。

只是作者后面会解释为什么它认为自己的 µthread 比 GPU thread 更适合这个场景。

---

# 18. 为什么还叫 “Memory-Mapped µthread”？

这一点 Introduction 也简单提到了。

GPU 线程通常：

```text
threadIdx
blockIdx
```

然后程序自己算：

```c
i = blockIdx.x * blockDim.x + threadIdx.x;

x = A[i];
```

作者的想法则更直接：

```text
µthread ↔ memory location
```

比如：

```text
µthread 0 → 0xA000
µthread 1 → 0xA020
µthread 2 → 0xA040
...
```

thread 天生就和某段 data address 对应。

于是地址计算可以减少。

论文说，每个 µthread 与特定 memory location 直接关联，因而能够减少传统 GPU/SIMT 环境里的地址计算代码。Low-Overhead_General-Purpose_Ne…

这一部分你现在知道目的即可，Section III.D 我们之后再拆。

---

# 19. 为什么他们最终采用 modified RISC-V + Vector？

这里和你的背景已经很接近了。

他们需要：

```text
General-purpose
```

所以自然希望：

```text
有ISA
可编程
编译器能支持
```

采用 RISC-V。

又因为 memory workload 中经常存在：

```text
数组
向量
批量处理
```

所以加入：

```text
RVV
RISC-V Vector Extension
```

利用 SIMD。

论文 Introduction 说，它的 NDP unit 使用 modified RISC-V ISA with vector extension，以较低成本使用 SIMD 并尽可能吃满 CXL memory 内部 DRAM bandwidth。Low-Overhead_General-Purpose_Ne…

所以以后看到：

```text
RISC-V
RVV
SIMD
FGMT
µthread
```

不要认为作者突然开始设计 CPU 了。

它们都服务于一个目标：

> **花尽可能小的面积，制造足够多的 outstanding memory requests，把 CXL Memory 内部 DRAM bandwidth 吃满。**

这才是这个 NDP core 的设计哲学。

---

# 20. Introduction 最后一段 Contributions 其实就是复述上面的故事

作者最后总结贡献：

第一：

```text
提出 M²NDP
=
M²func + M²µthread
```

而且不修改标准 CXL.mem，也不要求修改 host processor hardware。Low-Overhead_General-Purpose_Ne…

第二：

```text
M²func
```

降低 host → NDP 的 offloading / management latency，尤其解决 fine-grained NDP 的问题。Low-Overhead_General-Purpose_Ne…

第三：

```text
M²µthread
```

用轻量线程 + FGMT + modified RISC-V vector architecture，做一个比直接塞 CPU/GPU 更 cost-efficient 的通用 NDP core。Low-Overhead_General-Purpose_Ne…

最后实验结果是：

```text
最高 128× speedup
总体 geometric mean 14.5×
最高降低 87.9% energy
```

相对于使用 passive CXL memory 的 baseline host system。Low-Overhead_General-Purpose_Ne…

这些数字现在完全不用记。

---

# 21. 现在用一句完整的话概括 Introduction

如果明天导师突然问你：

> 这篇论文到底是干什么的？

你现在可以这样回答：

> CXL Memory Expander 可以低成本扩展 CPU 的内存容量，但 memory-bound 应用如果由 CPU 频繁访问 CXL Memory，会受到 CXL 链路带宽和访问延迟限制。因此可以在 CXL Memory 侧增加 NDP 单元，让计算靠近数据执行，减少数据跨 CXL 传输。但已有 NDP 一方面往往采用 workload-specific accelerator，通用性不足，而直接使用 CPU/GPU 又不够 cost-efficient；另一方面，CPU 通过传统 CXL.io/PCIe 启动细粒度 NDP kernel 时存在微秒级通信开销。作者因此提出 M²NDP：用 M²func 把 NDP 管理操作编码成 CXL.mem 的 memory access，降低 Host-NDP 通信开销；用 M²µthread 构建一个轻量、可编程、高并发的 RISC-V Vector NDP processor，用于高效执行 memory-bound kernel。

如果这段你能真正理解，而不是背下来，Introduction 就已经理解了大约 80%。

---

# 22. 最后，把整篇 Introduction 压成一条因果链

这个最适合你后面继续阅读时放在脑子里：

```text
应用需要越来越大的内存
        ↓
Local DRAM容量不够 / 成本高
        ↓
使用CXL Memory Expander
        ↓
CPU可以用load/store访问CXL Memory
        ↓
但CPU频繁访问远端CXL Memory
        ↓
CXL link出现
带宽瓶颈 + latency问题
        ↓
尤其伤害memory-bound workload
        ↓
把计算搬到数据旁边
        ↓
NDP
        ↓
但现有NDP有两个问题
        ↓
 ┌──────────────┴──────────────┐
 │                             │
NDP计算硬件怎么设计？       Host怎么调用NDP？
 │                             │
ASIC太专用                 CXL.io/PCIe太慢
CPU/GPU太贵                fine-grained offload
FPGA难编程                 开销可能比kernel还大
 │                             │
 ↓                             ↓
M² μthread                  M² func
 │                             │
轻量可编程RISC-V            用CXL.mem memory access
大量并发线程                表示function call
隐藏DRAM latency            减少offload overhead
 │                             │
 └──────────────┬──────────────┘
                ↓
              M²NDP
```

下一步最合适的是继续拆 **II-A “Considerations in Architecting NDP in CXL Memory”**。这一节其实就是 Introduction 中“为什么不用 GPU/CPU，NDP 硬件到底应该长什么样”的正式论证；它里面的 Table I 非常关键，而且比 II-B、II-C 更容易先讲清楚。