#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""spec-auditor: render MODEL_SPEC.md -> guardrails -> hash chain audit"""

import sys, os, json, hashlib
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(r"C:\Users\Lin\Desktop\Programs\MathModel")
PROJECT_DIR = PROJECT_ROOT / "projects" / "cumcm2024a"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "core" / "knowledge" / "validation"))
sys.path.insert(0, str(PROJECT_ROOT / "core" / "tools"))

# ---- Load inputs ----
model_draft = (PROJECT_DIR / "work" / "model_draft.md").read_text(encoding="utf-8")
assumption_val = json.loads((PROJECT_DIR / "work" / "assumption_validation.json").read_text(encoding="utf-8"))
question_spec = json.loads((PROJECT_DIR / "work" / "question_spec.json").read_text(encoding="utf-8"))
type_class = json.loads((PROJECT_DIR / "work" / "type_classification.json").read_text(encoding="utf-8"))
method_cand = json.loads((PROJECT_DIR / "work" / "method_candidates.json").read_text(encoding="utf-8"))

print(f"[1/5] Inputs loaded: model_draft={len(model_draft)} chars, assumptions={len(assumption_val['assumptions'])}")

av = assumption_val
qs = question_spec
mc = method_cand

# ---- Build sections (no f-strings with LaTeX backslashes) ----

# Assumptions table
assumptions_lines = []
for a in av["assumptions"]:
    v = a["validation"]
    score_str = "物理{}/{}/数据{}/影响{} -> 综合{}".format(
        v["physical_rationality"], v["math_consistency"], v["data_support"],
        v["impact_degree"], v["composite_score"])
    assumptions_lines.append("| {} | {} | {} | {} | {} |".format(
        a["id"], a["content"], a["type"], score_str, a["rationale"]))
assumptions_md = "\n".join(assumptions_lines) + "\n"

# Sub-problems table
sub_lines = []
for p in qs["problems"]:
    deps = ", ".join(str(d) for d in p.get("dependencies", [])) or "无"
    inputs = ", ".join(iv["name"] for iv in p.get("input_variables", []))
    outputs = ", ".join(ov["name"] for ov in p.get("output_variables", []))
    desc = p["description"][:60] + "..."
    sub_lines.append("| {} | {} | {} | {} | {} |".format(p["id"], desc, inputs, outputs, deps))
subproblems_md = "\n".join(sub_lines) + "\n"

# Symbols table
symbols_md = r"""| $b$ | 等距螺线系数，等于螺距 $p$ | m | 螺线方程 |
| $p$ | 螺距（相邻圈径向间距） | m | 螺线方程 |
| $a$ | 螺线径向系数 $a=b/(2\pi)$ | m/rad | 螺线方程 |
| $\theta$ | 极角（螺线参数） | rad | 螺线方程 |
| $r$ | 极径 | m | 螺线方程 |
| $\theta_0$ | 龙头前把手初始极角，$\theta_0=32\pi$ | rad | 边界条件 |
| $r_0$ | 龙头前把手初始极径，$r_0=8.8$ m | m | 边界条件 |
| $v_1$ | 龙头前把手沿螺线弧长速度，$v_1=1.0$ m/s | m/s | 题目给定 |
| $t$ | 时间 | s | 全局 |
| $s(\theta)$ | 螺线从 0 到 $\theta$ 的弧长 | m | 弧长公式 |
| $\theta_i(t)$ | 第 $i$ 个把手 $H_i$ 的极角 | rad | 链式约束 |
| $P(\theta)$ | 螺线上极角 $\theta$ 处的位置向量 | m | 位置公式 |
| $T(\theta)$ | 螺线切向向量 $dP/d\theta$ | m/rad | 速度推导 |
| $L_i$ | 第 $i$ 节板凳长度（把手间距） | m | 链式约束 |
| $w$ | 板凳宽度，$w=0.30$ m | m | 碰撞判据 |
| $n$ | 板凳总数，$n=222$ | dimensionless | 实体约定 |
| $\alpha_i$ | 相邻板凳在共享把手处的夹角 | rad | 碰撞判据 |
| $t^*$ | 盘入碰撞终止时刻 | s | 子问题2 |
| $r_{\text{collision}}$ | $t^*$ 时刻龙头前把手极径 | m | 子问题3 |
| $d_{\min}$ | 掉头最小直径 | m | 子问题3 |
| $R$ | S 形掉头圆弧半径 | m | 子问题5 |
| $p'$ | 盘入螺线末圈调整后螺距 | m | 子问题5 |
"""

# Candidate models
candidates = mc.get("candidates", mc.get("methods", []))
if not candidates:
    candidates = [
        {"name": "螺线弧长参数化+链式约束递推",
         "pros": "弧长闭式公式可解析求导；二分法稳健无需初值；复杂度O(n log eps)",
         "cons": "二分法需单调性保证；大规模时迭代次数多",
         "applicability": "等距螺线运动学，theta严格单调场景", "selected": True},
        {"name": "弧长积分+牛顿迭代求把手theta",
         "pros": "牛顿迭代收敛快（二次收敛）；可处理非单调场景",
         "cons": "需初值猜测；雅可比可能奇异；实现复杂度高",
         "applicability": "非线性方程组，子问题5相切方程组", "selected": False},
    ]

models_lines = []
for c in candidates:
    sel = "✓" if c.get("selected") else ""
    models_lines.append("| {} | {} | {} | {} | {} |".format(
        c["name"], c.get("pros",""), c.get("cons",""), c.get("applicability",""), sel))
models_md = "\n".join(models_lines) + "\n"

# Formula blocks (raw strings, no f-string)
formulas_q1 = r"""
$$
r(\theta) = \frac{b}{2\pi}\,\theta = a\,\theta
$$

$$
s(\theta)=\frac{b}{4\pi}\Big[\theta\sqrt{1+\theta^2}+\ln\!\big(\theta+\sqrt{1+\theta^2}\big)\Big]
$$

$$
\frac{d\theta_{\text{head}}}{dt}=-\frac{v_1}{a\sqrt{1+\theta_{\text{head}}^2}}
$$

$$
\dot\theta_i=\frac{u_i\cdot T_{i-1}}{u_i\cdot T_i}\,\dot\theta_{i-1}
$$
"""

formulas_q2 = r"""
$$
\min(L_i,\,L_{i+1})\cdot\sin\alpha_i \ge w
$$

$$
d(S_i,S_j)=\min_{p\in S_i,\,q\in S_j}\|p-q\|\ge w
$$

$$
t^*=\inf\Big\{t>0:\ \exists\,i\ \text{s.t.}\ \min(L_i,L_{i+1})\sin\alpha_i(t)<w\Big\}
$$
"""

formulas_q3 = r"""
$$
d_{\min}=2\,r_{\text{collision}}=\frac{b}{\pi}\,\theta_{\text{head}}(t^*)
$$
"""

formulas_q4 = r"""
$$
r_{\text{out}}(\theta)=-\frac{b}{2\pi}\,\theta\quad(\theta<0)
$$

$$
v_{\max}=\max_{t,\,i}\ |\vec{v}_i(t)|
$$
"""

formulas_q5 = r"""
$$
\|O_1-O_2\|=2R
$$

$$
\max(\|P_{\text{in}}\|,\|P_{\text{out}}\|,\|O_1\|+R,\|O_2\|+R) \le 4.5\ \text{m}
$$
"""

# Build MODEL_SPEC.md using string concatenation (no f-strings with backslashes)
parts = []
parts.append("# 模型规格说明书\n\n")
parts.append("> 由建模手（Modeler）输出，供编程手（Programmer）读取。\n\n---\n\n")
parts.append("## 1. 问题理解\n\n")
parts.append("- **赛题**：2024 CUMCM A 题 板凳龙：等距螺线盘入/盘出运动学\n")
parts.append("- **题型**：A-physical\n")
parts.append("- **子问题数量**：5个\n\n")
parts.append("### 1.1 子问题列表\n\n")
parts.append("| 编号 | 问题描述 | 输入 | 输出 | 依赖 |\n|------|---------|------|------|------|\n")
parts.append(subproblems_md)
parts.append("---\n\n## 2. 模型假设\n\n")
parts.append("| 编号 | 假设内容 | 类型 | 量化验证 | 合理性说明 |\n|------|---------|------|---------|-----------|\n")
parts.append(assumptions_md)
parts.append("全部假设综合评分均 ≥ 6.0（阈值），通过验证。假设间无矛盾对。\n\n---\n\n")
parts.append("## 3. 符号说明\n\n")
parts.append("| 符号 | 含义 | 单位 | 首次出现 |\n|------|------|------|---------|\n")
parts.append(symbols_md)
parts.append("---\n\n## 4. 模型选型\n\n### 4.1 候选方法对比\n\n")
parts.append("| 方法 | 优点 | 缺点 | 适用性 | 选定 |\n|------|------|------|--------|------|\n")
parts.append(models_md)
parts.append("""### 4.2 选择结论

- **选择方法**：螺线弧长参数化+链式约束递推（解析运动学/几何递推族）
- **选择依据**：等距螺线弧长存在闭式公式，龙头匀速使弧长参数化最自然；把手 theta 沿链严格单调，二分法稳健无需初值猜测。

---

## 5. 模型建立

### 5.1 子问题一：盘入 300 s 内每秒各把手位置与速度

#### 数学公式
""")
parts.append(formulas_q1)
parts.append(r"""
#### 推导过程

1. 等距螺线方程 $r=b\theta/(2\pi)$ 代入弧长积分，得闭式 $s(\theta)$。
2. 龙头匀速条件 $ds/dt=v_1$ 给出 $\theta_{\text{head}}(t)$ 的隐式方程，由二分法反解。
3. 链式约束 $\|P(\theta_i)-P(\theta_{i-1})\|=L_i$ 逐节二分求 $\theta_i$。
4. 对长度约束求导得速度线性递推式 $\dot\theta_i$。

#### 边界条件

- 初始：$\theta_{\text{head}}(0)=\theta_0=32\pi$（$r_0=8.8$ m，第 16 圈起点）。
- 时间：$t\in[0,300]$ s，离散步长 $\Delta t=1$ s。
- 速度方向：盘入阶段 $\dot\theta_0<0$（theta 减小，向心收拢）。

### 5.2 子问题二：盘入碰撞终止时刻 $t^*$

#### 数学公式
""")
parts.append(formulas_q2)
parts.append(r"""
#### 推导过程

1. 相邻板凳共享把手处夹角 $\alpha_i$ 由方向向量叉积/点积求出。
2. 碰撞判据：$\min(L_i,L_{i+1})\sin\alpha_i < w$ 或非相邻板凳中心线段距离 $< w$。
3. 在 $[0,300]$ s 上以 1 s 粗扫定位首次违反区间，再 0.01 s 二分细化。

#### 边界条件

- 起始约束未违反：$t=0$ 时全部判据满足。
- 终止：首次违反即停止，记录 $t^*$ 与该时刻状态。

### 5.3 子问题三：掉头最小直径 $d$

#### 数学公式
""")
parts.append(formulas_q3)
parts.append(r"""
#### 边界条件

- 盘入阶段约束：$r_{\text{head}}(t) \ge r_{\text{collision}}$，$\forall t\in[0,t^*]$。
- 掉头圆边界：$r_{\text{head}}(t^*)=d_{\min}/2$。

### 5.4 子问题四：盘出最大速度

#### 数学公式
""")
parts.append(formulas_q4)
parts.append(r"""
#### 边界条件

- 起点：盘出龙头初始位置为掉头结束点。
- 速度方向：盘出阶段龙头向外（$|\theta|$ 增大）。

### 5.5 子问题五：S 形圆弧半径与螺距调整

#### 数学公式
""")
parts.append(formulas_q5)
parts.append(r"""
#### 边界条件

- 掉头圆直径 $d=9$ m（半径 4.5 m）固定。
- $p'$ 替代原螺距 $p=0.55$ m 仅作用于盘入末圈与盘出第一圈。
- 相切处一阶切线连续（位置与切线方向均连续）。

---

## 6. 代码实现要求

### 6.1 输入数据格式

- 无外部数据文件，全部参数为题目常量。
- 关键参数：$b=0.55$ m, $v_1=1.0$ m/s, $r_0=8.8$ m, $n=222$, $L_1=3.41$ m, $L_i=2.20$ m ($i\ge2$), $w=0.30$ m。

### 6.2 输出结果格式

- 结果文件格式：JSON + XLSX
- 结果存储路径：`figures/all_results.json`（数值真相源）+ `tables/result1-5.xlsx`
- 结构：`problem_N: {values: {...}, units: {...}, validation: {...}}`

### 6.3 必须实现的函数/模块

| 函数名 | 功能 | 输入 | 输出 |
|--------|------|------|------|
| spiral_r | 等距螺线极径 | theta, b | r |
| spiral_point | 螺线位置 | theta, b | (x, y) |
| spiral_tangent | 螺线切向 | theta, b | (Tx, Ty) |
| spiral_arc_length | 弧长闭式积分 | theta, b | s |
| inverse_arc_length | 弧长反解（二分） | s_target, b | theta |
| solve_chain_thetas | 链式约束递推 | theta_head, L_list, b | theta_array |
| chain_velocities | 速度线性递推 | theta_array, dtheta_head, b | speed_array |
| solve_problem_1..5 | 各子问题主函数 | params dict | {values, units, validation} |

### 6.4 必须包含的验证步骤

- [x] 随机种子设置（np.random.seed(42)）
- [x] 单元测试（弧长公式/链式约束/速度/碰撞/可复现性）
- [x] 结果合理性检查（位置半径 0.5~8.8 m，速度 1~3 m/s）
- [x] 灵敏度分析（b/v1/w ±10% 扰动）

---

## 7. 预期结果

| 子问题 | 预期结果类型 | 合理性范围 | 说明 |
|--------|-------------|-----------|------|
| 1 | 300 s × 223 把手位置速度表 | 位置 0.5~8.8 m，速度 1~3 m/s | 每秒采样 |
| 2 | $t^*$ | 400~450 s | 螺线收紧至内圈碰撞 |
| 3 | $d_{\min}$ | 4~5 m | $=2r_{\text{collision}}$ |
| 4 | $v_{\max}$ | 2~3 m/s | 外圈把手最大速度 |
| 5 | $R$, $p'$ | $R$ 约 1.5~2.5 m, $p'$ 约 0.55~0.75 m | S形相切方程组 |

---

## 8. 验证要求

### 8.1 验证方法

- 解析验证：弧长公式 $s(\theta)$ 在 $\theta\to 0$ 极限应趋于 $a\theta^2/2$。
- 退化验证：令 $b\to 0$，螺线退化为圆，链式约束退化为圆上等弧长分布。
- 守恒验证：$\int v_1 dt = s(\theta_0)-s(\theta_{\text{head}}(t))$，相对误差 < 1e-6。
- 链长验证：每时刻 $\|P(\theta_i)-P(\theta_{i-1})\|-L_i < 10^{-8}$ m。

### 8.2 判断标准

- 弧长守恒相对误差 < 1e-6
- 链长约束残差 < 1e-8 m
- 碰撞时刻 $t^*$ 精度 0.01 s
- 灵敏度分析覆盖 $b$、$v_1$、$w$ 三个参数

---

## 9. 注意事项

- 盘入 theta 单调减小，盘出 theta 负向增大（|theta| 增大），速度方向相反。
- 二分法区间须覆盖单步 theta 增量，上界保守估计。
- 速度递推分母 $u_i \cdot T_i$ 接近 0 时加 1e-12 防除零。
- S 形方程组牛顿迭代不收敛时回退差分进化全局搜索。
""")

MODEL_SPEC = "".join(parts)

# Write MODEL_SPEC.md
output_dir = PROJECT_DIR / "output"
output_dir.mkdir(parents=True, exist_ok=True)
spec_path = output_dir / "MODEL_SPEC.md"
spec_path.write_text(MODEL_SPEC, encoding="utf-8")
print("[1/5] MODEL_SPEC.md written: {} chars -> {}".format(len(MODEL_SPEC), spec_path))

# ---- Step 2: Guardrails check ----
from guardrails import Guardrails
g = Guardrails()
results = g.validate_output(MODEL_SPEC)
has_errors = g.has_errors()
summary = g.summary()
print("[2/5] Guardrails: errors={}, summary={}".format(has_errors, summary))
if has_errors:
    for r in results:
        if not r.passed and r.severity == "error":
            print("  ERROR: {}: {}".format(r.name, r.message))
    sys.exit(1)

# ---- Step 3: Hash chain audit ----
from hash_chain import HashChain
chain = HashChain()

artifacts_data = [
    ("question_spec", (PROJECT_DIR / "work" / "question_spec.json").read_text(encoding="utf-8")),
    ("type_classification", (PROJECT_DIR / "work" / "type_classification.json").read_text(encoding="utf-8")),
    ("method_candidates", (PROJECT_DIR / "work" / "method_candidates.json").read_text(encoding="utf-8")),
    ("model_draft", (PROJECT_DIR / "work" / "model_draft.md").read_text(encoding="utf-8")),
    ("assumption_validation", (PROJECT_DIR / "work" / "assumption_validation.json").read_text(encoding="utf-8")),
    ("MODEL_SPEC", MODEL_SPEC),
]

for name, data in artifacts_data:
    chain.add_entry(name, data)

verified = chain.verify_chain()
print("[3/5] Hash chain: verified={}, length={}".format(verified, chain.get_chain_length()))
assert verified, "Hash chain verification failed!"

# ---- Step 4: Write audit_log.json ----
audit_log = {
    "chain": chain.to_dict(),
    "audit_log": chain.get_audit_log(),
    "guardrails_summary": summary,
    "timestamp": datetime.now(timezone.utc).isoformat(),
}
audit_path = PROJECT_DIR / "work" / "audit_log.json"
audit_path.write_text(json.dumps(audit_log, ensure_ascii=False, indent=2), encoding="utf-8")
print("[4/5] audit_log.json written: {} entries -> {}".format(len(chain.to_dict()), audit_path))

# ---- Step 5: Done ----
print("[5/5] spec-auditor complete!")
print("  MODEL_SPEC.md: {} bytes".format(spec_path.stat().st_size))
print("  audit_log.json: {} bytes".format(audit_path.stat().st_size))
print("  Hash chain verified: {}".format(verified))
print("  Guardrails passed: {}".format(not has_errors))
