# 9 bit Multiplier Partial Product Reduction Basics

本文面向 LAB2 的 9 bit signed multiplier 设计，目标是从 0 开始理解下面四个概念：

- CPA / RCA: carry-propagate adder / ripple-carry adder
- CSA: carry-save adder
- Wallace Tree
- Dadda Tree

这些概念在乘法器中的关系可以先用一句话抓住：

```text
partial products -> CSA compression tree -> two rows -> final CPA -> product
```

其中 Wallace Tree 和 Dadda Tree 都不是新的加法器单元，而是组织很多 HA/FA 的不同调度策略。

## I. From Multiplication To Dot Matrix

### 1.1 为什么乘法器不是一个简单的加法器

以无符号乘法为例，两个 n bit 数

$$
A = \sum_{i=0}^{n-1} a_i 2^i,\quad
B = \sum_{j=0}^{n-1} b_j 2^j
$$

则乘积为

$$
P = A \times B
  = \sum_{i=0}^{n-1}\sum_{j=0}^{n-1} a_i b_j 2^{i+j}
$$

其中每一项

$$
p_{i,j} = a_i b_j
$$

就是一个 partial product bit。它的权重是

$$
2^{i+j}
$$

所以乘法器的本质是：先生成很多带权重的 bit，再把相同权重的 bit 加起来。

### 1.2 dot matrix 的含义

在乘法器课件里经常会看到点图。每一个点代表一个 bit，所在的列代表这个 bit 的权重。

例如 4 bit unsigned multiplier 的 column height 是：

```text
column: 0 1 2 3 4 5 6
height: 1 2 3 4 3 2 1
```

解释如下：

```text
column 0: a0b0
column 1: a1b0, a0b1
column 2: a2b0, a1b1, a0b2
column 3: a3b0, a2b1, a1b2, a0b3
...
```

每一列的所有 dots 都拥有相同权重。例如 column 3 中的每个 dot 都乘以 \(2^3\)。

### 1.3 乘法器压缩的目标

假设某一列有 9 个 dots。如果直接用普通加法器逐行相加，会产生很长的 carry propagation path。乘法器的高速设计通常分两步：

1. 使用 CSA tree 把每一列的 dot height 压到不超过 2。
2. 最后只剩两行数时，再用一次 CPA 得到标准二进制乘积。

也就是：

$$
\sum \text{all dots}
\quad\Rightarrow\quad
R_0 + R_1
\quad\Rightarrow\quad
P
$$

第一步不传播长进位，第二步才传播进位。

### 1.4 9 bit Modified Baugh-Wooley 的初始列高度

对 9 bit signed multiplier，使用 Modified Baugh-Wooley 后，初始 dot matrix 仍然可以被看成 18 个权重列：

```text
column: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17
height: 1 2 3 4 5 6 7 8 9 9  7  6  5  4  3  2  1  1
```

这里 column 17 的那个 dot 来自 Baugh-Wooley 的 correction bit。对 9 bit 二补码乘法，常用修正常数为：

$$
2^{17} + 2^9
$$

也就是在 column 17 和 column 9 各加入一个常数 dot。

## II. CPA And Ripple-Carry Adder

### 2.1 CPA 的准确含义

CPA 是 carry-propagate adder，即进位传播加法器。它的特点是输出是标准二进制结果，必须把 carry 从低位传播到高位。

Ripple-carry adder, 简称 RCA，是最基本的 CPA。很多同学会把 CPA 和 RCA 混着说，但严格讲：

```text
CPA: 一类会传播进位的最终加法器
RCA: 最简单的一种 CPA
```

其他 CPA 还包括 CLA, carry-skip adder, carry-select adder 等。

### 2.2 Half Adder

Half adder, 简称 HA，用来加两个 1 bit 输入：

```text
x + y -> sum, carry
```

公式为：

$$
s = x \oplus y
$$

$$
c = x y
$$

数值上有：

$$
x + y = s + 2c
$$

如果这个 HA 位于 column k，则：

$$
(x+y)2^k = s2^k + c2^{k+1}
$$

所以 HA 的 sum 留在本列，carry 进入高一列。

### 2.3 Full Adder

Full adder, 简称 FA，用来加三个 1 bit 输入：

```text
x + y + z -> sum, carry
```

公式为：

$$
s = x \oplus y \oplus z
$$

$$
c = xy + yz + xz
$$

数值上有：

$$
x + y + z = s + 2c
$$

如果 FA 位于 column k，则：

$$
(x+y+z)2^k = s2^k + c2^{k+1}
$$

因此 FA 也可以被称为 3:2 compressor：

```text
3 input dots -> 1 sum dot in same column + 1 carry dot in next column
```

### 2.4 Ripple-Carry Adder 的递推公式

对两个 n bit 输入 \(A\) 和 \(B\)，RCA 从最低位开始逐位相加：

$$
c_0 = 0
$$

$$
s_i = a_i \oplus b_i \oplus c_i
$$

$$
c_{i+1} = a_i b_i + a_i c_i + b_i c_i
$$

最终结果为：

$$
S = \sum_{i=0}^{n-1}s_i2^i + c_n2^n
$$

关键点是：第 i 位的计算依赖 \(c_i\)，而 \(c_i\) 又来自第 i-1 位。所以 RCA 的延迟随位宽线性增长：

$$
T_{RCA} \approx n \cdot T_{FA}
$$

这就是 ripple 的含义：carry 像水波一样从低位一级一级传到高位。

### 2.5 RCA 例子

计算：

```text
  1011  = 11
+ 0110  =  6
------
 10001  = 17
```

逐位过程：

| bit | a_i | b_i | c_i | s_i | c_{i+1} |
| --- | --- | --- | --- | --- | ------- |
| 0 | 1 | 0 | 0 | 1 | 0 |
| 1 | 1 | 1 | 0 | 0 | 1 |
| 2 | 0 | 1 | 1 | 0 | 1 |
| 3 | 1 | 0 | 1 | 0 | 1 |

所以：

```text
s[3:0] = 0001
c4     = 1
result = 10001
```

### 2.6 CPA 在乘法器里的位置

在高速乘法器中，CPA 通常只放在最后一步：

```text
many partial product rows
        |
        v
CSA / Wallace / Dadda compression
        |
        v
two rows
        |
        v
final CPA
        |
        v
product
```

原因是 CPA 会传播进位。如果在压缩树中间就频繁使用 CPA，会把 critical path 拉长。

考试里常见判断：

```text
CSA tree reduces the number of operands.
CPA produces the final binary result.
```

## III. CSA: Carry-Save Adder

### 3.1 CSA 解决什么问题

如果要加很多个数，例如：

$$
X_0 + X_1 + X_2 + \cdots + X_{m-1}
$$

使用 RCA tree 的问题是每一级 RCA 都要传播 carry，延迟很长。

CSA 的思想是：

```text
不要立刻传播进位。
把 carry 保存到下一列，留给后面的压缩级继续处理。
```

所以 CSA 的输出不是一个最终二进制数，而是两个向量：

```text
sum row
carry row
```

这两个向量还需要继续相加，最终才得到标准二进制数。

### 3.2 CSA 的基本单元就是 FA

一个 n bit CSA 可以看成 n 个互不串联的 FA。第 i 位独立计算：

$$
s_i = x_i \oplus y_i \oplus z_i
$$

$$
c_{i+1} = x_i y_i + y_i z_i + x_i z_i
$$

注意这里不是 \(c_i\)，而是 \(c_{i+1}\)。这是因为该 carry 的权重比当前列高一位。

向量形式为：

$$
X + Y + Z = S + (C \ll 1)
$$

其中：

- \(S\) 是 sum row
- \(C\) 是 carry row
- \(C \ll 1\) 表示 carry row 左移一位后再参与数值求和

### 3.3 CSA 和 CPA 的根本区别

CPA 的第 i 位需要等待低位 carry：

$$
s_i = f(a_i,b_i,c_i)
$$

CSA 的第 i 位只看本列输入：

$$
s_i,c_{i+1} = f(x_i,y_i,z_i)
$$

所以 CSA 不会产生横跨很多 bit 的 carry chain。它的单级延迟近似是一个 FA 的延迟：

$$
T_{CSA} \approx T_{FA}
$$

### 3.4 CSA 数值例子

计算三个 4 bit 数：

```text
X = 1011 = 11
Y = 0110 =  6
Z = 0101 =  5
```

真实结果是：

```text
11 + 6 + 5 = 22 = 10110
```

逐列使用 FA：

| bit | x_i | y_i | z_i | s_i | carry to bit i+1 |
| --- | --- | --- | --- | --- | ---------------- |
| 0 | 1 | 0 | 1 | 0 | 1 |
| 1 | 1 | 1 | 0 | 0 | 1 |
| 2 | 0 | 1 | 1 | 0 | 1 |
| 3 | 1 | 0 | 0 | 1 | 0 |

得到：

```text
S      = 1000
C << 1 = 01110
```

相加：

```text
  01000
+ 01110
-------
  10110 = 22
```

注意 CSA 本身没有直接输出 10110。它只是把三个操作数变成了两个操作数。

### 3.5 CSA 在 dot matrix 中的解释

如果某个 column k 中有 3 个 dots：

```text
column k: x, y, z
```

用一个 FA 后变成：

```text
column k:   sum
column k+1: carry
```

数值不变：

$$
(x+y+z)2^k = s2^k + c2^{k+1}
$$

这就是部分积压缩树的全部基础。

## IV. Partial Product Compression

### 4.1 column height

column height 指某个权重列里有多少个 dots。

例如：

```text
column 8 has height 9
```

表示 column 8 中有 9 个权重为 \(2^8\) 的 bit 需要相加。

### 4.2 FA 如何改变 column height

在 column k 放一个 FA：

```text
consume: 3 dots from column k
produce: 1 sum dot to column k
         1 carry dot to column k+1
```

因此本列高度减少 2：

$$
h_k' = h_k - 2
$$

下一列高度增加 1：

$$
h_{k+1}' = h_{k+1} + 1
$$

### 4.3 HA 如何改变 column height

在 column k 放一个 HA：

```text
consume: 2 dots from column k
produce: 1 sum dot to column k
         1 carry dot to column k+1
```

因此本列高度减少 1：

$$
h_k' = h_k - 1
$$

下一列高度增加 1：

$$
h_{k+1}' = h_{k+1} + 1
$$

HA 的总 dot 数没有减少，但它可以降低当前列高度，把压力推给高一列。

### 4.4 为什么最终要压到 2 行

当所有 column height 都不超过 2 时，可以把每列最多两个 dots 分别放入两行：

```text
row0[k] = first dot in column k, or 0
row1[k] = second dot in column k, or 0
```

于是整个 dot matrix 等价于：

$$
P = Row0 + Row1
$$

这时只需要一个 18 bit CPA。

## V. Wallace Tree

### 5.1 Wallace Tree 的核心思想

Wallace Tree 的原则可以概括为：

```text
每一级尽可能多地压缩。
只要某列有 3 个或更多 dots，就尽量放 FA。
必要时用 HA 处理剩下的 2 个 dots。
重复直到所有列高度不超过 2。
```

它的目标是减少压缩级数，也就是缩短 critical path。

### 5.2 Wallace Tree 的算法描述

给定初始 dot matrix：

1. 对每一列，将 dots 尽量按 3 个一组。
2. 每组 3 个 dots 用一个 FA。
3. FA 的 sum 输出进入下一 stage 的同一列。
4. FA 的 carry 输出进入下一 stage 的高一列。
5. 对每一 stage 重复上述过程。
6. 直到所有列的 height 都不超过 2。

注意：一个 stage 内的 FA/HA 是并行的。某列 FA 产生的 carry 应该作为下一 stage 的输入，而不是同一 stage 内继续串到另一个 FA。否则就会把两个 FA 串联起来，破坏 tree 的并行性。

### 5.3 Wallace Tree 的直觉例子

以 4x4 unsigned multiplier 为例，初始高度为：

```text
column: 0 1 2 3 4 5 6
height: 1 2 3 4 3 2 1
```

Wallace Tree 会在 column 2, 3, 4 等较高的列尽快放 FA/HA，使下一 stage 的高度迅速下降。

例如 column 3 初始有 4 个 dots，可以先用一个 FA 消耗 3 个：

```text
column 3: 4 dots
   use 1 FA
column 3 next stage: 2 dots
column 4 next stage: receives 1 carry dot
```

这一步局部上把 column 3 的压力降下来了，但 column 4 会变高。这就是为什么压缩树需要逐级规划，而不能只盯着单列看。

### 5.4 Wallace Tree 的优缺点

优点：

- 通常压缩级数少。
- 延迟较低，适合追求速度。
- 概念简单：能压就压。

缺点：

- 结构不规则。
- wire routing 复杂。
- 可能使用比 Dadda Tree 更多的 HA/FA。
- 手写 RTL 时容易乱，尤其是 9x9 以上。

考试里可以这样记：

```text
Wallace: greedy reduction, faster but less regular.
```

## VI. Dadda Tree

### 6.1 Dadda Tree 的核心思想

Dadda Tree 和 Wallace Tree 一样使用 FA/HA 压缩 dot matrix，但 Dadda Tree 不急着在早期压到很低。

它的原则是：

```text
每一级只压到刚好满足目标高度。
不要过早使用不必要的 HA/FA。
```

这样通常可以用更少的加法器，同时保持接近 Wallace Tree 的压缩级数。

### 6.2 Dadda target height 序列

Dadda Tree 先生成一组目标高度：

$$
d_1 = 2
$$

$$
d_{k+1} = \left\lfloor \frac{3}{2} d_k \right\rfloor
$$

所以序列为：

```text
2, 3, 4, 6, 9, 13, ...
```

如果初始最大 column height 是 9，则压缩目标倒着使用：

```text
9 -> 6 -> 4 -> 3 -> 2
```

真正需要执行的 reduction stage 是：

```text
target 6
target 4
target 3
target 2
```

### 6.3 Dadda Tree 的压缩规则

对某一级 target height \(d\)，目标是让该级输出的每一列高度不超过 \(d\)。

对 column k：

- 如果本列输出高度会超过 \(d\)，就放 FA 或 HA。
- FA 让本列输出高度减少 2，并向 column k+1 输出一个 carry。
- HA 让本列输出高度减少 1，并向 column k+1 输出一个 carry。
- Dadda Tree 倾向于使用刚好够用的 FA/HA，而不是像 Wallace Tree 那样尽量压。

常用直觉规则：

```text
if height is much higher than target:
    use FA
if height is only target + 1:
    use HA
```

更严格地说，设计时要从低列到高列考虑，因为低列产生的 carry 会增加高列在下一 stage 的高度。

### 6.4 9 bit multiplier 的 Dadda 压缩计划

对 LAB2 的 9 bit Modified Baugh-Wooley multiplier，可以从下面的初始高度出发：

```text
column: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17
height: 1 2 3 4 5 6 7 8 9 9  7  6  5  4  3  2  1  1
```

一个可行的 Dadda target 计划是：

```text
Stage 1: reduce to height <= 6
Stage 2: reduce to height <= 4
Stage 3: reduce to height <= 3
Stage 4: reduce to height <= 2
Final : 18 bit CPA
```

下表给出一种可行的压缩数量安排。这里的 `FA=2, HA=1` 表示在该列放 2 个 FA 和 1 个 HA。具体 wire 名称可以由你在 RTL 中自行编号。

#### Stage 1: target height 6

| column | FA count | HA count |
| ------ | -------- | -------- |
| 6 | 0 | 1 |
| 7 | 1 | 1 |
| 8 | 2 | 1 |
| 9 | 3 | 0 |
| 10 | 2 | 0 |
| 11 | 1 | 0 |

该 stage 后的高度可以达到：

```text
1 2 3 4 5 6 6 6 6 6 6 6 6 4 3 2 1 1
```

#### Stage 2: target height 4

| column | FA count | HA count |
| ------ | -------- | -------- |
| 4 | 0 | 1 |
| 5 | 1 | 1 |
| 6 | 2 | 0 |
| 7 | 2 | 0 |
| 8 | 2 | 0 |
| 9 | 2 | 0 |
| 10 | 2 | 0 |
| 11 | 2 | 0 |
| 12 | 2 | 0 |
| 13 | 1 | 0 |

该 stage 后的高度可以达到：

```text
1 2 3 4 4 4 4 4 4 4 4 4 4 4 4 2 1 1
```

#### Stage 3: target height 3

| column | FA count | HA count |
| ------ | -------- | -------- |
| 3 | 0 | 1 |
| 4 | 1 | 0 |
| 5 | 1 | 0 |
| 6 | 1 | 0 |
| 7 | 1 | 0 |
| 8 | 1 | 0 |
| 9 | 1 | 0 |
| 10 | 1 | 0 |
| 11 | 1 | 0 |
| 12 | 1 | 0 |
| 13 | 1 | 0 |
| 14 | 1 | 0 |

该 stage 后的高度可以达到：

```text
1 2 3 3 3 3 3 3 3 3 3 3 3 3 3 3 1 1
```

#### Stage 4: target height 2

| column | FA count | HA count |
| ------ | -------- | -------- |
| 2 | 0 | 1 |
| 3 | 1 | 0 |
| 4 | 1 | 0 |
| 5 | 1 | 0 |
| 6 | 1 | 0 |
| 7 | 1 | 0 |
| 8 | 1 | 0 |
| 9 | 1 | 0 |
| 10 | 1 | 0 |
| 11 | 1 | 0 |
| 12 | 1 | 0 |
| 13 | 1 | 0 |
| 14 | 1 | 0 |
| 15 | 1 | 0 |

该 stage 后的高度为：

```text
1 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 1
```

这时所有列的高度都不超过 2，可以进入最终 CPA。

### 6.5 Dadda Tree 的优缺点

优点：

- 通常比 Wallace Tree 使用更少 HA/FA。
- 延迟仍然接近 Wallace Tree。
- 适合手工规划，因为每级 target 很清楚。

缺点：

- 比 Wallace Tree 稍微难理解。
- 每一级要小心统计 carry 对高列的影响。
- RTL wire 命名和表格管理比较繁琐。

考试里可以这样记：

```text
Dadda: delayed reduction, fewer adders, similar number of levels.
```

## VII. Wallace Tree vs Dadda Tree

### 7.1 核心差异

| Feature | Wallace Tree | Dadda Tree |
| ------- | ------------ | ---------- |
| 基本单元 | HA/FA | HA/FA |
| 策略 | 每级尽量多压 | 每级只压到目标高度 |
| 目标 | 尽快减少高度 | 减少硬件数量 |
| 结构 | 更不规则 | 规划更清晰 |
| 速度 | 通常很快 | 接近 Wallace |
| 面积 | 可能较大 | 通常较小 |

### 7.2 对 LAB2 的建议

对于 9 bit multiplier：

- 如果你想先写通，Dadda Tree 更适合，因为 target height 清楚。
- 如果你想追求最短逻辑级数，可以尝试 Wallace Tree。
- 如果课设报告要解释优化思路，Dadda Tree 更容易写成表格。

你当前方案是：

```text
Modified Baugh-Wooley + Dadda tree + final 18 bit CPA
```

这是一个很适合课程实验和报告表达的选择。

## VIII. Connecting This To Modified Baugh-Wooley

### 8.1 signed multiplication 的问题

二补码 signed number 可以写成：

$$
A = -a_{n-1}2^{n-1} + \sum_{i=0}^{n-2} a_i2^i
$$

$$
B = -b_{n-1}2^{n-1} + \sum_{j=0}^{n-2} b_j2^j
$$

展开：

$$
\begin{aligned}
P
&= A B \\
&= \sum_{i=0}^{n-2}\sum_{j=0}^{n-2} a_i b_j 2^{i+j} \\
&\quad - \sum_{i=0}^{n-2} a_i b_{n-1}2^{i+n-1} \\
&\quad - \sum_{j=0}^{n-2} a_{n-1} b_j2^{j+n-1} \\
&\quad + a_{n-1}b_{n-1}2^{2n-2}
\end{aligned}
$$

中间两项是负的，这就是 signed multiplier 比 unsigned multiplier 麻烦的地方。

### 8.2 Baugh-Wooley 的基本做法

Baugh-Wooley 的目标是把负的 partial product 转换成正的 bit matrix 加常数补偿。

对 sign-related partial products 做取反：

$$
a_i b_{n-1} \rightarrow \overline{a_i b_{n-1}}
$$

$$
a_{n-1} b_j \rightarrow \overline{a_{n-1} b_j}
$$

然后加入 correction bits，使整体数值保持不变。

对 n bit multiplier，Modified Baugh-Wooley 常见修正为：

$$
2^{2n-1} + 2^n
$$

对本实验 n=9：

$$
2^{17} + 2^9
$$

也就是：

```text
add constant 1 at column 17
add constant 1 at column 9
```

### 8.3 对你的 multiplier.v 的实现提醒

如果采用 Modified Baugh-Wooley，sign-related partial products 通常应该是 complemented dots：

```text
pp[i][8] = ~(a[i] & b[8]) for i = 0..7
pp[8][j] = ~(a[8] & b[j]) for j = 0..7
pp[8][8] =  (a[8] & b[8])
```

并且需要把 correction bits 放入 column 9 和 column 17。

之后的 Dadda/Wallace tree 不需要知道这些 dots 的语义。它只负责保持数值等价地压缩 dots：

```text
same column dot -> same weight
FA sum -> same column
FA carry -> next column
HA sum -> same column
HA carry -> next column
```

## IX. How To Write The RTL Compression Network

### 9.1 推荐的结构化写法

手写压缩树时，建议按 stage 和 column 命名：

```text
s1_c8_0   stage 1, column 8, sum dot 0
c1_c9_0   stage 1, generated carry into column 9, carry dot 0
s2_c8_0   stage 2, column 8, sum dot 0
...
```

不要只用 `wire tmp1, tmp2, tmp3`，后面一定会迷路。

### 9.2 每个 FA/HA 都要检查权重

如果在 column k 放 FA：

```text
fa_sum(x, y, z)   -> column k
fa_carry(x, y, z) -> column k+1
```

如果在 column k 放 HA：

```text
ha_sum(x, y)      -> column k
ha_carry(x, y)    -> column k+1
```

这是压缩树最重要的 invariant。只要这个 invariant 不破，整个树的数值就是对的。

### 9.3 最终两行的构造

当压缩到 height <= 2 后，把每一列的 dots 填入两行：

```text
row0[k] = column k first remaining dot
row1[k] = column k second remaining dot, or 0
```

然后使用 18 bit RCA：

```text
{carry_out, out[17:0]} = row0 + row1
```

在手写门级时，应该用 FA 串出最终 RCA，而不是直接写 `+`。最终超出 bit 17 的 carry 可以丢弃，因为 9 bit signed product 正好用 18 bit 二补码表示。

### 9.4 推荐实现顺序

建议按下面顺序做，不要一次写完全部：

1. 先确认 Baugh-Wooley partial product 和 correction bits。
2. 写 HA/FA function 或 module。
3. 按 Dadda Stage 1 写 wire，并用小 testbench 验证 stage 后 column height。
4. 写 Stage 2, Stage 3, Stage 4。
5. 构造 `row0` 和 `row1`。
6. 写最终 18 bit RCA。
7. 穷举 512 x 512 个输入，和 `a * b` golden 比较。
8. 替换进 image processor，跑 `make debug`。

### 9.5 常见错误

#### 错误 1: carry 放错列

FA/HA 的 carry 必须进入高一列：

```text
column k carry -> column k+1
```

如果留在原列，数值会变成错的。

#### 错误 2: 把 CSA 当成最终结果

CSA 输出的 `sum` 和 `carry` 不是最终结果。必须做：

$$
Result = Sum + (Carry \ll 1)
$$

在 dot matrix 表达里，carry 已经被放到高一列，所以最后是：

$$
Result = Row0 + Row1
$$

#### 错误 3: Baugh-Wooley sign dots 没取反

signed multiplier 的 sign-related partial products 不能直接照 unsigned multiplier 写。Modified Baugh-Wooley 的核心就是：

```text
invert sign-related dots
add correction constants
```

#### 错误 4: 在压缩树中间使用长 CPA

压缩树中间应该用 HA/FA 的 CSA-style reduction。中间使用完整 CPA 会传播 carry，导致 critical path 增长。

#### 错误 5: 同一 stage 中串联多个 FA

压缩树的一个 stage 应该是一层并行 compressor。某个 FA 产生的 carry 通常作为下一 stage 的输入。如果你把这个 carry 立刻送入同一 stage 的另一个 FA，就会形成串联路径，使延迟变长。

## X. Exam-Oriented Summary

### 10.1 一句话总结

CPA:

```text
Propagates carry and produces the final binary sum.
```

RCA:

```text
The simplest CPA. Delay grows linearly with bit width.
```

CSA:

```text
Saves carry instead of propagating it. Converts 3 operands into 2 operands.
```

Wallace Tree:

```text
Greedily compresses partial products as early as possible.
```

Dadda Tree:

```text
Compresses only to scheduled target heights, usually using fewer adders.
```

### 10.2 关键公式

HA:

$$
s = x \oplus y,\quad c = xy
$$

FA:

$$
s = x \oplus y \oplus z
$$

$$
c = xy + yz + xz
$$

CSA:

$$
X + Y + Z = S + (C \ll 1)
$$

Dadda target:

$$
d_1 = 2,\quad d_{k+1} = \left\lfloor \frac{3}{2}d_k \right\rfloor
$$

9 bit Baugh-Wooley correction:

$$
2^{17} + 2^9
$$

### 10.3 面试和考试常见问法

Question:

```text
Why not use ripple-carry adders to add all partial products directly?
```

Answer:

```text
Because each RCA propagates carry across many bits, creating a long critical path.
CSA compression avoids long carry propagation until the final CPA.
```

Question:

```text
What is the difference between Wallace and Dadda?
```

Answer:

```text
Wallace compresses aggressively at each level.
Dadda delays compression according to target heights and usually uses fewer adders.
```

Question:

```text
Why does a CSA output two rows instead of one result?
```

Answer:

```text
Because CSA saves carries instead of propagating them.
The numerical value is represented as Sum + shifted Carry.
```

Question:

```text
Where is the CPA used in a tree multiplier?
```

Answer:

```text
Only at the final stage, after the partial product matrix has been reduced to two rows.
```

## XI. Suggested Report Description

如果你在实验报告中介绍这个 multiplier，可以这样写：

```text
The signed 9 bit multiplier is implemented using a Modified Baugh-Wooley partial
product generator followed by a Dadda carry-save reduction tree. The Baugh-Wooley
scheme converts the two's-complement signed partial products into a positive dot
matrix with correction bits at columns 9 and 17. The Dadda tree then reduces the
column heights according to the target sequence 6, 4, 3, and 2 using only half
adders and full adders. After the matrix is reduced to two rows, an 18 bit
ripple-carry CPA generates the final two's-complement product.
```

这段话涵盖了：

- signed partial product generation
- correction bits
- CSA-style reduction
- Dadda target sequence
- final CPA

也正好对应课程 Chapter4 中的 signed multiplier, Baugh-Wooley, Wallace/Dadda tree 和 CPA/CSA。
