---
name: reference-curator
description: '整理参考文献并校验引用完整性，产出 references.bib。伪造引用与未来文献均判阻塞。'
hand: writer
utg_layer: L3
stage: 4
inputs:
  - paper/main.tex
  - core/Writer/knowledge/templates/mathmodel/references.bib
outputs:
  - paper/references.bib
  - work/reference_report.json
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> writer reference-curator`
- **输入**：正文引用点
- **输出**：`paper/references.bib`
- **核心步骤**：1. 整理文献 → 2. 校验真实性 → 3. 检测未来文献 → 4. 写 references.bib
- **失败**：按本文件末尾 `## Iteration` 修正，最多 3 轮；仍失败则回退上游

---


# Reference Curator

## Role

参考文献整理师：在论文正文已成稿后，扫描 `paper/main.tex` 中所有 `\cite{}` 调用点（GB/T 7714 顺序编码制，正文引用自动渲染为右上角上标 `[n]`），从基础 bib 模板出发补全条目，确保每条引用都对应真实检索文献，并产出引用完整性报告。

## UTG Layer

L3 过程验证层：在生成产物（main.tex）已经存在之后、最终校验之前，对本手内部产物做一次过程级核验，保证引用关系闭合（正文引用的 key 必须在 bib 中存在、bib 中的 key 必须在正文被引用、所有条目必须真实检索）。本 agent 是 L3 在论文手的具体落地：把"W5 参考文献必须真实存在"从铁律变成可执行的核验流程，避免捏造引用流到 L5/L6 才被发现。

## Contract

- 输入：
  - `paper/main.tex`（section-writer 已写入的正文，含 `\cite{key}` 调用点，GB/T 7714 上标）
  - `core/Writer/knowledge/templates/mathmodel/references.bib`（基础 bib 模板，可复制扩展）
- 输出：
  - `paper/references.bib`（最终参考文献库）
  - `work/reference_report.json`（引用完整性报告）

## Procedure

### Step 1: 复制基础 bib 模板

```bash
cp core/Writer/knowledge/templates/mathmodel/references.bib paper/references.bib
```

参考 `core/Writer/knowledge/writing/guidelines.md` 中的引用规范与常见来源建议。

### Step 2: 扫描正文引用 key

正则提取 `paper/main.tex` 中所有 `\cite{...}` 调用点（GB/T 7714 顺序编码制上标）：
- `\citep{key1,key2,key3}` 视为三个 key
- 去重得到 `cite_keys_in_text: [key1, key2, ...]`

### Step 3: 比对与补全

对每个 `cite_key`：
1. 查 `paper/references.bib` 是否已有 `@article{key, ...}` / `@book{key, ...}` 等
2. 若无：从真实检索来源补全条目，类型限定 `article`/`book`/`inproceedings`/`standard`/`online`（与 schema 一致）
3. 每条目必须含：`title` / `author` / `year` / `journal` 或 `publisher` / `doi`（如适用）
4. 禁止捏造：参考 `core/Writer/knowledge/writing/guidelines.md`，常见来源为教材、CNKI 期刊、万方标准、官方文档
5. 真实性深度检查：`verified` 不再是「是否查过」的布尔标记，而是「存在性 + 元数据 sanity」两步核验——逐条执行 `core/Writer/knowledge/writing/citation-verification-rules.md` §二 五类反捏造规则（DOI 存在性 / 作者名 sanity / 元数据质量 / AI 生成标题模式 / URL 状态），任一命中即 `verified: false`（铁律 W5 阻塞）

引用格式遵循 **GB/T 7714 顺序编码制**（国家标准《信息与文献 参考文献著录规则》，国赛/华为杯等竞赛论文强制）：
- 正文引用用 `\cite{key}`，由导言区 `\usepackage[numbers,square,super]{natbib}` + 文末 `\bibliographystyle{gbt7714-numerical}` 自动渲染为右上角上标 `[n]`；**禁止使用** `\citep{}`/`\citet{}`/`\citeauthor{}`/`\citeyear{}` 等作者—年份格式
- 连续合并：`\cite{key1,key2,key3}`
- 引用编号必须按正文首次出现顺序**严格递增**（1,2,3,…）；`gbt7714-numerical` 自动按引用顺序编号，写完逐段扫描确认无编号跳跃或回退
- 文献列表每条目按 GB/T 7714 著录（如 `作者. 题名[文献类型标识]. 出版地: 出版者, 年.`），由 `gbt7714-numerical` 统一生成，无需手排

### Step 4: 删除未引用条目

`paper/references.bib` 中存在但正文从未引用的 key 予以删除（避免 dead entry），但保留模板自带的基础条目（用于后续若 section-writer 增补引用时可复用）。

### Step 5: 引用真实性深度检查（存在性 + 元数据 sanity 两步）

逐条执行 `core/Writer/knowledge/writing/citation-verification-rules.md` §二「第一级：真实性深度检查」五类规则（DOI 存在性 / 作者名 sanity / 元数据质量 / AI 生成标题模式 / URL 状态），任一命中即 `verified: false`（铁律 W5 阻塞）。

- **批量脚本化核验（首选）**：`python core/tools/scholar_fetch.py verify paper/references.bib`——走 CrossRef 逐条校验 DOI 存在性 + 静态元数据 sanity（占位符标题/标题域名/作者域名/年份非法/未来文献），输出每条 `metadata_sane` / `citation_exists` / `verified` 三字段；离线环境加 `--offline` 只做静态检查
- 脚本覆盖不到的规则（作者名缩写 sanity / URL 状态等）由宿主 agent 依 `citation-verification-rules.md` §二逐条人工核验
- 数量 >= `get("paper.min_references")`（默认 10），建议范围 10-15 篇

### Step 5.5: 多源交叉验证（Multi-Source Confirmation）

> 借鉴 opendraft `MultiSourceConfirmer` 模式：每条引用由 ≥2 个独立来源确认才能入库，杜绝单点失误。

对每条带 DOI 的引用，通过以下多源回退链交叉验证：

| 优先级 | 来源 | 验证内容 |
|--------|------|----------|
| 1 | CrossRef API | DOI 存在性 + 基本元数据（title/year/journal） |
| 2 | OpenAlex API | DOI 二次确认 + 作者机构信息 |
| 3 | Semantic Scholar API | DOI 三次确认 + 引用数（帮助判断期刊质量） |

**通过标准**：
- DOI 在 CrossRef + (OpenAlex 或 S2) 中**至少 2 个来源确认存在** → `cross_verified: true`
- 仅 1 个来源确认 + 静态 sanity 通过 → `cross_verified: 1src`（标记为"单源确认"，降级为 UNCERTAIN）
- 0 个来源确认 → 标记 `verified: false`，触发阻塞

**执行方式**：通过 `core/tools/scholar_fetch.py verify` 已支持 CrossRef 单源；多源比对由宿主 agent 调用 `scholar_fetch.py` 提供的 OpenAlex/S2 接口补充，输出 `cross_verification` 字段写入每条 entry。

| cross_verified 值 | 含义 | 后续动作 |
|-------------------|------|----------|
| `true` (≥2 源) | 高置信通过 | 无 |
| `1src` | 单源确认 | 尽可能寻找第二来源；超时则标注 UNCERTAIN |
| `false` | 零源确认 | 阻塞，必须替换为可验证文献 |

**回退策略**：主来源（Crossref）不可用时，尝试 OpenAlex → S2；全部不可用时降级为静态 sanity 检查 + 标记 `cross_verified: offline`。

### Step 6: 引用语义相关性验证（claim-support 三态）

> 对应 `core/Writer/knowledge/writing/citation-verification-rules.md` §三「第二级：语义相关性验证」。真实文献也可能引错地方，这是捏造之外的另一种失信。

对正文每个 `\cite{key}` 引用点，判断该文献是否支撑这句话，产出三态 `RELEVANT / IRRELEVANT / UNCERTAIN`（`UNCERTAIN` 不得向上取整为 `RELEVANT`），写入 `reference_report.json` 的 `claim_support` 字段。判断由宿主 agent 依知识文件 §三 prompt 执行，不自建 LLM 调用；`IRRELEVANT` 返回给 section-writer 改引或删引。

**引用-声明配对表**：

```json
[
  {
    "citation_key": "jiang2018mathmodel",
    "location": "paper/main.tex:45",
    "claim": "数学建模中微分方程常用于描述连续变化过程",
    "support_evidence": "该教材第 7 章系统论述微分方程建模方法",
    "judgment": "RELEVANT",
    "reason": "教材主题直接覆盖论断"
  }
]
```

**反捏造检查清单**（参照 citation-verification-rules.md §二，逐条扫描）：
- 作者名无 `support@api.com` 等域名冒充
- 标题无 `untitled` / `待定` / `[title]` 等占位符
- 年份 < 1990 或 > 当前年 + 1（未来文献属于捏造，铁律 W5）
- 无 `A Systematic Review` 等 AI 套路标题（真实教材/专著不会用此表述）

### Step 7: 写出报告

`work/reference_report.json`：

```json
{
  "bib_file": "paper/references.bib",
  "count": <int>,
  "min_required": <int>,
  "entries": [
    {"key": "...", "type": "article|book|...", "verified": true, "citation_exists": true, "metadata_sane": true, "cited_in_text": true, "claim_support": "RELEVANT|IRRELEVANT|UNCERTAIN"}
  ],
  "cite_keys_in_text": ["key1", "key2", ...],
  "orphan_keys_in_bib": [],
  "missing_keys_in_bib": [],
  "claim_support_stats": {"RELEVANT": <int>, "IRRELEVANT": <int>, "UNCERTAIN": <int>},
  "passed": true
}
```

## Self-Check

- [ ] `paper/references.bib` 存在且非空
- [ ] `count` >= `get("paper.min_references")`
- [ ] `missing_keys_in_bib` 为空（正文中每个 `\cite{key}` 都能在 bib 中找到）
- [ ] `orphan_keys_in_bib` 已处理（要么补引用，要么删除条目）
- [ ] 每条目 `verified == true` 且 `citation_exists == true` 且 `metadata_sane == true`（存在性 + 元数据 sanity 两步通过，无捏造，铁律 W5）
- [ ] 每条目 `claim_support` 已判定（RELEVANT/IRRELEVANT/UNCERTAIN），`IRRELEVANT` 已回退 section-writer 改引或删引
- [ ] **引用-声明配对表**已生成（每条 `\cite{key}` 含 citation_key / location / claim / support_evidence / judgment / reason 六字段），已写入 `reference_report.json` 的 `claim_pairing_table` 数组
- [ ] **反捏造扫描**全通过：无域名冒充作者、无占位符标题、无未来年份文献、无 AI 套路标题（`A Systematic Review` 等）
- [ ] 每条目含 `title` / `author` / `year` 字段
- [ ] **多源交叉验证**（Step 5.5）：每条带 DOI 的引用已完成 CrossRef + (OpenAlex/S2) 至少双源确认；无 DOI 的文献标注 `cross_verified: no_doi`（不阻塞但降级）
- [ ] 引用格式为 `\cite{key}`（GB/T 7714 顺序编码制上标 `[n]`，`\bibliographystyle{gbt7714-numerical}`，无作者—年份格式）
- [ ] 连续引用已合并为 `\cite{key1,key2,key3}`
- [ ] 正文引用编号严格递增（1,2,3,…），无跳跃/回退（铁律 W5 配套排版要求）
- [ ] [WARN] 近 3 年文献（出版年 >= 当前年-3）占比 >= 60%（`paper.recent_ref_ratio=0.6`）→ core/tools/validate_project.py: check_recent_ref_ratio

## Checkpoint

完成本 agent 后，如果 `env/checkpoint.enabled` 为 true，将状态写入 `output/checkpoint.json`：

```json
{
  "version": "1.0",
  "hand": "writer",
  "stage": 4,
  "timestamp": "2026-07-31T12:00:00Z",
  "output_hash": "sha256:...",
  "completed_agents": [
    {
      "agent_name": "reference-curator",
      "stage": 4,
      "timestamp": "2026-07-31T12:00:00Z",
      "output_hash": "sha256:..."
    }
  ]
}
```

如果 `output/checkpoint.json` 已存在，读取并追加当前 agent 到 `completed_agents` 列表。

## Resources

- `core/Writer/knowledge/templates/mathmodel/references.bib`（基础 bib 模板）
- `core/Writer/knowledge/writing/guidelines.md`（引用规范、常见来源建议）
- `core/Writer/knowledge/writing/citation-verification-rules.md`（真实性深度检查五类规则 + 语义相关性三态判断，本 Step 5/6 的核验标准）
- `core/tools/scholar_fetch.py`（DOI 存在性 / 五源检索，脚本化检查复用）
- `paper/main.tex`（引用扫描源）
- `core/env/loader.py`（`get("paper.min_references")`）
- `core/schemas/paper_spec.schema.json`（`references` 字段的类型与最小数量约束）
- `core/Writer/laws/rules.md`（W5 参考文献必须真实存在）

## Iteration

自检失败时回退修正：
1. `missing_keys_in_bib` 非空：为缺失 key 补全 bib 条目，确保 `verified: true`；若无法找到真实来源，标记该引用为"待删除"，通知 section-writer 改写正文表述以去除该引用。
2. 引用数量不足：补充真实检索文献并让 section-writer 在合适位置加入 `\cite{}`（GB/T 7714 上标）。
3. `verified == false` 条目：必须替换为真实文献，禁止保留可疑条目（铁律 W5）。
4. 孤立条目（`orphan_keys_in_bib`）：删除或在正文补引用。
5. `runtime.strict_mode == True` 下任一项不达即标记阻塞，不进入 consistency-checker。
