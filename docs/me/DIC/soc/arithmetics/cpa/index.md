# Carry-Propagate Adder Basics

本文面向 LAB2 的 9 bit signed multiplier 最终 CPA 设计，目标是从 0 开始理解常见的 carry-propagate adder 结构。

在乘法器中，Dadda/Wallace 压缩树只负责把很多 partial product dots 压成两行：

```text
row0 + row1
```

最后一步必须用 CPA 得到标准二进制乘积：

```text
two rows -> final CPA -> product
```

本文重点介绍：

- RCA: ripple-carry adder
- CLA: carry-lookahead adder
- Carry-skip adder
- Carry-select adder
- Conditional-sum adder
- Parallel-prefix adder: Kogge-Stone, Brent-Kung, Sklansky
- 对 LAB2 18 bit final CPA 的选型建议

## I. What Is A CPA

### 1.1 CPA 的任务

CPA 是 carry-propagate adder，意思是“进位传播加法器”。它和 CSA 的根本区别是：

```text
CSA: 不传播长进位，只把多行压成两行。
CPA: 传播进位，输出标准二进制和。
```

假设要计算：

$$
S = A + B + c_0
$$

其中：

$$
A = \sum_{i=0}^{n-1} a_i2^i,\quad
B = \sum_{i=0}^{n-1} b_i2^i
$$

CPA 要输出：

$$
S = \sum_{i=0}^{n-1}s_i2^i + c_n2^n
$$

这里 \(c_n\) 是最终进位。对于固定 18 bit 二补码乘法器，如果只需要 18 bit 输出，最终超出 bit 17 的 carry 可以丢弃。

### 1.2 一位全加器公式

一位 full adder 的输入是：

```text
a_i, b_i, c_i
```

输出是：

```text
s_i, c_{i+1}
```

公式为：

$$
s_i = a_i \oplus b_i \oplus c_i
$$

$$
c_{i+1} = a_i b_i + a_i c_i + b_i c_i
$$

如果直接用 full adder 串起来，就是 RCA。

### 1.3 Propagate 和 Generate

为了分析高速加法器，通常定义：

$$
p_i = a_i \oplus b_i
$$

$$
g_i = a_i b_i
$$

其中：

- \(g_i\): generate。若 \(g_i=1\)，bit i 自己一定产生进位。
- \(p_i\): propagate。若 \(p_i=1\)，输入进位 \(c_i\) 会传到 \(c_{i+1}\)。

于是：

$$
s_i = p_i \oplus c_i
$$

$$
c_{i+1} = g_i + p_i c_i
$$

这是 CPA 设计中最重要的递推式。几乎所有高速 CPA 都是在加速这个式子的求解。

### 1.4 Propagate/Generate 真值表

| a_i | b_i | p_i = a_i xor b_i | g_i = a_i b_i | 含义 |
| --- | --- | ----------------- | ------------- | ---- |
| 0 | 0 | 0 | 0 | kill carry |
| 0 | 1 | 1 | 0 | propagate carry |
| 1 | 0 | 1 | 0 | propagate carry |
| 1 | 1 | 0 | 1 | generate carry |

注意：有些教材会定义 \(p_i=a_i+b_i\)，即 OR propagate。本文使用更常见的 XOR propagate。两种定义都能推导 CLA，但 sum 公式会略有不同。

## II. RCA: Ripple-Carry Adder

### 2.1 基本结构

RCA 是最简单的 CPA。它把 n 个 full adders 从低位到高位串联：

```text
c0 -> FA0 -> c1 -> FA1 -> c2 -> ... -> FA(n-1) -> cn
```

第 i 位：

$$
s_i = p_i \oplus c_i
$$

$$
c_{i+1} = g_i + p_i c_i
$$

由于 \(c_{i+1}\) 依赖 \(c_i\)，所以 bit i+1 必须等待 bit i 的 carry。

### 2.2 延迟和面积

RCA 面积很小：

$$
Area_{RCA} = O(n)
$$

但延迟随位宽线性增长：

$$
Delay_{RCA} = O(n)
$$

更具体地说，critical path 通常是：

```text
c0 -> c1 -> c2 -> ... -> cn
```

也就是 carry chain。

### 2.3 4 bit RCA 例子

计算：

```text
  A = 1011 = 11
+ B = 0110 =  6
--------------
      10001 = 17
```

先计算每一位的 p/g：

| i | a_i | b_i | p_i | g_i |
| - | --- | --- | --- | --- |
| 0 | 1 | 0 | 1 | 0 |
| 1 | 1 | 1 | 0 | 1 |
| 2 | 0 | 1 | 1 | 0 |
| 3 | 1 | 0 | 1 | 0 |

设 \(c_0=0\)：

$$
c_1 = g_0 + p_0c_0 = 0
$$

$$
c_2 = g_1 + p_1c_1 = 1
$$

$$
c_3 = g_2 + p_2c_2 = 1
$$

$$
c_4 = g_3 + p_3c_3 = 1
$$

sum:

$$
s_0 = p_0 \oplus c_0 = 1
$$

$$
s_1 = p_1 \oplus c_1 = 0
$$

$$
s_2 = p_2 \oplus c_2 = 0
$$

$$
s_3 = p_3 \oplus c_3 = 0
$$

结果：

```text
c4 s3 s2 s1 s0 = 1 0001
```

### 2.4 RCA 适合什么时候用

RCA 适合：

- 位宽小。
- 时序不紧。
- 面积优先。
- 教学和手写门级实现。

对 LAB2 的 18 bit final CPA，如果目标频率是 100 MHz，RCA 往往是可以先尝试的版本。它非常容易写对，也方便验证。

## III. CLA: Carry-Lookahead Adder

### 3.1 CLA 的核心思想

CLA 试图避免 carry 一级一级 ripple，而是用组合逻辑直接算出每一级 carry。

从基本递推式开始：

$$
c_{i+1}=g_i+p_ic_i
$$

展开前几级：

$$
c_1 = g_0 + p_0c_0
$$

$$
c_2 = g_1 + p_1c_1
    = g_1 + p_1g_0 + p_1p_0c_0
$$

$$
c_3 = g_2 + p_2c_2
    = g_2 + p_2g_1 + p_2p_1g_0 + p_2p_1p_0c_0
$$

$$
c_4 = g_3 + p_3g_2 + p_3p_2g_1 + p_3p_2p_1g_0 + p_3p_2p_1p_0c_0
$$

这就是 lookahead。它用更多门电路换更短延迟。

### 3.2 4 bit CLA 结构

4 bit CLA 通常先计算 bit-level p/g：

$$
p_i = a_i \oplus b_i,\quad g_i = a_ib_i
$$

然后并行计算：

$$
c_1 = g_0 + p_0c_0
$$

$$
c_2 = g_1 + p_1g_0 + p_1p_0c_0
$$

$$
c_3 = g_2 + p_2g_1 + p_2p_1g_0 + p_2p_1p_0c_0
$$

$$
c_4 = g_3 + p_3g_2 + p_3p_2g_1 + p_3p_2p_1g_0 + p_3p_2p_1p_0c_0
$$

最后：

$$
s_i = p_i \oplus c_i
$$

### 3.3 Group Propagate 和 Group Generate

对一个 4 bit block，可以定义：

$$
P_{3:0}=p_3p_2p_1p_0
$$

$$
G_{3:0}=g_3+p_3g_2+p_3p_2g_1+p_3p_2p_1g_0
$$

于是 block carry out 可以写成：

$$
c_4=G_{3:0}+P_{3:0}c_0
$$

这和单 bit 公式形式完全一样：

$$
c_{out}=G+Pc_{in}
$$

所以 CLA 可以层次化：

```text
bit p/g -> 4 bit group P/G -> higher-level CLA -> carries
```

### 3.4 CLA 的优缺点

优点：

- 比 RCA 快。
- block 化后结构仍然比较规整。
- 适合 16 bit, 32 bit 等中等位宽。

缺点：

- 直接展开大位宽 carry 会导致扇入很大。
- 面积比 RCA 大。
- wiring 和门级 fan-in 要注意。

考试里可以这样总结：

```text
CLA speeds up addition by computing carries in advance using propagate and generate signals.
```

## IV. Carry-Skip Adder

### 4.1 Carry-skip 的核心思想

Carry-skip adder 又叫 carry-bypass adder。它仍然在 block 内使用 RCA，但如果整个 block 都会 propagate carry，就让 carry 直接跳过这个 block。

对一个 block，定义：

$$
P_{block} = \prod_{i=m}^{k} p_i
$$

如果 \(P_{block}=1\)，表示这个 block 中每一位都会传播 carry，于是：

$$
c_{out}=c_{in}
$$

如果 \(P_{block}=0\)，则使用 block 内 RCA 算出来的 carry：

$$
c_{out}=c_{ripple}
$$

所以可以用 mux 表示：

$$
c_{out}=P_{block}c_{in}+\overline{P_{block}}c_{ripple}
$$

### 4.2 结构

一个 4 bit carry-skip block：

```text
        p0 p1 p2 p3
         |  |  |  |
         AND tree -> P_block

cin -> FA0 -> FA1 -> FA2 -> FA3 -> c_ripple
  \                                 /
   ------------ mux ---------------
                 |
               cout
```

### 4.3 例子

如果某 4 bit block 中：

```text
p3 p2 p1 p0 = 1111
```

那么：

$$
P_{block}=1
$$

无论 block 内部如何 ripple，carry out 都等于 carry in：

$$
c_{out}=c_{in}
$$

如果：

```text
p3 p2 p1 p0 = 1011
```

那么：

$$
P_{block}=0
$$

carry 不能保证跳过整个 block，必须使用 RCA 算出来的 \(c_{ripple}\)。

### 4.4 延迟直觉

Carry-skip 的 worst-case path 通常包括：

```text
first block ripple + middle block skips + last block ripple
```

它比纯 RCA 快，但通常不如 CLA 或 parallel-prefix 快。

### 4.5 优缺点

优点：

- 比 RCA 快。
- 面积增加不大。
- 实现比 CLA 简单。

缺点：

- 加速依赖 block propagate。
- 最坏情况仍然有 ripple 段。
- block size 需要权衡。

## V. Carry-Select Adder

### 5.1 Carry-select 的核心思想

Carry-select adder, 简称 CSLA。它的想法非常直接：

```text
既然不知道 block 的 cin 是 0 还是 1，
那就两个都提前算好。
等真正 cin 到来后，用 mux 选择正确结果。
```

对每个 block：

```text
RCA0 assumes cin = 0
RCA1 assumes cin = 1
real cin selects one result
```

### 5.2 数学描述

对一个 block，预先计算：

$$
(S^{(0)}, c_{out}^{(0)}) = A_{block}+B_{block}+0
$$

$$
(S^{(1)}, c_{out}^{(1)}) = A_{block}+B_{block}+1
$$

当真实 \(c_{in}\) 到来：

$$
S =
\begin{cases}
S^{(0)}, & c_{in}=0 \\
S^{(1)}, & c_{in}=1
\end{cases}
$$

$$
c_{out} =
\begin{cases}
c_{out}^{(0)}, & c_{in}=0 \\
c_{out}^{(1)}, & c_{in}=1
\end{cases}
$$

硬件上就是 mux：

$$
S = \overline{c_{in}}S^{(0)} + c_{in}S^{(1)}
$$

$$
c_{out} = \overline{c_{in}}c_{out}^{(0)} + c_{in}c_{out}^{(1)}
$$

### 5.3 16 bit carry-select 例子

把 16 bit 分成 4 个 block：

```text
block0: bit  3:0
block1: bit  7:4
block2: bit 11:8
block3: bit 15:12
```

block0 必须根据真实 \(c_0\) ripple：

```text
block0 uses one RCA
```

block1, block2, block3 可以各自并行计算两种情况：

```text
cin = 0 version
cin = 1 version
```

当 block0 的 carry out 到来后，选择 block1 的结果；block1 的 selected carry 再选择 block2；依此类推。

关键路径大致是：

```text
block0 RCA delay + several mux delays
```

而不是：

```text
all 16 bits RCA delay
```

### 5.4 Carry-select tree

普通 CSLA 的 block carry selection 仍然是串行 mux 链。为了进一步加速，可以把选择过程做成 tree 或层次结构。

例如 16 bit 可以先分为 4 bit 小块，再把两个小块合成 8 bit conditional result：

```text
4 bit conditional sums
        |
        v
8 bit conditional sums
        |
        v
16 bit final selection
```

这种结构接近 conditional-sum adder：它不仅预计算 sum，也预计算更大范围在 carry-in 为 0/1 时的结果，然后用层次化 mux 选择。

直觉上：

```text
linear carry-select: selection path is a chain
tree carry-select: selection path is a tree
```

代价是更多硬件和更多 mux。

### 5.5 优缺点

优点：

- 延迟比 RCA 小很多。
- 概念简单。
- block 化实现方便。

缺点：

- 面积较大，因为很多 block 算两遍。
- mux 很多。
- 对小位宽未必值得。

考试里可以这样总结：

```text
Carry-select adder reduces delay by precomputing both possible carry-in cases and selecting the correct one later.
```

## VI. Conditional-Sum Adder

### 6.1 Conditional-sum 是什么

Conditional-sum adder 可以看成 carry-select 的树形推广。

它对每个 bit 或小 block 都计算两种结果：

```text
cin = 0
cin = 1
```

然后逐级合并，形成更大 block 在 carry-in 为 0/1 时的条件结果。

### 6.2 两个 block 如何合并

假设低 block L 和高 block H 都已经有两套结果：

```text
L0: low block result when cin = 0
L1: low block result when cin = 1
H0: high block result when its cin = 0
H1: high block result when its cin = 1
```

当整个 combined block 的 cin = 0 时：

1. 低 block 使用 L0。
2. L0 的 carry out 决定高 block 选 H0 还是 H1。

当整个 combined block 的 cin = 1 时：

1. 低 block 使用 L1。
2. L1 的 carry out 决定高 block 选 H0 还是 H1。

这样就能生成 combined block 的两套条件结果。

### 6.3 延迟和面积

Conditional-sum 的选择网络是树形的，所以延迟大致是：

$$
Delay = O(\log n)
$$

但它需要大量重复计算和 mux，所以面积较大：

$$
Area > Area_{CSLA} > Area_{RCA}
$$

它更像理论上优雅、速度较快，但手写 RTL 比较繁琐的结构。

## VII. Parallel-Prefix Adders

### 7.1 Prefix adder 的核心思想

Parallel-prefix adder 是现代高速 CPA 中非常重要的一类，包括：

- Kogge-Stone adder
- Brent-Kung adder
- Sklansky adder
- Han-Carlson adder

它们的共同目标是快速计算所有 carry。

基本公式仍然是：

$$
c_{i+1}=g_i+p_ic_i
$$

难点是快速得到每一位从低位到当前位的 group generate 和 group propagate。

### 7.2 Prefix operator

定义每一位的 pair：

$$
(G_i,P_i)=(g_i,p_i)
$$

如果有两个相邻区间：

```text
high interval: (G_H, P_H)
low interval : (G_L, P_L)
```

合并后的区间满足：

$$
G = G_H + P_HG_L
$$

$$
P = P_HP_L
$$

记作 prefix operator：

$$
(G_H,P_H)\circ(G_L,P_L)
= (G_H+P_HG_L,\ P_HP_L)
$$

这个 operator 是 associative 的：

$$
X\circ(Y\circ Z)=(X\circ Y)\circ Z
$$

因此可以用 tree 并行计算所有前缀。

### 7.3 如何由 prefix 得到 carry

如果已经算出：

$$
(G_{i:0},P_{i:0})
$$

则：

$$
c_{i+1}=G_{i:0}+P_{i:0}c_0
$$

然后：

$$
s_i=p_i\oplus c_i
$$

### 7.4 8 bit prefix 例子

对 bit 0 到 bit 7，先有：

```text
(g0,p0), (g1,p1), ..., (g7,p7)
```

目标是并行算：

```text
(G0:0, P0:0)
(G1:0, P1:0)
(G2:0, P2:0)
...
(G7:0, P7:0)
```

例如：

$$
G_{3:0}=g_3+p_3g_2+p_3p_2g_1+p_3p_2p_1g_0
$$

$$
P_{3:0}=p_3p_2p_1p_0
$$

Prefix tree 的作用就是快速算出这些 \(G_{i:0}\) 和 \(P_{i:0}\)。

## VIII. Common Prefix Topologies

### 8.1 Kogge-Stone Adder

Kogge-Stone 是速度很快的 prefix adder。

特点：

- 逻辑深度小：

$$
O(\log n)
$$

- fan-out 小。
- wiring 很多。
- area 较大。

8 bit Kogge-Stone 大概分 3 个 prefix levels：

```text
level 1: distance 1
level 2: distance 2
level 3: distance 4
```

每一层把更远范围的 carry 信息合并进来。

适合：

- 高性能处理器 ALU。
- 宽位加法器。
- timing 非常紧的路径。

不太适合：

- 很小位宽。
- 面积敏感的课程实验。

### 8.2 Brent-Kung Adder

Brent-Kung 比 Kogge-Stone 更省面积和 wiring，但逻辑层数更多。

特点：

- area 较小。
- wiring 较少。
- fan-out 可控。
- delay 比 Kogge-Stone 略大。

可以粗略记为：

```text
Kogge-Stone: faster, larger
Brent-Kung : smaller, slower
```

Brent-Kung 常被看作很好的折中结构。

### 8.3 Sklansky Adder

Sklansky 又叫 divide-and-conquer adder。

特点：

- prefix depth 小。
- 结构很规整。
- 某些节点 fan-out 很大。

大 fan-out 会让实际物理实现中负载变大，因此理论逻辑级数少不一定代表实际最快。

### 8.4 Han-Carlson Adder

Han-Carlson 是 Kogge-Stone 和 Brent-Kung 的折中。

特点：

- 比 Kogge-Stone 少 wiring。
- 比 Brent-Kung 快。
- 结构复杂度中等。

如果不是为了做高性能加法器专题，课程实验中通常不需要手写 Han-Carlson。

## IX. Comparison Table

| Adder | Delay | Area | Wiring | Concept | 适合场景 |
| ----- | ----- | ---- | ------ | ------- | -------- |
| RCA | O(n) | O(n) | 很少 | 最简单 | 小位宽、面积优先 |
| CLA | O(log n) 或 block-level | 中等 | 中等 | 提前算 carry | 中等位宽 |
| Carry-skip | 约 O(sqrt n) | 小到中等 | 少 | carry 跳过 block | 简单提速 |
| Carry-select | block RCA + mux chain | 较大 | 中等 | 两种 cin 都预计算 | 位宽中等、速度优先 |
| Conditional-sum | O(log n) | 大 | 多 | tree select | 高速但面积大 |
| Kogge-Stone | O(log n) | 大 | 很多 | prefix tree | 极高速 |
| Brent-Kung | O(log n) | 中等 | 较少 | prefix tree | 面积/速度折中 |
| Sklansky | O(log n) | 中等 | 中等 | divide-and-conquer | 低深度但 fan-out 大 |

## X. Choosing A Final CPA For LAB2

### 10.1 你的 multiplier 最终需要什么

你的 Dadda tree 会把 18 个 column 压到最多两行。最终 CPA 输入可以理解为：

```text
row0[17:0]
row1[17:0]
```

输出：

```text
out[17:0] = row0 + row1
```

由于这是 9 bit signed x 9 bit signed，完整乘积正好是 18 bit 二补码。因此 bit 18 的最终 carry 不需要作为输出。

### 10.2 推荐第一版: 18 bit RCA

第一版建议使用 RCA：

```text
bit 0 FA -> bit 1 FA -> ... -> bit 17 FA
```

理由：

- 最容易写对。
- 面积小。
- 和门级实现要求最匹配。
- 18 bit 位宽不大。
- 当前系统 100 MHz 目标下大概率可接受。

门级 RCA 可以按下面的模式写：

```text
c[0] = 0
for i = 0..17:
    out[i] = row0[i] xor row1[i] xor c[i]
    c[i+1] = majority(row0[i], row1[i], c[i])
```

也就是：

$$
out_i = row0_i \oplus row1_i \oplus c_i
$$

$$
c_{i+1}=row0_irow1_i+row0_ic_i+row1_ic_i
$$

### 10.3 如果 RCA 时序不够: 4 bit block CLA

如果 DC 报告显示 final CPA 是关键路径，可以升级为 block CLA。

一种适合 18 bit 的切法：

```text
block0: bit  3:0
block1: bit  7:4
block2: bit 11:8
block3: bit 15:12
block4: bit 17:16
```

每个 4 bit block 内部用 CLA 直接算 carry，block 间也可以用 group P/G 进一步 lookahead。

这样比纯 RCA 快，但复杂度仍然可控。

### 10.4 如果想展示优化: Carry-select

如果实验报告想体现 CPA 优化，可以做 18 bit carry-select：

```text
block0: 4 bit RCA
block1: 4 bit dual RCA + mux
block2: 4 bit dual RCA + mux
block3: 4 bit dual RCA + mux
block4: 2 bit dual RCA + mux
```

关键路径大致变成：

```text
4 bit RCA delay + 4 mux delays
```

比 18 bit RCA 短，但面积大约会增加，因为后面每个 block 有两套 RCA。

### 10.5 不推荐第一版就写 Kogge-Stone

Kogge-Stone 对 18 bit 当然可行，但手写容易出错，而且 wiring 很多。对于这个实验来说，它更适合作为“如果有额外时间再优化”的版本。

建议路线：

```text
Version 1: RCA, make it correct
Version 2: 4 bit block CLA or carry-select, compare DC timing/area
Version 3: prefix adder only if you want an advanced optimization story
```

## XI. Worked Example: 4 Bit CLA vs RCA

### 11.1 RCA 的 carry chain

RCA 中：

$$
c_1 = g_0+p_0c_0
$$

$$
c_2 = g_1+p_1c_1
$$

$$
c_3 = g_2+p_2c_2
$$

$$
c_4 = g_3+p_3c_3
$$

每一级都等前一级。

### 11.2 CLA 的直接展开

CLA 中：

$$
c_1 = g_0+p_0c_0
$$

$$
c_2 = g_1+p_1g_0+p_1p_0c_0
$$

$$
c_3 = g_2+p_2g_1+p_2p_1g_0+p_2p_1p_0c_0
$$

$$
c_4 = g_3+p_3g_2+p_3p_2g_1+p_3p_2p_1g_0+p_3p_2p_1p_0c_0
$$

所以 CLA 通过更大的组合逻辑提前算 carry。它不是不需要 carry，而是不让 carry 一级一级 ripple。

### 11.3 小例子

令：

```text
A = 1011
B = 0110
c0 = 0
```

得到：

```text
p3 p2 p1 p0 = 1 1 0 1
g3 g2 g1 g0 = 0 0 1 0
```

CLA 计算：

$$
c_1 = 0 + 1\cdot0 = 0
$$

$$
c_2 = 1 + 0\cdot0 + 0\cdot1\cdot0 = 1
$$

$$
c_3 = 0 + 1\cdot1 + 1\cdot0\cdot0 + 1\cdot0\cdot1\cdot0 = 1
$$

$$
c_4 = 0 + 1\cdot0 + 1\cdot1\cdot1 + 1\cdot1\cdot0\cdot0 + 1\cdot1\cdot0\cdot1\cdot0 = 1
$$

sum:

$$
s_i=p_i\oplus c_i
$$

所以：

```text
s = 0001
c4 = 1
result = 10001
```

结果和 RCA 一样，但 carry 的计算方式不同。

## XII. Exam-Oriented Summary

### 12.1 必背概念

CPA:

```text
Propagates carry and outputs the final binary sum.
```

RCA:

```text
Smallest and simplest CPA, but carry delay is linear in bit width.
```

CLA:

```text
Uses generate/propagate equations to compute carries in advance.
```

Carry-skip:

```text
Lets carry bypass a block when all bits in that block propagate carry.
```

Carry-select:

```text
Precomputes both cin=0 and cin=1 results, then selects by the real carry.
```

Parallel-prefix:

```text
Uses an associative prefix operator to compute all carries in logarithmic depth.
```

### 12.2 必背公式

Bit propagate/generate:

$$
p_i=a_i\oplus b_i,\quad g_i=a_ib_i
$$

Carry recurrence:

$$
c_{i+1}=g_i+p_ic_i
$$

Sum:

$$
s_i=p_i\oplus c_i
$$

Prefix combine:

$$
(G_H,P_H)\circ(G_L,P_L)
= (G_H+P_HG_L,\ P_HP_L)
$$

Block carry:

$$
c_{out}=G_{block}+P_{block}c_{in}
$$

### 12.3 典型考题回答

Question:

```text
Why is RCA slow?
```

Answer:

```text
Because each bit's carry depends on the previous bit's carry, so the carry must ripple through all bits in the worst case.
```

Question:

```text
How does CLA speed up addition?
```

Answer:

```text
CLA expands carry equations using generate and propagate signals, allowing carries to be computed in parallel or hierarchically.
```

Question:

```text
What is the cost of carry-select adder?
```

Answer:

```text
It reduces delay by precomputing both carry-in cases, but it increases area because many blocks are duplicated and muxes are required.
```

Question:

```text
What is the key idea of parallel-prefix adders?
```

Answer:

```text
They use the associative generate/propagate prefix operator to compute all carry signals with logarithmic logic depth.
```

## XIII. Suggested Report Description

如果你最终使用 RCA，可以在报告中写：

```text
After Dadda reduction, the partial product matrix is reduced to two 18 bit rows.
The final carry-propagate addition is implemented as an 18 bit ripple-carry
adder using full-adder equations. Although RCA has linear carry propagation
delay, the final adder width is only 18 bits, so it provides a compact and
straightforward gate-level implementation for this lab.
```

如果你使用 carry-select 或 CLA，可以补充：

```text
To reduce the final carry propagation delay, the final CPA can be replaced by
a block carry-lookahead or carry-select adder. These structures trade extra
area for shorter carry computation delay by computing carries in advance or
precomputing both possible carry-in cases.
```
