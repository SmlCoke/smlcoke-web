# 连续时间傅里叶变换（2）
## 一. 导言
本文包含连续时间傅里叶变换的性质以及连续时间傅里叶变换在LTI的频域分析中的应用。


## 二. 连续时间傅里叶变换的性质
我们记：

$$f(t) \xleftrightarrow{\mathcal{F}} F(j\omega)$$
表示$f(t)$与$F(j\omega)$为一组傅里叶变换对，即满足公式(2.8)与(2.9)。在以下性质的讨论中，我们认为：

$x(t) \xleftrightarrow{\mathcal{F}} X(j\omega),\quad y(t) \xleftrightarrow{\mathcal{F}} Y(j\omega)$

### 2.1  线性性
在[连续时间傅里叶变换（1）](CFT1.md)一节我们多次运用到傅里叶变换的线性性质来推导几个常见非周期信号的傅里叶也变换，这里我们正式给出该性质。
**线性性：**

$$ax(t)+by(t)\xleftrightarrow{\mathcal{F}} aX(j\omega)+bY(j\omega)\tag{2.1}$$

这个性质的证明很简单，但介于其**重要性**（这也是我们将其放在第一条的原因），我们依旧给出证明过程：
>证明：
>$\begin{aligned}
\mathcal{F}\{ax(t)+by(t)\}={} &\int_{-\infty}^{+\infty}[ax(t)+by(t)]e^{-j\omega t}\, \text{d}t\\
= {} & \int_{-\infty}^{+\infty}ax(t)e^{-j\omega t}\, dt + \int_{-\infty}^{+\infty}by(t)e^{-j\omega t}\, dt\\
={} & aX(j\omega)+bY(j\omega)
\end{aligned}$

### 2.2 时移与频移
**时移性：**

$$x(t-t_0)\xleftrightarrow{\mathcal{F}} e^{-j\omega t_0}X(j\omega)\tag{2.2}$$

> 证明：
> $\begin{aligned}
\mathcal{F}\{x(t-t_0)\}={} & \int_{-\infty}^{+\infty}x(t-t0)e^{-j\omega t}\, dt \\
= {} &   e^{-j\omega t_0}\int_{-\infty}^{+\infty}x(t-t0)e^{-j\omega (t-t0)}\, d(t-t_0) \\
={} & e^{-j\omega t_0}\int_{-\infty}^{+\infty}x(t)e^{-j\omega t}\, dt \\
= {} & e^{-j\omega t_0}X(j\omega)
\end{aligned}$

**频移性：**

$$e^{-j\omega_0 t}x(t)\xleftrightarrow{\mathcal{F}} X(j(\omega-\omega_0))\tag{2.3}$$

> 证明：
> $\begin{aligned}
\mathcal{F}\{e^{j\omega_0 tx(t)}\}={} & \int_{-\infty}^{+\infty}e^{j\omega_0 t}x(t)e^{-j\omega t}\, dt \\
= {} &   \int_{-\infty}^{+\infty}x(t)e^{-j(\omega-\omega_0)t }\, dt \\
= {} & X(j(\omega-\omega_0))
\end{aligned}$

我们注意观察式(4.2)和(4.3)，可以发现两者**结构极为相似**，**时域的时移对应着频域乘以一个指数项，频域的频移对应着时域乘以一个指数项**！似乎有种对称性藏在其中，而且我们可以告诉读者的是，这种对称性并不是偶然的。我们借此断言，一**个函数及其傅里叶变换中，似乎会藏着点什么更有趣的性质，来描述这种对称性**。这种性质，就是我们之后会提到的“**对称互易性**”

### 2.3 共轭与共轭对称性

$$x^{*}(t)\xleftrightarrow{\mathcal{F}} X^{*}(-j\omega)\tag{2.4}$$

>证明：
>$X(j\omega) = \int_{-\infty}^{+\infty}x(t)e^{-j\omega t}\,dt$
>$X(-j\omega)=\int_{-\infty}^{+\infty}x(t)e^{j\omega t}\,dt$
>$X^{*}(-j\omega)=[\int_{-\infty}^{+\infty}x(t)e^{j\omega t}\,dt]^{*} = \int_{-\infty}^{+\infty}x^{*}(t)e^{-j\omega t} \,dt = \mathcal{F}\{x^{*}(t)\}$

上述性质称为傅里叶变换的**共轭性质**。
对于实信号$x(t)$，满足$x^{*}(t) = x(t)$，不难想到，其傅里叶变换之间也应该满足点什么关系，这个关系就是**实信号傅里叶变换的共轭对称性**：
#### 推论1. 当$x(t)$为实函数时，$X(jω)$有共轭对称性：

$$X(j\omega) = X^{*}(-j\omega) \rightarrow X^{*}(j\omega) = X(-j\omega)$$

#### 推论2. 更进一步有，对于实信号：

$$\text{Re}\{X(j\omega)\} = \text{Re}\{X(-j\omega)\}, \quad \text{Im}\{X(j\omega)\} = \text{Im}\{X(-j\omega)\}$$

即对于实函数，其傅里叶变换的：
① 实部是关于$ω$的偶函数
② 虚部是关于$ω$的奇函数
或者：

$$[|X(j\omega)|e^{j\phi(X(j\omega))}]^{*}=|X(j\omega)|e^{j\phi[X(-j\omega)]}$$

即对于实函数，其傅里叶变换的：
① 模长$|X(j\omega)|$是关于ω的偶函数
② 幅角$\phi[X(j\omega)]$是关于ω的奇函数
#### 推论3. 更进一步，
**(1) 考虑x(t)为实偶函数：** 
则：
**实：** $x(t) = x^{*}(t) \rightarrow X(j\omega) = X^{*}(-j\omega)$
**偶：**$x(t)=x(-t)\rightarrow X(j\omega) = X(-j\omega)$
因此有：

$$X(-j\omega)=X^{*}(-j\omega)$$

也就是说：

$$X(j\omega)=X^{*}(j\omega)\tag{2.5}$$

即：**若一个信号为实偶信号，则其傅里叶变换为实偶函数（虚部为0）。**

**(2) 考虑x(t)为实奇函数：** 
则：
**实：** $x(t) = x^{*}(t) \rightarrow X(j\omega) = X^{*}(-j\omega)$
**偶：** $x(t)=-x(-t)\rightarrow X(j\omega) = -X(-j\omega)$
因此有：

$$-X(-j\omega)=X^{*}(-j\omega)$$

也就是说：

$$-X(j\omega)=X^{*}(j\omega)\tag{2.6}$$

即：**若一个信号为实偶信号，则其傅里叶变换为纯虚奇函数（实部为0）。**

#### 推论4. 再进一步
我们已知任意实函数$x(t)$均可以表示为一个偶函数$x_e(t)=\frac{1}{2}[x(t)+x(-t)]$与一个奇函数$x_o(t)=\frac{1}{2}[x(t)-x(-t)]$之和，那么根据傅里叶变换的线性性质：

$$X(j\omega)=\mathcal{F}\{x(t)\}=\mathcal{F}\{x_e(t)\}+\mathcal{F}\{x_o(t)\}$$

那么由 **推论3.** 可知：
$\mathcal{F}\{x_e(t)\}$为实偶函数
$\mathcal{F}\{x_o(t)\}$为纯虚奇函数
也就是说：

$$\mathcal{F}\{x_e(t)\} = \text{Re}\{X(j\omega)\},\quad \mathcal{F}\{x_o(t)\} = \text{Im}\{X(j\omega)\}$$

==例题1.== 已知$\mathcal{F}\{e^{-\alpha t}u(t)\} =\frac{1}{\alpha+j\omega}, \alpha > 0$ ，求$\mathcal{F}\{e^{-\alpha |t|}u(t)\}$
> 请读者自行思考解答
> 答案：$\frac{2\alpha}{\alpha^2+\omega^2}$

### 2.4 时域微分

$$\frac{\text{d}x(t)}{\text{d}t}\xleftrightarrow{\mathcal{F}}j\omega X(j\omega)\tag{2.7}$$

> 证明
> $\begin{aligned}
x(t)=\int_{-\infty}^{+\infty}X(j\omega)e^{j\omega t}\,dt \rightarrow
\frac{\text{d}x(t)}{\text{d}t}=\int_{-\infty}^{+\infty}j\omega X(j\omega)e^{j\omega t}\,dt \rightarrow \mathcal{F}\{\frac{\text{d}x(t)}{\text{d}t}\}=j\omega X(j\omega)
\end{aligned}$

### 2.5 时域积分

$$\int_{-\infty}^{t}x(\tau)d\tau\xleftrightarrow{\mathcal{F}}\frac{1}{j\omega}X(j\omega)+\pi X(0)\delta(\omega)\tag{2.8}$$

>证明
>根据单位阶跃响应的卷积特性：
>$x(t)*u(t)=\int_{-\infty}^{t}x(\tau)\,d\tau$
>因此，根据**时域卷积定理（证明见下）**：
>$\begin{aligned}
\mathcal{F}\{\int_{-\infty}^{t}x(\tau)\,d\tau\}={} & \mathcal{F}\{x(t)*u(t)\} \\
= {} & X(j\omega)U(j\omega)\\
={} &  X(j\omega) [\frac{1}{j\omega}+\pi\delta(\omega)]\\
= {} & \frac{1}{j\omega}X(j\omega)+\pi X(j\omega)\delta(\omega)\\
= {} & \frac{1}{j\omega}X(j\omega)+\pi X(0)\delta(\omega) 
\end{aligned}$

### 2.6 时域与频域的尺度变换

$$x(at) \xleftrightarrow{\mathcal{F}} \frac{1}{|a|}X(j\frac{\omega}{a})\tag{2.9}$$

>证明
>$x(t)=\int_{-\infty}^{+\infty}X(j\omega)e^{j\omega t}\,dt$
>$\begin{aligned}
\mathcal{F}\{x(at)\}= {} & \int_{-\infty}^{+\infty}x(at)e^{-j\omega t}\, dt \\
= {} & \left\{
\begin{array}{ll}
\int_{-\infty}^{+\infty} x(t')\text{exp}(-j\omega t'/a)\, d(t'/a) & \text{if } a > 0 \\
\int_{+\infty}^{-\infty} x(t')\text{exp}(-j\omega t'/a)\, d(t'/a) & \text{if } a < 0
\end{array}
\right. \\
={} & \left\{
\begin{array}{ll}
\frac{1}{a}X(j\frac{\omega}{a})& \text{if } a > 0 \\
-\frac{1}{a}X(j\frac{\omega}{a})& \text{if } a < 0
\end{array}
\right. \\
= {} & \frac{1}{|a|}X(j\frac{\omega}{a})
\end{aligned}$
> **最典型应用**： $x(-t) \xleftrightarrow{\mathcal{F}}X(-j\omega)$

### 2.7 对称互易性
前面我们提到，式(4.2)和(4.3)两者**结构极为相似**，**时域的时移对应着频域乘以一个指数项，频域的频移对应着时域乘以一个指数项**！似乎有种对称性藏在其中，这种性质，就是“**对称互易性**”。
这里用一个例子来说明这种奇妙的对称性：
==例题2.== 求信号$x(t) = \frac{2}{1+t^2}$的傅里叶变换。
> 由例题1. 我们知道，$\mathcal{F}\{e^{-|t|}\}=\frac{2}{1+\omega^2}$，即：
>  $e^{-|t|}=\frac{1}{2\pi}\int_{-\infty}^{+\infty}\frac{1}{1+\omega^2}e^{j\omega t}\, d\omega$
>  $2\pi e^{-|t|}=\int_{-\infty}^{+\infty}\frac{2}{1+\omega^2}e^{j\omega t}\, d\omega$
>  等式两边同时交换$t, \omega$：
>  $2\pi e^{-|\omega|}=\int_{-\infty}^{+\infty}\frac{2}{1+t^2}e^{jt\omega}\, dt=\int_{+\infty}^{-\infty}\frac{2}{1+t^2}e^{-j\omega t}\, d(-t)=\int_{-\infty}^{+\infty}\frac{2}{1+t^2}e^{-j\omega t}\, dt=\mathcal{F}\{\frac{2}{1+t^2}\}$
>  即：
>  $\mathcal{F}\{x(t)\}=2\pi e^{-|\omega|}$

可见，如果信号$x(t)$的傅里叶变换是$X(j\omega)$，那么信号$X(t)$的傅里叶变换的**函数结构必然与$x(t)$存在一定相似性**，这就是下面的**对称互易性定理**：

$$x(t)\xleftrightarrow{\mathcal{F}}X(j\omega)\rightarrow X(t)\xleftrightarrow{\mathcal{F}}2\pi x(-\omega)\tag{2.10}$$

> 证明
> $x(t)=\frac{1}{2\pi}\int_{-\infty}^{+\infty}X(j\omega)e^{j\omega t}\, d\omega \rightarrow$
> $2\pi x(-t)=\int_{-\infty}^{+\infty}X(j\omega)e^{-j\omega t}\, d\omega \rightarrow$
> $2\pi x(-\omega) = \int_{-\infty}^{+\infty}X(t)e^{-j\omega t}\,dt\rightarrow$
> $\mathcal{F}\{X(t)\}=2\pi x(-\omega)$

除了求解这种函数形式与$X(t)$相似的信号的傅里叶变换外，对偶性也能用来确定或联想到傅里叶变换的其他性质。具体而言，如果一个时间函数有某些特性，而**这些特性在其傅里叶变换中隐含着一些别的什么东西**，那么与频率函数有关的同一特性也会在时域中隐含着对偶的东西。例如：**频域微分**。

### 2.8 频域微分
对于连续时间信号$x(t)$的导数信号$\frac{\text{d}x(t)}{\text{d}t}$，我们知道其傅里叶变换是：$j\omega X(j\omega)$
那么我们不妨猜测，傅里叶变换$X(j\omega)$的导数$\frac{\text{d}}{\text{d}\omega}X(j\omega)$对应的时域信号，很可能具有这种形式——$jtx(t)$。
事实上，我们有**傅里叶变换的频域微分性质**：

$$-jtx(t)\xleftrightarrow{\mathcal{F}}\frac{\text{d}}{\text{d}\omega}X(j\omega)\tag{2.11}$$

> 证明
> 由$X(j\omega)=\int_{-\infty}^{+\infty}x(t)e^{-j\omega t}\,dt$两边对$\omega$求导：
> $\frac{\text{d}}{\text{d}\omega}X(j\omega)=\int_{-\infty}^{+\infty}x(t)(-jt)e^{-j\omega t}\,dt=\int_{-\infty}^{+\infty}[-jtx(t)]e^{-j\omega t}\,dt$
> 进而：
> $-jtx(t)\xleftrightarrow{\mathcal{F}}\frac{\text{d}}{\text{d}\omega}X(j\omega)$

### 2.9 频域积分

$$-\frac{x(t)}{jt}+\pi x(0)\delta(t) \xleftrightarrow{\mathcal{F}}\int_{-\infty}^{\omega}X(j\omega')\,d\omega'\tag{2.12}$$

> 证明：
>  $\int_{-\infty}^{\omega}X(j\omega')\,d\omega'=X(j\omega)*u(j\omega)$
>  由**频域卷积定理（证明见下）**：$2\pi x(t)y(t)\xleftrightarrow{\mathcal{F}}X(j\omega)*Y(j\omega)$
>  因此：$X(j\omega)*u(j\omega)\xleftrightarrow{\mathcal{F}}2\pi x(t)\mathcal{F^{-1}}\{u(j\omega\})$
>  根据对称互易性：$\frac{1}{jt}+\pi \delta(t)\xleftrightarrow{\mathcal{F}}2\pi u(-j\omega)$
>  因此：$-\frac{1}{jt}+\pi \delta(-t)\xleftrightarrow{\mathcal{F}}2\pi u(j\omega)\rightarrow\frac{1}{2\pi}[-\frac{1}{jt}+\pi \delta(t)]\xleftrightarrow{\mathcal{F}} u(j\omega)$ 
>  因此：$X(j\omega)*u(j\omega)\xleftrightarrow{\mathcal{F}}-\frac{x(t)}{jt}+\pi x(0)\delta(t)$
>  即：$\int_{-\infty}^{\omega}X(j\omega')\,d\omega'\xleftrightarrow{\mathcal{F}}-\frac{x(t)}{jt}+\pi x(0)\delta(t)$

### 2.10 Parseval's定理
Parseval's定理的基本思想是：**一个信号在时域中的总能量等于其频域表示中的总能量**，其基本形式如下：

$$\int_{-\infty}^{+\infty}|x(t)|^2\,dt=\frac{1}{2\pi}\int_{-\infty}^{+\infty}|X(j\omega)|^2\,d\omega\tag{2.13}$$

> 证明：
>$\begin{aligned}
\int_{-\infty}^{+\infty}|x(t)|^2\,dt = {} & \int_{-\infty}^{+\infty}x^{*}(t)x(t)\,dt\\
={} & \int_{-\infty}^{+\infty}x(t)[\frac{1}{2\pi}\int_{-\infty}^{+\infty}X(j\omega)e^{j\omega t}\,d\omega]^{*}\,dt \\
={} & \int_{-\infty}^{+\infty}x(t)[\frac{1}{2\pi}\int_{-\infty}^{+\infty}X(j\omega)^{*}e^{-j\omega t}\,d\omega]\,dt \\
= {} & \frac{1}{2\pi}\int_{-\infty}^{+\infty}X(j\omega)^{*}[\int_{-\infty}^{+\infty}x(t)e^{-j\omega t}\,dt]\,d\omega  \text{（交换积分次序）} \\
= {} &\frac{1}{2\pi}\int_{-\infty}^{+\infty}X(j\omega)^{*}X(j\omega)\,d\omega\\
={} & \frac{1}{2\pi}\int_{-\infty}^{+\infty}|X(j\omega)|^2\,d\omega
\end{aligned}$

斯瓦尔定理允许我们在频域中计算时域信号的能量，尤其在频域处理更方便时非常有用。例如：
- 对一个带通信号，计算能量只需积分其频谱在通带部分的模平方；
- 在数字通信中，用来分析传输信号功率和能量分布。

### 2.11 时域卷积定理
频域卷积定理是傅里叶变换在LTI的频域分析中最重要的性质，其重要性体现在：对于一个单位冲激响应为$h(t)$的LTI，如果激励信号为$x(t)$，那么如果要求出响应$y(t)$，那么无需解微分方程，也无需作卷积$y(t)=x(t)*h(t)$，而能够采取一种在**某些情况下更简单**的方法，求出$y(t)$。例如：

我们知道如果LTI的单位冲激响应为$h(t)$，则其**频率响应**为：$H(j\omega)=\int_{-\infty}^{+\infty}h(t)e^{-j\omega t}\,dt$。
**(如果有读者不知道频率响应的定义和由来，请看以下解释：)**
> 对于一个单位冲激响应为$h(t)$的LTI，当激励为复指数信号$e^{j\omega_0 t}$是，其响应为：$y(t)=x(t)*h(t)=\int_{-\infty}^{+\infty}h(\tau)e^{j\omega_0 (t-\tau)}d\tau=[\int_{-\infty}^{+\infty}h(\tau)e^{-j\omega_0\tau}\,d\tau]e^{j\omega_0 t}$。
> 因此我们发现，**当线性时不变系统的激励为一个复指数信号时，其响应也是一个复指数信号**，其需要倍乘一个**与激励信号的频率有关的系数**：$\int_{-\infty}^{+\infty}h(\tau)e^{-j\omega_0 t}$。
> 如果我们记$H(j\omega)=\int_{-\infty}^{+\infty}h(\tau)e^{-j\omega t}$，那么这个系数就是：$H(j\omega_0)$，响应就是：$H(j\omega_0)e^{j\omega_0 t}$
> 因此我们就称这样一个重要系数$H(j\omega)$为该线性时不变系统的**频率响应**，它描述了响应中频率为$\omega$的信号成分与激励中频率为$\omega$的信号成分的关系：当输入频率为$\omega_0$时，响应成分的频率不变，幅度只需要倍乘$H(j\omega_0)$
  
我们假设有一个**非周期**激励信号$x(t)$，其傅里叶变换综合公式为：

$$x(t)=\frac{1}{2\pi}\int_{-\infty}^{+\infty}X(j\omega)e^{j\omega t}\,d\omega$$

我们写成求和形式：

$$x(t)=\lim_{\omega_0 \rightarrow 0}\sum_{k=-\infty}^{+\infty}\frac{1}{2\pi}X(jk\omega_0 )e^{jk\omega_0 t}\omega_0\tag{2.14}$$

可以发现，$x(t)$其实是一系列复指数信号的叠加，只不过这里的一系列是无穷多个。那么根据频率响应的定义以及线性时不变系统的线性性，我们可以直接写出**系统响应**：

$$y(t)=\lim_{\omega_0 \rightarrow 0}\sum_{k=-\infty}^{+\infty}H(jk\omega_0)\frac{1}{2\pi}X(jk\omega_0 )e^{jk\omega_0 t}\omega_0\tag{2.15}$$

我们将式(2.15)写回积分形式：

$$y(t)=\frac{1}{2\pi}\int_{-\infty}^{+\infty}H(j\omega)X(j\omega)e^{j\omega t}\,d\omega\tag{2.16}$$

对比$y(t)$的傅里叶变换综合公式：

$$y(t)=\frac{1}{2\pi}\int_{-\infty}^{+\infty}Y(j\omega)e^{j\omega t}\,d\omega$$

可以发现：

$$Y(j\omega)=X(j\omega)H(j\omega)\tag{2.17}$$

**因此，我们激动的发现，响应信号$y(t)$的傅里叶变换，就是激励信号的傅里叶变换与频率响应的乘积！**，只需要对$Y(j\omega)$做一次傅里叶反变换，即可求出信号$y(t)$的时域表达式，从而避免了解微分方程、冲激函数系数平衡、求时域卷积等一系列复杂的计算。
  
以上性质更一般的表述就是：
**两个信号的卷积的傅里叶变换，就是两个信号傅里叶变换的乘积**
或者：
  
$$y(t)=x(t)*h(t)\rightarrow Y(j\omega)=X(j\omega)H(j\omega)$$

这就是**时域卷积定理**，在LTI的频域分析中有重要作用。
其更加严格的数学证明参见：
> 证明：
> $\begin{aligned}
\mathcal{F}\{x(t)*h(t)\}={} & \int_{-\infty}^{+\infty}[\int_{-\infty}^{+\infty}x(\tau)h(t-\tau)\,d\tau] e^{-j\omega t}\,dt\\
={} & \int_{-\infty}^{+\infty}[\int_{-\infty}^{+\infty}x(\tau)h(t-\tau)e^{-j\omega t}\,d\tau] \,dt ——e^{-j\omega t}\text{对内层积分是常数} \\
={} & \int_{-\infty}^{+\infty}\{\int_{-\infty}^{+\infty}[x(\tau)e^{-j\omega \tau}][h(t-\tau)e^{-j\omega (t-\tau)}]\,d\tau\} \,dt  \\
={} & \int_{-\infty}^{+\infty}\{\int_{-\infty}^{+\infty}[x(\tau)e^{-j\omega \tau}][h(t-\tau)e^{-j\omega (t-\tau)}]\,dt\} \,d\tau  ——\text{交换积分次序}\\
={} & \int_{-\infty}^{+\infty}x(\tau)e^{-j\omega \tau}\int_{-\infty}^{+\infty}h(t-\tau)e^{-j\omega (t-\tau)}\,dt \,d\tau  ——\tau \text{对内层积分是常数}\\
={} & \int_{-\infty}^{+\infty}x(\tau)e^{-j\omega \tau}\int_{-\infty}^{+\infty}h(t-\tau)e^{-j\omega (t-\tau)}\,d(t-\tau) \,d\tau  \\
={} & \int_{-\infty}^{+\infty}x(\tau)e^{-j\omega \tau}H(j\omega) \,d\tau  \\
={} & H(j\omega) \int_{-\infty}^{+\infty}x(\tau)e^{-j\omega \tau}\,d\tau  ————H(j\omega)\text{对积分是常数}\\
= {} & X(j\omega)H(j\omega) \quad \#
\end{aligned}$ 
> 证毕。
### 2.12 频域卷积定理
在对称互易性的作用下，根据时域卷积定理，很容易联想到频域的卷积必定也会对应着时域的什么东西，这个性质就是——**频域卷积定理**：
$$x(t)y(t)\xleftrightarrow{\mathcal{F}}\frac{1}{2\pi}X(j\omega)*Y(j\omega) \tag{2.18}$$
证明方法与时域卷积定理类似，留给读者自行思考。
## 三. LTI的频域分析
### 3.1 截至目前，我们在做什么？
先来看看一个老生常谈的问题：
为什么频率响应如此重要？
在时域分析中，我们知道，对系统输入激励$x(t)$后，得到响应$y(t)$的时域表达式的方法有：
1. 解微分方程
2. 与单位冲激响应卷积

用单位冲激响应卷积的方法，**不会遇到冲激函数系数平衡的问题**，因为单位冲激响应已经考虑了。
之所以能应用单位冲激信号卷积的方法，是因为任何信号都能用单位冲激信号进行脉冲分解。
**换句话说，单位冲激信号是一类基本信号**。
而复指数信号也是一类基本信号，任何周期信号都可以用复指数信号进行分解——傅里叶展
开。并且，复指数信号还有一个好处就是，输入只需要乘以一个只与系统和信号频率相关的常
量即可得到输出，这个常量就是——频率响应$H(jω)$。这个结论，**也是用单位冲激信号的卷积发
现的**，联系这两者的重要关系是：

$$H(j\omega)=\int_{-\infty}^{+\infty}h(\tau)e^{-j\omega \tau}\,d\tau$$

**但是，并不是所有信号都是周期信号，大多数都是非周期的**。
因此，我们尝试对非周期信号进行==傅里叶展开==，看看能不能找到一些东西，使得我们依旧能够
套用上述结论，解决激励为非周期的情况。
这个东西，就是==傅里叶变换==。
但是非周期信号展开为复指数信号，并不是一个求和的运算，而是求和取极限的运算，即：积分
但是这并不影响我们套用结论，因为，积分的本质就是求和，或者说：**黎曼和**
由此，我们得到了激励为非周期情况下，输入与输出的关系：

$$Y(j\omega)=X(j\omega)H(j\omega)$$

这个关系是我们仿照“周期信号傅里叶展开作为激励，求输出与输入的关系”的方法，得到的。这
是物理上的理解。而且当我们从数学上证明时，也能证明这个式子是对的，此时我们的出发点是
——单位冲激响应的卷积。因此我们就发现了单位冲激响应的卷积，就对应着频率响应的相乘，
这个就是：==时域卷积定理==。
至此，我们已经完美解决了非周期信号的响应问题。
现在的问题是，我们对于周期信号和非周期信号作为激励的处理方法，是不同的：
3. 周期信号：傅里叶展开，基本信号倍乘$H(jkω0)$
4. 非周期信号：操作对象是傅里叶变换，倍乘$H(jω)$

我们希望找到一个通法，无论激励是周期的抑或非周期的，都能有一个通用的转换关系。
那么傅里叶变换能不能承担起这一使命呢？
傅里叶变换**积分的区间**是$-\infty$到$+\infty$，也就是说如果信号**不满足绝对可积**的话，我们无法通过积分求
出该信号的傅里叶变换。比如说直流信号、正弦信号，其傅里叶变换积分不收敛。
周期信号不满足绝对可积，无法用标准的积分变换公式求出其傅里叶变换，这一点是肯定的。
但当我们**引入不那么标准和严格的冲激函数**之后，情况就有所不同了。
然而不幸的是，我们依旧无法从傅里叶变换积分中，看出应该怎样用冲激函数拼凑我们的结
果。所以我们用冲激函数进行傅里叶反变换，得到了很重要很重要的一类结果：

$$\frac{1}{2\pi}\int_{-\infty}^{+\infty}\delta(\omega-\omega_0)e^{j\omega_0 t}=\frac{1}{2\pi}e^{j\omega_0 t}$$

或者更直白的说：

$$\mathcal{F}\{e^{j\omega_0 t}\}=2\pi \delta(\omega - \omega_0) \tag{*}$$

至此，任何包含**直流信号在内的周期信号的傅里叶变换**像我们都可以利用式$*$以及傅里叶展开求
出。也就是说，我们基于冲激函数，找到了周期信号的，不那么标准的一种傅里叶变换形式，这
种变换，我们称作——==广义傅里叶变换==
需要注意的是，由于周期信号是复指数信号的求和形式，因此，其傅里叶变换大概率有一个与非周
期信号很不同的点——求和符号$\sum$，或者说：==冲激串==！
至此，我们已经完全同统一了基于傅里叶变换方法的，周期信号和非周期信号作为LTI激励求解
响应的分析方法。
像这样，通过傅里叶变换或拉普拉斯变换等工具，将信号或系统从时间域转换到频率域进
行分析的方法称作：==频域分析==。
而贯穿于基于傅里叶变换的频域分析方法中，极为重要的概念就是：==频率响应==。
因为它直接关联起了激励和输入的关系，这种“关联”，就是一个简单的乘法。
**到这里，我们终于回答了开头提出的问题：“为什么频率响应如此重要？”**
现在，我们再来总结总结，截至目前我们对LTI的分析方法有哪些？
1. 时域分析法：
	- 直接求解系统的线性微分方程
	- 基于单位冲激响应的卷积方法
2. 频域分析法 
 	- 傅里叶展开与频率响应(只针对周期信号)
 	- 傅里叶变换与频率响应(针对所有信号)

### 3.2  LTI的时域分析与频域分析方法
**时域分析**
法一：求解常系数线性微分方程，零输入响应+零状态响应+冲激函数系数平衡法
法二：输入与单位冲激响应卷积，求解**零状态响应**

**频域分析**
法一：周期信号，傅里叶展开，系数倍乘频率响应，级数求和，求解**零状态响应**
法二：任意信号，傅里叶变换，时域卷积定理，傅里叶反变换，求解**零状态响应**
### 3.3 频率响应H(jω)的求法
上节的分析，我们已经认识到了频率响应的重要性。
现在我们来看看，如何用LTI的微分方程，求解出其频率响应。
考虑输入输出满足如下形式的常系数线性微分方程的连续时间线性时不变系统：

$$\sum_{k=0}^{N}a_k\frac{\text{d}^k y(t)}{\text{d} t^k}=\sum_{k=0}^{M}b_k\frac{\text{d}^k x(t)}{\text{d} t^k} \tag{5.1}$$

**结合时域微分性质，方程两边同时进行傅里叶变换**（当然，需要保证能够进行傅里叶变换）：

$$\sum_{k=0}^{N}a_k(j\omega)^kY(j\omega)=\sum_{k=0}^{M}b_k(j\omega)^kX(j\omega)\tag{5.2}$$

$$[\sum_{k=0}^{N}a_k(j\omega)^k]\cdot Y(j\omega)=[\sum_{k=0}^{M}b_k(j\omega)^k]\cdot X(j\omega)\tag{5.3}$$

进而得到：

$$H(j\omega)=\frac{Y(j\omega)}{X(j\omega)}=\frac{\sum_{k=0}^{M}b_k(j\omega)^k}{\sum_{k=0}^{N}a_k(j\omega)^k}\tag{5.4}$$

也就是说，频率响应可以直接由微分方程两端的系数写出。

### 3.4 系统响应的频域分析方法
总结一下，频域分析方法的步骤：
(1) 求输入信号的傅里叶变换$X(ω)$
(2) 求系统的频率响应$H(ω)$
(3) 求零状态响应$r_{\text{zs}}(t)$的傅里叶变换$X(ω)H(ω)$
(4) 傅里叶反变换，求解零状态响应

频率响应是一个复函数，可以分解为幅度与相位：

$$H(j\omega) = |H(j\omega)| e^{j\angle H(j\omega)}$$

* **$|H(j\omega)|$** 表示系统对频率为 $\omega$ 的信号的放大或衰减程度，称为**幅度响应**。
* **$\angle H(j\omega)$** 表示该频率分量经过系统后相位的变化，称为**相位响应**。

>**物理意义：**
> 频率响应揭示了系统对不同频率成分的滤波能力，是滤波器设计的核心依据（如低通、高通、带通等）。

频域分析方法的应用有很多，包括在信号抽样、滤波、调制解调中的应用。这里我们单独介绍一下一类比较常见的情况——当**激励为正弦信号**时。
（1）对于**实系统**（通常是指该系统的冲激响应h(t)是实数函数，即系统的微分方程系数是实数），设其频率响应为$H(j\omega)$，当激励信号为$\sin{(\omega_0 t+\mathcal{\phi})}$时：
$$y(t)=|H(j\omega_0)|\sin{(\omega_0 t+\phi+\angle H(j\omega_0))}$$
激励为余弦信号$\cos{(\omega_0 t+\phi)}$时同理：
$$y(t)=|H(j\omega_0)|\cos{(\omega_0 t+\phi+\angle H(j\omega_0))}$$
（2）对于**一般的线性时不变系统**：
当激励信号为$\sin{(\omega_0 t+\mathcal{\phi})}$时：
设：

$$H(j\omega_0)=A_{+}e^{j\theta_{+}}\quad H(-j\omega_0)=A_{-}e^{j\theta_{-}}$$

那么响应为：

$$y(t)=\frac{1}{2}A_{+}\sin{(\omega_0 t+\phi+\theta_{+})}+\frac{1}{2}A_{-}\sin{(\omega_0 t+\phi-\theta_{-})}$$

