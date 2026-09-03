// MCM/ICM (美赛) Typst Paper Template — English
//
// Note: The contest officially recommends LaTeX; this Typst template is an
// alternative for users who prefer fast compilation and concise syntax.
// Official LaTeX template: templates/en/mcm/
//
// Compile: typst compile mcm.typ mcm.pdf
// Requires: Typst 0.11+ (https://typst.app)

#let mcm-template = project => {
  // ===== Page setup =====
  set page(
    paper: "a4",
    margin: 2.5cm,
    header: align(right)[MCM/ICM $stack("— Page ", counter(page).display("1"), " —")$],
    numbering: "1",
  )

  // ===== Font: Times New Roman 12pt =====
  set text(
    font: "Times New Roman",
    size: 12pt,
    lang: "en",
  )

  // ===== Paragraph: double spacing (typst leading ~ 1.0em for 12pt double) =====
  // Double spacing in Typst: leading roughly equals one line height.
  set par(
    leading: 1.0em,
    spacing: 0pt,
    justify: true,
    first-line-indent: 0pt,
  )

  // ===== Headings =====
  set heading(numbering: "1.1.1")

  project
}

#show: mcm-template

// ==================== Summary Sheet (required, single page) ====================

#align(center)[
  #text(size: 18pt, weight: "bold")[Summary Sheet]
]

#v(0.5em)

*Problem:* #underline[Your problem title here]

*Team Control Number:* #underline[        ]

#v(0.5em)

#align(justify)[
  This paper addresses the problem of ... (one-sentence restatement). We develop a mathematical model based on ... and solve it using ... . The key results are: (1) ...; (2) ...; (3) ... . Sensitivity analysis shows that the model is robust within $plus.minus 20%$ parameter perturbation, with maximum deviation of $8.3%$.
]

#align(justify)[
  Our model provides a quantitative tool for ... and can be extended to ... . The main strengths are physical interpretability and computational efficiency; the main weakness is the assumption of linearity, which may not hold under extreme conditions.
]

*Keywords:* mathematical modeling; optimization; sensitivity analysis; numerical methods

#pagebreak()

// ==================== Table of Contents ====================

#heading(level: 1, numbering: none)[Table of Contents]
#outline(indent: auto, depth: 3)

#pagebreak()

// ==================== Problem Statement ====================

= Problem Statement

#align(justify)[
  We restate the problem in our own words. The contest asks us to ... . The key parameters and constraints are: ... . This paper is organized as follows: Section 2 analyzes the problem; Section 3 builds the model; Section 4 presents results; Section 5 discusses sensitivity.
]

= Problem Analysis

== Analysis of Sub-problem 1

#align(justify)[
  Sub-problem 1 asks us to determine how a physical quantity evolves over time. This is a mechanism modeling problem. The difficulty lies in the nonlinear nature of the system, which precludes a closed-form solution. Our approach: discretize the continuous equations and integrate numerically using a fourth-order Runge-Kutta scheme.
]

= Assumptions and Justifications

+ The system is isothermal during the study period; temperature effects on parameters are neglected. *Justification:* the time scale of heat dissipation is much longer than the simulation window.
+ Component interactions satisfy linear superposition. *Justification:* amplitudes remain in the linear regime.
+ External disturbances are modeled as Gaussian white noise. *Justification:* central limit theorem applies.

= Notation

#table(
  columns: (auto, auto),
  align: left + horizon,
  [*Symbol*], [*Meaning*],
  [$t$], [Time (s)],
  [$v$], [Velocity (m/s)],
  [$a$], [Acceleration (m/s^2)],
  [$theta$], [Angle (rad)],
)

= Model Building and Solution

== Model Formulation

#align(justify)[
  Based on the assumptions above, we construct the following kinematic model. The displacement $s$ and velocity $v$ satisfy:
]

$ "d"/"d"t s(t) = v(t), quad "d"/"d"t v(t) = a(t) $

#align(justify)[
  where $a(t)$ follows from Newton's second law:
]

$ m a(t) = F(t) - c v(t) - k s(t) $

== Solution and Results

The displacement curve is shown in @fig:disp.

#figure(
  // image("figures/q1_displacement.png", width: 80%),
  rect(width: 80%, height: 4cm, fill: gray.with-key(0.9), stroke: gray)[Placeholder: displacement-time curve],
  caption: [Displacement versus time],
) <fig:disp>

#align(justify)[
  As shown in @fig:disp, the displacement peaks at $12.35$ m at $t = 8.04$ s, then decays slowly — indicating a damped oscillation regime.
]

Key results are summarized in @tab:q1.

#table(
  columns: (auto, auto, auto),
  align: center + horizon,
  [*Parameter*], [*Value*], [*Unit*],
  [Peak displacement], [$12.35$], [m],
  [Peak time], [$8.04$], [s],
  [Steady-state displacement], [$10.00$], [m],
  caption: [Key results for sub-problem 1],
) <tab:q1>

= Sensitivity Analysis

#align(justify)[
  To assess robustness, we perturb key parameters $c$ and $k$ by $plus.minus 20%$. The peak displacement deviates by at most $8.3%$, indicating good robustness.
]

= Model Evaluation

#align(justify)[
  *Strengths:* clear physical interpretation; computationally efficient. *Weaknesses:* ignores nonlinear damping, which reduces accuracy under extreme loads. *Future work:* incorporate nonlinear damping terms and validate against experimental data.
]

= References

#bibliography("references.bib", title: [References], style: "ieee")

// ==================== Appendix ====================

#pagebreak()
#heading(level: 1, numbering: none)[Appendix]

== Appendix A: Core Code

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
