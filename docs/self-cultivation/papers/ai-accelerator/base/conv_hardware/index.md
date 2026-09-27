# Hardware Design for Convolutional Layer

## I. Overview

卷积层本质是线性运算，更准确的来说：对张量进行线性变换。根据线性代数，任意线性变换均可以对应到一个矩阵乘法操作。

但这里有一个很重要的区分：

1. Step 1: 从数学上看，可以把卷积核展开成一个巨大的 Toeplitz / Block-Toeplitz 卷积矩阵；
2. Step 2: 从实际 CPU/GPU/NPU 实现看，通常不会真的构造这个巨大稀疏 Toeplitz 矩阵；
3. Step 3: 最经典的工程方法是 im2col + GEMM：把输入的每个卷积窗口展开成列，然后调用高效矩阵乘法；
4. Step 4: 更现代的实现则常进一步做成 implicit GEMM：连 im2col 矩阵都不真正写回内存，而是在数据进入 MAC 阵列时动态产生。

接下来我们按照：

$$\boxed{
\text{Toeplitz数学表示}
\rightarrow
\text{im2col + GEMM}
\rightarrow
\text{implicit GEMM / direct convolution}
}$$

层层递进的关系，分析卷积层从数学映射到硬件实现流程的基础原理。

---

## II. 第一阶段：从卷积到 Toeplitz 卷积矩阵

### 2.1 Take Conv1D as an example

先考虑最简单的一维情况。

输入

\[
x=
\begin{bmatrix}
x_0\\
x_1\\
x_2\\
x_3\\
x_4
\end{bmatrix}
\]

卷积核长度为 3：

$$w=\begin{bmatrix}w_0&w_1&w_2\end{bmatrix}$$

假设：

$$K=3,\qquad S=1,\qquad P=0$$

那么输出长度为

$$L_{\text{out}}=5-3+1=3$$

分别对应：

$$\begin{cases}y_0=w_0x_0+w_1x_1+w_2x_2\\
y_1= w_0x_1+w_1x_2+w_2x_3\\
y_2= w_0x_2+w_1x_3+w_2x_4
\end{cases}$$

即：


$$\begin{bmatrix}
y_0\\
y_1\\
y_2
\end{bmatrix}
=
\begin{bmatrix}
w_0&w_1&w_2&0&0\\
0&w_0&w_1&w_2&0\\
0&0&w_0&w_1&w_2
\end{bmatrix}
\begin{bmatrix}
x_0\\
x_1\\
x_2\\
x_3\\
x_4
\end{bmatrix}$$

其中：

$$\boxed{T(w)=\begin{bmatrix}
w_0&w_1&w_2&0&0\\
0&w_0&w_1&w_2&0\\
0&0&w_0&w_1&w_2
\end{bmatrix}}$$

就是 **Toeplitz** 矩阵。其核心思想就是将**输入张量和输出张量都展平为一维向量**，将卷积操作转化为：

$$\mathbf{Y} = T(w) \cdot \mathbf{X}$$

### 2.2 Toeplitz 矩阵

#### 2.2.1 定义与构造

Toeplitz 矩阵的定义非常简单：**它是一个主对角线及其平行线上的元素皆相等的矩阵**。即满足：

$$A_{i,j}=A_{i-1,j-1}$$

例如标准 Toeplitz：

\[
\begin{bmatrix}
a&b&c&d\\
e&a&b&c\\
f&e&a&b\\
g&f&e&a
\end{bmatrix}
\]

在标准 Toeplitz 矩阵中，上下相邻两行满足**平移不变性（0填充）**，由于卷积操作本质上是 **“滑动窗口的乘加运算”** ，这种平移不变性恰好对应了 Toeplitz 矩阵中对角线元素相等的特性。

构造 Toeplitz 矩阵的通法如下（这里我们只考虑Conv1D和Conv2D）：

无论是 Conv1D 还是 Conv2D，Toeplitz 矩阵的核心思想都是：**将输入特征图$\mathbf{X}$展平为一维列向量，并将卷积核展开成一个巨大的 Toeplitz 矩阵。**

1. **确定维度**：
    - 假设输入特征图的尺寸为：$H_{\text{in}} \times W_{\text{in}}$，则输入特征图将被展平为长度为 $N_{\text{in}} = H_{\text{in}} \times W_{\text{in}}$ 的**一维列向量**。
    - 由输入特征图尺寸和卷积核尺寸确定输出特征图尺寸为：$H_{\text{out}} \times W_{\text{out}}$，则输出特征图将被展平为长度为 $N_{\text{out}} = H_{\text{out}} \times W_{\text{out}}$ 的**一维列向量**。
    - 由此可以确定 Toeplitz 矩阵$T(w)$的维度为：$N_{\text{out}} \times N_{\text{in}}$。
2. **填充元素**：
    - 矩阵$T(w)$的每一行，**代表卷积核在输入特征图上的一次特定位置的滑动**。并且第 $i$ 行计算的是 $\mathbf{Y}$ 的第 $i$ 个元素。
    - 因此，填充方法是：对于$T(w)$的第 $i$ 行，找到卷积核当前**覆盖的输入元素索引**，将**卷积核的权重填入这些索引对应的列**中，**其余列置零**。

#### 2.2 详解 Conv1D 的 Toeplitz 矩阵

我们依然考虑：

$$w=\begin{bmatrix}w_0&w_1&w_2\end{bmatrix}, \qquad \begin{bmatrix}
y_0\\
y_1\\
y_2
\end{bmatrix}
=
\begin{bmatrix}
w_0&w_1&w_2&0&0\\
0&w_0&w_1&w_2&0\\
0&0&w_0&w_1&w_2
\end{bmatrix}
\begin{bmatrix}
x_0\\
x_1\\
x_2\\
x_3\\
x_4
\end{bmatrix}$$

$K=3, L_{\text{in}}=5, L_{\text{out}}=3$，并且 padding = 0, stride = 1。

这一次，我们用索引形式表达卷积操作：

$$y[i]=\sum_{k=0}^{K-1}w[k]x[i+k], \quad i=0,1,\cdots,L_{\text{out}}-1$$

更一般化：

$$y[i]=\sum_{j=0}^{L_{\text{in}}-1}T_{ij}x[j]$$

显然我们要求 $T[i, i:i+K-1] = w$ 且其他元素为0。

因此，我们得到了 $T_{ij}$ 的定义：

$$\boxed{T_{ij}
=
\begin{cases}
w[j-i], & 0\le j-i<K\\
0,&\text{otherwise}
\end{cases}}$$

显然，从该式可以看出 $T_{ij}$ 只依赖于 $j-i$，而不依赖于特定的 $i$ 和 $j$。

接下来我们看：

**(1) Stride 会发生什么？**

依旧对于原来的例子，这一次我们令 $S=2$，则此时 $L_{\text{out}}=2$。而：

$$T(w)=\begin{bmatrix}
w_0&w_1&w_2&0&0\\
0&0&w_0&w_1&w_2
\end{bmatrix}$$

因此 **stride = 2 相当于在 stride=1 的卷积矩阵中，每隔一行取一行**。此时的$T(w)$并非严格的 Toeplitz 矩阵。

从矩阵观点看：

\[
\boxed{\text{stride 本质上是对 Toeplitz 输出行的降采样}}
\]

**(2) Padding 会发生什么？**

依旧对于原来的例子，这一次我们令 $P=1$，即**保持输入输出形状不变**，此时我们有：

$$w=\begin{bmatrix}w_0&w_1&w_2\end{bmatrix}, \qquad \begin{bmatrix}
y_0\\
y_1\\
y_2\\
y_3\\
y_4
\end{bmatrix}
=
\begin{bmatrix}
w_1&w_2&0&0&0\\
w_0&w_1&w_2&0&0\\
0&w_0&w_1&w_2&0\\
0&0&w_0&w_1&w_2\\
0&0&0&w_0&w_1
\end{bmatrix}
\begin{bmatrix}
x_0\\
x_1\\
x_2\\
x_3\\
x_4
\end{bmatrix}$$

在这种情况下，$T(w)$仍然是**非常标准的 Toeplitz 矩阵，并且是方阵，卷积核中心元素位于主对角线。**

**(3) Dilation 会发生什么？**

依旧对于原来的例子，这一次我们假设 $D=2$，即**膨胀卷积**，此时我们有：

$$\begin{bmatrix}
y_0
\end{bmatrix}
=
\begin{bmatrix}
w_0&0&w_1&0&w_2
\end{bmatrix}
\begin{bmatrix}
x_0\\
x_1\\
x_2\\
x_3\\
x_4
\end{bmatrix}$$

也就是说：

\[
\boxed{\text{dilation 相当于在 kernel tap 之间插入结构性的 0}}
\]

### 2.3 Conv2D 的 Toeplitz 矩阵

#### 2.3.1 Conv2D 的 "Toeplitz" 矩阵的定义与构造

Conv2D 卷积中，Toeplitz 矩阵的构造方式仍然遵循上述原则，但**此时需要考虑两个维度上的平移不变性**，最终的 Toeplitz 矩阵也并非严格意义的 Toeplitz 矩阵。

我们依旧从案例入手，考虑：

输入：

$$X=
\begin{bmatrix}
x_{00}&x_{01}&x_{02}\\
x_{10}&x_{11}&x_{12}\\
x_{20}&x_{21}&x_{22}
\end{bmatrix}$$

kernel：

$$W=\begin{bmatrix}
a&b\\
c&d
\end{bmatrix}$$

stride = 1，padding = 0，此时输出为一个 $2\times2$ 特征图：

$$Y=\begin{bmatrix}
y_{00}&y_{01}\\
y_{10}&y_{11}
\end{bmatrix}$$

我们将输入和输出特征图展开为一维向量


$$x_{\text{vec}}
=
\begin{bmatrix}
x_{00}\\
x_{01}\\
x_{02}\\
x_{10}\\
x_{11}\\
x_{12}\\
x_{20}\\
x_{21}\\
x_{22}
\end{bmatrix}
, \qquad
y_{\text{vec}}
=
\begin{bmatrix}
y_{00}\\
y_{01}\\
y_{10}\\
y_{11}
\end{bmatrix}$$

满足 $y_{\text{vec}} = T(w) x_{\text{vec}}$ 的矩阵 $T(w)$ 即为：

$$\boxed{T(W)=
\begin{bmatrix}
a&b&0&c&d&0&0&0&0\\
0&a&b&0&c&d&0&0&0\\
0&0&0&a&b&0&c&d&0\\
0&0&0&0&a&b&0&c&d
\end{bmatrix}}$$

这个 "Toeplitz" 矩阵比较有意思，我们延续上述:

$$\boxed{\text{矩阵}T(w)\text{的每一行，代表卷积核在输入特征图上的一次特定位置的滑动}}$$

的理解：

从$T(w)$
第 $i=1$ 行：$\begin{bmatrix}a&b&0&c&d&0&0&0&0\end{bmatrix}$ 到
第 $i=2$ 行：$\begin{bmatrix}0&a&b&0&c&d&0&0&0\end{bmatrix}$ 对应着：**卷积核在输入特征图上的第一个水平滑道的一次水平滑动**

同理，

从$T(w)$
第 $i=3$ 行：$\begin{bmatrix}0&0&0&a&b&0&c&d&0\end{bmatrix}$ 到
第 $i=4$ 行：$\begin{bmatrix}0&0&0&0&a&b&0&c&d\end{bmatrix}$ 对应着：**卷积核在输入特征图上的第二个水平滑道的一次水平滑动**

而：

从$T(w)$
**第 $i=1,2$ 行整体**：$\begin{bmatrix}a&b&0&c&d&0&0&0&0\\ 0&a&b&0&c&d&0&0&0\end{bmatrix}$ 到：
**第 $i=3,4$ 行整体**：$\begin{bmatrix}0&0&0&a&b&0&c&d&0\\ 0&0&0&0&a&b&0&c&d\end{bmatrix}$ 对应着：

**卷积核由第一个水平滑倒切换到第二个水平滑倒的竖直滑动**

因此，事实上 Conv2D 的 "Toeplitz" 矩阵可以用**分块的方式**来看:

$$T(w)=
\begin{bmatrix}
A&B&0\\
0&A&B
\end{bmatrix}$$

其中：

$\begin{bmatrix}A&B&0\end{bmatrix}$代表**第 $i=1,2$ 行整体**
$\begin{bmatrix}0&A&B\end{bmatrix}$代表**第 $i=3,4$ 行整体**

完整的卷积操作（矩阵乘法）可以表示为：

$$\begin{bmatrix}
\color{red}{y_{00}}\\
\color{red}{y_{01}}\\
\color{green}{y_{10}}\\
\color{green}{y_{11}}
\end{bmatrix} = \begin{bmatrix}
\color{red}{A}&\color{red}{B}&\color{red}{0}\\
\color{green}{0}&\color{green}{A}&\color{green}{B}
\end{bmatrix} \begin{bmatrix}
x_{00}\\
x_{01}\\
x_{02}\\
x_{10}\\
x_{11}\\
x_{12}\\
x_{20}\\
x_{21}\\
x_{22}
\end{bmatrix}$$

而具体到分块内部，有：

$$A = \begin{bmatrix}
a&b&0\\
0&a&b
\end{bmatrix}, \qquad B = \begin{bmatrix}
c&d&0\\
0&c&d
\end{bmatrix}$$

这里的 $A$ 和 $B$ **也很有意思**：

- $A$ 对应着卷积核 $w$ 在水平/竖直滑道上滑动过程中，**第一行$\begin{bmatrix}a&b\end{bmatrix}$的贡献**。且 **$A$ 的第 $i=1$ 行到 $i=2$ 行表示着 $\begin{bmatrix}a&b\end{bmatrix}$ 的水平滑动**
- $B$ 对应着卷积核 $w$ 在水平/竖直滑道上滑动过程中，**第二行$\begin{bmatrix}c&d\end{bmatrix}$的贡献**。且 **$B$ 的第 $i=1$ 行到 $i=2$ 行表示着 $\begin{bmatrix}c&d\end{bmatrix}$ 的水平滑动**
- 整体 $\begin{bmatrix}A&B&0\end{bmatrix}$ 到整体$\begin{bmatrix}0&A&B\end{bmatrix}$代表着**卷积核由第一个水平滑倒切换到第二个水平滑倒的竖直滑动**

并且：

- $A$ 是**卷积核子核**$\begin{bmatrix}a&b\end{bmatrix}$的**标准 Toeplitz 矩阵**
- $B$ 是**卷积核子核**$\begin{bmatrix}c&d\end{bmatrix}$的**标准 Toeplitz 矩阵**
- 完整 $T(w)$ 是 $\begin{bmatrix}A\\ B\end{bmatrix}$的**标准 Toeplitz 矩阵**

因此，这种矩阵事实上称作：**双重块 Toeplitz 矩阵（Block Toeplitz with Toeplitz Blocks, BTTB）**：

二维卷积有**两个滑动方向**：$W$ 方向和 $H$ 方向

水平方向移动一次：$[a,b,0]\rightarrow[0,a,b]$
这产生了**block 内部的 Toeplitz**。

垂直方向移动一次：这使**整个 block $[A,B,0]$ 变成 $[0,A,B]$**
这产生了**block 级别的 Toeplitz**。

因此：

\[
\boxed{
\text{二维空间滑动}
\Longleftrightarrow
\text{two-level Toeplitz structure}
}
\]

#### 2.3.2 考虑 Input Channel 后的 BTTB

真正 CNN 输入一般是：

$$X\in
\mathbb R^{C_{in}\times H_{in}\times W_{in}}$$

**先考虑只有一个 output channel**。

kernel：

$$W\in
\mathbb R^{C_{in}\times K_h\times K_w}$$

依旧只考虑 **Strid=1, Padding=0, Dilation=1** 时的卷积结果：


$$Y\in
\mathbb R^{H_{out}\times W_{out}}$$

按照**索引方式展开**输出特征图：

$$Y[h,w]
=
\sum_{c=0}^{C_{in}-1}
\sum_{k_h}
\sum_{k_w}
W[c,k_h,k_w]
X[c,h+k_h,w+k_w]$$

把整个输入展开（顺序：**先变列索引，再变行索引，最后变通道索引**）：

$$x_{\text{vec}}
\in
\mathbb R^{C_{in}H_{in}W_{in}}$$

那么仍然存在一个矩阵：


$$T(W)
\in
\mathbb R^{
(H_{out}W_{out})
\times
(C_{in}H_{in}W_{in})
}$$

满足：


$$y_{\text{vec}}=T(W)x_{\text{vec}}$$

这个矩阵可以理解成：


$$\boxed{T(W)
=
\begin{bmatrix}
T(W_0)&T(W_1)&\cdots&T(W_{C_{in}-1})
\end{bmatrix}}$$

其中每个：$T(W_c)$ 负责一个输入通道。

这很好理解，因为：


$$Y
=
X_0*W_0
+
X_1*W_1
+\cdots$$

输出的一个通道等于输入和卷积核每个通道的卷积结果累加和，所以矩阵形式就是把**每个通道对应的卷积矩阵在水平方向上拼接**，恰好对应**输入特征图最后变动通道索引的展开顺序**。

#### 2.3.3 考虑 Output Channel 后的 BTTB

现在：

$$W\in
\mathbb R^{
C_{out}\times C_{in}\times K_h\times K_w
}$$

即我们有 $C_{out}$ 个卷积核，每个卷积核的尺寸都是：$C_{in}\times K_h\times K_w$。

比如：

$$W^{(0)},W^{(1)},\dots,W^{(C_{out}-1)}$$

**每一组都对应一个卷积矩阵**：

$$\begin{cases}
T(W^{(0)}) = \begin{bmatrix}
T(W^{(0)}_0)&T(W^{(0)}_1)&\cdots&T(W^{(0)}_{C_{in}-1})\end{bmatrix} \\
T(W^{(1)}) = \begin{bmatrix}
T(W^{(1)}_0)&T(W^{(1)}_1)&\cdots&T(W^{(1)}_{C_{in}-1}) \end{bmatrix} \\
\cdots \\
T(W^{(C_{out}-1)}) = \begin{bmatrix}
T(W^{(C_{out}-1)}_0)&T(W^{(C_{out}-1)}_1)&\cdots&T(W^{(C_{out}-1)}_{C_{in}-1}) \end{bmatrix} \\
\end{cases}$$

最后**纵向堆叠**：


$$\boxed{
T_{\text{full}}
=
\begin{bmatrix}
T(W^{(0)}_0)&T(W^{(0)}_1)&\cdots&T(W^{(0)}_{C_{in}-1}) \\
T(W^{(1)}_0)&T(W^{(1)}_1)&\cdots&T(W^{(1)}_{C_{in}-1}) \\
\vdots & \vdots & \ddots & \vdots \\
T(W^{(C_{out}-1)}_0)&T(W^{(C_{out}-1)}_1)&\cdots&T(W^{(C_{out}-1)}_{C_{in}-1})
\end{bmatrix}}$$

于是：

$$y_{\text{vec}}=T_{\text{full}}x_{\text{vec}}$$

矩阵尺寸为：


$$T_{\text{full}}
\in
\mathbb R^{
(C_{out}H_{out}W_{out})
\times
(C_{in}H_{in}W_{in})
}$$

这是一个超大规模的稀疏矩阵。

## 2.4 由 Toeplitz 矩阵分析卷积层特性

仔细看 Toeplitz 卷积矩阵，会发现三个明显特征。

**(1) 高度稀疏(sparse)**。

例如二维案例：


$$T(W)=
\begin{bmatrix}
a&b&0&c&d&0&0&0&0\\
0&a&b&0&c&d&0&0&0\\
0&0&0&a&b&0&c&d&0\\
0&0&0&0&a&b&0&c&d
\end{bmatrix}$$

只有 kernel 覆盖的位置非零。

如果 $K_hK_w\ll H_{in}W_{in}$，那么**绝大多数位置都是 0**。

**(2) 大量重复权重(repeated)**，例如 \(a,b,c,d\) 会不断重复出现。

**(3) 非零元素分布高度规则(structured)**。

它们不是随机稀疏，而是由于滑动窗口产生的规则结构。

---

Toeplitz 矩阵不只是一个“计算技巧”，它**揭示了很多数学事实**。

例如卷积是线性的：


$$T(W)(\alpha x_1+\beta x_2)=
\alpha T(W)x_1+\beta T(W)x_2$$

因为：

$$\boxed{\text{卷积运算}\Leftrightarrow \text{矩阵乘法} \Leftrightarrow \text{线性变换}}$$

它还揭示了：**local connectivity**，因为矩阵每一行只有少量非零元素。

又揭示了：**weight sharing**，因为相同 kernel 参数在矩阵中反复出现。

普通全连接层：

\[
y=Wx
\]

其中 \(W\) 的每个元素通常都是独立参数。

而卷积：

\[
y=T(w)x
\]

虽然看起来矩阵很大，但整个矩阵实际上只由很少的参数：$w_0,w_1,\dots$ 生成。

因此可以把卷积理解成：**一个受到强结构约束的大型线性层**，这个观点非常重要。

---

此外，理解 Toeplitz 矩阵对理解转置卷积（ConvTranspose）也有重要意义，

对于卷积运算：

$$y_{1}=T(W)x_1$$

其中 $y_1 \in \mathbb{R}^{C_{out}H_{out}W_{out}}$，$x_1 \in \mathbb{R}^{C_{in}H_{in}W_{in}}$，

$$T(W) \in \mathbb{R}^{(C_{out}H_{out}W_{out}) \times (C_{in}H_{in}W_{in})}$$

那么这个线性算子的转置就是：

$$y_2=T(W)^T x_2$$

其中 $y_2 \in \mathbb{R}^{C_{in}H_{in}W_{in}}$，$x_2 \in \mathbb{R}^{C_{out}H_{out}W_{out}}$，

$$T(W)^T \in \mathbb{R}^{(C_{in}H_{in}W_{in}) \times (C_{out}H_{out}W_{out})}$$

这正是 **transposed convolution** 名称真正的来源。


--- 

如果我们将**普通卷积操作理解为**：kernel 在**输入上滑动** $\Rightarrow$ 每个位置做**局部点积** $\Rightarrow$ 得到**输出像素**

那么 **Toeplitz 矩阵可以理解为**：把 kernel *的**所有滑动位置提前全部展开** $\Rightarrow$ 每个位置变成矩阵的一行，得到卷积矩阵 $T(W)$  $\Rightarrow$ **通过矩阵乘法实现卷积运算**。

因此最核心的一句话是：

$$\boxed{
\text{Toeplitz 矩阵就是卷积核“所有空间位置的副本”的静态展开。}
}$$

由此，我们容易想到的最自然的问题就是：

> **既然 Toeplitz 表示如此直接，为什么 CPU/GPU/NPU 不直接构造 \(T(W)\)，然后拿矩阵乘法器算 \(T(W)x\)？**

这个问题会把我们从纯数学表示正式带入**计算量、存储量、数据搬运和硬件利用率**，也正是从 Toeplitz 走向 im2col 的关键一步。