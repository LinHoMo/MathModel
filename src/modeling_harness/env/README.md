# env —— 环境变量配置层

`src/modeling_harness/env/` 是 Modeling-Harness 项目根目录下的**用户可调环境变量配置层**，让用户在不修改 skill 逻辑的前提下调整交付规格与运行阈值。它是 UTG 多 Agent 架构演进的第一步落地：各 agent 不再硬编码阈值，而是统一通过 `src/modeling_harness/env/loader.py` 读取本目录的 `config.yaml`。

## 目录内容

| 文件 | 作用 |
| --- | --- |
| `config.yaml` | 六组可调参数（含默认值与中文注释），用户直接编辑此文件即可调整规格 |
| `loader.py` | 零外部依赖的加载器，提供 `load_config()` / `get(key)` 接口，缺失时回退默认值 |
| `README.md` | 本说明文档 |

## 参数组（V3）

> ⚠️ 本 README 仅作可读镜像，**非单一真源**。真值以 `src/modeling_harness/env/schema.yaml`（参数定义与分层）为准。
> 论文规格参数（paper / official / deliverables）已随 V2 移除。

| 组 | 内容 |
| --- | --- |
| `code` | 代码执行规格（随机种子、多次运行次数等） |
| `modeling` | 建模规格（模型表示、校验相关） |
| `review` | 评审规格（评审分组与阈值） |
| `runtime` | 运行时（语言、执行平台） |
| `checkpoint` | 断点与恢复 |
| `cloud_sandbox` | 云端沙箱（可选） |

分层语义：OFFICIAL（官方硬约束）/ DERIVED（派生值）/ TUNABLE（可调软目标）。
合并优先级：`schema.yaml` 的 value < `config.yaml` 的 overrides。

## loader.py 接口用法

`loader.py` 零外部依赖（仅用 Python 标准库，内置极简 YAML 解析器，不依赖 PyYAML），可直接 `import` 使用：

```python
# 假设从项目根目录运行，或已把 src/modeling_harness/env/ 加入 sys.path
from core.env.loader import load_config, get

# 方式一：一次性拿到完整 config dict
cfg = load_config()
print(cfg["modeling"]["assumption_score_threshold"])  # 6.0
print(cfg["code"]["random_seed"])       # 42
print(cfg["runtime"]["strict_mode"])    # True

# 方式二：按点号路径读取单个值（推荐，agent 内部使用）
get("code.random_seed")                 # 42
get("modeling.assumption_score_threshold")  # 6.0
get("runtime.strict_mode")              # True

# key 不存在时返回 default（不抛异常）
get("not.exist.key", default="fallback")  # "fallback"
```

`load_config()` 内部会缓存加载结果，重复调用不会重复读文件；返回的是深拷贝，调用方修改不会污染缓存。

### 命令行调试

```powershell
py core\env\loader.py
```

会打印加载到的完整配置与若干 `get(key)` 示例结果，便于验证配置是否生效。

## 修改示例

### 示例 2：把随机种子改为 2024、多次运行次数改为 10

```yaml
code:
  random_seed: 2024      # 随机种子
  multi_run_count: 10    # 启发式算法多次运行次数
```

Programmer 的 `code-implementer` 生成代码时使用新种子，`result-verifier` 按 10 次校验稳定性。

## 缺失回退机制

- 若 `src/modeling_harness/env/config.yaml` **不存在**：`load_config()` 返回 `loader.py` 内置的 `DEFAULT_CONFIG`（四组默认值与本文件表格一致），并向 stderr 打印警告，**不阻塞流程**。
- 若 `config.yaml` **某字段缺失**：仅该字段回退默认值，其余字段按文件读取（通过递归合并实现）。
- 若 `config.yaml` **解析失败**（格式错误）：整体回退 `DEFAULT_CONFIG` 并打印警告，不抛异常。

这一机制保证：即使配置文件被误删或写错，建模流程仍能以默认规格继续运行，不会因配置问题中断。

## 设计约束

- `loader.py` **零外部依赖**：不依赖 PyYAML，内置极简 YAML 解析器仅支持 `key: value`、两级缩进、`#` 注释（恰好覆盖 `config.yaml` 结构）。
- `config.yaml` 的字段类型由 `loader.py` 自动推断（int / float / bool / string），用户无需加引号。
- 修改 `config.yaml` 后无需重启进程外的任何操作，下次 `load_config()` 首次调用即生效（同一进程内会缓存，如需强制重载可调用内部 `_reload()`）。
