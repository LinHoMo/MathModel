# HANDOFF —— Modeling-Harness 跨题交接（给下一个 Agent）

> 本文面向**接手继续优化 harness 本身的 Agent**。项目实例的交接在各自目录的 `HANDOFF.md`。
> 本文只写四件事：门禁怎么跑、本轮改了什么、还欠什么、建议的工作序。
> 真源指针（不要在本文件里另记数字）：`docs/STATUS.md`（状态数字）、
> `docs/architecture/V3.1_ARCHITECTURE.md`（架构）、`docs/ONTOLOGY_TERMINOLOGY.md`（术语）、
> `TASKS.md`（任务看板）、`AGENTS.md`（工作协议）。
> 建立时间：2026-09-10，随「2026 A/B 双题建模演练 + harness 反向优化」一节交付。

---

## 1. 本次演练产出的实例入口

| 实例 | 交接文档 | 一句话 |
|---|---|---|
| 2026 A 药材烘干 | `projects/cumcm2026a/HANDOFF.md` | 径向耦合传热传质 PDE + Landau 移动边界；Q3 57.4222 h、Q4 64.7806 h |
| 2026 B 干扰源定位清除 | `projects/cumcm2026b/HANDOFF.md` | 楔形交会凸多边形 + 同心环覆盖 + 交会-归航清除；30 组演练清除比例 1.0 |
| 2024 A 参考实例 | `projects/cumcm2024a/` | 此前的弦长约束刚性链模型，作为对照样本 |

两篇实例交接文档的结构是刻意的模板：**一句话结论 → 交付物与真源边界 → 建模骨架 →
结果表 → 结构性发现 → 复现 → 踩坑清单 → 验证记录 → 局限 → 门禁 → 最短路径**。
后续新增实例建议沿用同一骨架，方便读者横向切换。

---

## 2. 四件套门禁（任何改动后必跑）

仓库的「四件套」是交付验收的固定口径。命令与通过形态如下（在仓库根执行）：

| 检查 | 命令 | 通过形态 |
|---|---|---|
| 项目级校验 | `py -3.12 src/modeling_harness/cli/validate.py` | `验证完成: 45 通过, 0 失败, 0 警告` |
| catalog 双视图 | `py -3.12 src/modeling_harness/cli/catalog_check.py --check` | `OK — v3 双视图与 roles/DAG/validators 三方一致` |
| 术语一致性 | `py -3.12 src/modeling_harness/cli/catalog_check.py --check-terminology` | `OK — production 区旧术语零残留` |
| 测试套件 | `py -3.12 -m pytest tests -q` | 全绿（本轮基线 600 passed / 0 failed / 0 skipped） |

其中 `validate.py` 内部是 L1–L6 分层防御。与实例文档关系最大的是三条：

- **L4 数值追溯**：把各活跃实例的结果聚合文件里的数值汇集为「池」，逐一核对模型描述文档里的
  数字能否在池中找到（相对容差 0.5%、绝对 0.01，通过阈值 90%）。**只扫实例根目录的 `*.md`**
  （不递归），所以根目录新增的交接文档会被计入分母。
- **L5 禁用词 / 内部路径 / 占位符**：默认**只扫 `projects/`**。`docs/` 下的文档不在扫描范围内，
  这也是本文可以正常引用脚本名与结果文件名的原因。
- **L6 图表引用**：检查模型描述文档里的代码围栏是否闭合、Mermaid 是否成对。

> 教训：**在这两个目录里写文档，先用校验器扫一遍再提交。** 本轮初稿就因为「在踩坑清单里举例
> 写出了禁用词本身」而被判失败 —— 举例也会命中，见 §3 与 §5。

---

## 3. 反馈：本轮对 harness 的修复（已随实例交付）

| 缺陷 | 现象 | 修复 | 影响面 |
|---|---|---|---|
| L6 图表引用误判 | 原实现用「反引号总数是否为偶数」判断围栏闭合，任何含合法 Mermaid 块的文档都被判「未闭合」 | 改为逐行围栏状态机（遇行首围栏翻转开合标记，结尾仍未闭合才报错） | 所有含 Mermaid 的模型描述文档 |
| L5 内部路径泄漏 | 实例创建脚本生成的说明模板里含内部脚本后缀与结果文件名，触发 L5.4 | 模板与两题目录说明改为中性表述 | 新实例的默认产物 |
| 实例数值对齐 | 两题 `model_ir.json` 的实验参数与结果台账存在口径差 | 按结果台账回填，重过 schema 校验 | 实例的模型定义 |

修复后四件套全绿（见 §2）。**注意**：这三处都是「演练反推出来」的，属于 feedback 路径；
建议后续新增实例时继续把「跑一遍四件套」当作照妖镜，而不是等提交后再补。

---

## 4. 前馈：知识沉淀（经验入库）

本轮把 A/B 两题的可复用经验按既有治理规范入库，**没有另起体系**：

| 层级 | 目录 | 本轮新增 | 规模变化 |
|---|---|---|---|
| 方法卡 | `src/modeling_harness/knowledge/methods/cards/` | `mc-moving-boundary-pde`、`mc-bearing-triangulation`、`mc-coverage-search` | 24 → 27 |
| 失败卡 | `src/modeling_harness/knowledge/failures/` | `fm-moving-boundary-ignored`、`fm-pde-grid-underresolved`、`fm-bearing-degenerate-crossing`、`fm-coverage-ring-incomplete`、`fm-truth-navigation` | 17 → 22 |
| playbook | `src/modeling_harness/knowledge/playbooks/` | `playbook-2026A-herb-drying`、`playbook-2026B-emitter-localization` | 12 → 14 |

**沉淀约定（后续 Agent 请遵守）**：

1. 新经验按同一格式补卡（方法卡三要素：Constraint / Prior / Validation），**不要新建目录或新体系**。
2. 新增卡片后同步两处规模数字：`knowledge/README.md` 与 `playbooks/INDEX.md`。规模数字若未同步，
   仓库级检查会不一致。
3. 新卡片的 `problem_type` / `family` 标识**刻意避开既有卡**，以免改变既有检索结果与检索测试期望。
   若确实需要复用既有标识，请先看检索测试的断言，再决定是扩断言还是换标识。

---

## 5. 未决与优化 backlog（按优先级）

**P0 — 仓库卫生（建议立刻做）**

- `.rivet/` 是本地工具状态库（含会话数据库与备份，约 4.4 MB），当前**未被忽略**也未纳入版本管理。
  它与 `projects/` 无关，属于工作区噪声。**已在本轮处理**：加入 `.gitignore`（与既有
  `.workbuddy/` 同级处理）。若后续再出现同类工作区目录，按同一模式处理，不要提交进仓库。

**P1 — 数值追溯余量提醒**

- 当前追溯比例约 91.7%，阈值 90%，余量已不大。追溯池的「噪声」主要来自三类非物理量：
  **章节编号**、**命令行里的解释器版本号**（如 `py -3.12` 会被拆成两个数）、
  **上标/紧贴系数的小数**（乘号不留空格会把系数从中间切开）。
- 两个可选方向：一是**写文档时规避**（章节起名不编号、乘号后加空格、指数用 e-notation），
  成本低、立竿见影；二是**改校验器**（对「围栏内代码块」与「版本号形态」做白名单），
  属于契约变更，须走 ADR 且不得破坏既有断言。**优先选前者**，后者留待确有必要时再动。

**P1 — 禁用词表对说明类文档的误伤面**

- 词表里有一批「元叙述/套话」词，本意是抑制论文腔，但交接说明类文档在「举例说明不要写什么」
  时极易自伤（本轮实例）。两个方向：一是文档写法规避（不举原词，只指向校验器顶部词表）；
  二是给「交接/说明类文档」加白名单或豁免标记。同样优先前者。

**P2 — 知识卡检索面**

- 新增的 3 方法卡与 5 失败卡是「入库」但未必进入既有检索路径（取决于检索按 problem_type 还是
  按 family）。若希望它们在未来的同类题上被自动召回，需要确认检索入口并补一条检索测试。
  这是一条**能力**（capability）而非基建（infra）的改动，优先级取决于是否真的要在检索中使用它们。

---

## 6. 给下一个 Agent 的工作序（最短路径）

1. **先建认知**：按 `AGENTS.md` §1 的必读顺序读完 `docs/STATUS.md` →
   `docs/architecture/V3.1_ARCHITECTURE.md` → `docs/ONTOLOGY_TERMINOLOGY.md` → `TASKS.md` →
   `AGENTS.md`。不要跳过，术语与边界都在里面。
2. **再定基线**：跑一遍四件套（§2），确认当前是全绿，再开始改动。基线不绿时先修基线。
3. **认领一条 backlog**：优先 §5 的 P0/P1，一次只动一件事，改动范围写进任务卡。
4. **收尾三件**：跑四件套 → 更新 `TASKS.md`（登记任务与 commit 锚点）与 `docs/STATUS.md`
   （若数字有变）→ 若改动属于架构级，补 `docs/decisions/` 的 ADR。
5. **想读实战样例**：直接进 `projects/cumcm2026a/HANDOFF.md` 与
   `projects/cumcm2026b/HANDOFF.md`，再对照 `research/` 与 `projects/cumcm2024a/` 的同类产物。
