# Markdown 写作规范

这页是给这个站点后续写文章用的。目标不是把 Markdown 写复杂，而是用少量稳定写法，让页面自动吃到现在这套样式。

## 1. 推荐结构

### 课程笔记

1. `# 标题`
2. 一段 2-4 句的开场，说明本章解决什么问题
3. `##` 作为大章节
4. `###` 作为知识点
5. `####` 作为“结论 / 公式 / 注意事项 / 推导步骤”这类强锚点

### 工具教程

1. 先写结果和适用环境
2. 再写安装 / 配置 / 验证
3. 命令行尽量放代码块，不要塞进正文
4. 易错点用 `[[[ warning`

### 博客随笔

1. 用 `##` 分段，不要每段都下钻太深
2. 引用、代码、图片三类内容尽量分开
3. 一屏内只保留一个主信息点

## 2. 最常用增强语法

### 提示框

```markdown
[[[ note "背景"
    这里写背景信息。

[[[ tip "结论"
    这里写最值得记住的结论。

[[[ warning "注意"
    这里写风险、坑点或前提条件。
```

### 标签页

适合放多种命令、不同平台写法或多段对照代码。

````markdown
=== "PowerShell"

    ```powershell
    git status
    ```

=== "Bash"

    ```bash
    git status
    ```
````

### 公式

行内公式继续用 `$...$`，块级公式继续用 `$$...$$`。

```markdown
这是行内公式 $CPI = \frac{cycles}{instructions}$。

$$
CPU\ 时间 = IC \times CPI \times Clock\ Cycle\ Time
$$
```

### 任务列表

```markdown
- [x] 完成配置
- [ ] 补测试页面
```

## 3. 站点新增的可复用样式

### 章节摘要

```markdown
<div class="chapter-summary">

**本章结论**

- 先看响应时间
- 再拆成 IC / CPI / 时钟周期
- 优化通常是多目标权衡

</div>
```

### 术语卡片

```markdown
<div class="term-grid">
  <div class="term-card">
    <div class="term-card__title">Setup Time</div>
    时钟到来前数据需要稳定的最短时间。
  </div>
  <div class="term-card">
    <div class="term-card__title">Hold Time</div>
    时钟到来后数据仍需保持稳定的时间。
  </div>
</div>
```

### 图片说明

```markdown
<div class="media-frame">

[[](image.webp)

<div class="figure-caption">图 1. 数据通路与控制通路关系</div>

</div>
```

## 4. 写作上的小约定

- 一个段落只讲一个动作或一个判断。
- 长段落优先拆成列表，不要靠很多加粗硬撑层级。
- `####` 现在已经有强样式了，适合放“小结论 / 小公式 / 小步骤”。
- 行内代码只放短符号、命令、变量名；长命令放代码块。
- 表格只用于对比，不要把整篇正文塞成表。

## 5. 一个稳妥模板

````markdown
# 标题

一句话说明这篇笔记解决什么问题。

<div class="chapter-summary">

**先看结论**

- 结论 A
- 结论 B
- 结论 C

</div>

## 背景

[[[ note "问题是什么"
    用 2-4 句交代上下文。

## 核心公式

#### 公式

$$
...
$$

#### 含义

- ...

## 实现或例子

```text
...
```
````
