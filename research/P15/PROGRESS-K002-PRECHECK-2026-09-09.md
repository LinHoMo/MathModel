# P15-K002 冻结前置进度 — 2026-09-09（白天续）

> 本文件承接 `PROGRESS-NIGHT-2026-09-09.md`，记录治理 v1.2 + K002 冻结前置（预检/G2/rubric v1.1）的推进。

---

## 1. 状态快照（2026-09-09 上午）

| 项 | 状态 |
|---|---|
| 治理 v1.2（统一标准，真迁移非注释兼容） | ✅ 完成并 push（8b23608 + 05c0ac1） |
| K001 状态机 | ✅ CLOSED（含三仓库审计 + K002 v0.2 回填 + negative 记录） |
| K002 预检 12 runs + 主盲评 | ✅ 完成（Organizer `o_0001iAuITsS`） |
| 区分度预检 | ✅ 6/6 题有区分度（STOP 未触发），L2 天花板暴露 |
| G2 Instrument validity | ✅ PASS（维度级 Cohen κ=0.879，分歧可归因） |
| **rubric v1.1 测量校准** | ✅ 已落地（commit 713b5b2）+ 工具链同步（133bc9c） |
| **v1.1 重评验证（L2 天花板修复验证）** | 🔄 Organizer 执行中（评估者 s_0001i8OXRa2） |
| K002 PREREGISTERED / FROZEN | ⏳ 待重评结论回填 |

## 2. 治理 v1.2（8b23608）要点

- **真正迁移字段**：5 题 `gt.json` allowed_model_families → allowed_modeling_structures（旧键删除）；e2e_metrics 输出键统一 structure_alignment（删 _method_hit 兜底）；catalog_check 删除 `# legacy compat` 行内豁免
- **测试可信度**：修复 test_e2e_metrics.py sys.path 指向已删目录的隐藏缺陷（进程级副作用掩盖）
- **校验范围统一**：validate.py RESEARCH_PROJECT_PREFIXES + _is_research_scan_path → 57/0 全绿
- **统一契约**：`protocol/P15-EXPERIMENT-CONTRACT-v2.md`（八层节点标准 + 通信协议 + 扩展指引）
- 验证：pytest 855/4、catalog_check OK、terminology OK

## 3. K002 预检结论（Organizer 交付）

- **区分度**：6 题全部有区分度（F MCQ 96.8–100 vs S 90.3–96.8，Δ 均负），0/6 零区分度 → 全保留
- **天花板问题（关键发现）**：L1/L2/L4 三层 12/12 全部满分，**L2 composite 差值全部为 0**——L2（K001 可比主终点）零区分度，分化 100% 来自 L3 叙述完备性
- **G2**：维度级 Cohen κ=0.879（18/22 维 κ=1.0），4 个低 κ 维全部可归因（天花板/二元维度伪影）；评估者 B 系统性尺度偏移 +3（A-C MAD=0.2）——分歧可归因，PASS
- **方向信号**：S<F 一致（6/6 题，n=1 下 p≈1.6%）——候选解释：格式不对称 / 生成侧差异 / 真实负效应，正式实验必须区分

## 4. rubric v1.1 测量校准（713b5b2）

动因：L2 天花板 → 主终点无法区分"结构化表示是否提升模型构建质量"。

校准点（总分结构/PASS 阈值不变，只改判据粒度）：
1. **§0.4 格式中立规则**：结构化 MODEL_IR 与叙述式 model_doc 评分等价（字段齐全=满分，叙述不额外加分）
2. **L2.6 四要素**：E1 机理-题面 / E2 机理-方程 / E3 机理-目标约束 / E4 候选对比（3 分锚点显式化；E4 由 model_family.secondary + modeling_trace 机械支撑）
3. **L2.4** 目标-机制-约束三角一致性；**L2.7** 方程符号集 ⊆ 变量/参数声明集
4. **L3.3/L3.4** 格式中立细化；**L4.3** ≥2 类极限检验 + 结果-主张关联

版本策略：K001 评分文件冻结引用 v1.0（历史不变）；K002 全程 v1.1；G1 映射表升级 v1.1。

## 5. 待办

- [ ] v1.1 重评结论回填（L2 区分度是否恢复）→ DRAFT v0.7（rubric v1.1 + 盲评呈现层统一声明）→ PREREGISTERED → FROZEN
- [ ] 正式实验盲评呈现层：S 臂 JSON 渲染叙述式模型卡 or 统一呈现（预检已暴露格式可辨）
- [ ] 108 runs 正式实验委派（FROZEN 后）
