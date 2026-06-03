# Programming Model

## I. Programming Model Overview

### 1.1 History

- 2001/2002, researchers see GPU as data parallel coprocessor, the GPGPU field is born 
- 2007, NVIDIA releases CUDA
    - CUDA – Compute Uniform Device Architecture
    - GPU shifts to GPGPU for computing
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

## II. NVIDIA Programming Model: CUDA

### 2.1 Computing Model

