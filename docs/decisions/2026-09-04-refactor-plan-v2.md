# MathModelSkills 深度体检与标准化方案

> 生成日期：2026-09-04
> 性质：**诊断与排期文档，本次未改动任何既有文件**
> 体检方法：八步体检法（读顶层文档找口径冲突 → 实跑自验脚本 → frontmatter 合规 → 资产体量 → 实际产出质量 → 孤儿参数 → 路径引用真实性 → 状态与仓库卫生）

---

## 0. 一句话结论

**这是一个架构设计正确、但执行链没有真正接通的项目。** 状态外置、脚本门禁、入口一行转发、引擎与实例分离——这四件最难做对的事它都做对了；但门禁可以被绕过、参数是三处重复且基线抄错、产物契约存在覆盖冲突，导致 `STATE.md` 显示的「29/29 全部完成」与门禁实跑的「6 项硬失败」同时成立。它现在更像一套**写得很完整的执行规范**，而不是一条能稳定跑出达标论文的流水线。

---

## 1. 体检结论（分维度评分）

| 维度 | 评分 | 判定依据（文件 / 数字） |
|---|---|---|
| **架构设计** | 8.5 / 10 | 状态外置 `work/STATE.md`、门禁脚本化 `core/tools/gate.py`、5 个 runtime 入口全部 `@AGENTS.md` 一行转发、`catalog.yaml → gen_runtime_manifest.py → agents/openai.yaml` 自动生成。UTG 六层到 29 agent 的映射无空缺 |
| **内容资产** | 8 / 10 | `knowledge/methodology` 54 篇 16424 行、`paper-cases` 117 篇 15601 行，是真实干货；29 个 agent frontmatter 的 `description` 100% 齐全（缺失数 0） |
| **可执行性** | 3 / 10 | `state.py` 报 29/29 完成、`failed=0`，但 `gate.py all` 报 6 项硬失败；29 步集中在 210 秒内完成，其中 7 步落在同一秒 `01:14:58` |
| **门禁可信度** | 2.5 / 10 | 同一指标两个脚本给两个数字（追溯率 `validate.py` 29.5% vs `validate_project.py` 51%）；假失败污染（`appendix.tex` 被当正文统计字数、`inputs/problem.md` 赛题原文被查禁用词） |
| **参数治理** | 3 / 10 | 同一参数 3 处定义（env/config.yaml、loader.py 的 DEFAULT_CONFIG、9 个竞赛包 config.yaml）；竞赛包 thresholds **无人消费**，是死参数；页数基线与国赛官方冲突 |
| **可发现性** | 5 / 10 | README「当前状态」与实跑结果全面不符；403 处知识库路径引用中 15 处断链 |
| **仓库卫生** | 4 / 10 | `__pycache__` 51 个、`_debug/` 24 个调试脚本、`work/` 混入 `run_*.py` 执行残留、顶层 `_v.txt` 为 GBK 乱码的验证输出 |

---

## 2. 最致命的 3 个断点

### 断点 1：门禁形同虚设，进度可以被直接推到终点

| 证据 | 数值 |
|---|---|
| `python core/tools/state.py cumcm2024a status` | **29/29 全部完成，failed=0** |
| `python core/tools/gate.py cumcm2024a all` | **79 通过 / 6 硬失败 / 1 软失败** |
| `python core/tools/validate_project.py --project projects/cumcm2024a` | **36 passed / 10 warnings / 9 hard errors** |
| 状态时间戳跨度 | 01:11:28 → 01:14:58，共 **210 秒**完成 29 步 |
| 同秒批量完成 | `01:14:58` 完成 7 步（reviewer 全 8 步中的 7 步） |

**根因**：`gate.py` 与 `state.py advance` 之间没有强制耦合。`advance` 不检查门禁结果，产物不达标也能登记完成。结果是流程可信度归零——STATUS 说做完了，实际论文 11 页 / 5867 字，而国赛要求正文 ≥20 页量级。

证据文件：`projects/cumcm2024a/work/state.json`、`projects/cumcm2024a/work/STATE.md`

---

### 断点 2：国赛参数基线抄错，且自身矛盾

现行 `core/env/config.yaml`：

```yaml
paper:
  min_pages: 25      # 注释写「国赛 25-30 页」
  max_pages: 30
  min_words: 18000   # 注释写「国赛 18000-25000 字」
  chars_per_page: 800
  page_fill_ratio: 0.8
```

对照 **《2025年全国大学生数学建模竞赛论文格式规范（2025年修订稿）》第四条**（来源：全国组委会官网 cmathc.org.cn/mcm/tz/303.html）：

> 论文从第四页开始是正文内容（**不要目录，尽量控制在 20 页以内**）；正文之后是论文附录（页数不限）。

| 项 | 现行值 | 国赛 2025 官方 | 偏差 |
|---|---|---|---|
| 正文页数 | min 25 / max 30 | **尽量 ≤20 页**（附录不限） | 下限超官方 5 页，上限超 10 页 |
| 正文页数（自洽） | min_pages 25 > max_pages×fill_ratio = 30×0.8 = **24** | — | **参数自身矛盾**，25 页永远过不了 24 页的填充率闸门 |
| 字数 | 18000 | 无官方规定 | 18000 ÷ 800 字/页 = **22.5 页**，必然突破 20 页上限 |

并且 `core/templates/latex/cumcm/rules.md` 第 8 行白纸黑字写着：

> 页数：正文 25–30 页（不足 25 页会明显吃亏）

同文件标注 `rules_verified: 2026-08-30` —— **是核对过、但核对错了**。这意味着 Agent 会拿着错误的官方基线去指导写作，越"达标"越违规。

---

### 断点 3：两项合规硬缺失，属"可能被取消评奖资格"级别

| 检查 | 实跑结果 | 官方要求（2025 试行） |
|---|---|---|
| 正文引用 | `main.tex` 中 `\cite` 出现 **0 次**（`references.bib` 有 10 条） | 第七条：所有引用必须在**正文引用处予以标注** |
| AI 使用披露 | 正文中 AI 相关关键词命中 **0 处** | 《人工智能工具使用规定(2025年试行)》：正文相应位置标注 + 参考文献列出 AI 工具 + 支撑材料含「AI工具使用详情」PDF |
| 编译链 | `main.log` 存在 **3 处未定义引用** | 未定义引用会导致参考文献列表渲染失败 |

项目的 `work/ai_usage_ledger.json` 里**记录了 3 条真实 AI 使用**（Claude Opus 4 用于公式推导、代码实现、章节撰写），但正文完全没披露——**用了 AI 却没声明，比不用 AI 更危险**。

补充一条极易踩的坑：AI 使用详情**不能放进附录**（附录参与查重，AI 内容相似度高会显著抬高查重率），必须作为独立 PDF 放支撑材料。当前 `cumcm/config.yaml` 把输出路径写成 `support_materials/ai_usage_disclosure.md`（Markdown），与官方要求的 PDF 不符。

---

## 3. 问题清单（P0 / P1 / P2）

### P0 — 不解决则整套系统不可用

| # | 问题 | 证据 | 影响 |
|---|---|---|---|
| P0-1 | 门禁与状态推进未强制耦合 | `state.py` 29/29 vs `gate.py` 6 硬失败 | 流程可信度归零，弱模型可"一键跑完" |
| P0-2 | 国赛页数/字数基线错误且自相矛盾 | `env/config.yaml` min_pages 25、`templates/latex/cumcm/rules.md` 第 8 行 | Agent 按错误基线写论文，越达标越违规 |
| P0-3 | 正文零引用、AI 使用零披露 | `main.tex` cite=0；AI 关键词 0 处 | 官方规范第十二条：可能取消评奖资格 |
| P0-4 | 参数三处重复 + 竞赛包参数为死参数 | `min_pages` 在 39 处出现；`loader.py` 全文无 `templates/latex` 引用 | 改一处不生效，用户"统一调整"诉求落空 |
| P0-5 | 追溯率口径分裂 | `validate.py` 29.5% vs `validate_project.py` 51% | 核心卖点（可追溯）无法证伪也无法证实 |

### P1 — 影响可维护性与可插拔性

| # | 问题 | 证据 | 影响 |
|---|---|---|---|
| P1-1 | 产物契约覆盖冲突：`work/guardrails_report.json` 被 `programmer` 与 `writer` 两个 agent 同时声明 | catalog 29 条 artifact，唯一路径仅 28 个 | writer 产物覆盖 programmer 产物，L5 护栏证据丢失 |
| P1-2 | 入口支持的竞赛三处不一致：`new_project.py` 3 个 / `AGENTS.md` 5 个 / 实际模板包 **9 个** | `new_project.py:173`、AGENTS.md 命令表、`ls core/templates/latex` | 6 个模板包（含 mathorcup/apmcm/renzhengbei/shuweibei）无法从入口创建 |
| P1-3 | 参数键名不统一：cumcm 用 `min_pages`、diangong 用 `body_pages`、huawei/huashu 用 `base: env.config.paper` | 各包 config.yaml | 无法写统一读取逻辑，插拔竞赛包必出错 |
| P1-4 | 脚手架目录与实际项目目录不一致：脚手架有 `inputs/external`，实际项目有 `tables/`（空）和 `_debug/`（24 文件） | `new_project.py:21-30` vs `ls projects/cumcm2024a` | 临时文件无处可去，只能污染正式目录 |
| P1-5 | `figures/` 职责错位：只放 `all_results.json`，真正的图在 `paper/figures/` | 目录清单 | 两个 figures 目录语义重叠，Agent 不知道往哪写 |
| P1-6 | 校验脚本存在假失败：把 `appendix.tex` 当正文统计字数（290 字 vs 需 18000）、把 `inputs/problem.md` 赛题原文纳入禁用词扫描 | `validate.py` 失败项输出 | 门禁持续报错 → 使用者学会忽略门禁 → 门禁彻底失去信用 |
| P1-7 | Reviewer 手缺 `knowledge/` `laws/` `templates/`（其余三手都有） | `ls core/Reviewer` | 四手结构不对称，插拔时 Reviewer 是特例 |
| P1-8 | README「当前状态」全面失真 | README 称 56通过/0失败、gate 57通过/0失败、217 passed；实跑 49/6/2、79/6/1、244 passed | 使用者基于假数据决策 |
| P1-9 | 15 处知识库路径断链，其中 cookbook 引用的 12 个代码模板全部不存在 | 403 引用 / 15 断链 | Agent 按图索骥找不到文件 |

### P2 — 卫生与体验

| # | 问题 | 证据 |
|---|---|---|
| P2-1 | `__pycache__` 51 个 + `_debug/` 24 个调试脚本 + `code/` 27 个 `diag_*.py` 混入正式代码 | 目录统计 |
| P2-2 | 顶层 `_v.txt` 是 GBK 乱码的验证输出（6.6KB），无 `.gitignore` 覆盖 | 根目录 |
| P2-3 | `work/` 混入执行残留脚本 `run_*.py`、`count_stats.py`、`diag_trac.py` | 目录清单 |
| P2-4 | 4 套审计/状态文件并存：`state.json` + `audit_log.json` + `audit_chain.json` + `final_audit_log.json` | 目录清单 |
| P2-5 | `paper/main.log` 显示 xelatex 仅运行 1 次，未跑完整链（xelatex→bibtex→xelatex→xelatex） | gate 输出 |

---

## 4. 国赛标准参数基线（用户指定：先固定国赛）

> 来源：《2025年全国大学生数学建模竞赛论文格式规范（2025年修订稿）》 + 《全国大学生数学建模竞赛人工智能工具使用规定（2025年试行）》
> 官方入口：https://www.cmathc.org.cn/mcm/tz/303.html ｜ https://www.mcm.edu.cn/

### 4.1 参数分层原则

**这是整个参数体系改革的核心**：把参数分成三层，性质不同、处置方式不同。

| 层 | 含义 | 可否被 profile 覆盖 | 违反后果 |
|---|---|---|---|
| **OFFICIAL**（官方硬约束） | 规范条文明确规定 | ❌ **锁定**，只能随当届官方文件更新 | 可能取消评奖资格 |
| **DERIVED**（派生值） | 由官方约束推算 | ⚠️ 仅可调派生系数 | 可能间接导致违规 |
| **TUNABLE**（经验软目标） | 无官方规定，来自获奖论文统计 | ✅ 用户自由调整 | 影响得分，不影响资格 |

### 4.2 国赛参数表（CUMCM 2025）

#### OFFICIAL 层 —— 不可覆盖

| 参数键 | 取值 | 规范依据 | 现行实现 |
|---|---|---|---|
| `body.max_pages` | **20** | 第四条：正文尽量控制在 20 页以内 | ❌ 现为 max 30 |
| `body.appendix_pages` | **unlimited** | 第四条：附录页数不限 | ❌ 未表达 |
| `body.no_toc` | **true** | 第四条：不要目录 | ✅ 已检查（`tableofcontents` 未出现） |
| `abstract.single_page` | **true** | 第三条：摘要内容（含标题和关键词）不能超过一页 | ❌ 未检查 |
| `abstract.no_english` | **true** | 第三条：无需翻译成英文 | ❌ 未检查 |
| `pagination.start_page` | **3** | 第三条：从第三页开始编写页码 | ❌ 未检查 |
| `pagination.position` | **footer_center** | 第三条：页码位于页脚中部，阿拉伯数字从 1 开始 | ❌ 未检查 |
| `layout.margin_cm` | **2.5** | 第一条：上下左右各留出至少 2.5 厘米 | ✅ main.tex 已设 2.5cm |
| `layout.no_header` | **true** | 第六条：不能有页眉 | ❌ 未检查 |
| `anonymity.scope` | **[摘要页, 正文, 附录, 支撑材料]** | 第六条 + 第十一条 | ⚠️ 现仅覆盖正文 |
| `electronic.format` | **pdf 或 docx** | 第十条：文件格式只能为 PDF 或 Word 之一 | ❌ 未检查 |
| `electronic.max_bytes` | **20971520**（20MB） | 第十条：文件大小不超过 20MB | ❌ 现仅检查 `pdf_min_bytes=102400`（下限） |
| `electronic.no_compress` | **true** | 第十条：不要压缩 | ❌ 未检查 |
| `electronic.no_commitment_page` | **true** | 第十条：承诺书和编号专用页不要放在电子版论文中 | ❌ 未检查 |
| `support.required_format` | **zip 或 rar** | 第十一条：使用 WinRAR 压缩（ZIP 或 RAR） | ❌ 未实现 |
| `support.max_bytes` | **20971520**（20MB） | 第十一条：大小不超过 20MB | ❌ 未实现 |
| `support.must_include` | **[全部可运行源程序, 自主查阅使用的数据, 支撑材料文件列表]** | 第五条 + 第十一条 | ❌ 未实现 |
| `citation.inline_required` | **true** | 第七条：在正文引用处予以标注 | ❌ **当前 cite=0** |
| `citation.style` | **gbt7714-numerical** | 第七条：按科技论文规范（现行已配置 ✅） | ✅ 配置正确但未生效 |
| `ai.disclosure_in_body` | **true** | AI 使用规定：在正文相应位置进行标注 | ❌ **当前 0 处** |
| `ai.disclosure_in_references` | **true** | AI 使用规定：在参考文献中列出所用 AI 工具 | ❌ 未实现 |
| `ai.support_pdf_name` | **AI工具使用详情** | AI 使用规定：支撑材料须含该 PDF | ❌ 现为 `ai_usage_disclosure.md` |
| `ai.support_pdf_format` | **pdf** | 同上 | ❌ 现为 `.md` |
| `ai.exclude_from_appendix` | **true** | 附录参与查重，AI 内容相似度高会抬高查重率 | ❌ 未实现 |

#### DERIVED 层 —— 由官方约束推算

| 参数键 | 取值 | 推导过程 |
|---|---|---|
| `paper.body_words_min` | **13000** | 目标 17 页（20 页留 3 页余量给图/表/参考文献）× 800 字/页 ≈ 13600，取整 13000 |
| `paper.body_words_max` | **16000** | 20 页 × 800 字/页 = 16000，超出将突破页数上限 |
| `paper.abstract_words` | **[400, 600]** | 现行值，且须满足 ≤1 页硬约束；两者冲突时以页数为准 |
| `paper.page_fill_ratio` | **0.85** | 目标 17/20 = 85%，较现行 0.8 收紧 |

#### TUNABLE 层 —— 用户自由调整（无官方依据，来自经验）

| 参数键 | 建议值 | 说明 |
|---|---|---|
| `paper.min_figures` | **6** | 保持现行值 |
| `paper.min_tables` | **4** | 保持现行值 |
| `paper.min_equations` | **15** | 保持现行值 |
| `paper.min_references` | **10** | 保持现行值（官方无数量规定） |
| `paper.recent_ref_ratio` | **0.3** | 现行 0.6 过严，导致持续 WARN；国赛鼓励近三年核心期刊但非强制，建议放宽到 0.3 或改 WARN |
| `paper.table_max_rows_inline` | **12** | 保持 |
| `paper.figure_min_width` | **0.85** | 保持 |

### 4.3 现行值 → 国赛标准 迁移对照

| 参数 | 现行 | 国赛 2025 | 处置 |
|---|---|---|---|
| `paper.min_pages` | 25 | **废弃**（改用 `body.max_pages=20` + `body_words_min=13000`） | 删除 |
| `paper.max_pages` | 30 | **20** | 改值 + 移入 OFFICIAL 层 |
| `paper.min_words` | 18000 | **13000**（min）/ **16000**（max） | 改值 + 移入 DERIVED 层 |
| `paper.chars_per_page` | 800 | 800 | 保留（派生系数） |
| `paper.page_fill_ratio` | 0.8 | **0.85** | 改值 |
| `paper.pdf_min_bytes` | 102400 | 保留下限 **+ 新增上限 20971520** | 补上限 |
| `paper.recent_ref_ratio` | 0.6 | **0.3** | 放宽（长期 WARN 会让门禁失去信用） |

---

## 5. 可插拔参数架构设计

### 5.1 现状：参数散在三处，且其中一处是死的

```
core/env/config.yaml                     ← 真正在被消费（7 组：paper/code/modeling/review/runtime/checkpoint/cloud_sandbox）
core/env/loader.py  DEFAULT_CONFIG       ← 硬编码兜底副本（第 28/29/34/38 行重复定义 min_pages=25 等）
core/templates/latex/*/config.yaml       ← 9 个包，其中 5 个抄了完全相同的数值
                                            ↑ loader.py 全文不引用 templates/latex，这些 thresholds 是死参数
```

验证：`grep -rn "templates/latex" --include="*.py" core/` 仅命中 `doctor.py:143`（只检查目录存在性）。

### 5.2 目标：单一真源 + 差量覆盖 + 官方锁

```
core/env/
├── schema.yaml           【新增】参数定义表：键 / 类型 / 范围 / 层级 / 是否可覆盖 / 依据条文
├── loader.py             【改造】删除 DEFAULT_CONFIG 硬编码，改为 schema 驱动 + 三层合并
├── config.yaml           【瘦身为 3 行】只写 profile 选择与少量用户覆盖
└── profiles/
    ├── _base.yaml        【新增】所有参数的默认值与层级声明
    ├── cumcm-2025.yaml   【新增】国赛（默认，官方值锁死）
    ├── mcm-2026.yaml
    ├── huawei.yaml
    ├── huashu.yaml
    ├── diangong.yaml
    ├── mathorcup.yaml
    ├── apmcm.yaml
    ├── renzhengbei.yaml
    └── shuweibei.yaml
```

**合并优先级**（后者覆盖前者）：
```
_base.yaml  <  profiles/<竞赛>.yaml  <  config.yaml 的用户覆盖段
                ↑ OFFICIAL 层参数在此之后不可被覆盖，强行覆盖则报错而非静默忽略
```

### 5.3 schema.yaml 示例（体现三层与锁定）

```yaml
paper:
  body:
    max_pages:
      value: 20
      type: int
      layer: OFFICIAL          # 不可被 profile 覆盖
      source: "2025规范 第四条"
      note: "正文尽量控制在20页以内（附录不限）"
  min_figures:
    value: 6
    type: int
    layer: TUNABLE            # 用户可改
    range: [3, 20]
    source: 经验值
ai:
  support_pdf_name:
    value: "AI工具使用详情"
    type: str
    layer: OFFICIAL
    source: "AI工具使用规定(2025试行)"
```

### 5.4 竞赛包改造：从"复制全套"到"只写差量"

**现状问题**：`cumcm / apmcm / mathorcup / renzhengbei / shuweibei` 这 5 个包的 `thresholds` 段完全相同（25/30/18000/6/4/15/10/400-600/0.8），是复制粘贴，不是调研结果。

**改造后**——`profiles/cumcm-2025.yaml` 只写国赛独有的东西：

```yaml
inherits: _base

official:                       # 官方硬约束，本包专有
  body: {max_pages: 20, no_toc: true, appendix_pages: unlimited}
  abstract: {single_page: true, no_english: true}
  pagination: {start_page: 3, position: footer_center}
  electronic: {format: [pdf, docx], max_bytes: 20971520, no_commitment_page: true}
  support: {format: [zip, rar], max_bytes: 20971520}
  ai: {disclosure_in_body: true, support_pdf_name: "AI工具使用详情", exclude_from_appendix: true}

tunable:                        # 经验目标，用户可改
  min_figures: 6
  min_tables: 4
  min_equations: 15
  min_references: 10

template:
  cls: core/templates/latex/cumcm/cumcmthesis.cls
  engine: xelatex
  compile_chain: [xelatex, bibtex, xelatex, xelatex]
```

**收益**：新增一个竞赛只需新增一个 profile 文件 + 一个模板目录；改国赛参数只改 `cumcm-2025.yaml` 一处；官方值写错会被 schema 的 `layer: OFFICIAL` 挡住，不可能被下游静默覆盖。

### 5.5 消除"兜底默认值"陷阱

现状：`validate_project.py:1060` 写 `_env_get("paper.min_pages", 25)` —— 即使 config 改了，一旦读取路径异常就会回退到 25，用户改了不生效且无任何提示。

**改造**：`schema.yaml` 驱动后，兜底值从 schema 取，且**回退时打印 WARNING 到 stderr**：

```python
# 改造后
min_pages = require("paper.body.max_pages")   # 缺失即抛错，不静默兜底
```

配套：新增 `python core/tools/env_doctor.py`，一键输出「当前生效参数 / 来源文件 / 是否被覆盖」，让用户改完立刻能验证生效。

---

## 6. 输入 / 输出 / 目录结构标准化

### 6.1 输入规范

| 现状 | 问题 | 标准 |
|---|---|---|
| `inputs/` 只放 `problem.md`（2692 字节 / 44 行） | 无格式约束、无校验、赛题原文被纳入禁用词扫描 | 见下 |

**标准输入契约**：

```
inputs/
├── problem.md            【必需】赛题全文，纯文本，UTF-8
└── external/             【可选】自主查阅的外部数据（赛题自带数据不放这里）
    ├── <数据集>/
    └── SOURCES.md        【必需-if-external】数据来源、获取日期、授权说明
```

配套动作：
1. `new_project.py` 增加 `--from-pdf` / `--from-docx`，自动转纯文本
2. 新增 `core/tools/check_input.py`：校验 problem.md 存在、UTF-8、字数 ≥500、可提取题目
3. **禁用词扫描排除 `inputs/`**（赛题是官方文本，不是 AI 产出）——修复 P1-6 的误报

### 6.2 输出规范（三层分离）

核心原则：**中间产物、手间契约、投稿交付物**是三种性质完全不同的东西，现在混在一起。

```
output/    → 手间契约（四手之间的接口，人读）
work/      → 中间产物（agent 之间的接口，机读，可中断恢复）
deliverables/ → 投稿交付物（交给组委会的最终文件）【新增】
```

**关键新增：`deliverables/`** —— 国赛要求提交三个独立文件，当前项目完全没有对应目录：

```
deliverables/
├── 论文.pdf                  ← 第十条：PDF/Word 之一，≤20MB，不压缩，无承诺书页
├── 支撑材料.zip              ← 第十一条：ZIP/RAR，≤20MB，含全部可运行源程序 + 文件列表
├── AI工具使用详情.pdf         ← AI 使用规定：文件名固定为此，含工具/版本/目的/交互记录/采纳情况
└── MANIFEST.md               ← 三项的自检清单（页数/大小/匿名/引用标注）
```

### 6.3 项目目录结构（优化后）

```
projects/<项目>/
├── inputs/                 # 【只读】输入，全程不被写入
│   ├── problem.md
│   └── external/
├── work/                   # 【机读】中间产物，全部在 catalog.yaml 登记
│   ├── state.json          # 唯一状态真源
│   ├── STATE.md            # 只读镜像（脚本生成，不手工编辑）
│   ├── audit_chain.json    # 唯一审计链
│   └── <agent 产物>.json
├── output/                 # 【人读】手间契约
│   ├── MODEL_SPEC.md
│   ├── CODE_DELIVERABLES.md
│   ├── PAPER_SPEC.md
│   └── reproducibility.json
├── code/                   # 【交付】正式代码，不含调试脚本
├── figures/                # 【交付】图的数据源 + 绘图脚本
│   ├── all_results.json    # 唯一数值真源，所有论文数字必须可追溯到此
│   └── <fig>.py
├── paper/                  # 【交付】论文源
│   ├── main.tex
│   ├── references.bib
│   ├── appendix.tex
│   └── figures/            # 渲染产物（*.pdf）
├── deliverables/           # 【新增】投稿交付物
└── _scratch/               # 【新增】临时区，脚手架显式创建，可随时清空
```

**相对现状的具体变更**：

| 变更 | 现状 | 变更后 | 理由 |
|---|---|---|---|
| `tables/` | 空目录，脚手架不生成 | **删除** | 表格直接写在 tex 中，无独立目录必要 |
| `_debug/`（24 文件） | 执行中长出，脚手架不认 | **`_scratch/`**，脚手架显式创建 | 让临时文件有家可归，不再污染 `code/` |
| `figures/` | 只有 `all_results.json` | 明确为「数据 + 绘图脚本」 | 与 `paper/figures/`（渲染产物）划清职责，解决 P1-5 |
| `code/diag_*.py`（27 个） | 混在正式代码里 | 移入 `_scratch/` | 支撑材料只应含可运行源程序 |
| `work/run_*.py` | 执行残留 | 移入 `core/tools/` 或删除 | 中间产物目录只放产物 |
| `deliverables/` | 不存在 | **新增** | 国赛三项提交物无处安放 |
| `inputs/external` | 脚手架生成但项目里没有 | 保留，且 `SOURCES.md` 作为条件必需 | 外部数据可追溯 |

### 6.4 产物契约冲突修复

- `work/guardrails_report.json` 被 `programmer/guardrails-checker` 与 `writer/guardrails-checker` 同时声明 → 改为 `work/guardrails_report_programmer.json` / `work/guardrails_report_writer.json`
- `STATE.md` 第 29 步声明 `work/revision_execution_report.json`，实际产出 `work/execution_report.json` → 统一为 `work/execution_report.json`
- 新增校验：`catalog.yaml` 中 artifact 路径必须唯一（当前 29 条声明仅 28 个唯一路径）

---

## 7. 门禁与状态机改造

### 7.1 核心：让门禁真正卡住流程

```
现状：  advance 不查门禁 → 产物不达标也能推进 → STATE 显示 29/29
目标：  advance 必须先查门禁 → 门禁 FAIL 则拒绝推进并回退
```

具体动作：
1. `state.py advance` 增加 `--gate-pass` 必需参数，或内部自动调用 `gate.py`，FAIL 时拒绝推进
2. `gate.py` 退出码语义化：`0` 全通过 / `1` 有软失败 / `2` 有硬失败（当前恒返回 0，脚本无法判断）
3. 状态机记录每次门禁结果快照，杜绝"同秒批量完成"（当前 7 步落在 `01:14:58`）

### 7.2 修掉假失败，重建门禁信用

门禁持续报假失败，使用者会学会忽略它——这比没有门禁更糟。

| 假失败 | 现状 | 修复 |
|---|---|---|
| 字数检查扫 `appendix.tex` | 「290 字，需 ≥18000」 | 只扫正文 `main.tex`；附录单独用"是否存在 + 是否含源程序"检查 |
| 禁用词扫 `inputs/problem.md` | 命中赛题原文的"最后" | 扫描范围排除 `inputs/` 与 `_scratch/` |
| 追溯率两个数字 | 29.5% vs 51% | 统一到 `validate_project.py` 的口径，`validate.py` 直接调用它 |

### 7.3 新增国赛合规检查项（现行完全没有的）

```
check_abstract_single_page    摘要 ≤1 页
check_no_toc                  无目录              （已有）
check_pagination_start        页码从第 3 页起
check_no_header               无页眉
check_electronic_size         20MB 上限
check_support_materials       支撑材料 ZIP 含源程序 + 文件列表
check_inline_citation         正文 \cite 数 ≥1 且与 bib 条目匹配   ← 当前为 0
check_ai_disclosure_body      正文含 AI 使用声明                   ← 当前为 0
check_ai_disclosure_ref       references.bib 含 AI 工具条目
check_ai_support_pdf          deliverables/AI工具使用详情.pdf 存在
check_ai_not_in_appendix      AI 内容未出现在附录（查重风险）
check_anonymity_full          摘要页/正文/附录/支撑材料均无身份信息
```

---

## 8. 整改任务表

### P0 任务（建议先做，产出可用底线）

| # | 任务 | 具体动作 | 验收标准 | 出处 |
|---|---|---|---|---|
| P0-A | 建立国赛 profile | 新建 `core/env/profiles/_base.yaml` + `cumcm-2025.yaml`，按 §4.2 表落全部参数 | `env_doctor` 输出的生效值与 §4.2 表逐项一致 | §4 |
| P0-B | 修正文页数/字数基线 | 改 `config.yaml`：`max_pages` 30→20、`min_words` 18000→13000、`page_fill_ratio` 0.8→0.85，删除 `min_pages` | `gate.py` 不再报 "11 pages (< 25)" 这类基于错误基线的判定 | §4.3 |
| P0-C | 修正 rules.md | `core/templates/latex/cumcm/rules.md` 第 8-10 行改为官方条文 + 标注来源 URL | 文件内每条规则可追溯到官方条文编号 | 断点 2 |
| P0-D | 补正文引用检查 | 新增 `check_inline_citation`，扫描 `main.tex` 的 `\cite` 与 bib 匹配 | 当前样例报 FAIL（cite=0），修复后转 PASS | 断点 3 |
| P0-E | 补 AI 披露三项检查 | 按 §7.3 新增 4 项 AI 检查；`render_ai_usage.py` 输出改 PDF 且文件名固定 | 样例能生成 `deliverables/AI工具使用详情.pdf` | 断点 3 |
| P0-F | 门禁与推进耦合 | `state.py advance` 内部调用 `gate.py`，FAIL 拒绝推进；`gate.py` 语义化退出码 | 人为删除一个产物后 advance 被拒绝 | 断点 1 |
| P0-G | 清理假失败 | 字数检查排除 appendix；禁用词扫描排除 inputs/_scratch；两脚本追溯率口径归一 | `validate.py` 在干净样例上 0 假失败 | §7.2 |

### P1 任务

| # | 任务 | 具体动作 | 验收标准 |
|---|---|---|---|
| P1-A | 参数单一真源 | 删 `loader.py` 的 DEFAULT_CONFIG；建 `schema.yaml`；9 个竞赛包改差量 profile | `grep -rn "min_pages" core/` 只剩 schema + profile + 消费点 |
| P1-B | 修产物契约冲突 | `guardrails_report.json` 按手拆分；`execution_report.json` 命名统一；catalog artifact 唯一性校验 | catalog 29 条声明 → 29 个唯一路径 |
| P1-C | 入口竞赛对齐 | `new_project.py` 的 choices 改为动态读取 `core/env/profiles/*.yaml` | 9 个 profile 全部可创建 |
| P1-D | 目录结构迁移 | 按 §6.3 调整 `PROJECT_DIRS`；`tables/` 删除；`_debug/` → `_scratch/`；新增 `deliverables/` | 新建项目目录与 §6.3 图一致 |
| P1-E | 样例产物归位 | `code/diag_*.py` → `_scratch/`；`work/run_*.py` 移出；`figures/` 补绘图脚本 | `code/` 只剩交付用代码 |
| P1-F | 补 Reviewer 手资源 | 建 `core/Reviewer/{knowledge,laws,templates}/` | 四手结构对称 |
| P1-G | README 数字回真 | 用实跑结果替换「当前状态」表，并注明生成命令与日期 | README 数字可复现 |
| P1-H | 修 15 处断链 | 优先补 cookbook 引用的 12 个代码模板，或删除对应引用 | 断链数归 0 |

### P2 任务

| # | 任务 | 具体动作 |
|---|---|---|
| P2-A | 仓库卫生 | `__pycache__` 加入 .gitignore 并清理；删除顶层 `_v.txt`；4 套审计文件归并为 `state.json` + `audit_chain.json` |
| P2-B | 编译链修复 | 统一走 `latexmk -xelatex`，修复 3 处未定义引用 |

> **清理安全提示**：本项目已是 git 仓库（7 次提交，当前有 9 项未提交变更）。任何批量删除前先 `git status` 确认，并优先用 `git mv` 归档而非直接删除。严禁使用 `find -name "_*" -delete` 这类会命中目录名的通配删除。

---

## 9. 关键设计决策（需要你拍板）

| 岔路口 | 选项 A | 选项 B | 建议 |
|---|---|---|---|
| **正文页数按哪个标准** | 官方 ≤20 页（宽松，可能显得单薄） | 某赛区流传的"含摘要参考文献 ≤25 页" | **A**。全国组委会规范效力最高，且第十二条明确"不符合本规范可能被取消评奖资格" |
| **min_words 定多少** | 13000（17 页 × 800） | 16000（20 页打满） | **A**。留 3 页给图表和参考文献，硬打满 20 页会挤压图表空间 |
| **OFFICIAL 层可否被覆盖** | 完全锁死 | 可覆盖但强制打印警告 | **A**。这类参数写错直接导致资格问题，不该留后门；要改请改 profile 源文件 |
| **是否做独立 CLI 编排器** | 做 | 不做，继续走「入口转发 + 状态外置 + 脚本门禁」 | **B**。你的目标是跨 runtime 通用，做 CLI 等于重复造轮子且绑定单一工具 |
| **样例项目如何处理** | 修复到达标（重写论文） | 归档为"已知不达标的历史样例" | 建议**先 B 后 A**：先归档避免误导，参数修完再重跑一次验证新基线可达 |
| **9 个竞赛包是否全保留** | 全保留 | 只留 cumcm/mcm，其余删除 | **先全保保留为 profile**，但只有 cumcm 做完整官方核验，其余标注 `verified: false` |

---

## 10. 验收标准

| 级别 | 出口条件（可验证） |
|---|---|
| **P0 完成** | ① `env_doctor` 输出与 §4.2 国赛参数表逐项一致；② `gate.py cumcm2024a all` 的页数/字数判定基于 20 页基线；③ 正文引用、AI 披露三项检查全部就位并能在样例上正确报 FAIL；④ 删除任一产物后 `state.py advance` 被拒绝 |
| **P1 完成** | ① `grep -rn "min_pages" core/` 仅剩 schema/profile/消费点三处；② catalog 29 条 artifact 路径全唯一；③ `new_project.py` 可创建全部 9 个竞赛；④ 新建项目目录结构与 §6.3 一致；⑤ 15 处断链归零 |
| **P2 完成** | ① `__pycache__` 不入版本库；② 审计文件归并为 2 套；③ `main.log` 显示完整 xelatex 编译链且 0 处未定义引用 |

---

## 11. 明确不做的事

1. **不做独立 CLI 编排器** —— 推理交给宿主 agent，脚本只管门禁与状态。
2. **不在诊断阶段改动任何既有文件** —— 本计划只做诊断与排期。
3. **不重写论文内容** —— P0/P1 只改机制与参数，样例论文的重写单独立项。
4. **不追求"全绿"** —— 门禁的价值在于报真问题。宁可 6 个真失败，不要 0 个假通过。
5. **不删除 9 个竞赛模板包** —— 改为 profile 化保留，避免资产流失。
6. **不把 AI 使用详情放进附录** —— 附录参与查重，AI 内容相似度极高。

---

## 12. 附：体检原始数据

### 12.1 `python core/tools/validate.py`

```
验证完成: 49 通过, 6 失败, 2 警告

失败项（阻塞交付）:
  - [L5] 禁用词: 发现禁用词: '最后' in projects\cumcm2024a\inputs\problem.md,
                 projects\cumcm2024a\work\ambiguity_prescreen.md
  - [L5] 正文列表: 正文包含列表环境(HARD): projects\cumcm2024a\paper\appendix.tex(itemize×0, enumerate×2)
  - [L6] 随机种子: 未设置随机种子
  - [L6] 论文结构: appendix.tex: 缺少参考文献;
                   appendix.tex: 字数不足(290字, 需>=18000, 其中中文252英文38);
                   appendix.tex: 图不足(0个, 需>=6);
                   appendix.tex: 表格不足(3表, 需>=4);
                   appendix.tex: 公式不足(0个, 需>=15)
  - [L4] 物理模型: 物理模型检查缺失: 时序因果
  - [L4] 数值追溯: 数值追溯比例=29.5%<90%(需≥90%)

警告项:
  - [L6] 文献年份: 近3年文献占比=20%<60%(WARN, 基准年2024): 2/10
  - [L6] 表格行数: appendix.tex: table#1有14行(>12); table#3有13行(>12);
                   main.tex: table#3有18行(>12,转longtable)
```

### 12.2 `python core/tools/gate.py cumcm2024a all`

```
  [FAIL] LaTeX 编译 - xelatex 失败: ! Extra alignment tab has been changed to \cr.
  [PASS] 代码可复现 - 27 个 .py 语法通过，all_results.json 可解析
  [PASS] PDF 产物 - 634 KB
  [FAIL] paper pages - 11 pages (< 25)
  [FAIL] page fill ratio - 实测 11/30 页 = 37% (< 80%)，正文偏空
  [FAIL] paper words - 5867 字符/词 (< 18000)
  [FAIL] paper tables - 3 tables (< 4)
  [PASS] paper figures - 6 figures (>= 6)
  [PASS] paper equations - 22 equations (>= 15)
  [PASS] paper references - 10 entries (>= 10)
  [FAIL] pdf compile chain - xelatex 仅运行 1 次，完整链需 >= 2 次;
                             存在 references.bib 但日志未见 bibtex/biber;
                             存在 3 处未定义引用
  （评审手 12 项全部 PASS）
------------------------------------------------------------
通过 79 / 硬失败 6 / 软失败 1
```

### 12.3 `python core/tools/validate_project.py --project projects/cumcm2024a`

```
汇总: 36 passed, 10 warnings, 9 hard errors

硬错误:
  - no undefined refs: main.log 含 undefined references/citations
  - traceability: 仅 78/154 可追溯 (51%)，违反铁律 W1
  - geometry criterion: 未发现点到线段距离模式
  - time bounds: T_MAX 未显式约束
  - pdf compile chain（同上）
  - page fill ratio: 实测 11/30 页 = 37% (< 80%)
  - paper pages: 11 pages (< 25)
  - paper words: 5867 字符/词 (< 18000)
  - paper tables: 3 tables (< 4)
```

### 12.4 状态机与时间戳

```
python core/tools/state.py cumcm2024a status
  项目: cumcm2024a   进度: 29/29   全部完成

state.json:  completed=29, failed=0, current=None
时间戳跨度:  2026-09-04T01:11:28Z  →  01:14:58Z   （210 秒 / 29 步）
同秒批量完成: 01:14:58 → 7 步   01:12:12 → 6 步   01:12:30 → 6 步
```

### 12.5 论文正文实测（`paper/main.tex`）

```
中文字符:        4459
figure:          6
table:           3
equation/align:  22
\cite:           0          ← 致命：bib 有 10 条，正文零引用
目录:            无（符合规范 ✅）
AI 声明关键词:   无          ← 致命：ai_usage_ledger.json 记了 3 条 AI 使用
```

### 12.6 参数散落统计

```
grep -rn "min_pages" core/  →  39 处
  core/env/loader.py          第 28 行（DEFAULT_CONFIG 硬编码副本）
  core/env/config.yaml        第 8 行
  core/env/README.md          3 处
  core/templates/latex/{cumcm,apmcm,mathorcup,renzhengbei,shuweibei}/config.yaml  各 1 处（数值全部相同）
  core/tools/{validate,validate_project,gate}.py   消费点
  core/{Modeler,Writer,Reviewer}/agents/*/SKILL.md 文档引用

grep -rn "18000" core/  →  17 处（同样的三处重复结构）

grep -rn "templates/latex" --include="*.py" core/  →  仅 doctor.py:143（只查目录存在）
  ⇒ 竞赛包 config.yaml 的 thresholds 是死参数，无任何代码消费
```

### 12.7 其他

```
pytest:              244 passed（README 声称 217 passed）
frontmatter:         29/29 均含 description ✅
知识库路径引用:       403 处引用 / 15 处断链（3.7%）
  - cookbook 引用的 12 个代码模板全部不存在
  - core/validators/modules/scholar_fetch.py 不存在（实际在 core/tools/）
catalog artifact:    29 条声明 / 28 个唯一路径（guardrails_report.json 冲突）
git:                 7 次提交，9 项未提交变更
脚手架目录:          inputs, inputs/external, work, output, code, figures, paper, paper/figures
实际项目目录:        _debug, code, figures, inputs, output, paper, tables, work
```

---

**下一步**：请确认 §9 的六个设计决策，确认后按 P0 → P1 → P2 顺序执行。若你希望调整优先级或范围，请指出具体条目。
