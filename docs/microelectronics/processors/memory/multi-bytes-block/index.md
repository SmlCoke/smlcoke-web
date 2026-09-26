### 1. 读操作：我只要一杯水，你却给我端来一整锅？

假设一个 Cache Block 是 16 个字节（4 个 Word）。CPU 执行了一条指令：`LDR R1, [地址]`，只想读其中的第 2 个 Word。

*   **如果 Hit（命中）**：
    Cache 确实是一次性把整个 Block（4 个 Word）都从 SRAM 阵列里读出来了。但是，CPU 怎么只拿到它想要的那个 Word 呢？
    这时候，地址里的 **Offset（偏移位）** 就发挥作用了！硬件里会有一个 **多路选择器（Multiplexer, MUX）**。Offset 就连在这个 MUX 的控制端上。虽然 Cache 吐出了 4 个 Word，但 MUX 根据 Offset，精准地“掐头去尾”，只把第 2 个 Word 挑选出来，顺着数据总线送给 CPU。
*   **如果 Miss（缺失）**：
    Cache 会向主存大喊：“给我把包含这个 Word 的**整个 16 字节的 Block** 都搬过来！”等整个 Block 搬进 Cache 后，再像上面那样，用 MUX 把那个 Word 挑出来给 CPU。
    *（顺带一提，PPT 第 12 页提到的 Critical-word-first 优化，就是主存先把 CPU 急需的那个 Word 传过来让 CPU 先跑，剩下 3 个 Word 随后再悄悄补齐。）*

---

### 2. 写操作：这才是真正的“大坑” (Read-Modify-Write)

读操作大不了就是浪费点取出来的数据，但写操作如果不小心，就会**破坏数据**。假设 CPU 执行 `STR R1, [地址]`，要把寄存器里的一个新 Word 写入 Cache，但只改这个 Block 里的第 2 个 Word。

*   **如果 Write Hit（写命中）**：
    Cache 里的这 16 个字节本来是好好的。现在我只想改其中 4 个字节，绝对不能把另外 12 个字节给覆盖掉。
    你在学 SRAM 结构时应该学过，SRAM 阵列除了有读写使能，通常还有 **Byte Enable（字节使能）** 信号或者 **Write Mask（写掩码）**。硬件会根据 Offset 生成对应的掩码信号，告诉 SRAM：“这次写入，你只准打开第 2 个 Word 对应的存储单元的‘大门’，其他单元的门给我锁死！”这样就实现了部分更新。

*   **如果 Write Miss（写缺失）+ Write-Allocate（写分配）**：
    **这是体系结构中最精妙、也是最容易错的地方！**
    你设想一下，既然 Cache 里没有这个 Block，我能不能直接在 Cache 里找个空位，把 CPU 给我的这个新 Word 写进去，然后把 Valid 设为 1，Dirty 设为 1？
    **绝对不行！**
    为什么？因为一个 Block 是 16 字节，你只填了 4 字节的有效数据，那剩下 12 字节是什么？是上一次残留的**随机垃圾数据**！如果以后 CPU 去读这另外 12 字节，就会读到乱码；如果这个脏块以后被写回（Write-Back）主存，这些垃圾数据就会把主存里原本正确的数据给**摧毁**！

    **所以，真正的解法是（Read-Modify-Write）：**

    1.  **Read（读）**：Cache 必须先委屈一下，去主存把这**整个旧的 16 字节 Block** 原封不动地捞上来。
    2.  **Modify（改）**：等这个旧 Block 完整地躺在 Cache 里了，再利用 Offset 和掩码机制，把 CPU 给的那个新 Word 覆盖到特定位置。
    3.  **Write（写）**：标记 Dirty = 1。大功告成！

这就是为什么 PPT 第 13 页说“Cache write: More complicate and takes longer than reads”。写确实比读麻烦太多了！

---

**一句话总结：**
面对部分数据的读写，硬件的法宝就是 **Offset 驱动的多路选择器（读）** 和 **掩码/字节使能电路（写）**。尤其在 Write Miss 时，必须先老老实实把整个块从主存搬过来填满 Cache，才能在上面做局部修改，这叫做 **读-改-写 (Read-Modify-Write)** 机制。

这个底层逻辑通透了吗？能把你之前学过的 SRAM 接口信号（比如掩码）和架构设计完美闭环！