# ADR-0007: Profiles Package (competition / research)

- Status / 状态：Accepted
- Date / 日期：2026-09-10
- Context / 上下文：目标结构规划 `profiles/` 顶层包（base.py + competition/ + research/），
  但技术重构后仅有 `workflows/competition/`（cumcm / mcm 两个赛事 profile yaml），
  **科研 profile 与 profiles/ 包均不存在**。用户确认"要搞两套 profile：一个竞赛一个科研"，
  并要求逻辑链路闭环（profile 必须被真实加载，不能是零引用死包）。
- Decision / 决策：
  1. 新建 `src/modeling_harness/profiles/` 包（依赖方向：仅标准库；不依赖
     runtime / roles / validators）：
     - `base.py`：`PROFILES_ROOT` / `PROFILE_KINDS` / `profile_path(kind, name)` /
       `AVAILABLE_PROFILES`（注册与寻址；yaml 解析留在消费方 composer）
     - `competition/cumcm.yaml`、`competition/mcm.yaml`：自
       `workflows/competition/` **git mv 迁入**（单一真源，workflows 下不复制）
     - `research/general.yaml`：新增科研通用 profile（kind: research；当前不调整
       base 4 阶段，差异声明于 description，扩展点见 profiles/README.md）
     - `README.md`：格式说明与扩展指引
  2. `runtime/execution/composer.py` 接入：
     - `load_competition` / 新增 `load_research` 改经 `profile_path` 寻址，
       解析失败统一转 `ComposeError`（对外契约不变，测试保持绿色）
     - `compose` 内部抽 `_compose(profile, label)`；新增 `compose_research(research)`
       ——两套 profile 均有真实组合入口（16 节点 DAG，与 base 一致）
  3. 测试：`tests/unit/test_workflow_compose.py` 增 `TestProfiles`
     （AVAILABLE_PROFILES / load_research / compose_research / 缺失 profile 抛错）
- Consequences / 影响：
  - `workflows/competition/` 目录清空删除（git mv 已记录重命名历史）。
  - composer 的行为契约不变（compose(competition=...) 兼容；错误类型仍为 ComposeError）。
  - 未来科研扩展（迭代修订 stage / 归档节点）通过 profiles/README.md 的
    insert_after / add_nodes 模式追加，无需改 core。
- 关联：T-CONF-006（domains 冻结）、ADR-0006（顶层归位）。
