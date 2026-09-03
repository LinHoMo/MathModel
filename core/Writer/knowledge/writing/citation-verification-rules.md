# 引用真实性验证规则（citation-verification-rules.md）

> 来源：OpenDraft `citation_validator.py` + `citation_claim_verifier.py`（竞争分析 B-1/B-2）。
> 目的：把铁律 W5「参考文献必须真实存在不可捏造」从「布尔标记 verified」升级为「存在性 + 元数据 sanity + 语义相关性」三级核验。
> 原则：可脚本化的静态规则交给脚本（`core/tools/scholar_fetch.py` 已有 CrossRef/OpenAlex/DBLP/Semantic Scholar/AMiner 五源）；需判断的语义相关性由宿主 agent 依本文件 §三 的 prompt 执行。

---

## 一、两级核验框架

引用验证拆成两个正交问题（OpenDraft 的核心洞察）：

1. **「这篇文献真实吗？」** → 存在性检查（DOI 是否注册、多源索引、元数据 sanity）
2. **「这篇文献支撑这句话吗？」** → 语义相关性判断

缺失任何一级，都会产生两类失信：捏造引用（第 1 级漏）与「真文献引错地方」（第 2 级漏）。

---

## 二、第一级：真实性深度检查（可脚本化，五类反捏造规则）

对每条 bib 条目逐项核对，命中即判 `verified: false`（铁律 W5 阻塞）：

### 1. DOI 存在性
- 调 CrossRef `https://api.crossref.org/works/{doi}`，或复用 `core/tools/scholar_fetch.py` 的 `crossref_bibtex_by_doi`
- 200 = 存在；404 = 不存在（捏造）；网络错误 = 标记 unknown，重试 3 次（429/5xx 指数退避）

### 2. 作者名 sanity（5 条）
- 重复缩写（如 `N. C. A. C. B. S. C. A.`）
- 同一姓与名（如 `Smith, Smith`）
- 纯缩写无全名
- 连续同字母（如 `AAAA BBBB`）
- 域名当作者（如 `support@api.com`）

### 3. 元数据质量
- 标题是域名
- 作者 == 标题
- URL 含错误关键词（`403` / `404` / `500` / `503`）
- 年份越界（< 1990 或 > 当前年+1）
- 占位符标题（`untitled` / `n/a` / `[title]` / `待定` …）

### 4. 通用 AI 生成标题模式
- 标题以 `A Systematic Review` / `A Comprehensive Study` / `An Overview` / `A Survey` 结尾（AI 批量生成的高频套路标题，竞赛论文中出现即可疑）

### 5. URL HTTP 状态
- HEAD 失败回退 GET；≥400 判 critical

---

## 三、第二级：语义相关性验证（需宿主 agent 判断）

对每个 `\cite{key}` 在正文中的引用点，判断该文献是否支撑这句话。产出三态：

| 判定 | 含义 | 处置 |
|---|---|---|
| `RELEVANT` | 文献主题 / 结论与论断一致 | 通过 |
| `IRRELEVANT` | 文献真实但与论断无关（引错地方） | 退回 section-writer 改引或删引 |
| `UNCERTAIN` | 缺摘要 / 论断模糊，无法判断 | **如实报 uncertain，禁止向上取整为 RELEVANT**（OpenDraft 强调 uncertain 是一等公民） |

**判断 prompt（宿主 agent 执行，不自建 LLM 调用）**：

```text
对下面这条 citation，判断它是否支撑对应的 claim（论断）：

- claim（正文论断）：<填入该 \cite 所在句的语义主干>
- citation（文献）：<title> / <摘要或来源描述>

输出：RELEVANT / IRRELEVANT / UNCERTAIN 三选一 + 一句理由（≤20 字）。

规则：
- 缺摘要或论断模糊 → UNCERTAIN，不要猜
- 若引用「错误部分」（wrong_part）不是 claim 原文真实出现的关键词，判定降级为 UNCERTAIN
```

---

## 四、与 scholar_fetch.py 的分工

| 检查 | 工具 |
|---|---|
| 搜索真实文献 / 取 BibTeX | `python core/tools/scholar_fetch.py bibtex "<query>"`（五源 fallback） |
| DOI 存在性 | `python core/tools/scholar_fetch.py bibtex-doi "<doi>"`（走 CrossRef） |
| 语义相关性 | 宿主 agent 依 §三 prompt 判断，无需外部工具 |

所有脚本化检查复用 `core/tools/scholar_fetch.py`，不新增第三方依赖。