# MathModelSkills 项目长期约定

## 国赛（CUMCM）官方基线 —— 已核实，勿用旧值

来源：《2025年全国大学生数学建模竞赛论文格式规范（2025年修订稿）》
https://www.cmathc.org.cn/mcm/tz/303.html ｜ 官网 https://www.mcm.edu.cn/

- **正文尽量控制在 20 页以内**，附录页数不限；不要目录
- 第 3 页为摘要专用页，**摘要 ≤1 页**，无需译成英文；从第 3 页起编页码，页脚中部，阿拉伯数字
- 无页眉；摘要页 / 正文 / 附录 / 支撑材料**任何地方**不得出现身份、学校、赛区信息
- 电子版：PDF 或 Word 之一，**≤20MB**，不压缩，**不含承诺书与编号专用页**
- 支撑材料：ZIP 或 RAR，**≤20MB**，含全部可运行源程序；文件列表放附录
- 引用：必须在正文引用处标注 + 参考文献列出，GB/T 7714 顺序编码制
- AI 使用（《人工智能工具使用规定 2025 试行》）：正文相应位置标注 + 参考文献列出所用 AI 工具
  + 支撑材料含「**AI工具使用详情**」PDF（工具/版本/目的环节/关键交互记录/采纳与人工修改情况）
- **AI 内容不能放附录** —— 附录参与查重，AI 文本相似度高会显著抬高查重率
- 违反规范者按第十二条可能取消评奖资格

⚠️ 仓库内 `core/env/config.yaml`（min_pages 25 / max_pages 30 / min_words 18000）与
`core/templates/latex/cumcm/rules.md` 第 8 行（「正文 25-30 页」）**均为错误基线**，
注有 rules_verified: 2026-08-30，是核对过但核对错了。整改前勿以此指导写作。

## 项目结构约定

- `core/` 是唯一可复用引擎，`projects/<项目>/` 是引擎跑出的实例，改引擎不动实例
- 单一真源链：`catalog.yaml` → `gen_runtime_manifest.py` → `agents/openai.yaml`
- 五个人口文件（CLAUDE.md / GEMINI.md / .cursorrules / .windsurfrules / .clinerules）均 `@AGENTS.md` 一行转发，**不要改成各自写内容**
- 不做自有品牌 CLI：推理交给宿主 agent，脚本只管门禁与状态

## 待办状态

诊断方案见根目录 `REFACTOR_PLAN.md`（2026-09-04 产出，仅诊断未改文件）。
§9 六个设计决策待用户拍板后按 P0 → P1 → P2 执行。
