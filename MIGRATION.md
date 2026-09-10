# MIGRATION — MathModel → Modeling-Harness

> 生效日期：2026-09-10 ｜ 类型：品牌迁移 + 技术层重建
> 本文件说明旧品牌 **MathModel** 与现品牌 **Modeling-Harness**（中文名：**建模执行框架**）
> 之间的关系、迁移路径与回滚方式。历史记录不改写，旧名仅在本文件、CHANGELOG 历史、
> 外部专名与历史数据中保留。

---

## 1. 为什么改名

原项目名 MathModel 与外部同名产品（MathModelAgent 等）存在命名混淆，且无法表达
本项目真实定位：**面向数模竞赛与科研的可信建模执行与验证框架（A verification-centered
modeling harness for competitions and research）**。新品牌 Modeling-Harness 强调
「Harness（可信执行与验证底座）」而非「Model（模型本身）」——认知由外部 Agent 完成，
Harness 负责执行、验证、证据与状态。

核心信条与关键红线保持不变：

- **The Agent Is Not The State. The Harness Is The State.**
- **Execution success ≠ Model correct.**

## 2. 映射表

| 类型 | 旧 | 新 | 策略 |
|---|---|---|---|
| 品牌名 | MathModel | **Modeling-Harness** | 品牌层全面替换 |
| 中文名 | — | **建模执行框架** | 新增 |
| 中文副标题 | — | 面向数模竞赛与科研的可信建模执行与验证框架 | 新增 |
| 英文副标题 | — | A verification-centered modeling harness for competitions and research | 新增 |
| 领域词 | 数学建模 | 数学建模 | **不动** |
| GitHub 组织 | LinHoMo | LinHoMo | 保留 |
| GitHub 仓库 | LinHoMo/MathModel | LinHoMo/modeling-harness | 改名，旧链接自动重定向 |
| Python 发行名 | mathmodel-skills | modeling-harness-skills → `modeling_harness`（技术重构后） | 新名为主，旧名不再使用 |
| CLI | （原无 CLI） | `mh` / `modeling-harness` | 技术重构新增 |
| 环境变量 | （harness 无 `MATHMODEL_*`；仅外部产品 `MATHMODEL_AGENT_API`） | `MH_*` | 外部产品变量保留原样 |
| 配置目录 | （无用户级配置目录） | `.mh/` | 技术重构新增 |
| Artifact ID | V3 Stable ID（P/Q/M/A/…） | `MH-<type>-<seq>` | 技术重构统一 |
| Schema 命名空间 | `mathmodel:v3/...` | `modeling_harness.*` | 技术重构统一 |
| 内部类名 | MathModelAgentAdapter（外部产品适配器） | MathModelAgentAdapter | **不改**（外部专名） |
| 历史记录 | MathModel | MathModel | **不改写，只加注** |

## 3. 三层迁移策略

### 品牌层：全面替换

README 标题/描述/目录树、catalog.yaml、CLAUDE.md、.github/copilot-instructions.md、
CONTRIBUTING.md、AGENTS.md 标题与 GitHub URL、docs 架构文档标题、env 注释、
validate.py / doctor.py / scholar_fetch.py 输出字符串 —— 全部替换为 Modeling-Harness。

### 技术层：新名为主

- Python 发行名：`mathmodel-skills` → `modeling-harness-skills`（品牌迁移）→
  `modeling_harness` 包（技术重构后）。
- Schema 命名空间：`mathmodel:v3/...` → `modeling_harness.*`。
- Artifact ID：统一 `MH-<type>-<seq>`（技术重构后）。
- 技术重构完成后**不再保留**任何 mathmodel shim / alias / deprecated 路径。

### 历史层：不改写，只加注

- CHANGELOG 旧条目、旧 release notes、旧 issue/PR 引用、git 历史不改。
- `research/`（实验报告、冻结规格、manifests）与 `projects/`（运行实例、run records）
  保持原样——它们是历史证据，改即伪造。
- 外部专名（MathModelAgent、zhanwen/MathModel、jihe520/MathModelAgent、
  LLM-MM-Agent/MM-Bench 等）保持原样，它们是第三方项目名。
- 已发表论文中的旧名不改。

## 4. 迁移路径

| 使用者 | 迁移动作 |
|---|---|
| 文档读者 | 旧链接 `LinHoMo/MathModel` 由 GitHub 自动重定向到 `LinHoMo/modeling-harness` |
| 代码/工具 | 技术重构后统一使用 `mh` CLI、`MH_*` 环境变量、`.mh/` 配置目录、`MH-` Artifact ID |
| 旧实例 | 技术重构提供一次性迁移脚本 `scripts/migrate_legacy_projects.py`（--dry-run 支持） |
| 历史数据 | 不改写；运行时不读旧兼容入口 |

## 5. 兼容时间表

| 时间 | 状态 |
|---|---|
| 2026-09-10（品牌迁移） | 品牌全面替换；旧品牌仅存于 MIGRATION.md / CHANGELOG 历史 / 外部专名 / 历史数据 |
| 2026-09-10（技术重构） | 技术层按最优结构重建，**不保留** mathmodel shim / alias / deprecated 路径；运行时不再兼容旧入口 |

## 6. 回滚方式

```powershell
# 品牌迁移回滚
git checkout main
git branch -D rebrand/modeling-harness
git reset --hard pre-rebrand-mathmodel

# 技术重构回滚
git reset --hard pre-tech-rebuild
```

GitHub 仓库名回滚：`gh repo rename MathModel` + `git remote set-url origin git@github.com:LinHoMo/MathModel.git`。
