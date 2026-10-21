# DRAM Structure Organization

## 1. 为什么 DRAM 不是一个大数组？

从软件看来，Memory 是一个类似：

```text
Memory[0]
Memory[1]
Memory[2]
...
```

的一维线性空间。但真实 DRAM 更接近：

```text
Channel
 └── DIMM
      └── Rank
           └── Chip
                └── Bank
                     └── Row
                          └── Column
```