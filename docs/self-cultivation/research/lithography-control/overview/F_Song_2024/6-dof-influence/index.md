你这次的思路里有一个非常重要的区分已经抓到了，但也混合了两件不同的事：

> “某个 DOF 的 setpoint 是否随时间变化”  
> 和  
> “这个 DOF 是否需要一直闭环控制”

这两件事不是一回事。把它们分开以后，第 1 个问题会清晰很多。

先给结论：

- 对 \(\theta_z\) 而言，你的直觉基本正确：**在一次 exposure scan 中，它通常希望尽量保持恒定，而不是不停做复杂 trajectory planning。**
- 对 \(z,\theta_x,\theta_y\) 而言则不同：因为 wafer surface 有实际的 3-D topology，它们确实可能随着 \(x,y\) 扫描位置而持续变化。
- 即便某个 setpoint 是常数，比如 \(\theta_{zr}[k]\equiv \theta_0\)，对应的 feedback loop 仍然必须每个 sample 持续执行，因为 actual \(\theta_z[k]\) 会受扰动而偏离 \(\theta_0\)。
- Song 明确说 vertical setpoints 来自 wafer measurement 阶段生成的 **3-D map**。所以你最后关于 mapping 的判断是对的。Motion_Control_of_Wafer_Scanner…

下面逐层拆开。

---

## 1. 先修正一个隐含假设：6 DOF 控制 ≠ 6 DOF 都有复杂的时变 trajectory

你现在可能潜意识里把 Section IV 和 Section V 连成了：

\[
\text{6 DOF}
\Rightarrow
\text{每个 DOF 都产生复杂 S-curve}
\Rightarrow
\text{每个 DOF 都不断变化}.
\]

其实不是。

更准确应该是：

\[
\boxed{
\text{每个 DOF 都有 reference/setpoint stream}
}
\]

但这个 stream 可以是：

- 高速变化；
- 缓慢变化；
- piecewise constant；
- 甚至长时间完全 constant。

比如 exposure scan 的主扫描轴 \(y\)：

\[
y_r(t)
\]

一定是复杂的：

\[
\text{acceleration}
\rightarrow
\text{constant velocity scan}
\rightarrow
\text{deceleration}.
\]

而某一次 scan 中的 yaw：

\[
\theta_{zr}(t)
\]

完全可能就是：

\[
\boxed{\theta_{zr}(t)=\theta_0}
\]

从 scan 开始到结束保持不变。

这仍然是一个合法的 setpoint trajectory，只不过它是常数函数。

---

# 2. Butler 2011 实际上明确支持你的直觉：曝光扫描时 yaw 尽量保持不变

这个地方非常有意思，因为 Butler 2011 比 Song 2024 讲得更直接。

Butler 在推 horizontal Gain Scheduling 时明确写道：

> during an exposure scan，yaw rotation 尽量保持 constant。

同时他紧接着指出，绕另外两个轴的 rotation velocities 可以更大，因为它们用于 **wafer surface tracking**。[ResearchGate](https://www.researchgate.net/publication/265509162_Position_Control_in_Lithographic_Equipment)

所以你问：

> “如果 wafer 的 grid rotation 校准好了，\(\theta_z\) 为什么还要不停改变？”

答案是：

\[
\boxed{\text{它不一定需要不停改变。}}
\]

至少对于 Butler 描述的典型 exposure scan，恰恰是：

\[
\dot\theta_z\approx0,\qquad
\ddot\theta_z\approx0.
\]

这也是他后面简化 GS 公式的原因之一。[ResearchGate](https://www.researchgate.net/publication/265509162_Position_Control_in_Lithographic_Equipment)

因此，我们上一轮如果让你形成了“6 个 DOF 都持续有复杂 trajectory”的印象，这里应该明确修正。

---

# 3. 那为什么 \(\theta_z\) controller 仍然必须每个 sample 工作？

因为：

\[
\boxed{
\text{constant reference}
\neq
\text{open loop / no control}.
}
\]

假设 alignment 得到：

\[
\theta_{zr}=20\ \mu{\rm rad}.
\]

那么整个 scan 期间可能都是：

\[
\theta_{zr}[0]
=
\theta_{zr}[1]
=
\cdots
=
20\ \mu{\rm rad}.
\]

但实际 stage orientation：

\[
\theta_z[k]
\]

并不会自动永远等于这个值。

因为有：

- actuator force disturbance；
- reaction forces；
- mechanical vibration；
- crosstalk；
- model uncertainty；
- sensor noise；
- structural modes；
- WS 本身剧烈 \(x/y\) acceleration 带来的动态影响。

所以每个 control cycle 仍然计算：

\[
e_{\theta_z}[k]
=
\theta_{zr}[k]-\theta_z[k]
\]

然后：

\[
e_{\theta_z}[k]
\rightarrow C_{\rm fb}
\rightarrow T_z[k].
\]

因此有一个非常重要的控制概念：

> **setpoint generator 决定“你想去哪”；feedback controller 负责“确保你真的在那里”。**

即使“我想待在原地”，feedback controller 也不能停。

---

# 4. 那 \(\theta_z\) 是否可能在不同曝光任务之间发生改变？

可以，但这里要区分“论文明确说了什么”和“进一步的工程可能性”。

Song 这篇论文在这一段只把 \(\theta_z\) 说成 alignment 所需要的 rotation，并没有详细建立一个“wafer alignment map → \(\theta_z(x,y)\)”算法。因此不能从 Song 直接推出：

\[
\theta_{zr}=\theta_{zr}(x,y)
\]

一定存在。

最简单的情况完全可以是整片 wafer 得到一个 global yaw correction：

\[
\theta_{zr}=\theta_0
\]

然后整个 wafer 基本保持这个值。

更复杂的实际 overlay/alignment system 当然可能考虑非理想 wafer grid deformation 等因素，但这已经超出当前 Song/Butler 这两篇论文在这里明确给出的内容。

所以你目前做算法库时不要擅自记：

> “\(\theta_z\) 是复杂的时变 trajectory。”

更稳妥的是：

> **\(\theta_z\)：alignment DOF；scan 内通常近似 constant，但仍持续闭环控制。**

---

# 5. \(z,\theta_x,\theta_y\) 就真的不一样了

这一部分你的思维链基本正确。

Song 在 Section V 开头明确说：

\[
z,\theta_x,\theta_y
\]

用于：

> **maintain the wafer surface in the focal plane of the lens。**

Motion_Control_of_Wafer_Scanner…

为什么它们可能必须随时间变化？

因为实际 wafer surface 不是一个完美平面：

\[
z=h(x,y).
\]

可能存在：

- bow；
- warp；
- local height variation；
- chuck/wafer surface nonflatness；
- 装夹造成的局部 tilt。

所以假设 WS 正沿着：

\[
y=y_r(t)
\]

扫描。

那么 lens 下方所对应 wafer surface 的高度实际上可能是：

\[
h(x_r(t),y_r(t)).
\]

因此理想的 vertical reference 就可能随时间变化：

\[
z_r(t)
=
f_z\!\left(
h(x_r(t),y_r(t))
\right).
\]

同时，如果局部 wafer surface 的 tangent plane 在变化，那么 roll/pitch reference 也要变化：

\[
\theta_{xr}(t),\qquad
\theta_{yr}(t).
\]

Butler 对这一点讲得很明确：绕 \(x/y\) 的 rotational velocity 可以比 yaw 明显得多，因为它们负责 **wafer surface tracking**；他甚至说这些 vertical rotations 可能具有较大的 acceleration，具体取决于 wafer 的 vertical topology。[ResearchGate](https://www.researchgate.net/publication/265509162_Position_Control_in_Lithographic_Equipment)

所以这里你可以建立一个很重要的对比：

\[
\boxed{
\theta_z:
\text{主要对应平面内 alignment}
}
\]

而

\[
\boxed{
z,\theta_x,\theta_y:
\text{主要对应 focus / wafer surface tracking}
}
\]

它们的时变性质完全不同。

---

# 6. “如果 wafer 只是整体倾斜，那不是一次调好就可以了吗？”

完全正确。

如果 wafer 真的是一个严格平面：

\[
h(x,y)=ax+by+c
\]

而且这种倾斜固定，那么理论上通过一次：

\[
z,\theta_x,\theta_y
\]

姿态调整，就可以把这个平面与 lens focal plane 对齐。

之后：

\[
\theta_{xr},\theta_{yr}
\]

都可以保持恒定。

真正让它们需要动态跟踪的是：

\[
\boxed{
h(x,y)\text{ 不是一个平面}
}
\]

比如更真实地：

\[
h(x,y)
=
ax+by+c
+
h_{\rm bow}(x,y)
+
h_{\rm local}(x,y).
\]

那么不同 \(x,y\) 位置上的：

- 高度；
- 局部斜率；

都不一样。

于是 WS 一边高速扫描，一边必须微调：

\[
z,\theta_x,\theta_y.
\]

这实际上是一个“coarse lateral scan + fine vertical following”的过程。

---

# 7. 那么我们怎么提前知道 wafer surface 长什么样？

对，你想到的正是 **wafer measurement / mapping**。

Song 在论文前面明确说，wafer measurement 阶段负责生成一个：

\[
\boxed{\text{3-D wafer map}}
\]

然后这个 map 用来确定 exposure 应该发生的位置。Motion_Control_of_Wafer_Scanner…

之后 Section III 又明确指出：

> horizontal setpoints 通常来自 polynomial motion trajectory，而 **vertical setpoints are derived from the 3-D map**。Motion_Control_of_Wafer_Scanner…

所以你的理解可以整理成：

### Measurement mode

先扫描 wafer：

\[
(x_i,y_i)
\rightarrow
h_i
\]

得到离散的 surface map：

\[
\boxed{
h(x,y)
}
\]

或者至少是一组 sampled height/topology data。

### Exposure mode

现在 lateral trajectory 已知：

\[
x_r[k],y_r[k].
\]

于是查这个 map，产生：

\[
z_r[k],\theta_{xr}[k],\theta_{yr}[k].
\]

最终：

\[
\mathbf r[k]
=
\begin{bmatrix}
x_r[k]\\
y_r[k]\\
z_r[k]\\
\theta_{xr}[k]\\
\theta_{yr}[k]\\
\theta_{zr}[k]
\end{bmatrix}.
\]

然后每周期 measurement：

\[
\mathbf y[k]
=
\begin{bmatrix}
x_l[k]\\
y_l[k]\\
z_l[k]\\
\theta_{xl}[k]\\
\theta_{yl}[k]\\
\theta_{zl}[k]
\end{bmatrix}
\]

与 setpoint 比较：

\[
\mathbf e[k]
=
\mathbf r[k]-\mathbf y[k].
\]

这就是完整的：

\[
\boxed{
\text{map}
\rightarrow
\text{setpoint}
\rightarrow
\text{measure}
\rightarrow
\text{control}
\rightarrow
\text{actuate}
}
\]

---

# 8. 一个小修正：3-D map 与 \(\theta_z\) 没有直接关系

你刚才把：

\[
\theta_z,\theta_x,\theta_y,z
\]

全放到了 wafer surface shape 这个原因下面，这里需要拆开。

3-D surface topology 主要决定：

\[
\boxed{
z,\theta_x,\theta_y
}
\]

因为这些是 out-of-plane pose。

但：

\[
\boxed{
\theta_z
}
\]

是 in-plane yaw。

wafer 表面的凹凸：

\[
h(x,y)
\]

不会直接告诉你 wafer grid 在 XY 平面里朝哪个方向。

因此：

- **3-D topology / leveling information** → \(z,\theta_x,\theta_y\)
- **alignment / wafer-grid orientation information** → \(x,y,\theta_z\)

更准确。

当然，一个完整的 wafer measurement/alignment system 可能同时建立多类 map，但 Song 这里明确提到的 “3-D map → vertical setpoints” 主要就是前一类。

---

# 9. 从 workload 角度，这里其实冒出了一个很有价值的新问题

你这次的问题反而引出了一个可能比普通 S-curve 更值得研究的 setpoint-generation workload：

\[
\boxed{
(x_r[k],y_r[k])+\text{3-D wafer map}
\rightarrow
z_r[k],\theta_{xr}[k],\theta_{yr}[k]
}
\]

它在线实现可能涉及：

- map lookup；
- interpolation；
- local plane fitting；
- gradient/slope estimation；
- coordinate transform。

例如从纯几何直觉上，如果有连续 surface：

\[
z=h(x,y),
\]

那么局部 slope：

\[
\frac{\partial h}{\partial x},
\qquad
\frac{\partial h}{\partial y}
\]

就和所需的 pitch/roll 有直接关系。

不过这里必须划清边界：

> **Song 只告诉我们 vertical setpoints 来源于 3-D map，并没有给出具体 map interpolation / leveling setpoint-generation 算法。**

所以这些 kernel 目前只能作为“值得进一步寻找位置/leveling算法论文”的候选，不能直接说 Song 已经给出了这些算法。
