# AXI 核心要点补充：握手协议之外

> 来源与定位：基于 `bus_part2.pdf` 的 AXI 部分，主要对应 PDF p.26-p.34（课件页脚 64-72），并结合课程中 AHB 的学习重点做对比。  
> 本笔记默认你已经理解 `VALID/READY` 和五个独立通道，因此只保留必要提醒，重点整理 **burst、地址/控制字段、response、ID/outstanding/ordering、AXI 与 AHB 差异**。

## 0. 这份笔记要抓住什么

AXI 除握手协议外，考试最容易问的是：

- AXI 为什么比 AHB 更适合高性能 SoC。
- AXI 的五个通道各自承载什么信息。
- AXI burst 和 AHB burst 有什么不同。
- `AxLEN / AxSIZE / AxBURST / WSTRB / LAST / RESP / ID` 这些字段大致是什么意思。
- outstanding、out-of-order、interleaving 到底解决什么问题。
- AXI4、AXI4-Lite、AXI4-Stream 在定位上有什么区别。

一句话先压缩：

```text
AHB 像“流水化共享总线”；
AXI 像“多通道、可并发、可 outstanding 的事务接口”。
```

## 1. AXI 是接口规范，不是互连本身

> 对应课件：PDF p.27（页脚 65）

课件原话核心：

```text
AXI is an interface specification that defines the interface of IP blocks,
rather than the interconnect itself.
```

含义：

- AXI 规定 master、slave、interconnect 之间如何通信。
- 它定义接口信号、通道、事务规则。
- 具体 interconnect 可以是 crossbar、NoC、bus matrix 或其他结构。

判断题抓手：

- “AXI 就是一条固定物理总线结构。”错误。
- “AXI 定义 IP block 的接口规范。”正确。
- “同一个 SoC 内可以有多个 AXI master 和多个 AXI slave。”正确。

## 2. 五个通道的非握手信息

> 对应课件：PDF p.27-p.28（页脚 65-66）

AXI 五个通道：

| 通道 | 方向 | 非握手信息 | 作用 |
| --- | --- | --- | --- |
| AW | master -> slave | 写地址、写控制、写事务 ID | 描述一次写事务要写哪里、怎么写 |
| W | master -> slave | 写数据、写字节选通、最后 beat 标志 | 传输真正的写数据 |
| B | slave -> master | 写响应、写事务 ID | 告诉 master 写事务结果 |
| AR | master -> slave | 读地址、读控制、读事务 ID | 描述一次读事务要读哪里、怎么读 |
| R | slave -> master | 读数据、读响应、读事务 ID、最后 beat 标志 | 返回读数据和读结果 |

可以记成：

```text
写：AW 描述写请求，W 搬写数据，B 返回写结果
读：AR 描述读请求，R 返回读数据和读结果
```

这里要注意：

- AXI 没有单独的 Read Response channel。
- 读响应作为 `R` 通道的一部分返回。
- 写响应有单独的 `B` 通道。

## 3. Ax 字段：AW 和 AR 共用的一类地址控制字段

AXI 常用 `Ax` 表示 AW 和 AR 都有的字段：

```text
AxADDR  = AWADDR 或 ARADDR
AxLEN   = AWLEN  或 ARLEN
AxSIZE  = AWSIZE 或 ARSIZE
AxBURST = AWBURST 或 ARBURST
AxID    = AWID   或 ARID
```

这里的 `x` 不是某个具体信号名，而是“Address channel 的通用写法”。

### 3.1 AxADDR：起始地址

`AxADDR` 表示本次 transaction 或 burst 的起始地址。

和 AHB 的一个关键差别：

- AHB burst 中，每个 beat 都会在地址阶段给出一个地址。
- AXI burst 中，通常一次 address handshake 描述整个 burst 的起始地址和控制信息，后续 data beats 不再每拍重新发完整地址。

课件 p.32 的关键词就是：

```text
One Address for entire burst
```

### 3.2 AxLEN：burst 长度

`AxLEN`(`AWLEN` 或 `ARLEN`) **描述一个 burst 中有多少个 data beats**。

常见理解方式：**burst beats = AxLEN + 1**


例如：

| AxLEN | beat 数 |
| --- | --- |
| 0 | 1 beat |
| 3 | 4 beats |
| 7 | 8 beats |
| 15 | 16 beats |

考试一般不会深挖 AXI3/AXI4 的最大长度差异；如果只做课程复习，重点记住 `AxLEN` 是 burst beat 数相关字段。

### 3.3 AxSIZE：每个 beat 多大

`AxSIZE` 描述每个 beat 的传输大小，**通常按字节数的 log2 编码理解**。

常见例子：

| AxSIZE | 每 beat 字节数 | 含义 |
| --- | --- | --- |
| 0 | 1 byte | 8 bit |
| 1 | 2 bytes | 16 bit |
| 2 | 4 bytes | 32 bit |
| 3 | 8 bytes | 64 bit |

和 AHB 的 `HSIZE` 对应关系很强：

```text
AHB: HSIZE 说明每个 beat 多大
AXI: AxSIZE 说明每个 beat 多大
```

### 3.4 AxBURST：burst 地址类型

`AxBURST` 描述 burst 地址如何变化。

常见类型：

| 类型 | 含义 | 典型用途 |
| --- | --- | --- |
| FIXED | **每个 beat 使用同一地址** | FIFO、外设数据寄存器 |
| INCR | **地址按 beat 大小递增** | 连续内存访问，最常见 |
| WRAP | **地址递增，到边界后回绕** | cache line 填充等 |

和 AHB 对比：

| 项目 | AHB | AXI |
| --- | --- | --- |
| burst 类型字段 | `HBURST` | `AxBURST` |
| beat 大小字段 | `HSIZE` | `AxSIZE` |
| 长度表达 | `HBURST` 同时编码部分长度信息，如 `INCR4/WRAP4` | `AxLEN` 单独表达 beat 数，`AxBURST` 表达地址模式 |
| 每 beat 地址 | 每个 beat 都有地址阶段 | 一个地址请求描述整个 burst |

AXI 协议 `WRAP` 地址边界范围的计算方法与 AHB 协议一致。

## 4. AXI Burst：比 AHB 更“事务化”

> 对应课件：PDF p.31-p.32（页脚 69-70）

AXI burst 的核心：

```text
一次地址请求 + 多个数据 beat
```

写 burst：

```text
AW：发起一次写 burst，给出起始地址、长度、大小、burst 类型
W ：连续发送多个写数据 beat
B ：整个写事务完成后返回一次写响应
```

读 burst：

```text
AR：发起一次读 burst，给出起始地址、长度、大小、burst 类型
R ：返回多个读数据 beat，并携带读响应
```

### 4.1 WLAST 与 RLAST

`WLAST` 和 `RLAST` **用来标记 burst 的最后一个 data beat**。

| 信号 | 通道 | source | 含义 |
| --- | --- | --- | --- |
| `WLAST` | W | master | 当前写数据 beat 是本次写 burst 的最后一个 |
| `RLAST` | R | slave | 当前读数据 beat 是本次读 burst 的最后一个 |

课件明确提到：WLAST indicates final data.

要注意：

- `WLAST=1` 表示写数据部分最后一个 beat。
- `WLAST` **不等于写事务完全结束**。
- 写事务整体还要等 `B` 通道写响应。

### 4.2 AXI burst 和 AHB burst 的最大差异

AHB burst 更像：

```text
每一拍地址阶段都出现一个地址：
Beat 0: HTRANS=NONSEQ, HADDR=A0
Beat 1: HTRANS=SEQ,    HADDR=A1
Beat 2: HTRANS=SEQ,    HADDR=A2
...
```

AXI burst 的语义划分为：


- AW/AR **一次说明整个 burst**：
    - 起始地址 = A0
    - beat 数  = AxLEN + 1
    - beat 大小 = AxSIZE
    - 地址模式 = AxBURST
- 之后 W/R 通道连续搬多个 data beats。


因此，AXI 的 burst 更像一个完整 transaction，而 AHB 的 burst 更像连续地址阶段构成的一串 transfer。

## 5. WSTRB：写数据的字节选通

`WSTRB` 是 AXI 写数据通道的重要字段，用于说明 `WDATA` 中哪些 byte lanes 有效。

它和 APB 的 `PSTRB` 思路类似：

```text
WSTRB[n] 对应 WDATA[8n+7 : 8n]
```

例如 32-bit `WDATA`：

| WSTRB bit | 对应字节 |
| --- | --- |
| `WSTRB[0]` | `WDATA[7:0]` |
| `WSTRB[1]` | `WDATA[15:8]` |
| `WSTRB[2]` | `WDATA[23:16]` |
| `WSTRB[3]` | `WDATA[31:24]` |

典型用途：

- 写一个 32-bit word 中的某个 byte。
- **支持非满宽写**。
- 支持内存映射寄存器中的**局部字段写入**。

判断题抓手：

- `WSTRB` 属于**写数据通道，不属于写地址通道**。
- `WSTRB` 指示哪个 byte lane 被写入。
- `WSTRB` 不用于读数据通道。

## 6. RESP：事务响应

AXI 中常见响应字段：

| 通道 | 响应字段 | 方向 | 含义 |
| --- | --- | --- | --- |
| B | `BRESP` | slave -> master | 写响应 |
| R | `RRESP` | slave -> master | 读响应，随读数据返回 |

常见响应类型：

| 响应 | 含义 |
| --- | --- |
| OKAY | 正常访问成功 |
| EXOKAY | exclusive access 成功 |
| SLVERR | slave error，slave 接收了访问但返回错误 |
| DECERR | decode error，地址译码失败或没有目标 slave |

课程复习时重点记：

- 写响应走独立 `B` 通道。
- 读响应随 `R` 通道返回。
- AXI 不只是传数据，也会明确返回访问状态。

和 AHB 对比：

| 项目 | AHB | AXI |
| --- | --- | --- |
| 响应信号 | `HRESP` | `BRESP`, `RRESP` |
| 写响应 | 数据阶段通过 `HRESP/HREADY` 体现 | 单独 `B` 通道返回 |
| 读响应 | 数据阶段通过 `HRESP/HREADY` 体现 | 随 `R` 通道返回 |

## 7. ID、Outstanding 与乱序完成

> 对应课件：PDF p.26, p.32（页脚 64, 70）

课件强调 AXI 支持：

```text
Multiple outstanding addresses
Out-of-order transaction completion
Fast slaves may return data ahead of slow slaves
```

这背后需要一个关键机制：**transaction ID**。

### 7.1 为什么需要 ID

如果 **master 连续发出多个事务**：

```text
Transaction A -> 慢 slave
Transaction B -> 快 slave
```

快 **slave 可能先返回 B 的响应**。  
如果没有 ID，master 就很难判断返回的数据/响应属于哪一笔请求。

因此 **AXI 使用 ID 类字段来标记事务**，例如：

```text
AWID / BID
ARID / RID
```

理解即可：

- 地址请求带 ID。
- 返回响应/读数据也带对应 ID。
- master 根据 ID 匹配返回结果。

### 7.2 Outstanding 的真正含义

Outstanding transaction 指：

```text
已经发起，但还没有完成的事务。
```

AXI 允许 master 在前一个事务未完成时继续发起新事务。  
这能隐藏访问延迟，提高吞吐。

但 outstanding 不是无限多：

- 受 master 生成能力限制。
- 受 slave/interconnect 缓冲能力限制。
- 受 ID 宽度和实现约束限制。

### 7.3 Out-of-order 的边界

AXI 支持乱序完成，但不是“随便乱”。

更准确的初学表述：

- **不同 ID 的事务可以更容易乱序返回**。
- **同一 ID 的事务通常有更强的顺序约束**。
- master 必须能根据 ID 把返回数据和原始请求对应起来。

考试层面建议记：

```text
ID 是 AXI 支持 outstanding / out-of-order 的关键机制之一。
```

## 8. Interleaving 不等于任意混排

> 对应课件：PDF p.32（页脚 70）

课件写到：

```text
AXI supports interleaved out-of-order transactions.
```

课程层面可以理解为：

- **多个读/写事务可以在时间上交错**。
- 读事务和写事务可以同时存在。
- 快 slave 可以先返回结果。
- 事务完成顺序不一定等于发起顺序。

但要避免一个误解：

```text
interleaved 不等于所有 beat 都可以不受限制地任意混在一起。
```

具体到某个 AXI 版本，读数据、写数据、ID、ordering 都有规则约束。  
本课程复习时不需要深挖版本细节，只要掌握“AXI 比 AHB 更允许并发和乱序，但仍靠 ID/通道规则保证正确性”。

## 9. AXI 与 AHB 的关键差异表

> 对应课件：PDF p.26-p.32（页脚 64-70）

| 维度 | AHB | AXI |
| --- | --- | --- |
| 协议形态 | 总线协议，典型共享/层级总线思路 | IP 接口规范，不等同于具体 interconnect |
| 通道结构 | 地址/控制流水 + 读/写数据相关信号 | 五个独立通道：AW/W/B/AR/R |
| 读写并发 | 读写共享同一套地址控制路径，并发能力有限 | 读写通道独立，可同时读写 |
| 地址与数据关系 | 地址阶段和数据阶段固定流水关系，数据通常滞后一拍 | 地址通道和数据通道解耦，时间关系更灵活 |
| wait/backpressure | `HREADY=0` 会冻结整个 AHB 流水线 | 各通道可独立 backpressure |
| burst 地址 | 每个 beat 都有地址阶段，`HTRANS` 区分 `NONSEQ/SEQ` | 一个地址请求描述整个 burst，data 通道传多个 beat |
| burst 字段 | `HBURST` + `HSIZE` | `AxLEN` + `AxSIZE` + `AxBURST` |
| 写响应 | 通过数据阶段响应体现 | 独立 `B` 通道 |
| 读响应 | 数据阶段响应 | 随 `R` 通道返回 |
| outstanding | 不是核心特征 | 核心特征之一 |
| 乱序完成 | 不作为核心能力 | 支持 out-of-order transaction completion |
| 事务识别 | 不强调 transaction ID | 用 ID 匹配 outstanding/乱序事务 |

最关键的考试句：

```text
AHB 是流水化的 bus transfer；
AXI 是多通道解耦的 transaction。
```

## 10. AXI4、AXI4-Lite、AXI4-Stream 的定位

> 对应课件：PDF p.33-p.34（页脚 71-72）

课件规格图中出现了 AXI3、AXI4、AXI4-Lite、AXI4-Stream、AXI5、ACE、CHI 等。

课程复习建议只抓定位：

| 规格 | 定位 |
| --- | --- |
| AXI4 | 面向 memory-mapped 高性能事务，支持 burst、outstanding 等 |
| AXI4-Lite | AXI4 的简化子集，常用于简单寄存器访问 |
| AXI4-Stream | 面向流式数据传输，不是 memory-mapped 地址访问 |
| ACE | AXI Coherency Extensions，和多核 cache coherence 相关 |
| CHI | Coherent Hub Interface，更偏一致性互连和可扩展系统 |

### 10.1 AXI4-Lite

AXI4-Lite 可以粗略理解为：

```text
像 APB 一样常用于寄存器访问，但接口形式属于 AXI 家族。
```

常见特点：

- 简化。
- 通常单 beat 访问。
- 不强调 burst。
- 适合控制寄存器、配置寄存器。

不要把 AXI4-Lite 当作高吞吐数据搬运接口。

### 10.2 AXI4-Stream

AXI4-Stream 可以粗略理解为：

```text
只关心数据流，不关心地址。
```

典型用途：

- DMA 数据流。
- 视频/音频流。
- 网络包流。
- 硬件加速器之间的数据流。

常见字段会有：

- `TDATA`：数据。
- `TVALID/TREADY`：流式握手。
- `TLAST`：一帧或一个 packet 的末尾。
- `TKEEP/TSTRB`：字节有效信息。

课件 SoC 示例里也出现了 `AXI-Stream`，说明真实 SoC 中 AXI、AXI-Stream、CHI、APB 可以同时存在。

## 11. 容易混淆的概念对照

| 容易混淆项 | 正确理解 |
| --- | --- |
| AXI 是总线还是接口 | 课件强调它是 interface specification，不是 interconnect itself |
| `AxLEN` 是否等于字节数 | 不是，表示 burst beat 数相关；每 beat 大小由 `AxSIZE` 表示 |
| `AxSIZE` 是否等于总 burst 大小 | 不是，它表示每个 beat 多大 |
| `AxBURST` 是否表示 beat 数 | 不主要表示 beat 数，它表示地址变化模式，如 FIXED/INCR/WRAP |
| `WLAST` 是否表示写事务结束 | 不是，只表示写数据最后一个 beat；写事务还要 B 响应 |
| AXI 读是否有单独 Read Response 通道 | 没有，读响应随 R 通道返回 |
| out-of-order 是否意味着无规则乱序 | 不是，依赖 ID 和 ordering 规则 |
| outstanding 是否无限多 | 不是，受实现资源和协议字段限制 |
| AXI4-Stream 是否有地址 | 通常不走 memory-mapped 地址，面向数据流 |

## 12. 判断题与填空抓手

1. AXI 是接口规范，不是具体 interconnect 本身。正确。
2. AXI 写事务由 AW、W、B 三类通道信息共同完成。正确。
3. AXI 读事务由 AR 和 R 通道完成，读响应随 R 通道返回。正确。
4. AXI burst 中，一个地址请求可以描述整个 burst。正确。
5. AXI burst 的每个 data beat 都必须重新发送完整地址。错误。
6. `AxLEN` 表示 burst beat 数相关字段，常按 `AxLEN+1` 理解 beat 数。正确。
7. `AxSIZE` 表示每个 beat 的大小。正确。
8. `AxBURST` 表示地址变化模式，例如 FIXED、INCR、WRAP。正确。
9. `WSTRB` 表示写数据中哪些 byte lanes 有效。正确。
10. `WLAST` 表示写数据通道最后一个 beat。正确。
11. `WLAST` 出现后写事务一定已经完全结束。错误。
12. 写事务最终还需要 B 通道返回写响应。正确。
13. `BRESP` 是写响应，`RRESP` 是读响应。正确。
14. AXI 支持多个 outstanding transactions。正确。
15. outstanding transaction 指已经发起但尚未完成的事务。正确。
16. AXI 支持 out-of-order completion，因此不需要 ID。错误。
17. ID 可用于区分多个 outstanding 或乱序返回的事务。正确。
18. AHB 的 `HREADY=0` 通常冻结整个流水线；AXI 可以按通道独立反压。正确。
19. AXI4-Lite 通常用于简单寄存器访问，不强调 burst。正确。
20. AXI4-Stream 面向流式数据传输，不是普通 memory-mapped 地址访问。正确。

## 13. 考前最短版

AXI 除握手以外，最重要的是“事务化”和“解耦”。写事务由 `AW + W + B` 组成，读事务由 `AR + R` 组成。`AW/AR` 地址通道不仅给地址，还给出 burst 长度、beat 大小、地址模式、ID 等控制信息。

AXI burst 的核心是：**一个地址请求描述整个 burst，数据通道传多个 beat**。`AxLEN` 描述 beat 数，`AxSIZE` 描述每 beat 大小，`AxBURST` 描述地址变化模式。写 burst 用 `WLAST` 标记最后一个写数据 beat，读 burst 用 `RLAST` 标记最后一个读数据 beat。写事务最后还需要 `B` 通道返回 `BRESP`。

AXI 相比 AHB 的关键不同：AHB 是地址/数据阶段固定流水的总线协议，wait state 会通过 `HREADY` 影响整个流水线；AXI 是五通道解耦的接口协议，读写、地址、数据、响应可以更独立地推进，支持 outstanding 和 out-of-order。ID 是理解 AXI 多 outstanding 和乱序返回的关键。
