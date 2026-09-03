# DOCX 交付线（docx-delivery.md）

> 来源：对标 math-modeling-skill 的 Word/DOCX 交付。
> 定位：定义论文手「多格式交付」的唯一正确姿势——**LaTeX 单一主线，DOCX 交付分支**。

---

## 一、铁则：LaTeX 主线，DOCX 是交付分支（不分叉）

1. **`paper/main.tex` 是唯一真值主线**：正文、公式、图表、参考文献、数值全部以 LaTeX 源为准，哈希链、schema、一致性、护栏全部针对 main.tex/main.pdf 执行。
2. **`paper/main.docx` 是「交付分支」**：面向中文赛题/工程评审常要求的 Word 提交形态。DOCX 由 `core/tools/tex_to_docx.py` 从最终 main.tex **单向渲染**，绝不反向改动论文内容或数值（铁律 W1：所有数值仍可追溯至 `figures/all_results.json`）。
3. **DOCX 不参与门禁的 HARD 判定**：它是加分交付件，不是正确性判据。main.tex 缺失时即使有 DOCX 也算失败。

## 二、策略：由 `runtime.deliver_docx` 控制（与 `compile_pdf` 同构）

| `runtime.deliver_docx` | 行为 |
|---|---|
| `never`（默认） | 不产出 DOCX，零成本（多数美赛/纯 LaTeX 场景） |
| `auto` | 检 pandoc 可用则高质量转换；无 pandoc 则产出纯文本降级版 DOCX（公式/图表以占位标注），始终交付可打开的 Word |
| `always` | 必须产出 DOCX（pandoc 缺失时以纯文本降级版满足，不阻塞） |

> 与 `compile_pdf` 的差异点：PDF 是论文真值载体、缺失是 HARD 失败；DOCX 是可选交付件，缺失只在 `deliver_docx=always` 时才需要说明，不构成 HARD。

## 三、转换工具调用

```bash
# 推荐：优先 pandoc（公式/图表/表格全保留），无 pandoc 自动降级纯文本
python core/tools/tex_to_docx.py paper/main.tex paper/main.docx
# 强制用 pandoc（pandoc 转换失败即报错，不降级）
python core/tools/tex_to_docx.py paper/main.tex paper/main.docx --force-pandoc
# 跳过 pandoc，只用纯标准库生成文本降级版
python core/tools/tex_to_docx.py paper/main.tex paper/main.docx --no-pandoc
```

- 工具零第三方依赖（同 `core/tools/state.py` / `core/tools/scholar_fetch.py`），pandoc 是「可选增强」而非「必需」。
- 纯文本降级版如实标注公式/图表为 `[公式]` / `[图]` / `[表]` 占位，不伪造还原。

## 四、final-validator 集成要点

1. 在 PDF 渲染（Step 4）之后新增 DOCX 交付步：读 `get("runtime.deliver_docx", "never")`，非 `never` 时才调用 `tex_to_docx.py`。
2. 交付清单（PAPER_SPEC.md「论文文件清单」）追加 `paper/main.docx`（仅当实际产出时）。
3. 哈希链审计（Step 5）在产出 DOCX 时把 `paper/main.docx` 纳入 artifacts。
4. 纯文本降级版必须在 PAPER_SPEC.md「已知问题」中标注「DOCX 为文本降级版，公式/图表未迁移，正式评审以 main.pdf 为准」。

## 五、交付清单（可选分支）

- `paper/main.tex`（必交付，主线）
- `paper/references.bib`（必交付）
- `paper/main.pdf`（按 `compile_pdf` 策略，理想必交付）
- `paper/main.docx`（按 `deliver_docx` 策略，可选交付分支）