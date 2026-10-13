可以。第二章其实不是在“漫无目的地补背景”，而是在为后面的 M²NDP 方案逐层铺设约束条件。你如果带着上一轮已经建立的两个问题去看，会容易很多：

> 问题 1：CXL Memory 里的 NDP 计算单元应该设计成什么样？  
> 问题 2：Host 应该怎样低开销地调用这个 NDP？

Section II 的 A、B、C 分别就是：

```text
II-A：先确定“NDP计算单元应该是什么样”
          ↓
II-B：再说明“CXL这个平台本身给了我们什么能力、又有什么限制”
          ↓
II-C：最后证明“传统Host→NDP通信方案真的太慢”
          ↓
Section III：
开始提出 M² μthread + M² func
```

所以第二章实际上就是整篇论文的“需求分析”。

---

# 一、II-A：Considerations in Architecting NDP in CXL Memory

这一节回答的核心问题是：

> 如果我们决定在 CXL Memory 里面加计算，那么这个计算硬件到底应该设计成什么样？

作者首先强调一件很容易误解的事情：

> “CXL Memory 里面加 NDP”虽然看起来有点像“给内存旁边塞一个 GPU”，但它和 GPU 的设计目标其实完全不同。

论文的 Table I 就是在讲这个区别。表里总结得非常直接：

```text
                           GPU             CXL Memory + NDP

Memory capacity            Low                  High
Cost(area/power)           High                 Low
FLOPS / Memory BW          High                 Low
Target workload        Compute-bound        Memory-bound
```

Low-Overhead_General-Purpose_Ne…

这里最值得理解的是后两行。

GPU 的设计目标是：

```text
大量计算资源
大量 FLOPS
+
高内存带宽
```

所以它非常适合：

```text
Matrix Multiplication
Convolution
Transformer GEMM
```

这种 compute-intensive workload。

但这篇论文的 NDP 面向的是：

```text
大量访存
少量计算
低 arithmetic intensity
```

比如：

```text
读 64 B
做几个加法
再读 64 B
```

这种情况下，你根本不需要几十、几百 TFLOPS。

作者甚至明确说，CXL NDP 主要针对的是“大 working set、低 arithmetic intensity、不能放进片上 Cache”的 memory-bound workload；如果程序本身 compute-bound，或者 working set 很小能够很好利用 CPU/GPU Cache，那么继续在 Host/GPU 上算反而更合适。Low-Overhead_General-Purpose_Ne…

所以 II-A 的第一个结论其实是：

> **不要把 NDP 设计成一个缩小版高性能 GPU。**

---

接下来就出现一个“成本约束”。

为什么不能直接：

```text
CXL Memory
+
100 个 GPU SM
```

？

因为 CXL Memory Expander 本质首先还是一个：

> Memory Expansion Device。

它的核心价值是：

```text
大容量
低成本
```

而不是：

```text
昂贵的Compute Accelerator
```

论文明确说，GPU 可以有 hundreds of SM，但 CXL Memory 不可能为了 NDP 也复制这种高成本配置。Low-Overhead_General-Purpose_Ne…

所以作者真正想要的是：

```text
                     理想NDP计算单元

                         通用
                          ↑
                          |
               可编程 ----+---- 低成本
                          |
                          ↓
                 足够高的访存并发度
                          |
                          ↓
                 吃满内部DRAM带宽
```

注意最后一句尤其重要。

作者追求的不是：

> “怎样最大化 FLOPS？”

而是：

> “怎样用尽可能低的硬件成本，制造足够多的并发 memory request，把 CXL Memory 自己内部的 DRAM bandwidth 吃满？”

这就直接为后面的：

```text
轻量 µthread
+
Fine-Grained Multithreading
+
RISC-V Vector
```

埋下伏笔。

换句话说，II-A 是在论证：

> **为什么后面需要 M² µthread 这样一个“不像 CPU、也不像传统 GPU”的轻量通用处理器。**

---

还有一个细节你以后读 Section III 时会反复遇到：

> general-purpose NDP 并不一定比专用 ASIC 慢很多。

作者的理由是：

对于 memory-bound workload：

```text
Performance ≈ 能不能把 Memory BW 吃满
```

而不是：

```text
Performance ≈ 有多少ALU / FLOPS
```

所以如果一个通用 NDP processor 已经能够把 DRAM bandwidth saturate，那么再换成专用逻辑，性能可能也不会提升很多。

这其实是作者选择“general-purpose”方案的理论依据。

因此 II-A 可以压缩成一句话：

> **CXL NDP 面向的是“大数据、低计算强度”的 memory-bound workload，因此硬件重点应该是低成本地制造高访存并发，而不是堆 FLOPS；这为后面的轻量 M² µthread 架构提供了设计依据。**

---

# 二、II-B：Compute Express Link Interconnect

II-B 第一眼看上去最吓人，因为突然出现：

```text
CXL.io
CXL.cache
CXL.mem
HDM
HDM-H
HDM-DB
DCOH
BI
ATS
ATC
P2P
```

但实际上，这一整节只是在回答：

> **“我们设计 M²NDP 的时候，CXL 这个平台到底允许我们做什么？”**

所以你不要把它当成“完整学习 CXL 协议”。

它只是挑了和这篇论文有关的部分。

---

## 2.1 先复习三个 CXL Protocol

论文首先说，CXL 使用 PCIe PHY，并定义三类协议：

```text
CXL.io
CXL.cache
CXL.mem
```

其中：

```text
CXL.io
≈ PCIe-style I/O
用于 device management


CXL.cache
用于 Host ↔ Device Cache Coherence


CXL.mem
用于 Host 访问 CXL Device Memory
```

Low-Overhead_General-Purpose_Ne…

对于这篇论文而言，真正的主角是：

# CXL.mem

因为它允许：

```text
CPU
 |
 | 普通 load / store
 ↓
CXL Memory
```

Host 不需要像传统 PCIe accelerator 那样：

```text
DMA
copy buffer
explicit transfer
```

而是可以直接：

```c
x = *ptr;
```

访问 CXL memory。

---

# 三、为什么论文一直强调 CXL.mem 比 CXL.io 快？

这是 II-B 中真正重要的性能背景。

论文给出的一个典型数字：

```text
CXL Memory Load-to-Use latency
≈ 150 ns
```

这个 150 ns 包含：

```text
Host Cache hierarchy
+
CXL protocol stack
+
off-chip wire
+
DRAM
```

而单纯 CXL protocol stack + physical wire 的 round trip，大约可以做到：

```text
≈ 70 ns
```

如果经过 CXL Switch，整体 CXL memory access latency 可能接近：

```text
≈ 300 ns
```

相比之下，论文认为传统 CXL.io/PCIe communication：

```text
≈ 1 µs 或更高
```

Low-Overhead_General-Purpose_Ne…

这里有一个很容易误读 Fig. 2 的地方：

> Fig. 2 上面的 52–70 ns，并不是“访问一次 CXL DRAM 总共只要 70 ns”。

它描述的是：

```text
CXL protocol stack
+
link / wire
```

的 round trip。

真正：

```text
load
→ data回来
→ CPU能够use
```

还要算 DRAM 等，所以论文使用的是：

```text
~150 ns load-to-use
```

这个区分以后看实验部分会用到。

---

# 四、HDM 是什么？

接下来论文突然说：

> Host-managed Device Memory，HDM

你可以把它理解成：

> CXL Memory Expander 上那块被 Host 当作系统内存管理的 Device DRAM。

例如：

```text
CPU Physical Address Space

0x0000...
    ↓
Local DRAM

0x8000...
    ↓
CXL Memory / HDM
```

Host 可以通过 Host Physical Address：

```text
HPA
```

访问它。

论文这里进一步区分：

```text
HDM-H
HDM-DB
```

Low-Overhead_General-Purpose_Ne…

这两个对你理解论文非常重要。

---

# 五、HDM-H：适合“Passive CXL Memory”

Passive CXL Memory 就是：

```text
CXL Memory Expander
┌─────────────────┐
│ CXL Controller  │
│                 │
│      DRAM       │
└─────────────────┘
```

没有 NDP。

它自己不会主动去修改 Host 正在 Cache 的那些 CXL memory data。

CPU：

```text
load CXL Memory
↓
Cache line进入CPU Cache
```

设备本身只是老老实实当 Memory。

这种情况下使用：

> HDM-H

就可以。

论文称其为 host-only coherent model，主要面向 passive memory expander。Low-Overhead_General-Purpose_Ne…

---

# 六、可是加了 NDP 后，情况发生了根本变化

现在：

```text
             CPU
              |
            Cache
              |
             CXL
              |
      CXL Memory
 ┌────────────────────┐
 │ NDP Processor      │
 │                    │
 │ DRAM               │
 └────────────────────┘
```

假设 CPU Cache 里面保存：

```text
A = 10
```

然后 NDP 直接把 CXL DRAM 里的 A 改成：

```text
A = 20
```

那么：

```text
CPU Cache: A = 10
CXL Memory: A = 20
```

出现 coherence problem。

这和我们上一轮讲 MESI 的问题是同一个本质：

> 有多个地方可能保存同一个地址的数据。

因此 NDP 不能简单地：

```text
直接偷偷改DRAM
```

而不告诉 Host Cache。

---

# 七、所以论文选择 HDM-DB

HDM-DB 支持：

```text
DCOH
Device Coherence Agent
```

以及：

```text
Snoop Filter
```

用来追踪：

> Host 到底 Cache 了哪些 HDM Cache Line。

当 NDP 想修改某个数据，而 CPU Cache 里可能还有副本时：

```text
CXL Device
   |
   | Back-Invalidate
   ↓
Host Cache
```

把 Host 里的 Cache Line invalid 掉。

论文把这个机制称为：

> BI — Back Invalidation

因此作者明确说：

> HDM-DB 很适合带 NDP capability 的 CXL Memory，M²NDP 就采用这种模型。Low-Overhead_General-Purpose_Ne…

这部分你可以直接和之前学的 MESI 对起来：

```text
CPU Core 0写
→ invalidate Core 1 Cache
```

现在变成：

```text
CXL NDP写
→ invalidate Host CPU Cache
```

本质非常接近。

所以这里终于和你们项目里导师说的：

> “通过 CXL 扩展 Cache coherence”

产生连接了。

---

# 八、为什么论文还提 ATS / ATC？

这一段第一次读很容易完全迷路。

其实作者只是在说一个限制：

> **CXL.mem 主要解决 Host → Device Memory 的访问，不意味着 Device 可以通过 CXL.mem 随便访问 Host DRAM。**

也就是：

```text
Host
  |
  | CXL.mem
  ↓
CXL Device Memory
```

很自然。

但是：

```text
CXL Device
  |
  | ???
  ↓
Host Memory
```

不是直接靠 CXL.mem 就解决。

论文提到，如果 CXL device 要做地址转换，可以利用 PCIe 定义的：

```text
ATS
Address Translation Services
```

设备向 Host 请求：

```text
Virtual Address
→ Physical Address translation
```

但这个过程可能很慢：

```text
µs-scale
```

因为可能经过协议和 Host page-table walk。

所以 Device 里通常还会放：

```text
ATC
Address Translation Cache
```

相当于：

> Device-side TLB-like cache

把最近的地址转换结果缓存起来。Low-Overhead_General-Purpose_Ne…

对于你当前读 II-B：

**知道这个意思就够了。**

后面 Section III-H Virtual Memory Support 再回来详细看。

---

# 九、为什么又突然提 CXL 3.0 P2P？

论文还提到：

```text
CXL Device A
     |
   Switch
     |
CXL Device B
```

设备之间可以：

> Peer-to-Peer 访问彼此的 CXL Memory。

作者为什么现在讲这个？

因为以后可能有：

```text
CXL-M²NDP 0
CXL-M²NDP 1
CXL-M²NDP 2
...
```

多个 NDP-enabled memory expander。

NDP 0 的 kernel 可能需要访问：

```text
NDP 1的Memory
```

P2P 就允许这种扩展。

这主要是为后面：

> Multiple CXL-M²NDP scalability

铺垫。

第一遍完全不用深究。

---

# 十、所以 II-B 真正要你带走什么？

不要记十个缩写。

只需要记住下面这个结构：

```text
CXL.mem
    ↓
Host可以低延迟load/store CXL Memory
    ↓
这给M²func提供了“快速通信通道”


HDM-DB + Back Invalidation
    ↓
允许NDP修改CXL Memory时
维持Host Cache coherence
    ↓
这给NDP真正参与计算提供正确性基础


ATS / ATC
    ↓
解决Device侧地址转换的一部分问题


CXL P2P
    ↓
允许未来多个CXL Memory/NDP之间扩展
```

所以 II-B 的作用就是：

> **告诉你作者设计 M²NDP 时，手里有哪些 CXL 机制可以利用，以及 CXL 本身有哪些边界条件。**

---

# 十一、II-C：Communication Overhead with CXL.io/PCIe

这一节是第二章最重要的一节之一。

因为它是在正式证明：

> **为什么仅仅有 M² µthread 还不够，为什么一定还需要 M² func。**

也就是你上一轮已经理解的第二个问题：

```text
NDP kernel自己可能很快

BUT

CPU怎么启动它？
```

---

# 十二、传统 Accelerator 是怎么 launch kernel 的？

你平时写 CUDA：

```c
kernel<<<grid, block>>>(args);
```

看起来一条语句。

但硬件下面不是：

```text
CPU
→ 发一个包
→ GPU立刻开始
```

而往往是一个相当复杂的 command submission system。

论文举的是：

> Ring Buffer

可以先把它理解成一个：

```text
Host和Device共享的Command Queue
```

比如：

```text
Ring Buffer:

| CMD0 | CMD1 | CMD2 | empty | empty |
                      ↑
                    tail
```

CPU 想启动 kernel：

```text
1. 准备Command
2. Command放到queue里
3. 更新tail pointer
4. 通知Device
```

GPU / Device：

```text
5. 发现tail改变
6. DMA读取Command pointer
7. DMA读取真正Command
8. 执行Kernel
```

这就是为什么“调用一次 accelerator”并不等于一次简单的 PCIe write。

---

# 十三、论文描述的 Ring Buffer Launch 到底发生了什么？

作者描述的是类似 GPU 的传统流程：

```text
User Program
    |
    ↓
Runtime
    |
    ↓
Driver
    |
Kernel Space
    |
    ↓
把GPU command写入Ring Buffer
    |
    ↓
更新write/tail pointer
    |
    ↓
PCIe / CXL.io
    |
    ↓
Device发现新Command
    |
    ↓
DMA fetch command pointer
    |
    ↓
DMA fetch command
    |
    ↓
Launch kernel
```

这个过程中需要：

```text
Host SW
+
kernel driver
+
ring buffer management
+
CXL.io protocol
+
multiple DMA
```

于是开销就上来了。

论文给出的估算是：

```text
Kernel Launch:
约 3–6 µs
```

而且可能涉及大约：

```text
2.5 CXL.io round trips
```

Low-Overhead_General-Purpose_Ne…

---

# 十四、执行完之后还没结束

Host 还得知道：

> Kernel 到底算完没有？

通常两种方法：

```text
Polling
```

或者：

```text
Interrupt
```

论文说：

```text
PCIe polling
≈ 2–3 µs

Interrupt
≈ 类似甚至更高
```

DMA 本身也有：

```text
≥ ~1 µs
```

的典型延迟。Low-Overhead_General-Purpose_Ne…

于是整个时间轴可能变成：

```text
CPU                         NDP

 |                           |
 |---- launch 3~6µs -------->|
 |                           |
 |        kernel 2µs         |
 |                           |
 |<-- completion 2~3µs ------|
 |
```

假设真正 kernel：

```text
2 µs
```

结果通信：

```text
5~9 µs
```

那么 NDP 本身再快都没有意义。

---

# 十五、这就是 fine-grained NDP 最怕的问题

如果 kernel 很长：

```text
kernel = 100 ms
launch = 5 µs
```

那：

```text
5 µs / 100 ms
≈ 0.005%
```

可以忽略。

这种叫 overhead 被：

> amortized

掉了。

但如果：

```text
kernel = 1 µs
launch = 5 µs
```

那就完全反过来了。

所以作者真正针对的是：

> fine-grained NDP offloading

也就是：

```text
kernel短
任务小
调用频繁
```

这时 communication overhead 成了主导因素。

这和你们光刻项目中的实时短周期任务，其实在“控制开销不能超过有效计算”这个抽象层面是很相似的——虽然具体工作负载并不相同。

---

# 十六、那不用 Ring Buffer，直接 MMIO 写 Device Register 行不行？

作者也讨论了这个办法。

比如 Device 暴露：

```text
START_REGISTER
STATUS_REGISTER
```

Host：

```c
*START_REGISTER = kernel_id;
```

然后：

```c
while (*STATUS_REGISTER != DONE);
```

确实比复杂 Ring Buffer 简单。

论文说，直接访问 device-side register 的 MMIO 方案可以避免一部分 ring-buffer overhead。Low-Overhead_General-Purpose_Ne…

但是它有两个问题。

第一：

```text
Dedicated Physical Register
```

数量有限。

比如：

```text
ARG0
ARG1
START
STATUS
```

这套 Register 正在服务 Kernel A 时，就很难同时安全接受 Kernel B。

所以：

> 不适合大量 concurrent requests。

第二：

这些 Device Register 是：

```text
physical device resource
```

不能像普通虚拟内存一样自然地分给：

```text
Process A
Process B
Process C
```

因此需要 privileged access / driver involvement，可能产生：

```text
User Space
↓
Kernel Space
↓
Device
```

context switch。

论文明确指出，直接 MMIO register 方案不能很好支持多个并发请求，而且这些物理资源不能安全地被多个 user process 共享，每次访问可能需要切换到 kernel space。Low-Overhead_General-Purpose_Ne…

所以：

```text
Ring Buffer
    ↓
并发性可以
但复杂 + 慢


Direct MMIO Register
    ↓
简单一点 + 较快
但并发差 + 多进程困难
```

作者两个都不满意。

---

# 十七、于是 Section II-C 自然推出 M² func

现在再看作者的设计目标就非常清楚了。

他们想要一种通信机制同时满足：

```text
Latency低
        +
能支持并发kernel
        +
User space可以直接调用
        +
不频繁进入kernel
        +
不需要修改Host CPU
        +
不修改CXL标准
```

那现成什么协议最快？

```text
CXL.mem
```

于是作者问：

> 既然 Host 已经可以通过 CXL.mem 用普通 load/store 在约百 ns 量级访问 CXL Memory，为什么不能把“Launch Kernel”也伪装成一次 Memory Access？

这就直接进入 Section III：

```text
Reserved Address Range
         ↓
Host普通store
         ↓
CXL.mem write packet
         ↓
Packet Filter发现：
“这个地址不是普通DRAM”
         ↓
解释成：
LaunchKernel(...)
```

所以 M² func 不是作者凭空想出来的 clever trick。

它是 II-C 逼出来的。

---

# 十八、现在把 A、B、C 连成完整逻辑

第二章真正的论证链是：

```text
II-A
我们要做NDP
↓
但NDP不能照搬GPU/CPU
↓
因为目标是memory-bound workload
↓
核心需求是：
低cost + 高memory concurrency + general-purpose
↓
因此后面需要
M² µthread


              ↓


II-B
我们部署在CXL Memory里
↓
CXL提供：
CXL.mem
HDM-DB / BI coherence
ATS/ATC
P2P
↓
其中最重要的是：
CXL.mem非常适合Host低延迟访问Device Memory
↓
因此它有潜力承担更多事情


              ↓


II-C
现有Host→NDP通信
主要靠CXL.io/PCIe
↓
Ring Buffer:
并发可以，但µs级开销
↓
Direct MMIO:
简单，但并发和多进程差
↓
fine-grained NDP无法接受
↓
那就利用低延迟CXL.mem
↓
M² func
```

因此：

```text
II-A  → M² µthread 的 Motivation

II-B  → M²NDP 能利用哪些 CXL 机制

II-C  → M² func 的 Motivation
```

这三句话基本就是第二章的骨架。

---

# 十九、Table I 和 Fig. 2 应该分别怎么看

这两个图表很容易把注意力带偏，所以单独说一下。

Table I 不是让你背参数。

它在表达：

> GPU 和 CXL-NDP 的“产品设计目标”完全不同。

核心就是：

```text
GPU:
Cost高
Compute能力高
Memory capacity相对低
服务compute-bound


CXL NDP:
Cost必须低
Compute能力不用很高
Memory capacity高
服务memory-bound
```

所以 Table I 是 M² µthread 的设计哲学来源。

---

Fig. 2 也不是让你背 CXL Packet Pipeline 每一层。

它真正想表达：

```text
PCIe / CXL.io path
    ↓
协议/软件/事务路径复杂
    ↓
latency较高


CXL.mem path
    ↓
针对Memory Semantic优化
    ↓
latency明显更低
```

以及：

```text
CXL.mem protocol + link
~几十ns级round trip

完整CXL Memory Load-to-Use
~百ns级

CXL.io / PCIe通信
~µs级
```

这就是为什么作者后面敢提出：

> 用 CXL.mem 做 NDP communication。

---

# 二十、你现在不需要完全掌握的 II-B 术语

第一次阅读到这里，我建议你暂时只做到“看到词知道它大概负责什么”：

```text
HDM
= Host管理的CXL Device Memory

HDM-H
= Passive CXL Memory使用的Host-only模式

HDM-DB
= Device也会操作Memory时使用，
  支持Device coherence

DCOH
= Device Coherence Agent

BI
= Back Invalidation，
  Device让Host的Cache Line失效

Snoop Filter
= 跟踪哪些Host Cache可能保存某条数据

ATS
= Device向Host请求地址转换

ATC
= Device缓存地址转换结果

P2P
= CXL Device之间直接访问
```

其中当前真正需要牢牢记住的只有三个：

```text
CXL.mem
HDM-DB
Back Invalidation
```

ATS/ATC/P2P 到论文后面出现时再深入，不会影响现在理解主线。

---

# 二十一、第二章读完后，你应该形成的最终 mental model

你现在可以把整篇论文的系统先画成：

```text
                  Host CPU
              ┌─────────────┐
              │ Application │
              │             │
              │ CPU Cache   │
              └──────┬──────┘
                     │
                     │ CXL
                     │
          ┌──────────▼───────────────┐
          │ CXL Memory Expander      │
          │                          │
          │ CXL Controller           │
          │      │                   │
          │      ├── NDP Controller  │
          │      │                   │
          │      ├── NDP Units       │
          │      │    ↑              │
          │      │ M² µthread        │
          │      │                   │
          │      └──────── DRAM      │
          └──────────────────────────┘
```

然后脑子里带着两个箭头：

```text
Host → NDP

问题：
如何低延迟launch kernel？

答案：
M² func
利用CXL.mem
```

以及：

```text
NDP → DRAM

问题：
如何便宜地制造大量并发memory access？

答案：
M² µthread
轻量线程 + FGMT + RISC-V Vector
```

而 II-B 中的 coherence 负责保证：

```text
Host Cache
     ↕
CXL Memory / NDP
```

共享数据时不会出现“Host 还拿着旧 Cache Line”这种错误。

至此，Introduction + Section II 实际上已经把全文最重要的设计动机全部讲完了。

下一章 Section III 并不是再提出新的“大问题”，而是开始回答：

> **既然问题已经确定，那 M² func 和 M² µthread 到底具体怎么做？**

因此后续阅读 Section III 时，可以不再从头理解动机，而是不断问两个问题：

> “这个机制是在实现 M² func，还是 M² µthread？”  
> “它具体解决前面哪一个 bottleneck？”

用这个视角读，Section III 会比 II-B 容易很多。