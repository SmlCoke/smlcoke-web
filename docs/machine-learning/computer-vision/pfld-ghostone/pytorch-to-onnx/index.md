# PyTorch to ONNX

```python
def reparameterize_model(model: torch.nn.Module) -> torch.nn.Module:
    """ Method returns a model where a multi-branched structure
        used in training is re-parameterized into a single branch
        for inference.
    :param model: MobileOne model in train mode.
    :return: MobileOne model in inference mode.
    """
    # Avoid editing original graph
    model = copy.deepcopy(model)
    for module in model.modules():
        if hasattr(module, 'reparameterize'):
            module.reparameterize()
    return model
```
这个函数在使用 `for module in model.modules():` 遍历模型中的各个模块时是如何便利的？在 base_module.py 定义自己的 block 和 bottleneck 时多次执行了类定义，并且继承了`nn.module`，并且这些 `block/bottleneck`内部又包含了其他模块例如`ReLU`, `Identity`, `Conv2d`, `BatchNorm2d`等。这些模块具有互相包含的关系，在遍历时不会重复吗？此外，具有reparameterize属性的模块执行`reparameterize()`后，这些新增的模块会再遍历一次吗？

**(1) model.modules() 的遍历机制**
`model.modules()` 采用的是 **深度优先 (Depth-First)** 的递归遍历方式。它会返回模型网络中所有的 nn.Module 实例，包含“父模块”和“子模块”。

举个具体的例子
假设 PFLD_GhostOne 结构如下（简化版）：
```
PFLD_GhostOne (整个模型)
├── backbone (GhostOneBottleneck)
│   ├── ghost_conv (Sequential)
│   │   ├── 0: GhostOneModule
│   │   │   ├── primary_conv (MobileOneBlock)  <--- 目标
│   │   │   │   ├── rbr_conv (ModuleList)
│   │   │   │   └── ...
│   │   │   └── cheap_operation (MobileOneBlock) <--- 目标
```
当执行 `for module in model.modules():` 时，迭代器生成的顺序是这样的：

1. PFLD_GhostOne (自己, Root)
2. GhostOneBottleneck (backbone)
3. Sequential (ghost_conv)
4. GhostOneModule (第0层)
5. MobileOneBlock (primary_conv) <-- 这里触发 reparameterize
6. ModuleList (rbr_conv)
7. Sequential (rbr_conv[0])
8. Conv2d inside rbr_conv[0]
9. BatchNorm2d inside rbr_conv[0]
10. ...
11. MobileOneBlock (cheap_operation) <-- 这里触发 reparameterize
12. ...


**(2) 关于“重复”与“包含关系”**
问：这些模块具有互相包含的关系，在遍历时不会重复吗？

答：**会包含所有层级，但同一个对象实例只会出现一次（除非在定义时同一个对象用了两次）。**

`model.modules()` 确实会把“父亲”、“儿子”、“孙子”都遍历一遍。

- 当遍历到 GhostOneModule (父) 时，`hasattr(module, 'reparameterize')` 为 False (假设它没定义这个方法)，所以跳过。
- 当遍历到 MobileOneBlock (子) 时，`hasattr(module, 'reparameterize')` 为 True，执行重参数化。
- 当遍历到 Conv2d (孙子) 时，`hasattr(module, 'reparameterize')` 为 False，跳过。
关键点： 这种机制确保了我们不需要知道 MobileOneBlock 藏在哪一层，只要它是 `nn.Module` 的一员，迭代器最终一定会“钻”到它面前。

**(3) 一边遍历一边修改 (最核心的问题)**
问：具有 `reparameterize` 属性的模块执行 `reparameterize()` 后，这些新增的模块会再遍历一次吗？

答：通常不会，且在这个特定场景下是安全的。

这是 **Python 生成器 (generator) 的特性**决定的。

1. 快照机制 (类比):
  `model.modules()` 本质上是在调用 `self.named_modules()`。PyTorch 在开始迭代的那一瞬间，根据当前的计算图结构生成了一个生成器。

2. reparameterize() 干了什么？
  让我们看 base_module.py 的代码：
  ```python
  def reparameterize(self):
    # ...
    # 1. 创建新层
    self.reparam_conv = nn.Conv2d(...)
    # 2. 删除旧层
    self.__delattr__('rbr_conv')
    # ...
  ```
  它是在当前正在遍历的 MobileOneBlock **对象内部动态添加了一个属性 reparam_conv 并删除了 rbr_conv**。

3. 迭代器的行为:
  - 当遍历到 MobileOneBlock 时，Python 的**迭代器已经“进入”了这个节点**。
  - 虽然在内部添加了新成员 `self.reparam_conv`，但标准的 Python **深度优先遍历迭代器通常不会动态地去把刚刚插入到当前节点下的新子节点加入到当前正在进行的迭代队列中去**（因为它已经处理过当前节点的子节点列表生成步骤了，或者说 modules() 的递归逻辑通常是预先确定的）。
  - 即便它遍历到了新加的 `Conv2d`：也没关系，因为 `Conv2d` 没有 `reparameterize` 方法，会被直接忽略。
  - 关于被删除的子模块 (`rbr_conv`): 迭代器在进入 MobileOneBlock 之前就**已经生成了包含 `rbr_conv` 的列表**，那么迭代器接下来可能会访问 `rbr_conv`。但因为在 MobileOneBlock 层级把它删了 (`__delattr__`)，**这只是切断了父子引用**。如果迭代器里还存着它的引用，它依然会被访问一次，但同样因为没有 `reparameterize` 方法而被忽略。
