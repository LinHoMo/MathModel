// 国赛(CUMCM)Typst 论文模板
//
// 注意:竞赛官方仍推荐 LaTeX,本 Typst 模板作为备选,适合追求快速编译的场景。
// 官方 LaTeX 模板见 templates/zh/cumcm/ 目录。
//
// 编译:typst compile cumcm.typ cumcm.pdf
// 依赖:Typst 0.11+ (https://typst.app)

#let cumcm-template = project => {
  // ===== 页面设置 =====
  set page(
    paper: "a4",
    margin: 2.5cm,
    header: align(right)[CUMCM $stack("第"， counter(page).display("I"), "页")$],
    numbering: "1",
  )

  // ===== 字体设置 =====
  // 中文用 SimSun(宋体),英文用 Times New Roman,字号 12pt
  set text(
    font: ("Times New Roman", "SimSun"),
    size: 12pt,
    lang: "zh",
    region: "cn",
  )

  // ===== 段落设置 =====
  // 行距 1.5,段前段后 6pt
  set par(
    leading: 1.5em,
    spacing: 6pt,
    justify: true,
    first-line-indent: 2em,
  )

  // ===== 标题设置 =====
  set heading(numbering: "1.1.1")
  show heading: it => {
    set par(first-line-indent: 0em)
    block(it)
  }

  project
}

#show: cumcm-template

// ==================== 标题页 ====================

#align(center)[
  #text(size: 24pt, weight: "bold")[全国大学生数学建模竞赛论文]
  #v(1em)
  #text(size: 16pt)[题目: #underline[你的题目在此]]
  #v(2em)

  #table(
    columns: (auto, auto),
    align: left + horizon,
    stroke: none,
    [*参赛队号:*], [#underline[        ]],
    [*参赛学校:*], [#underline[        ]],
    [*队员姓名:*], [#underline[        ]],
    [*指导教师:*], [#underline[        ]],
  )
]

#pagebreak()

// ==================== 摘要页 ====================

#heading(level: 1, numbering: none)[摘要]

#align(justify)[
  针对本文研究的数学建模问题,我们建立了相应的数学模型并进行了求解。本文的核心思路是:首先对问题进行深入分析,识别关键变量与约束条件;其次基于物理/统计/优化原理构建数学模型;最后采用数值方法求解并对结果进行灵敏度分析。
]

#align(justify)[
  针对问题一,我们建立了基于 $ODE$ 的机理模型,求解得到关键参数 $t = 1.423$ s。针对问题二,我们采用遗传算法进行优化,目标函数值较基线方法下降 $12.35$%。灵敏度分析表明模型在参数 $±20%$ 扰动范围内保持稳健。
]

#v(1em)
*关键词:* 数学建模;机理模型;优化;灵敏度分析

#pagebreak()

// ==================== 目录 ====================

#heading(level: 1, numbering: none)[目录]
#outline(indent: auto, depth: 3)

#pagebreak()

// ==================== 正文 ====================

= 问题重述

#align(justify)[
  本文用自己的话简述问题背景。注意不能照抄题目原文,而是用自己的语言概括问题的核心要求与约束条件。
]

= 问题分析

== 问题一的分析

#align(justify)[
  问题一要求求解某物理量随时间的变化。这是一个机理建模问题。难点在于系统具有非线性特性,无法直接求得解析解。本文的解决思路是:将连续方程离散化,采用数值积分方法逐步求解。
]

= 模型假设

#align(justify)[
  + 假设系统在研究时段内处于恒温状态,忽略温度对参数的影响。
  + 假设各组件之间的相互作用满足线性叠加原理。
  + 假设外部扰动可视为高斯白噪声。
]

= 符号说明

#table(
  columns: (auto, auto),
  align: left + horizon,
  [*符号*], [*含义*],
  [$t$], [时间 (s)],
  [$v$], [速度 (m/s)],
  [$a$], [加速度 (m/s^2)],
  [$theta$], [角度 (rad)],
)

= 模型建立与求解

== 模型建立

#align(justify)[
  基于上述假设,本文构建如下运动学模型。物体的位移 $s$ 与速度 $v$ 满足:
]

$ "d"/"d"t s(t) = v(t), quad "d"/"d"t v(t) = a(t) $

#align(justify)[
  其中 $a(t)$ 由牛顿第二定律给出:
]

$ m a(t) = F(t) - c v(t) - k s(t) $

#align(justify)[
  将其离散化得到差分方程,采用四阶 Runge-Kutta 方法求解。
]

== 模型求解结果

求解得到位移随时间变化曲线如图 1 所示。

#figure(
  // image("figures/q1_displacement.png", width: 80%),
  rect(width: 80%, height: 4cm, fill: luma(230), stroke: luma(128))[占位:位移-时间曲线],
  caption: [图 1 不同时刻下位移变化曲线],
) <fig:disp>

#align(justify)[
  从 @fig:disp 可以看出,位移在 $t = 8.04$ s 处达到峰值 $12.35$ m,随后缓慢回落。这表明系统存在阻尼振荡特性。
]

关键结果汇总见表 1。

#table(
  columns: (auto, auto, auto),
  align: center + horizon,
  [*参数*], [*数值*], [*单位*],
  [峰值位移], [$12.35$], [m],
  [峰值时刻], [$8.04$], [s],
  [稳态位移], [$10.00$], [m],
  caption: [问题一关键结果汇总],
) <tab:q1>

= 灵敏度分析

#align(justify)[
  为检验模型鲁棒性,本文对关键参数 $c$ 和 $k$ 做 $±20%$ 扰动分析。结果显示,在扰动范围内,峰值位移最大偏差 $8.3$%,模型稳健性良好。
]

= 模型评价

#align(justify)[
  本文模型优点在于物理意义明确、参数可解释;不足之处在于未考虑非线性效应,在极端工况下精度下降。改进方向是引入非线性阻尼项。
]

= 参考文献

#bibliography("references.bib", title: [参考文献], style: "gb-7714-2015-numeric")

// ==================== 附录 ====================

#pagebreak()
#heading(level: 1, numbering: none)[附录]

== 附录 A:核心代码

```python
import numpy as np
from scipy.integrate import solve_ivp

def equations(t, y, m, c, k, F):
    s, v = y
    a = (F(t) - c * v - k * s) / m
    return [v, a]

sol = solve_ivp(equations, [0, 25], [0, 0],
                args=(1.0, 0.5, 0.1, lambda t: 10),
                method="RK45", dense_output=True)
```
