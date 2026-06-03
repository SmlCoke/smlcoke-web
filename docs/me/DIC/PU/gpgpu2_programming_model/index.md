# Programming Model

## I. Programming Model Overview

### 1.1 History

- 2001/2002, researchers see GPU as data parallel coprocessor, the GPGPU field is born 
- 2007, NVIDIA releases CUDA
    - CUDA – Compute Unified Device Architecture
    - 统一计算设备架构
    - GPU shifts to GPGPU for computing
    - Graphics 编程 → General-Purpose 编程
- 2008, Khronos releases OpenCL specification

### 1.2 GPGPU Programming Model

一个编程模型应该包含：

- How to compute the wanted function
- 如何组织 memory 为计算服务
- How to map the function to the real hardware

此外，对于并行架构，尤其重要的是：

- How to divide the workload（如何划分工作量） 
- How to communicate between the divided work（如何在划分的工作之间进行通信）
- How to synchronize the divided work（如何同步划分的工作）

也就是说，GPGPU programming model 要能说明：在每一个时刻，每个 SM 中的每个 CUDA Core 应该做什么。

## II. NVIDIA Programming Model: CUDA

### 2.1 Computing Model

CUDA 使用的是**异构计算**（heterogeneous computing）模型：程序员写出的 GPGPU 应用程序会被分成两类代码：

- **Host code**：运行在 CPU 上的主机端代码
- **Device code**：运行在 GPGPU 上的设备端代码

从程序员视角看，一次典型 CUDA 执行流程如下：

- CPU 先把 processing data 从 main memory 拷贝到 GPU memory
- CPU 发出指令，告诉 GPU 要执行什么并行计算
- GPU 在多个 core 上并行执行
- 计算结果再从 GPU memory 拷回 main memory

![CUDA processing flow](./assets/cuda-processing-flow.webp)

CPU 通过 kernel 来调用 GPU。kernel 在 CUDA 的线程层级中也可以理解为一个 thread grid：

- `CPU: __host__`：指定代码在 CPU 上做
- `CUDA: __global__`：定义从 host 启动、在 device 上执行的 kernel
- `CUDA: __device__`：定义在 device 端调用、在 GPU 上执行的函数

注意，逻辑执行与 GPU 硬件的映射关系是：

- `kernel (grid)`(线程网格) $\rightarrow$ GPU
- `thread block`(线程块) $\rightarrow$ SM
- `thread`(线程) $\rightarrow$ SP / CUDA Core（逻辑对应，实际执行以 `warp` (线程束) 为调度单位）

kernel launch 的基本写法是：

```cpp
Name<<<dimGrid, dimBlock>>>(... parameters ...);
```

其中：

- `dimGrid`：**一个 grid 里有多少个 thread block**
- `dimBlock`：**一个 thread block 里分配多少个 thread**

例如向量逐元素相乘：

```cpp
// A = B * C, 8192 = 16 * 512
vect_mult<<<16, 512>>>(n, a, b, c);
```

这里的含义是：把 8192 个元素划分成 16 个 thread block，每个 thread block 有 512 个 thread。也可以换成其他满足总线程数需求的配置（例如手写标注中写到的 `8 x 1024`），但实际可行的 `dimBlock` 会受硬件最大线程数、寄存器、shared memory 等资源限制。

### 2.2 Thread Model

#### 2.2.1 Thread Hierarchy

CUDA 的线程层级是：

- Grid：线程网格
- Thread block：线程块
- Thread：线程

对应到程序里的内置变量：

- `gridDim(x, y, z)`：一个 grid 中 block 的**维度**，也就是“一个 grid 有几个 block, $x,y,z$的 范围是多少”
- `blockDim(x, y, z)`：一个 block 中 thread 的**维度**，也就是“**一个 block 有几个 thread, $x,y,z$的 范围是多少**”
- `blockIdx(x, y, z)`：当前 thread 所在 block 的编号，也就是“**当前 thread 在 grid 中的 block 编号**”
- `threadIdx(x, y, z)`：**当前 thread 在 block 内部的本地编号**

#### 2.2.2 Example

##### Example 1: 数组元素按照线程分配

如果只看一维数组（即假设所有层次均是一维网格），最常用的全局下标计算方式是：

```cpp
int index = threadIdx.x + blockIdx.x * blockDim.x;
```

这句话可以拆成：

- `blockIdx.x * blockDim.x`：前面已经经过了多少个完整 block
- `threadIdx.x`：当前 thread 在本 block 内的本地编号
- 两者相加得到当前 thread 对应的一维全局下标



![alt text](./assets/array_example.webp)

```cpp
__global__ void kernel1(int* A) {
    int index = threadIdx.x + blockIdx.x * blockDim.x;
    A[index] = index;
}
// kernel1 结果：0 1 2 3 4 5 6 7 8 9 10 11

__global__ void kernel2(int* A) {
    int index = threadIdx.x + blockIdx.x * blockDim.x;
    A[index] = blockIdx.x;
}
// kernel2 结果：0 0 0 0 1 1 1 1 2 2 2 2

__global__ void kernel3(int* A) {
    int index = threadIdx.x + blockIdx.x * blockDim.x;
    A[index] = threadIdx.x;
}
// kernel3 结果：0 1 2 3 0 1 2 3 0 1 2 3
```

复习时可以这样记：

- `index` 是全局连续编号
- `blockIdx.x` 在同一个 block 内相同
- `threadIdx.x` 在每个 block 内从 0 重新开始

##### Example 2: Vector Multiplication

向量逐元素相乘的例子是：

```cpp
__global__ void vect_mult(int n, double *a, double *b, double *c)
{
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        a[i] = b[i] * c[i];
    }
}
```

host code 调用：

```cpp
vect_mult<<<16, 512>>>(n, a, b, c);
```

这个配置的含义是：

- Grid：8192 elements -> 8192 threads
- 16 thread blocks
- 每个 thread block 有 `8192 / 16 = 512` threads

注意 `if (i < n)` 的含义：如果**元素数不是线程数的整数倍**，例如只有 8191 个元素，但是我们依旧会按照 $16\times 512=8192$ 分配，最后多出来的 thread 会因为这句判断而不访问数组，从而防止越界。

!!! Attention "当硬件资源不够时会发生什么？"
    例如每一个 SM 只有 32个 SP？
    ——需要**时分复用**！
    $512/32 = 16$ warps，因此会构建 16 个 warp(线程束)。每一个时刻独立执行 1 个 warp，其他 warp 处于等待状态，等当前 warp 执行完毕后再切换到下一个 warp。

**Thread mapping to hardware**

![alt text](./assets/thread_mapping_to_hardware.webp)


##### Example 3: Matrix-Vector Addition

课件的第二个 CUDA 例子是矩阵加向量广播：

```cpp
C[i, j] = A[i, j] + B[j]
```

指定划分方式：

- 每个 Thread Block 负责一个 $H\times W = 128\times 32$ 的 tile
- 每个 tile 由 `threadsPerBlock(16, 8)` 个 thread 处理
- 因此：每个 thread 计算 $(32/16) \times (128/8) = 2 \times 16$ 个元素

device code 的关键下标计算是：

```cpp
int row_start = blockIdx.y * blockDim.y * 16 + threadIdx.y * 16;
int col_start = blockIdx.x * blockDim.x * 2 + threadIdx.x * 2;
```

> (1) **拆解**：每一个 thread 处理 16 行数据，`blockDim.y` 是一个 thread block 的 thread 的行数，`blockIdx.y` 是当前 block 在 grid 中的行编号。`blockIdx.y * blockDim.y * 16` 就表示当前 thread block 的**起始行号**，`threadIdx.y * 16` 表示当**前 thread 在 block 内的行偏移**。
> (2) 列的计算同理。

然后每个 thread 用两层循环完成自己的 `[2, 16]` 小块：

```cpp
for (int i = 0; i < 16; ++i) {      // 16 rows
    int row = row_start + i;
    if (row < numRows) {
        for (int j = 0; j < 2; ++j) {   // 2 columns
            int col = col_start + j;
            if (col < numCols) {
                matrix[row * numCols + col] += bias[col];
            }
        }
    }
}
```

这里的 `if (row < numRows)` 和 `if (col < numCols)` 是为了**处理边界情况**：当矩阵的行数或列数不是 128 或 32 的整数倍时，最后一个 tile 会有一些线程对应的**行或列超出矩阵范围**，这些线程就不进行计算。

host code 中的配置是：

```cpp
dim3 threadsPerBlock(16, 8);
dim3 blocksPerGrid((numCols + 31) / 32,
                   (numRows + 127) / 128);

matrixAddBiasLargeTile<<<blocksPerGrid, threadsPerBlock>>>(
    d_matrix, d_bias, numRows, numCols
);
```

这里 `(numCols + 31) / 32` 和 `(numRows + 127) / 128` 是向上取整。例如：如果 `numCols = 63`，应该划分为两列线程块，普通整数除法 `63 / 32 = 1` 会少算一块，但 `(63 + 31) / 32 = 2`，正好覆盖剩余列。

### 2.3 Memory Model

Memory model 的基本思想是：

- Match data requirement
- Reduce accesses to global

也就是：根据数据的访问需求选择合适的存储层次，**尽量减少对 global memory 的访问**。

![CUDA memory model](./assets/memory-model.webp)

当前 CUDA memory model 中常见的类型包括：

- Register file：**寄存器文件，每个 thread 私有**，速度最快，用来放线程内部的临时变量
- Local memory：**局部存储器，每个 thread 私有**；名字叫 local，但物理上通常仍在**设备端全局存储器**中，只是逻辑上属于某个 thread
- Shared memory：**共享存储器，同一 thread block 内线程共享**，位于同一 SM 内部的单独存储空间，<span style="color: green;">并非全局存储器</span>
- L1 data cache：类似之前 RISC-V 处理器中学过的 Cache，由硬件管理
- Global memory：**设备端全局存储器**，所有 thread 都能访问，但**访问代价**高
- Constant memory：**常量存储器**，物理上也在设备端全局存储器中，适合只读常量数据
- Texture memory：**纹理存储器**，物理上也在设备端全局存储器中，有专门的缓存/访问路径

注意关注Shared memory：

- 是 GPGPU 性能调优的重要资源
- 它由**程序员显式控制**，而不是像 cache 一样完全交给硬件
- 它可以服务于同一个 block 内线程之间的数据复用和通信
- 某些架构中，L1 cache 和 shared memory 会共享片上空间，可以动态调整划分；**如果程序员愿意主动优化，就可以把更多片上资源作为 shared memory 使用，从而写出更高性能的 CUDA 程序**


