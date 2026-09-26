# Tcl 脚本使用指南

## I. Tcl 基础语法

Tcl(Tool Command Language) 是一种脚本语言，广泛应用于 EDA 工具中进行自动化操作。
Tcl 脚本就是一系列命令的集合。每条命令由**命令名 + 多个参数**组成，用空格或制表符分隔，**换行或分号**结束。
Tcl 的核心哲学是：**一切皆字符串，一切皆命令**。
一条 Tcl 语句的基本结构永远是：`命令 参数1 参数2 ...` (以空格分隔)

### 1.1 变量与输出
在 Tcl 中，不需要声明变量类型，赋值用 `set`，取值用 `$`。


1. 变量赋值 (用空格分隔命令和参数): `set my_clk_period 10.0`
2. 读取变量的值 (使用 `$`): `puts "T: $my_clk_period" ` , `puts` 相当于 Python 中的 `print` ，`;`用来分隔同行命令
3. 释放变量: `unset my_clk_period`


### 1.2 三大核心符号：`$`、`[]` 和 `{}`

1. **`$` (变量替换)**：提取变量的值。
2. **`[]` (命令替换)**：**极为重要！** 相当于 Bash 中的反引号 `` ` ``，它会先执行方括号里的命令，然后把结果放在原处。

    ```tcl
    # expr 是专门用来做数学计算的命令
    set a 5
    set b [expr $a + 2]   ;# 先执行 expr 5 + 2，然后把结果 7 赋给 b
    puts $b               ;# 输出 7

    # 在 EDA 中的常见用法：
    # 获取所有的输入端口，并赋给变量 all_in_ports
    set all_in_ports [all_inputs] 
    ```

3. **`{}` (大括号：分组与原样输出)**：
    *   在双引号 `""` 中，`$` 和 `[]` **会被**替换和执行。
    *   在花括号 `{}` 中，一切都是纯文本，**不进行**替换。

    ```tcl
    set name "World"
    puts "Hello $name"   ;# 输出: Hello World
    puts {Hello $name}   ;# 输出: Hello $name
    ```

### 1.3 列表 (List)
EDA 脚本中充斥着大量的列表操作（比如一组 pin、一组 path、一系列 cell）。

1. 创建列表: `set my_pins [list "clk" "rst_n" "enable"]`
2. 获取列表长度 (list length): `set pin_count [llength $my_pins]`
3. 获取列表元素 (list index，**索引从0开始**): `set first_pin [lindex $my_pins 0]`
4. 追加元素 (list append): `lappend my_pins "data_in"`

### 1.4 控制流 (If, For, Foreach)
**⚠️ Tcl 的一个大坑（C++/Rust 程序员极易踩中）：**
Tcl 强制要求左大括号 `{` 必须与上一行代码在**同一行**！因为 Tcl 是一行行解析命令的，如果 `{` 换行，Tcl 会认为上一行命令已经结束。

#### 1.4.1 If 条件判断

```tcl
set delay 2.5
if {$delay > 3.0} {
    puts "Timing Violation!"
} elseif {$delay == 3.0} {
    puts "Critical!"
} else {
    puts "Timing Met."
}
```

#### 1.4.2 Foreach 循环
用于遍历集合（Collection）或列表。

```tcl
set port_list [list "portA" "portB" "portC"]

foreach port $port_list {
    puts "Processing port: $port"
    # 在 EDA 中常常类似这样批量设置属性：
    # set_input_delay 2.0 -clock clk $port
}
```

#### 1.4.3 For 循环
格式：`for {初始化} {条件} {步进} {操作}`

```tcl

for {set i 0} {$i < 5} {incr i} {
    puts "Current index: $i"
}
```

注：`incr` 是 Tcl 中专门用来给**数字加 1** 的命令

### 1.5 函数 / 过程
在 Tcl 中定义函数使用 `proc` 命令。

```tcl
# 定义一个名字叫 setup_my_clock 的函数，接收两个参数
proc setup_my_clock {clk_name period} {
    puts "Creating clock $clk_name with period $period"
    
    # 在这调用 EDA 工具的命令
    # create_clock -name $clk_name -period $period [get_ports $clk_name]
    
    return "Clock created successfully"
}

# 调用函数
set result [setup_my_clock "core_clk" 5.0]
```

### 1.6 文件读写

1. **打开文件**：`set 句柄 [open "文件名" 模式]` （模式包括 `r` 读, `w` 写, `a` 追加）。
2. **按行读取**：`gets $句柄 变量名` （成功读取返回字符数，读到末尾返回 -1）。
3. **写入文件**：`puts $句柄 "字符串"`。
4. **关闭文件**：`close $句柄`。

    ```tcl
    # 写入报告
    set file_handle [open "my_custom_report.rpt" w]
    puts $file_handle "This is a custom area report."
    close $file_handle

    # 读取文件 (按行读取)
    set file_handle[open "timing.rpt" r]
    while {[gets $file_handle line] >= 0} {
    # 用正则表达式查找特定内容 (Tcl 的 regexp 很强大)
    if {[regexp {slack \(VIOLATED\)} $line]} {
        puts "Found a violation: $line"
    }
    }
    close $file_handle
    ```

## II. 其余命令

*暂时存放，后续分类*

(1) `search_path`: 搜索路径，返回符合条件的路径列表。例如：

```tcl
lappend search_path ~/Desktop/Workspace/SMIC18/db ../scripts ../design
```

## III. Synopsys 

*针对 Synopsys DC/ICC/PT 工具，非标准 Tcl，后续补充*

#### (1) `set_app_var`

设置应用级变量，好处是，如果拼写错了系统变量名（比如把 `target_library` 拼成了 `traget_library`），它会立刻报错，而用 `set` 则会默默创建一个没用的新变量。

案例：

```tcl
set_app_var target_library "slow.db S018V3EBCDSP_X8Y4D64_PR.db S018V3EBCDSP_X8Y4D80_PR.db"
```

#### (2) target_library

- **定义**：指定综合时最终映射到的**标准单元库**（technology library）。
- **作用**：工具会将 RTL 代码中的逻辑门（如与门、或门、触发器）**映射到该库中提供的实际物理单元**（如 NAND2、DFFRX1）。
- **特点**：
    - 通常只包含**标准单元库（.db 格式）**以及可能的** IP 或宏单元（如 SRAM）**。
    - 该库中的单元必须具有时序、面积、功耗等信息，用于驱动强度、延迟计算。
    - 综合完成后，网表中的每个逻辑门应该都能在 target_library 中找到对应的物理实现。

案例：

```tcl
set_app_var target_library "slow.db S018V3EBCDSP_X8Y4D64_PR.db S018V3EBCDSP_X8Y4D80_PR.db"
```

- **slow.db**

通常代表标准单元库的一个**慢速工艺角**（Slow Corner），用于 **setup 时序分析**。其中包含各种基本逻辑门（与或非、触发器、选择器等）的时序、面积、功耗信息。

#### (3) link_library

- **定义**：指定在 **链接（resolve references）** 时可以搜索的所有库。
- **作用**：
    - 包含 `target_library`（通常也会把 `target_library` 加入 `link_library`，否则无法链接到映射后的单元）。
    - 还包含**额外的库**，如：IP 核、DesignWare 库、已综合的子模块网表（`.db` 或 `.ddc`）、RAM/ROM 宏单元。
    - 用于解析设计中未定义的子模块（例化但未提供的模块）或符号。
- **特点**：
    - 链接过程发生在**读入 RTL、网表或进行层次化综合**时。
    - 可以指定多个库，用空格或冒号分隔。
    - 一个特殊值是 `“*”`，代表**已经读入内存的设计**（即 `current_design` 及其子模块），**工具会先搜索内存再搜索库**。

**示例：**

```tcl
set_app_var link_library "* slow.db SP018W_V1p5_max.db S018V3EBCDSP_X8Y4D64_PR.db"
```

- **SP018W_V1p5_max.db**

可能是一个标准单元库（名称中的 `max` 表示最大延迟 corner，或 `V1p5` 表示 `1.5V` 工作电压）。通常用于 setup 时序或与 slow.db 配合进行多场景分析。


#### (4) DesignWare

**DesignWare** 是 Synopsys 提供的**可复用 IP（知识产权）库**，集成在 Design Compiler 等综合工具中。它提供了一系列**预设计、预验证的逻辑功能模块**，例如：

- 算术单元：加法器、乘法器、乘加器、比较器
- 算术逻辑单元：移位器、计数器、除法器
- 存储及控制：FIFO、队列、各种编码/解码器
- 总线接口：AMBA、PCIe、USB 等（更高层次的 DesignWare IP）

> **注意**：DesignWare 不是物理库，而是**结构化的 RTL 模板或软宏**，综合后仍需映射到 `target_library` 中的标准单元。

#### (5) db 库
**db 库**（`.db` 文件）是 Synopsys 工具使用的**二进制数据库文件**，用于存储一个逻辑库或设计模块的完整信息，包括：

- 时序模型（延迟、约束、检查）
- 面积数据
- 功耗参数
- 功能描述（布尔函数、真值表）
- 引脚电容、驱动电阻等电气数据
- 对于硬宏：版图抽象（Lef 等效信息）和时序弧

**常见来源**

- **标准单元库**：由工艺厂（如 TSMC、SMIC）或库供应商将 `.lib`（文本格式）转换为 `.db` 提供。
- **IP 库**：存储器编译器、PLL、ADC/DAC 等生成的时序模型。
- **已综合的设计**：`write -format db` 可将子模块网表保存为 `.db`，供上层设计链接。

**`.db` vs `.lib`**

| 特性 | `.lib` (Liberty) | `.db` (Synopsys DB) |
|------|----------------|---------------------|
| 格式 | 文本，可读 | 二进制，不可读 |
| 工具 | 通用（多数 EDA 工具支持） | Synopsys 专用 |
| 速度 | 解析较慢 | 加载/保存快 |
| 用途 | 库交换格式 | 工具内部使用 |

> 通常我们只需关注 `.db`，因为 Synopsys 流程中最终读入的都是 `.db`（或 `.ddc`）。`link_library` 和 `target_library` 中的库路径指向的就是 `.db` 文件。


#### (6) set_min_library

`set_min_library` 是 Synopsys 工具（如 Design Compiler、PrimeTime、ICC）中用于关联**最大延迟（max）库**和**最小延迟（min）库**的命令，目的是同时进行**建立时间（setup）**和**保持时间（hold）**分析。

- 库中通常提供不同 PVT（工艺、电压、温度）角下的时序模型：
    - **max 库**：慢速（高延迟），用于分析建立时间（setup）
    - **min 库**：快速（低延迟），用于分析保持时间（hold）
- 在综合或静态时序分析（STA）时，如果同时使用两种库，工具需要知道：
    - **每个逻辑单元在 max 角下的延迟**（用于数据路径 setup 检查）
    - **同一逻辑单元在 min 角下的延迟**（用于数据路径 hold 检查以及时钟网络最小延迟）
- `set_min_library` 告诉工具：**哪个 min 库对应于某个 max 库**，确保为同一个单元正确选择两套时序数据。

**命令语法**

```tcl
set_min_library <max_library_name> -min_version <min_library_name>
```

- `max_library_name`：慢速（最大延迟）库的文件名（`.db` 或 `.lib`）
- `-min_version`：指定对应的快速（最小延迟）库

工具会记录这个映射关系，在时序分析时：

- 对 max 库中的单元使用其 max 延迟值
- 对同一个单元，当需要计算最小路径延迟时，自动切换到 `-min_version` 指定的库中读取相应单元的 min 延迟。