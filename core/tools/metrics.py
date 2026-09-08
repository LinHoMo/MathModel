#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""metrics.py — 指标计算工具

提供各类数学/统计指标计算函数，供其他模块调用。

用法（作为库）:
    from metrics import accuracy, f1_score, rmse

零第三方依赖。"""
from __future__ import annotations

import math
from typing import Sequence


def accuracy(predictions: Sequence, ground_truth: Sequence) -> float:
    """计算分类准确率。"""
    if len(predictions) != len(ground_truth):
        raise ValueError("长度不一致")
    if len(predictions) == 0:
        return 0.0
    correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
    return correct / len(predictions)


def precision(predictions: Sequence, ground_truth: Sequence, positive=1) -> float:
    """计算精确率。"""
    tp = sum(1 for p, g in zip(predictions, ground_truth) if p == positive and g == positive)
    fp = sum(1 for p, g in zip(predictions, ground_truth) if p == positive and g != positive)
    return tp / (tp + fp) if (tp + fp) > 0 else 0.0


def recall(predictions: Sequence, ground_truth: Sequence, positive=1) -> float:
    """计算召回率。"""
    tp = sum(1 for p, g in zip(predictions, ground_truth) if p == positive and g == positive)
    fn = sum(1 for p, g in zip(predictions, ground_truth) if p != positive and g == positive)
    return tp / (tp + fn) if (tp + fn) > 0 else 0.0


def f1_score(predictions: Sequence, ground_truth: Sequence, positive=1) -> float:
    """计算 F1 分数。"""
    p = precision(predictions, ground_truth, positive)
    r = recall(predictions, ground_truth, positive)
    return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


def rmse(predictions: Sequence[float], ground_truth: Sequence[float]) -> float:
    """计算均方根误差。"""
    if len(predictions) != len(ground_truth):
        raise ValueError("长度不一致")
    if len(predictions) == 0:
        return 0.0
    mse = sum((p - g) ** 2 for p, g in zip(predictions, ground_truth)) / len(predictions)
    return math.sqrt(mse)


def mae(predictions: Sequence[float], ground_truth: Sequence[float]) -> float:
    """计算平均绝对误差。"""
    if len(predictions) != len(ground_truth):
        raise ValueError("长度不一致")
    if len(predictions) == 0:
        return 0.0
    return sum(abs(p - g) for p, g in zip(predictions, ground_truth)) / len(predictions)


def r_squared(predictions: Sequence[float], ground_truth: Sequence[float]) -> float:
    """计算 R² 决定系数。"""
    if len(predictions) != len(ground_truth):
        raise ValueError("长度不一致")
    if len(predictions) == 0:
        return 0.0
    mean_gt = sum(ground_truth) / len(ground_truth)
    ss_res = sum((p - g) ** 2 for p, g in zip(predictions, ground_truth))
    ss_tot = sum((g - mean_gt) ** 2 for g in ground_truth)
    return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0


def correlation(x: Sequence[float], y: Sequence[float]) -> float:
    """计算皮尔逊相关系数。"""
    if len(x) != len(y) or len(x) == 0:
        return 0.0
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
    return cov / (std_x * std_y) if (std_x * std_y) > 0 else 0.0
