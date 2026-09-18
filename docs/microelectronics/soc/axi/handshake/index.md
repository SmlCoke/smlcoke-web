# AXI 握手协议详解

AXI 的握手协议本质上是一个非常经典的 **valid-ready 双向握手机制**。

它的核心思想是：

> 发送方用 `VALID` 表示"我这里有有效信息"；
> 接收方用 `READY` 表示"我现在可以接收"；
> 当 `VALID && READY` 在同一个时钟上升沿同时为 1 时，传输真正发生。

这个规则贯穿 AXI 的所有通道。

---

## I. AXI 为什么要用握手协议？

AXI 是 AMBA 总线协议族中的高性能总线协议，常用于 CPU、DMA、GPU、NPU、Memory Controller、片上互联 NoC/Interconnect 等模块之间的数据传输。

在 SoC 中，不同模块的速度可能不同：

```text
CPU 可能很快
Memory Controller 可能较慢
DMA 可能突发传输
Interconnect 可能有仲裁和拥塞
```

如果没有握手机制，发送方一旦发数据，接收方必须立刻接住，这会让系统非常脆弱。

AXI 用 `VALID/READY` 解决这个问题：

```text
发送方准备好数据 → 拉高 VALID
接收方能接收数据 → 拉高 READY
两者同时为 1 → 当前拍完成传输
```

所以 AXI 天然支持 **背压 back-pressure**。

---

## II. AXI 握手的最基本规则

AXI 的每个通道都有一组类似的握手信号：

```verilog
VALID
READY
payload
```

例如写地址通道：

```verilog
AWVALID
AWREADY
AWADDR
AWLEN
AWSIZE
AWBURST
```

写数据通道：

```verilog
WVALID
WREADY
WDATA
WSTRB
WLAST
```

读数据通道：

```verilog
RVALID
RREADY
RDATA
RRESP
RLAST
```

其中：

| 信号        | 方向      | 含义          |
| --------- | ------- | ----------- |
| `VALID`   | 发送方向接收方 | 当前通道上的信息有效  |
| `READY`   | 接收方向发送方 | 当前通道可以接收    |
| `payload` | 发送方向接收方 | 地址、数据、控制信息等 |

传输发生的条件永远是：

```verilog
fire = VALID && READY;
```

也常写成：

```verilog
handshake = xVALID && xREADY;
```

---

## III. 最重要的握手时序规则

### 3.1 规则一：发送方 `VALID` 不能依赖接收方的 `READY`

这是 AXI 握手中最重要的一条。

发送方如果有数据要发，就应该拉高 `VALID`，不能等到看到 `READY` 之后才拉高 `VALID`。

错误写法类似：

```verilog
if (ready)
    valid <= 1'b1;
```

这很危险，因为接收方也可能在等 `VALID` 才拉高 `READY`，于是双方互相等待，产生死锁。

正确思路是：

```verilog
if (has_data)
    valid <= 1'b1;
```

也就是说：

```text
VALID 表示“我有东西要给你”
READY 表示“我能接收”
```

发送方不能说：

```text
你先 READY，我才 VALID
```

否则可能死锁。

---

### 3.2 规则二：接收方 `READY` 可以依赖 `VALID`，也可以提前准备好

接收方是否拉高 `READY`，可以根据自己的状态决定。

例如：

```verilog
assign ready = fifo_not_full;
```

或者：

```verilog
assign ready = valid && buffer_available;
```

这通常是允许的。

也就是说：

```text
发送方 VALID 不能等 READY
接收方 READY 可以等 VALID，也可以提前准备好
```

原因是 AXI 要保证只要发送方有东西，就会主动表达出来；接收方可以根据是否真的有人发送，再决定是否接收。

---

### 3.3 规则三：`VALID` 拉高后，在握手完成前必须保持为 1

假设发送方某一拍拉高了 `VALID`，但是接收方 `READY = 0`，这说明接收方暂时无法接收。

此时发送方不能随便撤掉 `VALID`。

必须保持：

```text
VALID = 1
payload 保持稳定
```

直到某个时钟上升沿出现：

```verilog
VALID && READY == 1
```

传输完成后，发送方才可以撤掉 `VALID` 或者切换到下一笔传输。

---

### 3.4 规则四：`VALID=1 && READY=0` 时，payload 必须保持不变

这条非常重要。

例如写数据通道：

```text
WVALID = 1
WREADY = 0
WDATA  = 0x1234
```

如果下一拍 `WREADY` 仍然为 0，那么 `WDATA` 必须仍然是 `0x1234`。

不能变成：

```text
WDATA = 0x5678
```

因为接收方还没有接收上一笔数据。

所以当：

```verilog
VALID && !READY
```

时，发送方必须保持所有 payload 信号稳定。

---

### 3.5 规则五：只有 `VALID && READY` 同时为 1 的那个时钟沿才算传输成功

比如：

```text
Cycle 1: VALID=1, READY=0  → 没传输
Cycle 2: VALID=1, READY=0  → 没传输
Cycle 3: VALID=1, READY=1  → 传输发生
```

只有 Cycle 3 的时钟上升沿，接收方才真正采样 payload。

---

## IV. AXI 的五个独立通道

AXI 最经典的特点是：**读写分离，地址和数据分离，响应独立**。

AXI4 Full 有五个通道：

| 通道 | 名称                     | 方向             | 作用      |
| -- | ---------------------- | -------------- | ------- |
| AW | Write Address Channel  | Master → Slave | 写地址     |
| W  | Write Data Channel     | Master → Slave | 写数据     |
| B  | Write Response Channel | Slave → Master | 写响应     |
| AR | Read Address Channel   | Master → Slave | 读地址     |
| R  | Read Data Channel      | Slave → Master | 读数据和读响应 |

每个通道都有自己的 `VALID/READY` 握手。

```text
AW: AWVALID / AWREADY
W : WVALID  / WREADY
B : BVALID  / BREADY
AR: ARVALID / ARREADY
R : RVALID  / RREADY
```

这五个通道相互独立，可以并行工作。

---

## V. 写事务的握手过程

AXI 写事务涉及三个通道：

```text
AW 通道：发送写地址
W  通道：发送写数据
B  通道：返回写响应
```

整体流程如下：

```text
Master                  Slave
  |                       |
  | ---- AWADDR --------> |  写地址
  | ---- WDATA ---------> |  写数据
  | <---- BRESP --------- |  写响应
  |                       |
```

但是在 AXI 中，写地址和写数据是两个独立通道，它们的握手可以独立发生。

---

### 5.1 写地址通道 AW

AW 通道负责传输写地址和控制信息，例如：

```verilog
AWADDR   // 写起始地址
AWLEN    // burst 长度
AWSIZE   // 每拍传输字节数
AWBURST  // burst 类型
AWVALID
AWREADY
```

握手条件：

```verilog
AWVALID && AWREADY
```

当握手成功时，Slave 接收写地址信息。

示意：

```text
Cycle:    1   2   3   4
AWVALID:  1   1   1   0
AWREADY:  0   0   1   x
AWADDR:   A   A   A   x
                 ↑
            地址在这里被接收
```

在 Cycle 1 和 Cycle 2 中，因为 `AWREADY=0`，所以地址不能变化。

---

### 5.2 写数据通道 W

W 通道负责传输写数据：

```verilog
WDATA
WSTRB
WLAST
WVALID
WREADY
```

握手条件：

```verilog
WVALID && WREADY
```

如果是 burst 写传输，W 通道可能有多拍数据。

例如 `AWLEN = 3` 表示总共 4 拍数据，因为 AXI 中：

```text
burst beat 数量 = AWLEN + 1
```

假设一次 4-beat burst 写：

```text
Beat 0
Beat 1
Beat 2
Beat 3, WLAST=1
```

时序可能是：

```text
Cycle:    1   2   3   4   5   6
WVALID:   1   1   1   1   1   1
WREADY:   1   0   1   1   0   1
WDATA:    D0  D1  D1  D2  D3  D3
WLAST:    0   0   0   0   1   1
          ↑       ↑   ↑       ↑
        Beat0   Beat1 Beat2  Beat3
```

注意：

在 Cycle 2，`WVALID=1` 但 `WREADY=0`，所以 `D1` 没有被接收。

因此 Cycle 3 仍然必须保持 `D1`。

同理，Cycle 5 中 `D3` 也没有被接收，所以 Cycle 6 仍然保持 `D3` 和 `WLAST=1`。

---

### 5.3 写响应通道 B

当 Slave 完成写操作后，会通过 B 通道返回响应：

```verilog
BRESP
BVALID
BREADY
```

其中 `BRESP` 常见取值有：

| BRESP    | 含义                  |
| -------- | ------------------- |
| `OKAY`   | 正常完成                |
| `EXOKAY` | 独占访问成功，AXI4 一般较少用   |
| `SLVERR` | Slave 错误            |
| `DECERR` | Decode error，地址译码错误 |

B 通道方向是：

```text
Slave → Master
```

所以：

```text
Slave 拉高 BVALID
Master 拉高 BREADY
```

握手条件：

```verilog
BVALID && BREADY
```

写事务只有在 B 通道响应握手完成后，才算完整结束。

---

## VI. 写地址和写数据谁先到？

这是 AXI 中很容易混淆的一点。

AXI 允许：

```text
AW 先到，W 后到
W 先到，AW 后到
AW 和 W 同时到
```

因为 AW 和 W 是独立通道。

例如：

### 6.1 情况一：AW 先于 W

```text
Cycle:     1   2   3   4
AW fire:   1
W fire:            1   1 ...
```

Slave 先收到写地址，再收到写数据。

---

### 6.2 情况二：W 先于 AW

```text
Cycle:     1   2   3   4
W fire:    1   1
AW fire:           1
```

Slave 先收到写数据，再收到写地址。

这意味着 Slave 或 Interconnect 可能需要 buffer 来暂存先到的数据。

---

### 6.3 情况三：AW 和 W 同时发生

```text
Cycle:     1   2   3
AW fire:   1
W fire:    1   1   ...
```

这种情况性能最好。

---

## VII. 一个完整 AXI 写事务例子

假设 Master 要写 4 个 beat：

```text
地址：0x1000
每 beat：32 bit
burst 长度：4 beat
```

那么 AW 通道：

```text
AWADDR  = 0x1000
AWLEN   = 3
AWSIZE  = 2
AWBURST = INCR
```

其中：

```text
AWSIZE = 2 表示每 beat 传输 2^2 = 4 bytes
AWLEN = 3 表示 3 + 1 = 4 beats
```

写数据：

```text
WDATA beat0
WDATA beat1
WDATA beat2
WDATA beat3, WLAST=1
```

完整事务：

```text
Master                                 Slave

AWVALID=1, AWADDR=0x1000  ---------->
                    AWREADY=1 <------
AW 握手完成

WVALID=1, WDATA=D0        ---------->
                    WREADY=1 <------
Beat 0 完成

WVALID=1, WDATA=D1        ---------->
                    WREADY=1 <------
Beat 1 完成

WVALID=1, WDATA=D2        ---------->
                    WREADY=1 <------
Beat 2 完成

WVALID=1, WDATA=D3,
WLAST=1                  ---------->
                    WREADY=1 <------
Beat 3 完成

                    BVALID=1,
                    BRESP=OKAY <----
BREADY=1                 ---------->
B 握手完成，写事务结束
```

---

## VIII. 读事务的握手过程

AXI 读事务涉及两个通道：

```text
AR 通道：发送读地址
R  通道：返回读数据和读响应
```

整体流程：

```text
Master                  Slave
  |                       |
  | ---- ARADDR --------> |  读地址
  | <---- RDATA --------- |  读数据
  |                       |
```

---

### 8.1 读地址通道 AR

AR 通道类似 AW 通道，负责传输读地址和控制信息：

```verilog
ARADDR
ARLEN
ARSIZE
ARBURST
ARVALID
ARREADY
```

握手条件：

```verilog
ARVALID && ARREADY
```

当握手成功后，Slave 接收读请求。

---

### 8.2 读数据通道 R

Slave 根据 AR 请求返回数据：

```verilog
RDATA
RRESP
RLAST
RVALID
RREADY
```

方向是：

```text
Slave → Master
```

所以：

```text
Slave 拉高 RVALID
Master 拉高 RREADY
```

握手条件：

```verilog
RVALID && RREADY
```

如果是 burst 读，R 通道也会返回多拍数据。

最后一拍通过 `RLAST=1` 标记。

---

## IX. 一个完整 AXI 读事务例子

假设 Master 从地址 `0x2000` 读取 4 个 beat：

```text
ARADDR  = 0x2000
ARLEN   = 3
ARSIZE  = 2
ARBURST = INCR
```

事务如下：

```text
Master                                 Slave

ARVALID=1, ARADDR=0x2000  ---------->
                    ARREADY=1 <------
AR 握手完成

                    RVALID=1,
                    RDATA=D0,
                    RLAST=0 <--------
RREADY=1                  ---------->
Beat 0 完成

                    RVALID=1,
                    RDATA=D1,
                    RLAST=0 <--------
RREADY=1                  ---------->
Beat 1 完成

                    RVALID=1,
                    RDATA=D2,
                    RLAST=0 <--------
RREADY=1                  ---------->
Beat 2 完成

                    RVALID=1,
                    RDATA=D3,
                    RLAST=1 <--------
RREADY=1                  ---------->
Beat 3 完成，读事务结束
```

读事务没有单独的响应通道，读响应 `RRESP` 和读数据 `RDATA` 一起返回。

---

## X. AXI 握手与流水线的关系

AXI 的 `VALID/READY` 很适合流水线设计。

如果接收方一直 `READY=1`，发送方也一直 `VALID=1`，那么每个周期都能传输一拍数据。

```text
Cycle:   1   2   3   4   5
VALID:   1   1   1   1   1
READY:   1   1   1   1   1
DATA:    D0  D1  D2  D3  D4
         ↑   ↑   ↑   ↑   ↑
       每周期传输一拍
```

这就是满吞吐率：

```text
1 beat / cycle
```

如果中间有 back-pressure：

```text
Cycle:   1   2   3   4   5
VALID:   1   1   1   1   1
READY:   1   0   1   0   1
DATA:    D0  D1  D1  D2  D2
         ↑       ↑       ↑
```

只有 `VALID && READY` 的周期才真正传输。

---

## XI. AXI 中 Master 和 Slave 的职责

以写事务为例：

| 通道 | 发送方    | 接收方    | VALID 谁拉？ | READY 谁拉？ |
| -- | ------ | ------ | --------- | --------- |
| AW | Master | Slave  | Master    | Slave     |
| W  | Master | Slave  | Master    | Slave     |
| B  | Slave  | Master | Slave     | Master    |

以读事务为例：

| 通道 | 发送方    | 接收方    | VALID 谁拉？ | READY 谁拉？ |
| -- | ------ | ------ | --------- | --------- |
| AR | Master | Slave  | Master    | Slave     |
| R  | Slave  | Master | Slave     | Master    |

总结：

```text
谁提供 payload，谁拉 VALID
谁接收 payload，谁拉 READY
```

这是判断 AXI 信号方向的最简单方法。

---

## XII. AXI 握手中的常见错误

### 12.1 错误一：`VALID` 等待 `READY`

错误：

```verilog
always_ff @(posedge clk) begin
    if (ready)
        valid <= 1'b1;
end
```

问题是如果接收方也在等待 `valid`，系统会死锁。

正确：

```verilog
always_ff @(posedge clk) begin
    if (reset)
        valid <= 1'b0;
    else if (has_data)
        valid <= 1'b1;
    else if (valid && ready)
        valid <= 1'b0;
end
```

---

### 12.2 错误二：`VALID=1 && READY=0` 时改变数据

错误：

```text
Cycle 1: VALID=1, READY=0, DATA=D0
Cycle 2: VALID=1, READY=0, DATA=D1
```

这是错误的，因为 D0 还没有被接收。

正确：

```text
Cycle 1: VALID=1, READY=0, DATA=D0
Cycle 2: VALID=1, READY=0, DATA=D0
Cycle 3: VALID=1, READY=1, DATA=D0  → 传输完成
```

---

### 12.3 错误三：忘记处理 `LAST`

对于 burst 传输，最后一拍必须标记：

```text
写数据最后一拍：WLAST = 1
读数据最后一拍：RLAST = 1
```

否则接收方不知道 burst 什么时候结束。

---

### 12.4 错误四：认为 AW 和 W 必须同时握手

AXI 中 AW 和 W 是独立通道。

所以不能写出这种强绑定逻辑：

```verilog
AWREADY = WREADY;
WREADY  = AWREADY;
```

这类逻辑容易造成性能下降甚至死锁。

正确设计中，AW 和 W 通道应尽量独立处理，必要时通过 FIFO 或 buffer 对齐地址和数据。

---

## XIII. AXI 握手协议和 APB/AHB 的区别

你前面已经学习了 APB、AHB，可以这样对比：

| 协议  | 特点                  |
| --- | ------------------- |
| APB | 简单、低速、非流水，适合寄存器访问   |
| AHB | 单地址通道，流水化地址和数据阶段    |
| AXI | 多独立通道，读写分离，支持乱序和高吞吐 |

AXI 的握手比 APB/AHB 更灵活。

APB 更像：

```text
一次访问一步步完成
setup phase → enable phase
```

AHB 更像：

```text
地址阶段和数据阶段流水重叠
```

AXI 更像：

```text
地址、数据、响应全部拆成独立通道
每个通道都有自己的 valid-ready 握手
```

所以 AXI 更适合高性能 SoC。

---

## XIV. 用一句话理解 AXI 握手

可以把 AXI 握手想象成两个人递东西：

```text
VALID：我手上有东西，伸出来了
READY：我准备好接了
VALID && READY：东西交接成功
```

如果对方还没准备好：

```text
VALID=1, READY=0
```

那发送方必须一直拿着同一个东西，不能换。

如果自己还没有东西：

```text
VALID=0
```

就不能让对方误以为当前数据有效。

---

## XV. RTL 设计中推荐的思维模板

你写 AXI 相关 RTL 时，建议每个通道都先抽象成这种结构：

```verilog
wire fire = valid && ready;
```

然后所有状态更新都围绕 `fire` 进行。

例如发送端：

```verilog
always_ff @(posedge clk) begin
    if (rst) begin
        valid <= 1'b0;
    end else begin
        if (!valid || ready) begin
            if (has_next_payload) begin
                valid   <= 1'b1;
                payload <= next_payload;
            end else begin
                valid <= 1'b0;
            end
        end
    end
end
```

这段逻辑的关键是：

```verilog
if (!valid || ready)
```

它的含义是：

```text
当前没有未完成传输，或者当前传输已经被接收
```

只有这时才允许更新 payload。

如果：

```verilog
valid && !ready
```

说明当前 payload 还没被接收，必须保持不变。

---

## XVI. AXI 握手最核心的总结

你只需要牢牢记住以下几条：

```text
1. VALID 表示发送方有有效信息。
2. READY 表示接收方可以接收信息。
3. VALID && READY 同时为 1 的时钟沿，传输发生。
4. VALID 一旦拉高，在握手前不能随便撤销。
5. VALID=1 且 READY=0 时，payload 必须保持稳定。
6. VALID 不能依赖 READY，否则可能死锁。
7. READY 可以依赖 VALID。
8. AXI 的五个通道各自独立握手。
9. 写事务：AW + W + B。
10. 读事务：AR + R。
```

对于 AXI，真正重要的不是死记信号，而是形成这个模型：

```text
每一个 AXI 通道都是一个独立的 valid-ready 流接口。
地址是一条流，写数据是一条流，写响应是一条流，读地址是一条流，读数据也是一条流。
```

掌握了这一点，后面理解 AXI burst、outstanding transaction、ID、乱序返回、interconnect、DMA 设计都会顺畅很多。
