可以。Section III 的 A–D 已经从“为什么需要 M²NDP”正式进入“它到底怎么工作”。这一段最容易混淆的地方，是论文把三种不同层次的东西揉在一起讲：

- M² func：Host 怎样“调用/管理”NDP；
- NDP kernel：真正要执行的那段程序；
- M² µthread：NDP kernel 在 CXL Memory 内部怎样被拆成大量轻量执行实例。

先抓住这三个层次，再看 Fig. 4、Fig. 5 和 GPU 对比，就会清楚很多。

我按 A → B → C → D 拆。

---

## A. Overview：先把整个 M²NDP 系统分成“控制”和“执行”两部分

Section III-A 本身很短，作用就是正式定义 M²NDP。

作者说 M²NDP 有两个核心机制：

```text
M²NDP
├── M² func
│    └── Host ↔ NDP 的管理 / offloading
│
└── M² µthread
     └── NDP kernel 在设备内部怎样执行
```

M² func 解决的是：

> “Host 怎么低开销地告诉 NDP：注册 kernel、启动 kernel、查状态？”

M² µthread 解决的是：

> “收到 kernel 以后，CXL Memory 里面那堆 NDP 计算单元怎么高效执行它？”

而且两者都放在 CXL Memory Controller 一侧；这个控制器仍然正常支持普通 CXL.mem read/write。Low-Overhead_General-Purpose_Ne…

所以你可以把 Fig. 3 暂时理解成：

```text
Host CPU
   |
   | CXL.mem
   v
+--------------------------------+
| CXL Memory Expander            |
|                                |
| CXL Controller                 |
|   |                            |
|   +-- Packet Filter            |  ← 识别 M² func
|   |                            |
|   +-- NDP Controller           |  ← 管 kernel
|   |                            |
|   +-- NDP Units                |  ← 跑 µthreads
|                                |
| DRAM Controllers ---- DRAM     |
+--------------------------------+
```

这里最重要的区分是：

> **M² func 不是“计算单元”，M² µthread 也不是“通信协议”。**

一个负责 Host→Device 控制，一个负责 Device 内部执行。

---

# B. Memory-Mapped NDP Management Function：M² func 到底是什么

这一节真正的核心只有一个想法：

> **拿 CXL Memory 地址空间的一小段地址，不再当普通 DRAM，而是当成“函数调用接口”。**

这就是你问的“CXL memory 中的 M² func 区域”。

---

## 1. 为什么要搞一个 “M² func region”？

标准 CXL.mem 很快，但它原本只认识：

```text
Read address X
Write address X
```

它并没有：

```text
RegisterKernel
LaunchKernel
PollKernelStatus
```

这种 packet type。

最直接的办法当然是：

> 修改 CXL.mem 协议，增加自定义 command。

但那意味着：

- Host CPU CXL Controller 要改；
- CXL 协议实现要改；
- 甚至可能需要新增 ISA 指令。

作者不想这样。

于是它反过来利用“地址本身”编码命令：

```text
普通 CXL.mem 地址：
0x8000_0000
→ 真正访问 DRAM

特殊预留地址：
0x0001_0040
→ 不访问 DRAM
→ 被解释成 LaunchKernel()
```

论文把这片特殊地址空间称为：

> M² func region

并在 CXL Memory 输入端放一个：

> packet filter

检查每一个 CXL.mem request 的地址。Low-Overhead_General-Purpose_Ne…

---

## 2. 所以它和 MMIO 非常像

你可以直接用 SoC 里熟悉的 MMIO 类比。

例如：

```text
0x1000_0000 → UART TX Register
0x1000_0004 → UART STATUS Register
```

CPU：

```c
*(uint32_t *)0x10000000 = 'A';
```

看起来是 store。

但实际上不是：

> “把 A 存入某个 SRAM。”

而是：

> “调用 UART 发数据。”

M² func 同理：

```text
M² func base = 0x10000

base + 0x00 → RegisterKernel
base + 0x20 → UnregisterKernel
base + 0x40 → LaunchKernel
base + 0x60 → PollKernelStatus
base + 0x80 → TLB shootdown
```

这个 offset 关系就是 Table II。Low-Overhead_General-Purpose_Ne…

所以：

```c
store args -> base + 0x40
```

语义不是“存数据”，而是：

```c
ndpLaunchKernel(args);
```

这就是：

> Memory-Mapped Function

---

# 3. M² func region 是真的占了一块 DRAM 吗？

这里要非常精确。

论文说的是：

> reserve some physical memory space of the CXL memory

也就是说从 Host 的物理地址视角，它确实被分配了一个 CXL-memory physical address range。

但是对匹配这个区域的访问：

> packet filter 会截获，并把它解释为 M² func call，而不是普通 memory read/write。

所以最好的 mental model 是：

```text
Host Physical Address Space

+--------------------------+
| Normal CXL Memory        |
| → 真DRAM                 |
|                          |
+--------------------------+
| M² func region           |
| → 地址存在               |
| → 但访问被Packet Filter  |
|   截获成“函数调用”       |
+--------------------------+
```

它“看起来像 memory”，但语义不是普通 memory。

---

# 4. 为什么每个 process 都有自己的 M² func region？

论文不是全系统只有一组：

```text
Launch
Status
...
```

而是每个 Host process 可以申请自己的 M² func region。

初始化的时候：

```text
Host process
    |
    ↓
M²NDP driver
    |
    ↓
分配一个 uncacheable M² func region
    |
    ↓
通过 CXL.io 告诉设备：
base / bound / ASID
```

Packet Filter 中保存：

```text
base address
bound address
ASID
```

每个 process 只需要 18 B metadata。Low-Overhead_General-Purpose_Ne…

例如：

```text
Process A, ASID=0x07:
0x10000 ~ 0x1FFFF

Process B, ASID=0x0A:
0x20000 ~ 0x2FFFF
```

这就是 Fig. 4 里面 Packet Filter 那张小表。

于是：

```text
Process A store 0x10040
→ A 的 LaunchKernel

Process B store 0x20040
→ B 的 LaunchKernel
```

避免多个用户进程共享几个固定物理 device register 的麻烦。

---

# 5. 为什么 M² func region 必须 Uncacheable？

这个细节非常重要。

如果 CPU 执行：

```text
store -> M² func address
```

结果命中了 CPU Cache：

```text
CPU L1:
“哦，我先把这个store留在cache里”
```

那 CXL Memory Controller 根本收不到这个请求。

当然就不会启动 kernel。

所以这块地址必须是：

> uncacheable

让每次 load/store 都真正通过 CXL.mem 发到设备。

论文明确说明 Host 对 M² func region 的 store 会 bypass Host cache。Low-Overhead_General-Purpose_Ne…

---

# 6. 参数怎么传？

作者用了一个很巧但很好理解的方法：

```text
Address
→ 表示“调用哪个函数”

Write Data
→ 表示“函数参数”
```

例如：

```text
Address = base + 0x40
           ↓
      LaunchKernel

Write Data =
{
  sync/async,
  kernel ID,
  µthread pool base,
  µthread pool bound,
  argument size,
  kernel arguments...
}
```

所以非常像：

```c
LaunchKernel(arg0, arg1, arg2...);
```

只是编码成：

```text
CXL.mem Write
Address = Function ID
Data    = Arguments
```

作者甚至允许使用 CPU vector register 一次把多个参数打包进 write data。Low-Overhead_General-Purpose_Ne…

---

# 7. 返回值怎么办？

这是个很好的问题，因为 CXL.mem write response 本身不能像：

```c
return kernelInstanceID;
```

一样携带任意返回值。

所以作者用了：

```text
第一次：
store → 调用函数

第二次：
load ← 取返回值
```

例如：

```text
store args -> LaunchKernel 地址
       |
       v
NDP Controller执行调用

fence

load <- 同一个 LaunchKernel 地址
       |
       v
返回 kernelInstanceID / error
```

而这个 return value 会被 NDP Controller 存在对应位置，之后普通 CXL.mem read 把它读回来。Low-Overhead_General-Purpose_Ne…

这也是为什么中间需要：

> fence

保证：

```text
store function call
```

在：

```text
load return value
```

之前完成正确的 ordering。

---

# 8. Fig. 4 逐步看：它其实是在演示一个 VectorAdd

这是你最应该吃透的图。

论文假设：

```text
A = 0xA000
B = 0xB000
C = 0xC000

计算：
C = A + B
```

而 M² func region：

```text
Physical:
0x10000 ~ 0x1FFFF
```

对应当前 process：

```text
ASID = 0x07
```

Fig. 4 中 Host：

```text
x7 = 0x60040   // Virtual Address
```

经地址转换：

```text
VA 0x60040
    ↓
PA 0x10040
```

为什么是：

```text
0x10040
```

？

因为：

```text
M² func base
= 0x10000

LaunchKernel offset
= 2 << 5
= 64
= 0x40

所以：
0x10000 + 0x40
= 0x10040
```

这正好对应 Table II 的：

```text
ndpLaunchKernel
offset = 2 << 5
```

---

然后 Host 执行：

```asm
vse64.v v1, (x7)
```

你可以粗略理解成：

> 把 vector register v1 的内容 store 到 x7 指向的地址。

v1 里面不是 VectorAdd 的 A/B/C 数据本体。

而是：

```text
Launch metadata / arguments
```

例如：

```text
sync/async
kernel ID
µthread pool:
    base  = 0xA000
    bound = 0xA1FF
argument size
B base = 0xB000
C base = 0xC000
...
```

Fig. 4 就是在演示：

```text
Host一条Store
        ↓
CXL.mem write：
Addr = 0x10040
Data = kernel launch arguments
        ↓
Packet Filter：
0x10040 ∈ M²func region
        ↓
不是普通DRAM write
        ↓
NDP Controller：
“这是LaunchKernel”
        ↓
启动VectorAdd
```

论文图注明确说明这个例子计算 `C=A+B`，A/B/C 分别位于 0xA000、0xB000、0xC000，每个 µthread 负责 32 B 数据。Low-Overhead_General-Purpose_Ne…

这张图后半部分涉及 µthread，等讲完 D 再回来就完全通了。

---

# C. NDP Kernel Launch：一次 Kernel 到底怎么被启动？

B 是在定义：

> “函数调用接口长什么样”。

C 才正式描述：

> “调用 LaunchKernel 后到底发生什么”。

---

## 1. 先区分两种 arguments

论文专门强调：

### M² func arguments

控制：

> kernel 怎么 launch。

例如：

```text
sync / async
kernel ID
µthread pool region
kernel argument size
```

### NDP kernel arguments

是 kernel 代码本身使用的数据参数。

例如 VectorAdd：

```text
B base
C base
N
```

所以：

```text
ndpLaunchKernel(
    sync,
    kernelID,
    pool_base,
    pool_bound,
    argSize,
    kernelArgs...
)
```

前半部分是 runtime/control metadata。

后半部分才是用户 kernel 需要的参数。Low-Overhead_General-Purpose_Ne…

大数组当然不会直接塞进 CXL.mem write packet。

例如：

```text
A: 1 GB
```

不会把 1 GB 参数发过去。

而是：

```text
A 已经在 CXL Memory
→ 参数只传 pointer/base address
```

这和 CUDA kernel 参数传 pointer 很接近。

---

# 2. µthread pool region 是什么？

这是 Section C/D 之间的关键桥梁。

论文定义：

> 每个 kernel instance 都关联一个 virtual memory region，称为 µthread pool region。

例如：

```text
µthread pool:
0xA000 ~ 0xA1FF
```

这不是：

> “存放 µthread 数据结构的线程池”。

这个名字很容易误导。

它更准确的理解是：

> **用某一段数据地址空间定义“应该生成多少个 µthreads，以及每个 µthread 对应哪块数据”。**

假设每个 µthread 对应 32 B：

```text
0xA000 → µthread 0
0xA020 → µthread 1
0xA040 → µthread 2
0xA060 → µthread 3
...
```

所以：

```text
Pool Region
=
待处理的数据地址范围
+
µthread 生成空间
```

这一点后面 D 就会正式解释。

---

# 3. launch 后 Host 马上得到什么？

NDP Controller 收到 launch request 后：

```text
Host
 |
 | store LaunchKernel
 v
NDP Controller
```

会先给 acknowledgment。

然后 Host：

```text
fence
load same M²func address
```

取得函数返回值。

这里分：

### synchronous launch

```text
Host
 |
 | launch
 v

NDP kernel运行
 |
 |
finish
 |
 v
Host的load最终返回
```

也就是说：

> 返回时 kernel 已经结束。

---

### asynchronous launch

```text
Host
 |
 | launch
 v
NDP开始运行
 |
 +---- 立即返回kernelInstanceID
 |
Host继续干其他事情
```

以后再：

```text
ndpPollKernelStatus()
```

查询。

论文明确说明 async 模式允许 Host-side computation 和其他 NDP kernel 与当前 kernel overlap。Low-Overhead_General-Purpose_Ne…

这和 CUDA 的 asynchronous kernel launch 思想非常相似。

---

# 4. 多个 kernel 同时来怎么办？

如果有足够资源：

```text
Kernel A
Kernel B
Kernel C
```

可以 concurrent execution。

如果 NDP resource 不够：

```text
Kernel A running
Kernel B running
Kernel C launch arrives
```

则：

```text
Kernel C
→ buffered
→ 等之前kernel释放资源
```

如果 launch buffer 都满了：

```text
→ 返回error
```

Low-Overhead_General-Purpose_Ne…

因此 M² func 并不是：

> 一次只能跑一个 kernel 的 command register。

它设计上支持：

> 多个 Host thread / process 发起多个 concurrent NDP kernels。

这正是它优于“直接 MMIO 写几个 device register”的一部分。

---

# 5. Fig. 5 到底在比较什么？

Fig. 5 比较三种：

```text
(a) M² func
(b) CXL.io + Ring Buffer
(c) CXL.io + Direct MMIO
```

作者定义：

```text
x = CXL.mem one-way latency
y = CXL.io one-way latency
z = NDP kernel execution time
```

并给典型值：

```text
x ≈ 75 ns
因为CXL memory round-trip LtU约150 ns

y ≈ 500 ns
因为PCIe/CXL.io一次round trip量级约1 µs

z = kernel runtime
```

Low-Overhead_General-Purpose_Ne…

---

## Fig. 5(a)：M² func

关键路径大致就是：

```text
Host
 |
 | CXL.mem write
 | Launch
 v
NDP

 |===== kernel z =====|

Host
 ^
 | CXL.mem read response
 |
```

作者建模的总时间：

```text
z + 2x
```

重点不是“精确数两个箭头”。

重点是：

> M² func 只需要很少的 CXL.mem 往返，而且 CXL.mem 本身又快。

---

## Fig. 5(b)：Ring Buffer

传统方案需要：

```text
准备command
↓
enqueue command
↓
doorbell / tail update
↓
device DMA读pointer
↓
device DMA读command
↓
launch
↓
完成后产生completion
↓
Host再检查completion
```

而且作者模型里 launch / error check 会产生多轮 command/completion 操作。

于是通信关键路径远长于 M² func。

Fig. 5 给出的抽象总时间是：

```text
z + 8y
```

---

## Fig. 5(c)：Direct MMIO

比 Ring Buffer 简单：

```text
Host写设备寄存器
↓
launch
↓
kernel执行
↓
poll/read status
```

所以：

```text
z + 3y
```

比 Ring Buffer 好。

但是上一篇我们说过：

> 固定 physical device register 不适合大量 concurrent kernel / multi-process。

所以仍然不是作者想要的方案。

---

## Fig. 5 真正想证明什么？

不是：

> CXL.mem 永远比 PCIe 快 4 倍。

而是：

```text
Fine-grained kernel:
z 本来就很短

如果通信是：
8y、3y
→ 通信可能比计算本身还大

M² func:
2x
→ overhead大幅压缩
```

论文因此报告，在 Fig. 5 的示例假设下，M² func 相比传统方案可显著减少 communication overhead 和 end-to-end runtime。Low-Overhead_General-Purpose_Ne…

---

# D. Memory-Mapped µthread：NDP 内部到底怎么执行 Kernel？

这是这一轮最关键的部分。

作者现在开始回答：

> 已经把 kernel launch 到 CXL Memory 了，那里面的计算硬件怎么跑？

核心目标只有一句：

> **用很低的硬件成本制造大量并发 memory accesses，隐藏 DRAM latency，尽可能吃满 DRAM bandwidth。**

---

# 1. 为什么不能直接用普通 OoO CPU？

你熟悉 CPU 的话，可以这样理解。

一个高性能 OoO Core 为了同时挂很多 memory request，需要：

```text
ROB
Issue Queue
Load Queue
Store Queue
Register Rename
Wakeup / Select
Dependency checking
Speculation
...
```

当然能很好隐藏 latency。

但硬件非常贵。

作者认为：

> 对 memory-bound NDP，这种控制逻辑性价比太差。

所以不用“大而强的单线程”。

而用：

> 很多极轻量线程。

Low-Overhead_General-Purpose_Ne…

---

# 2. Fine-Grained Multithreading 是核心

假设：

```text
µthread 0:
load A
→ DRAM miss
→ 等100ns
```

如果只有它：

```text
ALU/LSU大量时间空着
```

那就切：

```text
cycle 0: µthread0
cycle 1: µthread1
cycle 2: µthread2
cycle 3: µthread3
...
```

某个 µthread 等 memory 时，就执行其他 µthread。

这就是作者的：

> FGMT — Fine-Grained Multithreading

和 GPU 用大量 warp 隐藏 memory latency 是同一基本思想。

区别在于作者重新设计了 thread 粒度和执行模型。

---

# 3. 为什么叫 “µthread”？

因为它不是 CPU OS thread。

普通 CPU thread：

```text
Architectural state:
x0~x31
f0~f31
vector registers
CSR
...
```

无论这个程序实际用不用，都有一个完整 ISA context 的概念。

如果你要同时保存几十/几百个 thread context：

```text
Register File会非常大
```

作者观察：

> memory-bound kernel 往往寄存器需求很少。

所以 kernel 注册时直接告诉 NDP：

```text
我需要：
5 integer registers
3 vector registers
```

那么这个 µthread 就只分配：

```text
x0 ~ x4
v0 ~ v2
```

而不是完整的大 register context。

这就是 “micro-thread / lightweight thread”。

Low-Overhead_General-Purpose_Ne…

所以核心关系是：

```text
少量register / thread
        ↓
同样面积能保留更多thread context
        ↓
更多concurrent µthreads
        ↓
更多outstanding memory accesses
        ↓
隐藏DRAM latency
        ↓
吃满Memory BW
```

---

# 4. 它为什么又和 GPU 类似？

作者确实大量拿 GPU 比。

因为 M² µthread 在很多地方采用 GPU 风格：

```text
线程由Hardware创建
而不是OS创建

大量并发线程

FGMT隐藏memory latency

没有OoO

Kernel式执行

大量数据并行
```

论文 Table III 把 CPU、GPU 和 M²NDP 对比得很明确。Low-Overhead_General-Purpose_Ne…

但作者又认为：

> GPU 的 thread/block/SIMT 模型并不是为这种 NDP 场景量身定做的。

因此后面的 A1–A4 全是在回答：

> “为什么不直接照搬 CUDA GPU SM？”

---

# 5. 第一个区别：GPU thread 是“编号驱动”，M² µthread 是“地址驱动”

这是最重要的一点。

GPU：

```text
grid
 └── block
      └── thread
```

thread 身份通常来自：

```text
blockIdx
threadIdx
blockDim
```

然后程序自己：

```c
i = blockIdx.x * blockDim.x + threadIdx.x;
A[i] ...
```

也就是说：

```text
Thread ID
   ↓
计算 index
   ↓
计算 address
   ↓
访问 data
```

而 M² µthread：

```text
Memory Address
   ↓
直接定义 µthread
```

例如：

```text
µthread pool:
0xA000 ~ 0xA1FF

granularity = 32B

µthread 0 → 0xA000
µthread 1 → 0xA020
µthread 2 → 0xA040
...
```

生成一个 µthread 时，硬件直接告诉它：

```text
x1 = mapped address
x2 = offset from pool base
```

所以程序不需要先从：

```text
block ID
thread ID
```

算出地址。

论文称之为：

> Memory-Mapped µthreading

并报告这种方法可以减少地址计算相关指令。Low-Overhead_General-Purpose_Ne…

---

# 6. 现在回看 Fig. 4 后半部分

前面我们只讲了 launch。

现在整个图就通了。

Host 发：

```text
µthread pool:
base  = 0xA000
bound = 0xA1FF
```

然后 NDP Controller 知道：

> 我要处理 A[0xA000 : 0xA1FF]。

如果每个 µthread 负责：

```text
32 B
```

那么自然生成：

```text
µthread 0 → 0xA000
µthread 1 → 0xA020
µthread 2 → 0xA040
µthread 3 → 0xA060
µthread 4 → 0xA080
...
```

Fig. 4 里你会看到：

```text
NDP Unit 0:
µthr0: 0xA000
µthr4: 0xA080

NDP Unit 1:
µthr1: 0xA020
µthr5: 0xA0A0

...
```

所以这个 VectorAdd 可以理解成：

```text
µthr0:
A[0xA000:0xA01F]
+
B[对应offset]
→
C[对应offset]

µthr1:
A[0xA020:0xA03F]
+
B[对应offset]
→
C[对应offset]
```

这里：

```text
A
```

被选作 µthread pool region。

而：

```text
B base
C base
```

作为 kernel arguments。

每个 µthread 已经知道自己相对于 A base 的 offset：

```text
offset = x2
```

所以：

```text
A_addr = x1
B_addr = B_base + x2
C_addr = C_base + x2
```

非常自然。

这就是 Fig. 4 的真正含义。

---

# 7. 作者为什么强调 Scalar + SIMD，而不是 GPU 式 SIMT-only？

这里要按论文自己的抽象来理解。

GPU warp：

```text
32 threads
↓
同一条instruction
↓
32 lanes执行
```

例如每个 thread 都算：

```c
i = blockIdx.x * blockDim.x + threadIdx.x;
```

于是某些：

```text
loop control
address calculation
index calculation
```

实际上每个 lane 都在做类似的事情。

作者认为这种操作存在：

> redundant computation

所以它采用：

```text
RISC-V scalar
+
RVV SIMD/vector
```

也就是：

```text
需要一份的控制/地址逻辑
→ scalar instruction

真正批量数据操作
→ vector instruction
```

而不是所有东西都放进 SIMT lane 里做。

这是作者认为 M²NDP 可以减少 ALU、register file 成本的一个重要原因。Low-Overhead_General-Purpose_Ne…

注意这里最好按论文的架构抽象来读，不需要把它泛化成“真实现代 GPU 完全没有 scalar 能力”。

---

# 8. 第二个区别：GPU 按 Thread Block 分配资源，M² 按单个 µthread

你已经知道 CUDA：

```text
Grid
 ├── Block 0
 │    ├── Warp 0
 │    ├── Warp 1
 │    └── ...
 ├── Block 1
 ...
```

GPU 资源的一个重要管理粒度是：

> Thread Block

一个 block 进入 SM 后会占：

```text
registers
shared memory
warp slots
...
```

直到：

> 整个 block 都结束

这些 block-level resource 才能完全释放。

于是对于不规则 workload：

```text
Warp0 finished
Warp1 finished
Warp2还在慢慢跑
```

则 Warp0/1 已经不工作了，但这个 Block 的一部分资源可能仍无法给下一个 Block 灵活使用。

作者称这种问题为：

> resource fragmentation / underutilization

M² µthread 则：

```text
一个µthread结束
↓
立即释放这个µthread的资源
↓
马上生成新的µthread
```

不必等：

```text
“同一个block里的其他µthreads”
```

因为压根没有 CUDA 那套 thread-block hierarchy。

论文认为这尤其适合 irregular workload。Low-Overhead_General-Purpose_Ne… Low-Overhead_General-Purpose_Ne…

---

# 9. 一个具体 GPU vs M² 的例子

假设有 32 个任务：

```text
Task 0~30：100 cycles
Task 31：1000 cycles
```

GPU 如果它们属于一个 Thread Block：

```text
0~30 很早完成
31 还在跑
```

这个 block 仍没有结束。

而 M² 模型中：

```text
µthread 0 finished
→ slot立即给 µthread 32

µthread 1 finished
→ slot立即给 µthread 33
...
```

所以持续保持：

```text
很多active contexts
```

这也是论文后面 Fig. 6(a) 要表达的现象。

---

# 10. 第三个区别：Scratchpad 的共享范围更大

CUDA shared memory：

```text
Thread Block A
    ↕
Shared Memory A

Thread Block B
    ↕
Shared Memory B
```

即使两个 block 恰好同时跑在同一个 SM：

> 它们也不能直接通过同一个 CUDA shared memory scope 共享数据。

而作者设计：

```text
NDP Unit
├── µthread 0
├── µthread 1
├── µthread 2
├── ...
└── Scratchpad
```

同一个 NDP Unit 上的所有 µthread：

> 都可以共享这一块 scratchpad。

所以它没有 CUDA thread-block 这个额外隔离层。

作者认为这样可以减少：

- global memory traffic；
- 重复初始化 shared memory；
- block 之间同步/数据复制开销。

Low-Overhead_General-Purpose_Ne…

---

# 11. 第四个区别：µthread 的数据粒度直接匹配 DRAM access granularity

这是一个很硬件化、但非常漂亮的设计点。

论文举例：

```text
DDR5:
memory access granularity ≈ 64 B

LPDDR5:
≈ 32 B
```

那么一个 µthread 就负责差不多：

```text
32 B / 64 B
```

这种粒度的数据。

也就是说：

```text
一个µthread
≈ 一次底层memory transaction附近的数据量
```

为什么？

因为作者目标是：

> Memory BW utilization

而不是尽量制造超宽 SIMD。

---

GPU warp 通常：

```text
32 threads
×
4 B FP32
=
128 B
```

一个 warp 对应更大的数据范围。

如果 workload 很规整：

```text
thread0做A[0]
thread1做A[1]
...
```

很好。

但如果是不规则 graph / pointer chasing：

```text
lane0 有效
lane1 没活
lane2 分支A
lane3 分支B
...
```

就出现：

> intra-warp divergence

SIMD lane 利用率下降。

M²NDP 把 µthread 粒度缩到更接近一次 memory access，就可以降低：

```text
“必须把一大群线程绑在一个warp里一起行动”
```

造成的浪费。Low-Overhead_General-Purpose_Ne…

---

# 12. 所以 M² µthread 与 CUDA thread 到底是什么关系？

可以这样总结：

| | CUDA GPU | M² µthread |
|---|---|---|
| 身份 | blockIdx/threadIdx | memory address / offset |
| 创建粒度 | Thread Block | Individual µthread |
| 调度 | Warp/FGMT | Individual lightweight µthread + FGMT |
| 执行风格 | SIMT | Scalar + SIMD/RVV |
| Address generation | 线程 ID 算 index/address | 地址直接赋给 µthread |
| Register | 按实际需求分配，但 GPU context 较重 | 极轻量，kernel 注册时声明需求 |
| Scratchpad scope | Thread Block | 整个 NDP Unit |
| 主要目标 | 高 throughput compute | 低成本饱和 DRAM BW |

作者不是说：

> “GPU 模型不好。”

而是：

> “GPU 是为了 compute throughput 设计的；我们是为了 memory-bound NDP，所以应该重新优化线程抽象。”

---

# 13. 把 A/B/C/D 用同一个 VectorAdd 例子串起来

这是这一部分最重要的整体流程。

假设：

```text
C = A + B

A @ 0xA000
B @ 0xB000
C @ 0xC000
```

第一步，Host 之前已经注册：

```text
VectorAdd kernel
→ kernel ID = 1
```

然后：

### A/B：调用 M² func

Host 准备：

```text
sync = 0/1
kernel ID = 1
µthread pool = [0xA000, 0xA1FF]
B base = 0xB000
C base = 0xC000
```

执行：

```text
store -> M² func base + 0x40
```

Packet Filter：

```text
“这个地址属于M²func region”
```

于是：

```text
→ LaunchKernel()
```

---

### C：Kernel instance 被创建

NDP Controller 创建：

```text
VectorAdd kernel instance
```

如果异步：

```text
立即返回 kernelInstanceID
```

如果同步：

```text
等 kernel 完成后返回
```

---

### D：µthreads 被生成

Pool：

```text
0xA000 ~ 0xA1FF
```

每个 µthread：

```text
32 B
```

于是：

```text
µthr0 → A+0x00
µthr1 → A+0x20
µthr2 → A+0x40
...
```

每个 µthread 获得：

```text
mapped address
offset
```

然后执行类似：

```text
load vector A[offset]
load vector B[offset]
vector add
store vector C[offset]
```

很多 µthreads 交错执行：

```text
µthr0 memory wait
→ µthr1

µthr1 memory wait
→ µthr2

...
```

直到：

```text
所有 pool region 都处理完
```

kernel finished。

这样你就可以把：

```text
M² func region
Fig. 4
Fig. 5
µthread pool
GPU comparison
kernel scheduling
```

全部放进同一个模型里。

---

# 14. 这一部分你现在应该牢固掌握的 6 个概念

Section III A–D 读完，真正需要留下来的不是所有微小细节，而是：

1. **M² func region 是一段特殊 CXL Memory physical address range；访问它会被 Packet Filter 解释成函数调用，而不是普通 DRAM access。**

2. **M² func 的编码方式是：Address = function type，Write Data = arguments；返回值通过后续 read 获取。**

3. **µthread pool region 不是传统意义的“线程对象数组”，而是用一段数据地址范围定义要生成哪些 µthreads。**

4. **一个 µthread 直接对应一个 memory location / chunk，因此避免 GPU 那种从 block/thread ID 计算数据地址的部分开销。**

5. **M²NDP 仍然借鉴 GPU 的大量硬件线程 + FGMT 来隐藏 memory latency，但去掉了 Thread Block 粗粒度资源管理，并采用 Scalar + RVV SIMD。**

6. **Fig. 5 的核心不是背 `z+2x / z+8y / z+3y`，而是证明：对于短 kernel，Host→NDP 的 launch/completion overhead 本身可能成为主要瓶颈，而 M² func 就是专门压缩这部分的。**

理解到这个程度，Section III A–D 的主干已经比较扎实。接下来的 E/F/G/H 会开始更靠近你熟悉的“处理器微架构”领域：**NDP Unit 内部 datapath、Cache hierarchy、kernel programming model、Virtual Memory/TLB**。其中 III-E 的 Fig. 7 会把现在比较抽象的 µthread/F​​GMT 真正落实成寄存器、slot、dispatch、ALU/LSU 这些硬件模块。