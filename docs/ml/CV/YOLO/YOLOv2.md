# YOLOv2 相比 YOLOv1 的核心改动（精简版）

> 目标一句话：**YOLOv2 通过引入 anchor、改进坐标参数化与训练策略，显著提升了定位稳定性与召回率，同时保持实时性。**



## I. 从“直接回归框”到“Anchor-based 预测”（最核心变化）

### YOLOv1

* 每个 grid cell **直接回归 bounding box**：
  \[(x, y, w, h)\]
* 回归空间大，
  * 大物体：单 cell 压力过大
  * 小物体：易冲突


### YOLOv2

* 引入 **Anchor Boxes（先验框）**
* 网络不再预测 box 本身，而是预测 **相对于 anchor 的偏移量**：

\[
(t_x, t_y, t_w, t_h)
\]

最终 box 由：

\[
\begin{aligned}
b_x &= \sigma(t_x) + c_x \\
b_y &= \sigma(t_y) + c_y \\
b_w &= p_w \cdot e^{t_w} \\
b_h &= p_h \cdot e^{t_h}
\end{aligned}
\]

* \((p_w, p_h\))：anchor 宽高
* \((c_x, c_y\))：grid cell 左上角

📌 **效果**：

* 回归难度显著降低
* Recall 明显提升（v2 论文明确指出）



## II. Anchor 的来源：K-means 聚类（数据驱动）

* 对训练集 GT box 的 \((w, h)\) 做 K-means
* 距离度量：

\[
d(box, centroid) = 1 - IOU
\]

📌 Anchor ≈ 数据集中最常见的物体形状（先验）



## III. “责任分配”机制的变化

### YOLOv1

* 一个 cell 的 B 个 predictor **动态竞争**
* IOU 最大者负责 GT

### YOLOv2

* 每个 predictor **绑定一个 anchor**
* 一个 GT box 分配给：

  * 中心点所在 cell
  * **IOU 最大的 anchor**

📌 predictor 具有了“形状语义”



## IV. Bounding box 参数化改进（稳定训练）

* 使用 \(\sigma(t_x), \sigma(t_y)\)：
  * 限制中心点在 cell 内（0,1）
* 使用 \(e^{t_w}, e^{t_h}\)：

  * 保证宽高为正
  * 相对缩放更稳定

📌 减少数值发散，训练更稳



## V. 从 FC 到 Fully Convolutional

* 移除 YOLOv1 中的全连接层
* 网络变为 **全卷积结构（FCN）**

📌 带来的好处：

* 可变输入尺寸（multi-scale training）
* 更好的泛化能力



