# YOLOv3

## I. Bounding Box Prediction

> **This should be 1 if the bounding box prior overlaps a ground truth object by more than any other bounding box prior.**

这是最关键的一句。

拆开理解：

**“overlaps” 是什么？**

指的是 **IoU（Intersection over Union）**

**这句话在说什么？**

对某一个 **ground truth object**：

1. 把所有 bounding box priors（anchors）拿出来
2. 计算它们和该 GT 的 IoU
3. **IoU 最大的那个 anchor**
4. → 它的 **objectness label = 1**

换句话说：

> **每个真实目标，只“认领”一个 anchor（IoU 最大的那个）**

所以：

> “This should be 1”
> 指的是：
> 👉 **objectness 的监督标签为 1**

不是预测值，而是 **训练时的目标值（label）**


> **If the bounding box prior is not the best but does overlap a ground truth object by more than some threshold we ignore the prediction, following [17].**

这一句非常 subtle。

情况分三类：

| anchor 与 GT 的 IoU          | 处理方式              |
| -------------------------- | ----------------- |
| 最大 IoU 的那个                 | 正样本（objectness=1） |
| IoU > threshold（0.5），但不是最大 | **忽略（ignore）**    |
| IoU ≤ threshold            | 负样本（objectness=0） |

这里的 **ignore** 是关键：

**既不是正样本，也不是负样本**

即：

* 不算 objectness loss
* 不算 bbox loss
* 不算 class loss

这样做的原因是：

> **避免惩罚“其实预测得还不错、只是没被选中”的 anchor**


> **If a bounding box prior is not assigned to a ground truth object it incurs no loss for coordinate or class predictions, only objectness**

这句话非常重要，我们拆开：

**“not assigned to a ground truth object” 是指谁？**

* 不是 IoU 最大的 anchor
* 也不是被 ignore 的 anchor
* 即：**普通背景 anchor**

**“no loss for coordinate or class predictions”**

意思是：

* 不回归 bbox（x, y, w, h）
* 不预测类别
* 因为：

  > **本来就没有目标，回归坐标/类别是没有意义的**

**“only objectness”**

但仍然：

* 计算 objectness loss
* 目标是：
  \[
  \text{objectness} = 0
  \]

即：

> **你应该学会说：这里没有物体**


## II. Class Prediction
> During training we use binary cross-entropy loss for the class predictions. This formulation helps when we move to more complex domains like the Open Images Dataset [7]. In this dataset there are many overlapping labels (i.e. Woman and Person).

**Binary cross-entropy loss**

- 单个类别的 BCE 公式
    对某个类别 (c)：真实标签：\(y_c \in {0,1}\)，预测概率：\(p_c \in (0,1\))，则：
    \[
    \mathcal{L}_{\text{BCE}}(y_c, p_c)
    = - \left[ y_c \log p_c + (1-y_c)\log(1-p_c) \right]
    \]
    如果 \(y_c = 1\)，你就希望 \(p_c \to 1\)；如果 \(y_c = 0\)，你就希望 \(p_c \to 0\)

- 多类别时的 BCE（YOLOv3 实际用的）
    对一个 box，有 (C) 个类别：

    \[
    \mathcal{L}_{\text{class}}
    = \sum_{c=1}^{C}
    \mathcal{L}_{\text{BCE}}(y_c, p_c)
    \]

    **逐类独立求和**，没有归一化，没有类别之间的“竞争”

**YOLOv3 把“类别预测”建模成一个多标签问题（multilabel classification），而不是传统的“单标签多分类”（softmax）。**

也就是说：**一个 bounding box 可以同时属于多个类别**，每个类别是一个**独立的二分类问题**

> **传统做法：softmax（单标签分类）**
softmax 的隐含假设是：
\[
\sum_{c=1}^C p_c = 1
\]
也就是：**一个框只能属于一个类别**
例如：这个框要么是 `Person`,要么是 `Dog`,不可能同时是两个,这在 **VOC / COCO 的早期版本** 里大致成立。
**YOLOv3 的做法：multilabel + sigmoid**
YOLOv3 改成：每个类别 **一个 sigmoid**，各类别 **互不竞争**
\[
p_c = \sigma(z_c), \quad c = 1,\dots,C
\]
$z_c$是线性分类器的原始输出，范围是$(-\infty, +\infty)$
意味着：一个 box 可以同时满足，`Person = 1`，`Woman = 1`，`Adult = 1`


## III. Predictions Across Scales

### 3.1 “base feature extractor 在网络的哪个部分？为什么还要加几个卷积层？”
base feature extractor = Darknet-53 主干网络（backbone），就是一些列卷积层和残差块
为什么还要多加几层卷积层？
**把“分类特征”转成“检测特征”**

* backbone 主要学的是 **语义表征**
* 检测需要的是：精确定位（回归）+objectness+类别判断
所以需要 **专门的 detection head 卷积层**

### 3.2 scale 与 anchor box
> In our experiments with COCO [10] we predict 3 boxes at each scale so the tensor is N × N × [3 ∗ (4 + 1 + 80)] for the 4 bounding box offsets, 1 objectness prediction, and 80 class predictions.

这里的每个scale对应3个boxes，就是说一个grid cell有3个anchor box，当然，来自不同的尺寸

### 3.3 anchor box的尺寸

**在整个训练集的所有 ground truth box 上，仅用宽高 (w, h) 做 K-means 聚类得到了9个anchor box：**
COCO 上得到的就是：

```
(10×13), (16×30), (33×23),
(30×61), (62×45), (59×119),
(116×90), (156×198), (373×326)
```

> ✅ **每个 scale 分配 3 个 anchor**

具体分配方式（从小到大）：

| Scale | Feature Map | Anchor 尺寸                      |
| ----- | ----------- | ------------------------------ |
| 小目标   | 52×52       | (10×13), (16×30), (33×23)      |
| 中目标   | 26×26       | (30×61), (62×45), (59×119)     |
| 大目标   | 13×13       | (116×90), (156×198), (373×326) |

### 3.4 grid cell 中， 如何使用这些 anchor box?
训练时流程是：
1. 对一个 GT box
2. 找 **IoU 最大的 anchor（在所有 scale 上）**
3. 只把这个 anchor 标为正样本
4. anchor 所在的 grid cell 负责预测该目标 