# 权威公开数据源目录（DATA-SOURCES）

> 供 problem-parser / code-implementer / section-writer 在题目需要外部数据时选用。
> 铁律：论文中引用的任何外部数据必须在正文标注**来源名称 + URL + 访问日期**（W5 反伪造延伸）。
> 使用在线数据前确认比赛规则允许联网获取（CUMCM 允许公开数据，须引用；美赛同理）。

## 使用规范

1. **优先级**：题给数据 > 官方统计机构 > 国际组织 > 学术开放数据集 > 商业/爬虫数据（慎用）。
2. **可复现**：下载的原始文件存 `projects/<项目>/inputs/external/`，记录下载日期与版本号。
3. **口径一致**：跨年/跨国数据必须说明统计口径（如名义/实际、常住人口口径）。
4. **许可证**：商用数据集须确认 License 允许竞赛使用。

## 分领域目录

### 宏观经济与社会
| 来源 | 覆盖 | 说明 |
|---|---|---|
| 国家统计局（data.stats.gov.cn） | 中国宏观、行业、地区面板 | 官方权威；API 可下载 |
| World Bank Open Data（data.worldbank.org） | 全球发展指标（WDI） | 跨国面板首选 |
| IMF Data（data.imf.org） | 宏观经济、贸易、汇率 | |
| 联合国数据（data.un.org） | 人口、社会指标 | |

### 环境与气候
| 来源 | 覆盖 | 说明 |
|---|---|---|
| 中国气象数据网（data.cma.cn） | 中国站点气象 | 需注册 |
| NOAA（noaa.gov） / NASA GISS | 全球气温、海洋、卫星 | 公开免费 |
| Our World in Data（ourworldindata.org） | 环境-社会交叉指标 | 可视化友好，含 CSV |
| IQAir / 生态环境部 | 空气质量 | 城市级 AQI |

### 能源
| 来源 | 覆盖 | 说明 |
|---|---|---|
| IEA（iea.org/data） | 全球能源平衡 | 部分免费 |
| BP 世界能源统计年鉴 | 分国别能源消费 | 年度 PDF/数据 |
| 中电联 / 国家能源局 | 中国电力 | |

### 金融
| 来源 | 覆盖 | 说明 |
|---|---|---|
| akshare / Tushare（Python 库） | A 股、基金、宏观 | 注意接口合规 |
| Yahoo Finance | 美股行情 | |
| FRED（fred.stlouisfed.org） | 美国宏观序列 | 官方联储 |

### 交通与城市
| 来源 | 覆盖 | 说明 |
|---|---|---|
| 交通运输部 / 各省市开放数据平台 | 客流、路网 | |
| OpenStreetMap（osm.org） | 路网地理 | ODbL 许可证须标注 |
| 高德/百度开放平台 | 地理编码、路径 | 有配额限制 |

### 健康与人口
| 来源 | 覆盖 | 说明 |
|---|---|---|
| WHO / Global Health Observatory | 全球健康指标 | |
| 国家卫健委统计年鉴 | 中国健康 | |
| 全国人口普查（国家统计局） | 人口结构 | 十年一次，抽样数据可用 |

### 通用机器学习数据集
| 来源 | 覆盖 | 说明 |
|---|---|---|
| Kaggle Datasets | 竞赛级结构化数据 | 注意 License |
| UCI ML Repository | 经典基准 | 引用数据集原文 |
| 阿里天池 | 中文场景数据 | |

### 体育与赛事
| 来源 | 覆盖 | 说明 |
|---|---|---|
| IOC / Olympics.com（olympics.com/ioc） | 奥运奖牌、项目设置 | 官方口径；奖牌榜建模首选 |
| FAO / 各单项联合会官网 | 单项规则与成绩 | 规则细节（如网球计分）以官方为准 |
| Sports-Reference（sports-reference.com） | 历史赛事统计 | 非官方，交叉验证后使用 |

### 开放网络与复杂系统
| 来源 | 覆盖 | 说明 |
|---|---|---|
| SNAP（snap.stanford.edu） | 社交/引用/交通网络基准 | 学术标准数据集，引用原文 |
| OpenFlights（openflights.org/data.html） | 全球机场与航线 | ICM D 网络题常用 |
| OpenStreetMap（见交通与城市） | 路网拓扑 | 与 OSM 条目同许可证要求 |

### 国际治理与贸易
| 来源 | 覆盖 | 说明 |
|---|---|---|
| OECD Data（data.oecd.org） | OECD 国家经济-社会面板 | 政策类（ICM F）首选之一 |
| UN Comtrade（comtrade.un.org） | 双边贸易流量 | 口径（HS 编码版本）须标注 |
| FAOSTAT（fao.org/faostat） | 粮食、农业、土地利用 | 可持续/食物系统题常用 |
| Global Forest Watch（globalforestwatch.org） | 森林覆盖与毁林 | 环境类（ICM E）题常用 |

## 美赛题型 → 数据源映射

| 美赛题型 | 首选数据源入口 |
|---|---|
| MCM A / B | 多为机理题，外部数据需求低；需要时按分领域目录选用 |
| MCM C | 题给数据文件为主；补充口径用国家统计局 / World Bank / Kaggle |
| ICM D | SNAP / OpenFlights / OSM（网络结构）+ 题给数据 |
| ICM E | 环境与气候 + Global Forest Watch + Our World in Data |
| ICM F | World Bank + OECD + UN Comtrade + 联合国数据 |

> 题名与题面以 `core/knowledge/problems/MCM-ICM.md` 已核实表为准（1995–2025）。

## 与产物的衔接

- 外部数据清单写入 `work/question_spec.json` 的 assumptions/data 部分（problem-parser）。
- 每个外部数据的加载与预处理在 `code/main.py` 中注释来源。
- 论文「数据准备」一节集中列出来源表（reference-curator 负责引用闭合）。
