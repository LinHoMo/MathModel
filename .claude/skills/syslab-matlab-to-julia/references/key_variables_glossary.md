# 关键指标词汇表 (Key Variables Glossary)

本文档整理了 MATLAB 到 Julia 转换过程中需要特别关注的关键指标变量。这些指标通常用于功能测试（Back-to-Back Testing）的结果测试，正确识别和处理这些指标对于确保转换质量至关重要。

---

## 目录

1. [通信系统指标](#1-通信系统指标)
2. [信号处理指标](#2-信号处理指标)
3. [控制系统指标](#3-控制系统指标)
4. [图像处理指标](#4-图像处理指标)
5. [通用指标](#5-通用指标)
6. [自动检测规则](#6-自动检测规则)
7. [人工确认流程](#7-人工确认流程)
8. [自定义扩展方法](#8-自定义扩展方法)

---

## 1. 通信系统指标

### BER (误码率) - Bit Error Rate

- **常见变量名**: `BER`, `ber`, `bit_error_rate`, `ber_rate`, `BitErrorRate`
- **含义**: 传输过程中错误比特数与总比特数的比值，衡量数字通信系统可靠性的核心指标
- **单位**: 无量纲
- **典型范围**: 1e-6 ~ 1e-2
- **默认容差**: 相对容差 1e-6, 绝对容差 1e-9
- **检测规则**:
  - 变量名包含 `ber`, `BER`, `BitError`
  - 上下文出现 `biterr`, `bit_error`, `error_count`
  - 计算 pattern: `error_bits / total_bits`

### SNR (信噪比) - Signal-to-Noise Ratio

- **常见变量名**: `SNR`, `snr`, `SNR_dB`, `snr_dB`, `signal_to_noise`
- **含义**: 信号功率与噪声功率的比值，通常以 dB 表示
- **单位**: dB 或线性比值
- **典型范围**: -10 dB ~ 30 dB (通信系统常见)
- **默认容差**: dB 表示时绝对容差 0.01 dB；线性值时相对容差 1e-6, 绝对容差 1e-9
- **检测规则**:
  - 变量名包含 `snr`, `SNR_dB`, `signal_to_noise`
  - 上下文出现 `awgn`, `noise_power`, `signal_power`
  - 计算 pattern: `10*log10(signal_power/noise_power)`

### EbN0 (比特信噪比) - Energy per Bit to Noise Power Spectral Density Ratio

- **常见变量名**: `EbN0`, `ebn0`, `EbN0_dB`, `ebn0_dB`, `Eb_No`
- **含义**: 每比特能量与噪声功率谱密度的比值，用于衡量通信系统在归一化条件下的性能
- **单位**: dB 或线性比值
- **典型范围**: 0 dB ~ 20 dB
- **默认容差**: 相对容差 1e-6, 绝对容差 1e-9
- **检测规则**:
  - 变量名包含 `ebn0`, `EbN0`, `Eb_N0`
  - 上下文出现 `berawgn`, `berfading`
  - 常与 BER 曲线分析关联

### EsN0 (符号信噪比) - Energy per Symbol to Noise Power Spectral Density Ratio

- **常见变量名**: `EsN0`, `esn0`, `EsN0_dB`, `esn0_dB`
- **含义**: 每符号能量与噪声功率谱密度的比值
- **单位**: dB 或线性比值
- **典型范围**: 0 dB ~ 25 dB
- **默认容差**: 相对容差 1e-6, 绝对容差 1e-9
- **检测规则**:
  - 变量名包含 `esn0`, `EsN0`
  - 与 EbN0 存在转换关系: EsN0 = EbN0 + 10*log10(k)，k 为每符号比特数

### PER (误包率) - Packet Error Rate

- **常见变量名**: `PER`, `per`, `packet_error_rate`, `PER_rate`
- **含义**: 错误数据包数与总数据包数的比值
- **单位**: 无量纲
- **典型范围**: 1e-4 ~ 1e-1
- **默认容差**: 相对容差 1e-6, 绝对容差 1e-9
- **检测规则**:
  - 变量名包含 `per`, `PER`, `PacketError`
  - 上下文出现 `packet`, `frame_error`, `CRC`
  - 计算 pattern: `error_packets / total_packets`

### FER (帧错误率) - Frame Error Rate

- **常见变量名**: `FER`, `fer`, `frame_error_rate`, `FER_rate`
- **含义**: 错误帧数与总帧数的比值
- **单位**: 无量纲
- **典型范围**: 1e-4 ~ 1e-1
- **默认容差**: 相对容差 1e-6, 绝对容差 1e-9
- **检测规则**:
  - 变量名包含 `fer`, `FER`, `FrameError`
  - 上下文出现 `frame`, `frame_check`, `CRC_error`

### 频谱效率 - Spectral Efficiency

- **常见变量名**: `spectral_efficiency`, `SE`, `spec_eff`, `bps_per_hz`
- **含义**: 单位带宽内的数据传输速率，衡量频谱利用率
- **单位**: bit/s/Hz
- **典型范围**: 0.5 ~ 10 bit/s/Hz
- **默认容差**: 相对容差 1e-6, 绝对容差 1e-9
- **检测规则**:
  - 变量名包含 `spectral`, `spec_eff`, `SE`
  - 计算 pattern: `data_rate / bandwidth`

### 吞吐量 - Throughput

- **常见变量名**: `throughput`, `Throughput`, `thrpt`, `data_rate`, `effective_rate`
- **含义**: 系统实际传输的有效数据速率
- **单位**: bit/s, Mbps, Gbps
- **典型范围**: 取决于系统规模
- **默认容差**: 相对容差 1e-6, 绝对容差 1e-9
- **检测规则**:
  - 变量名包含 `throughput`, `thrpt`, `data_rate`
  - 常与延迟、丢包率等配合使用

### 时延 - Latency/Delay

- **常见变量名**: `latency`, `delay`, `Latency`, `Delay`, `RTT`, `rtt`, `end_to_end_delay`
- **含义**: 数据从发送端到接收端的传输时间
- **单位**: 秒 (s), 毫秒 (ms)
- **典型范围**: 1 ms ~ 1000 ms (取决于应用场景)
- **默认容差**: 绝对容差 1e-3 s
- **检测规则**:
  - 变量名包含 `latency`, `delay`, `RTT`
  - 计算 pattern: `receive_time - send_time`

---

## 2. 信号处理指标

### PSD (功率谱密度) - Power Spectral Density

- **常见变量名**: `PSD`, `psd`, `power_spectral_density`, `Pxx`, `pxx`
- **含义**: 信号功率在频域的分布密度
- **单位**: dB/Hz 或 W/Hz
- **典型范围**: -100 dB/Hz ~ 0 dB/Hz
- **默认容差**: 相对容差 1e-6, 绝对容差 1e-9
- **检测规则**:
  - 变量名包含 `psd`, `PSD`, `Pxx`, `power_spectrum`
  - 上下文出现 `pwelch`, `periodogram`, `fft`
  - 常与频谱分析函数关联

### MSE (均方误差) - Mean Square Error

- **常见变量名**: `MSE`, `mse`, `mean_square_error`, `mse_val`, `MSE_val`
- **含义**: 预测值与真实值差值的平方的均值
- **单位**: 与被测变量单位相同（平方）
- **典型范围**: 1e-10 ~ 1.0
- **默认容差**: 相对容差 1e-8, 绝对容差 1e-12
- **检测规则**:
  - 变量名包含 `mse`, `MSE`, `MeanSquare`
  - 计算 pattern: `mean((y_true - y_pred).^2)`
  - 常见于滤波、估计、拟合场景

### RMSE (均方根误差) - Root Mean Square Error

- **常见变量名**: `RMSE`, `rmse`, `root_mean_square_error`, `RMS_error`
- **含义**: MSE 的平方根，与原始数据同量纲
- **单位**: 与被测变量单位相同
- **典型范围**: 1e-5 ~ 1.0
- **默认容差**: 相对容差 1e-8, 绝对容差 1e-12
- **检测规则**:
  - 变量名包含 `rmse`, `RMSE`, `RootMean`
  - 计算 pattern: `sqrt(mean((y_true - y_pred).^2))`
  - 常与 MSE 配对出现

### 相关系数 - Correlation Coefficient

- **常见变量名**: `corr_coef`, `r`, `R`, `correlation`, `pearson_r`, `corr`
- **含义**: 衡量两个变量线性相关程度的指标
- **单位**: 无量纲
- **典型范围**: -1.0 ~ 1.0
- **默认容差**: 绝对容差 1e-10
- **注意**: `r`、`R` 命名过短，只能作为弱线索，不能单独作为判定依据
- **检测规则**:
  - 变量名包含 `corr`, `r`, `R`, `pearson`
  - 上下文出现 `corrcoef`, `corr`, `pearson`
  - 值域严格在 [-1, 1] 范围内

### 失真度 - Distortion

- **常见变量名**: `distortion`, `THD`, `thd`, `distortion_ratio`
- **含义**: 信号相对于理想信号的失真程度
- **单位**: dB 或百分比 (%)
- **典型范围**: 0.01% ~ 10% 或 -80 dB ~ -20 dB
- **默认容差**: 相对容差 1e-6, 绝对容差 1e-9
- **检测规则**:
  - 变量名包含 `distort`, `THD`
  - 上下文出现 `harmonic`, `nonlinear`
  - 常见于音频、通信信号质量评估

---

## 3. 控制系统指标

### 超调量 - Overshoot (Mp)

- **常见变量名**: `Mp`, `overshoot`, `Overshoot`, `Mp_percent`, `percent_overshoot`
- **含义**: 阶跃响应中输出超过稳态值的最大百分比
- **单位**: 百分比 (%)
- **典型范围**: 0% ~ 50%
- **默认容差**: 绝对容差 0.1%
- **检测规则**:
  - 变量名包含 `overshoot`, `Mp`
  - 上下文出现 `step`, `stepinfo`, `step_response`
  - 计算 pattern: `(max(y) - final_value) / final_value * 100`

### 上升时间 - Rise Time (tr)

- **常见变量名**: `tr`, `rise_time`, `RiseTime`, `tr_val`
- **含义**: 阶跃响应从稳态值的 10% 上升到 90% 所需时间
- **单位**: 秒 (s)
- **典型范围**: 0.001 s ~ 100 s
- **默认容差**: 绝对容差 1e-3 s
- **检测规则**:
  - 变量名包含 `rise_time`, `tr`
  - 上下文出现 `stepinfo`, `step`, `step_response`
  - 常与其他时域指标配合使用

### 调节时间 - Settling Time (ts)

- **常见变量名**: `ts`, `settling_time`, `SettlingTime`, `ts_val`
- **含义**: 阶跃响应进入并保持在稳态值 ±2% (或 ±5%) 范围内所需时间
- **单位**: 秒 (s)
- **典型范围**: 0.01 s ~ 100 s
- **默认容差**: 绝对容差 1e-3 s
- **检测规则**:
  - 变量名包含 `settling`, `ts`
  - 上下文出现 `stepinfo`, `step`, `step_response`
  - 需指定误差带 (通常 2% 或 5%)

### 稳态误差 - Steady-state Error (ess)

- **常见变量名**: `ess`, `steady_state_error`, `SteadyStateError`, `ess_val`
- **含义**: 系统稳态输出与期望输出之间的差值
- **单位**: 与被控量同单位
- **典型范围**: 接近 0 (理想情况)
- **默认容差**: 相对容差 1e-6
- **检测规则**:
  - 变量名包含 `ess`, `steady_state`, `SteadyStateError`
  - 上下文出现 `dcgain`, `stepinfo`
  - 计算 pattern: `abs(final_value - desired_value)`

### 相位裕度 - Phase Margin

- **常见变量名**: `PM`, `phase_margin`, `PhaseMargin`, `Pm`, `pm`
- **含义**: 系统在增益交叉频率处，相位距离不稳定边界（-180°）的裕量
- **单位**: 度 (degree)
- **典型范围**: 30° ~ 90° (良好稳定裕度)
- **默认容差**: 绝对容差 0.1°
- **检测规则**:
  - 变量名包含 `phase_margin`, `PM`, `Pm`
  - 上下文出现 `margin`, `bode`, `nyquist`
  - 常与增益裕度配合使用

### 增益裕度 - Gain Margin

- **常见变量名**: `GM`, `gain_margin`, `GainMargin`, `Gm`, `gm`
- **含义**: 系统在相位交叉频率处，增益距离不稳定边界的裕量
- **单位**: dB 或倍数（比较前需统一）
- **典型范围**: 6 dB ~ 20 dB (良好稳定裕度)
- **默认容差**: dB 表示时绝对容差 0.01 dB；倍率表示时相对容差 1e-6
- **检测规则**:
  - 变量名包含 `gain_margin`, `GM`, `Gm`
  - 上下文出现 `margin`, `bode`, `nyquist`
  - 常与相位裕度配合使用

---

## 4. 图像处理指标

### PSNR (峰值信噪比) - Peak Signal-to-Noise Ratio

- **常见变量名**: `PSNR`, `psnr`, `psnr_val`, `peak_snr`
- **含义**: 衡量图像质量的指标，基于 MSE 计算
- **单位**: dB
- **典型范围**: 20 dB ~ 50 dB
- **默认容差**: 绝对容差 0.1 dB
- **检测规则**:
  - 变量名包含 `psnr`, `PSNR`
  - 上下文出现 `immse`, `psnr`, `imquality`
  - 计算 pattern: `10 * log10(MAX^2 / MSE)`

### SSIM (结构相似性) - Structural Similarity Index

- **常见变量名**: `SSIM`, `ssim`, `ssim_val`, `ssim_index`
- **含义**: 衡量两幅图像结构相似程度的指标，考虑亮度、对比度和结构
- **单位**: 无量纲 (0 ~ 1)
- **典型范围**: 0.5 ~ 1.0 (高质量图像 > 0.9)
- **默认容差**: 绝对容差 1e-4
- **检测规则**:
  - 变量名包含 `ssim`, `SSIM`
  - 上下文出现 `ssim`, `StructuralSimilarity`
  - 值域严格在 [0, 1] 范围内

### 准确率 - Accuracy

- **常见变量名**: `accuracy`, `Accuracy`, `acc`, `ACC`, `accuracy_rate`
- **含义**: 正确分类的样本数与总样本数的比值
- **单位**: 无量纲 (0 ~ 1) 或百分比
- **典型范围**: 0.5 ~ 1.0
- **默认容差**: 绝对容差 1e-6
- **检测规则**:
  - 变量名包含 `accuracy`, `acc`
  - 上下文出现 `confusionmat`, `classification`
  - 计算 pattern: `(TP + TN) / (TP + TN + FP + FN)`

### 召回率 - Recall

- **常见变量名**: `recall`, `Recall`, `sensitivity`, `TPR`, `true_positive_rate`
- **含义**: 正例中被正确识别的比例
- **单位**: 无量纲 (0 ~ 1)
- **典型范围**: 0 ~ 1.0
- **默认容差**: 绝对容差 1e-6
- **检测规则**:
  - 变量名包含 `recall`, `sensitivity`, `TPR`
  - 上下文出现 `confusionmat`, `precision_recall`
  - 计算 pattern: `TP / (TP + FN)`

### F1分数 - F1 Score

- **常见变量名**: `F1`, `f1`, `f1_score`, `F1_score`, `f_measure`
- **含义**: 准确率和召回率的调和平均值
- **单位**: 无量纲 (0 ~ 1)
- **典型范围**: 0 ~ 1.0
- **默认容差**: 绝对容差 1e-6
- **检测规则**:
  - 变量名包含 `f1`, `F1`, `f_measure`
  - 计算 pattern: `2 * precision * recall / (precision + recall)`
  - 常与 precision, recall 配对出现

---

## 5. 通用指标

### 计算时间 - Elapsed Time / Runtime

- **常见变量名**: `elapsed_time`, `runtime`, `exec_time`, `t_elapsed`, `wall_time`, `cpu_time`
- **含义**: 程序或函数执行所需的时间
- **单位**: 秒 (s)
- **典型范围**: 取决于问题规模
- **默认容差**: 无固定容差 (仅作参考)
- **检测规则**:
  - 变量名包含 `time`, `elapsed`, `runtime`
  - 上下文出现 `tic`, `toc`, `timeit`, `cputime`
  - 注意区分 wall time 和 CPU time

### 内存占用 - Memory Usage

- **常见变量名**: `memory_usage`, `mem_usage`, `memory`, `mem`, `peak_memory`
- **含义**: 程序执行过程中占用的内存量
- **单位**: 字节 (bytes), MB, GB
- **典型范围**: 取决于问题规模
- **默认容差**: 无固定容差 (仅作参考)
- **检测规则**:
  - 变量名包含 `memory`, `mem_usage`
  - 上下文出现 `memory`, `whos`, `sizeof`
  - 常与性能优化相关

### 迭代次数 - Iteration Count

- **常见变量名**: `iterations`, `iter`, `n_iter`, `iter_count`, `max_iter`, `num_iterations`
- **含义**: 算法收敛或达到终止条件所需的迭代次数
- **单位**: 次 (整数)
- **典型范围**: 取决于算法和问题
- **默认容差**: 无容差要求 (整数比较)
- **检测规则**:
  - 变量名包含 `iter`, `iteration`
  - 上下文出现 `for`, `while` 循环, 优化算法
  - 用于判断算法收敛性

---

## 6. 自动检测规则

### 6.1 变量名模式匹配

系统通过以下正则表达式模式自动识别关键指标:

```regex
# 通信系统指标
(?i)(ber|bit_error|biterror)
(?i)(snr|signal.*noise|signaltonoise)
(?i)(ebn0|eb_n0|ebno)
(?i)(esn0|es_n0|esno)
(?i)(per|packet.*error|packeterror)
(?i)(fer|frame.*error|frameerror)

# 信号处理指标
(?i)(psd|power.*spectral|pxx)
(?i)(mse|mean.*square.*error)
(?i)(rmse|root.*mean.*square)
(?i)(corr|correlation|pearson)
(?i)(distort|thd)

# 控制系统指标
(?i)(overshoot|mp_percent)
(?i)(rise.*time|tr_val|risetime)
(?i)(settling.*time|ts_val|settlingtime)
(?i)(ess|steady.*state.*error)
(?i)(phase.*margin|pm\b)
(?i)(gain.*margin|gm\b)

# 图像处理指标
(?i)(psnr|peak.*snr)
(?i)(ssim|structural.*similarity)
(?i)(accuracy|acc\b)
(?i)(recall|sensitivity|tpr)
(?i)(f1|f1_score|f_measure)

# 通用指标
(?i)(elapsed.*time|runtime|exec.*time|wall.*time)
(?i)(memory.*usage|mem_usage)
(?i)(iter|iteration.*count)
```

### 6.2 上下文线索检测

除了变量名模式，系统还会检测以下上下文线索:

| 指标类别 | 相关函数/上下文 |
|---------|----------------|
| 通信指标 | `awgn`, `biterr`, `symerr`, `berawgn`, `berfading` |
| 信号处理 | `fft`, `pwelch`, `periodogram`, `filter`, `xcorr` |
| 控制系统 | `step`, `stepinfo`, `bode`, `nyquist`, `margin`, `lsim` |
| 图像处理 | `immse`, `psnr`, `ssim`, `imabsdiff`, `confusionmat` |

### 6.3 计算模式识别

系统会识别常见的计算模式来推断指标类型:

```matlab
% BER 计算模式
ber = bit_errors / total_bits;

% MSE 计算模式
mse = mean((y_true - y_pred).^2);

% PSNR 计算模式
psnr = 10 * log10(max_val^2 / mse);

% 超调量计算模式
overshoot = (max(y) - steady_state) / steady_state * 100;
```

---

## 7. 人工确认流程

当自动检测无法确定变量类型时，按以下流程进行人工确认:

### 7.1 确认步骤

1. **阅读源码注释**: 检查变量声明或计算处的注释说明
2. **分析计算公式**: 根据计算方式推断指标类型
3. **检查输入输出**: 分析变量的输入来源和输出用途
4. **参考文档**: 查阅相关算法或函数的官方文档
5. **咨询领域专家**: 如仍无法确定，向领域专家咨询

### 7.2 确认记录模板

```markdown
### 变量确认记录

**变量名**: [变量名]
**所在文件**: [文件路径:行号]
**自动检测结果**: [检测结果或"未知"]
**人工确认结果**: [确认的指标类型]
**确认依据**: [说明确认理由]
**确认人**: [确认人姓名]
**确认日期**: [YYYY-MM-DD]
```

### 7.3 确认优先级

| 优先级 | 条件 |
|-------|------|
| 高 | 关键输出结果，直接影响功能测试结论 |
| 中 | 中间计算结果，可能影响最终结果精度 |
| 低 | 辅助变量，仅用于调试或日志 |

---

## 8. 自定义扩展方法

### 8.1 添加新指标

在 `key_variables_glossary.md` 中按以下格式添加新指标:

```markdown
### [指标名] (English Name)

- **常见变量名**: `[变量名1]`, `[变量名2]`, ...
- **含义**: [简要描述]
- **单位**: [单位说明]
- **典型范围**: [范围说明]
- **默认容差**: [相对/绝对容差]
- **检测规则**: [命名模式、上下文线索]
```

### 8.2 更新检测规则

1. **添加正则表达式**: 在自动检测规则中添加新的匹配模式
2. **添加上下文线索**: 在上下文线索表中添加相关函数
3. **更新计算模式**: 如有新的计算模式，添加到模式识别库

### 8.3 自定义容差配置

可在项目级别配置自定义容差:

```yaml
# tolerance_config.yaml
tolerances:
  communication:
    BER:
      relative: 1e-6
      absolute: 1e-9
    SNR:
      relative: 1e-6
      absolute: 1e-9

  signal_processing:
    MSE:
      relative: 1e-8
      absolute: 1e-12
    RMSE:
      relative: 1e-8
      absolute: 1e-12

  control_systems:
    time_metrics:
      absolute: 1e-3

  image_processing:
    PSNR:
      absolute: 0.1
```

### 8.4 扩展流程

1. 在词汇表中添加新指标定义
2. 更新自动检测规则
3. 添加测试用例测试检测效果
4. 更新相关文档和示例

---

## 附录: 指标分类汇总表

| 类别 | 指标 | 变量名示例 | 默认容差 |
|-----|------|----------|---------|
| 通信系统 | BER | `ber`, `BER` | 相对 1e-6, 绝对 1e-9 |
| 通信系统 | SNR | `snr`, `SNR_dB` | dB 时绝对 0.01 dB；线性值时相对 1e-6, 绝对 1e-9 |
| 通信系统 | EbN0 | `ebn0`, `EbN0` | 相对 1e-6, 绝对 1e-9 |
| 通信系统 | EsN0 | `esn0`, `EsN0` | 相对 1e-6, 绝对 1e-9 |
| 通信系统 | PER | `per`, `PER` | 相对 1e-6, 绝对 1e-9 |
| 通信系统 | FER | `fer`, `FER` | 相对 1e-6, 绝对 1e-9 |
| 通信系统 | 频谱效率 | `spectral_efficiency` | 相对 1e-6, 绝对 1e-9 |
| 通信系统 | 吞吐量 | `throughput` | 相对 1e-6, 绝对 1e-9 |
| 通信系统 | 时延 | `latency`, `delay` | 绝对 1e-3 |
| 信号处理 | PSD | `psd`, `Pxx` | 相对 1e-6, 绝对 1e-9 |
| 信号处理 | MSE | `mse`, `MSE` | 相对 1e-8, 绝对 1e-12 |
| 信号处理 | RMSE | `rmse`, `RMSE` | 相对 1e-8, 绝对 1e-12 |
| 信号处理 | 相关系数 | `corr_coef`, `r` | 绝对 1e-10 |
| 信号处理 | 失真度 | `distortion`, `THD` | 相对 1e-6, 绝对 1e-9 |
| 控制系统 | 超调量 | `Mp`, `overshoot` | 绝对 0.1% |
| 控制系统 | 上升时间 | `tr`, `rise_time` | 绝对 1e-3 |
| 控制系统 | 调节时间 | `ts`, `settling_time` | 绝对 1e-3 |
| 控制系统 | 稳态误差 | `ess` | 相对 1e-6 |
| 控制系统 | 相位裕度 | `PM`, `phase_margin` | 绝对 0.1° |
| 控制系统 | 增益裕度 | `GM`, `gain_margin` | dB 时绝对 0.01 dB；倍率时相对 1e-6 |
| 图像处理 | PSNR | `psnr`, `PSNR` | 绝对 0.1 dB |
| 图像处理 | SSIM | `ssim`, `SSIM` | 绝对 1e-4 |
| 图像处理 | 准确率 | `accuracy`, `acc` | 绝对 1e-6 |
| 图像处理 | 召回率 | `recall`, `TPR` | 绝对 1e-6 |
| 图像处理 | F1分数 | `f1`, `F1` | 绝对 1e-6 |
| 通用 | 计算时间 | `elapsed_time`, `runtime` | 无固定 |
| 通用 | 内存占用 | `memory_usage` | 无固定 |
| 通用 | 迭代次数 | `iterations`, `iter` | 无 (整数) |

---

*文档版本: 1.1*
*最后更新: 2026-04-27*
