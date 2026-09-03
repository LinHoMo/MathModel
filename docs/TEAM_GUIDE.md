# 团队协作指南

> 数学建模竞赛通常为 3 人团队、72-96 小时限时。本文档提供角色分工、时间轴、工具配置与冲突解决的最佳实践。

## 一、角色分工

### 1.1 三手映射（3 人团队）

| 角色 | 对应 Agent 手 | 主要职责 | 技能要求 |
|---|---|---|---|
| **建模手** | Modeler（6 agent） | 问题分析、模型建立、假设验证 | 数学推导、方法选型、文献检索 |
| **编程手** | Programmer（6 agent） | 代码实现、数值求解、结果验证 | Python/MATLAB、算法实现、调试 |
| **撰写手** | Writer（7 agent） | 论文撰写、图表制作、排版校验 | LaTeX、学术写作、可视化 |

> 评审手（Reviewer 4 agent）由三人共同承担，通常在论文初稿完成后集中进行。

### 1.2 分工原则

- **主线串联，支线并行**：Modeler → Programmer → Writer 为主线，不可跳步；但各手内部可并行（如建模手做第 2 问时编程手可开始第 1 问代码）。
- **契约驱动**：下游消费上游的结构化产物（MODEL_SPEC.md → CODE_DELIVERABLES.md → PAPER_SPEC.md），不依赖口头约定。
- **全员评审**：Reviewer 的 4 个 agent 可由三人分工执行（judge-scorer 全员、weakness-hunter 建模手主导、revision-planner 撰写手主导、revision-executor 分工执行）。

### 1.3 交叉备份

每个角色应了解相邻手的基本流程：
- 建模手了解 Programmer 的 `all_results.json` 格式，避免提出不可计算的模型。
- 编程手了解 Writer 的图表命名规范（`fig_<问题号>_<类型>_<描述>.png`），减少返工。
- 撰写手了解 Modeler 的假设编号体系，保持论文-模型一致。

## 二、时间轴模板

### 2.1 国赛 72 小时（cumcm / diangong / huawei / huashu）

| 时段 | 时长 | 建模手 | 编程手 | 撰写手 |
|---|---|---|---|---|
| Day 1 上午 | 6h | 问题解析 + 文献检索 | 环境搭建 + 数据预处理 | 论文框架 + 摘要初稿 |
| Day 1 下午 | 6h | 模型 1 建立 | 模型 1 代码实现 | 第 1 问撰写 |
| Day 1 晚上 | 4h | 模型 2 建立 | 模型 1 测试验证 | 图表制作 |
| Day 2 上午 | 6h | 模型 2 + 3 建立 | 模型 2 代码实现 | 第 2 问撰写 |
| Day 2 下午 | 6h | 模型 3 + 灵敏度 | 模型 3 + 结果验证 | 第 3 问撰写 |
| Day 2 晚上 | 4h | 假设验证 + 模型评价 | 结果汇总 + all_results.json | 第 4 问撰写 |
| Day 3 上午 | 6h | 全员评审（Reviewer 4 agent） | 修改代码 | 修改论文 |
| Day 3 下午 | 4h | 最终校验 | 最终校验 | 排版 + PDF 输出 |
| Day 3 晚上 | 2h | 提交检查 | 提交检查 | 提交检查 |

### 2.2 美赛 96 小时（mcm / apmcm）

在 72h 基础上增加：
- 额外 12h 用于 MCM/ICM 特有的 Summary Sheet 和 Use Back Sheet
- 英文写作需额外校对时间（语法、术语一致性）
- 信件类题型（ICM）需额外 4h 用于格式调整

### 2.3 里程碑检查点

```
M1: 选题完成（Day 1 前 2h）→ python core/tools/state.py <项目> status
M2: 模型 1 建立（Day 1 结束）→ MODEL_SPEC.md 至少覆盖第 1 问
M3: 代码初版可运行（Day 2 上午）→ main.py 输出第 1 问结果
M4: 论文初稿完成（Day 2 结束）→ paper/main.tex 所有章节有内容
M5: 评审完成（Day 3 上午）→ review/REVIEW_REPORT.json 通过
M6: 最终提交（截止前 2h）→ validate.py 全绿 + PDF 可打开
```

## 三、工具配置

### 3.1 统一环境

```bash
# 所有成员使用相同版本的 Python 和依赖
pip install -r requirements.txt

# 初始化项目（仅队长执行一次）
python core/tools/new_project.py <项目名> --competition cumcm --problem <赛题文件>

# 初始化状态
python core/tools/state.py <项目> init
```

### 3.2 协作模式

**模式 A：共享文件系统（推荐，局域网/同一台电脑）**

```
projects/<项目>/
├── work/STATE.md          # 全员可读的状态看板
├── output/MODEL_SPEC.md   # 建模手写，编程手写
├── code/main.py           # 编程手写
├── paper/main.tex         # 撰写手写
└── figures/               # 编程手/撰写手写
```

- 用 `STATE.md` 作为看板，每次完成一步后更新。
- 文件级锁：同一时间只有一人编辑同一文件。

**模式 B：Git 协作（远程团队）**

```bash
# 每人一个分支
git checkout -b modeler-work
git checkout -b programmer-work
git checkout -b writer-work

# 每完成一个 agent 步骤提交一次
git add output/MODEL_SPEC.md && git commit -m "modeler/model-builder: done"

# 合并到 main 由队长负责
```

### 3.3 沟通协议

| 场景 | 方式 | 频率 |
|---|---|---|
| 进度同步 | 读 `STATE.md` | 每完成一步 |
| 阻塞求助 | 即时通讯 + 说明卡在哪一步 | 即时 |
| 模型变更 | 建模手更新 MODEL_SPEC.md + 口头通知 | 即时 |
| 数值修正 | 编程手更新 `all_results.json` + 通知撰写手 | 即时 |

## 四、冲突解决

### 4.1 模型选择分歧

```
建模手提出方案 A，编程手认为难以实现 →
1. 建模手给出 10 分钟可行性论证
2. 编程手给出 10 分钟实现难度评估
3. 撰写手从论文表达角度给出意见
4. 无法达成一致 → 选建模手方案（建模手对模型质量负责）
5. 记录到 RETROSPECTIVE.md 供赛后复盘
```

### 4.2 时间分配冲突

```
某一问耗时超预期 →
1. 评估剩余时间是否够完成所有问
2. 不够 → 砍掉最低优先级的子问题（与评委评分权重对齐）
3. 撰写手先写已完成部分，不等待
4. 记录超时原因到 RETROSPECTIVE.md
```

### 4.3 论文-代码数值不一致

```
consistency-checker 发现不一致 →
1. 以 all_results.json 为准（铁律：数值可追溯）
2. 编程手确认代码输出是否正确
3. 撰写手更新论文中的数值
4. 不允许在论文阶段修改数值口径
```

## 五、赛后复盘

比赛结束后 48h 内执行：

```bash
# 生成回顾报告
python core/tools/retrospect.py <项目>

# 扫描到反思银行
python core/tools/reflection_bank.py scan

# 查看统计
python core/tools/reflection_bank.py stats

# 搜索特定经验
python core/tools/reflection_bank.py search "超时"
```

三人一起填写 RETROSPECTIVE.md 的「经验沉淀」小节，把可复用教训归档到知识库。

## 六、常见团队反模式

| 反模式 | 后果 | 正确做法 |
|---|---|---|
| 三人同时写论文 | 风格割裂、公式编号冲突 | 撰写手主笔，其他人只提供内容 |
| 建模手不参与编程 | 模型理解偏差、调试困难 | 建模手至少审查代码的模型实现部分 |
| 编程手不做测试 | 错误传播到论文 | test-runner 门禁必须通过 |
| 最后一刻才排版 | PDF 编译失败无法修复 | Day 3 上午必须有可编译的 tex |
| 忽略评审意见 | 低分提交 | Reviewer 4 agent 全部执行，不跳过 |
