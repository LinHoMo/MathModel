# 项目治理报告 — 2026-09-09（v1.2 统一标准治理）

> 触发：用户指令「完全完成后要进行项目的治理（历史债务/测试不可信赖/历史兼容性/历史命名/引用路径/旧文档记录），深入思考检查并按最新最优方案优化」+「不要注释兼容，要真正意义上改造到最新的状态；统一系统每一个节点的标准和节点之间的通信」。
> 范围：MathModel 仓库（LLM-free Harness）。全部改动已验证：pytest 855 passed / 4 skipped、catalog_check --check OK、--check-terminology OK、validate.py 57/0 全绿。

---

## 1. 治理框架（六类问题 × 处置原则）

| 类 | 处置原则 |
|---|---|
| 历史债务 | 可机械修复的立即修（迁移类路径）；历史快照只读加 ARCHIVAL-NOTE，不删不改 |
| 测试不可信赖 | 全部测试有真实断言（1624 个 assert）；3 个「无断言」为 unittest 风格误报；4 个 skip 归因清晰 |
| 历史兼容性 | 生产输出统一新键；历史数据按历史格式只读（读取 ≠ 写入兼容） |
| 历史命名 | 旧术语生产区零残留（术语门禁移除行内豁免）；字符串 ≠ 本体（词表 canonical） |
| 引用路径 | 活跃文档立即修复；历史文档标注 archival；迁移类路径全库批量替换 |
| 旧文档记录 | 23 份历史规划/报告加 ARCHIVAL-NOTE 横幅（正文不动，保持快照诚实性） |

## 2. 引用路径修复（治理⑤+⑥）

### 2.1 活跃文档（立即修复）
- `AGENTS.md`：五层目录 benchmark 层 `core/tools/evaluation/` → `core/tools/`（benchmark.py / e2e_metrics.py / bench_mmbench.py）
- `README.md`：能力层路径同步更新
- `CHANGELOG.md`：`core/AGENTS.md`→`AGENTS.md`、`core/tools/runtime/replay.py`→`core/tools/replay.py`、evaluation 路径迁移
- `docs/ARCHITECTURE.md`：`core/tools/validation/citation_check.py`→`core/tools/citation_check.py`
- `core/tools/benchmark.py` docstring：evaluation 子路径迁移（批量替换覆盖）
- 批量迁移替换（仅目标存在时）：8 个文件 × 22 处 `core/tools/evaluation/xxx.py`→`core/tools/xxx.py`

### 2.2 测试代码残留（真实缺陷，已修）
- `tests/integration/test_e2e_metrics.py`：`sys.path.insert(0, …core/tools/evaluation)` 指向已删目录 → 修复为 `core/tools`。**该缺陷使该测试文件单独运行时 import 失败**（此前靠其他测试文件的进程级 sys.path 副作用掩盖）——正是「测试不可信赖」的实证。

### 2.3 历史文档（archival 标注，23 份）
V3_ARCHITECTURE_PLAN / V3_MIGRATION_MAP / V3_BASELINE_AUDIT / V3_IMPLEMENTATION_REPORT / V3_RED_TEAM_REPORT / V3_FINAL_AUDIT / IMPROVEMENT_PLAN / P13_3D_REPORT / P13_3_REPORT / P13_3C_REPORT / P13_3D_R2_PREREG / P13_3D_R3_PREREG / R3_1_CALIBRATION_REPORT / R3_2_REAL_WRITER_PREREG / R3_WRITER_PROTOCOL / R3_W0/W1_PROMPT_TEMPLATE / COMPETITION_INTELLIGENCE_AUDIT / PAPER_INTELLIGENCE_AUDIT / SCIENTIFIC_WRITING_AUDIT / RESEARCH_QUALITY_AUDIT / BASELINE_REPORT / decisions/2026-09-04-refactor-plan-v2.md

### 2.4 保留（非失效引用）
- `docs/architecture/HARDENING_PROGRAM.md`：`projects/bench-*|P13-3D* → research/` 是**迁移完成说明**（描述历史事实）
- `docs/BENCHMARK.md`：`core/knowledge/bench/imported`、`projects/_bench_*` 是**命令输出路径**（由命令创建）
- `research/REPOSITORY_AUDIT/*`：历史审计快照（描述当时状态）

### 2.5 空目录
- `core/tools/evaluation/`（仅 __pycache__ 残留，源文件已迁至 core/tools/ 根）→ **已删除**

## 3. 测试可信度（治理②）

| 检查 | 结果 |
|---|---|
| assert 总数 | 1624 个（全库 test_*.py） |
| 无断言文件 | 3 个：test_aggregate_scores / test_gate_paper_thresholds / test_openai_manifest —— 均为 unittest `self.assert*` 风格（正则误报），实际有断言，**健康** |
| 4 skipped 归因 | 3 个 e2e = V2 流水线显式占位（V3 runtime 已覆盖，见 tests/integration/test_*_runtime.py）；1 个 = 无人工审批节点条件跳过。均带注释说明，**无掩盖** |
| 单测隔离缺陷 | test_e2e_metrics.py sys.path 失效（§2.2）——修复后单文件可独立运行 |
| e2e_metrics 测试更新 | `test_method_hit_compact_canonicalization` → `test_structure_hit_compact_canonicalization`（结构唯一评分依据后断言新函数） |

## 4. 历史兼容性与命名统一（治理③④，真正改造，非注释兼容）

| 项 | 旧 | 新 | 状态 |
|---|---|---|---|
| gt.json 字段 | `allowed_model_families` | `allowed_modeling_structures` | ✅ 5 题全部迁移（字段删除，无并存） |
| e2e_metrics 输出键 | `method_selection` | `structure_alignment` | ✅（历史数据读取仍按旧键） |
| e2e_metrics detail 键 | `method_selection_basis` / `top1_family` / `top1_family_hit` | `structure_alignment_basis` / `top1_structure` / `top1_structure_hit` | ✅ |
| 评分逻辑 | 结构命中 or 字符串方法兜底（`_method_hit`） | 结构命中唯一依据（紧凑匹配保留在 `_structure_hit`） | ✅ `_method_hit`/`_load_card_names` 已删除 |
| k002_gen_bundles | `gt.get(…modeling_structures) or gt.get(…families)` | `gt.get("allowed_modeling_structures") or []` | ✅ |
| 术语门禁 | `# legacy compat` 行内豁免 | **豁免机制删除**（生产区零注释兼容，杜绝未来混入） | ✅ |
| CUMCM-Bench-v2.json | — | 已全部为 `allowed_modeling_structures`（本轮确认无旧字段） | ✅ |

**关键决策**：历史数据（K001 55 runs / B0 / B0-R2 项目 / bench-m4 基线）是冻结快照，**只读不迁移**；读取历史数据时按历史格式读取（如测试锚点 `method_selection`），新写入一律新键。这是「历史数据读取」而非「写入兼容」。

## 5. 校验范围统一（历史债务治理）

**问题**：`validate.py` 将 projects/ 内滞留的 P15 研究实验项目（p151-*/rcs1-*/v3-real-*，无论文交付契约）当作论文交付实例校验 → 4 项假失败（占位 main.tex 63 字 / 图表引用 / 物理模型 / 数值追溯 25%）。

**修复**（语义与文档声明一致）：
- 新增 `RESEARCH_PROJECT_PREFIXES = ("p151-", "rcs1-", "v3-real-", "bench-")` 统一常量
- 新增 `_is_research_scan_path()`：research/ 目录 + projects/ 下研究实验项目统一识别
- `iter_repo()`（全仓库扫描）与 `_live_project_dirs()`（项目级扫描）**共用同一排除语义**
- 结果：validate.py 57 通过 / 0 失败（此前 53/4）

## 6. 统一契约文档（节点标准 + 通信协议）

新增 `research/P15/protocol/P15-EXPERIMENT-CONTRACT-v2.md`，定义：
- 输入层（problem_cards / gt.json 唯一字段名）
- 词表层（model_families.yaml 18 canonical，字符串 ≠ 本体）
- Bundle 层（臂差异仅在 BEGIN REFERENCE 区）
- Run 层（manifest v2 / MODEL_IR 18 字段 / deterministic v2 键）
- Register 层（三 gate：哈希 / 覆盖度 / 验证计划 + 退出码）
- 盲评层（22 维 rubric、去标识、Generator ≠ Evaluator）
- 冻结层 / 分析层（配对 Δ + bootstrap + 区分度预检）
- **兼容与迁移规则**（v1.2 已执行清单）
- **扩展指引**（新题/新卡/新实验/新指标/新节点的插入契约）

## 7. 验证

- `py -3.12 -m pytest tests -q` → **855 passed / 4 skipped**（零回归）
- `py -3.12 core/tools/catalog_check.py --check` → OK
- `py -3.12 core/tools/catalog_check.py --check-terminology` → OK（production 零残留，无行内豁免）
- `py -3.12 core/tools/validate.py` → **57 通过 / 0 失败**

## 7.1 K001 冻结基线更新（术语治理迁移，2026-09-09 补充）

- **事件**：本报告 §3 的字段迁移（5 题 `gt.json` `allowed_model_families` → `allowed_modeling_structures`，删除旧键）改变了 K001 冻结清单中的 `problem_cards/*/gt.json` → `k001_freeze.py --check` 报 5 处 CHANGED。
- **性质**：K001 已 CLOSED（实验完成），评分数据独立冻结于 DATA FREEZE（165 文件，未受影响，未漂移）；gt.json 迁移是术语统一治理（删除旧键，非注释兼容）——**恢复旧字段违背治理指令，故不恢复**。
- **处置**：K001 冻结基线重冻（44 文件，frozen_root `a9fe304…`）；治理报告与 git 历史共同记录此次一次性漂移的原因。此后 K001 冻结校验以新基线为准。
- **审计含义**：K001 的实验期协议（评分时点的 gt.json 内容）由 DATA FREEZE 165 文件 + 评分文件内嵌 `rubric_version`/题面 sha256 追溯；术语迁移不改变 K001 的 55 个 runs 的评分依据（评分对照冻结题面与产物，不依赖 gt.json 字段名）。

## 8. 遗留（不属本轮范围，记录观察）

1. `projects/` 内 19 个 P15 历史研究项目**保持原位**（B0/B0-R2 报告路径引用为历史快照；K001/K002 正式 runs 已各自独立目录，不再依赖 projects/）。未来若需要，可整体迁至 research/ 并更新报告链接（会破坏历史快照，需显式决策）。
2. `research/P13-3D/scripts/run_p13_3d.py` 等 docstring 仍描述 evaluation/ 时代位置（研究区历史脚本，保留）。
3. e2e 3 个显式占位测试（V2 流水线产物）保持 skip——V3 runtime 已有真实覆盖；若未来需重建 V2 fixture 可恢复。
