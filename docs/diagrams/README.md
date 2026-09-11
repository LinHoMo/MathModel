# docs/diagrams — 生成物（GENERATED，勿手改）

> 本目录**全部为生成物**，由 `mh diagram repo` 从 `src/modeling_harness/catalog/v3.yaml`
> 确定性渲染。真源在 catalog；改图请改 catalog 后重跑，不要手改本目录文件。
>
> 重新生成：`py -3.12 src/modeling_harness/cli/diagram_gen.py repo`
> 渲染器：`src/modeling_harness/viz/`（零第三方依赖，输出 byte-stable，可直接 git diff）。

| 文件 | 说明 |
|---|---|
| `harness-architecture.svg` | harness 架构总览（Roles → stage/DAG 节点 → Validators） |
| `harness-architecture.html` | 同上，自包含 HTML（明暗双主题） |
| `harness-architecture.ir.json` | 派生用的 DiagramIR（可 diff 的中间表示） |
