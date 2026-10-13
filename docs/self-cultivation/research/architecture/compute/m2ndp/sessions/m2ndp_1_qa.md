你现在卡住的不是某个缩写，而是还没有把这篇论文里的“软件对象”和“硬件实体”一一对应起来。这个问题确实需要先彻底解决，否则后面看到 kernel、thread、resource、launch、controller、queue 时都会觉得作者在“抽象地说好处”。

先给一个最重要的纠正：

> **M² µthread 不是一块硬件。**
>
> 真正的硬件叫 **NDP Unit**。  
> M² µthread 是这块硬件采用的一种“线程执行/调度抽象”。

类似于：

```text
CPU Core        = 硬件
CPU thread      = 执行上下文

GPU SM          = 硬件
CUDA thread     = 软件/执行实例

NDP Unit        = 硬件
M² µthread      = 轻量执行实例 / 硬件线程上下文
```

而：

> **NDP kernel 是一段程序代码。**

所以先把整篇论文映射成下面这张图：

```text
Host CPU
┌───────────────────────────────────┐
│ User Process A                    │
│   ndpLaunchKernel(...)            │
│                                   │
│ User Process B                    │
│   ndpLaunchKernel(...)            │
└───────────────┬───────────────────┘
                │
                │ load/store
                │ CXL.mem
                ▼
================================================ CXL Link
                ▼
CXL Memory Expander
┌────────────────────────────────────────────────────────┐
│ CXL Controller                                         │
│                                                        │
│  Packet Filter                                         │
│      │                                                 │
│      ├─ 普通地址 ──────────────→ DRAM Controller       │
│      │                                                 │
│      └─ M²func地址 ──→ NDP Controller                  │
│                             │                          │
│                    kernel launch / scheduling          │
│                             │                          │
│                ┌────────────┼────────────┐             │
│                ▼            ▼            ▼             │
│             NDP Unit 0   NDP Unit 1 ... NDP Unit 31   │
│                │            │                          │
│            µthreads      µthreads                      │
│                │            │                          │
│                └────── Memory NoC ─────────┐           │
│                                            ▼           │
│                                    Memory Controllers  │
│                                            │           │
│                                      LPDDR / DRAM      │
└────────────────────────────────────────────────────────┘
```

论文明确说 M² func 和 M² µthread 都位于带 NDP 的 CXL memory 侧，并由 CXL controller 芯片实现；M² func 负责 host–NDP communication，M² µthread 负责 NDP kernel execution。Low-Overhead_General-Purpose_Ne…

下面按你的 10 个问题回答。

---

# 1. NDP Unit 到底是什么硬件？

这里其实 Section III-E 的 Fig. 7 已经把答案画出来了，只是你现在刚读到 III-D，所以之前还没看到完整硬件。

作者的 NDP Unit 本质上可以理解成：

> **一个高度简化、面向 memory-bound workload 的多线程 RISC-V Vector 小处理器。**

不是 MAC array，不是固定功能加速器，也不是普通 OoO CPU。

论文的 Fig. 7 中，一个 NDP Unit 大概包含：

```text
NDP Unit
│
├── µthread Generator
│     负责产生新的 µthread
│
├── 多个 NDP Sub-core
│
│    Sub-core 0
│    ├── µthread slots
│    ├── decoder / register renaming
│    ├── register file
│    ├── scalar ALU
│    ├── scalar SFU
│    ├── scalar LSU
│    ├── vector ALU
│    ├── vector SFU
│    └── vector LSU
│
│    Sub-core 1
│    ...
│
├── L1 Instruction Cache
├── L1 Data Cache
├── Scratchpad Memory
├── I-TLB
├── D-TLB
│
└── Memory interconnect
      ↓
    L2 / Memory Controller / DRAM
```

论文明确描述了 NDP Unit 具有多个 sub-core、µthread generator、µthread slots、register file，以及 scalar/vector execution units；µthread 之间通过 FGMT 交错发射，而单个 µthread 内部的指令是顺序执行的。Low-Overhead_General-Purpose_Ne…

论文评估时甚至给了一个具体配置：

```text
32 NDP Units @ 2 GHz

每个 NDP Unit：
4 sub-cores

每个 sub-core：
16 µthread slots

因此每个 NDP Unit：
4 × 16 = 64 个硬件 µthread context

还有：
48 KB register file
128 KB scratchpad / L1D
256-bit vector units
scalar ALU / SFU / LSU
vector ALU / SFU / LSU
```

Low-Overhead_General-Purpose_Ne…

所以你完全可以把它理解成：

> “一堆很小、很简单、没有 OoO 的 RISC-V Vector cores，通过大量轻量硬件线程隐藏 DRAM latency。”

它的核心竞争力不是：

```text
单线程 IPC 很高
```

而是：

```text
非常多 outstanding memory accesses
        ↓
把 DRAM bandwidth 吃满
```

---

# 2. NDP Controller 是什么？硬件还是软件？

论文中的 NDP Controller 是：

> **CXL Memory Expander 内部的控制硬件。**

论文明确说，它类似于 GPU 中用于控制管理工作的 microcontroller。Low-Overhead_General-Purpose_Ne…

它不是 Host Linux 上的 daemon，也不是用户程序。

可以把整个 CXL Memory 分成两个层次：

```text
Control Plane
─────────────
NDP Controller

Data / Execution Plane
──────────────────────
NDP Units
```

NDP Controller 大概负责：

```text
接收 M²func command
        ↓
解析：
RegisterKernel?
LaunchKernel?
PollStatus?
        ↓
维护 kernel metadata
        ↓
检查 NDP resource
        ↓
给 NDP Units 分配执行资源
        ↓
启动 µthread generator
        ↓
跟踪 kernel completion
        ↓
返回 status / kernelInstanceID
```

比如 Host 发：

```text
ndpLaunchKernel(...)
```

它并不是直接连到 ALU。

而是：

```text
Host
 ↓
Packet Filter
 ↓
NDP Controller
 ↓
NDP Unit
```

所以它有点类似 GPU 里的 command processor / firmware controller。

但要注意：论文并没有把 NDP Controller 的 RTL 微架构详细画出来，因此“内部到底几个 FSM、有没有小 RISC-V core”等更底层细节，论文没有明确给出，不能从本文确定。

---

# 3. Kernel、Thread、Resource 分别到底是什么？

这是最需要厘清的一组概念。

## Kernel：软件程序

Kernel 本质是：

> **一段准备让 accelerator/NDP 执行的程序。**

例如 VectorAdd：

```c
void VectorAdd(...) {
    load A
    load B
    add
    store C
}
```

最终在本文里会被编译成：

> modified RISC-V + RVV instructions。

所以 NDP kernel 是：

```text
机器指令代码
+
一些 metadata
```

例如注册一个 kernel 时，要告诉系统：

```text
codeLoc
scratchpadMemSize
numIntRegs
numFloatRegs
numVectorRegs
```

这些就是 Table II 的 `ndpRegisterKernel()` 参数。Low-Overhead_General-Purpose_Ne…

因此：

```text
NDP kernel = 软件代码
```

不是硬件。

---

## µthread：一次 kernel 的轻量执行实例

例如 kernel 是：

```c
C[i] = A[i] + B[i]
```

那么可能产生：

```text
µthread 0：
处理 A[0:7]

µthread 1：
处理 A[8:15]

µthread 2：
处理 A[16:23]
...
```

所有 µthread 执行：

> 同一套 kernel code，

但是：

> 对不同数据执行。

所以：

```text
Kernel
= “做什么”

µthread
= “这段kernel代码的一次执行实例”
```

类似 CUDA：

```text
CUDA kernel
↓
大量 CUDA threads
```

这里只是：

```text
NDP kernel
↓
大量 M² µthreads
```

---

## µthread 在硬件里是什么？

具体就是一份硬件 context，例如：

```text
PC
register mapping/base IDs
CSR/state
current decoded instruction info
```

Fig. 7 中每个：

```text
µthread slot
```

就是保存一个 µthread 当前执行状态的地方。Low-Overhead_General-Purpose_Ne…

因此它不是一块完整 processor。

例如 64 个 µthread：

```text
µthread 0
µthread 1
...
µthread 63
```

并不代表造了 64 套 vector ALU。

而是：

```text
64份 thread context
      ↓
共享少量 ALU / LSU / Vector Units
```

每个 cycle 调度其中一些执行。

这和 GPU 一个 SM 可以 resident 很多 warp/thread，但并不是每个 thread 独占完整 datapath 是同一思想。

---

## Resource 是什么？

论文中说：

> “available resource is insufficient”

这里不是一个抽象的软件概念。

主要指实际硬件资源，例如：

```text
µthread slots
physical registers
scratchpad capacity
NDP Unit execution capacity
launch queue / buffer entries
```

例如：

Kernel A 要：

```text
100个µthreads
5个INT register / thread
3个Vector register / thread
64KB scratchpad
```

Kernel B 又来了。

如果剩下：

```text
µthread slots不够
或者
register file不够
或者
scratchpad不够
```

B 就不能马上 fully resident。

于是：

```text
Kernel B launch
→ pending/buffered
→ 等A释放resource
```

论文明确说明，当可用 NDP resource 不足时，launch request 会被 buffer，等前面的 kernel 完成后再服务；buffer 满则返回 error。Low-Overhead_General-Purpose_Ne…

---

# 4. Ring Buffer 和 Direct MMIO 到底是硬件还是软件？

答案是：

> **它们都是“软硬件共同组成的 Host–Device communication mechanism”。**

不能单纯叫软件协议，也不能单纯叫一块硬件。

---

## Ring Buffer 是什么？

本质是：

> Host 和 Device 共享的一块循环命令队列。

假设内存中：

```text
Ring Buffer:

+------+------+------+------+------+
| CMD0 | CMD1 | CMD2 | empty| empty|
+------+------+------+------+------+
                     ^
                   tail
```

Host 软件不断往里面：

```text
enqueue command
```

Device 不断：

```text
dequeue command
```

这部分“Ring Buffer 数据结构”是软件定义的。

但是整个机制还需要硬件支持：

```text
PCIe/CXL.io transaction
DMA engine
device command processor
doorbell register
interrupt/polling
```

所以真实流程类似：

```text
User Program
   |
   | launch API
   v
Runtime / Driver
   |
   | 创建 command descriptor
   v
Host Memory中的 command
   |
   | 将command pointer放进ring buffer
   v
Ring Buffer
   |
   | 更新tail pointer / doorbell
   v
PCIe / CXL.io
   |
   v
Device
   |
   | DMA #1
   | 读取command pointer
   |
   | DMA #2
   | 读取真正command
   v
Command Processor
   |
   v
Launch Kernel
```

论文正是这样描述：Host runtime/driver 把 command 放入共享 ring buffer，更新 write/tail pointer 通知设备，设备随后通过 DMA 获取 command。Low-Overhead_General-Purpose_Ne…

所以每一个步骤都有具体东西在动：

```text
软件：
构造command
维护queue

硬件：
PCIe packet
DMA read
device command fetch
```

---

## Direct MMIO 是什么？

更简单。

设备在 PCIe BAR 中暴露一些 register：

```text
0x00 COMMAND
0x08 ARG0
0x10 ARG1
0x18 STATUS
```

Host：

```c
MMIO_ARG0 = ...
MMIO_ARG1 = ...
MMIO_COMMAND = START;
```

硬件路径：

```text
CPU store
 ↓
PCIe Root Complex
 ↓
PCIe Memory Write TLP
 ↓
Device BAR
 ↓
Device Register
 ↓
Command Logic
```

完成后 Host：

```text
MMIO read STATUS
```

或者 device 发 interrupt。

所以 Direct MMIO：

> 本质是 CPU 直接读写 Device Register。

比 Ring Buffer 少了：

```text
queue management
DMA fetch command
```

所以更简单、更快。

但论文指出它的问题是：

```text
固定device register资源有限
难以支持多个concurrent requests
多process共享困难
```

Low-Overhead_General-Purpose_Ne…

---

# 5. 三种通信路径到底差多少延迟？

现在就可以把 Fig. 5 看懂了。

论文定义：

```text
x = CXL.mem one-way latency ≈ 75 ns

因为：
round-trip load-to-use ≈ 150 ns
```

以及：

```text
y = CXL.io / PCIe one-way ≈ 500 ns

因为：
round-trip ≈ 1 µs
```

论文 Fig. 5 给出这两个近似值。Low-Overhead_General-Purpose_Ne…

然后：

### M² func

通信开销大约：

```text
2x

= 2 × 75 ns
= 150 ns
= 0.15 µs
```

---

### Ring Buffer

Fig. 5 抽象模型：

```text
8y

= 8 × 500 ns
= 4 µs
```

---

### Direct MMIO

约：

```text
3y

= 3 × 500 ns
= 1.5 µs
```

如果论文 Fig. 5 的例子中：

```text
NDP kernel runtime z = 6.4 µs
```

那么总时间大概：

```text
M²func:
6.4 + 0.15
= 6.55 µs

Direct MMIO:
6.4 + 1.5
= 7.9 µs

Ring Buffer:
6.4 + 4
= 10.4 µs
```

这下所谓：

> “M² func 减少通信开销”

就不是一句空话了。

它实际上在减少：

```text
Host准备command
+
多次CXL.io round-trip
+
DMA fetch
+
driver/kernel transition
```

而把控制路径压成：

```text
一个CXL.mem write
+
一个CXL.mem read
```

论文也报告传统 ring-buffer kernel launch 约 3–6 µs，polling 可达约 2–3 µs，PCIe DMA 至少约 1 µs。Low-Overhead_General-Purpose_Ne…

当然，这些不是“所有真实机器永远固定如此”的定律，而是论文引用已有系统数据并用于其评估模型。

---

# 6. 都是同一块 NDP Hardware，为什么每个 Process 还要有自己的 M² func region？

这是一个非常好的问题。

答案是：

> **M² func region 并不是“为每个 process 造一套 NDP hardware”。**

它只是：

> 每个 process 自己的“控制接口 / mailbox / namespace”。

类比一下：

一颗 GPU 只有一套 GPU hardware。

但：

```text
Process A
Process B
Process C
```

都可以创建自己的：

```text
CUDA context
command queue
virtual address space
```

不是说 GPU 被复制了三份。

M²NDP 也是：

```text
          同一套 NDP Units
                 ↑
      ┌──────────┼──────────┐
      │          │          │
Process A    Process B   Process C
M² region A  M² region B M² region C
```

为什么要分开？

第一，防止命令互相覆盖。

如果大家都用：

```text
0x10040 = Launch
```

而且只有一份返回值状态：

```text
status
kernel ID
return value
```

Process A 和 B 很容易相互干扰。

第二，需要安全隔离。

论文给每个 process 的 packet-filter entry 保存：

```text
base
bound
ASID
```

所以能知道：

> 这个请求属于哪个 Host process。

Low-Overhead_General-Purpose_Ne…

第三，kernel metadata 和 return value 也需要 process-specific state。

论文明确说 M² func region 是 per-process 分配的，因此能被 Host 隔离和保护。Low-Overhead_General-Purpose_Ne…

因此：

```text
M²func Region
≠ NDP计算硬件

M²func Region
= Process-specific control address space
```

---

# 7. “多个 NDP kernel 并行”到底怎么可能？DRAM 一次能把它们数据全部取出来？

不需要“一次全部取出来”。

这里的并行是：

> **大量 memory request 同时处于 outstanding / execution 状态。**

不是：

> DRAM 一拍把所有 kernel 的所有数据吐出来。

论文评估配置本来就不是：

```text
1个NDP core + 1根DRAM
```

而是：

```text
32 NDP Units
        ↓
片上Crossbar / NoC
        ↓
32-channel LPDDR5
        ↓
409.6 GB/s
```

Low-Overhead_General-Purpose_Ne…

真实情况更像：

```text
Kernel A:
µthread A0 → Memory request
µthread A1 → Memory request
µthread A2 → Memory request

Kernel B:
µthread B0 → Memory request
µthread B1 → Memory request

Kernel C:
µthread C0 → Memory request
```

这些请求进入：

```text
NoC
↓
Memory Controller
↓
不同Channel
↓
不同Bank
```

DRAM controller 再调度。

所以时间上可能：

```text
t0:
Channel0处理A0
Channel1处理B0
Channel2处理A1
...

t1:
Channel0处理B1
Channel1处理C0
...
```

这就是 memory-level parallelism。

不是：

```text
“一次DRAM read = 同时拿所有kernel全部data”
```

而是：

> 许多请求并行排队、流水和分布到不同 channel/bank。

而且 NDP Unit 本身也有：

```text
多个sub-core
每个sub-core多个µthread slot
多个NDP Unit
```

所以硬件天然可以 resident 多个 kernel 的 µthreads。

如果资源不够，就不会强行并发：

```text
Kernel B
→ pending
```

论文明确允许 concurrent kernels，也明确说资源不足时会 buffer。Low-Overhead_General-Purpose_Ne…

---

# 8. 一次 `ndpLaunchKernel` 到底传哪些参数？

Table II 给得非常明确：

```text
ndpLaunchKernel(
    synchronicity,
    ndpKernelID,
    µthreadPoolRegion(base, bound),
    kernelArgSize,
    kernelArguments
)
```

返回：

```text
kernelInstanceID
或
ERR
```

Low-Overhead_General-Purpose_Ne…

逐个解释。

### synchronicity

表示：

```text
同步 launch
or
异步 launch
```

后面第 10 问详细讲。

---

### ndpKernelID

表示：

> 要运行哪一段已经注册好的 NDP kernel code。

例如：

```text
Kernel ID 1 = VectorAdd
Kernel ID 2 = Histogram
Kernel ID 3 = SPMV
```

---

### µthreadPoolRegion(base, bound)

表示：

> 这一次 kernel 要处理的数据区域，从而定义要生成哪些 µthreads。

例如：

```text
base  = 0xA000
bound = 0xA1FF
```

如果每个 µthread 32 B：

```text
0xA000
0xA020
0xA040
...
```

分别产生 µthread。

---

### kernelArgSize

告诉 NDP Controller：

> 后面的 kernel arguments 总共有多少字节。

这样硬件才能正确解析 write packet 中的参数。

---

### kernelArguments

这是 kernel 真正使用的参数。

例如 VectorAdd：

```text
B_base = 0xB000
C_base = 0xC000
N = ...
```

注意：

> 大数组本身不放在 arguments 中。

传的是：

```text
pointer/base address
scalar parameter
```

数组已经在 CXL Memory 里。

---

另外很容易混淆：

```text
codeLoc
scratchpadMemSize
numIntRegs
numFloatRegs
numVectorRegs
```

这些不是 launch 参数。

它们属于：

```text
ndpRegisterKernel()
```

也就是 kernel 第一次注册时告诉设备：

> “这段程序代码在哪，需要多少硬件资源。”

---

# 9. 什么叫 µthread 是“地址驱动”的？

这是 M² µthread 最独特的点。

传统 GPU 逻辑：

```text
Thread ID
  ↓
计算index
  ↓
计算数据地址
  ↓
访问数据
```

比如：

```c
int i = blockIdx.x * blockDim.x + threadIdx.x;
float x = A[i];
```

所以：

> thread 是先存在的，再由 thread ID 算数据地址。

---

M²NDP 反过来：

> **数据地址本身定义这个 µthread。**

例如：

```text
µthread pool region:
0xA000 ~ 0xA1FF

granularity:
32 B
```

那么硬件可以直接产生：

```text
µthread 0:
mapped address = 0xA000
offset         = 0x000

µthread 1:
mapped address = 0xA020
offset         = 0x020

µthread 2:
mapped address = 0xA040
offset         = 0x040
```

这些值在 µthread 创建时直接交给寄存器：

```text
x1 = mapped address
x2 = offset
```

论文明确描述了这种机制。Low-Overhead_General-Purpose_Ne…

---

为什么这么做？

假设：

```text
A base = 0xA000
B base = 0xB000
C base = 0xC000
```

µthread 2 获得：

```text
x1 = 0xA040
x2 = 0x40
```

它就直接知道：

```text
A address = x1
          = 0xA040

B address = B_base + x2
          = 0xB040

C address = C_base + x2
          = 0xC040
```

不需要：

```text
threadIdx
blockIdx
blockDim
乘法
加法
```

先算 `i`，再算 `base+i*sizeof(T)`。

所以减少了：

> address generation instruction。

这就是论文所谓：

> memory-mapped µthread。

还有一个很重要的细节：

作者自己也说，这种映射并不是强制的。

µthread 甚至可以映射到 dummy address，只要 kernel 不真的访问那个地址；这时候 offset 可以单纯作为 thread ID 使用。Low-Overhead_General-Purpose_Ne…

所以这是：

> 一种优化执行抽象，

不是：

> 所有 NDP kernel 必须数学上“一条 thread = 一个真实地址”。

---

# 10. 返回值、synchronous、asynchronous 到底是什么？和异步电路有关吗？

完全没有关系。

这里：

```text
synchronous
asynchronous
```

说的是：

> **软件调用语义。**

不是：

```text
同步时钟电路
异步逻辑电路
```

---

## Synchronous launch

意思是：

> Host 调用 kernel 后，等待 kernel 完成再继续。

逻辑类似：

```c
result = run_kernel_sync();
next_work();
```

时序：

```text
Host                   NDP

 |---- Launch ---------->|
 |                       |
 |                       | execute
 |                       |
 |                       | finish
 |<---- return ----------|
 |
 | next instruction
```

论文中的实现是：

```text
Host store
→ LaunchKernel

fence

Host load
→ 等待function return
```

对于 synchronous：

> 这个返回直到 kernel termination 后才回来。

Low-Overhead_General-Purpose_Ne…

---

## Asynchronous launch

意思是：

> Host 发出 kernel 后，不等 kernel 执行完，立刻继续自己的工作。

类似：

```c
id = launch_kernel_async();

do_something_else();

while (!poll(id));
```

时序：

```text
Host                   NDP

 |---- Launch ---------->|
 |<-- kernelInstanceID --|
 |
 | Host继续执行          | kernel running
 |                       |
 |---- Poll ------------>|
 |<---- running ----------|
 |
 |---- Poll ------------>|
 |<---- finished ---------|
```

论文明确说 asynchronous launch 会立即返回，从而允许：

```text
Host computation
+
其他 NDP kernels
+
当前 NDP kernel
```

重叠执行。Low-Overhead_General-Purpose_Ne…

---

## 那“返回值”到底是什么？

这里还要区分两种完全不同的返回。

第一种：

> M² func 的控制返回值。

比如：

```text
kernelInstanceID
ERR
running / finished / pending
```

这通过：

```text
store function call
↓
NDP Controller执行
↓
NDP Controller保存return value
↓
Host对同一M²func地址load
```

拿回来。论文明确说明 write 本身不能携带 arbitrary return value，所以用随后的一次 read 获取。Low-Overhead_General-Purpose_Ne…

第二种：

> Kernel 真正计算出的数据结果。

例如：

```text
C = A + B
```

这里的：

```text
C[]
```

不会通过 M² func return packet 返回。

而是 NDP kernel 直接：

```text
store C → CXL Memory DRAM
```

Host 后面普通：

```c
load C[i]
```

即可。

所以：

```text
M²func return
= 控制信息

NDP kernel output
= 实际存储在CXL Memory里的计算结果
```

这两个一定不要混。

---

# 最后，把真实软件—硬件执行过程完整走一遍

假设 Host 要做：

```text
C = A + B
```

A/B/C 已经在 CXL Memory 中。

第一阶段，注册 Kernel：

```text
Host software:

ndpRegisterKernel(
    codeLoc,
    scratchpad size,
    numIntRegs,
    numVectorRegs...
)
        ↓
M²func store
        ↓
CXL.mem
        ↓
Packet Filter
        ↓
NDP Controller
        ↓
记录：

Kernel ID = 7
Code @ ...
需要多少register
需要多少scratchpad
```

第二阶段，Launch：

```text
ndpLaunchKernel(
    async,
    KernelID=7,
    pool=[A_base,A_bound],
    args={B_base,C_base}
)
```

然后：

```text
CPU store
 ↓
CXL.mem
 ↓
Packet Filter
 ↓
NDP Controller
```

NDP Controller 检查：

```text
有没有µthread slot？
有没有register？
有没有scratchpad？
```

如果够：

```text
启动kernel
```

然后 µthread generator：

```text
A_base + 0x00 → µthread0
A_base + 0x20 → µthread1
A_base + 0x40 → µthread2
...
```

每个 µthread 拿到：

```text
PC = VectorAdd kernel entry

x1 = 自己对应的A地址
x2 = offset
```

然后很多 µthreads：

```text
load A
load B
vector add
store C
```

在多个：

```text
NDP Unit
Sub-core
µthread slot
```

上交错执行。

Memory request：

```text
NDP Units
 ↓
NoC
 ↓
多个Memory Controllers
 ↓
多个DRAM channels/banks
```

并发进行。

Kernel 全部完成：

```text
NDP Controller:
KernelInstance #42 = FINISHED
```

Host：

```text
Poll #42
→ FINISHED
```

然后：

```text
普通load C[]
```

取得真正结果。

这才是这篇论文从 Host 软件一直到 DRAM 的完整技术路径。

理解这套模型以后，作者后面谈的：

```text
µthread slot
register allocation
FGMT
scratchpad
TLB
cache hierarchy
back invalidation
```

就都不再是孤立名词了——它们全部是在给这条执行路径里的具体硬件模块补细节。