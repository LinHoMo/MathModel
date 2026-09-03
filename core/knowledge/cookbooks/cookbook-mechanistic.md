# Cookbook: 机理/物理模型类

> 适用场景：基于物理定律/化学原理/生物机制建立微分方程/代数方程。CUMCM A/B 题、MCM A 题高频。

---

## 1. 常微分方程组 (ODE)

| 类型 | 典型应用 | 求解方法 | 代码模板 |
|------|----------|----------|----------|
| **显式/隐式 RK** | 非刚性/弱刚性、精度要求高 | `scipy.integrate.solve_ivp` (RK45/DOP853/Radau/BDF) | `ode_rk_template.py` |
| **多步法/预测-修正** | 长时积分、能量守恒 | `solve_ivp` (Adams/BDF) | `ode_multistep.py` |
| **共轭梯度/谱方法** | 高精度、周期边界 | `dedalus` / `shenfun` / 自实现 | `ode_spectral.py` |
| **事件检测/终止** | 碰撞/阈值触发/周期 | `events` 参数 | `ode_events.py` |

**常见坑**：
1. 刚性问题用显式法 → 步长极小/发散 → 必用 BDF/Radau
2. 守恒量漂移 → 共轭格式/辛积分/投影修正
3. 事件检测漏触发 → 精细化 `max_step`/`rtol`/`atol`

**验证清单**：✅ 守恒量相对误差<1e-6 ✅ 反演已知解/解析解 ✅ 步长收敛性(阶数验证) ✅ 事件准确触发

---

## 2. 偏微分方程 (PDE)

| 方程类型 | 典型应用 | 离散方法 | 代码模板 |
|----------|----------|----------|----------|
| **抛物型 (热/扩散)** | 热传导、扩散、布莱克-斯科尔斯 | 有限差分(FTCS/CN/DuFort-Frankel)、有限元(FEniCS/dolfinx)、谱方法 | `pde_heat_fd.py`, `pde_heat_fe.py` |
| **双曲型 (波/输运)** | 声波、水波、交通流 | 有限体积(Godunov/Lax-Friedrichs/Roe)、DG、特征线法 | `pde_wave_fv.py`, `pde_transport.py` |
| **椭圆型 (稳态/势流)** | 稳态热传导、静电场、地下水 | 有限差分(五点/九点)、有限元、多重网格 | `pde_poisson_fd.py`, `pde_poisson_fe.py` |
| **纳维-斯托克斯** | 不可压/可压流体、湍流 | SIMPLE/PISO/分数步、LES/DNS、有限体积(OpenFOAM) | `pde_ns_fv.py` |

**边界条件处理**：Dirichlet(本质/自然)、Neumann(自然/本质)、Robin、周期、对称/反对称

**代码模板目录**：
```
core/Programmer/knowledge/code-templates/mechanistic/
├── ode_rk_template.py
├── ode_multistep.py
├── ode_spectral.py
├── ode_events.py
├── pde_heat_fd.py
├── pde_heat_fe.py
├── pde_wave_fv.py
├── pde_transport.py
├── pde_poisson_fd.py
├── pde_poisson_fe.py
├── pde_ns_fv.py
├── fem_elasticity.py          # 固体力学 FEM
├── fem_heat.py                # 热传导 FEM
├── inverse_problem.py         # 参数反演 (伴随法/梯度下降)
└── sensitivity_adjoint.py     # 伴随灵敏度
```

---

## 3. 固体力学 / 结构分析 (FEM)

| 模型 | 适用场景 | 本构关系 | 代码模板 |
|------|----------|----------|----------|
| **线性弹性** | 小变形、各向同性/各向异性 | 胡克定律、各向同性(λ,μ/E,ν) | `fem_elasticity.py` |
| **几何非线性** | 大位移/大转动、小应变 | 格林-拉格朗日应变、第二皮奥拉-基尔霍夫应力 | `fem_geometric_nl.py` |
| **材料非线性** | 塑性/蠕变/超弹性/损伤 | J2 塑性、奥登模型、莫尼-里夫林、相场损伤 | `fem_plasticity.py`, `fem_hyperelastic.py` |
| **接触/破坏** | 碰撞/摩擦/裂纹扩展 | 惩罚法/拉格朗日乘子/Nitsche、相场/相干区 | `fem_contact.py`, `fem_phase_field.py` |

**求解器**：直接法(稀疏 LU/Cholesky)、迭代法(CG/GMRES+预条件)、多重网格

---

## 4. 流体力学 / CFD

| 模型 | 适用场景 | 湍流模型 | 代码模板 |
|------|----------|----------|----------|
| **势流/欧拉** | 不粘/高雷诺、外部流场 | 无/代数模型 | `cfd_potential.py` |
| **RANS** | 工程湍流、稳态/非稳态 | k-ε/k-ω/SST/RSM | `cfd_rans.py` (OpenFOAM/pyFOAM) |
| **LES/DES** | 大涡/分离流、瞬态细节 | Smagorinsky/动力学/WALE | `cfd_les.py` |
| **多相流** | 气液/固液/相变 | VOF/Level Set/相场/Euler-Euler | `cfd_multiphase.py` |

---

## 5. 参数反演 / 逆问题

| 方法 | 适用场景 | 核心思想 | 代码模板 |
|------|----------|----------|----------|
| **最小二乘/正则化** | 参数少、前向模型可微 | `min ||y - f(θ)||² + λ||Lθ||²` | `inverse_lsq.py` |
| **伴随法梯度** | 参数多(>100)、PDE 约束 | 伴随方程求梯度 O(1) 前向求解 | `inverse_adjoint.py` |
| **贝叶斯反演/MCMC** | 不确定性量化、后验分布 | MCMC/HMC/NUTS 采样后验 | `inverse_bayesian.py` (PyMC/NumPyro) |
| **集合卡尔曼/粒子滤波** | 实时/序列同化 | EnKF/EnKS/粒子滤波 | `inverse_enkf.py` |

**正则化参数选择**：L曲线/广义交叉验证(GCV)/交叉验证/贝叶斯证据

---

## 6. 灵敏度分析 / 不确定性量化 (UQ)

| 方法 | 适用场景 | 计算成本 | 代码模板 |
|------|----------|----------|----------|
| **局部/一次阶** | 筛选关键参数、梯度可得 | 低 (n+1 次前向) | `sa_local.py` |
| **全局/方差基础 (Sobol/FAST)** | 非线性/非单调/交互作用 | 中高 (N×(2d+2)) | `sa_sobol.py` (SALib) |
| **Morris 初筛** | 参数多、先筛选再精分析 | 低 (r×(d+1)) | `sa_morris.py` |
| **多项式混沌展开 (PCE)** | 代理模型、快速 UQ | 中 (训练后极快) | `sa_pce.py` (Chaospy/UQpy) |
| **蒙特卡洛/拟蒙特卡洛** | 基准、任意分布 | 高 (10^4-10^6) | `sa_mc.py` |

---

## 7. 选型决策树 (机理类)

```
物理过程？
├─ 热/扩散/抛物型 → 有限差分(CN)/有限元(FEniCS) → 首选
├─ 波/输运/双曲型 → 有限体积(Godunov/Roe)/DG → 首选
├─ 稳态/椭圆型 → 有限差分/有限元/多重网格 → 首选
├─ 流体/NS → RANS(k-ω SST)/LES → 按精度/资源选
├─ 固体/结构 → 线性弹性/非线性 FEM → 按变形量选
├─ 参数未知/反演 → 参数少→最小二乘/伴随法；参数多/不确定性→贝叶斯/EnKF
└─ 灵敏度/UQ → 筛选→Morris；精分析→Sobol/PCE；基准→MC
```

**铁律**：
- 机理模型 **必须推导从基本定律出发**，每步有依据 (M3)
- 符号定义 **必须完整含量纲**，全文一致 (M4)
- 边界/初始条件 **必须显式列出**，物理意义明确 (M5)
- 数值格式 **必须验证阶数/守恒/稳定性** (CFL条件/能量估计)
- 参数反演 **必须给出不确定性量化** (后验协方差/置信区间/可信区间)

---

## 8. 竞赛实战提示

| 竞赛 | 题型 | 推荐首选 | 避坑指南 |
|------|------|----------|----------|
| CUMCM A | 优化+机理 | ODE/PDE + 参数反演 + 优化耦合 | 机理参数实测/文献支撑、灵敏度分析 |
| CUMCM B | 实验/机理 | PDE/FEM + 参数辨识 | 实验数据驱动参数、交叉验证 |
| MCM A | 连续/机理 | PDE/ODE + 无量纲化 + 尺度分析 | Memo 清楚陈述模型假设、边界条件 |
| 电工杯 | 工程物理 | FEM/CFD + 实测校核 | 工程规范边界、安全系数、工况包络 |

---

*版本：1.0 | 更新：2026-09-01 | 维护：Modeler 手*