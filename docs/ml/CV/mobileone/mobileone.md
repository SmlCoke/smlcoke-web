# MobileOne

## I. MobileOne Block
MobileOne 结构的核心思想是 **结构重参数化（Structural Re-parameterization）**。

1.  **训练阶段（Train-time）：多分支结构**
    为了增强模型的特征提取能力，MobileOne 在训练时引入了“过参数化（Over-parameterization）”的分支。
    *   **Scale Branch**: $1 \times 1$ 卷积，用于捕捉从输入到输出的线性变换。（当主卷积 `kernel_size > 1` 时才存在）
    *   **Skip Branch**: 仅含 BatchNorm 的跳跃连接（当输入输出维度匹配时）。
    *   **Conv Branch**: 包含多个（`num_conv_branches`）标准卷积分支。

    这种设计使得损失函数的解空间更加平滑，更容易找到全局最优解。

2.  **推理阶段（Inference-time）：单路结构**
    在部署时，通过数学变换，将上述所有并行分支的权重和偏置“吸收”合并到一个单独的卷积层中。
    *   **结果**：最终模型在推理时只包含简单的 `Conv-BN-ReLU` 结构，完全消除了多分支带来的显存访问成本和计算冗余。

```python
class MobileOneBlock(nn.Module):
    def __init__(self, ...):
        # ...
        if inference_mode:
            # 推理模式：只定义一个卷积层
            self.reparam_conv = nn.Conv2d(...)
        else:
            # 训练模式：定义多分支
            # 1. Skip Branch (Identity + BN)
            self.rbr_skip = nn.BatchNorm2d(...) if ... else None
            # 2. Conv Branches (Over-parameterized)
            self.rbr_conv = nn.ModuleList([...])
            # 3. Scale Branch (1x1 Conv)
            self.rbr_scale = self._conv_bn(kernel_size=1, ...)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # 推理模式：单层卷积
        if self.inference_mode:
            return self.activation(self.se(self.reparam_conv(x)))

        # 训练模式：多分支输出相加
        # Result = Skip(x) + Scale(x) + Conv_Branches(x)
        identity_out = self.rbr_skip(x) if self.rbr_skip is not None else 0
        scale_out = self.rbr_scale(x) if self.rbr_scale is not None else 0
        out = scale_out + identity_out
        for ix in range(self.num_conv_branches):
            out += self.rbr_conv[ix](x)
        return self.activation(self.se(out))

    def reparameterize(self):
        # 将多分支参数融合，切换为推理模式
        kernel, bias = self._get_kernel_bias()
        self.reparam_conv = nn.Conv2d(...)
        self.reparam_conv.weight.data = kernel
        self.reparam_conv.bias.data = bias
        self.inference_mode = True
```

## II. MobileOne 重参数化总结
**(1) 原结构：conv + bn**

$$\begin{align*} 
& \mathbf{y_1}  = \mathbf{Wx} \\ 
& \mathbf{y}  = \frac{(\mathbf{y_1} - \mu_{\text{running}})}{\sqrt{\sigma_{\text{running}}^2 + \epsilon}} \cdot \gamma + \beta \Rightarrow \\
& \mathbf{y} = \mathbf{Wx} \cdot \frac{\gamma}{\sqrt{\sigma_{\text{running}}^2 + \epsilon}} - \mu_{\text{running}} \cdot \frac{\gamma}{\sqrt{\sigma_{\text{running}}^2 + \epsilon}} + \beta \\
\end{align*}$$

**(2) 合并后**
我们记：$\sigma^{\prime} = \sqrt{\sigma_{\text{running}}^2 + \epsilon}$，则：
  
$$\mathbf{y} = \mathbf{\frac{W}{\sigma^{\prime}}x}+\beta-\mu_{\text{running}} \cdot \frac{\gamma}{\sigma^{\prime}}$$

即：合并为：Conv_weight, Conv_bias

核心函数：（来自 MobileOneBlock）
```python
def _fuse_bn_tensor(self, branch) -> Tuple[torch.Tensor, torch.Tensor]:
    """ 分支融合原子操作：将 (Conv+BN) 或 (BN) 融合为 (Conv_weight, Conv_bias)。
    
    原理：
    BN 公式: y = (x - mean) / sqrt(var + eps) * gamma + beta
    卷积公式: y = Wx 
    融合后: y = (W * gamma / std) * x + (beta - mean * gamma / std)
    
    :param branch: 输入分支，可能是 nn.Sequential(Conv, BN) 或者单独的 nn.BatchNorm2d
    """
    if isinstance(branch, nn.Sequential):
        # Case 1: 分支是 Conv + BN
        # 为什么是 .conv 和 .bn？详见本类的辅助函数 .conv_bn 的命名约定
        kernel = branch.conv.weight
        running_mean = branch.bn.running_mean
        running_var = branch.bn.running_var
        gamma = branch.bn.weight
        beta = branch.bn.bias
        eps = branch.bn.eps
    else:
        # Case 2: 分支只有 BN (Skip Connection)
        assert isinstance(branch, nn.BatchNorm2d)
        if not hasattr(self, 'id_tensor'):
            # 构造一个恒等映射卷积核（Identity Kernel）
            # 这是一个 KxK 的卷积核，除了中心点是 1，其余都是 0
            input_dim = self.in_channels // self.groups
            # 这是考虑了 分组卷积 (Group Convolution) 的情况。
            # 如果是标准卷积，则self.groups = 1, 每个卷积核的深度等于输入通道数self.in_channels；如果是DWConv，则self.groups = self.in_channels, 每个卷积核的深度为1。
            kernel_value = torch.zeros((self.in_channels,
                                        # 按道理这里应该是self.out_channels，但是对应 Case 2: 分支只有 BN (Skip Connection)，这是恒等映射，self.in_channels == self.out_channels
                                        input_dim,
                                        self.kernel_size,
                                        self.kernel_size),
                                        dtype=branch.weight.dtype,
                                        device=branch.weight.device)
            # 构建了一个标准的 PyTorch 卷积权重容器，形状为：()[out_channels, in_channels/groups, K, K]，初始值全为0
            # 如果是标准卷积，则 input_dim = self.in_channels；对应标准卷积的卷积核需要处理所有通道；如果是 DWConv，则 input_dim = 1；对应 DWConv 的卷积核每个只处理一个通道。
            for i in range(self.in_channels):
                # 按道理这里应该是self.out_channels，但是对应 Case 2: 分支只有 BN (Skip Connection)，这是恒等映射，self.in_channels == self.out_channels
                kernel_value[i, i % input_dim,
                                self.kernel_size // 2,
                                self.kernel_size // 2] = 1
                # 让卷积核中间的值为0
                # 如果是标准卷积，input_dim = self.in_channels, 则 i % input_dim = i，即每隔通道的[self.kernel_size // 2, self.kernel_size // 2]位置为1
                # 如果是 DWConv，input_dim = 1, 则 i % input_dim = 0，即只有每个卷积核的第0个输入通道的[self.kernel_size // 2, self.kernel_size // 2]位置为1
            self.id_tensor = kernel_value
        kernel = self.id_tensor
        running_mean = branch.running_mean
        running_var = branch.running_var
        gamma = branch.weight
        beta = branch.bias
        eps = branch.eps
        
    # 融合公式实现
    std = (running_var + eps).sqrt()
    # t = gamma / std
    t = (gamma / std).reshape(-1, 1, 1, 1) # reshape 以支持广播乘法
    
    # 新 Weight = 旧 Weight * (gamma / std)
    # 新 Bias = beta - mean * (gamma / std)
    return kernel * t, beta - running_mean * gamma / std
```