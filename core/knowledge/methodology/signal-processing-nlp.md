# 信号处理与自然语言处理方法论

> 本文件提供数学建模竞赛中常用的信号处理方法（FFT 频域分析、小波去噪、滤波）与自然语言处理方法（TF-IDF、Word2Vec、LDA 主题模型），覆盖两条完整建模链路：信号去噪→频谱分析、文本预处理→向量化→主题建模。

---

## 一、方法选择决策树

```
输入数据
├── 数值型时间序列 / 波形（信号）？
│   ├── 周期性分析 / 主导频率 → FFT / 功率谱
│   ├── 去噪（信噪比低）→ 小波阈值去噪（pywt）
│   ├── 提取低频趋势 → 低通滤波（Butterworth）
│   ├── 提取高频突变/边缘 → 高通滤波
│   ├── 非平稳 + 时频局部化 → 小波变换 / 短时傅里叶（STFT）
│   └── 平稳信号 → 直接 FFT
└── 文本（自然语言）？
    ├── 关键词提取 / 文本向量化 → TF-IDF
    │   ├── 高维稀疏特征 → 接线性模型/LDA
    │   └── 匹配/检索 → 余弦相似度
    ├── 语义表示（词级）→ Word2Vec
    │   └── 中文需先分词（jieba）
    └── 主题挖掘 / 文档聚类 → LDA 主题模型
        └── 需先定主题数（困惑度/一致性）
```

---

## 二、信号处理

### 2.1 傅里叶变换（FFT）

**原理**：时域信号 x(t) 可分解为不同频率正弦波的叠加，FFT 给出各频率分量的幅度与相位。

```
X(f) = ∫ x(t)·e^(-j2πft) dt
离散:  X_k = Σₙ xₙ·e^(-j2πkn/N)
```

**代码要点**：

```python
import numpy as np
import matplotlib.pyplot as plt

def fft_analysis(signal, fs):
    """
    signal: 时域信号数组；fs: 采样频率(Hz)
    返回频率轴与单边幅度谱，识别主导频率
    """
    N = len(signal)
    yf = np.fft.rfft(signal)                 # 单边谱（去 Nyquist 以上）
    freqs = np.fft.rfftfreq(N, d=1.0 / fs)
    amp = np.abs(yf) / N                     # 幅度
    amp[1:] *= 2                             # 单边幅度修正（保留能量）

    # 主导频率（剔除直流）
    idx = np.argsort(amp[1:])[::-1]  # 从大到小
    print("前三主导频率(Hz):", freqs[1:][idx[:3]].round(3))
    return freqs, amp
```

### 2.2 小波去噪（pywt）

**原理**：小波变换同时提供时间与频率的局部化信息，是多分辨分析。去噪时对高频细节系数做**软/硬阈值**处理，再重构，比傅里叶更适合非平稳信号。

```python
import numpy as np
import pywt

def wavelet_denoise(signal, wavelet='db4', level=3, mode='soft'):
    """
    signal: 1D 信号
    mode: 'soft' 软阈值（平滑）| 'hard' 硬阈值（保留尖峰）
    """
    coeffs = pywt.wavedec(signal, wavelet, level=level)

    # 用第一层细节系数估计噪声 σ，采用通用阈值
    sigma = np.median(np.abs(coeffs[-1])) / 0.6745
    threshold = sigma * np.sqrt(2 * np.log(len(signal)))

    denoised_coeffs = [coeffs[0]]            # 近似系数不动
    for c in coeffs[1:]:
        if mode == 'soft':
            c_new = pywt.threshold(c, threshold, mode='soft')
        else:
            c_new = pywt.threshold(c, threshold, mode='hard')
        denoised_coeffs.append(c_new)

    return pywt.waverec(denoised_coeffs, wavelet)
```

### 2.3 滤波（低通/高通）

**原理**：低通滤波保留低频成分（去高频噪声/平滑），高通滤波保留高频成分（提取突变）。常用 Butterworth 滤波器（通带平坦）。

```python
import numpy as np
from scipy.signal import butter, filtfilt

def butter_filter(signal, cutoff, fs, btype='low', order=4):
    """
    btype: 'low' 低通 | 'high' 高通 | 'band' 带通
    cutoff: 截止频率(Hz)，带通时为 [low, high]
    """
    nyq = 0.5 * fs
    if isinstance(cutoff, (list, tuple)):
        Wn = [c / nyq for c in cutoff]
    else:
        Wn = cutoff / nyq
    b, a = butter(order, Wn, btype=btype)
    return filtfilt(b, a, signal)            # 零相位滤波
```

---

## 三、自然语言处理（NLP）

### 3.1 文本预处理

```python
import re
import jieba

def preprocess_text(doc):
    """中文文本清洗与分词"""
    doc = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', doc)  # 去标点/符号
    doc = doc.lower()
    words = [w.strip() for w in jieba.cut(doc) if len(w.strip()) > 1]
    return words  # 返回词列表
```

### 3.2 TF-IDF 向量化

**原理**：TF（词频）× IDF（逆文档频率），衡量词对单篇文档的区分度。

```
tfidf(t,d) = tf(t,d) × log( N / (1 + df(t)) )
```

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def tfidf_pipeline(docs):
    """
    docs: 原始文本列表（分词后以空格连接的字符串或词列表）
    """
    vectorizer = TfidfVectorizer(
        token_pattern=r'(?u)\b\w+\b',
        max_features=5000,
        min_df=2, max_df=0.9
    )
    X = vectorizer.fit_transform(docs)
    print("词表大小:", len(vectorizer.get_feature_names_out()))
    print("TF-IDF 矩阵形状:", X.shape)

    # 文档间相似度
    sim = cosine_similarity(X)
    return X, vectorizer, sim
```

### 3.3 Word2Vec 词向量

**原理**：用神经网络在大量语料上学习词的稠密向量，使语义相近的词向量距离近（CBOW / Skip-gram 两种训练方式）。可做「词类比」「相似词」。

```python
from gensim.models import Word2Vec

def train_word2vec(sentences, vector_size=100, window=5, min_count=2):
    """
    sentences: 分词后的词列表的列表 [[w1,w2,...], ...]
    """
    model = Word2Vec(
        sentences, vector_size=vector_size,
        window=window, min_count=min_count, workers=4, seed=42
    )
    # 相似词
    try:
        print("与“金融”最相似的词:", model.wv.most_similar('金融', topn=5))
    except KeyError:
        pass
    return model
```

### 3.4 LDA 主题模型

**原理**：LDA 假设每篇文档是若干主题的混合（θ_d），每个主题是词表上的概率分布（φ_k）。用变分推断/吉布斯采样估计，从而得到「文档-主题」「主题-词」分布。

```python
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

def lda_topic_model(docs, n_topics=5, n_top_words=10):
    """
    docs: 文本列表；先做词频矩阵，再 LDA
    主题数选择可用困惑度(perplexity)或主题一致性
    """
    cv = CountVectorizer(token_pattern=r'(?u)\b\w+\b', max_df=0.9, min_df=2)
    X = cv.fit_transform(docs)
    feature_names = cv.get_feature_names_out()

    lda = LatentDirichletAllocation(
        n_components=n_topics, random_state=42, max_iter=50
    )
    doc_topic = lda.fit_transform(X)

    # 主题关键词
    topics = []
    for topic_dist in lda.components_:
        idx = topic_dist.argsort()[-n_top_words:][::-1]
        topics.append(feature_names[idx].tolist())
    return lda, doc_topic, topics
```

主题数选择（困惑度曲线）：

```python
def select_topic_num(docs, k_range=range(2, 12)):
    from sklearn.feature_extraction.text import CountVectorizer
    X = CountVectorizer(token_pattern=r'(?u)\b\w+\b').fit_transform(docs)
    perps = []
    for k in k_range:
        lda = LatentDirichletAllocation(n_components=k, random_state=42, max_iter=30)
        lda.fit(X)
        perps.append(lda.perplexity(X))
    return list(k_range), perps
```

---

## 四、建模步骤（两条完整链路）

### 4.1 信号去噪 → 频谱分析

```
1. 采集信号，确定采样频率 fs（满足 Nyquist）
2. 可视化原始时域波形
3. 小波/滤波去噪（记录小波基与阈值）
4. FFT 得到幅度谱 / 功率谱
5. 识别主导频率与谐波结构
6. 结合物理背景解释频率来源
```

### 4.2 文本预处理 → 向量化 → 主题建模

```
1. 语料清洗（去 HTML/标点/停用词/低频词）
2. 中文分词（jieba）；英文去停用词 + 词干化
3. TF-IDF / Count 向量化
4. 主题数选择（困惑度/一致性曲线）
5. LDA 得到文档-主题分布与主题-词分布
6. 主题命名与结果解读
```

---

## 五、适用条件

| 方法 | 适用条件 |
|------|---------|
| FFT | 平稳周期信号，强调频率成分，频率不随时间变化 |
| 小波变换/去噪 | 非平稳信号，需要时频局部化，信噪比低 |
| 滤波 | 信号与噪声在频域可区分，系统近似线性 |
| TF-IDF | 只依赖词频统计，任务偏关键词提取/检索/浅层语义 |
| Word2Vec | 语料较大（词级语义与类比效果更佳），需要词向量表示 |
| LDA | 文档可视为主题混合、主题相对独立、语料规模中等以上 |

---

## 六、竞赛常见场景

| 题型 | 题型含义 | 典型场景 | 推荐方法组合 |
|------|---------|---------|-------------|
| A | 物理建模 | 振动/波谱信号分析、共振频率识别 | FFT + 功率谱 + 小波时频图 |
| B | 实验设计 | 传感器信号去噪后比对实验组 | 小波去噪 + 低通滤波 + 方差分析 |
| C | 数据分析 | 电商评论/舆情文本挖掘 | 分词 + TF-IDF + LDA 主题聚类 |
| C | 数据分析 | 新闻/文献相似度、检索 | TF-IDF + 余弦相似度 / Word2Vec |
| D | 优化调度 | 故障信号特征提取后优化维修排程 | 小波特征 + 分类 + 整数规划 |
| E | 交叉学科 | 生物电信号(EEG/ECG) × 医学 | 带通滤波 + 小波去噪 + 频谱/时频分析 |

---

## 七、常见陷阱与解决方案

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| FFT 出现频谱泄漏 | 非整周期截断 | 加窗（Hanning/Hamming） |
| 混叠（假频率） | 采样率不足（<2f_max） | 提高 fs 或先抗混叠低通滤波 |
| 小波去噪过度平滑 | 阈值过大 | 用噪声自适应阈值（σ·√(2lnN)），对比软/硬阈值 |
| LDA 主题词无意义 | 未去停用词/低频词 | 停用词表 + min_df 过滤，主题数调参 |
| 主题数选择主观 | 单看困惑度单调 | 结合主题一致性(coherence)与领域可解释性 |
| Word2Vec 效果差 | 语料太小 | 语料不足时用 TF-IDF 或预训练词向量 |
| 中文未分词直接向量化 | 空格分词失效 | 先 jieba 分词，再向量化 |

---

## 八、参考资源

- 教材：《信号与系统》（Oppenheim）、《统计自然语言处理》（宗成庆）
- Python 库：`numpy.fft` / `scipy.signal`（FFT/滤波）、`pywt`（小波）、`sklearn.feature_extraction.text`（TF-IDF）、`sklearn.decomposition`（LDA）、`gensim`（Word2Vec/LDA）、`jieba`（分词）
- 扩展：`librosa`（音频）、`transformers`（预训练模型）

### 检查清单

- [ ] 采样率满足 Nyquist（fs > 2f_max）
- [ ] FFT 已加窗处理，频率轴与幅度归一化正确
- [ ] 小波基与阈值选择有依据（报告 σ 与阈值）
- [ ] 文本已去除停用词、低频词与标点，中文已分词
- [ ] LDA 主题数由困惑度/一致性曲线确定，主题可解释
- [ ] Word2Vec 与 TF-IDF 的适用场景区分正确
- [ ] 结果能回溯到原始信号/语料，随机种子固定 42