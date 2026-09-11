# ADR-0011: 知识卡双层门禁与 source_type 枚举增补

- Status / 状态：Accepted
- Date / 日期：2026-09-11
- Context / 上下文：

  知识层（method / failure / pattern 卡）存在两份互相独立的契约：

  1. `src/modeling_harness/runtime/knowledge/cards.py` 的运行时契约（自研 `yamlio` 解析
     + 必填字段 / ID 正则 / `failure_mode` 枚举 / 跨卡引用完整性），**fail-closed**；
  2. `src/modeling_harness/schemas/v3/knowledge/*.schema.json` 的 JSON Schema 契约
     （`additionalProperties: false`、类型、枚举）。

  问题在于：第 2 份契约在 Python 代码中**零引用**（`grep -rn "method_card.schema"` 无命中），
  因此长期没有任何执行点。后果是两类缺陷完全隐形：

  - 5 张 `mc-bzd-*.yaml` 缺 schema 必填字段 `often_combined_with` / `anti_patterns`，
    且 `source_type: BZD` 不在枚举内；
  - `mc-bearing-triangulation.yaml` 的 `formulations[0]` 含未加引号的 ASCII 冒号空格
    （`{P : arg(...)}`），PyYAML 会解析为映射而非字符串；
    同类的多行 flow 序列还会直接击穿自研解析器。

  同时发现 schema 侧本身存在漂移：`source_type` 枚举不含 `BZD`，但 5 张 BZD 试点卡与
  `tests/runtime/test_knowledge_obligation_mapping.py::test_bzd_cards_loaded_and_sourced`
  均把 `BZD` 当作合法契约值。此处**数据侧与测试侧是规格，schema 侧是过时的一方**。

- Decision / 决策：

  1. **新增知识卡双层门禁**，挂载进既有 `catalog_check.py`（符合 ADR-0009：集成进既有
     工具/节点，不新增 DAG 节点），纳入 `run_all()`，因此被 `doctor.py` 自动消费：
     - 第一层：调用 `runtime.knowledge.cards.load_knowledge()`，与真实消费路径同源、
       零第三方依赖、恒执行；
     - 第二层：JSON Schema 全量校验，`jsonschema` 为软依赖（ADR-0004），缺失时降级跳过。
  2. **schema 枚举增补 `BZD`**，并写入 description 说明其与 `expert_knowledge` 的区分
     （BZD = 外部 GitHub 评审知识仓库，保留独立溯源）。同步应用到 method_card /
     failure / pattern / competition_pack 四份 schema，保持词汇表一致。
  3. **数据侧补齐** schema 必填字段（`often_combined_with` / `anti_patterns`），
     保留 `source_type: BZD` 原值不变。
  4. **第三层：反向引用闭合**（2026-09-11 增补）。运行时 `load_knowledge()` 只对
     `card.known_failures → failure` 一个方向 fail-closed；
     `failure.applies_to → card.known_failures` 的反向无人校验，于是「写了失败记忆
     但方法卡检索不到」的死知识可以长期存在。门禁侧补齐该方向，**刻意不进运行时
     加载路径**——否则知识库编辑中间态会让运行时 fail-closed 崩溃。
  5. **降级不再静默**（2026-09-11 增补）。第二层原先在 `jsonschema` 缺失时直接
     `return`，输出仍为 OK，使「schema 全绿」在缺依赖环境下名不副实。改为写入
     `warnings` 并显式打印；新增 `--strict` 把降级提升为硬失败，供已装依赖的 CI
     使用以确保 schema 层真的执行过。warnings 默认不计入退出码，保持 ADR-0004
     的零硬依赖约束。

- Consequences / 后果：

  正面：
  - 知识卡缺陷从「运行时 fail-closed 崩溃才暴露」提前到静态检查阶段；
  - 两层互为补充：自研解析器容忍但 PyYAML 报错的写法（未加引号的冒号空格）由
    第二层捕获，运行时契约不覆盖的枚举 / 额外字段也由第二层捕获；
  - 已见效：本次改动过程中即时捕获 6 个既有缺陷 + 2 个新引入缺陷。

  负面 / 约束：
  - `catalog_check` 现在会加载全部知识卡，知识卡 YAML 语法错误会使 doctor 变红；
    这是预期行为（fail-closed 语义一致）。
  - `jsonschema` 缺失环境下第二层跳过，门禁强度下降；但**不再静默**——以 WARN
    显式打印，可用 `--strict` 提升为硬失败。不改变 ADR-0004 的零硬依赖约束。
  - 反向引用闭合提高了新增失败记忆的成本：新增 fm 卡必须同步挂进对应方法卡的
     `known_failures`，否则 catalog_check FAIL。这是刻意的——宁可让写入成本高一点，
     也不要积累检索不到的死知识。

  后续义务：
  - 新增 / 修改知识卡后必须跑 `mh catalog-check` 与 `mh doctor`；
  - 若将来新增其他 `source_type` 取值，须同步更新四份 schema，保持枚举一致。

- Evidence / 证据：

  - `grep -rn "method_card.schema" --include=*.py src/` → 零命中（改动前）。
  - 反向测试三组，均被门禁捕获（临时卡 `fm-zz-temp-negative-test.yaml`，验证后已删除）：
    - 非法 `failure_mode: not-a-real-mode` → 第一层捕获；
    - `source_type: BZD` + `bogus_extra_key: 1`（改动前）→ 第二层捕获；
    - 多行 flow 序列 `applies_to: [a,\n b]` → 第一层捕获 `YAML 解析失败: 意外的缩进层级`。
  - 门禁接入后基线：`mh catalog-check` OK；`mh doctor` 就绪 13 / 警告 0 / 阻塞 0；
    方法卡 32 / 失效卡 31 全部通过 schema。
  - `tests/runtime/test_knowledge_obligation_mapping.py:46` 断言 `card.source_type == "BZD"`。
  - **第三层反向闭合实测**：接入时发现 2 处存量断裂（`fm-small-sample-deep-learning
    → mc-xgboost`、`fm-timeseries-no-backtest → mc-grey-gm11`），已补齐；现全库
    双向闭合（0 断裂）。活性由 `tests/unit/test_catalog_check.py::TestGateIsAlive`
    证明：故意制造断裂的迷你知识库被判 1 条、闭合的判 0 条。
  - **降级可见性实测**：缺 jsonschema 环境打印 WARN 且 exit 0；加 `--strict` 后
    exit 1；有 jsonschema 环境无 WARN。三种情形均有单测覆盖。
  - 新增知识卡计数同步：`knowledge/README.md` 方法卡 27→32、失败卡 26→33
    （计数仅此一处维护，先例 6a62ea2）。
