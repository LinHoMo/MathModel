# P13-3D — Model → Paper Conversion（预注册 v2）

> 核心问题：**一个 Model Artifact 被转换成论文之后，论文是否忠实地继承了模型？**
> 以及：更好的 Model Construction 是否传导为更好的 Paper Quality？
> 治理：P13-3C 已收口（10 题/4 regime/三臂/R4 消融/R5 外部验证）；本轮不加第四臂、不优化 checklist。

## 1. 三臂（唯一变量 = 输入 Model Artifact）

| Arm | Model Artifact 来源 | Writer |
|---|---|---|
| B0 | 原始核心产物 | Same Writer |
| MMA | MathModelAgent Modeler 产物 | Same Writer |
| B1 | Construction Core 产物 | Same Writer |

首轮 3 题：2024_A（Mechanism）/ 2021_C（Data）/ 2022_B（Optimization）——各 regime 首席，且已有 R4/R5 盲评模型分作为传导起点锚。

## 2. Writer 操作化（冻结，刻意不含忠实度指令）

Writer = 独立子代理会话，输入仅【题目原文 + 匿名 MODEL_ARTIFACT】，提示词为自然论文撰写指令（"按建模方案撰写问题重述/假设/符号/模型建立/求解方法四部分，公式 LaTeX，无实验数据处以占位符标注"）——**不含任何"不得新增/修改模型"的反作弊条款**。Fidelity Gate 测的是自然 Mutation 率：如果 Writer 自发的行为就是偷偷重建模，Gate 必须抓到。

## 3. 双指标（独立，不合并）

### 3.1 Paper Quality（多维，不加总为单一数）

- Mathematical correctness：公式/推导/量纲正确性
- Problem alignment：论文是否回答了题目要求
- Completeness：模型组件覆盖度
- Communication：表达清晰度、结构合理性

（Experimental validity 本轮 n/a——三臂产物均为构造层，无实验结果。）

### 3.2 Model Fidelity Gate（双向，独立仪表盘）

比对方向一（Addition）：论文中出现 Artifact 没有的变量/约束/目标/假设/机制 = **Unauthorized Model Addition**；

比对方向二（Deletion）：Artifact 中的元素在论文中消失 = **Unauthorized Model Deletion**；

另记 Modification（同 id 异式）/ Renaming（同质异名）/ Semantic Drift（同形异义）；

每条 mutation 记录：type / severity（critical-major-minor）/ affected object / artifact 引用 / paper 引用。

汇总：Fidelity Score = 1 − (deletion+modification+drift 权重和)/artifact 元素数；Addition 单列计数。

## 4. 盲评协议

- Writer 输入匿名 artifact（X/Y/Z，映射仅存本报告）。
- 评委 = 独立子代理（同底层 LLM、无臂知识），每题一个：输入【题目 + 三份论文 + 三份对应匿名 artifact】→ 输出 Paper Quality 四维 + 每对的 mutation log。
- 已知局限：评委与生成侧同底层 LLM；论文文风可能泄露臂信息（记录但不校正）。

## 5. 判读预注册

- 若出现"B0 论文分 ≈ B1 论文分 但 B0 Fidelity ≪ B1"：即 **Paper Quality ≠ Model Quality**（Writer 补偿效应）——Fidelity Gate 的价值实锤。
- 若"B1 论文分与 Fidelity 双高"：传导成立，Model Construction 是论文质量的合法上游。
- 传导系数（探索性）：Paper Quality 对 Model 分（R4/R5 盲评分）做跨臂回归的斜率方向。

## 6. Fidelity Gate 五类 Mutation（扩展自 v1）

| Type | 定义 | 严重性判定 |
|---|---|---|
| Addition | Artifact 中不存在的变量/约束/目标/假设出现在论文中 | critical: 改变模型行为；major: 声明新能力；minor: 补充说明 |
| Deletion | Artifact 中的元素在论文中消失 | critical: 丢失核心组件；major: 丢失约束/假设；minor: 省略细节 |
| Modification | 同一 id 的表达式/定义发生变化 | critical: 改变数学含义；major: 改变参数值/范围；minor: 符号重排 |
| Renaming | 同一实体在论文中使用不同名称 | major: 造成歧义；minor: 同义替换 |
| Semantic Drift | 同一术语在 Artifact 和论文中含义不同 | critical: 概念偷换；major: 语义窄化/泛化；minor: 措辞差异 |

## 7. 执行计划

### Round 1（本轮）：3 题 × 3 臂 = 9 份论文

- 2024_A（Mechanism）：B0 / MMA / B1 → 3 papers
- 2021_C（Data）：B0 / MMA / B1 → 3 papers
- 2022_B（Optimization）：B0 / MMA / B1 → 3 papers

### Round 2（若 Round 1 传导成立）：扩到 7-10 题

保留 Round 1 的 3 题，新增 R5 的其他题目。
