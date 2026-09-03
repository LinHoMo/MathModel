# 工具链附录模板（toolchain-appendix-template.md）

> **来源**：R4-W9 调研发现 + 复现性铁律 #4 落地。
> **交叉验证**：见 [knowledge/laws/cross-validation-record.md](../../../knowledge/laws/cross-validation-record.md) P1-11 / C4-W9。
> **适用范围**：通用学术路径（`academic/`）所有论文产出的"复现性附录"章节。
>
> **使用方法**：复制本模板到论文项目的 `paper/` 或 `appendix/` 目录，重命名为 `toolchain_appendix.md`，逐项填写。完成后的内容应作为论文附录的"Toolchain & Reproducibility"小节。
>
> **写作原则**：
> - **完整**：Python / R / MATLAB 任一使用即必填该语言版本与包版本
> - **精确**：版本号精确到 minor（如 Python 3.10.12，非 Python 3）
> - **可复现**：包版本用 `==` 固定，避免 `>=` 或 `latest`
> - **环境完整**：除语言版本外，还需填写系统信息与编译器版本

---

## 0. 元信息

- **论文标题**：[填写]
- **目标 venue**：[期刊/会议名]
- **附录位置**：[独立附录 / Supplementary Materials / 论文末尾]
- **检查清单版本**：v1.0（2026-07-19）
- **检查人**：[填写]

---

## 1. Python 工具链（必填，如使用 Python）

### 1.1 Python 版本

- **Python 版本**：3.10.12
- **发行版**：CPython（CPython / PyPy / Anaconda）
- **虚拟环境**：venv / conda / poetry（选一）
- **环境文件**：`requirements.txt` 或 `environment.yml` 路径：`code/requirements.txt`

### 1.2 核心 Python 包版本

| # | 包名 | 版本 | 用途 |
|---|------|------|------|
| 1 | numpy | 1.26.4 | 数值计算 |
| 2 | scipy | 1.11.4 | 科学计算（统计 / 优化 / 插值） |
| 3 | matplotlib | 3.8.2 | 可视化 |
| 4 | pandas | 2.1.4 | 数据处理 |
| 5 | scikit-learn | 1.3.2 | 机器学习 |
| 6 | pytorch | 2.1.2 | 深度学习（如使用） |
| 7 | tensorflow | 2.15.0 | 深度学习（如使用，与 pytorch 二选一） |
| 8 | statsmodels | 0.14.1 | 统计建模 |
| 9 | seaborn | 0.13.1 | 统计可视化 |
| 10 | jupyter | 1.0.0 | 笔记本环境 |
| 11 | notebook | 7.0.6 | Jupyter Notebook 服务端 |
| 12 | pip | 23.3.1 | 包管理器 |
| 13 | setuptools | 68.2.2 | 打包工具 |
| 14 | tqdm | 4.66.1 | 进度条 |
| 15 | h5py | 3.10.0 | HDF5 文件读写 |

### 1.3 requirements.txt 示例

```
numpy==1.26.4
scipy==1.11.4
matplotlib==3.8.2
pandas==2.1.4
scikit-learn==1.3.2
torch==2.1.2
statsmodels==0.14.1
seaborn==0.13.1
tqdm==4.66.1
h5py==3.10.0
```

---

## 2. R 工具链（选填，如使用 R）

### 2.1 R 版本

- **R 版本**：4.3.2
- **RStudio 版本**：2023.12.0+369（如使用）
- **CRAN mirror**：清华 TUNA（https://mirrors.tuna.tsinghua.edu.cn/CRAN/）

### 2.2 核心 R 包版本

| # | 包名 | 版本 | 用途 |
|---|------|------|------|
| 1 | ggplot2 | 3.4.4 | 可视化 |
| 2 | dplyr | 1.1.4 | 数据处理 |
| 3 | tidyr | 1.3.0 | 数据整理 |
| 4 | readr | 2.1.4 | 数据读取 |
| 5 | caret | 6.0-94 | 机器学习 |
| 6 | lme4 | 1.1-35 | 混合效应模型 |
| 7 | survival | 3.5-7 | 生存分析 |
| 8 | brms | 2.20.4 | 贝叶斯回归 |

### 2.3 sessionInfo() 输出（粘贴至此）

```
R version 4.3.2 (2023-10-31)
Platform: x86_64-pc-linux-gnu (64-bit)
Running under: Ubuntu 22.04.3 LTS

Matrix products: default
BLAS:   /usr/lib/x86_64-linux-gnu/blas/libblas.so.3.10.0
LAPACK: /usr/lib/x86_64-linux-gnu/lapack/liblapack.so.3.10.0

locale:
 [1] LC_CTYPE=en_US.UTF-8       LC_NUMERIC=C
 [3] LC_TIME=en_US.UTF-8        LC_COLLATE=en_US.UTF-8
 [5] LC_MONETARY=en_US.UTF-8    LC_MESSAGES=en_US.UTF-8
 [7] LC_PAPER=en_US.UTF-8       LC_NAME=C
 [9] LC_ADDRESS=C               LC_TELEPHONE=C
[11] LC_MEASUREMENT=en_US.UTF-8 LC_IDENTIFICATION=C
```

---

## 3. MATLAB 工具链（选填，如使用 MATLAB）

### 3.1 MATLAB 版本

- **MATLAB 版本**：R2023b
- **License 类型**：Academic / Commercial / Student（选一）
- **工具箱清单**：
  - Optimization Toolbox 9.5
  - Statistics and Machine Learning Toolbox 12.5
  - Curve Fitting Toolbox 3.8
  - Deep Learning Toolbox 14.7

### 3.2 关键脚本版本

| # | 脚本名 | 版本 | 用途 |
|---|--------|------|------|
| 1 | main_solver.m | v1.2 | 主求解器 |
| 2 | data_loader.m | v1.0 | 数据加载 |
| 3 | plot_results.m | v1.1 | 结果可视化 |

---

## 4. 系统信息（必填）

### 4.1 操作系统

- **OS**：Ubuntu 22.04.3 LTS
- **内核**：Linux 6.2.0-39-generic
- **发行版**：x86_64-pc-linux-gnu

### 4.2 CPU

- **型号**：Intel Xeon Gold 6248R @ 3.00GHz
- **核数**：24 物理核 / 48 逻辑核
- **缓存**：35.75 MB L3

### 4.3 GPU（如使用）

- **型号**：NVIDIA A100-SXM4-40GB
- **显存**：40 GB
- **驱动版本**：535.129.03
- **CUDA 版本**：12.2
- **cuDNN 版本**：8.9.6

### 4.4 内存与存储

- **内存**：256 GB DDR4-3200
- **存储**：2 TB NVMe SSD（read 7000 MB/s, write 5300 MB/s）

---

## 5. 编译器版本（必填，如涉及编译）

### 5.1 LaTeX 工具链

- **TeX 发行版**：TeX Live 2023
- **xelatex 版本**：3.141592653-2.6-1.40.25
- **latexmk 版本**：4.79
- **biber 版本**：2.19
- **关键 LaTeX 包**：
  - ctex 2.12
  - hyperref 7.00v
  - biblatex 3.20
  - algorithm2e 5.3
  - booktabs 1.61803398
  - listings 1.10
  - amsmath 2.17p

### 5.2 C/C++ 编译器（如使用）

- **gcc 版本**：11.4.0
- **g++ 版本**：11.4.0
- **CMake 版本**：3.27.7

### 5.3 其他编译器（如使用）

- **Java JDK**：OpenJDK 17.0.8.1
- **Rust**：1.74.0
- **Go**：1.21.5

---

## 6. 复现性附录示例段（可直接套用）

> **Appendix A: Toolchain and Reproducibility**
>
> All experiments were conducted on a Linux server (Ubuntu 22.04.3 LTS, Intel Xeon Gold 6248R @ 3.00GHz, 24 cores, 256 GB RAM) equipped with an NVIDIA A100-SXM4-40GB GPU (Driver 535.129.03, CUDA 12.2, cuDNN 8.9.6).
>
> The implementation uses Python 3.10.12 with the following key packages: numpy 1.26.4, scipy 1.11.4, matplotlib 3.8.2, pandas 2.1.4, scikit-learn 1.3.2, and pytorch 2.1.2. The complete `requirements.txt` is provided in the supplementary materials (`code/requirements.txt`). Statistical analyses use statsmodels 0.14.1; visualization uses seaborn 0.13.1.
>
> All random number generators are seeded with `np.random.seed(42)` and `torch.manual_seed(42)`. Experiments are repeated 5 times; reported numbers are mean ± standard deviation. The complete codebase is available at https://github.com/example/repo (commit hash: a1b2c3d4).
>
> The manuscript was typeset with LaTeX (TeX Live 2023, xelatex 3.141592653-2.6-1.40.25, latexmk 4.79, biber 2.19). Key packages include ctex 2.12, hyperref 7.00v, biblatex 3.20, and booktabs 1.61803398.

---

## 7. 与既有资源的关联

### 7.1 与 reproducibility_checklist_template.md 的关系

| 模板 | 路径 | 用途 |
|------|------|------|
| reproducibility_checklist_template.md | `core/Writer/knowledge/templates/academic/planning/` | 论文级复现性清单（含 6 大节，覆盖代码/数据/结果/论文） |
| 本模板 | `core/Writer/knowledge/templates/academic/planning/` | 工具链附录（聚焦语言/包/系统/编译器版本） |

> **使用顺序**：先用 reproducibility_checklist_template.md 规划整体复现性框架，再用本模板填写工具链附录。

### 7.2 与数模路径版本的关系

数模路径（72-96 小时强约束）使用简化版工具链附录，字段与本附录对齐，去掉了非竞赛场景字段（如 GPU 集群、Docker 等）。

### 7.3 与 rules.md 复现性铁律 #4 的关系

- 铁律 #4 要求："模型可复现：固定随机种子 `np.random.seed(42)`"
- 本模板 §1.1 / §4.3 / §6 均包含随机种子声明
- 详见 [knowledge/laws/rules.md](../../../knowledge/laws/rules.md)

---

## 8. 版本与维护

- 维护者：skills 项目组
- 最后更新：2026-07-19
- 交叉验证：[cross-validation-record.md](../../../knowledge/laws/cross-validation-record.md) P1-11 / C4-W9
- 来源：Deep Research Skills Evolution V2 — P1 优化项
