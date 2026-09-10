# profiles/ — 场景 Profile 真源

两套场景 profile，均叠加在 base workflow（`workflows/base.yaml` + `workflows/stages/`）之上：

| kind | 目录 | 当前可用 | 定位 |
|---|---|---|---|
| competition | `profiles/competition/` | `cumcm`（国赛）、`mcm`（美赛） | 赛事场景：按赛事覆盖建模参数 / 节点 |
| research | `profiles/research/` | `general` | 科研场景：迭代式建模 + 严格证据门禁 + 可归档模型文档 |

## Profile 文件格式（schema_version: 3）
与 `workflows/base.yaml` 同构的子集，支持 key：

- `remove_stages: [stage]` — 移除 base 阶段
- `insert_after: [{after, stage}]` — 在某阶段后插入阶段（该 stage 须存在于 `workflows/stages/`）
- `add_nodes: {node_id: {type, role, depends_on, outputs, ...}}` — 追加节点
- `remove_nodes: [node_id]` — 移除节点
- `description` / `kind` / `name` — 场景元数据

## 接入方式
`runtime/execution/composer.py` 通过 `modeling_harness.profiles.profile_path(kind, name)`
寻址，自行解析 yaml：

```python
from modeling_harness.runtime.execution.composer import WorkflowComposer
comp = WorkflowComposer(WF)
dag = comp.compose_research("general")        # 科研 profile
dag = comp.compose(competition="cumcm")       # 赛事 profile
```

## 扩展科研 profile（示例）
科研场景需要迭代修订（evidence → 再建模）时：先在 `workflows/stages/` 增加
`revision.yaml` stage，再在 `profiles/research/xxx.yaml` 中 `insert_after`
插入；需要模型文档归档节点时用 `add_nodes`（参考 `workflows/stages/evidence.yaml`
节点字段格式）。

## 历史
- `profiles/` 于 2026-09-10 补建（ADR-0007）：competition profile 自
  `src/modeling_harness/workflows/competition/` 迁入；新增 research 场景。
- 单一真源：勿在 `workflows/` 下复制 profile 数据。
