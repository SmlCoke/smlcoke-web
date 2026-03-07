


这是一个非常核心且经典的证明，它不仅是数字通信理论的基石，也是历年考试和面试的高频考点。这个证明的物理意义是：**不论你发送什么形状的波形，只要接收端使用对应的“匹配滤波器”，你就能榨干这个波形里的每一滴能量，获得理论上能达到的最大信噪比。**

根据课件第37-41页的内容，我们可以将这个证明拆解为**5个清晰的步骤**。

---

### 证明过程：匹配滤波器输出最大信噪比

#### 第一步：建立接收端信号模型
假设在持续时间 $0 \le t \le T$ 内，发送的基带信号为 $s(t)$。
信号在信道中受到加性高斯白噪声（AWGN）$n(t)$ 的干扰，且噪声的双边功率谱密度为 $G_n(f) = \frac{N_0}{2}$。

接收端收到的信号为：
$$ r(t) = s(t) + n(t) $$

假设接收滤波器的冲激响应为 $h(t)$，接收信号通过该滤波器后，输出信号 $y(t)$ 可以表示为有用信号与噪声的卷积之和：
$$ y(t) = \int_0^t r(\tau)h(t-\tau)d\tau = \underbrace{\int_0^t s(\tau)h(t-\tau)d\tau}_{y_s(t)} + \underbrace{\int_0^t n(\tau)h(t-\tau)d\tau}_{y_n(t)} $$

#### 第二步：写出 $t=T$ 抽样时刻的信噪比表达式
在 $t=T$ 时刻进行抽样，输出的有用信号的瞬时值为：
$$ y_s(T) = \int_0^T s(\tau)h(T-\tau)d\tau $$

输出的噪声平均功率（方差）为噪声平方的数学期望：
$$ E[y_n^2(T)] = E\left[ \int_0^T n(\tau)h(T-\tau)d\tau \cdot \int_0^T n(t)h(T-t)dt \right] $$
把数学期望符号移到积分号内部：
$$ E[y_n^2(T)] = \int_0^T \int_0^T E[n(\tau)n(t)] h(T-\tau)h(T-t) dt d\tau $$

因为 $n(t)$ 是白噪声，它的自相关函数 $E[n(\tau)n(t)] = \frac{N_0}{2}\delta(\tau-t)$。代入上式，利用冲激函数 $\delta$ 的筛选性质（令 $\tau = t$）：
$$ E[y_n^2(T)] = \frac{N_0}{2} \int_0^T \int_0^T \delta(t-\tau) h(T-\tau) h(T-t) dt d\tau = \frac{N_0}{2} \int_0^T h^2(T-t) dt $$

所以，在 $t=T$ 时刻，输出信噪比 $\left(\frac{S}{N}\right)_0$ 可表示为：
$$ \left(\frac{S}{N}\right)_0 = \frac{y_s^2(T)}{E[y_n^2(T)]} = \frac{\left[ \int_0^T s(\tau)h(T-\tau)d\tau \right]^2}{\frac{N_0}{2} \int_0^T h^2(T-\tau) d\tau} $$

#### 第三步：使用柯西-施瓦茨不等式求最大值（核心）
根据柯西-施瓦茨（Cauchy-Schwartz）不等式，对于任意两个平方可积函数 $g_1(\tau)$ 和 $g_2(\tau)$，必有：
$$ \left| \int_0^T g_1(\tau)g_2(\tau)d\tau \right|^2 \le \int_0^T g_1^2(\tau)d\tau \cdot \int_0^T g_2^2(\tau)d\tau $$

我们令：
$g_1(\tau) = s(\tau)$
$g_2(\tau) = h(T-\tau)$

将它们代入我们刚才求出的信噪比分子的括号中：
$$ \left[ \int_0^T s(\tau)h(T-\tau)d\tau \right]^2 \le \int_0^T s^2(\tau)d\tau \cdot \int_0^T h^2(T-\tau)d\tau $$

#### 第四步：得出最大信噪比结论
把不等式的右边代入到信噪比的公式中，会发现含有 $h$ 的积分项恰好被上下约掉了：

$$ \left(\frac{S}{N}\right)_0 \le \frac{\int_0^T s^2(\tau)d\tau \cdot \int_0^T h^2(T-\tau)d\tau}{\frac{N_0}{2} \int_0^T h^2(T-\tau)d\tau} $$

$$ \left(\frac{S}{N}\right)_0 \le \frac{\int_0^T s^2(\tau)d\tau}{N_0 / 2} $$

在信号与系统中，信号幅度的平方在时间上的积分 $\int_0^T s^2(\tau)d\tau$ 正好等于**信号的总能量 $E$**。

因此：
$$ \left(\frac{S}{N}\right)_0 \le \frac{E}{N_0 / 2} = \frac{2E}{N_0} $$
**（这就证明了：输出信噪比的上限只由信号能量 $E$ 和噪声功率谱密度 $N_0$ 决定，与其波形长什么样子毫无关系！）**

#### 第五步：得出匹配滤波器的冲激响应条件
什么时候不等式能取到“等号”（也就是达到最大信噪比）呢？

柯西-施瓦茨不等式取等号的条件是：两个函数成比例。
即：$g_2(\tau) = c \cdot g_1(\tau)$ （$c$ 为任意常数，通常令 $c=1$ 或 $k$）

把刚才设的函数代回来：
$$ h(T-\tau) = c \cdot s(\tau) $$
令 $t = T-\tau$（即 $\tau = T-t$），可以得到最佳滤波器的冲激响应表达式：
$$ h(t) = c \cdot s(T-t) \quad (0 \le t \le T) $$

**结论：** 
当接收滤波器的冲激响应 $h(t)$ 是输入信号 $s(t)$ 的**时间反转并延迟 $T$** 时（这正是**匹配滤波器**的定义），不等式取等号。此时，在 $t=T$ 抽样时刻，可以获得**最大输出信噪比 $\frac{2E}{N_0}$**。

**证明完毕。**