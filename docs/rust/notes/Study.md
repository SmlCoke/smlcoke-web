# Rust学习笔记
SmlCoke的Rust学习笔记，记录学习过程中遇到的问题和解决方案。

## 一. 入门

### 1.1 hello world
```rust
fn main() {

}
```


这几行定义了一个名叫 `main` 的函数。`main` 函数是一个特殊的函数：在可执行的 Rust 程序中，它**总是最先运行的代码**。第一行代码声明了一个叫做 `main` 的函数，它没有参数也**没有返回值**。如果有参数的话，它们的名称应该出现在小括号 `()` 中。
函数体被包裹在 `{}` 中。Rust 要求**所有函数体都要用花括号包裹起来**。一般来说，将左花括号与函数声明置于同一行并以空格分隔，是良好的代码风格。

```rust
println!("Hello, world!");
```
println! 调用了一个 Rust 宏（macro），**当看到符号 ! 的时候，就意味着调用的是宏而不是普通函数**，并且宏并不总是遵循与函数相同的规则。

### 1.2 编译与运行
编译指令
```bash
rustc main.rs
```
这将会生成文件：`main.exe` (Windows) 或 `main` (Linux 和 macOS)，和`main.pdb`(Windows 调试符号文件)。

### 1.3 cargo

Cargo 是 Rust 的构建系统和包管理器。
它可以处理很多任务，比如构建代码、下载依赖库并编译这些库。（我们把代码所需要的库叫做 **依赖（dependencies）**）。

#### 1.3.1 创建新项目
使用 Cargo 创建一个新项目：
```bash
cargo new hello_cargo
```
这样会在当前目录下创建一个名为 `hello_cargo` 的新目录，并且同时成为一个新的 git 仓库。该仓库包含的初始文件/文件夹如下：
- src/ 目录：包含项目的源代码文件。
- Cargo.toml 文件：包含项目的元数据和依赖信息。
- .git/ 目录：包含 git 版本控制信息。
- .gitignore 文件：指定哪些文件和目录不应被 git 版本控制跟踪。

当然，可以使用:
```bash
cargo new hello_cargo --vcs none
```
**创建项目但是不构建为 git 仓库**。

#### 1.3.2 关于 Cargo.toml
Cargo.toml 文件是一个文本文件，使用 [TOML](https://toml.io/en/) 格式编写。它包含了项目的元数据和依赖信息。以下是一个示例 Cargo.toml 文件的内容：

```toml
[package]
name = "hello_cargo"
version = "0.1.0"
edition = "2024"

[dependencies]
```
- 第一行，`[package]`，是一个片段 section 标题，表明下面的语句用来配置一个包。随着我们在这个文件增加更多的信息，还将增加其他 section。
- 接下来的三行设置了 Cargo 编译程序所需的配置：**项目的名称**、**项目的版本**以及**要使用的 Rust 版本**。
最后一行，`[dependencies]`，是**罗列项目依赖的 section 的开始**。在 Rust 中，**代码包被称为 crates**。
- 在 Cargo.toml 文件中，标题以及之后的内容属同一个 section，直到遇到下一个标题才开始新的 section。

#### 1.3.3 构建和运行项目

**构建项目：**
```bash
cargo build
```
这样做之后，当前项目目录下会生成一个 `target` 目录，里面包含了编译后的文件。默认情况下，Cargo 会以**调试模式**构建项目，生成的可执行文件会放在 `target/debug/` 目录下。
**运行项目：**
```bash
./target/debug/hello_cargo
```

编译好项目后，会产生一个cargo.lock文件，用于**锁定项目的依赖版本**，以确保在不同的机器或不同的时间构建项目时，**使用相同版本的依赖库**。由于 Cargo.lock 文件对于可重现构建非常重要，因此它通常会和项目中的其余代码一样提交到版本控制系统中。

强制升级依赖项到最新版本：
```bash
cargo update
```
或者直接修改 Cargo.toml 文件中依赖项的版本号，然后运行 `cargo build`，Cargo 会自动下载并使用新的版本。
**编译并运行项目**
```bash
cargo run
```
Rust 在重新编译项目之前，会检查自上次编译以来，项目的源代码或依赖项是否有任何更改。如果没有更改，Cargo 会跳过重新编译的步骤，直接运行上次编译生成的可执行文件。

**检查代码**
```bash
cargo check
```
快速检查代码确保其可以编译，但并不产生可执行文件
推荐**编写代码时定期运行 cargo check 确保它们可以编译**。当准备好使用可执行文件时才运行 `cargo build`

#### 1.3.4 release
要以**发布模式**构建项目，可以使用以下命令：
```bash
cargo build --release
```
这会在 target/release 而不是 target/debug 下生成可执行文件。这些优化可以让 Rust 代码运行的更快，不过启用这些优化也需要消耗更长的编译时间。
因此**发布模式一般只用于最终发布的版本，而不是在开发过程中频繁使用**。

## 二. 编程概念
先贴一张图，这是我在学习 `Python` 和 `C++` 中从来没有见到过的，非常清晰的报错信息
![alt text](image.png)

### 2.1 变量
变量默认不可变，例如
```rust
let x = 5;
```
但是可以添加 `mut` 关键字使变量可变，例如
```rust 
let mut x = 5;
x = 6;
```

### 2.2 常量
常量不仅默认不可变，而且一定不可变，并且不是用 `let` 来声明，而是用 `const` 来声明，而且还要标准清楚**数据类型**。例如
```rust
const THREE_HOURS_IN_SECONDS: u32 = 60 * 60 * 3;
```
**常量可以在任何作用域中声明，包括全局作用域**，这在一个值需要被很多部分的代码用到时很有用。

### 2.3 遮蔽（shadowing）
我们可以定义一个与之前变量同名的新变量：称为第一个变量被第二个 遮蔽（Shadowing） 了，这意味着使用变量的名称时，编译器将看到第二个变量，直到**第二个变量自己也被遮蔽**或**第二个变量的作用域结束**
典型例子
```rust
fn main() {
    let x = 5;

    let x = x + 1;

    {
        let x = x * 2;
        println!("The value of x in the inner scope is: {x}");
    }

    println!("The value of x is: {x}");
}
```

输出结果为：
```bash
The value of x in the inner scope is: 12
The value of x is: 6
```

### 2.4 数据类型
在 Rust 中，每一个值都有一个特定数据类型（data type）
两种数据类型子集：scalar 和 compound
#### 2.4.1 标量类型（Scalar Types）
Rust中的四种基本标量类型：整型、浮点型、布尔类型和字符类型

**整型：**

|长度|	有符号|	无符号|
|----|-------|-------|
|8-bit|	i8|	u8|
|16-bit|	i16|	u16|
|32-bit|	i32|	u32|
|64-bit|	i64|	u64|
|128-bit|	i128|	u128|
|架构相关|	isize|	usize|

范围：$-2^{n-1} \sim 2^{n-1}-1$

整型字面值：

|数字字面值| 例子|
|----------|-----|
|Decimal (十进制)|	98_222|
|Hex (十六进制)|	0xff|
|Octal (八进制)|	0o77|
|Binary (二进制)|	0b1111_0000|
|Byte (单字节字符)(仅限于u8)|	b'A'|

可以是多种数字类型的数字字面值允许使用类型后缀，例如 57u8 来指定类型，同时也允许使用 _ 做为分隔符以方便读数，例如1_000，它的值与你指定的 1000 相同。

整型默认是: `i32`

**浮点型**
Rust 的浮点数类型是 `f32` 和 `f64`
`f32`和`f64`几乎一样快，但是`f64`更精确
采用`IEEE-754`标准

**布尔类型**
Rust 中的布尔类型有两个可能的值：true 和 false。
Rust 中的布尔类型使用 bool 表示。
```rust
let t = true;
let f: bool = false; // with explicit type annotation
```

**字符类型**
用单引号声明 `char` 字面值，而与之相反的是，使用双引号声明字符串字面值。
Rust 的 `char` 类型的**大小为四个字节** (four bytes)，并代表了一个 **Unicode 标量值**（Unicode Scalar Value），这意味着它**可以比 ASCII 表示更多内容**。
在 Rust 中，带变音符号的字母（Accented letters），中文、日文、韩文等字符，emoji（绘文字）以及零长度的空白字符都是有效的 `char` 值。

示例
```rust
let c = 'z';
let z: char = 'ℤ'; // with explicit type annotation
let heart_eyed_cat = '😻';
```

#### 2.4.2 复合类型（Compound Types）
Rust 有两个原生的复合类型：**元组（tuple）**和**数组（array）**。

**元组类型**
元组是一个将多个**不同类型的值**组合进一个复合类型的主要方式。元组**长度固定**：一旦声明，其长度不会增大或缩小。
示例
```rust 
let tup: (i32, f64, u8) = (500, 6.4, 1);
```

**用模式匹配（pattern matching）来解构（destructure）元组值**：
```rust
let tup = (500, 6.4, 1);
let (x, y, z) = tup;
println!("The value of y is: {y}");
```

可以使用点号（.）后跟值的索引来直接访问所需的元组元素。例如:
```rust
let five_hundred = tup.0;
let six_point_four = tup.1;
```

不带任何值的元组有个特殊的名称，叫做 单元（unit） 元组。这种值以及对应的类型都写作 `()`，表示空值或空的返回类型。**如果表达式不返回任何其他值，则会隐式返回单元值。**

**数组类型**
数组中的每个元素的**类型必须相同**
Rust中的数组**长度是固定**的
**数组是可以在栈 (stack) 上分配的已知固定大小的单个内存块**
```rust
let a = [1, 2, 3, 4, 5];
```
> 数组并不如 vector 类型灵活。vector 类型是标准库提供的一个 允许 增长和缩小长度的类似数组的集合类型。当不确定是应该使用数组还是 vector 的时候，那么很可能应该使用 vector。

像这样编写数组的类型：在**方括号中包含每个元素的类型**，后跟分号，再后跟数组元素的**数量**。
```rust
let a: [i32; 5] = [1, 2, 3, 4, 5];
```

可以通过在方括号中**指定初始值加分号再加元素个数**的方式来创建一个每个元素都为相同值的数组
```rust
let a = [3;5]; // 等同于 let a = [3, 3, 3, 3, 3];
```

数组元素的访问：
```rust
let b = a[0];
```

### 2.5 函数
Rust中的所有函数采用 `snake case` 命名约定，所有字母小写，采取下划线分割
用`fn`定义函数
源码中函数定义在 `main` 函数 之后，也可以定义在之前，只要函数被调用时**出现在调用之处可见的作用域**内就行。
```rust
fn func1(x: i32, label: char) {
    println!("The value of x from func1 is {x}, label is {label}");
}
```

### 2.6 语句（Statements）和表达式（Expressions）
Rust中，需要区分语句和表达式
- 语句是执行某些操作但**不返回值**的指令。例如，`let` 语句用于**创建变量**，它没有返回值。
- 表达式是**计算并产生一个值**的代码片段。例如，`5 + 6` 是一个表达式，它计算结果为 `11`。

函数定义也是statement，但是调用函数不是statement
语句不返回值，例如**如下无法通过编译**
```rust
let y = let x = 5; // ❌️
let y = (let x = 5); // ❌️
```
但是在C和Ruby中是可以的。

Rust 是 Expressions-Base 的语言，大多数代码都是表达式，函数调用是表达式、宏调用是表达式、用`{}`创建一个新的作用域也是表达式。**表达式会返回一个值**
```rust
fn main() {
    let y = {
        let x = 3;
        x + 1
    };

    println!("The value of y is: {y}");
}
```

这里的
```rust
{
    let x = 3;
    x + 1
}
```
就是一个表达式，返回值是4。

### 2.7 具有返回值的函数
- 函数可以向调用它的代码返回值。
- 我们并不对返回值命名，**但要在箭头 `->`后声明它的类型**。
- 在 Rust 中，**函数的返回值等同于函数体最后一个表达式的值**。
- ==使用 return 关键字和指定值，可从函数中提前返回==；但大部分函数**隐式地返回最后的表达式**。这是一个

有返回值的函数的例子：
**最 Rust，最推荐的写法：**
```rust
fn five() -> i32 {
    3*x+2
}
```

当然，我们也可以用 `return` 引导的语句提前返回：
```rust
fn five() -> i32 {
    return 3*x+2;
}
```

此外，这种写法也可以：
```rust
fn five() -> i32 {
    return 3*x+2
}
```
因为在`rust`中，**块 `{}` 中的最后一条“语句”，分号是可选的**


### 2.8 控制流 
#### 2.8.1 条件判断
Rust 中的条件判断使用 `if` 关键字。
```rust
if number < 5 {
    println!("condition was true");
} else {
    println!("condition was false");
}
```
- 所有的 `if` 表达式都以 `if` 关键字开头，其后跟一个条件
- 代码中的条件必须是 bool 值，如下实例无法通过编译
```rust
let number = 3;
if number  {
    println!("condition was true");
} else {
    println!("condition was false");
}
```

Rust **并不会尝试自动地将非布尔值转换为布尔值**，必须总是显式地使用布尔值作为 if 的条件。这一点与`C`, `Python`, `Ruby`等语言不同。

#### 2.8.2 else if 用于多重条件判断
```rust
if number % 4 == 0 {
    println!("number is divisible by 4");
} else if number % 3 == 0 {
    println!("number is divisible by 3");
} else if number % 2 == 0 {
    println!("number is divisible by 2");
} else {
    println!("number is not divisible by 4, 3, or 2");
}
```

- `Rust` **只会执行第一个条件为 `true` 的代码块**，并且一旦它找到一个以后，甚至都不会检查剩下的条件了
- 使用过多的 else if 表达式会使代码显得杂乱无章，所以**如果有多于一个 else if 表达式，最好重构代码**。用 `match` 重构代码

#### 2.8.3 使用 if 在 let 语句中赋值
```rust
let condition = true;
let number = if condition { 5 } else { 6 };
```
- `if` 表达式的**两个分支必须返回相同类型的值**

#### 2.8.4 循环
Rust 有三种循环：`loop`、`while` 和 `for`。

##### loop
示例：
```rust
loop {
    println!("again!");
}
let result = loop {
    counter += 1;

    if counter == 10 {
        break counter * 2;
    }
};
```

这里包含了关于`loop`的两个重点：
- loop会无限循环，除非显式地使用`break`关键字退出循环
- loop循环可以作为一个表达式使用，并且可以通过`break`语句返回一个值。返回方法就是返回`break`后跟的值。


**循环标签：**
如果存在嵌套循环，break 和 continue 应用于此时最内层的循环。
如果想要中断指定的循环，可以使用循环标签（loop labels）。
```rust
let mut count = 0;
'counting_up: loop {
    println!("count = {count}");
    let mut remaining = 10;

    loop {
        println!("remaining = {remaining}");
        if remaining == 9 {
            break;
        }
        if count == 2 {
            break 'counting_up;
        }
        remaining -= 1;
    }

    count += 1;
}
println!("End count = {count}");
```

##### while
```rust
while number != 0 {
    println!("{number}!");
    number -= 1;
}
```

##### for
用的最多的循环形式
```rust
let a = [10, 20, 30, 40, 50];
for element in a {
    println!("the value is: {element}");
}
```

## 三. 分析一个示例
**猜字游戏：**
```rust
use std::cmp::Ordering;
use std::io;

use rand::Rng;

fn main() {
    println!("Guess the number!");

    let secret_number = rand::thread_rng().gen_range(1..=100);

    loop {
        println!("Please input your guess.");

        let mut guess = String::new();

        io::stdin()
            .read_line(&mut guess)
            .expect("Failed to read line");

        let guess: u32 = match guess.trim().parse() {
            Ok(num) => num,
            Err(_) => continue,
        };

        println!("You guessed: {guess}");

        match guess.cmp(&secret_number) {
            Ordering::Less => println!("Too small!"),
            Ordering::Greater => println!("Too big!"),
            Ordering::Equal => {
                println!("You win!");
                break;
            }
        }
    }
}
```

### 3.1 导入外部库
```rust
use std::cmp::Ordering;
use std::io;
use rand::Rng;
```

### 3.2 io
```rust
io::stdin()
    .read_line(&mut guess)
    .expect("Failed to read line");
```
- `.read_line(&mut guess)`：从标准输入读取一行，并将其存储在 `guess` 变量中。`&mut guess` 表示传递的是 `guess` 的可变引用，这样 `read_line` 方法**可以修改 `guess` 变量的内容**。

- `.expect("Failed to read line")`：这是错误处理的一种方式。`.read_line()`函数返回一个`Result`类型的值（只可能是`Ok`或`Err`），`Result`是**枚举类型**，其示例拥有`.expect()`方法。如果`read_line`成功读取输入，它会返回一个`Ok`值，expect 会获取 Ok 中的值并原样返回。**在本例中，这个值是用户输入到标准输入中的字节数**，程序继续执行。如果发生错误，它会返回一个`Err`值，`.expect()`方法会使程序**崩溃并打印出指定的错误消息**。

### 3.3 crate
上面代码使用了 `rand` crate 来生成随机数。
- crate 是一组 Rust 源代码文件
- 在`cargo.toml`文件中添加依赖：
    ```toml
    [dependencies]
    rand = "0.8.5"
    ```
- 然后运行 `cargo build`，Cargo 会自动下载并编译 `rand` crate 及其依赖项。注意，版本号可能会随着时间变化而不同，而`cargo.lock`文件会锁定具体的版本号，便于重现构建。

### 3.4 match 控制流运算符
```rust
match guess.cmp(&secret_number) {
    Ordering::Less => println!("Too small!"),
    Ordering::Greater => println!("Too big!"),
    Ordering::Equal => {
        println!("You win!");
        break;
    }
}
```
- 一个 match 表达式由 分支（arms） 构成。一个分支包含一个 模式（pattern）和表达式开头的值与分支模式相匹配时应该执行的代码
- `match` 关键字后跟一个表达式（本例中是 `guess.cmp(&secret_number)`），该表达式的值会与**后续的各个模式pattern**进行比较。
- 每个模式后面跟着 `=>` 符号，表示如果表达式的值与该**模式匹配**，则执行该模式后面的代码。
- `match`匹配到第一个满足条件的`pattern`后，就会执行对应的代码，不会继续**检查后续的模式**。

## 四. 所有权

### 4.1 所有权规则
1. Rust 中的每一个值都有一个 所有者（owner）。
2. 值在任一时刻有且只有一个所有者。
3. 当所有者离开作用域，这个值将被丢弃。

### 4.2 内存与分配

对比两端代码：

**demo1：正确**
```rust
let mut s = String::from("hello");
s.push_str(", world!");
println!("{s}");
```

**demo2：错误**
```rust
let s1 = "hello";
s1.push_str(", world!"); 
```

为什么 String 可变而字面值却不行呢？区别在于两个类型对内存的处理上。
> 就字符串字面值来说，我们在**编译时就知道其内容**，所以文本被直接**硬编码进最终的可执行文件**中。这使得字符串字面值快速且高效。不过这些特性都只得益于字符串字面值的不可变性。不幸的是，我们**不能为了每一个在编译时大小未知的文本而将一块内存放入二进制文件**中，并且它的大小还可能随着程序运行而改变。

### 4.3 作用域、所有权与值
#### 4.3.1 `drop` 函数
当一个变量离开作用域时，Rust 会调用一个特殊的函数来清理这个值占用的内存。这个函数叫做 `drop`，它会自动被调用来释放资源。
调用 `drop` 函数的唯一过程就是：**“所有权离开作用域”**

#### 4.3.2 所有权的转让
```rust
let s1 = String::from("hello");
let s2 = s1;
```
这里的 `s1` 是一个 `String` 类型的变量，它拥有一个字符串值 "hello"。当我们执行 `let s2 = s1;` 时，**s1 的所有权被转移（moved）到 s2**。这意味着 `s1` 不再拥有 "hello" 这个字符串值，`s2` 现在是这个值的唯一所有者。
因此我们接下来再执行：
```rust
println!("{s1}");
```
会导致编译错误，因为 `s1` 已经不再拥有那个字符串值了。

但是对于一些类型来说，**Rust 会在赋值时进行深复制（deep copy）**，而不是所有权转移。因为这些类型实现了 **Copy trait**）（Rust 不允许自身或其任何部分实现了 **Drop trait** 的类型使用 **Copy trait**）。
```rust
let x = 5;
let y = x;
println!("x = {x}, y = {y}");
```
在这个例子中，`x` 是一个 `i32` 类型的变量，它是一个 Copy 类型。当我们执行 `let y = x;` 时，`x` 的值被复制到 `y` 中，而 `x` 仍然有效。因此我们可以同时打印 `x` 和 `y` 的值。

**所有权的转让同样会发生在函数调用中，这一点与 C++/Python/Ruby 等语言很不同。**
```rust
fn main() {
    let s = String::from("hello");  // s 进入作用域

    takes_ownership(s);             // s 的值移动到函数里 ...
                                    // ... 所以到这里不再有效

    let x = 5;                      // x 进入作用域

    makes_copy(x);                  // x 应该移动函数里，
                                    // 但 i32 是 Copy 的，
    println!("{}", x);              // 所以在后面可继续使用 x

} // 这里，x 先移出了作用域，然后是 s。但因为 s 的值已被移走，
  // 没有特殊之处

fn takes_ownership(some_string: String) { // some_string 进入作用域
    println!("{some_string}");
} // 这里，some_string 移出作用域并调用 `drop` 方法。
  // 占用的内存被释放

fn makes_copy(some_integer: i32) { // some_integer 进入作用域
    println!("{some_integer}");
} // 这里，some_integer 移出作用域。没有特殊之处
```

对于 `String` 类型，如果我们想要深度复制**堆**上的数据，而不仅仅是栈上的数据，可以使用一个叫做 `clone` 的常用方法。
```rust
let s1 = String::from("hello");
let s2 = s1.clone();

println!("s1 = {s1}, s2 = {s2}");
```

#### 4.3.3 作用域与赋值
```rust
let mut s = String::from("hello");
s = String::from("ahoy");

println!("{s}, world!");
```
起初我们声明了变量 `s` 并绑定为一个 `"hello"` 值的 `String`。接着立即创建了一个值为 `"ahoy"` 的 `String` 并赋值给 `s`。在这里，**完全没有任何内容指向了原始堆上的值**。因此原始的字符串立刻就离开了作用域。Rust 会在其上运行 `drop` 函数**同时内存会马上释放**。当结尾打印其值时，将会是 "ahoy, world!"。

总之，作用域、所有权与值的转让关系可以一句话总结：**将值赋给另一个变量时它会移动。当持有堆中数据值的变量离开作用域时，其值将通过 drop 被清理掉，除非数据被移动为另一个变量所有。**。

只需要记住它们满足的最核心的三个条件：
1. Rust 中的每一个值都有一个 所有者（owner）。
2. 值在任一时刻有且只有一个所有者。
3. 当所有者离开作用域，这个值将被丢弃。

### 4.4 引用与借用

#### 4.4.1 不可变引用
引用（reference）像一个指针，因为它是一个地址，我们可以由此访问储存于该地址的属于其他变量的数据。与指针不同，引用在其生命周期内保证指向某个特定类型的有效值。

当我们传入函数参数时，往往只想让参数获取值的引用，**而不是获取值的所有权**。这一点可以通过**引用**完成：
```rust
fn main() {
    let s1 = String::from("hello");

    let len = calculate_length(&s1);

    println!("The length of '{s1}' is {len}.");
}

fn calculate_length(s: &String) -> usize {
    s.len()
}
```

变量的引用不具有所有权，因此试图通过引用修改值是行不通的，会导致**编译错误**，例如：
```rust
fn main() {
    let s = String::from("hello");

    change(&s);
}

fn change(some_string: &String) {
    some_string.push_str(", world");
}
```

#### 4.4.2 可变引用
```rust
fn main() {
    let mut s = String::from("hello");

    change(&mut s);
}

fn change(some_string: &mut String) {
    some_string.push_str(", world");
}
```

- 可变引用允许我们修改通过引用访问的数据。
- 但是在任何给定的时间，**只能有一个可变引用**。

#### 4.4.3 多引用的存在性问题
两条原则：
(1) **不可变引用可以同时存在多个**，因为大家都没有修改值的能力，不用担心自己引用的数据会被其他引用修改。
(2) **可变引用在同一时间只能有一个**，因为如果有多个可变引用指向同一数据，那么就无法保证数据的一致性了。

==幸运的是，Rust 的编译器在编译时会自动检测引用的生命周期==
```rust
let mut s = String::from("hello");

let r1 = &s; // 没问题
let r2 = &s; // 没问题
println!("{r1} and {r2}");
// 此位置之后 r1 和 r2 不再使用

let r3 = &mut s; // 没问题
println!("{r3}");
```
不可变引用 `r1` 和 `r2` 的作用域在 `println!` 最后一次使用之后结束，**这发生在可变引用 `r3` 被创建之前**。因为它们的作用域没有重叠，所以代码是可以编译的。**编译器可以在作用域结束之前判断不再使用的引用。**

#### 4.4.4 悬垂引用（Dangling Referances）
在 Rust 中编译器确保引用永远也不会变成悬垂引用：当你拥有一些数据的引用，**编译器确保不允许数据在其引用之前离开作用域。**
案例：
```rust
fn main() {
    let reference_to_nothing = dangle();
}

fn dangle() -> &String {
    let s = String::from("hello");
    &s
}
```
我们仔细分析一下这段代码：

**(1) 内存布局：`String` 在内存中是怎么存的？**

当你写下 `let s = String::from("hello");` 时，内存中其实分成了两部分：
*   **栈（Stack）上**：存放的是变量 `s` 本身。它是一个固定大小的结构体，包含三个字段：**指针**（指向堆内存）、**长度**（Length）和**容量**（Capacity）。
*   **堆（Heap）上**：存放的是真正的字符串内容 `"hello"`。栈上的指针就指向这块堆内存。

**(2) 当函数结束（遇到 `}`）时，发生了什么？**

在 Rust 中，函数体执行完毕意味着该函数的**作用域（Scope）结束**。此时会发生一系列连锁反应：

1. **变量名失效（Variable Name）**
变量名 `s` 是编译时的一个标识。一旦离开作用域，你在后续代码中就再也无法通过 `s` 这个名字来访问任何东西了。
2. **栈空间被回收（Stack Frame）**
==函数运行所在的“栈帧”被弹出==(**任何语言中，函数调用以栈帧为底层本质**)。这意味着存放在栈上的那 3 个字段（指针、长度、容量）所占用的内存被标记为“可用”，也就是**失效**了。
3. **触发 `drop` 函数（堆内存释放）**
这是最关键的一步。由于 `s` 是这块堆内存的**所有者（Owner）**，当所有者离开作用域时，Rust 会自动调用一个名为 `drop` 的特殊函数。
   - `drop` 会立即释放 `s` 指向的那块**堆空间**（即存储 `"hello"` 的地方）。
   - 堆内存被归还给操作系统，不再属于当前程序。

**(3) 为什么返回 `&s` 会产生悬垂引用？**

```rust
fn dangle() -> &String {
    let s = String::from("hello"); // 1. s 创建，拥有堆内存
    &s                             // 2. 返回 s 的引用（即 s 的内存地址）
}                                  // 3. s 离开作用域，栈上的 s 消失，堆上的 "hello" 被销毁
```

*   **返回了什么？** 你返回了一个指向变量 `s` 的地址。
*   **引用了什么？** 此时这个引用指向的是一个**刚刚被回收的栈位置**。
*   **后果：** 接收这个返回值的外部变量，拿到的是一个指向“虚无”或“垃圾数据”的指针。如果 Rust 允许你这样做，程序在读取这个引用时就会崩溃（段错误）。


#### 4.4.5 变量遮蔽、重新赋值与引用
我们观察下面这个例子（✅️）：
```rust
let s = String::from("hello world");
let y = &s;
let s = String::from("hello"); // 遮蔽了上一个 s
// 此时访问 y 会发生什么？
```
**(1) 底层发生了什么？**
1.  编译器在当前函数的栈帧（Stack Frame）里开辟了一块空间给 `s_1`。
2.  `y` 存储了 `s_1` 的地址。
3.  编译器又在栈帧里开辟了一块**新的、独立的**空间给 `s_2`。
4.  **关键点：** 第二个 `let` 只是告诉编译器：“从现在起，当我写 `s` 这个词时，请指向 `s_2`；至于 `s_1`，我不打算再通过名字访问它了。”

**结论：** `s_1` 并没有消失，它依然占据着栈空间，它对堆内存 "hello world" 的**所有权依然存在**。

**(2) 为什么 `s_1` 不会被立即 Drop？**

Rust 的 `drop`（析构）触发时机只有两个：
1.  **主动移动（Move）：** 所有权转交给了别人。
2.  **作用域结束（End of Scope）：** 运行到了代码块的末尾 `}`。

**变量遮蔽（Shadowing）不属于以上任何一种。** 
虽然你无法通过名字 `s` 访问 `s_1` 了，但 `s_1` 这个实体依然存活在当前的 `{}` 作用域内。它必须等到函数结束（或代码块结束）时，由编译器自动插入 `drop(s_1)` 的指令。

**(3) 如果没有 `y` 引用 `s_1`，它会被提前 Drop 吗？**

这是一个进阶细节：**非词法作用域生命周期（NLL, Non-Lexical Lifetimes）**。
在现代 Rust 中，如果编译器发现 `s_1` 被遮蔽后，**后面再也没有任何地方**（比如你的 `y`）用到 `s_1` 相关的内容，为了优化内存，编译器**可能**会提前销毁 `s_1`。
但如果有了 `let y = &s;`：
编译器看到 `y` 还在用，它就会强行保证 `s_1` 必须活到 `y` 最后一次使用的位置之后。


再看下面这个截然不同的例子（❌️）：
```rust
let mut s = String::from("hello world");
let y = &s;
s = String::from("hello"); 
// 此时访问 y 会发生什么？
```
**结论：编译报错，原因：悬垂引用**
- `y` 是对 `s` 的不可变借用（&String）。
- 重新赋值 `s = ...` 的动作，本质上是要销毁旧的 String 并写入新的。这需要对 `s` 拥有写权限（即独占访问）。
- Rust 规则：当存在一个不可变引用（y）时，原对象不能被修改或重新赋值。 否则 y 就会变成悬垂引用。


### 4.5 Slice类型
切片（slice）允许你引用集合中一段连续的元素序列，而不用引用整个集合。slice 是一种引用，所以它不拥有所有权。

#### 4.5.1 字符串Slice
字符串 slice（string slice）是 `String` 中一部分值的引用，它看起来像这样：
```rust
let s = String::from("hello world");
let hello = &s[0..5];
let world = &s[6..11];
```
- `s[starting_index..ending_index]` 的类型是 `str`，str 在 Rust 中是一个“动态大小类型”（DST, Dynamically Sized Type）。**它代表的是内存中的一段连续字节，但编译器在编译时不知道它到底有多长**。Rust 不允许直接将 DST 存放在变量中（==因为变量必须在栈上分配已知大小的空间==）。
- `&s[starting_index..ending_index]` 的类型是 `&str`，它是一个对 `str` 的引用，包含地址和长度，==大小是确定的==
- “字符串 slice” 的类型声明写作 `&str`

我们看一个很经典的例子（❌️）：
```rust
fn main() {
    let mut s = String::from("hello world");

    let word = first_word(&s);

    s.clear(); // 错误！

    println!("the first word is: {word}");
}

fn first_word(s: &String) -> &str {
    let bytes = s.as_bytes();

    for (i, &item) in bytes.iter().enumerate() {
        if item == b' ' {
            return &s[0..i];
        }
    }

    &s[..]
}
```
- `word` 是一个字符串切片 `&str`。它不仅引用了 `s`，还具体引用了 `s` 拥有的堆内存上的部分字节。
- `s.clear()` 需要申请一个可变借用（`&mut self`），因为这个操作会清空堆内存。
- Rust 核心借用规则：**同一时间，要么只能有一个可变借用，要么可以有多个不可变借用，但二者不能共存**。
如果允许执行 `s.clear()`，那么 `word` 指向的那块内存就被释放了，`word` 就失效了。Rust 编译器在**编译阶段就阻止了这种风险**


#### 4.5.2 其他Slice
字符串 slice，正如你想象的那样，是针对字符串的。不过也有更通用的 slice 类型。考虑一下这个数组：
```rust
let a = [1, 2, 3, 4, 5];
```
就跟我们想要获取字符串的一部分那样，我们也会想要引用数组的一部分。我们可以这样做：
```rust
let a = [1, 2, 3, 4, 5];
let slice = &a[1..3];
assert_eq!(slice, &[2, 3]);
```

#### 4.5.3 Deref Coercion（解引用强制转换）
**“解引用强制转换”** 是一个自动挡功能。它解决的是：==“如果函数要的是 &str，但我手里只有 &String，该怎么办？”==
我们当然可以显示转换：
```rust
let s = String::from("hello");
let slice = &s[0..2];
```
实际上，Rust 编译器会自动帮你做这个转换：
```rust
let my_string = String::from("hello");
let word = first_word(&my_string); // 注意：first_word需要传入参数&str，但是这里传的是 &String
```
编译器魔法：`String` 实现了 `Deref<Target = str>`。当编译器发现类型不匹配，但存在 Deref 关系时，它会自动帮你调用 `.deref()`。


## 五. 结构体

### 5.1 定义和实例化结构体
**结构体的定义案例：**
```rust
struct User {
    active: bool,
    username: String,
    email: String,
    sign_in_count: u64,
}
```
**结构体的实例化案例：**
```rust
fn main() {
    let user1 = User {
        active: true,
        username: String::from("someusername123"),
        email: String::from("someone@example.com"),
        sign_in_count: 1,
    };
}
```

- 从结构体中获取值，用`.`
- 如果结构体是可变的，那么我们就可以修改它的字段：
```rust
let mut user1 = ...
user1.email = ...
```
- 整个实例必须是可变的；Rust 并不允许只将某个字段标记为可变
- 注意结构体实例化时，也可能出现**所有权转移问题**

### 5.2 元组结构体
可以定义与元组类似的结构体，称为**元组结构体**（tuple structs）。元组结构体有着结构体名称提供的含义，但没有具体的字段名，只有字段的类型
案例：
```rust
struct Color(i32, i32, i32);
struct Point(i32, i32, i32);
fn main() {
    let black = Color(0, 0, 0);
    let origin = Point(0, 0, 0);
}
```

### 5.3 类单元结构体
- 我们也可以定义一个没有任何字段的结构体！它们被称为 类单元结构体（unit-like structs）因为它们类似于 ()，即“元组类型”一节中提到的 unit 类型。
- 类单元结构体常常在你想要在某个类型上实现 trait 但不需要在类型中存储数据的时候发挥作用.
案例：
```rust
struct AlwaysEqual;
fn main() {
    let subject = AlwaysEqual;
}
```

### 5.4 Debug trait

trait 是 Rust 中非常重要的一个概念，**它定义了某些类型必须实现的方法集合**。当一个类型实现了某个 trait，就意味着这个类型提供了 trait 中定义的所有方法的具体实现。这个概念非常近似于 Python 中的抽象基类。这里我们用 `Debug` trait 来举例说明：

```rust
#[derive(Debug)]
struct Rectangle {
    width: u32,
    height: u32,
}

fn main() {
    let rect1 = Rectangle {
        width: 30,
        height: 50,
    };

    println!("rect1 is {rect1:?}");
}
```

**{:#?}风格：**
```rust
$ cargo run
   Compiling rectangles v0.1.0 (file:///projects/rectangles)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.48s
     Running `target/debug/rectangles`
rect1 is Rectangle {
    width: 30,
    height: 50,
}
```

**dbg!**宏
很强，接收一个表达式的所有权（与 println! 宏相反，后者接收的是引用），打印出代码中调用 `dbg!` 宏时所在的**文件和行号**，以及该表达式的**结果值**，并**返回该值的所有权**。
```rust
#[derive(Debug)]
struct Rectangle {
    width: u32,
    height: u32,
}
fn main() {
    let scale = 2;
    let rect1 = Rectangle {
        width: dbg!(30 * scale),
        height: 50,
    };

    dbg!(&rect1);
}
```
输出
```bash
$ cargo run
   Compiling rectangles v0.1.0 (file:///projects/rectangles)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.61s
     Running `target/debug/rectangles`
[src/main.rs:10:16] 30 * scale = 60
[src/main.rs:14:5] &rect1 = Rectangle {
    width: 60,
    height: 50,
}
```

### 5.5 方法
#### 5.5.1 方法
定义和使用示例：
```rust
#[derive(Debug)]
struct Rectangle {
    width: u32,
    height: u32,
}

impl Rectangle {
    fn area(&self) -> u32 {
        self.width * self.height
    }
}

fn main() {
    let rect1 = Rectangle {
        width: 30,
        height: 50,
    };

    println!(
        "The area of the rectangle is {} square pixels.",
        rect1.area()
    );
}
```

- 在 `area` 的签名中，使用 `&self` 来替代 `rectangle: &Rectangle`，`&self` 实际上是 `self: &Self` 的缩写。在一个 `impl` 块中，`Self` 类型是 `impl` 块的**类型的别名**。方法的第一个参数必须有一个名为 `self` 的 `Self` 类型的参数，所以 Rust 让你在第一个参数位置上只用 `self` 这个名字来简化。注意，我们仍然需要在 `self` 前面使用 `&` 来表示这个方法借用了 `Self` 实例，就像我们在 `rectangle: &Rectangle` 中做的那样。
- 使用方法替代函数，除了可使用方法语法和不需要在每个函数签名中重复 self 的类型之外，其**主要好处在于组织性**。我们将某个类型实例能做的所有事情都一起放入 impl 块中，而不是让将来的用户在我们的库中到处寻找 Rectangle 的功能。

#### 5.5.2 关联函数
- 所有在 impl 块中定义的函数被称为 **关联函数**（associated functions）
- 我们可以定义不以 self 为第一参数的关联函数（**因此不是方法**），因为它们**并不作用于一个结构体的实例**。我们已经使用了一个这样的函数：在 String 类型上定义的 String::from 函数。
- 调用方法：`结构体名::函数名`

## 六. 枚举和模式匹配

### 6.1 枚举
```rust
enum IpAddrKind {
    V4,
    V6,
}

let four = IpAddrKind::V4;
let six = IpAddrKind::V6;
```

### 6.2 将数据放进枚举的变体
```rust
enum IpAddr {
    V4(String),
    V6(String),
}
let home = IpAddr::V4(String::from("127.0.0.1"));
let loopback = IpAddr::V6(String::from("::1"));
```

- 枚举替代结构体还有另一个优势：**每个变体可以处理不同类型和数量的数据**。这一点用结构体/元组的方式无法做到
```rust
enum IpAddr {
    V4(u8, u8, u8, u8),
    V6(String),
}
let home = IpAddr::V4(127, 0, 0, 1);
let loopback = IpAddr::V6(String::from("::1"));
```

```rust
enum Message {
    Quit, // 类单元变体
    Move { x: i32, y: i32 }, // 类结构体变体
    Write(String), // 类元组变体
    ChangeColor(i32, i32, i32), // 类元组变体
}
```

### 6.3 Option枚举
```rust
enum Option<T> {
    None,
    Some(T),
}
```

Rust 引入 `Option<T>` 是为了解决其他编程语言中 `Null` 带来的问题。`Option<T>` 是一个枚举类型，它有两个变体：`Some(T)` 和 `None`。`Some(T)` 表示存在一个值，而 `None` 表示不存在值。
- 为了拥有一个可能为空的值，你必须要显式的将其放入对应类型的 `Option<T>` 中。**接着，当使用这个值时，必须明确的处理值为空的情况**。
- **只要一个值不是 `Option<T>` 类型，你就可以安全的认定它的值不为空。这是 Rust 的一个经过深思熟虑的设计决策**，来限制空值的泛滥以增加 Rust 代码的安全性。

### 6.4 match 控制流结构
`match` 允许我们将一个值与一系列的模式相比较，并根据相匹配的模式执行相应代码。模式可由字面值、变量、通配符和许多其他内容构成
每个分支相关联的代码是一个表达式，而表达式的结果值将作为整个 match 表达式的返回值。
```rust
enum Coin {
    Penny,
    Nickel,
    Dime,
    Quarter,
}
fn value_in_cents(coin: Coin) -> u8 {
    match coin {
        Coin::Penny => 1,
        Coin::Nickel => 5,
        Coin::Dime => 10,
        Coin::Quarter => 25,
    }
}
```

#### 6.4.1 绑定值的模式
```rust
#[derive(Debug)] // 这样可以立刻看到州的名称
enum UsState {
    Alabama,
    Alaska,
    // --snip--
}
enum Coin {
    Penny,
    Nickel,
    Dime,
    Quarter(UsState),
}
```

- 这代表了 Rust 枚举（Enum）中一个非常强大的特性：枚举的变体可以持有**另一个自定义类型（甚至是另一个枚举）作为它的数据**。
- 这种模式在 Rust 中被称为 “**关联数据（Associated Data）**”。 

有了这种模式之后，我们就可以做到：
```rust
fn value_in_cents(coin: Coin) -> u8 {
    match coin {
        Coin::Penny => 1,
        Coin::Nickel => 5,
        Coin::Dime => 10,
        Coin::Quarter(state) => {
            println!("State quarter from {:?}!", state);
            25
        }
    }
}
```
这种设计叫 **代数数据类型（Algebraic Data Types）**。它的好处是：数据和逻辑是紧密结合的。
- 安全性：你不能凭空创建一个没有“州”的 Quarter。编译器会强迫你提供州的信息。
- 表达力：通过这种嵌套，你可以构建非常复杂的逻辑模型。例如，你可以定义一个 IpAddress 枚举，它有的变体存 V4(u8, u8, u8, u8)，有的变体存 V6(String)。这也与 Option<T> 的原理相同，是 Rust 消灭 `null` 的核心设计之一。

#### 6.4.2 匹配Option<T>
比如我们想要编写一个函数，它获取一个 Option<i32> ，如果其中含有一个值，将其加一。如果其中没有值，函数应该返回 None 值，而不尝试执行任何操作。
```rust
fn plus_one(x: Option<i32>) -> Option<i32> {
    match x {
        None => None,
        Some(i) => Some(i + 1),
    }
}
let five = Some(5);
let six = plus_one(five);
let none = plus_one(None);
```

#### 6.4.3 匹配是穷尽的
Rust 知道我们没有覆盖所有可能的情况甚至知道哪些模式被忘记了！Rust 中的匹配是 穷尽的（exhaustive）：必须穷举到最后的可能性来使代码有效。如下这个案例就是❌️的
```rust
fn plus_one(x: Option<i32>) -> Option<i32> {
    match x {
        Some(i) => Some(i + 1),
    }
}
```
==Rust 防止我们忘记明确的处理 None 的情况，这让我们免于假设拥有一个实际上为空的值，从而使之前提到的价值亿万的错误不可能发生。==

#### 6.4.4 通配模式和_占位符
- other => ：其他模式
- _ => ：可以匹配任意值而不绑定到该值，这告诉 Rust 我们不会使用这个值，所以 Rust 也不会警告我们存在未使用的变量。

### 6.5 if let 和 let else 语法糖
`if let` 语法获取通过等号分隔的一个模式和一个表达式。它的工作方式与 `match` 相同
使用 `if let` 意味着编写更少代码，更少的缩进和更少的样板代码。然而，这样会失去 `match` 强制要求的穷尽性检查来确保你没有忘记处理某些情况。
```rust
let config_max = Some(3u8);
if let Some(max) = config_max {
    println!("The maximum is configured to be {max}");
}
```
可以在 `if let` 中包含一个 `else`。`else` 块中的代码与 `match` 表达式中的 `_` 分支块中的代码相同，这样的 `match` 表达式就等同于 `if let` 和 `else`
```rust
let mut count = 0;
if let Coin::Quarter(state) = coin {
    println!("State quarter from {state:?}!");
} else {
    count += 1;
}
```

或者使用`let else`语法糖：
```rust
fn describe_state_quarter(coin: Coin) -> Option<String> {
    let Coin::Quarter(state) = coin else {
        return None;
    };

    if state.existed_in(1900) {
        Some(format!("{state:?} is pretty old, for America!"))
    } else {
        Some(format!("{state:?} is relatively new."))
    }
}
```

## 七. 包、crate和模块

### 7.1 crate, package and rs

#### 7.1.1 核心概念的层级关系

**Package (包) > Crate (单元包) > Module (模块)**

*   **Package (包)**：就是你 `cargo new` 出来的那个**文件夹**。它的标识是目录下必须有一个 `Cargo.toml` 文件。一个包可以包含多个 Crate。
*   **Crate (单元包)**：是 Rust 编译的**最小单位**。编译器（rustc）每次编译的都是一个 Crate。它最终会生成一个可执行文件（Binary）或一个库文件（Library）。
*   **Module (模块)**：是 Crate 内部的代码组织方式（用 `mod` 关键字定义的）。

#### 7.1.2 文件夹与代码的对应关系

当你运行 `cargo new my_project` 时，Cargo 会默认创建一个 **Package**。

**(A) src/main.rs：Binary Crate 的根**
*   **地位**：如果你有这个文件，Cargo 会自动认为这个 Package 包含一个名为 `my_project` 的 **Binary Crate**（二进制单元包）。
*   **特殊之处**：
    *   它是该 Crate 的 **Crate Root**（根文件）。编译器从这里开始读代码。
    *   它必须包含一个 `main` 函数。
    *   编译结果：**一个可执行文件**（在 `target/debug/` 下）。

**(B) src/lib.rs：Library Crate 的根**
*   **地位**：如果你手动创建或通过 `cargo new --lib` 创建了这个文件，Cargo 会认为这个 Package 包含一个名为 `my_project` 的 **Library Crate**（库单元包）。
*   **特殊之处**：
    *   它是该库 Crate 的 **Crate Root**。
    *   它没有 `main` 函数。
    *   编译结果：**一个供别人调用的库**（`.rlib` 文件）。



#### 7.1.3 src/main.rs 和 src/lib.rs 的“潜规则”

这是初学者最容易困惑的地方：**一个 Package 到底能有几个 Crate？**

1.  **一个 Package 最多只能有一个 Library Crate**。即：`src/lib.rs` 只能有一个。
2.  **一个 Package 可以有多个 Binary Crate**。
    *   默认的一个是 `src/main.rs`。
    *   其他的可以放在 `src/bin/` 目录下，比如 `src/bin/another_tool.rs`，每个文件都是一个独立的 Binary Crate。


#### 7.1.4 为什么要区分 main.rs 和 lib.rs？（实战逻辑）

想象你在写一个大型程序（比如一个图片处理器）：

*   **src/lib.rs (Library)**：这里写核心逻辑。比如“如何旋转图片”、“如何调整亮度”。这些代码是通用的，不涉及具体的交互。
*   **src/main.rs (Binary)**：这里只负责交互。它调用 `lib.rs` 里的逻辑。它像是一个“外壳”，负责读取用户输入的命令行参数，然后交给库去处理。

**好处：**
*   你的核心逻辑（lib）可以被其他人的程序引用。
*   你**可以轻松地写多个 Binary（比如一个是命令行工具，一个是图形界面工具），它们都共享同一个核心库。**

### 7.2 定义模块 (Modules)
- **作用**: 将代码分组，控制作用域和私有性。
- **定义方式**: 使用 `mod` 关键字。
  ```rust
  mod front_of_house {
      pub mod hosting {
          pub fn add_to_waitlist() {}
      }
  }
  ```
- **模块树**: 类似于文件系统目录树。
  - `src/main.rs` 和 `src/lib.rs` 是 crate 根。
- **查找规则**: 声明 `mod garden;` 时，编译器会查找：
  1. 内联花括号 `{ ... }`。
  2. `src/garden.rs`。
  3. `src/garden/mod.rs`（旧风格）。

### 7.3 引用路径 (Paths)
- **绝对路径 (Absolute path)**: 从 crate 根开始，以 `crate` 关键字或 crate 名称开头。
  ```rust
  crate::front_of_house::hosting::add_to_waitlist();
  ```
- **相对路径 (Relative path)**: 从当前模块开始，以 `self`、`super` 或当前模块标识符开头。
  ```rust
  front_of_house::hosting::add_to_waitlist();
  ```

### 7.4 私有性与 pub
- **默认私有**: 模块内的项（函数、结构体等）默认对父模块私有。
- **子访父**: 子模块可以访问父模块的项。
- **父访子**: 父模块无法访问子模块的私有项，除非使用 `pub`。
- **pub 关键字**:
  - `pub mod`: 使模块对父模块可见。
  - `pub fn/struct/enum`: 使项可见。
  - **注意**: 仅将模块设为 `pub` 不会自动将其内容设为 `pub`。
- **super**: 访问父模块路径（类似文件系统的 `..`）。
  ```rust
  super::deliver_order();
  ```

### 7.5 结构体与枚举的公有性
- **Struct**: 
  - 结构体设为 `pub`，实际上其字段**仍然是私有**的。
  - 需要单独对每个字段加 `pub`。
  - 必须提供公有的构造函数（如果存在私有字段）。
- **Enum**:
  - 枚举设为 `pub`，则其**所有变体 (variants) 自动变为 `pub`**。

### 7.6 总结前文：经典案例
```rust
mod back_of_house {
    pub struct Breakfast {
        pub toast: String,
        seasonal_fruit: String,
    }

    impl Breakfast {
        pub fn summer(toast: &str) -> Breakfast {
            Breakfast {
                toast: String::from(toast),
                seasonal_fruit: String::from("peaches"),
            }
        }
    }
}

pub fn eat_at_restaurant() {
    // 在夏天订购一个黑麦土司作为早餐
    let mut meal = back_of_house::Breakfast::summer("Rye");
    // 改变主意更换想要面包的类型
    meal.toast = String::from("Wheat");
    println!("I'd like {} toast please", meal.toast);

    // 如果取消下一行的注释代码不能编译；
    // 不允许查看或修改早餐附带的季节水果
    // meal.seasonal_fruit = String::from("blueberries");
}
```

### 7.7 使用 use 关键字将路径引入作用域

**`use` 关键字的作用**：可以创建一个短路径（shortcut），将路径引入作用域，这就类似于在文件系统中创建软连接。
- 一旦将路径引入作用域，就可以直接使用该名称，而不需要写出完整的路径。
- `use` **只能将名称引入到当前作用域**。==这是最核心有用的原则，必须牢记==。

**惯用模式**：
- **函数**：习惯上将**父模块**引入作用域，而不是函数本身。
    - 理由：这样可以清楚地看出函数不是本地定义的。
    ```rust
    // 推荐
    use crate::front_of_house::hosting;
    hosting::add_to_waitlist();

    // 不推荐
    use crate::front_of_house::hosting::add_to_waitlist;
    add_to_waitlist();
    ```
- **结构体、枚举和其他项**：习惯上指定**完整路径**。
    - 理由：这是惯例。
    ```rust
    use std::collections::HashMap;
    let mut map = HashMap::new();
    ```
    - **例外**：如果两个不同模块中有同名的项，则必须引入父模块，或者使用 `as` 关键字重命名。

**使用 `as` 关键字提供新的名称**：
```rust
use std::fmt::Result;
use std::io::Result as IoResult;

fn function1() -> Result { /* ... */ }
fn function2() -> IoResult<()> { /* ... */ }
```

**使用 `pub use` 重导出名称**：
- 当使用 `use` 关键字时，该名称在当前作用域中是**私有**的。
- 如果希望调用代码也能使用该名称，可以使用 `pub use`。这被称为**重导出（Re-exporting）**。
```rust
pub use crate::front_of_house::hosting;
```

**使用外部包（External Packages）**：
1. 在 `Cargo.toml` 中添加依赖（例如 `rand`）。
2. 在代码中使用 `use` 将其引入作用域。
   ```rust
   use rand::Rng;
   ```

**嵌套路径（Nested Paths）**：
当我们需要引入同一个包或模块下的多个项时，可以使用嵌套路径来消除大量的 `use` 行。
```rust
// 普通写法
use std::cmp::Ordering;
use std::io;

// 嵌套写法
use std::{cmp::Ordering, io};

// 引入模块本身及其内部项 (self)
use std::io::{self, Write};
```

**Glob 运算符（Glob Operator）**：
如果希望将一个路径下**所有**公有项都引入作用域，可以使用 `*`。
```rust
use std::collections::*;
```
*常用于测试模块 `tests` 中引入 `super::*`*。


### 7.8 总结前文
**在这个场景下，.rs代码就相当于module，在.rs中用 mod/pub mod 声明的模块实际上相当于声明的是这个.rs module的子module**
事实上，.rs代码确实就是 Module 的一种，mod 和 pub mod 声明的也是子模块。
例如我们对于如下的**文件树**：
```
src/
├── lib.rs            (Crate Root)
├── network.rs        (Module: network)
└── network/          (文件夹，存放 network 的子模块)
    └── client.rs     (Submodule: network::client)
```
对应的**模块树**就是
```
lib.rs (crate root)
├── network (module)
└── network::client (submodule)
```

这一点是“将模块拆分为多个文件的基础”，而且可以知道的是，文件树的结果不等于模块树，除了路径引导外，子模块的构建方式还可以在模块内部使用mod声明子模块，详见下文。

### 7.9 将模块拆分为多个文件
案例：拆分前：
**`src/lib.rs`**
```rust
mod A {
    pub mod B {
        pub fn B_f() {}
    }
}
```

拆分后：
**`src/lib.rs`**
```rust
mod A;
```

**`src/A.rs`**
```rust
pub mod B {
    pub fn B_f() {}
}
```

当然也可以是：
**`src/lib.rs`**
```rust
mod A;
```
这一点一样，然后不一样的是：
**`src/A.rs`**
```rust
mod B;
```

**`src/A/B.rs`**
```rust
pub fn B_f() {}
```

- 因此我们可以看到，**模块树和文件树的关系并不是一一对应的**，以上两种拆分方式有两种文件树结构，**但是它们的模块树结构完全一致。**

- 我们将各个模块的代码移动到独立文件了，同时模块树保持不变。**这个技巧让你可以在模块代码增长时，将它们移动到新文件中。**

## 八. 常见集合
### 8.1 Vector
#### 8.1.1 定义
`Vec<T>` 是一个动态数组，可以在运行时增长或缩小。

#### 8.1.2 创建
```rust
let v: Vec<i32> = Vec::new();
```

**vec!** 宏：这个宏会根据我们提供的值来创建一个新的 vector，Rust 会自动推断 vector 的类型。
```rust
let v = vec![1, 2, 3];
```

#### 8.1.3 插入、访问和删除
**插入**
`.push()`
**访问**
两种方式：
1. 通过索引：`v[0]`（如果索引越界会 panic）
2. 通过 `get` 方法：`v.get(0)`（返回 `Option<&T>`，越界时返回 `None`）

案例：
```rust
let v = vec![1, 2, 3, 4, 5];
let third: &i32 = &v[2];
println!("The third element is {third}");
let third: Option<&i32> = v.get(2);
match third {
    Some(third) => println!("The third element is {third}"),
    None => println!("There is no third element."),
}
```
形如：`let a = v[0];` 之类的操作可能会涉及到所有权转让的问题，这行语句是否会会报错取决于所有权的转让。简单来说：
**是否可以直接通过 `v[0]` 获取值（不加 `&`），取决于 T 是否实现了 `Copy` trait。**

**删除**：
`.pop()`：从 vector 的末尾删除最后一个元素并返回它的值（如果 vector 为空则返回 `None`）。

#### 8.1.4 遍历
使用 `for` 循环来获取 `vector` 中的每一个元素的不可变引用并将其打印：
```rust
let v = vec![100, 32, 57];
for i in &v {
    println!("{i}");
}
```

我们也可以遍历可变 vector 的每一个元素的**可变引用**以便能改变它们。
```rust
let mut v = vec![100, 32, 57];
for i in &mut v {
    *i += 50;
    // 为了修改可变引用所指向的值，必须使用解引用运算符
}
```

> 由于借用检查器的规则，无论可变还是不可变地遍历一个 `vector` 都是安全的。如果尝试在上面两个案例中的 for 循环体内插入或删除项，都会产生编译错误。**`for` 循环中获取的 `vector` 引用阻止了同时对整个 `vector` 进行修改。**

#### 8.1.5 使用枚举存储多种类型
```rust
enum SpreadsheetCell {
    Int(i32),
    Float(f64),
    Text(String),
}

let row = vec![
    SpreadsheetCell::Int(3),
    SpreadsheetCell::Text(String::from("blue")),
    SpreadsheetCell::Float(10.12),
];
```

### 8.2 String
#### 8.2.1 定义
`String` 是 Rust 中一个可增长、可变、UTF-8 编码的字符串类型。它是一个**堆分配的**字符串类型，提供了许多方法来处理文本数据。
其内部表现是一个 `Vec<u8>`

#### 8.2.2 创建
创建一个空字符串：
```rust
let mut s = String::new();
```
从字符串字面值创建：
```rust
let data = "initial contents";
let s = data.to_string();
// 该方法也可直接用于字符串字面值：
let s = "initial contents".to_string();
```
或者：
```rust
let s = String::from("initial contents");
```

#### 8.2.3 更新
**追加字符串**：
```rust
let mut s = String::from("foo");
s.push_str("bar");
```
**追加单个字符**：
```rust
let mut s = String::from("lo");
s.push('l');
```
**使用 + 运算符或 format! 宏拼接字符串**：
```rust
let s1 = String::from("Hello, ");
let s2 = String::from("world!");
let s3 = s1 + &s2; // 注意：s1 的所有权被转移了，s2 被借用了
```

深度分析一下：
```rust
let s3 = s1 + &s2;
```

**(1) 从所有权角度，这一行发生了什么？**
`+` 运算符调用的是 `Add trait` 的一个方法。对于 String 类型，它的方法签名大致如下：
```rust
fn add(self, s: &str) -> String { ... }
```
第一个参数是 `self`，不带`&`，意味着会发生所有权转让。
底层执行过程：
1. 复用内存：Rust 为了效率，并不会创建一个全新的 `String` 然后把 `s1` 和 `s2` 拷贝进去。相反，**它直接接管了 s1 的堆内存缓冲区**。
2. 追加数据：它把 `s2` 的内容追加到 `s1` 那个缓冲区的末尾。
3. 重新包装：最后，它把**这个增长后的缓冲区重新包装成一个新的 String 并返回，赋值给 s3**。

**(2) `s3` 包含了 `s2` 的不可变引用吗？**
不，`s3` 并不包含 `s2` 的引用。

- 在 `add` 函数执行期间，它借用了 `s2` 的内容，并把这些内容**拷贝（Copy）** 到了 `s3` 所拥有的堆内存缓冲区里。
- 一旦 `add` 函数结束，借用就结束了。
- `s3` 和 `s2` 之间没有任何生命周期上的联系。

**format!**宏
返回一个带有结果内容的 **String**，使用引用而不**会获取任何参数的所有权**。
```rust
let s1 = String::from("tic");
let s2 = String::from("tac");
let s3 = String::from("toe");
let s = format!("{s1}-{s2}-{s3}");
```

#### 8.2.4 索引字符串
不能通过`[]`直接访问字符串，因为`String` 是一个 UTF-8 编码的字符串，直接索引可能会导致访问到一个无效的字符边界。

从 Rust 的角度来讲，事实上有三种相关方式可以查看字符串：**字节（Bytes）、标量值（Scalar Values）和字形簇（Grapheme Clusters）**。

#### 8.2.5 遍历字符串的方法
**(1) .chars(): 按 Unicode 标量值（字符）遍历**
这是最常用的方法。它将字节流解析为一个个独立的 Unicode 字符（`char` 类型，每个 `char` **固定占 4 字节**）。
```rust
let s = String::from("你好世界");

for c in s.chars() {
    println!("{}", c);
}
```
- 结果：依次打印出 你, 好, 世, 界。
- 适用场景：处理文本内容、统计字符个数。
- 注意：这里的“字符”是 **Unicode Scalar Value**，但在处理带音标的字符（如 é）或 Emoji 时，一个“人类感觉的字符”**可能由多个 Unicode 标量组成**。

**(2) .bytes(): 按字节遍历**
返回底层的每一个字节（`u8`）。
```rust
let s = String::from("Hi!");

for b in s.bytes() {
    println!("{}", b);
}
```
结果：依次打印出 72, 105, 33（即 H, i, ! 的 **ASCII 码**）。
适用场景：底层协议解析、加密、处理纯 ASCII 文本（性能最高）。
注意：**对于中文等非 ASCII 字符，一个汉字会产生 3 个字节，单独操作这些字节通常没有实际意义**。


### 8.3 HashMap
`HashMap<K, V>` 类型储存了一个键类型 `K` 对应一个值类型 `V` 的映射。它通过一个哈希函数（`hashing function`）来实现映射，决定如何将键和值放入内存中。

哈希 map 是同质的：**所有的键必须是相同类型，值也必须都是相同类型**
#### 8.3.1 创建
```rust
use std::collections::HashMap;
let mut scores = HashMap::new();
scores.insert(String::from("Blue"), 10);
scores.insert(String::from("Yellow"), 50);
```

#### 8.3.2 访问
```rust
let team_name = String::from("Blue");
let score = scores.get(&team_name).copied().unwrap_or(0);
``` 
- `get` 方法返回一个 `Option<&V>`，如果键存在则返回 `Some(&value)`，否则返回 `None`。
- `copied()` 将 `Option<&V>` 转换为 `Option<V>`，**前提是 `V` 实现了 `Copy` trait**。
- `unwrap_or(0)` 在 `Option<V>` 是 `None` 时返回默认值 `0`。

#### 8.3.3 遍历
```rust
for (key, value) in &scores {
        println!("{key}: {value}");
    }
```

#### 8.3.4 哈希 map 和所有权
对于像 i32 这样的实现了 `Copy` trait 的类型，其值可以拷贝进哈希 `map`。对于像 `String` 这样拥有所有权的值，**其值将被移动而哈希 `map` 会成为这些值的所有者**，如示例 8-22 所示：
```rust
use std::collections::HashMap;

let field_name = String::from("Favorite color");
let field_value = String::from("Blue");

let mut map = HashMap::new();
map.insert(field_name, field_value);
// 这里 field_name 和 field_value 不再有效，
// 尝试使用它们看看会出现什么编译错误！
```
如果将值的引用插入哈希 map，这些值本身将不会被移动进哈希 map。**但是这些引用指向的值必须至少在哈希 map 有效时也是有效的。**

#### 8.3.5 插入

**(1) 覆盖一个值**
`.insert(<key>, <value>)` 会将值插入到哈希 map 中，如果该键已存在，则会覆盖其值。
**(2) 只在键不存在时插入**
`.entry(<key>).or_insert(<value>)` 只有在键不存在时才会插入值。
- 如果键 `key` 已存在，`or_insert` 返回一个指向现有值的**可变引用(&mut T)**，==不对值进行修改==。
- 如果键 `key` 不存在，`or_insert` **将插入提供的值**并返回一个指向新值的**可变引用**。
```rust
use std::collections::HashMap;
let mut scores = HashMap::new();
scores.insert(String::from("Blue"), 10);
scores.entry(String::from("Yellow")).or_insert(50);
scores.entry(String::from("Blue")).or_insert(50);
println!("{scores:?}");
```

根据方法二，我们可以实现根据旧值更新新值，方法如下：
```rust
use std::collections::HashMap;
let text = "hello world wonderful world";
let mut map = HashMap::new();
for word in text.split_whitespace() {
    let count = map.entry(word).or_insert(0);
    *count += 1;
}
println!("{map:?}");
```

## 九. 错误处理
### 9.1 panic! 宏
`panic!` 宏会导致程序崩溃并显示一个错误信息。
用法：
```rust
fn main() {
    panic!("crash and burn");
}
```

### 9.2 用 Result 处理可恢复的错误

#### 9.2.1 `Result` 枚举
```rust
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```
`T` 和 `E` 是泛型类型参数；第十章会详细介绍泛型。现在你需要知道的就是 `T` 代表成功时返回的 `Ok` 变体中的数据的类型，而 `E` 代表失败时返回的 `Err` 变体中的错误的类型。
案例：
```rust
use std::fs::File;

fn main() {
    let greeting_file_result = File::open("hello.txt");

    let greeting_file = match greeting_file_result {
        Ok(file) => file,
        Err(error) => panic!("Problem opening the file: {error:?}"),
    };
}
```

**匹配不同的错误**：
```rust
use std::fs::File;
use std::io::ErrorKind;

fn main() {
    let greeting_file_result = File::open("hello.txt");
    let greeting_file = match greeting_file_result {
        Ok(file) => file,
        Err(error) => match error.kind() {
            ErrorKind::NotFound => match File::create("hello.txt") {
                Ok(fc) => fc,
                Err(e) => panic!("Problem creating the file: {e:?}"),
            },
            _ => {
                panic!("Problem opening the file: {error:?}");
            }
        },
    };
}
```

`File::open` 返回的 `Err` 变体中的值类型 `io::Error`，它是一个标准库中提供的结构体。这个结构体有一个返回 `io::ErrorKind` 值的 `kind` 方法可供调用。`io::ErrorKind` 是一个标准库提供的枚举，它的变体对应 io 操作可能导致的不同错误类型。我们感兴趣的变体是 `ErrorKind::NotFound`，它代表尝试打开的文件并不存在。这样，match 就匹配完 `greeting_file_result` 了，不过对于 `error.kind()` 还有一个内层 `match。`

我们希望在内层 `match` 中检查的条件是 `error.kind()` 的返回值是否为 `ErrorKind` 的 `NotFound` 变体。如果是，则通过 `File::create` 尝试创建该文件。然而因为 `File::create` 也可能会失败，还需要在内层 `match` 表达式中增加了第二个分支。当文件不能被创建，会打印出一个不同的错误信息。外层 `match` 的最后一个分支保持不变，这样对任何除了文件不存在的错误会使程序 `panic`。

#### 9.2.2 unwrap 和 expect
`unwrap` 和 `expect` 是 `Result` 类型的两个常用方法，它们提供了更简洁的方式来处理 `Result`，但它们的使用需要谨慎，因为它们会在遇到错误时导致程序崩溃。
- `unwrap`：当 `Result` 是 `Ok` 时返回其中的值；当 `Result` 是 `Err` 时调用 `panic!` 宏并显示错误信息。
- `expect`：与 `unwrap` 类似，**但允许你提供一个自定义的错误信息**，当 `Result` 是 `Err` 时会显示这个信息。
  ```rust
  use std::fs::File;
  fn main() {
      let greeting_file = File::open("hello.txt")
          .expect("hello.txt should be included in this project");
  }
  ```

#### 9.2.3 传播错误
案例：
```rust
use std::fs::File;
use std::io::{self, Read};

fn read_username_from_file() -> Result<String, io::Error> {
    let username_file_result = File::open("hello.txt");

    let mut username_file = match username_file_result {
        Ok(file) => file,  // 文件句柄从 username_file_result 中被提取出来并绑定到 username_file 变量上
        Err(e) => return Err(e),
    };

    let mut username = String::new();

    match username_file.read_to_string(&mut username) {
        Ok(_) => Ok(username),
        Err(e) => Err(e),
    }
}
```

#### 9.2.4 传播错误的快捷方式：`?` 运算符
```rust
use std::fs::File;
use std::io::{self, Read};

fn read_username_from_file() -> Result<String, io::Error> {
    let mut username_file = File::open("hello.txt")?;
    let mut username = String::new();
    username_file.read_to_string(&mut username)?;
    Ok(username)
}
```

`Result` 值之后的 `?` 被定义为与前述案例中定义的处理 `Result` 值的 `match` 表达式有着几乎完全相同的工作方式。如果 `Result` 的值是 `Ok`，这个表达式将会返回 `Ok` 中的值而程序将继续执行。**如果值是 `Err`，`Err` 将作为整个函数的返回值，就好像使用了 `return` 关键字一样，这样错误值就被传播给了调用者**。

> `?` 运算符所使用的**错误值被传递给了 `from` 函数**，它定义于标准库的 `From` trait 中，其用来**将错误从一种类型转换为另一种类型**。当 `?` 运算符调用 `from` 函数时，收到的**错误类型被转换为由当前函数返回类型所指定的错误类型**。这在当函数返回单个错误类型来代表所有可能失败的方式时很有用，即使其可能会因很多种原因失败。

? 运算符消除了大量样板代码并使得函数的实现更简单。我们甚至可以在 ? 之后直接使用链式方法调用来进一步简化代码，例如：
```rust
use std::fs::File;
use std::io::{self, Read};
fn read_username_from_file() -> Result<String, io::Error> {
    let mut username = String::new();
    File::open("hello.txt")?.read_to_string(&mut username)?;
    Ok(username)
}
```

**? 也可用于 `Option<T>` 值**。如同对 `Result` 使用 ? 一样，只能在返回 `Option` 的函数中对 `Option` 使用 `?`。在 `Option<T>` 上调用 `?` 运算符的行为与 `Result<T, E>` 类似：如果值是 `None`，此时 `None` 会从函数中提前返回。如果值是 `Some`，`Some` **中的值会被 `?` 提取出来**作为表达式的返回值同时函数继续。
案例：
```rust
fn last_char_of_first_line(text: &str) -> Option<char> {
    text.lines().next()?.chars().last()
}
```

当然，返回 `Option<T>` 的 `?` 和 `Result<T, E>` 的 `?` 不可以混搭。 

#### 9.2.5 main 函数中的错误传播
`main`函数支持返回：`Result<(), Box<dyn Error>>`，这允许我们在 `main` 函数中使用 `?` 来传播错误。

#### 9.2.6 要不要 `panic!`？

**(1) 什么时候用 panic! (不可恢复)**
- 定义的逻辑错误：如果这个错误发生了，说明程序代码本身写得不对（Bug）。
  例子：数组越界访问、除以零、逻辑上不可能到达的 else 分支。
- 违反“契约”：你的函数要求调用者必须传正数，结果对方传了负数。
- 环境初始化失败：程序启动时必须读取的配置文件缺失，没它程序根本无法运行。
- 原型开发/示例代码：为了快速验证思路，或者写教程演示核心逻辑，不想被复杂的错误处理分散注意力。

**(2) 什么时候用 Result (可恢复)**
- 预料中的失败：这件事本身就有可能失败，且失败是正常的。
  例子：文件不存在、网络连接超时、用户输入的不是数字。
- 库（Library）代码：永远优先选择 Result。作为库的作者，你不应该替调用者决定是否崩溃。你应该把错误“抛”给调用者，由他们决定是尝试重试、换个路径，还是自己崩溃。

记住一句话：==只要涉及到“外部世界”，永远用 Result。==
- 用户是外部世界（会乱输入）。
- 文件系统是外部世界（文件会被删，硬盘会满）。
- 网络是外部世界（会断网，服务器会宕机）。

只有在内存中且逻辑自洽的小世界里，你才有底气说：“这里绝对不会出错，如果错了就是我写 Bug 了，直接 panic 吧。”

## 十. 泛型、trait 和生命周期
### 10.1 泛型

#### 10.1.1 在函数定义中使用泛型

```rust
fn largest(list: &[i32]) -> i32 {}
fn largest(list: &[char]) -> char {}
// ---> ---> ---> ---> 
fn largest<T>(list: &[T]) -> T {}
// 为了开启比较功能，标准库中定义的 std::cmp::PartialOrd trait 可以实现类型的比较功能（查看附录 C 获取该 trait 的更多信息）。依照帮助说明中的建议，我们限制 T 只对实现了 PartialOrd 的类型有效后代码就可以编译了
fn largest<T: std::cmp::PartialOrd>(list: &[T]) -> T {}
```

#### 10.1.2 结构体定义中的泛型
```rust
struct Point<T> {
    x: T,
    y: T,
}

struct Point<T, U> {
    x: T,
    y: U,
}
```

#### 10.1.3 枚举定义中的泛型
```rust
enum Option<T> {
    Some(T),
    None,
}

enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

#### 10.1.4 方法定义中的泛型
```rust
struct Point<T> {
    x: T,
    y: T,
}
impl<T> Point<T> {
    fn x(&self) -> &T {
        &self.x
    }
}
fn main() {
    let p = Point { x: 5, y: 10 };

    println!("p.x = {}", p.x());
}
```

我们**可以为泛型参数选择一个与结构体定义中声明的泛型参数所不同的名称，不过依照惯例使用了相同的名称**。如果你在impl中编写一个声明泛型类型的方法，那么该方法将在任何类型的实例上定义，无论最终用什么具体类型来替换泛型类型。

定义方法时也可以为泛型指定限制（constraint）。例如，可以选择为 Point<f32> 实例实现方法，而不是为泛型 Point 实例。
```rust
impl Point<f32> {
    fn distance_from_origin(&self) -> f32 {
        (self.x.powi(2) + self.y.powi(2)).sqrt()
    }
}
```

#### 10.1.5 泛型的性能
泛型并不会使程序比具体类型运行得慢。
Rust 通过在编译时进行泛型代码的**单态化（monomorphization）**来保证效率。单态化是一个通过填充编译时使用的具体类型，将通用代码转换为特定代码的过程。==编译器寻找所有泛型代码被调用的位置并使用泛型代码针对具体类型生成代码==。

### 10.2 Trait: 定义共同行为
trait 定义了某个特定类型拥有可能与其他类型共享的功能。可以通过 trait 以一种抽象的方式定义共同行为。可以使用 `trait bounds` **指定泛型是任何拥有特定行为的类型**。
一个类型的行为由其可供调用的方法构成。如果可以**对不同类型调用相同的方法**的话，这些类型就可以共享相同的行为了。trait 定义是一种将方法签名组合起来的方法，目的是定义一个实现某些目的所必需的行为的集合。

#### 10.2.1 定义 trait
```rust
pub trait Summary {
    fn summarize(&self) -> String;
}
```
在方法签名后跟分号，而**不是在大括号中提供其实现**。接着每一个实现这个 trait 的类型都需要**提供其自定义行为的方法**。

#### 10.2.2 为类型实现 trait
```rust
pub struct NewsArticle {
    pub headline: String,
    pub location: String,
    pub author: String,
    pub content: String,
}

impl Summary for NewsArticle {
    fn summarize(&self) -> String {
        format!("{}, by {} ({})", self.headline, self.author, self.location)
    }
}

pub struct SocialPost {
    pub username: String,
    pub content: String,
    pub reply: bool,
    pub repost: bool,
}

impl Summary for SocialPost {
    fn summarize(&self) -> String {
        format!("{}: {}", self.username, self.content)
    }
}
```

注意用法：
```rust
impl Summary for NewsArticle {
    fn summarize(&self) -> String {
        // snip
    }
}
```

调用时（可能来自其他 `crate`） trait 必须和类型一起引入作用域以便使用额外的 trait 方法。
但是不能为外部类型实现外部 trait。例如，不能在 `aggregator` crate 中为 Vec<T> 实现 `Display` trait。这是因为 `Display` 和 Vec<T> 都定义于标准库中，它们并不位于 `aggregator` crate 本地作用域中。这个限制是被称为相干性（coherence）的程序属性的一部分，或者更具体的说是 孤儿规则（orphan rule），其得名于不存在父类型。


#### 10.2.3 默认实现
```rust
pub trait Summary {
    fn summarize(&self) -> String {
        String::from("(Read more...)")
    }
}
```
默认实现允许调用相同 trait 中的其他方法，哪怕这些方法没有默认实现。
```rust
pub trait Summary {
    fn summarize(&self) -> String {
        format!("(Read more from {}...)", self.summarize_author())
    }

    fn summarize_author(&self) -> String;
}
```
为了使用这个版本的 `Summary`，只需在为类型实现 `trait` 时定义 `summarize_author` 即可。

#### 10.2.4 使用 trait 作为参数
为 `NewsArticle` 和 `SocialPost` 类型实现了 `Summary` trait，用其来定义了一个函数 `notify` 来调用其参数 `item` 上的 `summarize` 方法，该参数是**实现了 `Summary` trait 的某种类型**。**为此可以使用 `impl` Trait 语法，像这样：**
```rust
pub fn notify(item: &impl Summary) {
    println!("Breaking news! {}", item.summarize());
}
```

#### 10.2.5 `Trait Bound` 语法
`impl` Trait 语法实际上是 `Trait Bound` 的语法糖，`Trait Bound` 的原型如下：
```rust
pub fn notify<T: Summary>(item: &T) {
    println!("Breaking news! {}", item.summarize());
}
```

- `impl` Trait 适合处理简短情况
- `Trait Bound` 适合处理复杂情况，例如当函数有多个参数并且每个参数都需要不同的 trait 时，或者当一个参数需要多个 trait 时。案例：
  ```rust
  // impl Trait
  pub fn notify(item1: &impl Summary, item2: &impl Summary) {}
  // Trait Bound
  pub fn notify<T: Summary>(item1: &T, item2: &T) {}
  ```

**通过 "+" 指定多个 Trait Bound**
```rust
// impl Trait
pub fn notify(item: &(impl Summary + Display)) {}
// Trait Bound
pub fn notify<T: Summary + Display>(item: &T) {}
```

**通过 "where" 简化 Trait Bound**
```rust
fn some_function<T: Display + Clone, U: Clone + Debug>(t: &T, u: &U) -> i32 {
```

```rust
fn some_function<T, U>(t: &T, u: &U) -> i32
where
    T: Display + Clone,
    U: Clone + Debug,
{}
```

#### 10.2.6 返回实现了 Trait 的类型
```rust
fn returns_summarizable() -> impl Summary {
    // 这里我们返回了一个 SocialPost 实例，但我们也可以返回任何其他实现了 Summary trait 的类型
    SocialPost {
        username: String::from("horse_ebooks"),
        content: String::from("of course, as you probably already know, people"),
        reply: false,
        repost: false,
    }
}
```
返回一个只是**指定了需要实现的 trait 的类型的能力**在闭包和迭代器场景十分的有用。例如：
> `impl Trait` 允许你简单的指定函数返回一个 `Iterator` 而无需写出实际的冗长的类型。
这只适用于返回单一类型的情况，返回 `类型A 或 类型B` 是不允许的。


#### 10.2.7 使用 Trait Bound 来条件实现方法
只有那些为 `T` 类型实现了 `PartialOrd` trait（来允许比较） 和 `Display` trait（来启用打印）的 Pair<T> 才会实现 cmp_display 方法，标记方法就是：`<T: Display + PartialOrd>`。
```rust
impl<T: Display + PartialOrd> Pair<T> {
    fn cmp_display(&self) {
        if self.x >= self.y {
            println!("The largest member is x = {}", self.x);
        } else {
            println!("The largest member is y = {}", self.y);
        }
    }
}
```

#### 10.2.8 使用 Trait Bound 来条件实现 trait
```rust
impl<T: Display> ToString for Pair<T> {
    // --snip--
}
```


### 10.3 生命周期

#### 10.3.1 生命周期
Rust 中的**每一个引用都有其生命周期（lifetime）**，也就是**引用保持有效的作用域**
**引用的生命周期必须小于或等于它所引用的值的生命周期。**
典型案例：
错误：❌️
```rust
fn main() {
    let r;                // ---------+-- 'a
                          //          |
    {                     //          |
        let x = 5;        // -+-- 'b  |
        r = &x;           //  |       |
    }                     // -+       |
                          //          |
    println!("r: {r}");   //          |
}                         // ---------+
```

正确：✅️
```rust
fn main() {
    let x = 5;            // ----------+-- 'b
                          //           |
    let r = &x;           // --+-- 'a  |
                          //   |       |
    println!("r: {r}");   //   |       |
                          // --+       |
}                         // ----------+
```

#### 10.3.2 函数中的泛型声明周期
错误案例：❌️
```rust
fn longest(x: &str, y: &str) -> &str {
    if x.len() > y.len() { x } else { y }
}
```
原因：编译器**无法确定返回的引用是指向 `x` 还是 `y`**，因为它们可能具有不同的生命周期。

**生命周期注解语法**
```rust
&i32        // 引用
&'a i32     // 带有显式生命周期的引用
&'a mut i32 // 带有显式生命周期的可变引用
```

**函数签名中的生命周期注解**
我们希望函数签名表达如下限制：也就是这**两个参数和返回的引用存活的一样久**。（两个）参数和返回的引用的生命周期是相关的。就像如下案例中在每个引用中都加上了 'a 那样。
```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```
现在函数签名表明对于某些生命周期 `'a`，函数会获取两个参数，它们都是与生命周期 `'a` 存在的至少一样长的字符串 slice。函数会返回一个同样也与生命周期 `'a` 存在的至少一样长的字符串 slice。它的实际含义是 `longest` 函数返回的引用的生命周期与函数参数**所引用的值的生命周期的较小者一致**

让我们看看如何通过传递拥有不同具体生命周期的引用来限制 `longest` 函数的使用:
正确案例：✅️
```rust
fn main() {
    let string1 = String::from("long string is long");

    {
        let string2 = String::from("xyz");
        let result = longest(string1.as_str(), string2.as_str());
        println!("The longest string is {result}");
    }
}
```

错误案例：❌️
```rust
fn main() {
    let string1 = String::from("long string is long");
    let result;
    {
        let string2 = String::from("xyz");
        result = longest(string1.as_str(), string2.as_str());
    }
    println!("The longest string is {result}");
}
```

**作为人类**，我们可以直观地发现 `string1` 比 `string2` 更长，因此 `result` 会包含指向 `string1` 的引用。因为 `string1` 尚未离开作用域，对于 println! 来说 string1 的引用仍然是有效的。**然而，编译器并不能识别出这种情况**。我们通过生命周期参数告诉 Rust 的是： **`longest` 函数返回的引用的生命周期应该与传入参数的生命周期中较短那个保持一致。**因此，借用检查器不允许示例中的代码，**因为它可能会存在无效的引用**。

当从函数返回一个引用，返回值的生命周期参数需要与一个参数的生命周期参数相匹配。**如果返回的引用没有指向任何一个参数，那么唯一的可能就是它指向一个函数内部创建的值。然而它将会是一个悬垂引用**，因为它将会在函数结束时离开作用域。

综上，生命周期语法是用于**将函数的多个参数与其返回值的生命周期进行关联**的。一旦它们形成了某种关联，Rust 就有了足够的信息来允许内存安全的操作并阻止会产生悬垂指针亦或是违反内存安全的行为。

#### 10.3.3 结构体定义中的生命周期注解
案例：
```rust
struct ImportantExcerpt<'a> {
    part: &'a str,
}
```
这个注解意味着 `ImportantExcerpt` 的实例**不能比其 `part` 字段中的引用存在的更久**。


#### 10.3.4 生命周期省略规则
Rust 有一些**特殊的规则**来推断出函数或方法中引用的生命周期，这些规则被称为生命周期省略规则（lifetime elision rules）。当满足这些规则时，我们就不需要在函数签名中显式地指定生命周期参数了。
函数或方法的参数的生命周期被称为 **输入生命周期（input lifetimes）**，而返回值的生命周期被称为 **输出生命周期（output lifetimes）**

编译器采用三条规则来判断引用何时不需要明确的注解。第一条规则适用于输入生命周期，后两条规则适用于输出生命周期。**如果编译器检查完这三条规则后仍然存在没有计算出生命周期的引用，编译器将会停止并生成错误**。这些规则适用于 `fn` 定义，以及 `impl` 块
- 第一条规则：编译器为每一个引用参数都分配一个生命周期参数
- 第二条规则：如果只有一个输入生命周期参数，那么编译器将会把它赋予所有输出生命周期参数
- 第三条规则：如果方法有 `&self` 或 `&mut self` 作为其中一个参数，那么 `self` 的生命周期将会被赋予所有输出生命周期参数

应用了三个规则之后编译器还没有计算出返回值类型的生命周期，那么编译器就会报错。

#### 10.3.5 方法定义中的声明周期注解
第三条规则的适用场景
```rust
impl<'a> ImportantExcerpt<'a> {
    fn announce_and_return_part(&self, announcement: &str) -> &str {
        println!("Attention please: {announcement}");
        self.part
    }
}
```

#### 10.3.6 静态生命周期
`'static` 生命周期是所有生命周期中最长的一个，**它表示整个程序的持续时间**。字符串字面值拥有 `'static` 生命周期，因为它们被存储在程序的二进制文件中，并且在程序运行期间一直存在。
```rust
let s: &'static str = "I have a static lifetime.";
```


### 10.4 总结
**同时使用泛型类型参数、trait bound 和生命周期注解**：
```rust
use std::fmt::Display;

fn longest_with_an_announcement<'a, T>(
    x: &'a str,
    y: &'a str,
    ann: T,
) -> &'a str
where
    T: Display,
{
    println!("Announcement! {ann}");
    if x.len() > y.len() { x } else { y }
}
```

## 十一 编写自动化测试
### 11.1 如何编写测试
#### 11.1.2 检查结果
样本代码
```rust
pub fn add(left: u64, right: u64) -> u64 {
    left + right
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_works() {
        let result = add(2, 2);
        assert_eq!(result, 4);
    }
}
```

方便在 test 时调用的宏：
- `asset!()`: 断言表达式为真，如果不为真则 panic。
- `assert_eq!()`: 断言两个表达式相等，如果不相等则 panic。
- `assert_ne!()`: 断言两个表达式不相等，如果相等则 panic。

**自定义失败信息**
任何在 `assert!` 的一个必需参数和 `assert_eq!` 和 `assert_ne!` 的两个必需参数之后指定的参数都会传递给 `format!` 宏
案例：
```rust
    #[test]
    fn greeting_contains_name() {
        let result = greeting("Carol");
        assert!(
            result.contains("Carol"),
            "Greeting did not contain name, value was `{result}`"
        );
    }
```

#### 11.1.3 使用 #[should_panic] 检查 panic 是否正确触发
除了检查返回值之外，检查代码是否按照期望处理错误也是很重要的。
```rust
pub struct Guess {
    value: i32,
}

impl Guess {
    pub fn new(value: i32) -> Guess {
        if value < 1 || value > 100 {
            panic!("Guess value must be between 1 and 100, got {value}.");
        }

        Guess { value }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    #[should_panic]
    fn greater_than_100() {
        Guess::new(200);
    }
}
```

为了使 should_panic 测试结果更精确，我们可以给 should_panic 属性增加一个可选的 expected 参数：
```rust
#[should_panic(expected = "less than or equal to 100")]
```

这样会不仅会检测是否触发 `panic!`，还会检查 panic 的错误信息是否包含 "less than or equal to 100" 这个字符串。

### 11.2 控制测试如何运行
`cargo test` 产生的二进制文件的默认行为是并发运行所有的测试，并截获测试运行过程中产生的输出，阻止它们被显示出来，使得阅读测试结果相关的内容变得更容易。不过可以指定命令行参数来改变 `cargo test` 的默认行为。

Rust 默认使用线程来并行运行。这意味着测试会更快地运行完毕，所以你可以更快的得到代码能否工作的反馈。因为测试是在同时运行的，你应该**确保测试不能相互依赖，或依赖任何共享的状态，包括依赖共享的环境，比如当前工作目录或者环境变量**

- 控制线程数量：`cargo test --test-threads=1` 让测试串行运行。
- 失败的测试默认打印输出，如果也想要看到**通过的测试**中打印的输出：`cargo test -- --show-output`。
- 运行单个测试：`cargo test <test_name>` 只运行测试名称中包含 `<test_name>` 的测试。
- 过滤运行多个测试：`cargo test <test_name1> <test_name2>` 只运行测试名称中包含 `<test_name1>` 或 `<test_name2>` 的测试。
- 运行测试模块：`cargo test <module_name>::` 只运行模块 `<module_name>` 中的测试。
- 除非特别指定否则忽略某些测试：`#[ignore]`
  - 当需要运行 ignored 的测试时：`cargo test -- --ignored`
  - 当需要运行全部测试时：`cargo test -- --include-ignored`

### 11.3 单元测试

#### 11.3.1 测试模块和 `#[cfg(test)]`
测试模块的 `#[cfg(test)]` 注解告诉 Rust 只在执行 `cargo test` 时才编译和运行测试代码，而在运行 `cargo build` 时不这么做。

#### 11.3.2 测试私有函数
测试模块是私有函数的**子模块**，因此测试模块中的代码**可以访问父模块中的私有函数**。
```rust
pub fn add_two(a: usize) -> usize {
    internal_adder(a, 2)
}

fn internal_adder(left: usize, right: usize) -> usize {
    left + right
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn internal() {
        let result = internal_adder(2, 2);
        assert_eq!(result, 4);
    }
}
```

### 11.4 集成测试
集成测试的目的是测试库的多个部分能否一起正常工作。

#### 11.4.1 tests 目录
集成测试放在 `tests` 目录(与 `src` 目录同级)中。每个文件都是一个独立的 crate。
因为每一个 tests 目录中的测试文件都是完全独立的 crate，所以需要将库引入到每个测试 crate 的作用域中。
并不需要将 `tests/integration_test.rs` 中的任何代码标注为 `#[cfg(test)]`。 tests 文件夹在 Cargo 中是一个特殊的文件夹，Cargo 只会在运行 `cargo test` 时编译这个目录中的文件。
可以使用 cargo test 的 `--test` 后跟文件的名称来运行某个特定集成测试文件中的所有测试：
```bash
cargo test --test integration_test
```

#### 11.4.2 集成测试中的子模块
如果需要在集成测试中使用子模块，可以在测试文件中定义一个模块，并将测试函数放在该模块(mod.rs)中。示例：
```
├── Cargo.lock
├── Cargo.toml
├── src
│   └── lib.rs
└── tests
    ├── common
    │   └── mod.rs
    └── integration_test.rs
```

用法：integration_test.rs:
```rust
use adder::add_two;

mod common;

#[test]
fn it_adds_two() {
    common::setup();

    let result = add_two(2);
    assert_eq!(result, 4);
}
```

## 十二. 实战：构建一个命令行程序

一些技巧：
**(1) Vec<String> 的问题**
这段代码有误❌️
```rust
let args: Vec<String> = env::args().collect();
let query = &args[1];
```
原因：因为这样会在 vector 内部产生一个空洞，Rust 不允许 vector 出现空洞，否则到了 vector 离开作用域时，内存会被二次释放

**(2) std::fs**
`fs::read_to_string` 返回 `Result<String>`

**(3) 返回 `Result` 而不是调用 `panic!`**
接着修改 `main` 将 `Err` 成员转换为对用户更友好的错误，而不是 `panic!` 调用产生的关于 thread `'main'` 和 RUST_BACKTRACE 的文本。

**(4) unwrap_or_else**
```rust
let config = Config::build(&args).unwrap_or_else(|err| {
        panic!("Problem parsing arguments: {err}");
        process::exit(1);
        }
    );
```
它定义于标准库的 `Result<T, E>` 上。使用 `unwrap_or_else` 可以进行一些自定义的非 `panic!` 的错误处理。当 `Result` 是 `Ok` 时，这个方法的行为类似于 `unwrap`：它返回 `Ok` 内部封装的值。然而，当其值是 `Err` 时，该方法会调用一个闭包（closure），也就是一个我们定义的作为参数传递给 `unwrap_or_else` 的匿名函数。

**(5) run**
我们将提取一个叫做 `run` 的函数来存放目前 `main` 函数中**不属于设置配置或处理错误的所有逻辑**。

**(6) trait 对象 Box<dyn Error>**
前只需知道 `Box<dyn Error>` 意味着函数**会返回实现了 `Error` trait 的类型**，**不过无需指定具体将会返回的值的类型**。
这提供了在**不同的错误场景可能有不同类型的错误返回值的灵活性**。这也就是 `dyn`，它是“动态的”（“dynamic”）的缩写。

**(7) 编写测试**
```rust
        let contents = "\
Rust:
safe, fast, productive.
Pick three.";
```
注意双引号之后的反斜杠，这告诉 Rust 不要在字符串字面值内容的开头加入换行符

**(8) 生命周期**
```rust
// 在这个案例中，返回值的声明周期应该与 contents 参数相关联
// 换句话说，我们告诉 Rust 函数 search 返回的数据将与 search 函数中的参数 contents 的数据存在的一样久。
// 解惑：“生命周期不应该跟更短的那个参数相同吗？”
// 你提到的“跟最短的那个一致”通常发生在你同时使用了两个参数作为数据源的情况下。
pub fn search<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    vec![]
}
```
在 Rust 中标记生命周期的金律：**看数据的来源**。
- 谁是数据的源头：**返回的引用（指针）指向哪块内存，就把谁和返回值绑定在一起**。
- 为什么标记：为了防止“皮之不存，毛将焉附”。contents 是皮，返回的切片是毛。

**(9) 标准输出与标准错误**

- `stdout`: 标准输出，通常用于正常的程序输出。
- `stderr`: 标准错误，通常用于输出错误信息。
- `println!()`: 默认将输出发送到标准输出。
- `eprintln!()`: 将输出发送到标准错误。

## 十三. 函数式语言特性：迭代器与闭包
Rust 的 闭包（closures）是可以**保存在变量中或作为参数传递给其他函数的匿名函数**。你可以在一个地方创建闭包，然后在不同的上下文中执行闭包运算。
不同于函数，**闭包允许捕获其被定义时所在作用域中的值**。我们将展示这些闭包特性如何支持代码复用和行为定制。

### 13.1 闭包

#### 13.1.1 闭包
在 Rust 里，闭包就是“短工”函数。
- 普通函数 (`fn`)：是“正式员工”。它定义在外面，很独立。它不知道你在函数外面定义了什么变量，除非你通过参数传给它。
- 闭包 (`||`)：是“临时工”。它直接写在代码逻辑里。它最大的特权是：它可以直接拿它“出生环境”里的变量来用。

#### 13.1.2 闭包的写法
```rust
fn main() {
    // 闭包写法 1：最全的写法（带类型，带花括号）
    let add_one_v2 = |x: i32| -> i32 { x + 1 };

    // 闭包写法 2：常用的“偷懒”写法（编译器自动推导类型，去掉了花括号）
    let add_one_v3 = |x| x + 1;

    // 调用方式和函数一模一样
    println!("{}", add_one_v3(5)); // 输出 6
}
```

#### 13.1.3 闭包的三种捕获方式

- 只读党 (`Fn`)：闭包里**只是读了一下外面的变量，没改它**。
  特点：这种闭包最温和，**可以被多次调用**。
  例子：`|x| x + secret`（只读了 secret）。
  这本只是一种**不可变借用**，**也就是说闭包存在期间，外边的变量不能被修改了**。
- 篡改党 (`FnMut`)：闭包里**修改了外面的变量**（前提是变量得是 `mut` 的）。
  特点：因为它要改状态，所以调用它时，闭包自己也得是 `mut` 的。
  例子：计数器。
  ```rust
  let mut count = 0;
  let mut add_count = || { 
        count += 1; // 修改了外面的 count
        println!("Count: {}", count); 
  };
  add_count(); // 1
  add_count(); // 2
  ```
- 一次性党 (FnOnce)：闭包把外面的变量**吃掉（Move）**了。
  特点：因为**变量的所有权被它拿走**了，所以这个闭包只能被调用一次。**用完一次后，闭包连同它肚子里的变量一起报废**。
  例子：
  ```rust
  let real_consume_s = || {
        println!("我要打印 s: {}", s);
        
        // 【关键操作】：显式销毁 s，或者把 s 移交给别人
        // drop 函数要求传入所有权，所以闭包必须把 s 从外面“抢”进来
        drop(s); 
    }; 
  ```

#### 13.1.4 `move` 关键字：强制闭包获取外部变量的所有权
`move` 的作用：**强制闭包把用到的变量打包带走（获取所有权）**。
```rust
use std::thread;

fn main() {
    let key = String::from("SecretKey");

    // 错误写法：
    // thread::spawn(|| println!("{}", key)); 
    // 报错：虽然闭包只想读 key，但主线程可能先结束，key 就没了。

    // 正确写法：
    thread::spawn(move || {
        // move 就像是把 key 塞进了闭包的背包里，彻底归闭包所有
        println!("在子线程中: {}", key);
    }).join().unwrap();
    
    // println!("{}", key); // 这里报错！因为 key 已经被 move 进子线程了
}
```


### 13.2 迭代器(iterator)
#### 13.2.1 迭代器及其用法
在 Rust 中，迭代器是惰性的（lazy），这意味着在调用消费迭代器的方法之前不会执行任何操作。例如:
```rust
let v1 = vec![1, 2, 3]
let v1_iter = v1.iter();
```

用法：
```rust
for val in v1_iter {
    println!("Got: {val}");
}
```

#### 13.2.2 `next` 方法

迭代器的核心方法是 `next`，它返回迭代器中的下一个元素(Some)。**当迭代器结束时，`next` 返回 `None`**。
```rust
pub trait Iterator {
    type Item;

    fn next(&mut self) -> Option<Self::Item>;

    // 此处省略了方法的默认实现
}
```
- `next` 方法要自己实现
- 类似 Python(PyTorch) 中的 `__getitem__`
- 迭代器的 `.next()` 方法可以直接调用
  ```rust
  let mut v1_iter = v1.iter();
  assert_eq!(v1_iter.next(), Some(&1));
  ```

#### 13.2.3 所有权问题
- 从 `next` 调用中获取的值是对 vector 中值的不可变引用。`iter` 方法生成一个**不可变引用的迭代器**。
- 如果我们需要一个获取 v1 所有权并**返回拥有所有权**的迭代器，则可以调用 `into_iter` 而不是 `iter`。
- 类似地，如果我们希望**迭代可变引用**，可以调用 `iter_mut` 而不是 `iter`。

#### 13.2.4 迭代器适配器
迭代器适配器是定义在 `Iterator` trait 上的**方法**，它们**返回一个新的迭代器**，这个迭代器在原有迭代器的基础上进行了某些处理。
- `map`：接受一个闭包作为参数，闭包会被应用到迭代器的每个元素上，并返回一个新的迭代器，新的迭代器会产生闭包返回的值。
- `filter`：接受一个闭包作为参数，闭包会被应用到，迭代器的每个元素上，并返回一个新的迭代器，新的迭代器会产生闭包返回值为 `true` 的元素。
- `take`：接受一个整数 `n` 作为参数，并返回一个新的迭代器，这个迭代器会产生前 `n` 个元素。
- `zip`：接受另一个迭代器作为参数，并返回一个新的迭代器，这个迭代器会产生一个元组，元组的第一个元素来自第一个迭代器，第二个元素来自第二个迭代器。

案例：
```rust
let v1: Vec<i32> = vec![1, 2, 3];
v1.iter().map(|x| x + 1);
```
上述代码实际上并没有做任何事；**所指定的闭包从未被调用过。警告提醒了我们原因所在：迭代器适配器是惰性的，因此我们需要在此处消费迭代器。**

消费方法例如：
- `sum`：消费迭代器，**将迭代器中的所有元素相加并返回总和**。
- `collect`：消费迭代器，**将迭代器中的所有元素收集到一个集合中**，例如 `Vec<T>` 或 `HashMap<K, V>`。

```rust
let v1: Vec<i32> = vec![1, 2, 3];
let v2: Vec<_> = v1.iter().map(|x| x + 1).collect();
assert_eq!(v2, vec![2, 3, 4]);
```


### 13.3 使用迭代器改进前面的 I/O 项目

#### 13.3.1 `build` 函数从接受 `&[String]` 改编为接受迭代器
```rust
impl Config {
    pub fn build(
        mut args: impl Iterator<Item = String>,
    ) -> Result<Config, &'static str> {
        // --snip--
```

注意，这里用到了 `Trait Bound` 的语法糖 `impl Trait`，即：
- `mut args` 是要传入的参数，并且根据前文，是一个迭代器
- `impl Iterator<Item = String>` 是参数的类型，表示任何实现了 `Iterator` trait 且其 `Item` 类型为 `String` 的类型。

### 13.4 性能对比：循环 VS 迭代器
为了决定是否使用循环或迭代器，你需要了解哪个实现更快：使用显式 `for` 循环的 `search` 函数版本，还是使用迭代器的版本。

关键在于：**迭代器，作为一个高级的抽象，被编译成了与手写的底层代码大体一致性能的代码。迭代器是 Rust 的零成本抽象（zero-cost abstractions）之一**，它意味着抽象并不会引入额外的运行时开销，它与本贾尼·斯特劳斯特卢普（C++ 的设计和实现者）在《Foundations of C++》（2012）中所定义的零开销（zero-overhead）如出一辙：
> In general, C++ implementations obey the zero-overhead principle: What you don’t use, you don’t pay for. And further: What you do use, you couldn’t hand code any better.