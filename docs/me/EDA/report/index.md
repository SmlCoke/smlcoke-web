# Report 阅读指南

## I. 时序报告 (Timing Report)

### 1.1 核心 Metrics

#### (1) Setup Time (建立时间, $t_{su}$)

1. **物理含义**：时钟有效沿到来**之前**，数据必须保持稳定的最短时间。
2. **报告体现**：对应“最大延迟（Max Delay）”检查。限制了逻辑的最长路径。

#### (2) Hold Time (保持时间, $t_{h}$)
1. **物理含义**：时钟有效沿到来**之后**，数据必须继续保持稳定的最短时间。
2. **报告体现**：对应“最小延迟（Min Delay）”检查。限制了逻辑的最短路径。

#### (3) Arrivals Time (AT, 到达时间)

1. **物理含义**：数据信号从**时钟边沿触发**（Launch FF）出发，经过各种门延迟和线延迟，**实际到达终点（Capture FF）D 端**的时间。
2. **公式解释**：

$$\text{Arrival Time} = \text{CLK→Q Time} + \sum \text{Gate Delays} + \sum \text{Wire Delays}$$

#### (4) Required Time (RT, 需求时间)

1. **物理含义**：为了**满足 Setup 或 Hold 条件**，数据**必须到达终点的时间界限**。它是工具根据时钟周期、时钟网络延迟和 $t_{su}$ 或 $t_{h}$ 反推出来的标准线。
2. **公式解释**：

$$\begin{aligned}
\text{Required Time(Setup)} &= \text{目标寄存器时钟到达时间} - t_{\text{setup}} \\
\text{Required Time(Hold)} &= \text{目标寄存器时钟到达时间} + t_{\text{hold}}
\end{aligned}$$

#### (5) Slack (时序裕量)

1. **物理含义**：实际到达时间与需求时间之间的“安全距离”。
2. **计算公式**：

$$\begin{aligned}
\text{Setup Slack} &= \text{Required Time} - \text{Arrival Time} \\
\text{Hold Slack} &= \text{Arrival Time} - \text{Required Time}
\end{aligned}$$

**正确范围**：**必须 $\ge 0$**。如果是正数，说明满足时序且有盈余（Met）；如果是负数，说明**违例（Violated）**，芯片极大概率失效。

#### (6) WNS (Worst Negative Slack, 最差负裕量)

1. **物理含义**：整个设计中，所有路径里**最差**的那条路径的 Slack 值。
2. **正确范围**：**目标是 $\ge 0$**。如果 WNS 是 -0.5ns，说明你芯片的最高频率达不到预期，需要降频或优化 RTL。
#### (7) TNS (Total Negative Slack, 总负裕量)

1. **物理含义**：设计中所有违例路径（Slack < 0）的 Slack 负值之和。
2. **代表什么**：WNS 代表你病得**最重**的地方，TNS 代表你**全身病的范围**。如果 WNS 只有 -0.1ns，但 TNS 是 -100ns，说明你的设计有成千上万条路径差一点点达标（通常是全局时钟约束过紧）。

#### (8) Skew (时钟偏斜)

1. **物理含义**：同一个时钟源发出的时钟信号，到达两个不同触发器时钟端的时间差。
2. **报告体现**：后端布线（CTS）后非常关注，合理的 Skew 可以用来“借时间（Useful Skew）”，但恶性 Skew 会导致严重的 Hold 违例。
#### (9) **Uncertainty (时钟不确定性)**

1. **物理含义**：工具为了模拟真实世界中时钟的抖动（Jitter）、偏斜（Skew）以及给后期布线预留的余量，而人为加上的“惩罚值”。
2. **正确范围**：综合（DC）阶段通常设得较大（如周期的 5%-10%），后端（ICC/Innovus）阶段随着真实时钟树建好会逐渐减小。