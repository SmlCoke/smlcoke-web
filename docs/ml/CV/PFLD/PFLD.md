# PFLD

## I. Introduction

### 1.0 Challenges
挑战一：局部变异。**面部表情、极端光照条件**（如高光与阴影）以及遮挡会导致人脸图像产生局部变化或干扰。某些区域的特征点可能偏离正常位置，甚至完全消失。

挑战二：全局变异。**姿态(pose)变化**与**成像质量(imaging quality)**是全局影响人脸外观的两大因素。当面部整体结构估计出现偏差时，可能导致（大量）特征点定位失准。

挑战三：数据失衡(data imbalance)。无论在浅层学习还是深度学习中，可用数据集常出现类别/属性分布不均衡的情况。这种失衡极易导致算法/模型无法准确表征数据特性，从而在不同属性上表现欠佳。

挑战四：**模型效率(Model Efficiency)**。适用性还面临另外两大限制——模型规模与计算需求。诸如机器人控制、增强现实和视频聊天等任务，往往需要在智能手机或嵌入式产品这类计算与内存资源有限的平台上实时运行。

### 1.1 Pre Arts

> 近期，Kumar与Chellapa提出了一种名为姿态条件树突卷积神经网络（PCD-CNN）的单树突CNN模型[19]。该网络通过将分类网络与模块化次级分类网络相结合，有效提升了检测精度。Honari等人则开发了具有等变地标变换（ELT）损失项的序贯多任务网络（SeqMT）[12]。文献[30]中，作者提出了一种基于由粗到精回归树集成（ERT）的面部特征点回归方法[16]。针对图像风格固有差异对特征点检测的影响，Dong团队构建了风格聚合网络（SAN）[9]，通过联合原始人脸图像与风格聚合图像来训练特征点检测器。Wu等人将边界信息视为人脸几何结构特征，提出了边界感知的人脸对齐算法LAB，该算法通过边界线推导面部特征点，从而显著减少了特征点定义中的模糊性问题。其他代表性的人脸对齐技术还包括[33, 42, 47, 10, 37, 36]等。尽管现有深度学习方法已取得显著进展，但在实际应用中如何协同优化检测器的精度、效率与模型紧凑性，仍存在巨大的改进空间。

### 1.2 PFLD

**增加 MS-FC 层，获取更大的 receptive field，更好地捕捉人脸的全局结构。**
> To enlarge the receptive field and better catch the global structure on faces, a multi-scale fully-connected (MS-FC) layer
is added for precisely localizing landmarks in images

采用 MobileNet 构建 backbone，优点是**轻量高速，适合边缘部署**
> As for the processing speed and model compactness, we build the backbone network of our PFLD using MobileNet blocks

## II. Methodology

###  2.1 Loss Function
==Against Challenge 1, 2, 3==

传统的 L2 Loss 仅计算 2D 坐标距离，缺乏对 3D 几何结构的感知。作者利用**辅助网络**预测 3D 到 2D 的投影参数，以此作为正则化手段，帮助主网络更好地理解人脸姿态。

**3D-to-2D Projection Analysis**
设 $\mathbf{X}$ 为 2D 图像特征点，$\mathbf{U}$ 为 3D 标准人脸模型特征点，二者通过投影矩阵 $\mathbf{P}$ 关联。

1.  **数据定义**：
    *   $\mathbf{X}$ ($2 \times N$)：图像平面上的 2D 关键点坐标。
    *   $\mathbf{U}$ ($4 \times N$)：标准 3D 人脸模型的关键点坐标，使用**齐次坐标** $[u_i, v_i, z_i, 1]^T$，以便统一表示旋转和平移。

2.  **投影矩阵 $\mathbf{P}$ ($2 \times 4$) 与自由度**：
    *   基于**弱透视投影模型 (Weak Perspective Model)**，投影由 6 个自由度决定：
        *   **Rotation (3 DoF)**: 欧拉角 (Yaw, Pitch, Roll)。
        *   **Scale (1 DoF)**: 缩放比例。
        *   **Translation (2 DoF)**: 平面位移 ($t_x, t_y$)。

3.  **简化策略**：
    *   由于输入人脸图像已经过**检测、居中 (Centralized) 和归一化 (Normalized)**，**平移**和**缩放**因素已被消除或固定。
    *   因此，辅助网络**只需估算 3 个欧拉角 (Euler Angles)** 即可有效表征人脸的几何姿态变化。

**对稀有训练样本施加更大的惩罚**
> Under the circumstances, “equally” penalizing each sample makes it unequal instead. To address this issue, we advocate to penalize more on errors corresponding to rare training samples than on those to rich ones.


**Loss Funcion**
从数学角度而言，损失函数可表述为以下通用形式：

$$\mathcal{L}:=\frac{1}{M} \sum_{m=1}^{M} \sum_{n=1}^{N} \gamma_{n}\left\|\mathbf{d}_{n}^{m}\right\|$$

其中$||\cdot||$表示用于衡量第m个输入中第n个特征点距离/误差的特定度量指标。N代表每张人脸需检测的预定义特征点数量，**M表示每个训练批次batch中的图像数量**。在给定度量标准（如本文采用的$\ell_2$范数）后，权重系数$\gamma_n$起关键作用。综合前述几何约束与数据不平衡等考量，我们设计的新型损失函数如下：

$$\mathcal{L}:=\frac{1}{M} \sum_{m=1}^{M} \sum_{n=1}^{N}\left(\sum_{c=1}^{C} \omega_{n}^{c} \sum_{k=1}^{K}\left(1-\cos \theta_{n}^{k}\right)\right)\left\|\mathbf{d}_{n}^{m}\right\|_{2}^{2} .$$

显然，式(2)中的$\sum_{c=1}^{C} \omega_{n}^{c} \sum_{k=1}^{K}\left(1-\cos \theta_{n}^{k}\right)$项等价于式(1)中的$\gamma_n$。具体分析该损失函数：其中$\theta^1$、$\theta^2$与$\theta^3$（$K=3$）分别表示**真实值与估计值在偏航角、俯仰角及翻滚角上的偏差角度**。显然，**偏差角增大时惩罚力度随之增强**。此外，我们将样本划分为多属性类别，包括侧脸、正脸、抬头、低头、表情及遮挡等类别。权重参数$\omega_n^c$根据类别$c$的样本占比进行调整（本研究直接采用占比的倒数）。例如，当禁用几何约束与数据不平衡功能时，该损失函数即退化为普通$\ell_2$损失。无论三维姿态或数据不平衡是否影响训练过程，本损失函数都能通过距离度量有效处理局部变异问题。

### 2.2 BackBone Network

> Similar to other CNN based models, we employ several convolutional layers to extract features and predict landmarks. Considering that human faces are of strong global structures, like symmetry and spacial relationships among eyes, mouth, nose, etc., such global structures could help localize landmarks more precisely. Therefore, instead of single scale feature maps, we extend them into multi-scale maps. The extension is finished via executing convolution operations with strides, which enlarges the receptive field. Then we perform the final prediction through fully connecting the multi-scale feature maps. The detailed configuration of the backbone subnet is summarized in Table 1.
> 与其他基于卷积神经网络（CNN）的模型类似，我们采用多个卷积层进行特征提取与关键点预测。考虑到人脸具有强烈的全局结构特征（如对称性及眼、口、鼻等器官的空间关系），这些全局结构有助于更精准地定位关键点。**因此，我们并未使用单一尺度特征图，而是将其扩展为多尺度特征图——通过带步长的卷积操作扩大感受野来实现扩展**，最终通过全连接多尺度特征图完成预测。主干子网的具体配置详见表1。
> ![alt text](image.png)
> 表1：主干网络配置。每行代表一组**重复$n$次**的相同层结构。同一序列中的**所有层均具有相同数量的输出通道** $c$。每组序列的**首层**步长为$s$。扩展系数$t$始终作用于输入尺寸。

**重点：MS-FC (Multi-Scale Fully Connected) Layer**

**Why Multi-Scale?**
*   **Single Scale 其实不够用**: 传统 CNN (如 VGG/ResNet) 通常只利用最后一层特征图进行预测。虽然高层特征语义强（包含全局结构信息），但分辨率过低，丢失了关键点定位所需的**空间细节**。
*   **Multi-Scale 的优势**: 融合不同深度的特征图。
    *   **浅层/大尺寸**: 保留边缘、纹理等几何细节（利于精确位置回归）。
    *   **深层/小尺寸**: 包含拓扑结构、姿态等语义信息（利于全局约束）。

**PFLD 的实现策略**
PFLD 在 Backbone 推理过程中，从不同阶段引出分支（Table 1 中的 S1, S2, S3），最后进行拼接融合。

*   **S1 (Scale 1)**: 输入 $14 \times 14 \times 16$，捕捉细粒度特征（如器官轮廓）。
*   **S2 (Scale 2)**: 输入 $7 \times 7 \times 32$，捕捉中等尺度特征。
*   **S3 (Scale 3)**: 输入 $1 \times 1 \times 128$，捕捉高度抽象的全局特征。

**Fusion 过程**:
这三个尺度的特征图分别被 Flatten（拉平），然后 **Concat（拼接）** 成一个长向量，最后输入全连接层进行预测。这种设计兼顾了模型轻量化与高精度定位需求。


It is worth to mention that the **quantization techniques** are totally compatible with **ShuffleNet and MobileNet**, which means the size ofour model can be further reduced by quantization.

### 2.3 Auxiliary Network

> our intention is to estimate the 3D rotation information including yaw, pitch, and roll angles. Having these three Euler angles, the pose of head can be determined
> 我们的目标是通过估计包含偏航角（yaw）、俯仰角（pitch）和翻滚角（roll）的三维旋转信息。获取这三个欧拉角后，即可确定头部姿态。

**计算这三个角的方式：**
> (1) predefine ONE standard face (averaged over a bunch of frontal faces) and fix 11 landmarks on the dominant face plane as references for ALL of training faces
> (2) use the corresponding 11 landmarks of each face and the reference ones to estimate the rotation matrix
> (3) compute the Euler angles from the rotation matrix
>
> (1) 预定义一个标准人脸（通过对多张正面人脸取平均生成），并在主导人脸平面上**固定11个关键点作为所有训练人脸的参考基准**  
> (2) 利用每张人脸**对应的11个关键点**与参考关键点来**估算旋转矩阵**  
> (3) 从该旋转矩阵中计算欧拉角

the input of the auxiliary net is from the 4-th block of the backbone net (see Table 1)

![alt text](image-1.png)
> Table 2: The auxiliary net configuration. As the auxiliary branch is no longer needed in the testing, we do not apply the MobileNet techniques in our implementation.

## III. Experiments
### 3.1 Experimental Settings
数据集。为评估我们提出的PFLD方法性能，我们在两个广泛使用的挑战性数据集上进行实验：300W[25]和AFLW[18]。300W数据集标注了包括LFPW、AFW、HELEN、XM2VTS和IBUG在内的五个面部数据集，共包含68个关键点。我们遵循[9,34,19]的研究设置，使用3,148张图像进行训练，689张图像用于测试。测试图像分为两个子集：由LFPW和HELEN中554张图像组成的常规子集，以及来自IBUG的135张图像构成的挑战子集。常规子集与挑战子集共同构成完整测试集。AFLW数据集包含24,386张自然场景人脸图像，采集自Flicker平台，涵盖极端姿态、表情和遮挡情况。这些人脸图像的头部姿态变化范围较大：偏航角（yaw）为0°至120°，俯仰角（pitch）和翻滚角（roll）可达90°。AFLW为每张人脸提供最多21个关键点标注。我们分别使用20,000张和4,386张图像进行训练和测试。

d对比。参与对比的方法包括经典及近年提出的深度学习方案：RCPR (ICCV'13)[4]、SDM (CVPR'13)[38]、CFAN (ECCV'14)[42]、CCNF (ECCV'14)[1]、ESR (IJCV'14)[5]、ERT (CVPR'14)[16]、LBF (CVPR'14)[24]、TCDCN (ECCV'14)[45]、CFSS (CVPR'15)[46]、3DDFA (CVPR'16)[48]、MDM (CVPR'16)[29]、RAR (ECCV'16)[37]、CPM (CVPR'16)[33]、DVLN (CVPRW'17)[35]、TSR (CVPR'17)[22]、Binary-CNN (ICCV'17)[3]、PIFA-CNN (ICCV'17)[15]、RDR (CVPR'17)[36]、DCFE (ECCV'18)[30]、SeqMT (CVPR'18)[12]、PCDCNN (CVPR'18)[19]、SAN (CVPR'18)[9]和LAB (CVPR'18)[34]。

评估指标。遵循多数先前工作[5,34,9,19]，我们采用归一化平均误差（NME）来衡量精度，该指标通过计算所有**标注关键点的归一化误差平均值**获得。对于300W数据集，我们使用两种归一化因子报告结果：一种采用**瞳孔中心距离作为归一化基准**（inter pupil），另一种采用**外眼角距离**（inter-ocular）进行归一化。针对AFLW数据集，由于存在大量侧面人脸，我们按照[19,9,34]的方法，通过所有**可见关键点的真实边界框尺寸对误差**进行归一化。同时采用累积误差分布（CED）曲线进行方法比较。除精度外，我们还对比了处理速度和模型大小。

### 3.2 Experimental Results

#### 检测准确率
我们首先在300W数据集上将PFLD模型与现有最优方法进行对比。表4展示了实验结果，其中包含PFLD 0.25X、PFLD 1X和PFLD 1X+三个版本。PFLD 1X代表完整模型，**PFLD 0.25X是通过将MobileNet模块的宽度参数设为0.25得到的压缩模型（两者均仅使用300W训练数据），而PFLD 1X+表示额外在WFLW数据集[40]上预训练的完整模型。**从表3数据可见，PFLD 1X显著优于先前方法，尤其在挑战性子集上表现突出。虽然PFLD 0.25X性能略逊于PFLD 1X，但仍超越包括最新提出的LAB[34]、SAN[9]和PCD-CNN[19]在内的其他竞争者。这一对比充分说明PFLD 0.25X实现了良好的实践平衡——在模型体积缩减约80%的同时，精度损失极小。这也印证了深度学习卷积层的大量特征通道可能存在于低维流形中的假设。后文将展示PFLD 0.25X相较PFLD 1X的速度优势。至于PFLD 1X+，其精度优势进一步扩大，表明通过输入更多训练数据可进一步提升网络性能。

我们还通过图3的CED曲线评估精度差异。从更实用的角度出发，本实验所有参与方法均采用300W检测器获取测试集人脸框（不同于先前使用真实标注人脸框的对比）。部分方法（如SAN）相比使用真实标注框时性能有所下降，这反映了特征点检测器对人脸检测器的稳定性依赖。曲线显示PFLD以显著优势超越其他方法。

在AFLW数据集上进一步评估各方法性能差异。表5列出了各竞争方法的NME结果，可见TSR、CPM、SAN及我们的PFLD系列显著优于其他方法。其中PFLD 1X以1.88 NME位居榜首，SAN（1.91 NME）次之，PFLD 0.25X以2.07 NME位列第三。需再次强调PFLD 0.25X的模型体积和处理速度远优于SAN（详见表3）。

#### 模型体积
表3对比了PFLD与经典及最新深度学习方法的模型体积和处理速度。PFLD 0.25X仅2.1Mb，较PFLD 1X节省超10Mb，且远小于SDM（10.1Mb）、LAB（50.7Mb）和SAN（约800Mb，含两个基于VGG的子网270.5Mb+528Mb）。

#### 处理速度  
我们进一步评估了各算法在英特尔i7-6700K CPU（标记为C）和英伟达GTX 1080Ti GPU（标记为G）上的运行效率（特殊说明除外）。由于仅能获取SDM[38]的CPU版本和SAN[9]的GPU版本，因此仅分别记录它们的CPU耗时与GPU耗时。对于LAB[34]，其项目页面仅提供CPU版本下载。但文献[34]中作者指出，该算法在TITAN X GPU（标记为G*）上耗时约60毫秒。对比数据显示，我们的PFLD 0.25X和PFLD 1X在CPU与GPU上的速度均显著优于其他算法。需注意LAB的CPU耗时单位为秒而非毫秒。**PFLD 0.25X在CPU和GPU上耗时相同（1.2毫秒），这是因为大部分时间消耗在I/O操作上。此外，PFLD 1X的CPU耗时约为0.25X版本的5倍，GPU耗时约为3倍，但仍远快于其他算法**。我们还测试了PFLD 0.25X和PFLD 1X在**高通ARM 845处理器（表格中标记为A）**上的表现：PFLD 0.25X**单张人脸处理耗时7毫秒**（超过140帧/秒），PFLD 1X则为26.4毫秒（超过37帧/秒）。

#### 消融实验  
为验证所提损失函数的优势，我们在300W和AFLW数据集上进行了消融研究，对比了包括L2和L1在内的两种典型损失函数。如表6所示，L2与L1损失的差异不明显——在300W上IPN指标分别为4.40和4.35，在AFLW上NME指标分别为2.33和2.31。我们的基准损失采用L2，并设置三种对比方案：仅含几何约束（γ=1，标记为"ours w/o θ"）、仅含加权策略（θ_k=0，关闭辅助网络，标记为"ours w/o γ"）以及同时包含几何约束与加权策略（标记为"ours"）。实验结果表明：在300W数据集上，"ours w/o θ"和"ours w/o γ"分别比基准L2相对提升4.1%（IPN 4.22）和5.9%（IPN 4.14）；在AFLW数据集上分别相对提升4.3%（NME 2.23）和7.3%（NME 2.16）。而同时引入几何信息与加权策略的完整方案，在300W和AFLW上分别实现10.2%（IPN 3.95）和19.3%（NME 1.88）的相对提升，验证了所设计损失函数的有效性。

#### 补充结果  
**图4展示了300W和AFLW测试集中不同姿态、光照、表情、遮挡以及妆容风格的人脸可视化结果，可见PFLD 0.25X能获得优异的关键点定位效果**。**为构建完整系统，我们采用MTCNN[43]检测图像/视频帧中的人脸区域，再将检测结果输入PFLD进行关键点定位。**图5展示了两组多人脸场景的检测效果：第一组图片中所有人脸均被成功检测且关键点定位精准；第二组图片后两排存在两例漏检，这是由于严重遮挡导致人脸检测失败所致（需强调这是人脸检测器的局限而非关键点定位算法的问题）。**所有被检测到的人脸，其关键点均被准确计算。**


## IV. Concluding Remarks
面部关键点检测器需要关注三个核心方面以确保其在大规模及实时任务中的胜任能力，即**准确性、效率和紧凑性**。本文提出了一种实用的面部关键点检测器PFLD，其结构包含主干网络与辅助网络两个子网。主干网络采用 **MobileNet** 模块构建，可显著减轻卷积层的计算压力，并通过**调节宽度参数**使用户能根据需求灵活调整模型尺寸。我们引入了**多尺度全连接层以扩大感受野**，从而增强对脸部结构的捕捉能力。为进一步规范关键点定位，我们定制了**辅助网络分支**，可有效估计**旋转信息**。针对几何正则化与数据不平衡问题，设计了一种**新型损失函数**。大量实验结果表明，该设计在精度、模型体积和处理速度方面均优于当前最先进方法，验证了PFLD0.25X版本在实际应用中的优异平衡性。

当前版本PFLD仅采用旋转信息（偏航角、翻滚角和俯仰角）作为几何约束。未来可引入**其他几何/结构信息以进一步提升精度**，例如借鉴LAB[34]方法通过边界线约束关键点偏移范围。另一改进方向是将基础L2损失函数替换为任务专用损失函数。此外，针对训练数据不平衡和有限的情况，设计更精细的损失加权策略也颇具价值。上述构想将作为我们未来的研究方向。