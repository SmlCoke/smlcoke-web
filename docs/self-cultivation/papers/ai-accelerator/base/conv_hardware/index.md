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

