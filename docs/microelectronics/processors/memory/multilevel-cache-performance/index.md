# 多级缓存结构的 Miss Penalty 和 CPI 计算方法

## I. 核心定义

### 1.1 $\text{CPI}$

$\text{CPI}$: Cycles per Instruction，每条指令平均需要多少个时钟周期完成。理想情况下 $\text{CPI} = 1$，但实际中由于各种因素（如 Cache Miss）会增加 CPI。

### 1.2 Miss Rate

$\text{Miss Rate}$: Cache Miss 的比例，即访问 Cache 时发生 Miss 的次数占总访问次数的百分比。通常分为指令 Cache Miss Rate 和数据 Cache Miss Rate。

此外，在描述上，还有局部未命中率（Local Miss Rate）和全局未命中率（Global Miss Rate）的概念：

1.  **局部未命中率 (Local Miss Rate)**：
    *   **定义**：$\frac{\text{该级 Cache 的未命中次数}}{\text{到达该级 Cache 的访问总次数}}$。
    *   **计算公式**：$\text{L1 Miss Penalty} = \text{L2 Hit Time} + \text{L2 Local Miss Rate} \times \text{Memory Penalty}$。
2.  **全局未命中率 (Global Miss Rate)**：
    *   **定义**：$\frac{\text{该级 Cache 的未命中次数}}{\text{CPU 发出的总访存次数}}$。
    *   $\text{L2 Global Miss Rate} = \text{L1 Miss Rate} \times \text{L2 Local Miss Rate}$

### 1.3 $\text{Memory Stalls}$

$\text{Memory Stalls}$: **每条指令平均因为内存访问延迟而停顿的周期数**。对于多级 Cache 结构，$\text{Memory Stalls}$ 包含了每一级 Cache 的 Miss Penalty 以及主存访问的延迟。

如果是独立的 I-Cache 和 D-Cache，$\text{Memory Stalls}$ 可以拆解为：

$$\text{Memory Stalls} = \text{I-Cache Stalls} + \text{D-Cache Stalls}$$

### 1.4 $\text{Miss Penalty}$

$\text{Miss Penalty}$: 当发生 Cache Miss 时，CPU 需要等待的额外周期数。对于多级 Cache 结构，$\text{Miss Penalty}$ 包含了**访问下一级 Cache 的时间（$\text{Hit time}$）**以及**访问下一级 Cache miss 时的 Miss Penalty（$\text{Miss Rate}\times \text{Miss Penalty}$）**。即：

$$\text{Miss Penalty} = \text{Hit Time} + \text{Miss Rate} \times \text{Miss Penalty}$$

比如说，对于两级 Cache:

$$\text{L1 Miss Penalty} = \text{L2 Hit Time} + \text{L2 Miss Rate} \times \text{L2 Miss Penalty}$$

$$\text{L2 Miss Penalty} = \text{Memory Access Cycles}$$

### 1.5 $\text{AMAT}$

$\text{AMAT}$: Average Memory Access Time，**平均内存访问时间**。对于多级 Cache 结构，$\text{AMAT}$ 可以通过以下公式计算：

$$\text{AMAT} = \text{Hit Time} + \text{Miss Rate} \times \text{Miss Penalty}$$

例如，

$$\text{AMAT} = \text{L1 Hit Time} + \text{L1 Miss Rate} \times \text{L1 Miss Penalty}$$

$\text{Memory Stalls}$ 就可以计算为：

$$\text{Memory Stalls} = \text{AMAT} - \text{L1 Hit Time}$$

### 1.6 $\text{CPI}_{\text{实际}}$

考虑一个 I-Cache 和 D-Cache 独立的处理器，实际 CPI 可以通过以下公式计算：

$$\begin{aligned}
\text{CPI}_{\text{实际}} &= \text{CPI}_{\text{理想}} + \text{Memory Stalls} \\
& = \text{CPI}_{\text{理想}} + \text{I-Cache Stalls} + \text{D-Cache Stalls} \\
& = \text{CPI}_{\text{理想}} + (\text{AMAT} - \text{L1 Hit Time})_\text{I} + \text{Memory Access Rate}\times (\text{AMAT} - \text{L1 Hit Time})_\text{D} \\
& = \text{CPI}_{\text{理想}} + \text{L1-I Miss Rate} \times \text{L1-I Miss Penalty} + \text{Memory Access Rate}\times \text{L1-D Miss Rate} \times \text{L1-D Miss Penalty} \\
\end{aligned}$$

其中，$\text{Memory Access Rate}$ 是指数据访存指令占总指令的比例。

## II. 多级 Cache 的性能计算模板

### Step 1. 总 CPI 模型

$$\begin{aligned}
\text{CPI}_{\text{实际}} &= \text{CPI}_{\text{理想}} + \text{Memory Stalls} \\
& = \text{CPI}_{\text{理想}} + \text{I-Cache Stalls} + \text{D-Cache Stalls} \\
& = \text{CPI}_{\text{理想}} + (\text{AMAT} - \text{L1 Hit Time})_\text{I} + \text{Memory Access Rate}\times (\text{AMAT} - \text{L1 Hit Time})_\text{D} \\
& = \text{CPI}_{\text{理想}} + \text{L1-I Miss Rate} \times \text{L1-I Miss Penalty} + \text{Memory Access Rate}\times \text{L1-D Miss Rate} \times \text{L1-D Miss Penalty} \\
\end{aligned}$$

### Step 2. 展开多级 Cache 的 Miss Penalty

以 L1-L2-DRAM 为例

#### (1) Memory Penalty

$\text{Memory Penalty} = \text{Memory Access Cycles}$

#### (2) L2 Miss Penalty

$\text{L2 Miss Penalty} = \text{Memory Penalty}$

#### (3) L1 Miss Penalty

$$\begin{aligned}
\text{L1 Miss Penalty} &= \text{L2 Hit Time} + \text{L2 Miss Rate} \times \text{L2 Miss Penalty}\\
&= \text{L2 Hit Time} + \text{L2 Miss Rate} \times \text{Memory Penalty}\\
&= \text{L2 Hit Time} + \text{L2 Miss Rate} \times \text{Memory Access Cycles}
\end{aligned}$$

#### (4) AMAT

$\text{AMAT} = \text{L1 Hit Time} + \text{L1 Miss Rate} \times \text{L1 Miss Penalty}$

#### Step 3. 考虑 I-Cache 和 D-Cache 的独立访问

$\text{I-Cache Stalls} = (\text{AMAT} - \text{L1 Hit Time})_\text{I}= \text{L1-I Miss Rate} \times \text{L1-I Miss Penalty}$

$\text{D-Cache Stalls} = \text{Memory Access Rate}\times (\text{AMAT} - \text{L1 Hit Time})_\text{D} = \text{Memory Access Rate}\times \text{L1-D Miss Rate} \times \text{L1-D Miss Penalty}$

#### Step 4. 最终计算 $\text{CPI}_{\text{实际}}$

$\text{CPI}_{\text{实际}} = \text{CPI}_{\text{理想}} + \text{I-Cache Stalls} + \text{D-Cache Stalls}$