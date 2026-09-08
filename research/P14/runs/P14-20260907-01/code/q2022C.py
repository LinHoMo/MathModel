#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""q2022C.py — P14 实验：玻璃成分判别（artifact 2022_C/B1_F 冻结机制 M1–M4）.

数据溯源（executor-defined pilot dataset，随本文件 sha256 冻结溯源）：
  仓库无真实 2022_C 附件数据 → 合成成分数据集：3 类（高钾/铅钡/其他）×
  D=10 氧化物特征（SiO2, Na2O, CaO, ...），Dirichlet 类中心有区分度，
  RandomState(42)，每类 80/60/60（满足 A3 小样本）。
机制实现：M1 CLR（零值以 1e-6 替换后取对数）；M2 PCA（SVD）；
M3 K-means（k-means++ 初始化）；M4 Fisher LDA（合并协方差白化后近类均值）。
输出：stdout 严格 JSON {"metrics": {...}}。
"""
import json
import sys

import numpy as np

D = 10
CLS = ["high_k", "lead_barium", "other"]
COUNTS = [80, 60, 60]
CENTER = {
    "high_k": np.array([70, 2, 1, 8, 3, 5, 4, 3, 2, 2], dtype=float),
    "lead_barium": np.array([40, 2, 1, 5, 25, 10, 2, 8, 4, 3], dtype=float),
    "other": np.array([55, 8, 6, 9, 4, 6, 5, 3, 2, 2], dtype=float),
}


def make_data():
    rng = np.random.RandomState(42)
    X, y = [], []
    for ci, c in enumerate(CLS):
        base = CENTER[c] / CENTER[c].sum()
        for _ in range(COUNTS[ci]):
            conc = base * rng.uniform(0.7, 1.3, size=D)
            conc = conc + 1e-6
            x = rng.dirichlet(conc / conc.min() * 30.0) * 100.0
            X.append(x)
            y.append(ci)
    return np.array(X), np.array(y)


def clr(X):
    Z = np.where(X <= 0, 1e-6, X)
    g = np.exp(np.mean(np.log(Z), axis=1, keepdims=True))
    return np.log(Z / g)


def pca_fit(Z, var_keep=0.95):
    mu = Z.mean(axis=0)
    Xc = Z - mu
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    var = S ** 2
    keep = int(np.searchsorted(np.cumsum(var) / var.sum(), var_keep) + 1)
    keep = max(1, min(keep, Vt.shape[0]))
    return mu, Vt[:keep].T


def kmeans(X, k, seed=42, iters=50):
    rng = np.random.RandomState(seed)
    idx = [int(np.argmin(((X - X[i]) ** 2).sum(axis=1))) for i in [0]]
    centers = [X[idx[0]]]
    for _ in range(k - 1):
        d2 = np.min(((X[:, None, :] - np.array(centers)[None]) ** 2).sum(axis=2), axis=1)
        centers.append(X[int(rng.choice(len(X), p=d2 / d2.sum()))])
    centers = np.array(centers)
    labels = np.zeros(len(X), dtype=int)
    for _ in range(iters):
        d2 = ((X[:, None, :] - centers[None]) ** 2).sum(axis=2)
        new = d2.argmin(axis=1)
        if (new == labels).all():
            break
        labels = new
        for j in range(k):
            if (labels == j).any():
                centers[j] = X[labels == j].mean(axis=0)
    return labels


def best_map_accuracy(y, lab):
    """聚类准确率（多数票）：每个簇映射到簇内真实标签的众数，任意 K 均可用。"""
    pred = np.empty_like(y)
    for c in sorted(set(lab.tolist())):
        m = y[lab == c]
        if len(m) == 0:
            continue
        pred[lab == c] = np.bincount(m).argmax()
    return float((pred == y).mean()), pred


def silhouette(X, lab):
    d = ((X[:, None, :] - X[None]) ** 2).sum(axis=2)
    s = []
    for i in range(len(X)):
        same = lab == lab[i]
        if same.sum() <= 1:
            continue
        a = d[i][same].sum() / (same.sum() - 1)
        b = min(d[i][lab == c].mean() for c in set(lab.tolist()) if c != lab[i])
        s.append((b - a) / max(a, b))
    return float(np.mean(s)) if s else 0.0


def lda_fit_predict(Xtr, ytr, Xte):
    mus = [Xtr[ytr == c].mean(axis=0) for c in sorted(set(ytr.tolist()))]
    Sw = np.zeros((Xtr.shape[1], Xtr.shape[1]))
    for c in sorted(set(ytr.tolist())):
        Xc = Xtr[ytr == c] - mus[c]
        Sw += Xc.T @ Xc
    Sw += np.eye(Sw.shape[0]) * 1e-9
    W = np.linalg.inv(Sw)
    pred = []
    for x in Xte:
        scores = [-(x - m) @ W @ (x - m) for m in mus]
        pred.append(int(np.argmax(scores)))
    return np.array(pred)


def pipeline(X, y, use_clr, var_keep=0.85, k=3, seed=42, mask_tr=None, mask_te=None):
    F = clr(X) if use_clr else X
    if mask_tr is None:
        mu, W = pca_fit(F, var_keep)
        Z = (F - mu) @ W
        lab = kmeans(Z, k, seed)
        acc_km, pred = best_map_accuracy(y, lab)
        return {"acc": acc_km, "sil": silhouette(Z, lab), "pred": pred, "y": y}
    mu, W = pca_fit(F[mask_tr], var_keep)
    Ztr, Zte = (F[mask_tr] - mu) @ W, (F[mask_te] - mu) @ W
    pred = lda_fit_predict(Ztr, y[mask_tr], Zte)
    return {"acc": float((pred == y[mask_te]).mean())}


def run_ablation():
    X, y = make_data()
    with_clr = pipeline(X, y, True)
    without = pipeline(X, y, False)
    pred = with_clr["pred"]
    by_type = {CLS[ci]: float((pred[y == ci] == y[y == ci]).mean()) for ci in range(3)}
    return {"accuracy_with_clr": with_clr["acc"], "accuracy_without_clr": without["acc"],
            "silhouette_gap": with_clr["sil"] - without["sil"], "accuracy_by_type": by_type}


def run_sensitivity():
    X, y = make_data()
    F = clr(X)
    grid, best_k, best_acc = [], None, -1.0
    for k in range(2, 9):
        lab = kmeans(F, k, seed=42)
        acc, _ = best_map_accuracy(y, lab)
        grid.append({"K": k, "kmeans_acc": acc})
        if acc > best_acc:
            best_acc, best_k = acc, k
    comps = []
    best_c, best_ca = None, -1.0
    for vp in (0.70, 0.75, 0.80, 0.85, 0.90, 0.95):
        r = pipeline(X, y, True, var_keep=vp)
        comps.append({"var_keep": vp, "lda_acc": r["acc"]})
        if r["acc"] > best_ca:
            best_ca, best_c = r["acc"], vp
    return {"accuracy_grid": grid, "best_K": best_k, "best_kmeans_acc": best_acc,
            "lda_acc_grid": comps, "best_components": best_c, "best_lda_acc": best_ca}


def run_noise():
    X, y = make_data()
    rng = np.random.RandomState(42)
    curve = []
    for level in (0.01, 0.03, 0.05, 0.10):
        accs = []
        for _ in range(20):
            Xn = X * (1.0 + rng.normal(0, level, X.shape))
            Xn = np.clip(Xn, 1e-6, None)
            Xn = Xn / Xn.sum(axis=1, keepdims=True) * 100.0
            accs.append(pipeline(Xn, y, True, var_keep=0.85)["acc"])
        curve.append({"noise": level, "acc": float(np.mean(accs))})
    drop = curve[0]["acc"] - curve[-1]["acc"]
    return {"accuracy_noise_curve": curve, "accuracy_drop_at_10pct": drop}


def run_cv():
    X, y = make_data()
    rng = np.random.RandomState(42)
    # 分层 5 折：每类各自 shuffle 后切 5 份，测试折 = 各类同折号拼接，训练折 = 其余全部
    class_folds = {}
    for ci in sorted(set(y.tolist())):
        idx = np.where(y == ci)[0]
        rng.shuffle(idx)
        class_folds[ci] = np.array_split(idx, 5)
    accs = []
    for f in range(5):
        te = np.concatenate([class_folds[ci][f] for ci in class_folds])
        tr = np.concatenate([class_folds[ci][j] for ci in class_folds
                             for j in range(5) if j != f])
        r = pipeline(X, y, True, var_keep=0.85, mask_tr=tr, mask_te=te)
        accs.append(r["acc"])
    mean, std = float(np.mean(accs)), float(np.std(accs))
    return {"cv_accuracy_mean": mean, "cv_accuracy_std": std,
            "meets_85pct_target": bool(mean >= 0.85)}


EXPERIMENTS = {
    "EXP-2022C-C0-1": run_ablation,
    "EXP-2022C-C0-2": run_sensitivity,
    "EXP-2022C-C0-3": run_noise,
    "EXP-2022C-C1-1": run_ablation,
    "EXP-2022C-C1-2": run_sensitivity,
    "EXP-2022C-C1-3": run_noise,
    "EXP-2022C-C1-4": run_cv,
}

if __name__ == "__main__":
    exp = sys.argv[1]
    res = EXPERIMENTS[exp]()
    print(json.dumps({"experiment_id": exp, "metrics": res},
                     ensure_ascii=False, sort_keys=True))
