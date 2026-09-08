# Artifact Integrity Protocol — Three-Layer Non-Emptiness Gate

> **版本**: 1.0
> **日期**: 2026-09-08
> **审计对象**: `projects/p151-2024a/state/registry.json`（16 个 artifact）
> **核心原则**: 区分三层 — non-empty（有东西）/ structurally valid（结构对）/ semantically populated（内容有意义）。禁止用 `len(text) > N` 作为"有意义"的证明。

---

## 1. 设计动机

### 1.1 B0 实测问题

`projects/p151-2024a/state/registry.json` 中 16 个 artifact 的 payload 分布：

| payload 形态 | 数量 | artifact | 问题 |
|-------------|------|----------|------|
| `[]`（空列表） | 10 | P001, Q001, M001, A001, A002, E001, R001, F001, C001 | 完全空壳 |
| `["mc-topsis","mc-ahp","mc-pca"]`（方法卡ID列表） | 1 | D001 | 非空但无实质内容 |
| `["mc-topsis","mc-ahp"]`（方法卡ID列表） | 1 | D002 | 非空但无实质内容 |
| `["问题重述与分析"]` 等单字符串 | 5 | S001-S005 | 占位符级别的节标题 |

**所有 16 个 artifact 的 `provenance={}`、`validation={}`** — 无执行溯源、无验证记录。

### 1.2 为什么不能用 `len(payload) > 0`

- D001 的 `payload=["mc-topsis","mc-ahp","mc-pca"]` 长度为 3，但只是方法卡 ID 列表，不是文献检索结果
- S001 的 `payload=["问题重述与分析"]` 长度为 1，但只是节标题，不是论文正文
- `payload=[]` 但 `data={"card_id": "mc-topsis"}` 的 artifact（如 M001）有元数据但无模型定义
- 因此需要分层：**非空 ≠ 结构有效 ≠ 语义充实**

---

## 2. 三层 Gate 设计

### 2.1 架构总览

```
Artifact Input
     │
     ▼
┌─────────────────────────┐
│ Layer 1: Non-Empty      │  deterministic
│ (有东西吗？)             │  必须通过
└───────────┬─────────────┘
            │ PASS
            ▼
┌─────────────────────────┐
│ Layer 2: Structurally   │  deterministic
│ Valid (结构对吗？)       │  必须通过
└───────────┬─────────────┘
            │ PASS
            ▼
┌─────────────────────────┐
│ Layer 3: Semantically   │  semantic / LLM judge
│ Populated (内容有意义吗?)│  可选，高价值场景执行
└─────────────────────────┘
```

**执行规则**:
- Layer 1 FAIL → 整体 INVALID，不进入 Layer 2
- Layer 2 FAIL → 整体 FAIL，不进入 Layer 3
- Layer 3 仅在 Layer 1+2 全 PASS 后执行；Layer 3 FAIL → 整体 WEAK（不阻断，但标记为"需人工审查"）
- Layer 3 是可选的：benchmark 评分、论文数值引用等场景必须执行；普通状态推进可跳过

### 2.2 Artifact Type 分类

registry 中存在的 artifact type（v3.1 schema）：

| type | 说明 | 典型数量 | Layer 1 严格度 |
|------|------|---------|----------------|
| `problem` | 赛题 | 1 | 高 — 必须包含题面文本 |
| `question` | 子问题 | 1-N | 高 — 必须包含问题描述 |
| `model` | 数学模型 | 1-N | 高 — 必须包含目标/约束/变量 |
| `assumption` | 模型假设 | 2-N | 中 — 必须包含假设陈述 |
| `decision` | 决策记录 | 1-N | 中 — 必须包含决策内容 |
| `experiment` | 实验 | 1-N | 高 — 必须包含方法/参数/结果 |
| `result` | 实验结果 | 1-N | 高 — 必须包含数值结果 |
| `figure` | 图表 | 0-N | 中 — 必须包含图表数据或路径 |
| `claim` | 研究结论 | 1-N | 高 — 必须包含结论陈述+证据引用 |
| `paper_section` | 论文章节 | 5-N | 高 — 必须包含正文文本 |

---

## 3. Layer 1 — Non-Empty（deterministic）

### 3.1 通用检查（所有 type）

| 检查 ID | 检查项 | 通过标准 |
|---------|--------|---------|
| L1-00 | artifact 存在 | `artifact is not None` |
| L1-01 | payload 字段存在 | `"payload" in artifact` |
| L1-02 | payload 非空 | `payload is not None and payload != [] and payload != {} and payload != ""` |
| L1-03 | 非纯占位符 | payload 中的字符串不全是占位符模式（见 3.3） |

### 3.2 各 type 的必需内容

#### problem artifact
- **必需**: payload 包含 `text` 字段（题面原文，非空字符串，长度 ≥ 50 字符）
- **B0 实测**: P001 payload=[] → **FAIL**

#### question artifact
- **必需**: payload 包含 `sub_questions` 列表，列表非空，每个元素有 `id` 和 `text` 字段
- **B0 实测**: Q001 payload=[] → **FAIL**

#### model artifact
- **必需**: payload 包含以下字段（全部非空）:
  - `objective`: 目标函数/优化目标描述
  - `constraints`: 约束条件列表（非空）
  - `variables`: 变量定义列表（非空）
- **可选但加分**: `equations`（公式列表）、`parameters`（参数定义）
- **B0 实测**: M001 payload=[]，data 仅有 `{card_id, family, shortlist}` → **FAIL**

#### assumption artifact
- **必需**: payload 包含 `statement` 字段（假设陈述，非空字符串，长度 ≥ 10 字符）
- **可选**: `justification`（假设理由）、`relaxation_impact`（放松假设的影响）
- **B0 实测**: A001, A002 payload=[] → **FAIL**

#### decision artifact
- **必需**: payload 包含 `decision` 字段（决策内容），且 `alternatives` 列表非空
- **区分**: 方法卡 ID 列表（如 `["mc-topsis"]`）**不满足**此要求，必须是结构化决策
- **B0 实测**: D001 payload=["mc-topsis","mc-ahp","mc-pca"]（纯 ID 列表）→ **FAIL**；D002 同理 → **FAIL**

#### experiment artifact
- **必需**: payload 包含以下字段（全部非空）:
  - `method`: 实验方法描述
  - `parameters`: 参数配置（dict，非空）
  - `results`: 实验结果（dict 或 list，非空）
- **B0 实测**: E001 payload=[] → **FAIL**

#### result artifact
- **必需**: payload 包含 `values` 字段（数值结果，dict 非空，至少一个 key 的 value 是数值类型）
- **B0 实测**: R001 payload=[] → **FAIL**

#### figure artifact
- **必需**: payload 包含 `data`（图表数据，非空）或 `file_path`（图表文件路径，文件存在）
- **B0 实测**: F001 payload=[] → **FAIL**

#### claim artifact
- **必需**: payload 包含以下字段（全部非空）:
  - `claim`: 结论陈述（非空字符串，长度 ≥ 10 字符）
  - `evidence_ref`: 证据引用列表（非空，每个元素指向已注册的 result/experiment artifact）
- **B0 实测**: C001 payload=[]，data 仅有 `{statement, claim_type, experiment_refs}` → **FAIL**

#### paper_section artifact
- **必需**: payload 包含 `content` 字段（正文文本，非空字符串，长度 ≥ 200 字符）
- **禁止**: payload 仅为节标题（如 `["问题重述与分析"]`）
- **B0 实测**: S001-S005 payload=["节标题"]（单字符串，长度 < 200）→ **FAIL**

### 3.3 占位符模式黑名单

以下字符串模式判定为占位符，不计入"非空":

| 模式 | 示例 | 匹配规则 |
|------|------|---------|
| 节标题 | `"问题重述与分析"`, `"模型建立"`, `"结果与分析"` | 精确匹配已知节标题列表 |
| 模板默认 | `"TODO"`, `"TBD"`, `"待填写"`, `"placeholder"` | 大小写不敏感包含匹配 |
| 方法卡 ID | `"mc-topsis"`, `"mc-ahp"`, `"mc-pca"` | 匹配 `^mc-[a-z-]+$` 正则 |
| 空结论 | `"Q001 结论"`, `"结论"` | 匹配 `^Q\d+ 结论$` 或 `"结论"` |
| 空标题 | `"赛题"`, `"Q001"`, `"Q001 实验"`, `"Q001 结果"` | 匹配已知空标题列表 |

---

## 4. Layer 2 — Structurally Valid（deterministic）

### 4.1 通用检查（所有 type）

| 检查 ID | 检查项 | 通过标准 |
|---------|--------|---------|
| L2-00 | JSON 可解析 | artifact 整体是合法 JSON 对象 |
| L2-01 | schema_version 存在 | `"schema_version" in artifact` 且值为 `"3.1"` |
| L2-02 | artifact_id 格式正确 | 匹配 `^[A-Z]\d{3}$`（如 P001, Q001, M001） |
| L2-03 | type 合法 | `type` 在已知 type 列表中（见 2.2） |
| L2-04 | status 合法 | `status in ("active", "draft", "superseded", "invalidated", "deprecated")` |
| L2-05 | created_at 可解析 | ISO 8601 格式 |
| L2-06 | lifecycle_history 非空 | 至少包含 `"created"` 事件 |
| L2-07 | 必需字段类型正确 | 按各 type schema 检查字段类型 |

### 4.2 各 type 的 schema 必需字段

#### problem
```json
{
  "schema_version": "3.1",
  "artifact_id": "P001",
  "type": "problem",
  "status": "active",
  "title": "string (non-empty)",
  "created_by": "string (non-empty)",
  "created_at": "ISO8601",
  "payload": {
    "text": "string (≥50 chars)",
    "source": "string (optional)",
    "competition": "string (optional)"
  }
}
```

#### question
```json
{
  "payload": {
    "sub_questions": [
      {"id": "Q001", "text": "string (≥10 chars)", "depends_on": ["string"]}
    ],
    "original_text": "string (optional)"
  }
}
```

#### model
```json
{
  "payload": {
    "objective": "string (non-empty)",
    "constraints": [{"expression": "string", "description": "string"}],
    "variables": [{"name": "string", "domain": "string", "description": "string"}],
    "equations": [{"latex": "string", "description": "string"}],
    "parameters": [{"name": "string", "value": "number|string", "unit": "string"}]
  }
}
```

#### assumption
```json
{
  "payload": {
    "statement": "string (≥10 chars)",
    "justification": "string (optional)",
    "relaxation_impact": "string (optional)",
    "testable": "boolean (optional)"
  }
}
```

#### decision
```json
{
  "payload": {
    "decision": "string (non-empty)",
    "alternatives": [{"id": "string", "score": "number", "reason": "string"}],
    "criteria": ["string"],
    "evidence_ids": ["string (non-empty list)"],
    "reasoning": "string (non-empty, not template default)"
  }
}
```

#### experiment
```json
{
  "payload": {
    "method": "string (non-empty)",
    "parameters": {"key": "value (non-empty dict)"},
    "results": {"metric_name": "number|string (non-empty)"},
    "baseline": "string (optional)",
    "repetitions": "integer (optional, ≥1)"
  }
}
```

#### result
```json
{
  "payload": {
    "values": {"metric_name": "number (at least one numeric value)"},
    "uncertainty": {"metric_name": "number (optional)"},
    "raw_data_path": "string (optional, file exists if provided)"
  }
}
```

#### figure
```json
{
  "payload": {
    "data": {"x": [...], "y": [...]} ,
    "file_path": "string (file exists if provided)",
    "caption": "string (optional)",
    "figure_type": "string (optional: bar/line/scatter/table)"
  }
}
```

#### claim
```json
{
  "payload": {
    "claim": "string (≥10 chars)",
    "claim_type": "string (comparative/quantitative/qualitative)",
    "evidence_ref": ["string (references to registered result/experiment artifacts)"],
    "confidence": "number (0.0-1.0, optional)",
    "limitations": "string (optional)"
  }
}
```

#### paper_section
```json
{
  "payload": {
    "section_name": "string (non-empty)",
    "content": "string (≥200 chars, actual prose)",
    "word_count": "integer (≥50, optional)",
    "citations": ["string (optional)"]
  }
}
```

### 4.3 引用一致性检查

| 检查 ID | 检查项 | 通过标准 |
|---------|--------|---------|
| L2-08 | depends_on 引用存在 | artifact 的 `depends_on` 列表中的每个 ID 都在 registry 中存在 |
| L2-09 | relations 引用存在 | artifact 的 `relations` 列表中的 from/to ID 都在 registry 中存在 |
| L2-10 | model variable 引用一致 | model payload 中 constraints 引用的 variable 都在 variables 列表中定义 |
| L2-11 | claim evidence_ref 引用存在 | claim payload.evidence_ref 中的每个 ID 都指向已注册的 result/experiment artifact |
| L2-12 | experiment result 绑定 | experiment 的 relations 中存在 `produces` 关系指向 result artifact |
| L2-13 | result claim 绑定 | result 的 relations 中存在 `supports` 关系指向 claim artifact |

---

## 5. Layer 3 — Semantically Populated（semantic / LLM judge）

### 5.1 使用条件

- **前置**: Layer 1 + Layer 2 全部 PASS
- **触发场景**:
  - benchmark 评分前（必须）
  - 论文数值引用前（必须）
  - 模型选型决策前（必须）
  - 普通状态推进（可选，跳过则标记为 `semantic_check: "skipped"`）

### 5.2 检查项

#### S3-01: 内容不是模板默认值的简单填充
- **方法**: 对比 artifact payload 内容与已知模板默认值库
- **模板默认值库**:
  - model objective: `"最大化目标函数"`, `"最小化误差"`（无具体问题指向）
  - assumption statement: `"数据服从正态分布"`, `"变量之间相互独立"`（无具体问题指向）
  - claim: `"该方法有效"`, `"结果表明模型可行"`（无具体数值支撑）
- **通过标准**: payload 中不包含纯模板默认值，或模板默认值已被具体问题上下文修改

#### S3-02: 变量/约束/目标与题面相关
- **方法**: LLM judge 输入题面文本 + model payload，判断 model 的 objective/variables/constraints 是否与题面描述的物理/数学问题相关
- **Prompt 模板**:
  ```
  题面: {problem_text}
  模型定义:
  - 目标: {objective}
  - 变量: {variables}
  - 约束: {constraints}
  
  请判断该模型定义是否与题面描述的问题直接相关。
  评分: 0(完全不相关) - 10(高度相关)
  阈值: ≥6 为 PASS
  输出格式: {"score": N, "reason": "..."}
  ```
- **通过标准**: score ≥ 6

#### S3-03: 实验结果与方法一致
- **方法**: LLM judge 输入 experiment method + result values，判断结果是否是该方法可能产出的
- **通过标准**: 结果数值范围合理，与方法描述的输出类型一致

#### S3-04: 结论有数值支撑
- **方法**: 检查 claim.claim 中是否包含具体数值（数字/百分比/比较结果），且这些数值可在 result.values 中找到
- **通过标准**: claim 中至少包含 1 个具体数值，且该数值在 result 中存在

### 5.3 Layer 3 输出

```json
{
  "layer": 3,
  "verdict": "PASS | WEAK | FAIL",
  "checks": [
    {"id": "S3-01", "verdict": "PASS", "detail": "..."},
    {"id": "S3-02", "verdict": "PASS", "score": 8, "detail": "..."},
    {"id": "S3-03", "verdict": "WEAK", "detail": "..."},
    {"id": "S3-04", "verdict": "FAIL", "detail": "claim 中无数值支撑"}
  ],
  "overall": "WEAK (Layer 1+2 PASS, Layer 3 partial)"
}
```

### 5.4 限制与免责

- Layer 3 依赖 LLM judge，**不是 deterministic**，结果可能因模型/温度/版本而异
- Layer 3 FAIL 不阻断流程（标记为 WEAK），但高价值场景（benchmark 评分、论文引用）必须人工复核
- Layer 3 的 LLM judge 本身需要被 audit：记录 judge 的 model_provider、prompt_hash、latency，防止 judge 本身也是空执行
- **禁止**用 Layer 3 的 PASS 来弥补 Layer 1/2 的 FAIL — Layer 1/2 是硬门禁

---

## 6. 伪代码 / 函数签名

### 6.1 主入口

```python
def check_artifact_integrity(artifact: dict, registry: dict,
                              problem_text: str = "",
                              run_layer3: bool = False) -> dict:
    """
    三层 Artifact Integrity Gate。
    
    Args:
        artifact: 单个 artifact dict（来自 registry.artifacts[id]）
        registry: 完整 registry dict（用于引用一致性检查）
        problem_text: 题面文本（Layer 3 需要）
        run_layer3: 是否执行 Layer 3（默认 False）
    
    Returns:
        {
            "artifact_id": str,
            "type": str,
            "overall": "PASS|FAIL|INVALID|WEAK",
            "layer1": {"verdict": ..., "checks": [...]},
            "layer2": {"verdict": ..., "checks": [...]},
            "layer3": {"verdict": ..., "checks": [...]} | None
        }
    """
    l1 = _layer1_non_empty(artifact)
    if l1["verdict"] != "PASS":
        return _wrap(artifact, "INVALID", l1, None, None)
    
    l2 = _layer2_structurally_valid(artifact, registry)
    if l2["verdict"] != "PASS":
        return _wrap(artifact, "FAIL", l1, l2, None)
    
    if not run_layer3:
        return _wrap(artifact, "PASS", l1, l2, None)
    
    l3 = _layer3_semantically_populated(artifact, problem_text)
    overall = "PASS" if l3["verdict"] == "PASS" else "WEAK"
    return _wrap(artifact, overall, l1, l2, l3)
```

### 6.2 Layer 1 实现逻辑

```python
def _layer1_non_empty(artifact: dict) -> dict:
    checks = []
    atype = artifact.get("type", "")
    payload = artifact.get("payload")
    
    # L1-00 ~ L1-02: 通用非空
    checks.append(_check("L1-00", "artifact exists", artifact is not None))
    checks.append(_check("L1-01", "payload field exists", "payload" in artifact))
    checks.append(_check("L1-02", "payload non-empty",
                          payload is not None and payload != [] and payload != {}))
    
    # L1-03: 非纯占位符
    checks.append(_check("L1-03", "not pure placeholder",
                          not _is_placeholder_payload(payload)))
    
    # 按 type 检查必需内容
    type_checks = _TYPE_REQUIRED_CHECKS.get(atype, [])
    for check_fn in type_checks:
        checks.append(check_fn(artifact))
    
    verdict = "PASS" if all(c["pass"] for c in checks) else "FAIL"
    return {"verdict": verdict, "checks": checks}
```

### 6.3 Layer 2 实现逻辑

```python
def _layer2_structurally_valid(artifact: dict, registry: dict) -> dict:
    checks = []
    
    # L2-00 ~ L2-07: 通用结构
    checks.append(_check("L2-00", "valid JSON", isinstance(artifact, dict)))
    checks.append(_check("L2-01", "schema_version=3.1",
                          artifact.get("schema_version") == "3.1"))
    checks.append(_check("L2-02", "artifact_id format",
                          bool(re.match(r'^[A-Z]\d{3}$', artifact.get("artifact_id", "")))))
    checks.append(_check("L2-03", "valid type",
                          artifact.get("type") in _VALID_TYPES))
    checks.append(_check("L2-04", "valid status",
                          artifact.get("status") in _VALID_STATUSES))
    checks.append(_check("L2-05", "created_at parseable",
                          _parse_iso(artifact.get("created_at", "")) is not None))
    checks.append(_check("L2-06", "lifecycle_history non-empty",
                          len(artifact.get("lifecycle_history", [])) > 0))
    
    # L2-07: 字段类型正确（按 type schema）
    checks.extend(_check_field_types(artifact))
    
    # L2-08 ~ L2-13: 引用一致性
    checks.extend(_check_reference_consistency(artifact, registry))
    
    verdict = "PASS" if all(c["pass"] for c in checks) else "FAIL"
    return {"verdict": verdict, "checks": checks}
```

### 6.4 批量检查

```python
def check_registry_integrity(registry_path: str, problem_text: str = "",
                              run_layer3: bool = False) -> dict:
    """
    检查整个 registry 中所有 artifact 的完整性。
    
    Returns:
        {
            "registry_path": str,
            "total_artifacts": int,
            "summary": {"PASS": N, "FAIL": N, "INVALID": N, "WEAK": N},
            "artifacts": [check_artifact_integrity(a, ...) for a in artifacts],
            "overall": "PASS|FAIL|INVALID"  (≥80% PASS 才为 PASS)
        }
    """
    registry = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    artifacts = registry.get("artifacts", {})
    
    results = []
    for aid, art in artifacts.items():
        results.append(check_artifact_integrity(art, registry, problem_text, run_layer3))
    
    summary = Counter(r["overall"] for r in results)
    pass_rate = summary.get("PASS", 0) / len(results) if results else 0
    overall = "PASS" if pass_rate >= 0.8 else "FAIL"
    if any(r["overall"] == "INVALID" for r in results):
        overall = "INVALID"
    
    return {
        "registry_path": registry_path,
        "total_artifacts": len(results),
        "summary": dict(summary),
        "pass_rate": round(pass_rate, 3),
        "artifacts": results,
        "overall": overall,
    }
```

---

## 7. B0 实测结果（Layer 1+2）

对 `projects/p151-2024a/state/registry.json` 的 16 个 artifact 执行 Layer 1+2：

| artifact | type | Layer 1 | Layer 2 | overall | 主要失败原因 |
|----------|------|---------|---------|---------|-------------|
| P001 | problem | FAIL | — | INVALID | payload=[]，无题面文本 |
| Q001 | question | FAIL | — | INVALID | payload=[]，无 sub_questions |
| D001 | decision | FAIL | — | INVALID | payload=方法卡ID列表，非结构化决策 |
| M001 | model | FAIL | — | INVALID | payload=[]，无 objective/constraints/variables |
| A001 | assumption | FAIL | — | INVALID | payload=[]，无 statement |
| A002 | assumption | FAIL | — | INVALID | payload=[]，无 statement |
| D002 | decision | FAIL | — | INVALID | payload=方法卡ID列表 |
| E001 | experiment | FAIL | — | INVALID | payload=[]，无 method/parameters/results |
| R001 | result | FAIL | — | INVALID | payload=[]，无数值结果 |
| F001 | figure | FAIL | — | INVALID | payload=[]，无图表数据 |
| C001 | claim | FAIL | — | INVALID | payload=[]，无 claim/evidence_ref |
| S001 | paper_section | FAIL | — | INVALID | payload=节标题，无正文（<200 chars） |
| S002 | paper_section | FAIL | — | INVALID | 同上 |
| S003 | paper_section | FAIL | — | INVALID | 同上 |
| S004 | paper_section | FAIL | — | INVALID | 同上 |
| S005 | paper_section | FAIL | — | INVALID | 同上 |

**汇总**: 16/16 INVALID（Layer 1 全 FAIL），pass_rate = 0.0，overall = INVALID。

**结论**: B0 registry 中没有任何一个 artifact 通过最基本的 non-empty 检查。这不是"部分空"，而是"全空"。

---

## 8. 与 Execution Authenticity Gate 的关系

| Gate | 检查对象 | 层级 | 关系 |
|------|---------|------|------|
| Execution Authenticity Gate | RunRecord + 执行痕迹 | 运行级 | EAG-10 调用本 Gate 的 Layer 1 |
| Artifact Integrity Gate | 单个 artifact / registry | 产物级 | 本 Gate 独立运行，也可被 EAG 调用 |

**执行顺序**:
1. 先跑 Execution Authenticity Gate → INVALID 则直接拒绝，不检查 artifact
2. EAG PASS/FAIL 后，对 registry 中所有 artifact 跑 Artifact Integrity Gate Layer 1+2
3. 高价值场景跑 Layer 3

**组合判定**:
- EAG INVALID → 整体 INVALID（不看 artifact）
- EAG PASS + Artifact Integrity INVALID → 整体 INVALID（执行了但产出空壳）
- EAG PASS + Artifact Integrity PASS → 整体 PASS
- EAG FAIL + Artifact Integrity PASS → 整体 FAIL（执行有问题但产物可用，需修复执行配置）

---

## 9. 证据索引

| 证据 | 路径 |
|------|------|
| B0 registry (16 artifacts) | `projects/p151-2024a/state/registry.json` |
| DefaultNodeExecutor (空 payload 来源) | `core/runtime/execution/handlers.py` |
| ArtifactRegistry create | `core/runtime/artifacts/registry.py` |
| v3.1 artifact schema | `core/schemas/` (如存在) |
| Execution Authenticity Protocol | `research/P15/measurement_recovery/EXECUTION_AUTHENTICITY_PROTOCOL.md` |
| Gate 实现 | `research/P15/measurement_recovery/execution_gate.py` |
