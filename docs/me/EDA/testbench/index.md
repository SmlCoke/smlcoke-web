# Testbench 学习使用笔记

## I. Testbench 语法基础：基于 SystemVerilog

> 注意，该板块介绍 testbench 验证中常用的语法，并且全部基于 SystemVerilog 而非 Verilog。

### 1.1 数据类型

#### 1.1.1 wire/reg $\rightarrow$ logic

SystemVerilog 引入了 **`logic`** 类型。在绝大多数情况下，`logic` 可以完全替代 `wire` 和 `reg`，从而无需像 Verilog 一样担心如下两个问题：

* 什么时候用 `wire`？（答：用 `assign` 赋值，或者连接底层模块输出的时候）
* 什么时候用 `reg`？（答：在 `always` 或 `initial` 块里赋值的时候）

`logic` 是一种改良型的数据类型。SystemVerilog 编译器会自动根据语境选择 `logic` 的语义：如果在 `initial` 或 `always` 块里给它赋值，它表现得像 `reg`（能存储状态）；如果你用 `assign` 给它赋值，或者把它连到被测模块（DUT）的输出端，它表现得像 `wire`。


#### 1.1.2 字符串处理: `string` 类型

在 Verilog 中，如果想存一个字符串（比如文件名），需要定义一个位宽很长的 `reg` 数组（例如 `reg [8*20:1] file_name;`），非常僵硬，一旦名字变长就会截断报错。

**SystemVerilog 的改进：**
引入了原生、动态分配内存的 **`string`** 类型。
同时，引入了**字符串格式化系统函数** **`$sformatf()`**（用法完全等同于 C 语言的 `sprintf`）。

**示例**：

```systemverilog
string file_name;
int    test_id = 5;

file_name = $sformatf("cpu_test_%0d.txt", test_id); 
// 此时 file_name 的内容动态变成了 "cpu_test_5.txt"
```

### 1.2 时间单位（`timescale`）

在 testbench 中，我们需要用到延时语句，比如 `#5;`。这个 `5` 到底代表多少时间？这就取决于 ``timescale`。这也是工业界极其重视的规范，不写规范会导致多个模块联合仿真时时间错乱。

语法格式：

```systemverilog
`timescale <时间单位> / <时间精度>
```

* **时间单位 (Time Unit)**：决定了 `#数字` 代表的实际物理时间。
* **时间精度 (Time Precision)**：决定了仿真器内部计算时间时的最小刻度（舍入误差），也决定了波形图里能看到的最小时间分辨率。

**示例：** 假设 ``timescale 1ns / 1ps`

* 当写 `#5` 时，因为“时间单位”是 1ns，所以延时了 5ns。
* 当写 `#1.2345` 时，因为“时间精度”是 1ps (也就是 0.001ns)，仿真器会保留到小数点后三位，把延时处理为 `1.235ns` (四舍五入)。

Testbench 中，通常将 ``timescale 1ns / 1ps` 写在所有的 TB 文件第一行顶格写上，这属于预编译指令，不受模块边界限制，必须写在 `module` 外面。

### 1.3 文件读写

#### 1.3.1 文件读的系统任务

文件读写非常像 C 语言。在 SystemVerilog 中，我们需要一个**文件句柄（File Descriptor）**来记录打开的文件。它的类型用标准的 `int` 即可。

**相关的系统任务：**

* **`$fopen("路径", "模式")`**：打开文件并返回句柄。路径格式为 `string`, 模式有 `"r"`(读)、`"w"`(写)、`"a"`(追加)。如果打开失败，会返回 `0`。
* **`$fclose(句柄)`**：关闭文件。读写完一定要关闭，否则会造成内存泄漏。
* **`$feof(句柄)`**：判断是否到达文件末尾（End Of File）。如果没有到末尾返回 0，到了末尾返回非 0。

**格式化读取：整数变量 = $fscanf(文件句柄, "格式", 变量1, 变量2...);**

**原理剖析：**
`$fscanf` 是有返回值的！它返回的是 **“成功匹配读取的变量个数”**。
假设你的 `.txt` 文件格式是每一行两个 32 位的十六进制数：
`00000033  00000000`  *(比如左边是机器码，右边是预期的 ALU 结果)*
你用 `$fscanf(fd, "%h %h", inst, gold)` 读取：

* 如果这行成功读到了两个数，它返回 `2`。
* 如果这行只有空格或换行，或者遇到奇怪的字符，它可能返回 `0` 或 `-1`。

**工程规范：一定要判断返回值是否等于你期望的数量**，这样可以过滤掉文件末尾的空行，防止读入未知的 `X` 态（不定态）。

#### 1.3.2 特殊：内存读入

Verilog 还提供了一个专门给 Memory 一次性读入全部数据的系统任务：

* `$readmemh("代码.txt", 存储器数组名)`：读取十六进制文件。
* `$readmemb("代码.txt", 存储器数组名)`：读取二进制文件。
* **区别**：`$fscanf` 主要用于 Testbench 控制端，带时间延迟一行行读入和校验数据；而 `$readmemh` 主要用于零时间开销直接把整个 `.txt` 的文件内容拷贝进 Memory 模块内部阵列中。这两个系统任务在验证使用了 Memory 的设计时会经常使用。

#### 1.3.3 文件写的系统任务

与读取文件类似，写文件也需要获取一个文件句柄（File Descriptor），区别仅在于 `$fopen` 时传入的模式不同，以及使用专门的写入函数。

`$fopen` 函数有两个专用于写文件的模式：

* **`"w"` (Write 模式)**：**覆盖写**。<span style="color: green;">如果文件不存在，会自动创建</span>；如果文件已经存在，会**清空**原文件里的所有内容，从头开始写。
* **`"a"` (Append 模式)**：**追加写**。<span style="color: green;">如果文件不存在，会自动创建</span>；如果文件存在，会在原文件的**末尾继续追加**内容，以前的内容不会丢失。

文件**写相关的系统任务**：

* **`$fdisplay(文件句柄, "格式", 变量...);`**
    * **特点**：和打印到屏幕的 `$display` 用法完全一样，**自带换行符**（**写完这行自动跳到下一行**）。最推荐初学者使用。
* **`$fwrite(文件句柄, "格式", 变量...);`**
    * **特点**：和 C 语言的 `printf` 类似，**不带换行符**。如果你想换行，必须在格式字符串里手动加上 `\n`。适合需要将多次结果拼接在同一行的情况。
* **`$fstrobe(文件句柄, "格式", 变量...);`**
    * **特点**：它会在当前仿真时间步（Time Step）的最后时刻才执行写入，用于避免竞争冒险导致的读取旧值问题。

### 1.4 task 与 function

之前我（们）往往把所有的激励（拉低复位、等几个时钟、给输入、等输出）全部写在一个几千行的 `initial` 块里。一旦要修改某个时序，就要到处找，极难维护，很不**工程化**。

在 SystemVerilog 中，解法就是 **“子程序封装”**。SV 提供了两种子程序——**`task`（任务）** 和 **`function`（函数）**：

1. **`task` （任务）：可以消耗仿真时间。**
    * 只要你的操作里包含 `#10`（延迟）、`@(posedge clk)`（等时钟边沿）、`wait(sig == 1)`（等待信号）这些与**时间**有关的语句，**必须**使用 `task`。
    * `task` 内部可以调用其他 `task`，也可以调用 `function`。
2. **`function` （函数）：绝对不能消耗仿真时间（零时刻执行完毕）。**
    * 它里面**严禁**出现任何 `#`、`@`、`wait` 等时间控制语句。
    * 它通常用于纯数学计算（比如算个 ALU 的预期结果）、数据类型转换、或者零时刻的打印。
    * `function` 内部只能调用其他 `function`，**绝对不能**调用 `task`（因为 task 可能会挂起消耗时间，这违背了 function 零时间的原则）。
    * `function` 可以作为可综合语法写入设计模块。

> **注：** 这里涉及到 Verilog/SystemVerilog 中的逻辑层次划分：
> `Module` > `assign` = `always` = `initial` > `task` > `function`。

#### 1.4.1 `task` 的标准写法

在 SystemVerilog 中，写 `task` 的语法非常接近 C 语言。可以直接在括号里定义输入输出参数。

```systemverilog
task automatic <task_name>()

endtask
```

!!! note "automatic 关键字"
    `automatic` 关键字很重要。Verilog `task` 是“静态分配内存”的。如果你在不同的地方（**并发**）两次调用同一个 task，它们的内部变量会互相覆盖，导致极其诡异的 Bug。

    加上 `automatic` 后，每次调用这个 task，仿真器都会为它在内存里**动态分配独立的堆栈空间**。这在现代验证中是 **绝对的强制规范**。


#### 1.4.2 `function` 的标准写法

`function` 的核心作用就是 **“瞬时计算”或“瞬时操作”**。
在传统的 Verilog 中，`function` 必须有一个返回值（且名字和 function 名字一样，很反人类）。
**SystemVerilog 做了两点极大的优化：**

1. 引入了 `return` 语句（就像 C 语言一样）。
2. 引入了 `void` 返回类型（如果你只想封装几句打印，不需要返回值，可以声明为 `void function`）。

    ```systemverilog
    // [示例 1]：带返回值的 function (计算预期结果)
    // 根据 RV32I 汇编指令的操作码，计算下一个 PC 应该是多少
    function automatic logic [31:0] calc_next_pc(
    input logic [31:0] current_pc,
    input logic        is_branch_taken,
    input logic [31:0] branch_offset
    );
    if (is_branch_taken) begin
        return current_pc + branch_offset; // 直接使用 return
    end else begin
        return current_pc + 32'd4;
    end
    endfunction

    // [示例 2]：不带返回值的 void function (用于零时刻的比对打印)
    function automatic void check_result(
    input logic [31:0] expected, 
    input logic [31:0] actual
    );
    if (expected !== actual) begin
        $display("[ERROR] 结果不匹配！预期: %h, 实际: %h", expected, actual);
        error_count++; // error_count 必须是外部定义的全局变量
    end else begin
        $display("[PASS] 结果正确: %h", actual);
    end
    endfunction
    ```

> 按照我现在的理解：`task` 和 `function` 最大的作用就是封装子过程，简化 `initial` 块测试主流程的复杂程度，便于单独调试和复用。

### 1.5 命令行参数

**Compile Once, Run Multiple（编译一次，运行多次）。**
把芯片硬件代码和测试平台编译成一个仿真可执行文件后，我们通过在运行命令后面加上不同的参数，来动态改变 Testbench 的行为。
SystemVerilog 原生提供了两个系统函数来实现这一点：`$test$plusargs` 和 `$value$plusargs`。

#### 1.5.1 `$test$plusargs` —— 布尔型开关 (是否存在某个参数)

这个函数主要用来做**开关控制**。它会去检查你在运行命令中是否敲了某个特定的参数。

* **返回类型**：如果找到了这个参数，返回非 0 值（真）；没找到，返回 0（假）。
* **常见用途**：控制**是否打印详细调试信息**、**是否开启波形输出**。因为打印和写波形会拖慢仿真速度，通常跑大批量回归测试时是关掉的，只有出错 debug 时才打开。

#### 1.5.2 `$value$plusargs` —— 键值对传参 (提取参数的具体值)

这是我们**最常用、最核心**的函数！它可以从命令行不仅识别参数名，还能提取等号后面的具体数值或字符串。

* **语法格式**：`$value$plusargs("变量名=%格式", 接收变量)`
    * 这里的格式和 C 语言一样：`%s` 代表字符串，`%d` 代表十进制整数，`%h` 代表十六进制。
* **返回类型**：如果成功找到了这个参数并提取了值，返回 `1`；如果没有传入这个参数，返回 `0`。

#### 1.5.3 命令行参数传递

在主流仿真器的命令行模式中，只需要在仿真命令（`vsim, vcs, xsim`）后面加上参数即可，例如：

```systemverilog
vsim -c tb_cmd_args -do "run -all; quit" +TESTNAME=test.txt +DUMP_WAVES
```

**对于 Vivado XSim (GUI操作)**
如果习惯图形界面，可以在 Vivado 中：

1. 点击左侧 `Simulation` -> `Simulation Settings`。
2. 在弹出的窗口中切换到 `Simulation` 标签页。
3. 找到 **`xsim.simulate.xsim.more_options`** 这一栏。
4. 在里面填入：`+TESTNAME=add_test.txt +DUMP_WAVES`。
5. 然后点击 Run Simulation 即可生效。

### 1.6 并发线程——`fork...join`

在写 RTL 时，我们知道所有的 `always`/`assign` 块都是天生并行的（或者说，它们本身是无时无刻不在工作的电路）。但是在写Testbench 的 `initial` 或 `task` 时，代码默认是**串行（顺序）执行**的。

那么会出现一个问题：如果我们在 `initial` 块里写了一个 `wait` 语句，等待 DUT 输出 valid 信号，但 DUT 永远不输出 valid 了，这时仿真就会**卡死（Hang）**，无法继续往下执行。这个时候，我们就可以通过一个叫做“**超时看门狗**”的技术，来控制最长仿真时间，一旦超出这个时间立刻终止程序，避免卡死。

这也就是说，我们需要在 `initial` 块里同时**并行**做两件事:

* 正常仿真任务
* 超市看门狗，检测是否超时

这两个任务就是两个**线程**(thread)，在本案例中，只要有一个线程先完成了，我们就可以**跳出这个块**。

在 SystemVerilog 中，以上设想可以通过 `fork...join` 相关语法来实现。

#### 1.6.1 基础心法

在 `fork` 和 `join` 之间，**每一个独立的语句，或者每一个 `begin ... end` 块，都会变成一个独立的并行线程。**

**【非常重要的防坑指南】**
初学者常犯的错是没加 `begin...end`：

```systemverilog
// 错误示范：这会产生 2 个并行的线程，#10 和 a=1 是同时发生的！
fork
    #10;
    a = 1;
join
```

**工程规范**：在 `fork` 里面，一定要用 `begin : 线程名字` 和 `end` 把逻辑包起来。这样一个 `begin...end` 块才算作一个完整的线程。

#### 1.6.2 SytemVerilog 中的三大并行模式

Verilog 只有一种 `fork...join`，而 SystemVerilog 扩展为了三种。

1. `fork ... join` (**全员到齐才放行**)
    * **规则**：主程序走到这里，会分裂出多个子线程。必须**等待里面所有的子线程都执行完毕**，主程序才会继续往下走。
    * **场景**：你要同时初始化多路总线，必须等所有总线都初始化完了才进行下一步。
2. `fork ... join_any` (**只要有一个完成就放行**) —— **最常用！**
    * **规则**：多个子线程同时起跑，**只要有任何一个线程率先执行完毕**，主程序立刻继续往下走。
    * **场景**：**超时看门狗（Watchdog）**。线程 A 负责死等 DUT 的返回，线程 B 负责倒计时（比如 1000 个时钟周期）。如果 A 先等到了，说明 DUT 正常；如果 B 先倒数完了，说明 DUT 死机了，直接报错！
3. `fork ... join_none` (**只管点火，不管发射**)
    * **规则**：派生出子线程后，主程序**一瞬间都不等**，直接往下走。子线程会在后台默默运行。
    * **场景**：开启一个后台时钟监控器（Monitor），它在整个仿真期间一直盯着总线，而不阻塞主测试流程。

!!! attention "disable fork"
    当使用 `join_any` 时，假设线程 A（正常收到数据）率先完成了，主程序往下走了。**但是，线程 B（倒计时报错）仍然在后台偷偷运行！** 如果不把它杀掉，等仿真再往前走 1000 个周期，线程 B 突然倒数结束了，报了个错，这会让你在查 Bug 时完全摸不着头脑。
    **所以，在 `join_any` 后面，一定要紧跟一句 `disable fork;`，它的作用是无情地把当前 `fork` 里还在后台苟延残喘的其他线程全部强制杀掉。**

#### 1.6.3 Example

如下是一个 `fork...join` 语法、超时看门狗、以及 `disable fork` 用法的示例：

```systemverilog
`timescale 1ns/1ps

module tb_fork_watchdog;

    logic clk;
    logic dut_out_valid;

    // 产生时钟
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // 用 task 封装等待逻辑
    task automatic wait_cpu_response(int timeout_cycles);
        $display("[%0t] [INFO] 开始等待 CPU 返回 valid 信号...", $time);
        
        fork
            // ------------------------------------
            // 线程 1：正常业务逻辑 (死等 valid)
            // ------------------------------------
            begin : thread_wait_dut
                wait(dut_out_valid == 1'b1);
                $display("[%0t] [SUCCESS] 成功等到了 CPU 返回信号！", $time);
            end

            // ------------------------------------
            // 线程 2：看门狗逻辑 (倒计时)
            // ------------------------------------
            begin : thread_watchdog
                // 倒数 timeout_cycles 个时钟周期
                repeat(timeout_cycles) @(posedge clk); 
                $display("[%0t] [FATAL] 等待超时！CPU 死锁了，仿真强行终止！", $time);
                $fatal(1); // 直接结束仿真报错
            end
        join_any // 只要有 1 个线程先完成，就跳出 fork

        // 必须立刻杀死剩下的线程！
        disable fork; 
    endtask

    // 主测试流程
    initial begin
        dut_out_valid = 0;

        // 模拟场景 A：CPU 正常工作，过了 50 个周期给出了 valid
        fork // 这个 fork...join 只是为了造一个模拟 DUT 的后台任务
            begin
                #500; // 等待500ns (50个周期)
                dut_out_valid = 1;
            end
        join_none // 挂在后台造信号，主线不等待

        // 调用任务，限制最大等待 100 个周期
        // 结果：正常逻辑会先赢（50周期 < 100周期），看门狗会被 disable 掉
        wait_cpu_response(100);

        // -------------------------------------------
        
        $display("\n===============================");

        // 模拟场景 B：CPU 死锁了，一直没有给出 valid
        dut_out_valid = 0;

        // 这次限制等待 100 个周期，但 DUT 永远不会给 valid 了
        // 结果：看门狗会赢，触发 $fatal 结束仿真
        wait_cpu_response(100);

    end
endmodule
```

在工业界，`fork...join` 里面的块**强制要求命名**。因为如果在复杂的并发中出了问题，仿真工具打出来的 Debug Log 会明确告诉你：“哪个名字的线程挂了”，如果不命名，你看到的将是天书。