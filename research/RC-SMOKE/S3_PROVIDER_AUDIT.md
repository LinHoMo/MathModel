# S3 Provider Boundary Audit（RC Smoke）

- 日期：2026-09-07 · 审计人：主会话 · 依据：RUNBOOK_RC_SMOKE.md A/B/C 分级
- 触发：预备盘点发现 `core/adapters/` 为空，疑似 provider 能力缺失。

## 1. 审计问题

> 系统是否**声明**支持 external provider execution？是否存在对应正式入口？声明与实际是否一致？

## 2. 证据

| 声明/入口 | 位置 | 实测 |
|---|---|---|
| 外部 LLM runtime 入口（OpenAI 兼容 manifest，Codex 运行时） | `adapters/openai.yaml`（由 `catalog.yaml` 单一真源经 `core/tools/gen_runtime_manifest.py` 生成；`--check` 漂移检测接入 doctor.py） | `--check` → 无漂移 (exit 0)；`--verify` → 生成 4 手 29 agent (exit 0) |
| adapter 桥接层 | `core/runtime/adapters/__init__.py`（P5 桥接：manifest / cloud_sandbox / runtime_compat 三模块稳定 import 面，实现暂留 core/tools/） | import 面存在且自述迁移映射 |
| 云代码执行沙箱 | `core/tools/runtime/cloud_sandbox.py`（E2B / Daytona 后端，默认 enabled=false，本地回退） | `status` → e2b/daytona 无 API key 不可用、local 可用、fallback=local，**行为与文档一致** (exit 0) |
| `core/adapters/` | 不存在实体 | **非缺陷**：真正的 adapter 输出在仓库根 `adapters/`（openai.yaml），`core/adapters/` 属陈旧路径预期，AGENTS.md 五层表中的 `adapters` 指上述两处 |

## 3. 判定

- **无 A 级缺陷**：已声明的能力（runtime manifest 生成/漂移检测、云沙箱可选回退）全部有正式入口且 CLI 实测通过；未发现"声称支持但无法执行"的路径。
- `core/adapters/` 空目录属**观测路径错误**（审计过程修正），不是产品缺陷；如需可在文档层面澄清 `adapters/` 双位置语义（B 类改进建议，不阻塞 RC）。
- 云沙箱真实云端执行（E2B/Daytona）未测（无 API key）——按声明属可选能力且默认关闭，不构成声明-实现缺口；若未来启用，补一次带 key 的 S3 深测。
- S3 线 smoke 判定：**PASS（boundary 级）**。深测（真实外部 runtime 驱动 29 agent）留作 S3 扩展项，不阻塞 RC。

## 4. 结论

S3 不重开 RC issue。RC Smoke 当前状态：S1 运行前门禁全绿（执行阶段待启动）、S2 阻塞（等用户材料）、S3 **boundary PASS**。
