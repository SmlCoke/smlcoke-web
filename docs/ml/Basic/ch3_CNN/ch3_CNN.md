# Convolutional Neural Networks (CNN) 基础

## I. Motivation for CNN
在处理图像任务时，全连接神经网络（Fully Connected NN）会面临参数量过大的问题。CNN 通过利用图像的三个特性来简化网络架构：

### 1.1 Detection of Local Patterns
图像中的某些模式（如边缘、颜色块）通常比整张图像小得多。神经元只需要关注图像的一个局部区域（Receptive Field）即可识别这些模式。

### 1.2 Translation Invariance
同样的模式可能会出现在图像的不同位置。我们可以让不同位置的神经元共享同一组参数（Shared Weights），即使用同一个滤波器来检测不同位置的相同特征。

### 1.3 Subsampling
像素的下采样不会改变图像中的物体。例如，去掉奇数行和偶数列后的图像，人类依然可以辨认出其中的物体。这为减少计算量提供了依据。

## II. Convolutional Layer
卷积层是 CNN 的核心，它实现了“局部感受野”和“参数共享”。

### 2.1 Filter (Tensor)
每一个 Filter（滤波器）本质上是一个小矩阵（例如 $3 \times 3$）。Filter 在图像上滑动并进行点积运算，输出特征图（Feature Map）。


### 2.2 Stride and Padding
- **Stride (步长)**：滤波器每次移动的像素数。
- **Padding (填充)**：在图像四周补充 0 或其他数值，用以控制输出特征图的大小并保护边缘信息。

### 2.3 Output Size Calculation
假设输入特征图大小为 $W \times H$，滤波器大小为 $F \times F$，步长为 $S$，填充为 $P$。则输出尺寸为：

$$W_{out} = \lfloor \frac{W - F + 2P}{S} \rfloor + 1$$

$$H_{out} = \lfloor \frac{H - F + 2P}{S} \rfloor + 1$$

### 2.4 Feature Map
经过多个 Filter 卷积后，会得到多个 Feature Map。若输入有 $C$ 个通道，则每个 Filter 的深度也必须为 $C$。

## III. Pooling Layer
池化层用于减少空间维度，从而减少参数量并提高模型的鲁棒性。

### 3.1 Max Pooling
在感受野中选取最大值作为该区域的代表。这是最常用的池化方式，能够保留最显著的特征。


### 3.2 Average Pooling
计算感受野内所有像素的平均值。

## IV. CNN Architecture Overview
一个典型的 CNN 架构通常由以下两部分组成：

### 4.1 Feature Extraction
通过交替叠加卷积层（Convolutional Layer）和池化层（Pooling Layer）来提取图像的高层特征。
- **Flatten**：在进入分类层之前，需要将多维的 Feature Map 拉直成一维向量。

### 4.2 Classification
使用扁平化后的向量作为输入，通过全连接层（Fully Connected Layers）和 Softmax 激活函数输出类别的概率分布。

## V. CNN for AlphaGo
CNN 不仅限于处理图像。在 AlphaGo 中，棋盘被视为 $19 \times 19$ 的“图像”，由于围棋也具有局部模式（如某些棋型）和某种程度的平移不变性，CNN 同样表现出色。
- 注意：由于棋盘像素不能随意丢弃，AlphaGo 的 CNN 架构中通常不使用 Pooling 层。
