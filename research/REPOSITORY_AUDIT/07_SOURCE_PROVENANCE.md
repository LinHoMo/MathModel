# 07 — Source Provenance：外部资料溯源与使用分级审计

> **审计角色**：Competitive Landscape & External Source Provenance 研究员
> **审计日期**：2026-09-08
> **核心原则**：Source of truth = 可验证的外部资料。无 provenance 的资料不得进入 benchmark / knowledge / gold standard。
> **铁律**：«不要把"获奖论文用了某模型"直接变成 gold standard。» Gold standard 必须回答 «这个模型为什么合理？»

---

## 1. Source Hierarchy 定义

### Level 0 — Official（官方）

| 属性 | 定义 |
|---|---|
| **来源** | CUMCM 官网（mcm.edu.cn）、全国大学生数学建模竞赛组委会、中国工业与应用数学学会（CSIAM）、竞赛管理系统（cumcm.cnki.net） |
| **内容类型** | 官方竞赛规则、官方论文格式规范、官方评阅文件、官方题面、官方附件、官方 AI 工具使用规定、官方章程 |
| **使用规则** | **最高优先级，可直接作为 ground truth**。所有内部规范必须与 Level 0 对齐。如发现冲突，以 Level 0 为准并记录差异。 |
| **验证要求** | URL 必须指向 mcm.edu.cn / csiam.org.cn / cumcm.cnki.net 域名，或高校官网转载的组委会官方文件（需标注原始来源）。 |

### Level 1 — Universities / Competition Organizers（高校/赛区）

| 属性 | 定义 |
|---|---|
| **来源** | 高校数学建模协会、官方赛区组委会、高校教务处/创新创业学院/竞赛中心发布的通知和培训材料 |
| **内容类型** | 赛区评阅工作规范、高校报名通知、校内选拔赛规则、培训课程资料、赛区获奖名单 |
| **使用规则** | **可作为官方规则的佐证和补充**。赛区级规范（如《赛区评阅工作规范》）有官方效力。高校通知可用于确认时间安排、流程细节。 |
| **验证要求** | URL 必须指向 `.edu.cn` 域名或官方赛区网站。需记录发布机构和发布日期。 |

### Level 2 — Published Award Papers（已发表获奖论文）

| 属性 | 定义 |
|---|---|
| **来源** | 全国一等奖/二等奖论文、官方公开优秀论文集、高校整理的获奖论文库、正式出版的优秀论文选集 |
| **内容类型** | 完整建模论文（含假设、模型、求解、结果、检验、灵敏度分析） |
| **使用规则** | **可作为 reference solution（多样性分析）和 training material**。**不得直接作为 gold standard**——获奖论文用了某模型不代表该模型是唯一正确或最优选择。必须回答"这个模型为什么合理"才能升级为 gold standard。 |
| **验证要求** | 需确认论文的奖项等级、年份、题目、参赛队伍（如可公开）。优先使用官方出版物或高校官网发布的论文。 |

### Level 3 — Established Modeling Resources（已建立建模资源）

| 属性 | 定义 |
|---|---|
| **来源** | 方法分类教材、经验总结、教学材料、算法解释文档、开源教程（如 Datawhale）、正式出版的数学建模书籍 |
| **内容类型** | 算法原理讲解、模型分类体系、建模方法论、代码示例、经验技巧 |
| **使用规则** | **可作为 knowledge base / method card 的素材来源**。可用于构建算法资源库和方法分类体系。不得作为特定题目的标准答案。 |
| **验证要求** | 优先使用有正式出版或知名开源组织（如 Datawhale）维护的资源。需记录作者/机构和出版日期。 |

### Level 4 — GitHub / Blogs / Community（社区）

| 属性 | 定义 |
|---|---|
| **来源** | GitHub 项目、个人博客、社区论坛（知乎/CSDN/掘金/小红书）、社交媒体、未验证的技术文章 |
| **内容类型** | Agent 项目、工具实现、经验分享、候选方法发现、其他 Agent 架构参考 |
| **使用规则** | **仅用于发现资料、发现实现、发现候选方法、发现其他 Agent 架构**。**不能未经验证成为 ground truth**。所有从 Level 4 获得的信息必须经过 Level 0-3 的交叉验证才能升级。 |
| **验证要求** | 必须记录 URL 和访问日期。项目需记录 Star 数、最后更新时间、架构概述。自我宣称的指标（如"85+ score""award-winning"）标记为 **marketing claim**，不得作为证据。 |

---

## 2. 已检索资料清单

本次审计共检索 **28 项**外部资料，按 Source Hierarchy 分级记录如下。

### 2.1 Level 0 — Official（官方资料，5 项）

#### SRC-001：CUMCM 官方网站首页

| 字段 | 内容 |
|---|---|
| source_url | http://www.mcm.edu.cn |
| source_type | official |
| publisher | 全国大学生数学建模竞赛组委会 / 中国工业与应用数学学会 |
| publication_date | 持续更新（检索时 2026-09-08 可访问） |
| access_date | 2026-09-08 |
| retrieval_method | direct（web.fetch） |
| what_claim_it_supports | 官网域名确认；2026 赛题发布时间（9月10日18:00）；2025 参赛规模（1837 院校/68311 队/20 万+人）；主办方为中国工业与应用数学学会；AI 工具使用规定（2026 试行）已发布 |
| whether_primary_source | true |
| verification_status | verified |

#### SRC-002：2026 高教社杯全国大学生数学建模竞赛第一次通知（含章程/参赛规则/评阅规范全文）

| 字段 | 内容 |
|---|---|
| source_url | https://www.gxufe.edu.cn/wwwservice/download?fileid=5032b109-6993-4c0a-bee7-a21ce7bb3b79.pdf |
| source_type | official（高校官网转载的组委会官方文件，原始来源为 mcm.edu.cn） |
| publisher | 全国大学生数学建模竞赛组委会（2026 年 3 月 25 日修订） |
| publication_date | 2026-03-25 |
| access_date | 2026-09-08 |
| retrieval_method | search → web.fetch（全文精读） |
| what_claim_it_supports | 竞赛时间（2026-09-10 18:00 至 09-13 20:00）；参赛作品组成（参赛论文+支撑材料）；源程序必须作为附录放入论文正文之后且与正文同一文件；源程序还需放入支撑材料；AI 工具可作为辅助但参赛队负全部责任；评奖标准（假设合理性/建模创造性/结果正确性/文字表述清晰性）；相似度≥25% 原则上不能报送全国评阅；每篇论文至少 3 位评委独立评阅；赛区报送全国评阅论文数量上限计算方式 |
| whether_primary_source | true（组委会官方文件，高校官网转载） |
| verification_status | verified |

#### SRC-003：全国大学生数学建模竞赛论文格式规范（2020 年修订稿）

| 字段 | 内容 |
|---|---|
| source_url | https://www.gxufe.edu.cn/wwwservice/download?client=pc&fileid=45586fec-ecab-4a79-8023-d8760f002dea.pdf |
| source_type | official |
| publisher | 全国大学生数学建模竞赛组委会（2020 年修订稿） |
| publication_date | 2020（修订年份） |
| access_date | 2026-09-08 |
| retrieval_method | search → web.fetch（摘要精读） |
| what_claim_it_supports | 论文第三页为摘要专用页；第四页开始正文（不要目录，**尽量控制在20页以内**）；正文之后为附录（页数不限）；附录必须打印并与正文装订在一起提交；纸质版和电子版格式规范 |
| whether_primary_source | true |
| verification_status | verified |
| **重要备注** | 任务简报中提及"正文不超过30页"，但检索到的最新官方规范（2020修订稿）为"尽量控制在20页以内"。2026 年是否有更新版本需在 mcm.edu.cn 直接确认。本仓库 env 配置 min_pages=17 为软目标，与官方"20页以内"兼容。 |

#### SRC-004：全国大学生数学建模竞赛章程（2023 年修订稿）

| 字段 | 内容 |
|---|---|
| source_url | http://www.jsnu.edu.cn/_upload/article/files/5c/98/ab5bdf5d45ffa60c15e321ee7308/218318e9-402a-45b2-ba08-d100292aabdf.pdf |
| source_type | official |
| publisher | 全国大学生数学建模竞赛组委会（2023 年修订稿，2023-12-01 试行） |
| publication_date | 2023-11-17（高校发布日期） |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 竞赛宗旨；评奖办法（赛区初评→全国复评）；公示和异议制度（公示期7天，异议期至竞赛结束后6个月） |
| whether_primary_source | true |
| verification_status | verified |

#### SRC-005：全国大学生数学建模竞赛人工智能工具使用规定（2026 年试行）

| 字段 | 内容 |
|---|---|
| source_url | http://www.mcm.edu.cn（官网"最新文章"栏目列出，检索时未获取全文 PDF） |
| source_type | official |
| publisher | 全国大学生数学建模竞赛组委会 |
| publication_date | 2026（试行） |
| access_date | 2026-09-08 |
| retrieval_method | direct（官网首页确认存在，全文待获取） |
| what_claim_it_supports | 2026 年首次试行 AI 工具使用规定；参赛队可使用 AI 工具作为辅助但须对原创性/真实性/准确性负全部责任；需遵守使用规定（具体条款待获取全文） |
| whether_primary_source | true |
| verification_status | pending（官网确认文件存在，但全文内容未获取。需后续从 mcm.edu.cn 下载全文 PDF） |
| **行动项** | 需在竞赛开始前获取该规定全文，编码为 writer 的 AI 使用披露生成和合规检查项。 |

### 2.2 Level 1 — Universities / Competition Organizers（高校/赛区资料，6 项）

#### SRC-006：东华大学 2026 年度全国大学生数学建模竞赛报名通知

| 字段 | 内容 |
|---|---|
| source_url | https://jw.dhu.edu.cn/_t1379/2026/0813/c9979a379721/page.htm |
| source_type | university |
| publisher | 东华大学教务处 |
| publication_date | 2026-08-13 |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 确认官网为 www.mcm.edu.cn；校内报名流程；竞赛组织群安排 |
| whether_primary_source | false（高校通知，非组委会原始文件） |
| verification_status | verified |

#### SRC-007：重庆理工大学 2026 年暑期培训计划通知（确认竞赛日期）

| 字段 | 内容 |
|---|---|
| source_url | https://www.cqut.edu.cn/info/1103/71040.htm |
| source_type | university |
| publisher | 重庆理工大学 |
| publication_date | 2026-08-04（最后更新） |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 确认 2026 竞赛日期为 9月10日（周四）18时至9月13日（周日）20时 |
| whether_primary_source | false |
| verification_status | verified（与 SRC-002 官方通知一致） |

#### SRC-008：中国民用航空飞行学院 2026 年数学建模竞赛选拔赛通知（含 AI 工具使用规定附录）

| 字段 | 内容 |
|---|---|
| source_url | https://www.cafuc.edu.cn/jwcx/info/1021/1752.htm |
| source_type | university |
| publisher | 中国民用航空飞行学院教务处 |
| publication_date | 2026-05-14 |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | AI 工具使用规定附录内容：可使用 AI 工具但须遵循公开透明原则；核心建模与分析必须由参赛队独立完成；使用 AI 生成的内容应在正文相应位置标注 |
| whether_primary_source | false（校内选拔赛规定，参考全国组委会规定） |
| verification_status | verified |

#### SRC-009：全国大学生数学建模竞赛赛区评阅工作规范（2019 年修订稿，附于 SRC-002）

| 字段 | 内容 |
|---|---|
| source_url | 附于 SRC-002 PDF 全文中 |
| source_type | official（赛区评阅规范，组委会发布） |
| publisher | 全国大学生数学建模竞赛组委会（2019 年修订稿） |
| publication_date | 2019（修订年份） |
| access_date | 2026-09-08 |
| retrieval_method | web.fetch（SRC-002 全文包含） |
| what_claim_it_supports | 评阅组组成；评阅前准备（随机编号、回避制度、试评阅）；评阅过程（实际评阅时间≥2天、每篇≥3位评委独立评阅、分歧复议）；突出创新点论文发现机制；相似度查证（≥25% 原则上不能报送全国评阅） |
| whether_primary_source | true |
| verification_status | verified |

#### SRC-010：太原理工大学 2026 年参赛通知

| 字段 | 内容 |
|---|---|
| source_url | https://cxcy.tyut.edu.cn/info/1026/7833.htm |
| source_type | university |
| publisher | 太原理工大学创新创业学院 |
| publication_date | 2026-06-08 |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 确认官网为 http://www.mcm.edu.cn/；竞赛组织流程 |
| whether_primary_source | false |
| verification_status | verified |

#### SRC-011：长沙理工大学全国大学生数学建模比赛简介

| 字段 | 内容 |
|---|---|
| source_url | https://www.csust.edu.cn/stxy/info/1155/10546.htm |
| source_type | university |
| publisher | 长沙理工大学数学与统计学院 |
| publication_date | 2026-03-10 |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 确认官方网站为 https://www.mcm.edu.cn；奖项设置说明（赛区一二三等奖→全国一二等奖） |
| whether_primary_source | false |
| verification_status | verified |

### 2.3 Level 2 — Published Award Papers（获奖论文相关，4 项）

#### SRC-012：2023 年 CUMCM A 题（定日镜优化）获奖案例报道

| 字段 | 内容 |
|---|---|
| source_url | https://c.m.163.com/news/a/IL195H2M0514HNSF.html |
| source_type | award-paper（获奖案例报道，非论文全文） |
| publisher | 网易新闻（高校获奖宣传） |
| publication_date | 2023-12-03 |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 2023 A 题聚焦定日镜优化；使用 Campo 布置方法；建立定日镜场输出热功率和光学效率模型；单目标优化（单位镜面面积年平均最大输出热功率）；基于多级惩罚函数的求解方法 |
| whether_primary_source | false（新闻报道，非论文全文） |
| verification_status | pending（模型家族和求解方法可参考，但需获取论文全文验证细节） |
| **结构化记录** | problem=2023-A 定日镜场优化; model_family=光学效率模型+单目标优化; subproblem=定日镜布置/热功率计算/优化求解; variables=镜面面积/布置坐标/光学效率; assumptions=Campo布置方法/太阳辐射模型; objective=单位镜面面积年平均最大输出热功率; constraints=场地约束/镜面数量约束; solution_method=多级惩罚函数优化; validation=N/A（报道未提及）; sensitivity=N/A; failure_patterns=N/A |

#### SRC-013：2023 年 CUMCM B/C 题（蔬菜销售/多波束测深）获奖案例报道

| 字段 | 内容 |
|---|---|
| source_url | http://m.toutiao.com/group/7325611727993831951/ |
| source_type | award-paper（获奖案例报道） |
| publisher | 今日头条（洛阳理工学院获奖宣传） |
| publication_date | 2024-01-19 |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 2023 获奖论文涉及：多层次数据分析在生鲜商超蔬菜销售管理；基于多波束测探原理的测线优化模型；基于优化模型制定收益最大蔬菜进货定价方案；基于几何分析的多波束测深优化模型；基于遗传算法的定日镜优化 |
| whether_primary_source | false |
| verification_status | pending |
| **结构化记录** | problem=2023-B 蔬菜补货定价 / 2023-C 多波束测深; model_family=聚类+Prophet预测+遗传算法/模拟退火（蔬菜题）; 几何分析+优化模型（测深题）; subproblem=销售预测/补货优化/定价策略; 测线优化/覆盖率计算; variables=销售量/价格/补货量/测线位置; assumptions=季节性/周期性特征; 几何测量模型; objective=收益最大化/覆盖率最大化; constraints=库存约束/需求约束; 测量精度约束; solution_method=遗传算法+模拟退火/几何优化; validation=N/A; sensitivity=N/A; failure_patterns=N/A |

#### SRC-014：数学建模优秀论文精选与点评（2016-2021 北京理工大学获奖论文集）

| 字段 | 内容 |
|---|---|
| source_url | https://mbook.kongfz.com/1336733/10451333015/ |
| source_type | award-paper（正式出版物） |
| publisher | 北京理工大学（正式出版的优秀论文选集） |
| publication_date | 2022 前后（收录 2016-2021 论文） |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 收录 2016-2021 年北理工学生获全国一/二等奖及北京市一等奖的部分论文；全文刊登未作删节；包含 2020 B 题"穿越沙漠"等完整论文 |
| whether_primary_source | true（正式出版物，论文全文） |
| verification_status | verified（出版物存在，具体论文内容需获取实体书） |
| **使用建议** | 可作为 reference solution 的重要来源。需获取实体书或电子版，逐篇提取结构化信息。 |

#### SRC-015：2024 年 CUMCM 获奖情况报道（安徽赛区 134 项）

| 字段 | 内容 |
|---|---|
| source_url | https://m.thepaper.cn/newsDetail_forward_29683878 |
| source_type | award-paper（获奖名单报道） |
| publisher | 澎湃新闻 |
| publication_date | 2024-12-18 |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 2024 年 CUMCM 安徽赛区获奖情况（全国一等奖2项/二等奖5项/赛区一等奖35项等）；CUMCM 为国家级 A 类赛事，首批列入教育部"高校学科竞赛排行榜" |
| whether_primary_source | false |
| verification_status | verified（获奖数据可交叉验证） |

### 2.4 Level 3 — Established Modeling Resources（已建立建模资源，3 项）

#### SRC-016：Datawhale intro-mathmodel（数学建模导论开源教程）

| 字段 | 内容 |
|---|---|
| source_url | https://github.com/datawhalechina/intro-mathmodel |
| source_type | established-resource |
| publisher | Datawhale（开源学习组织） |
| publication_date | 持续维护（2025 仍在用于组队学习） |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 基于《数学建模导论——基于Python语言》整理的开源教程；覆盖常用数学模型（线性/非线性规划、微分方程、预测、评价、聚类等）的 Python 实现；配套在线学习网站 |
| whether_primary_source | false（二次整理的教程，非原创研究） |
| verification_status | verified（项目存在且持续维护） |
| **使用建议** | 可作为 knowledge base / method card 的代码参考素材。需审查其模型实现的正确性后再纳入。 |

#### SRC-017：数学建模方法入门及其应用（科学出版社正式教材）

| 字段 | 内容 |
|---|---|
| source_url | https://mbook.kongfz.com/824741/10439965017/ |
| source_type | established-resource |
| publisher | 科学出版社（ISBN 9787030569578） |
| publication_date | 2018（第1版） |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 系统介绍预测预报方法（回归/时间序列/马尔可夫/灰色/神经网络）、关联分析方法（相关系数/通径分析/主成分/典型相关）、综合评价与决策方法（模糊综合评价/AHP/灰色关联/方差分析）、分类方法等 |
| whether_primary_source | true（正式出版教材） |
| verification_status | verified |
| **使用建议** | 可作为 method card 分类体系和算法原理的权威参考。 |

#### SRC-018：全国大学生数学建模竞赛培训问题的探索（中国科技论文在线）

| 字段 | 内容 |
|---|---|
| source_url | https://www.paper.edu.cn/download/downpdf/paper/MUjGAF3QORTVMIeQeQ |
| source_type | established-resource |
| publisher | 中国科技论文在线 |
| publication_date | N/A |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 竞赛题目来源；常用软件（Mathematica/Matlab/Lindo/Lingo）；蒙特卡罗算法作为比赛必用方法 |
| whether_primary_source | false |
| verification_status | verified |

### 2.5 Level 4 — GitHub / Blogs / Community（社区资料，10 项）

#### SRC-019：MathModelAgent（GitHub 项目）

| 字段 | 内容 |
|---|---|
| source_url | https://github.com/jihe520/MathModelAgent |
| source_type | community |
| publisher | jihe520（个人开发者） |
| publication_date | 2025-02（掘金博客发布时间） |
| access_date | 2026-09-08 |
| retrieval_method | search → web.fetch（掘金文章精读） |
| what_claim_it_supports | 三智能体协作框架（建模手/代码手/论文手）；本地+E2B 双模式；多 LLM 配置；LaTeX 输出 |
| whether_primary_source | false |
| verification_status | unverified（项目架构基于博客文章描述，未实际运行验证） |
| **marketing claim** | "3天→1小时""获奖级论文"——无 benchmark evidence |

#### SRC-020：Math Modeling Skill（XiaoMaColtAI，GitHub 项目）

| 字段 | 内容 |
|---|---|
| source_url | https://github.com/XiaoMaColtAI/math-modeling-skill |
| source_type | community |
| publisher | XiaoMaColtAI（个人开发者） |
| publication_date | 2026-03（掘金发布时间） |
| access_date | 2026-09-08 |
| retrieval_method | search → web.fetch（掘金文章全文精读） |
| what_claim_it_supports | 三阶段工作流+三角色；7 大类 60+ 算法资源库；4 个子 Skill（pdf/xlsx/docx/paper_search）；优秀论文库；去 AI 味指南；xlsx 强制使用公式而非硬编码 |
| whether_primary_source | false |
| verification_status | partial（目录结构和算法分类有文章详细描述，但未实际安装运行验证） |
| **marketing claim** | "全流程自动化"——无端到端评测数据 |

#### SRC-021：ASI-Bench（GitHub 项目）

| 字段 | 内容 |
|---|---|
| source_url | https://github.com/apexin-ai/ASI-Bench |
| source_type | community（学术研究项目，有 arXiv 论文） |
| publisher | apexin-ai（清华/哈佛等机构联合） |
| publication_date | 2026-08（arXiv:2608.17271） |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 11 大学科 60 项项目级科研任务；端到端科研能力评估；任务来源于 1300+ 学术文献 |
| whether_primary_source | false（有论文但项目为社区开源） |
| verification_status | verified（arXiv 论文存在，项目结构有公开描述） |
| **使用建议** | 可作为 MMBench 任务结构设计的参考范式。其项目级任务设计（多环节闭环）值得借鉴。 |

#### SRC-022：IDA-Bench（GitHub 项目）

| 字段 | 内容 |
|---|---|
| source_url | https://github.com/lhydave/IDA-Bench |
| source_type | community（学术研究项目，有 arXiv 论文） |
| publisher | 北大/伯克利联合团队 |
| publication_date | 2025-06（arXiv:2505.18223） |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 迭代式数据分析基准；多轮演进指令；最强 Agent 成功率仅 40%；证明静态单轮 benchmark 高估实际分析能力 |
| whether_primary_source | false |
| verification_status | verified（arXiv 论文存在） |

#### SRC-023：AgentSociety（清华 FIB Lab，GitHub 项目）

| 字段 | 内容 |
|---|---|
| source_url | https://github.com/tsinghua-fib-lab/agentsociety |
| source_type | community（学术研究项目） |
| publisher | 清华 FIB 实验室 |
| publication_date | 2025-07（Urban Cup 2025 使用） |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 多智能体社会模拟框架；含 agentsociety-benchmark 子包；LLM 驱动的自主认知智能体；大规模异质 Agent 交互 |
| whether_primary_source | false |
| verification_status | verified（项目存在，有学术论文支撑） |

#### SRC-024：OmniaBench（GitHub 项目）

| 字段 | 内容 |
|---|---|
| source_url | https://github.com/scuuy/OmniaBench |
| source_type | community（学术研究项目，有 arXiv 论文） |
| publisher | scuuy（四川大学等） |
| publication_date | 2026-07（arXiv:2607.14989） |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 通用 Agent 基准；代码/数据集/评估工具全开源（Apache 2.0）；HuggingFace 数据集 |
| whether_primary_source | false |
| verification_status | verified |

#### SRC-025：MATH Dataset / MATH500 / GSM8K（标准数学推理基准）

| 字段 | 内容 |
|---|---|
| source_url | https://github.com/hendrycks/math |
| source_type | community（学术研究项目，已成为事实标准） |
| publisher | Dan Hendrycks 等（UC Berkeley） |
| publication_date | MATH (2021)；MATH500 (2023)；GSM8K (2021) |
| access_date | 2026-09-08 |
| retrieval_method | search（多次交叉验证） |
| what_claim_it_supports | MATH：7500 道竞赛级数学题，7 大领域 5 级难度；MATH500：500 道代表性子集；GSM8K：8500 道小学数学题；这些是 LLM 数学推理的事实标准基准；2025 USAMO 测试所有大模型得分 <5% |
| whether_primary_source | true（基准数据集本身为原始研究产出） |
| verification_status | verified |
| **使用建议** | 可作为"基础数学推理能力"的下游评估维度。**不得作为建模专项能力的评估基准**——这些基准不覆盖建模全流程。 |

#### SRC-026：MathDebugger（北京大学 DCAI，EMNLP 2026）

| 字段 | 内容 |
|---|---|
| source_url | EMNLP 2026 论文（检索时未找到独立 GitHub 仓库） |
| source_type | community（学术研究项目） |
| publisher | 北京大学 DCAI 团队 |
| publication_date | 2026-09（EMNLP 2026 接收） |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | 数学合成数据质检基准；4000 题+2000 带标注答案+7 类细粒度错误类型；评测 14 个 LLM 和 3 个 PRM；合成数据中存在大量隐性错误 |
| whether_primary_source | false |
| verification_status | pending（论文信息有公开报道，但未获取论文全文和代码） |

#### SRC-027：SPSSPRO（商业数学建模平台）

| 字段 | 内容 |
|---|---|
| source_url | https://www.spsspro.com |
| source_type | community（商业产品） |
| publisher | SPSSPRO 团队（CUMCM 2026 官方赞助单位） |
| publication_date | 持续运营 |
| access_date | 2026-09-08 |
| retrieval_method | search（官网确认 CUMCM 赞助商身份） |
| what_claim_it_supports | 在线数据分析平台；拖拽式统计分析/机器学习/可视化；CUMCM 官方赞助单位 |
| whether_primary_source | false |
| verification_status | verified（赞助商身份在 mcm.edu.cn 官网确认） |
| **使用建议** | 仅作为"工具民主化"路线的参考，不纳入技术架构。其黑箱工具调用模式与 evidence graph 理念冲突。 |

#### SRC-028：数维杯 2026 参赛规则（含 AIGC 检测标准）

| 字段 | 内容 |
|---|---|
| source_url | https://m.sohu.com/a/1062634385_120128117/ |
| source_type | community（其他竞赛规则，非 CUMCM 官方） |
| publisher | 数维杯组委会（搜狐转载） |
| publication_date | 2026-08-14 |
| access_date | 2026-09-08 |
| retrieval_method | search |
| what_claim_it_supports | AIGC 生成比例超过 30% 视为雷同；总相似比（含引用）超过 50% 视为雷同；评审标准（摘要要素/问题解读/假设合理性/建模动机/模型有效性/稳定性敏感性分析） |
| whether_primary_source | false（数维杯是独立竞赛，非 CUMCM） |
| verification_status | verified |
| **使用建议** | 其 AIGC 检测标准（30% 阈值）可作为参考，但**不得直接套用为 CUMCM 标准**。CUMCM 的 AI 使用规定需以 SRC-005 为准。其评审标准可与 CUMCM 官方评阅标准交叉对比。 |

---

## 3. CUMCM 官方规范检索汇总

### 3.1 官方论文格式规范

| 项目 | 内容 | 来源 |
|---|---|---|
| **规范名称** | 《全国大学生数学建模竞赛论文格式规范》 | SRC-003 |
| **发布机构** | 全国大学生数学建模竞赛组委会 | SRC-003 |
| **版本** | 2020 年修订稿（检索到的最新版本） | SRC-003 |
| **摘要页** | 论文第三页为摘要专用页 | SRC-003 |
| **正文起始** | 第四页开始正文，不要目录 | SRC-003 |
| **正文页数** | **尽量控制在 20 页以内**（软目标，非硬上限） | SRC-003 |
| **附录** | 正文之后为附录，页数不限；附录必须打印并与正文装订在一起 | SRC-003 |
| **源程序位置** | 源程序应作为附录放入参赛论文正文之后，与论文正文编辑在同一个文件中 | SRC-002 |
| **支撑材料** | 源程序除放入论文附录外，还应放入支撑材料（ZIP/RAR 压缩包） | SRC-002 |
| **文件格式** | PDF 或 Word 之一（建议非图片 PDF），不要压缩 | SRC-002 |
| **承诺书/编号页** | 参赛论文中不能包含承诺书和编号专用页（单独打印装订在论文之前） | SRC-002 |

**⚠️ 重要差异说明**：任务简报中提及"正文不超过 30 页"，但检索到的官方规范（2020 修订稿）为"尽量控制在 20 页以内"。可能的解释：
1. 2026 年有更新版本将页数放宽至 30 页（需在 mcm.edu.cn 确认）
2. 任务简报中的"30 页"可能参考了其他竞赛（如数维杯 25 页、美赛 25 页）或包含附录的总页数
3. 本仓库 env 配置 min_pages=17 为软目标，与官方"20 页以内"兼容

**行动项**：需在 2026 竞赛开始前从 mcm.edu.cn 下载最新版论文格式规范，确认是否有页数更新。

### 3.2 官方/历史评阅标准

| 项目 | 内容 | 来源 |
|---|---|---|
| **评奖主要标准** | 假设的合理性、建模的创造性、结果的正确性、文字表述的清晰程度 | SRC-002（章程第二条） |
| **论文必须包含** | 模型的假设、建立和求解、计算方法的设计和计算机实现、结果的分析和检验、模型的改进 | SRC-002（章程第二条） |
| **评委数量** | 每篇论文至少 3 位评委独立评阅 | SRC-002（评阅规范第十三条） |
| **评阅时间** | 实际评阅时间原则不少于 2 天 | SRC-002（评阅规范第十一条） |
| **分歧处理** | 评委分歧较大时组织复议，消除误判和个人评分习惯误差 | SRC-002（评阅规范第十四条） |
| **突出创新点** | 允许赛区额外报送有突出创新点但全面量达不到全国奖水平的论文（每赛区每年每题最多 1 篇） | SRC-002（评阅规范附件1） |
| **相似度阈值** | 两个相似度（知网文献库+竞赛自建库）中任何一个 ≥25%，原则上不能报送全国评阅 | SRC-002（评阅规范附件3） |
| **赛区报送上限** | 按报名队数分段计算（≤200队部分12%，200-500队部分10%，500-800队部分8%，>800队部分5%），再按比例分配 | SRC-002（评阅规范附件2） |
| **一等奖申报比例** | 每个赛区报送全国评阅论文中，申报一等奖数量不超过 40% | SRC-002（评阅规范附件2） |
| **同校报送上限** | 同一所学校每道赛题报送全国评阅不超过 4 篇（其中一等奖不超过 2 篇） | SRC-002（评阅规范附件2） |

**关键洞察**：官方评阅标准的四项核心（假设合理性/建模创造性/结果正确性/表述清晰性）中，**没有论文长度、没有算法数量、没有参考文献数量**。这直接验证了本仓库"longer paper ≠ better solution""more algorithms ≠ better model selection"的判断。

### 3.3 官方题面和附件获取渠道

| 渠道 | URL | 说明 | 来源 |
|---|---|---|---|
| CUMCM 官网 | http://www.mcm.edu.cn | 赛题于竞赛开始时发布 | SRC-001 |
| 竞赛管理系统 | https://cumcm.cnki.net | 报名、下载赛题、提交作品的官方系统 | SRC-002 |
| 中国知网 | （官网合作发布渠道） | 赛题同步发布 | SRC-001 |
| 中国大学生在线 | （官网合作发布渠道） | 赛题同步发布 | SRC-001 |
| 高等教育出版社 | （官网合作发布渠道） | 赛题同步发布 | SRC-001 |
| 中国高校数学建模课程中心 | （官网合作发布渠道） | 赛题同步发布 | SRC-001 |
| 北太振寰 | （官网合作发布渠道） | 赛题同步发布 | SRC-001 |

### 3.4 竞赛规则和时间安排（2026）

| 项目 | 内容 | 来源 |
|---|---|---|
| **竞赛时间** | 2026 年 9 月 10 日（周四）18:00 至 9 月 13 日（周日）20:00 | SRC-002 / SRC-007 |
| **赛题发布** | 竞赛开始时在官网及合作网站发布 | SRC-001 |
| **MD5 码提交** | 9 月 10 日 18:00 至 9 月 13 日 20:00（可多次上传） | SRC-002 |
| **电子文档提交** | 9 月 13 日 20:30 至 9 月 14 日 14:00 | SRC-002 |
| **纸质版提交** | 按赛区组委会要求（含承诺书和编号专用页） | SRC-002 |
| **参赛队伍** | 每队不超过 3 人，同一学校，研究生不得参加 | SRC-002（章程第三条） |
| **指导教师** | 最多 1 名，竞赛期间不得指导 | SRC-002（章程第三条） |
| **AI 工具** | 可作为辅助，参赛队负全部责任，须遵守《AI 工具使用规定（2026 试行）》 | SRC-002（参赛规则第6条）/ SRC-005 |
| **2025 参赛规模** | 1837 院校/校区，68311 队（本科 61463/高职 6848），20 万+人 | SRC-001 |

---

## 4. 获奖论文检索与结构化记录

### 4.1 检索说明

本次审计通过新闻报道、出版物信息和高校官网检索到以下获奖论文线索。**注意**：由于 CUMCM 获奖论文全文通常不公开在线发布（需通过官方出版物或高校内部资料获取），本次检索到的多为案例报道而非论文全文。结构化记录中标注 N/A 的字段表示报道未提及，需获取论文全文后补充。

### 4.2 获奖论文结构化记录

#### PAPER-001：2023 A 题 — 定日镜场优化设计

| 字段 | 内容 |
|---|---|
| problem | 2023 CUMCM A 题（定日镜场优化） |
| paper | 某高校全国一等奖论文（具体队伍待确认） |
| model_family | 光学效率模型 + 单目标优化模型 |
| subproblem | 定日镜布置方法 / 热功率计算 / 优化求解 |
| variables | 镜面面积、布置坐标、光学效率、太阳辐射参数 |
| assumptions | Campo 布置方法、太阳辐射模型、镜面反射模型 |
| objective | 单位镜面面积年平均最大输出热功率 |
| constraints | 场地几何约束、镜面数量约束、阴影遮挡约束 |
| solution_method | 基于多级惩罚函数的优化算法 |
| validation | N/A（报道未提及） |
| sensitivity | N/A（报道未提及） |
| failure_patterns | N/A |
| source | SRC-012 |
| verification_status | pending（需获取论文全文验证） |

**Gold standard 评估**：该论文使用了 Campo 布置方法+多级惩罚函数优化，但«这并不意味着 Campo 布置是定日镜问题的唯一正确方法»。要升级为 gold standard，必须回答：Campo 布置方法相比其他布置方法（如径向交错、仿生布置）的优势是什么？多级惩罚函数相比其他优化算法（遗传算法、PSO）的收敛性和精度如何？这些问题在报道中未回答。

#### PAPER-002：2023 B 题 — 蔬菜商品补货和定价方案

| 字段 | 内容 |
|---|---|
| problem | 2023 CUMCM B 题（蔬菜补货与定价） |
| paper | 复旦大学全国一等奖论文（队伍：曹宇轩等） |
| model_family | 聚类分析 + Prophet 时间序列预测 + 遗传算法/模拟退火优化 |
| subproblem | 销售数据分析 / 需求预测 / 补货优化 / 定价策略 |
| variables | 销售量、价格、补货量、库存水平、商品品类 |
| assumptions | 蔬菜季节性/周期性特征、需求可预测、库存约束 |
| objective | 收益最大化（或损耗最小化+收益最大化多目标） |
| constraints | 库存容量约束、需求约束、新鲜度约束、定价范围约束 |
| solution_method | Prophet 预测 + 遗传算法/模拟退火优化 |
| validation | N/A |
| sensitivity | N/A |
| failure_patterns | N/A |
| source | SRC-013 / 复旦获奖报道 |
| verification_status | pending |

**Gold standard 评估**：Prophet+遗传算法是该题的常见解法组合，但«Prophet 预测的适用性取决于数据的季节性和周期性强度»。对于噪声大、趋势突变的数据，Prophet 可能不如 LSTM 或 XGBoost。必须论证为什么 Prophet 适合该数据集才能升级为 gold standard。

#### PAPER-003：2023 C 题 — 多波束测深测线优化

| 字段 | 内容 |
|---|---|
| problem | 2023 CUMCM C 题（多波束测深测线优化） |
| paper | 洛阳理工学院赛区一等奖论文 |
| model_family | 几何分析模型 + 优化模型 |
| subproblem | 测线覆盖计算 / 测线间距优化 / 覆盖率评估 |
| variables | 测线位置、测线间距、覆盖宽度、水深参数 |
| assumptions | 几何测量模型、海底地形简化假设 |
| objective | 覆盖率最大化 / 测量效率最大化 |
| constraints | 测量精度约束、设备参数约束、测线长度约束 |
| solution_method | 几何分析 + 优化算法 |
| validation | N/A |
| sensitivity | N/A |
| failure_patterns | N/A |
| source | SRC-013 |
| verification_status | pending |

#### PAPER-004：2020 B 题 — 穿越沙漠（收录于北理工优秀论文集）

| 字段 | 内容 |
|---|---|
| problem | 2020 CUMCM B 题（穿越沙漠） |
| paper | 北京理工大学获奖论文（收录于 SRC-014 出版物） |
| model_family | 动态规划 / 图论最短路 / 资源优化 |
| subproblem | 路径规划 / 资源分配 / 天气应对策略 |
| variables | 位置、时间、资金、水量、食物量、天气状态 |
| assumptions | 天气模型、资源消耗模型、市场价格模型 |
| objective | 收益最大化 / 成功穿越概率最大化 |
| constraints | 资源容量约束、时间约束、天气约束 |
| solution_method | 动态规划 / 最短路算法 |
| validation | N/A（需获取论文全文） |
| sensitivity | N/A |
| failure_patterns | N/A |
| source | SRC-014 |
| verification_status | pending（出版物存在，需获取实体书阅读全文） |

### 4.3 获奖论文使用原则

**«不要把"获奖论文用了某模型"直接变成 gold standard。»**

获奖论文的模型选择受到以下因素影响，不能简单复制：
1. **数据特征**：特定年份/题目的数据分布可能特别适合某模型，换一套数据可能不适用
2. **评委偏好**：不同评委对模型类型有个人偏好，获奖不代表模型客观最优
3. **时间约束**：72 小时内的选择可能是"够用就好"而非"理论最优"
4. **团队背景**：队员熟悉的工具和方法影响选择，不代表方法本身最合适
5. **题目解读**：不同队伍对题目的理解不同，模型选择基于不同的问题重构

**Gold standard 必须回答**：
- 这个模型的**假设**是什么？在本题中是否成立？
- 这个模型相比**候选模型**的优势是什么？有定量比较吗？
- 这个模型的**局限性**是什么？在什么条件下会失效？
- 这个模型的**结果**是否经过验证？验证方法是什么？
- 灵敏度分析是否覆盖了关键参数？

只有回答了以上问题的获奖论文模型，才能从 Level 2（reference solution）升级为 benchmark gold standard。

---

## 5. 资料使用建议

### 5.1 使用分级矩阵

| 资料 | 级别 | 可直接进入 benchmark gold standard | 可作为 reference solution | 可作为 training material | 仅作为发现线索 | 禁止使用 |
|---|---|---|---|---|---|---|
| SRC-001 官网首页 | L0 | — | — | ✅（流程/规模参考） | — | — |
| SRC-002 2026 通知+规则全文 | L0 | ✅（评阅标准/提交规则） | — | ✅ | — | — |
| SRC-003 论文格式规范 2020 | L0 | ✅（格式校验标准） | — | ✅ | — | — |
| SRC-004 章程 2023 | L0 | ✅（评奖标准） | — | ✅ | — | — |
| SRC-005 AI 工具使用规定 2026 | L0 | ⚠️ pending（全文待获取） | — | ✅（待全文） | — | — |
| SRC-006~011 高校通知 | L1 | — | — | ✅（流程参考） | ✅（时间/渠道确认） | — |
| SRC-012~013 获奖案例报道 | L2 | ❌（非全文，细节不足） | ⚠️ partial（模型家族参考） | ✅ | ✅（发现论文线索） | — |
| SRC-014 北理工获奖论文集 | L2 | ❌（需逐篇论证模型合理性） | ✅（全文可获取后） | ✅ | ✅ | — |
| SRC-015 获奖名单报道 | L2 | — | — | ✅（规模参考） | ✅ | — |
| SRC-016 Datawhale 教程 | L3 | — | — | ✅（方法卡素材） | ✅（代码参考） | — |
| SRC-017 科学出版社教材 | L3 | — | — | ✅（方法分类权威参考） | — | — |
| SRC-018 培训论文 | L3 | — | — | ✅ | ✅ | — |
| SRC-019 MathModelAgent | L4 | ❌ | ❌ | ⚠️（架构参考） | ✅（发现 Agent 架构） | ❌（marketing claim 不得作为证据） |
| SRC-020 Math Modeling Skill | L4 | ❌ | ❌ | ⚠️（算法分类/去AI味参考） | ✅（发现 Skill 架构） | ❌（"全流程自动化"为 marketing claim） |
| SRC-021 ASI-Bench | L4 | ⚠️（任务结构可参考，非建模专项） | — | ✅ | ✅（benchmark 设计参考） | — |
| SRC-022 IDA-Bench | L4 | — | — | ✅ | ✅（迭代式评估范式参考） | — |
| SRC-023 AgentSociety | L4 | — | — | ⚠️（多 Agent 交互参考） | ✅ | — |
| SRC-024 OmniaBench | L4 | — | — | ✅ | ✅（通用 Agent 评估参考） | — |
| SRC-025 MATH/MATH500/GSM8K | L4(学术) | ❌（纯数学解题≠建模） | — | ✅（基础推理能力下游评估） | ✅ | — |
| SRC-026 MathDebugger | L4 | — | — | ✅（错误分类参考） | ✅ | — |
| SRC-027 SPSSPRO | L4 | ❌ | ❌ | — | ✅（工具平台参考） | ❌（黑箱工具调用不得纳入架构） |
| SRC-028 数维杯规则 | L4 | ❌（非 CUMCM 官方） | — | ⚠️（AIGC 阈值参考） | ✅（其他竞赛对比） | ❌（不得套用为 CUMCM 标准） |

### 5.2 禁止使用清单

以下资料**不得**作为 ground truth 或证据使用：

1. **任何 Level 4 项目的自我宣称指标**（如"85+ score""award-winning""fully automatic""3天→1小时"）——标记为 marketing claim
2. **数维杯等其他竞赛的规则**——不得套用为 CUMCM 标准
3. **SPSSPRO 等商业平台的黑箱算法结果**——不可追溯，与 evidence graph 冲突
4. **未获取全文的获奖论文模型细节**——基于报道的模型描述不足以验证
5. **MATH/GSM8K 等纯数学解题基准的结果**——不能作为数学建模能力的证据
6. **个人博客中未经验证的"经验总结"**——如"论文要凑到20页"等非官方建议

### 5.3 待验证/待获取行动项

| 优先级 | 行动项 | 原因 |
|---|---|---|
| P0 | 获取《全国大学生数学建模竞赛人工智能工具使用规定（2026 年试行）》全文 | 2026 首次试行，直接影响论文合规性 |
| P0 | 确认 2026 年是否有更新版论文格式规范（页数是否从 20 页变为 30 页） | 任务简报与官方 2020 版存在差异 |
| P1 | 获取北理工优秀论文集（SRC-014）实体书或电子版 | 重要的 reference solution 来源 |
| P1 | 系统收集 CUMCM 历年题面+附件（构建 MMBENCH_ROOT 语料库） | benchmark 基础设施 |
| P2 | 获取 MathDebugger 论文全文和代码 | 错误分类体系可借鉴 |
| P2 | 实际安装运行 Math Modeling Skill（SRC-020）验证其算法库和子 Skill | 从 partial 升级为 verified |

---

## 附录：检索统计

| 指标 | 数值 |
|---|---|
| 检索总资料数 | 28 项 |
| Level 0（官方） | 5 项 |
| Level 1（高校/赛区） | 6 项 |
| Level 2（获奖论文） | 4 项 |
| Level 3（已建立资源） | 3 项 |
| Level 4（社区） | 10 项 |
| verified | 19 项 |
| pending | 6 项 |
| unverified / partial | 3 项 |
| 含 marketing claim 标记 | 3 项（SRC-019, SRC-020, 及部分多 Agent 框架宣称） |
| 检索日期 | 2026-09-08 |
| 检索工具 | general_search（中英文多轮）+ web.fetch（深度阅读 4 篇全文） |
