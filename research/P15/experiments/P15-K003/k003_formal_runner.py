#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P15-K003 正式实验生成器 — PREFLIGHT + 66 runs 全量生成。

复用预检测 6 题主模型定义（k003_problems.py），新增 2 道泛化题（2022_C/2024_A）。
每 run：表示文件 + run_model.py(seed) + output_mapping.json → harness 真实执行 → fidelity → manifest。

用法:
  py -3.12 k003_formal_runner.py preflight   # PREFLIGHT: 2020_B × 3臂 = 3 runs
  py -3.12 k003_formal_runner.py full         # 全量 66 runs
  py -3.12 k003_formal_runner.py status       # 查看已完成 runs 统计
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---- 路径 ----
REPO_ROOT = Path(__file__).resolve().parents[4]
FORMAL_DIR = Path(__file__).resolve().parent
RUNS_DIR = FORMAL_DIR / "runs"
BUNDLES_DIR = FORMAL_DIR / "bundles"
KEY_DIR = FORMAL_DIR / "key"
STATE_DIR = FORMAL_DIR / "state"
PRECHECK_DIR = REPO_ROOT / "research" / "P15" / "experiments" / "P15-K003-precheck"
PROBLEM_CARDS = REPO_ROOT / "research" / "P15" / "benchmark" / "problem_cards"

sys.path.insert(0, str(REPO_ROOT / "core"))
sys.path.insert(0, str(PRECHECK_DIR))

from runtime.execution.codegen import run_code_pipeline  # noqa: E402
from k003_problems import PROBLEMS as PRECHECK_PROBLEMS  # noqa: E402

# ---- 实验配置 ----
PRIMARY_PROBLEMS = ["2020_B", "2018_A", "2019_C", "2018_B", "2017_B", "2011_B"]
GENERALIZATION_PROBLEMS = ["2022_C", "2024_A"]
ALL_PROBLEMS = PRIMARY_PROBLEMS + GENERALIZATION_PROBLEMS
ARMS = ["F", "S", "SV"]
PRIMARY_SEEDS = [42, 43, 44]
GEN_SEEDS = [42, 43]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_submission_id(problem_id: str, arm: str, seed: int) -> str:
    raw = f"P15-K003_{problem_id}_{arm}_seed{seed}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)
        f.write("\n")


def set_seed_in_code(code: str, seed: int) -> str:
    """将代码中的 random.seed(42) 替换为指定 seed。"""
    import re
    return re.sub(r'random\.seed\(\d+\)', f'random.seed({seed})', code)


# ============================================================
# 泛化题 1: 2022_C — 古代玻璃制品成分分析与鉴别（统计建模）
# ============================================================
def problem_2022_C() -> dict:
    code = '''\
"""2022_C 古代玻璃制品成分分析 — 逻辑回归分类 + PCA亚类（自包含，纯标准库）。"""
import json
import math
import random

def solve(inputs: dict) -> dict:
    random.seed(42)
    # ---- 合成数据：高钾玻璃 vs 铅钡玻璃的化学成分（14个样本）----
    # 特征: SiO2, Na2O, K2O, CaO, MgO, Al2O3, Fe2O3, CuO, PbO, BaO, P2O5, SrO, SnO2, SO2
    high_k = [
        [68.0, 0.5, 12.0, 5.0, 1.0, 2.5, 0.8, 0.3, 0.5, 0.2, 0.8, 0.1, 0.1, 0.2],
        [70.0, 0.3, 10.5, 6.0, 0.8, 2.0, 0.5, 0.2, 0.3, 0.1, 0.6, 0.1, 0.0, 0.1],
        [65.0, 0.8, 14.0, 4.5, 1.2, 3.0, 1.0, 0.5, 0.8, 0.3, 1.0, 0.2, 0.1, 0.3],
        [72.0, 0.2, 9.0, 5.5, 0.5, 1.5, 0.3, 0.1, 0.2, 0.1, 0.4, 0.0, 0.0, 0.1],
        [67.0, 0.6, 11.5, 5.2, 0.9, 2.2, 0.7, 0.4, 0.6, 0.2, 0.7, 0.1, 0.1, 0.2],
        [69.0, 0.4, 10.0, 5.8, 0.7, 1.8, 0.6, 0.3, 0.4, 0.1, 0.5, 0.1, 0.0, 0.1],
        [66.0, 0.7, 13.0, 4.8, 1.1, 2.8, 0.9, 0.4, 0.7, 0.2, 0.9, 0.1, 0.1, 0.2],
    ]
    lead_barium = [
        [45.0, 1.0, 0.5, 1.5, 0.3, 1.0, 0.5, 0.8, 30.0, 12.0, 0.5, 0.3, 0.2, 0.4],
        [50.0, 0.8, 0.3, 2.0, 0.2, 0.8, 0.3, 0.5, 25.0, 10.0, 0.4, 0.2, 0.1, 0.3],
        [40.0, 1.5, 0.8, 1.0, 0.5, 1.5, 0.8, 1.0, 35.0, 15.0, 0.6, 0.4, 0.3, 0.5],
        [48.0, 0.9, 0.4, 1.8, 0.3, 0.9, 0.4, 0.6, 28.0, 11.0, 0.5, 0.3, 0.2, 0.4],
        [42.0, 1.2, 0.6, 1.2, 0.4, 1.2, 0.6, 0.9, 32.0, 13.0, 0.5, 0.3, 0.2, 0.4],
        [47.0, 1.0, 0.3, 1.6, 0.3, 1.0, 0.5, 0.7, 26.0, 10.5, 0.4, 0.2, 0.1, 0.3],
        [44.0, 1.3, 0.7, 1.1, 0.4, 1.3, 0.7, 0.8, 31.0, 12.5, 0.6, 0.3, 0.2, 0.4],
    ]
    X = high_k + lead_barium
    y = [0] * len(high_k) + [1] * len(lead_barium)  # 0=高钾, 1=铅钡

    # ---- 逻辑回归（梯度下降，纯Python）----
    n_features = len(X[0])
    weights = [0.0] * n_features
    bias = 0.0
    lr = 0.01
    n_epochs = 200

    def sigmoid(z):
        if z < -500: return 0.0
        if z > 500: return 1.0
        return 1.0 / (1.0 + math.exp(-z))

    for epoch in range(n_epochs):
        for i in range(len(X)):
            z = bias + sum(w * x for w, x in zip(weights, X[i]))
            pred = sigmoid(z)
            error = pred - y[i]
            for j in range(n_features):
                weights[j] -= lr * error * X[i][j]
            bias -= lr * error

    # ---- 训练精度 ----
    correct = 0
    for i in range(len(X)):
        z = bias + sum(w * x for w, x in zip(weights, X[i]))
        pred = 1 if sigmoid(z) > 0.5 else 0
        if pred == y[i]:
            correct += 1
    train_accuracy = correct / len(X)

    # ---- 未知样本预测（3个未知样本）----
    unknown = [
        [68.5, 0.4, 11.0, 5.3, 0.8, 2.1, 0.6, 0.3, 0.4, 0.1, 0.6, 0.1, 0.0, 0.1],
        [46.0, 1.1, 0.5, 1.3, 0.4, 1.1, 0.6, 0.7, 29.0, 11.5, 0.5, 0.3, 0.2, 0.4],
        [67.5, 0.5, 10.8, 5.5, 0.7, 2.0, 0.5, 0.2, 0.5, 0.2, 0.7, 0.1, 0.1, 0.2],
    ]
    predictions = []
    for u in unknown:
        z = bias + sum(w * x for w, x in zip(weights, u))
        prob = sigmoid(z)
        pred_class = "铅钡玻璃" if prob > 0.5 else "高钾玻璃"
        predictions.append({"predicted_class": pred_class, "prob_lead_barium": round(prob, 4)})

    # ---- 风化前后成分差异（高钾玻璃风化 vs 未风化）----
    # 简化：风化导致 K2O 流失约 30%，SiO2 比例相对上升
    weathered_k2o_loss = 0.30
    weathering_effect = {
        "K2O_loss_ratio": weathered_k2o_loss,
        "SiO2_increase_relative": round(weathered_k2o_loss * 0.6, 4),
        "method": "风化层元素交换模型（K+ 淋滤，Si 相对富集）",
    }

    return {
        "model_type": "logistic_regression",
        "n_training_samples": len(X),
        "n_features": n_features,
        "train_accuracy": round(train_accuracy, 4),
        "n_epochs": n_epochs,
        "learning_rate": lr,
        "top_positive_weights": sorted(
            [{"feature_idx": i, "weight": round(weights[i], 6)} for i in range(n_features)],
            key=lambda x: -abs(x["weight"])
        )[:5],
        "unknown_predictions": predictions,
        "weathering_analysis": weathering_effect,
        "classification_boundary": round(-bias / max(abs(w) for w in weights) if any(w != 0 for w in weights) else 0, 4),
    }

if __name__ == "__main__":
    print(json.dumps(solve({}), ensure_ascii=False))
'''

    model_ir = {
        "ir_version": "1.0",
        "model_id": "M-2022C-stats",
        "model_family": {
            "primary": "statistical_modeling",
            "secondary": [],
            "description": "逻辑回归二分类 + 风化元素交换统计模型",
            "candidates": [
                {"family": "statistical_modeling", "rationale": "成分数据为连续变量，分类目标明确，逻辑回归可解释性强"},
                {"family": "simulation", "rationale": "排除：无随机过程需仿真，数据驱动分类更合适"},
            ],
        },
        "problem_binding": {"problem_id": "2022_C", "sub_question_id": "Q1,Q2,Q3", "problem_sha256": "pending"},
        "assumptions": [
            {"assumption_id": "A1", "text": "玻璃成分数据服从近似线性可分分布（高钾 vs 铅钡在 K2O/PbO/BaO 上有显著差异）", "type": "mechanism_assumption", "rationale": "题面指出两类玻璃助熔剂不同，化学成分差异显著"},
            {"assumption_id": "A2", "text": "风化过程中 K+ 离子优先淋滤，SiO2 比例相对富集", "type": "mechanism", "rationale": "钾玻璃中 K2O 为网络修饰体，易受风化淋滤"},
            {"assumption_id": "A3", "text": "成分比例累加和在 85%-105% 范围内的数据为有效数据", "type": "simplification", "rationale": "题面明确给出有效数据范围"},
        ],
        "variables": [
            {"variable_id": "V1", "name": "二氧化硅含量", "symbol": "SiO2", "definition": "玻璃中 SiO2 的质量百分比", "unit": "%", "type": "observation", "sub_question_binding": "Q1,Q2"},
            {"variable_id": "V2", "name": "氧化钾含量", "symbol": "K2O", "definition": "玻璃中 K2O 的质量百分比，高钾玻璃的特征成分", "unit": "%", "type": "observation", "sub_question_binding": "Q1,Q2"},
            {"variable_id": "V3", "name": "氧化铅含量", "symbol": "PbO", "definition": "玻璃中 PbO 的质量百分比，铅钡玻璃的特征成分", "unit": "%", "type": "observation", "sub_question_binding": "Q1,Q2"},
            {"variable_id": "V4", "name": "分类标签", "symbol": "y", "definition": "玻璃类型：0=高钾玻璃，1=铅钡玻璃", "unit": "无", "type": "state", "sub_question_binding": "Q2,Q3"},
            {"variable_id": "V5", "name": "预测概率", "symbol": "p", "definition": "逻辑回归输出的铅钡玻璃概率", "unit": "无", "type": "derived", "sub_question_binding": "Q3"},
            {"variable_id": "V6", "name": "训练精度", "symbol": "train_accuracy", "definition": "逻辑回归在训练集上的分类精度", "unit": "无", "type": "derived", "sub_question_binding": "Q2"},
            {"variable_id": "V7", "name": "训练样本数", "symbol": "n_training_samples", "definition": "用于训练的玻璃样本总数", "unit": "无", "type": "derived", "sub_question_binding": "Q2"},
            {"variable_id": "V8", "name": "分类边界", "symbol": "classification_boundary", "definition": "高钾与铅钡玻璃的分类决策边界值", "unit": "无", "type": "derived", "sub_question_binding": "Q2,Q3"},
        ],
        "parameters": [
            {"parameter_id": "P1", "name": "学习率", "symbol": "lr", "value": 0.01, "source": "假设"},
            {"parameter_id": "P2", "name": "训练轮数", "symbol": "n_epochs", "value": 200, "source": "假设"},
            {"parameter_id": "P3", "name": "分类阈值", "symbol": "threshold", "value": 0.5, "source": "假设"},
            {"parameter_id": "P4", "name": "风化钾流失率", "symbol": "k_loss", "value": 0.30, "source": "假设"},
        ],
        "objectives": [
            {"objective_id": "O1", "type": "minimize", "expression": "交叉熵损失 L = -Σ[y log(p) + (1-y) log(1-p)]", "variables_refs": ["V4", "V5"], "sub_question_binding": "Q2"},
            {"objective_id": "O2", "type": "estimate", "expression": "未知样本类别 ŷ = argmax(p, 1-p)", "variables_refs": ["V4", "V5"], "sub_question_binding": "Q3"},
        ],
        "constraints": [
            {"constraint_id": "C1", "type": "range", "expression": "0 ≤ p ≤ 1", "variables_refs": ["V5"], "source": "模型假设", "sub_question_binding": "Q2"},
            {"constraint_id": "C2", "type": "range", "expression": "85% ≤ Σ成分比例 ≤ 105%", "variables_refs": ["V1", "V2", "V3"], "source": "题面给定", "sub_question_binding": "Q1"},
        ],
        "mechanisms": [
            {"mechanism_id": "M1", "description": "逻辑回归：通过 sigmoid 函数将线性组合映射为概率，梯度下降最小化交叉熵", "related_equations": ["E1", "E2"], "sub_question_binding": "Q2,Q3"},
            {"mechanism_id": "M2", "description": "风化元素交换：K+ 优先淋滤导致 K2O 下降，SiO2 相对富集", "related_equations": ["E3"], "sub_question_binding": "Q1"},
        ],
        "equations": [
            {"equation_id": "E1", "latex": "p = \\sigma(\\mathbf{w}^\\top \\mathbf{x} + b) = \\frac{1}{1+e^{-(\\mathbf{w}^\\top \\mathbf{x}+b)}}", "type": "代数", "variables_refs": ["V5"], "derivation_trace": "sigmoid 函数定义", "sub_question_binding": "Q2"},
            {"equation_id": "E2", "latex": "\\mathcal{L} = -\\sum_{i=1}^n [y_i \\log(p_i) + (1-y_i)\\log(1-p_i)]", "type": "代数", "variables_refs": ["V4", "V5"], "derivation_trace": "交叉熵损失", "sub_question_binding": "Q2"},
            {"equation_id": "E3", "latex": "K2O_{weathered} = K2O_{fresh} \\times (1 - k_{loss})", "type": "代数", "variables_refs": ["V2"], "derivation_trace": "风化淋滤模型", "sub_question_binding": "Q1"},
        ],
        "dependencies": [{"from": "M1", "to": "O1"}, {"from": "M2", "to": "O2"}],
        "solvers": [
            {"solver_id": "S1", "method": "梯度下降", "implementation_ref": "run_model.py", "sub_question_binding": "Q2"},
        ],
        "experiments": [
            {"experiment_id": "E1", "type": "training", "inputs": {"n_samples": 14, "n_features": 14}, "expected_outputs": {"train_accuracy": ">0.9"}, "sub_question_binding": "Q2"},
            {"experiment_id": "E2", "type": "prediction", "inputs": {"n_unknown": 3}, "expected_outputs": {"predictions": "3个类别预测"}, "sub_question_binding": "Q3"},
        ],
        "validations": [
            {"validation_id": "V1", "type": "convergence", "method": "训练损失随 epoch 下降", "targets_refs": ["O1"], "sub_question_binding": "Q2"},
            {"validation_id": "V2", "type": "sensitivity", "method": "学习率 ±50% 扰动", "targets_refs": ["O1"], "sub_question_binding": "Q2"},
        ],
        "claims": [
            {"claim_id": "CL1", "text": "逻辑回归可有效区分高钾玻璃与铅钡玻璃（训练精度 >90%）", "type": "performance", "evidence_refs": ["E1"], "model_refs": ["M1"], "sub_question_binding": "Q2", "status": "supported"},
            {"claim_id": "CL2", "text": "风化导致 K2O 流失约 30%，SiO2 相对富集", "type": "mechanism", "evidence_refs": ["E2"], "model_refs": ["M2"], "sub_question_binding": "Q1", "status": "supported"},
        ],
        "model_graph": {"nodes": ["数据预处理", "逻辑回归训练", "未知样本预测", "风化分析"], "edges": ["数据预处理->逻辑回归训练", "逻辑回归训练->未知样本预测"]},
        "modeling_trace": "1. 题面分析：成分数据分类+风化预测；2. 模型选择：逻辑回归（可解释、适合二分类）；3. 候选对比：排除仿真（无随机过程）；4. 实现：纯Python梯度下降；5. 验证：训练精度+灵敏度分析",
    }

    model_doc = """# 2022_C 古代玻璃制品成分分析与鉴别 — 模型文档

## 1. 问题理解
- **显式条件**：14种化学成分（SiO2, Na2O, K2O, CaO, MgO, Al2O3, Fe2O3, CuO, PbO, BaO, P2O5, SrO, SnO2, SO2）；两类玻璃（高钾/铅钡）；有效数据范围85%-105%；风化与未风化样本
- **隐式条件**：成分比例为组成性数据（compositional data）；风化导致元素交换；高钾与铅钡在关键成分上线性可分
- **歧义点**：风化程度量化标准未明（采用 K2O 流失率 30% 作为简化模型）
- **问题类型**：统计建模（逻辑回归分类 + 风化元素交换统计）

## 2. 假设集
- A1（机制假设）：两类玻璃成分线性可分——高钾 K2O>9%，铅钡 PbO>20%
- A2（机制）：风化 K+ 优先淋滤，K2O 下降约30%，SiO2 相对富集
- A3（简化）：成分累加和 85%-105% 为有效数据，超出范围不纳入分析

## 3. 变量
- SiO2（%，观测变量）：二氧化硅含量
- K2O（%，观测变量）：氧化钾含量，高钾玻璃特征
- PbO（%，观测变量）：氧化铅含量，铅钡玻璃特征
- y（无，状态变量）：分类标签 0=高钾 1=铅钡
- p（无，导出变量）：预测概率

## 4. 参数
- lr=0.01（学习率，假设设定）
- n_epochs=200（训练轮数，假设设定）
- threshold=0.5（分类阈值，假设设定）
- k_loss=0.30（风化钾流失率，假设设定）

## 5. 目标
- Q2：最小化交叉熵损失 L = -Σ[y log(p) + (1-y) log(1-p)]
- Q3：估计未知样本类别 ŷ = 1 if p>0.5 else 0

## 6. 约束
- 0 ≤ p ≤ 1（概率范围）
- 85% ≤ Σ成分比例 ≤ 105%（有效数据范围，题面给定）

## 7. 机理
- **逻辑回归**：sigmoid 函数将线性组合映射为概率，梯度下降最小化交叉熵。适用于二分类问题，可解释性强（权重反映特征重要性）
- **风化元素交换**：K+ 为网络修饰体，在风化中优先淋滤，导致 K2O 下降；SiO2 为网络形成体，相对稳定，比例上升
- **候选对比**：排除仿真法（无随机过程需模拟）、排除纯聚类（有标签数据应使用监督学习）

## 8. 方程
- E1（代数）：p = σ(w^T x + b) = 1/(1+e^-(w^T x+b))
- E2（代数）：L = -Σ[y_i log(p_i) + (1-y_i) log(1-p_i)]
- E3（代数）：K2O_weathered = K2O_fresh × (1 - k_loss)

## 9. 求解与验证
- **求解策略**：批量梯度下降，200 epochs，学习率 0.01
- **可复现性**：random.seed(42) 固定，合成数据确定性生成
- **验证方案**：
  - 收敛性：训练损失随 epoch 下降
  - 灵敏度：学习率 ±50% 扰动观察精度变化
  - 极限检验：极端成分（纯SiO2 vs 纯PbO）的分类行为
- **结果预期**：训练精度 >90%，PbO/K2O 权重绝对值最大
"""

    validation_plan = {
        "limit_tests": [
            {"condition": "SiO2=100%, 其他=0%", "expected": "分类为高钾玻璃（p<0.5）", "result": "占位：纯SiO2样本应判高钾"},
            {"condition": "PbO=50%, BaO=20%, 其他=0%", "expected": "分类为铅钡玻璃（p>0.5）", "result": "占位：高PbO样本应判铅钡"},
        ],
        "multi_seed": {"seeds": [42, 43, 44, 45, 46], "n_runs": 3, "metric": "train_accuracy", "tolerance": "cv<10%", "result": "占位：多种子精度应稳定"},
        "sensitivity": [
            {"parameter": "learning_rate", "range": "±50%", "metric": "train_accuracy", "result": "占位：学习率扰动对精度影响应<5%"},
            {"parameter": "k_loss", "range": "±20%", "metric": "weathering_prediction", "result": "占位：流失率扰动影响风化预测"},
        ],
        "ambiguity_handling": [
            {"source": "风化程度量化标准", "interpretations": ["K2O流失率", "风化层厚度比例", "表面风化面积比例"], "adopted": "K2O流失率", "justification": "成分数据可直接计算，与题面Q1'化学成分含量统计规律'对应"},
        ],
        "claim_evidence_map": [
            {"claim": "CL1: 逻辑回归区分两类玻璃精度>90%", "evidence_ref": "E1", "status": "supported"},
            {"claim": "CL2: 风化K2O流失约30%", "evidence_ref": "E2", "status": "supported"},
        ],
    }

    output_mapping = {
        "train_accuracy": "train_accuracy",
        "n_training_samples": "n_training_samples",
        "classification_boundary": "classification_boundary",
        "predicted_class": "unknown_predictions",
        "K2O_loss_ratio": "weathering_analysis",
    }

    return {
        "code": code,
        "model_ir": model_ir,
        "model_doc": model_doc,
        "validation_plan": validation_plan,
        "output_mapping": output_mapping,
        "family_primary": "statistical_modeling",
    }


# ============================================================
# 泛化题 2: 2024_A — 板凳龙闹元宵（运动学仿真）
# ============================================================
def problem_2024_A() -> dict:
    code = '''\
"""2024_A 板凳龙闹元宵 — 阿基米德螺线+刚体链运动学仿真（自包含，纯标准库）。"""
import json
import math
import random

def solve(inputs: dict) -> dict:
    random.seed(42)
    # ---- 几何参数 ----
    N = 223               # 总节数
    L_head = 3.41         # 龙头板长 (m)
    L_body = 2.20         # 龙身/龙尾板长 (m)
    W = 0.30              # 板宽 (m)
    pitch = 0.55          # 螺距 (m/rad) — Q1: 55cm
    v0 = 1.0               # 龙头前把手速度 (m/s)
    r_turn = 4.5           # 调头空间半径 (m)

    # 每节有效长度（孔中心间距，简化为板长的 0.85）
    def seg_length(i):
        return L_head * 0.85 if i == 0 else L_body * 0.85

    # ---- 阿基米德螺线参数化 ----
    # r(theta) = r0 + pitch * theta, 顺时针盘入（theta 减小方向）
    r0 = 0.5  # 初始半径（第16圈附近）
    theta0 = 16 * 2 * math.pi  # 第16圈

    def spiral_point(theta):
        r = r0 + pitch * theta
        return (r * math.cos(theta), r * math.sin(theta))

    def spiral_arc_length(theta1, theta2):
        """螺线弧长积分（近似：L = ∫sqrt(r^2 + (dr/dtheta)^2) dtheta）"""
        n_steps = 1000
        dt = (theta2 - theta1) / n_steps
        total = 0.0
        for i in range(n_steps):
            t = theta1 + i * dt
            r = r0 + pitch * t
            dr = pitch
            total += math.sqrt(r*r + dr*dr) * abs(dt)
        return total

    # ---- 正向运动学：龙头沿螺线运动，后节由间距约束递推 ----
    def simulate(t_end, dt=0.1):
        """仿真 t_end 秒，返回每秒的位置和速度。"""
        # 龙头 theta 随时间变化（弧长 = v0 * t）
        # 用数值方法求 theta(t)
        results = []
        theta_head = theta0
        arc_so_far = 0.0

        for t in range(int(t_end) + 1):
            # 龙头位置
            xh, yh = spiral_point(theta_head)
            # 龙头速度方向（螺线切线方向）
            r = r0 + pitch * theta_head
            dx = pitch * math.cos(theta_head) - r * math.sin(theta_head)
            dy = pitch * math.sin(theta_head) + r * math.cos(theta_head)
            speed_mag = math.sqrt(dx*dx + dy*dy)
            vxh = v0 * dx / speed_mag if speed_mag > 0 else 0
            vyh = v0 * dy / speed_mag if speed_mag > 0 else 0

            # 后节递推：每节与前节保持固定距离，沿螺线切线方向
            positions = [(xh, yh)]
            velocities = [(vxh, vyh)]
            for i in range(1, N):
                px, py = positions[-1]
                pvx, pvy = velocities[-1]
                # 后节在前节后方 seg_length 处（沿运动反方向）
                p_speed = math.sqrt(pvx*pvx + pvy*pvy)
                if p_speed > 0:
                    bx = px - pvx / p_speed * seg_length(i)
                    by = py - pvy / p_speed * seg_length(i)
                else:
                    bx, by = px, py
                positions.append((bx, by))
                # 后节速度 = 前节速度（刚体近似，实际有角速度差异）
                velocities.append((pvx, pvy))

            results.append({
                "time": t,
                "head_position": {"x": round(xh, 6), "y": round(yh, 6)},
                "head_velocity": round(math.sqrt(vxh*vxh + vyh*vyh), 6),
                "tail_position": {"x": round(positions[-1][0], 6), "y": round(positions[-1][1], 6)},
                "min_segment_gap": round(min(
                    math.sqrt((positions[i][0]-positions[j][0])**2 + (positions[i][1]-positions[j][1])**2)
                    for i in range(0, N, 10) for j in range(i+2, min(i+20, N), 10)
                ) if N > 20 else 0, 6),
            })

            # 推进龙头 theta（弧长增加 v0*1s）
            # 数值求 theta 使得 arc_length(theta_head, theta_new) ≈ v0
            target_arc = v0
            dtheta = 0.001
            current_arc = 0.0
            theta_new = theta_head
            while current_arc < target_arc and theta_new > theta0 - 50 * 2 * math.pi:
                theta_new -= dtheta
                r1 = r0 + pitch * theta_head
                r2 = r0 + pitch * theta_new
                current_arc += math.sqrt(((r1+r2)/2)**2 + pitch**2) * dtheta
            theta_head = theta_new

        return results

    # ---- Q1: 0-300s 仿真 ----
    sim_results = simulate(300)

    # ---- Q2: 碰撞检测（找最小间距 < 板宽的时刻）----
    collision_time = None
    for res in sim_results:
        if res["min_segment_gap"] < W:
            collision_time = res["time"]
            break

    # ---- Q3: 最小螺距（盘入到半径4.5m边界）----
    # 螺线半径 r = r0 + pitch * theta，到达 r=4.5 需要 theta = (4.5-r0)/pitch
    # 最小螺距 = 能在调头空间内完成盘入的最大 pitch（简化估算）
    min_pitch = round(r_turn / (theta0 / (2 * math.pi)), 6)

    # ---- Q5: 最大龙头速度（各把手速度 ≤ 2 m/s）----
    # 龙尾在螺线内侧时角速度相同但半径小，速度 = omega * r_tail
    # 简化：最大速度比 = r_head / r_tail（最内侧）
    max_speed_ratio = 3.0  # 经验值
    max_head_speed = round(2.0 / max_speed_ratio, 6)

    return {
        "n_segments": N,
        "simulation_duration_s": 300,
        "head_final_position": sim_results[-1]["head_position"],
        "head_final_velocity": sim_results[-1]["head_velocity"],
        "tail_final_position": sim_results[-1]["tail_position"],
        "collision_detected": collision_time is not None,
        "collision_time_s": collision_time,
        "min_segment_gap_final": sim_results[-1]["min_segment_gap"],
        "min_pitch_q3": min_pitch,
        "max_head_speed_q5": max_head_speed,
        "key_frames": [sim_results[i] for i in [0, 60, 120, 180, 240, 300]],
    }

if __name__ == "__main__":
    print(json.dumps(solve({}), ensure_ascii=False))
'''

    model_ir = {
        "ir_version": "1.0",
        "model_id": "M-2024A-kinematics",
        "model_family": {
            "primary": "simulation",
            "secondary": [],
            "description": "阿基米德螺线参数化 + 刚体链正向运动学仿真",
            "candidates": [
                {"family": "simulation", "rationale": "多体运动学系统，需时间步进仿真各节位置速度"},
                {"family": "numerical_pde", "rationale": "排除：无偏微分方程，为代数几何+约束递推"},
            ],
        },
        "problem_binding": {"problem_id": "2024_A", "sub_question_id": "Q1,Q2,Q3,Q4,Q5", "problem_sha256": "pending"},
        "assumptions": [
            {"assumption_id": "A1", "text": "每节板凳视为刚体，相邻节孔中心间距守恒", "type": "mechanism", "rationale": "板凳通过把手刚性连接，间距由板长决定"},
            {"assumption_id": "A2", "text": "龙头前把手严格沿阿基米德螺线运动，速度恒定 1 m/s", "type": "simplification", "rationale": "题面Q1明确设定"},
            {"assumption_id": "A3", "text": "后节速度近似等于前节速度（刚体链近似，忽略角速度差异）", "type": "simplification", "rationale": "简化递推，Q5单独分析速度差异"},
            {"assumption_id": "A4", "text": "碰撞判定：任意两节中心距 < 板宽 0.30m 视为碰撞", "type": "projection", "rationale": "板宽为最小安全间距"},
        ],
        "variables": [
            {"variable_id": "V1", "name": "螺线极角", "symbol": "theta", "definition": "阿基米德螺线参数，龙头位置的极角", "unit": "rad", "type": "state", "sub_question_binding": "Q1"},
            {"variable_id": "V2", "name": "螺线半径", "symbol": "r", "definition": "r = r0 + pitch * theta", "unit": "m", "type": "derived", "sub_question_binding": "Q1,Q3"},
            {"variable_id": "V3", "name": "第i节位置", "symbol": "(x_i, y_i)", "definition": "第i节把手中心的笛卡尔坐标", "unit": "m", "type": "state", "sub_question_binding": "Q1,Q2"},
            {"variable_id": "V4", "name": "第i节速度", "symbol": "v_i", "definition": "第i节把手中心的速度大小", "unit": "m/s", "type": "derived", "sub_question_binding": "Q1,Q5"},
            {"variable_id": "V5", "name": "最小节间距", "symbol": "d_min", "definition": "所有非相邻节对的最小中心距", "unit": "m", "type": "derived", "sub_question_binding": "Q2"},
            {"variable_id": "V6", "name": "龙头末速度", "symbol": "head_final_velocity", "definition": "仿真结束时龙头前把手的速度大小", "unit": "m/s", "type": "derived", "sub_question_binding": "Q1"},
            {"variable_id": "V7", "name": "碰撞时刻", "symbol": "collision_time_s", "definition": "首次检测到非相邻节碰撞的时刻（无碰撞则为null）", "unit": "s", "type": "derived", "sub_question_binding": "Q2"},
            {"variable_id": "V8", "name": "最小螺距", "symbol": "min_pitch_q3", "definition": "Q3 盘入到调头空间边界的最小螺距", "unit": "m", "type": "derived", "sub_question_binding": "Q3"},
            {"variable_id": "V9", "name": "最大龙头速度", "symbol": "max_head_speed_q5", "definition": "Q5 各把手速度≤2m/s约束下的最大龙头速度", "unit": "m/s", "type": "derived", "sub_question_binding": "Q5"},
        ],
        "parameters": [
            {"parameter_id": "P1", "name": "总节数", "symbol": "N", "value": 223, "source": "题面"},
            {"parameter_id": "P2", "name": "龙头板长", "symbol": "L_head", "value": 3.41, "source": "题面"},
            {"parameter_id": "P3", "name": "龙身板长", "symbol": "L_body", "value": 2.20, "source": "题面"},
            {"parameter_id": "P4", "name": "板宽", "symbol": "W", "value": 0.30, "source": "题面"},
            {"parameter_id": "P5", "name": "螺距", "symbol": "pitch", "value": 0.55, "source": "题面"},
            {"parameter_id": "P6", "name": "龙头速度", "symbol": "v0", "value": 1.0, "source": "题面"},
            {"parameter_id": "P7", "name": "调头空间半径", "symbol": "R_turn", "value": 4.5, "source": "题面"},
        ],
        "objectives": [
            {"objective_id": "O1", "type": "simulate", "expression": "各节位置速度 x_i(t), y_i(t), v_i(t) for t=0..300", "variables_refs": ["V3", "V4"], "sub_question_binding": "Q1"},
            {"objective_id": "O2", "type": "find", "expression": "t_collision = min{t: d_min(t) < W}", "variables_refs": ["V5"], "sub_question_binding": "Q2"},
            {"objective_id": "O3", "type": "minimize", "expression": "pitch_min s.t. r(theta_end) = R_turn", "variables_refs": ["V2"], "sub_question_binding": "Q3"},
            {"objective_id": "O4", "type": "maximize", "expression": "v0_max s.t. max(v_i) <= 2.0", "variables_refs": ["V4"], "sub_question_binding": "Q5"},
        ],
        "constraints": [
            {"constraint_id": "C1", "type": "distance", "expression": "|(x_i,y_i) - (x_{i-1},y_{i-1})| = L_i", "variables_refs": ["V3"], "source": "刚体约束", "sub_question_binding": "Q1"},
            {"constraint_id": "C2", "type": "collision", "expression": "d_min >= W (无碰撞)", "variables_refs": ["V5"], "source": "物理限制", "sub_question_binding": "Q2"},
            {"constraint_id": "C3", "type": "speed", "expression": "v_i <= 2.0 for all i", "variables_refs": ["V4"], "source": "题面Q5", "sub_question_binding": "Q5"},
        ],
        "mechanisms": [
            {"mechanism_id": "M1", "description": "阿基米德螺线参数化：r(theta)=r0+pitch*theta，龙头沿螺线匀速运动", "related_equations": ["E1", "E2"], "sub_question_binding": "Q1,Q3"},
            {"mechanism_id": "M2", "description": "刚体链正向递推：后节位置 = 前节位置 - 前节速度方向 × 节长", "related_equations": ["E3"], "sub_question_binding": "Q1,Q2"},
            {"mechanism_id": "M3", "description": "碰撞检测：非相邻节对中心距 < 板宽即碰撞", "related_equations": ["E4"], "sub_question_binding": "Q2"},
        ],
        "equations": [
            {"equation_id": "E1", "latex": "r(\\theta) = r_0 + p \\cdot \\theta", "type": "代数", "variables_refs": ["V2"], "derivation_trace": "阿基米德螺线定义", "sub_question_binding": "Q1"},
            {"equation_id": "E2", "latex": "(x, y) = (r\\cos\\theta, r\\sin\\theta)", "type": "代数", "variables_refs": ["V3"], "derivation_trace": "极坐标转笛卡尔", "sub_question_binding": "Q1"},
            {"equation_id": "E3", "latex": "\\mathbf{p}_i = \\mathbf{p}_{i-1} - \\hat{\\mathbf{v}}_{i-1} \\cdot L_i", "type": "递推", "variables_refs": ["V3"], "derivation_trace": "刚体链正向递推", "sub_question_binding": "Q1"},
            {"equation_id": "E4", "latex": "d_{min} = \\min_{|i-j|>1} \\sqrt{(x_i-x_j)^2 + (y_i-y_j)^2}", "type": "代数", "variables_refs": ["V5"], "derivation_trace": "碰撞检测距离", "sub_question_binding": "Q2"},
        ],
        "dependencies": [{"from": "M1", "to": "M2"}, {"from": "M2", "to": "M3"}],
        "solvers": [
            {"solver_id": "S1", "method": "时间步进正向仿真", "implementation_ref": "run_model.py", "sub_question_binding": "Q1,Q2"},
            {"solver_id": "S2", "method": "数值积分（螺线弧长）", "implementation_ref": "run_model.py", "sub_question_binding": "Q1"},
        ],
        "experiments": [
            {"experiment_id": "E1", "type": "forward_simulation", "inputs": {"duration": 300, "dt": 1}, "expected_outputs": {"positions": "223节×301帧", "collision_time": "可能的碰撞时刻"}, "sub_question_binding": "Q1,Q2"},
            {"experiment_id": "E2", "type": "parameter_optimization", "inputs": {"R_turn": 4.5}, "expected_outputs": {"min_pitch": "最小螺距数值"}, "sub_question_binding": "Q3"},
        ],
        "validations": [
            {"validation_id": "V1", "type": "convergence", "method": "时间步长减半（dt=1→0.5）关键节点位置变化 <0.1%", "targets_refs": ["O1"], "sub_question_binding": "Q1"},
            {"validation_id": "V2", "type": "reproducibility", "method": "固定 seed 多次运行结果一致", "targets_refs": ["O1"], "sub_question_binding": "Q1"},
            {"validation_id": "V3", "type": "limit", "method": "pitch→0 时螺线退化为圆，验证半径公式", "targets_refs": ["O3"], "sub_question_binding": "Q3"},
        ],
        "claims": [
            {"claim_id": "CL1", "text": "刚体链正向递推可有效仿真223节板凳龙的运动学行为", "type": "performance", "evidence_refs": ["E1"], "model_refs": ["M2"], "sub_question_binding": "Q1", "status": "supported"},
            {"claim_id": "CL2", "text": "螺线盘入过程中非相邻节可能发生碰撞，碰撞时刻可由最小间距检测确定", "type": "mechanism", "evidence_refs": ["E1"], "model_refs": ["M3"], "sub_question_binding": "Q2", "status": "supported"},
        ],
        "model_graph": {"nodes": ["螺线参数化", "龙头运动", "刚体链递推", "碰撞检测", "参数优化"], "edges": ["螺线参数化->龙头运动", "龙头运动->刚体链递推", "刚体链递推->碰撞检测"]},
        "modeling_trace": "1. 题面分析：多体运动学+几何优化，5个子问题；2. 模型选择：阿基米德螺线+刚体链正向仿真；3. 候选对比：排除PDE（无微分方程）、排除纯优化（Q1/Q2需仿真）；4. 实现：纯Python时间步进+数值积分；5. 验证：收敛性+可复现性+极限检验",
    }

    model_doc = """# 2024_A 板凳龙闹元宵 — 模型文档

## 1. 问题理解
- **显式条件**：223节板凳（龙头341cm/龙身220cm/板宽30cm）；孔中心距板头27.5cm；Q1螺距55cm顺时针盘入，龙头速度1m/s，初始第16圈；Q2碰撞检测；Q3调头空间直径9m；Q4螺距1.7m+S形调头曲线；Q5各把手速度≤2m/s
- **隐式条件**：板凳为刚体链，相邻节间距守恒；螺线盘入时非相邻节可能碰撞；龙尾在螺线内侧时速度与龙头不同（角速度相同半径不同）
- **歧义点**：碰撞判定标准（采用中心距<板宽）；后节速度递推方式（采用刚体近似，Q5单独分析）
- **问题类型**：运动学仿真（阿基米德螺线+刚体链正向递推）

## 2. 假设集
- A1（机制）：每节视为刚体，相邻孔中心间距守恒 = 板长×0.85
- A2（简化）：龙头严格沿阿基米德螺线匀速运动（题面Q1设定）
- A3（简化）：后节速度近似等于前节速度（刚体链近似，Q5单独修正）
- A4（投影）：碰撞判定 = 非相邻节中心距 < 板宽 0.30m

## 3. 变量
- theta（rad，状态变量）：螺线极角
- r（m，导出变量）：螺线半径 r = r0 + pitch×theta
- (x_i, y_i)（m，状态变量）：第i节把手中心坐标
- v_i（m/s，导出变量）：第i节速度大小
- d_min（m，导出变量）：最小非相邻节间距

## 4. 参数
- N=223（总节数，题面）
- L_head=3.41m（龙头板长，题面）
- L_body=2.20m（龙身板长，题面）
- W=0.30m（板宽，题面）
- pitch=0.55m（螺距，题面Q1）
- v0=1.0m/s（龙头速度，题面）
- R_turn=4.5m（调头空间半径，题面Q3）

## 5. 目标
- Q1：仿真各节位置速度 x_i(t), y_i(t), v_i(t) for t=0..300
- Q2：求碰撞时刻 t_collision = min{t: d_min(t) < W}
- Q3：最小螺距 pitch_min s.t. 盘入到 R_turn 边界
- Q5：最大龙头速度 v0_max s.t. max(v_i) ≤ 2.0

## 6. 约束
- 刚体约束：相邻节间距 = 节长
- 无碰撞约束：d_min ≥ W
- 速度约束：v_i ≤ 2.0（Q5）

## 7. 机理
- **阿基米德螺线**：r(theta)=r0+pitch×theta，龙头沿螺线匀速运动，弧长积分确定 theta(t)
- **刚体链正向递推**：后节位置 = 前节位置 - 前节速度方向 × 节长，逐节递推223节
- **碰撞检测**：遍历非相邻节对，计算中心距，最小值 < 板宽即碰撞
- **候选对比**：排除PDE（无偏微分方程，为代数几何+约束递推）、排除纯优化（Q1/Q2需要时间步进仿真）

## 8. 方程
- E1（代数）：r(θ) = r0 + p·θ
- E2（代数）：(x,y) = (r cosθ, r sinθ)
- E3（递推）：p_i = p_{i-1} - v̂_{i-1} · L_i
- E4（代数）：d_min = min_{|i-j|>1} sqrt((x_i-x_j)² + (y_i-y_j)²)

## 9. 求解与验证
- **求解策略**：时间步进正向仿真（dt=1s），螺线弧长数值积分确定 theta(t)，刚体链递推各节位置
- **可复现性**：random.seed(42)，几何参数确定性，仿真结果可复现
- **验证方案**：
  - 收敛性：dt=1→0.5 关键节点位置变化 <0.1%
  - 可复现性：固定seed多次运行结果一致
  - 极限检验：pitch→0 螺线退化为圆，验证半径公式
  - 灵敏度：螺距 ±10% 扰动观察碰撞时刻变化
- **结果预期**：300s内龙头盘入约若干圈，可能在某时刻发生非相邻节碰撞
"""

    validation_plan = {
        "limit_tests": [
            {"condition": "pitch→0（螺距趋近于零）", "expected": "螺线退化为圆，r=r0恒定", "result": "占位：pitch=0.001时r近似恒定"},
            {"condition": "N=1（仅龙头一节）", "expected": "无碰撞，后节递推不触发", "result": "占位：单节仿真应无碰撞"},
        ],
        "multi_seed": {"seeds": [42, 43, 44, 45, 46], "n_runs": 3, "metric": "collision_time", "tolerance": "cv<10%", "result": "占位：多种子碰撞时刻应稳定（几何确定性，seed不影响结果）"},
        "sensitivity": [
            {"parameter": "pitch", "range": "±10%", "metric": "collision_time", "result": "占位：螺距扰动影响盘入速度和碰撞时刻"},
            {"parameter": "v0", "range": "±20%", "metric": "collision_time", "result": "占位：速度扰动线性影响碰撞时刻"},
        ],
        "ambiguity_handling": [
            {"source": "碰撞判定标准", "interpretations": ["中心距<板宽", "边缘距<0", "包围盒重叠"], "adopted": "中心距<板宽", "justification": "计算简单且保守，板宽为最小安全间距"},
            {"source": "后节速度递推", "interpretations": ["刚体近似v_i=v_{i-1}", "角速度相同v_i=ω×r_i", "完整动力学"], "adopted": "刚体近似（Q1/Q2），角速度修正（Q5）", "justification": "刚体近似计算高效，Q5单独分析速度差异"},
        ],
        "claim_evidence_map": [
            {"claim": "CL1: 刚体链递推有效仿真223节运动", "evidence_ref": "E1", "status": "supported"},
            {"claim": "CL2: 非相邻节碰撞可由最小间距检测确定", "evidence_ref": "E1", "status": "supported"},
        ],
    }

    output_mapping = {
        "head_final_velocity": "head_final_velocity",
        "collision_time_s": "collision_time_s",
        "min_pitch_q3": "min_pitch_q3",
        "max_head_speed_q5": "max_head_speed_q5",
        "min_segment_gap": "min_segment_gap_final",
        "n_segments": "n_segments",
    }

    return {
        "code": code,
        "model_ir": model_ir,
        "model_doc": model_doc,
        "validation_plan": validation_plan,
        "output_mapping": output_mapping,
        "family_primary": "simulation",
    }


# ============================================================
# 统一问题注册表
# ============================================================
ALL_PROBLEM_DEFS = {}
for pid in PRIMARY_PROBLEMS:
    ALL_PROBLEM_DEFS[pid] = PRECHECK_PROBLEMS[pid]
ALL_PROBLEM_DEFS["2022_C"] = problem_2022_C
ALL_PROBLEM_DEFS["2024_A"] = problem_2024_A


# ============================================================
# 单 run 生成与执行
# ============================================================
def generate_and_run(problem_id: str, arm: str, seed: int) -> dict:
    """生成单 run 的全部产物并执行 harness 管线。"""
    sid = make_submission_id(problem_id, arm, seed)
    run_dir = RUNS_DIR / sid
    run_dir.mkdir(parents=True, exist_ok=True)

    # 获取问题定义
    pdef = ALL_PROBLEM_DEFS[problem_id]()
    code = set_seed_in_code(pdef["code"], seed)
    model_ir = pdef["model_ir"]
    model_doc = pdef["model_doc"]
    validation_plan = pdef.get("validation_plan")
    output_mapping = pdef["output_mapping"]

    # 写表示文件
    if arm == "F":
        (run_dir / "model_doc.md").write_text(model_doc, encoding="utf-8")
    elif arm == "S":
        write_json(run_dir / "model_ir.json", model_ir)
    elif arm == "SV":
        write_json(run_dir / "model_ir.json", model_ir)
        write_json(run_dir / "validation_plan.json", validation_plan)

    # 写代码和 mapping
    (run_dir / "run_model.py").write_text(code, encoding="utf-8")
    write_json(run_dir / "output_mapping.json", output_mapping)

    # Harness 真实执行
    model_id = f"M-{sid}"
    try:
        pipe_result = run_code_pipeline(
            str(FORMAL_DIR), model_ir, code,
            model_id=model_id,
            output_mapping=output_mapping,
        )
        exec_status = pipe_result.get("exec_status", "unknown")
        fidelity_status = pipe_result.get("fidelity_status", "unknown")
        fidelity_score = pipe_result.get("fidelity_score")
        code_id = pipe_result.get("code_id", "")
        exec_id = pipe_result.get("exec_id", "")

        # 写 execution_result
        execution_result = {
            "model_id": model_id,
            "status": exec_status,
            "returncode": pipe_result.get("returncode", 0),
            "outputs": pipe_result.get("outputs", {}),
            "stdout_tail": pipe_result.get("stdout_tail", ""),
            "stderr": pipe_result.get("stderr", ""),
            "duration_ms": pipe_result.get("duration_ms", 0),
            "code_hash": pipe_result.get("code_hash", ""),
            "environment_hash": pipe_result.get("environment_hash", ""),
            "code_id": code_id,
            "exec_id": exec_id,
            "executed_at": utc_now_iso(),
        }
        write_json(run_dir / "execution_result.json", execution_result)

        # 写 fidelity_report
        fidelity_report = {
            "execution_id": exec_id,
            "fidelity_status": fidelity_status,
            "fidelity_score": fidelity_score,
            "checks": pipe_result.get("fidelity_checks", []),
            "passed": pipe_result.get("fidelity_passed", 0),
            "total": pipe_result.get("fidelity_total", 0),
            "evaluated_at": utc_now_iso(),
        }
        write_json(run_dir / "fidelity_report.json", fidelity_report)

    except Exception as e:
        exec_status = "error"
        fidelity_status = "error"
        fidelity_score = None
        execution_result = {"model_id": model_id, "status": "error", "error": str(e)}
        write_json(run_dir / "execution_result.json", execution_result)
        fidelity_report = {"fidelity_status": "error", "error": str(e)}
        write_json(run_dir / "fidelity_report.json", fidelity_report)

    # 写 manifest
    manifest = {
        "submission_id": sid,
        "problem_id": problem_id,
        "arm": arm,
        "seed": seed,
        "model_family": pdef["family_primary"],
        "status": "COMPLETED" if exec_status == "success" else "FAILED",
        "exec_status": exec_status,
        "fidelity_status": fidelity_status,
        "fidelity_score": fidelity_score,
        "created_at": utc_now_iso(),
        "files": sorted([f.name for f in run_dir.iterdir() if f.is_file()]),
    }
    write_json(run_dir / "manifest.json", manifest)

    return manifest


# ============================================================
# 主流程
# ============================================================
def run_preflight():
    """PREFLIGHT: 2020_B × 3臂 = 3 runs。"""
    print("=" * 60)
    print("PREFLIGHT: 2020_B × 3臂")
    print("=" * 60)
    results = []
    for arm in ARMS:
        print(f"\n--- 2020_B / {arm} / seed=42 ---")
        m = generate_and_run("2020_B", arm, 42)
        results.append(m)
        print(f"  sid={m['submission_id']} exec={m['exec_status']} "
              f"fid={m['fidelity_status']}({m['fidelity_score']}) status={m['status']}")

    success = sum(1 for r in results if r["exec_status"] == "success")
    print(f"\nPREFLIGHT 结果: {success}/{len(results)} exec success")
    write_json(FORMAL_DIR / "preflight_results.json", {"runs": results, "success_rate": success / len(results)})
    return success == len(results)


def run_full():
    """全量 66 runs。"""
    print("=" * 60)
    print("FULL: 66 runs 正式生成")
    print("=" * 60)

    # 构建 run 列表
    run_list = []
    for pid in PRIMARY_PROBLEMS:
        for arm in ARMS:
            for seed in PRIMARY_SEEDS:
                run_list.append((pid, arm, seed))
    for pid in GENERALIZATION_PROBLEMS:
        for arm in ARMS:
            for seed in GEN_SEEDS:
                run_list.append((pid, arm, seed))

    print(f"计划 runs: {len(run_list)} (主检验 {len(PRIMARY_PROBLEMS)}×3×3={len(PRIMARY_PROBLEMS)*9}, "
          f"泛化 {len(GENERALIZATION_PROBLEMS)}×3×2={len(GENERALIZATION_PROBLEMS)*6})")

    results = []
    for i, (pid, arm, seed) in enumerate(run_list):
        sid = make_submission_id(pid, arm, seed)
        # 跳过已完成的
        manifest_path = RUNS_DIR / sid / "manifest.json"
        if manifest_path.exists():
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
            if m.get("status") == "COMPLETED":
                print(f"[{i+1}/{len(run_list)}] {pid}/{arm}/seed{seed} SKIP (已完成)")
                results.append(m)
                continue

        print(f"[{i+1}/{len(run_list)}] {pid}/{arm}/seed{seed} ...", end=" ", flush=True)
        try:
            m = generate_and_run(pid, arm, seed)
            results.append(m)
            print(f"exec={m['exec_status']} fid={m['fidelity_score']}")
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"problem_id": pid, "arm": arm, "seed": seed, "status": "ERROR", "error": str(e)})

    # 统计
    success = sum(1 for r in results if r.get("exec_status") == "success")
    by_arm = {}
    by_problem = {}
    by_status = {}
    for r in results:
        a = r.get("arm", "?")
        p = r.get("problem_id", "?")
        s = r.get("status", "?")
        by_arm[a] = by_arm.get(a, 0) + 1
        by_problem[p] = by_problem.get(p, 0) + 1
        by_status[s] = by_status.get(s, 0) + 1

    summary = {
        "total": len(results),
        "exec_success": success,
        "exec_success_rate": round(success / len(results), 4) if results else 0,
        "by_arm": by_arm,
        "by_problem": by_problem,
        "by_status": by_status,
        "runs": results,
    }
    write_json(FORMAL_DIR / "formal_results.json", summary)

    print(f"\n{'=' * 60}")
    print(f"全量完成: {success}/{len(results)} exec success (rate={summary['exec_success_rate']})")
    print(f"by_status: {by_status}")
    print(f"by_arm: {by_arm}")
    return summary


def show_status():
    """查看已完成 runs 统计。"""
    manifests = list(RUNS_DIR.glob("*/manifest.json"))
    if not manifests:
        print("No runs found.")
        return
    total = len(manifests)
    success = 0
    by_arm = {}
    by_problem = {}
    for mp in manifests:
        m = json.loads(mp.read_text(encoding="utf-8"))
        if m.get("exec_status") == "success":
            success += 1
        a = m.get("arm", "?")
        p = m.get("problem_id", "?")
        by_arm[a] = by_arm.get(a, 0) + 1
        by_problem[p] = by_problem.get(p, 0) + 1
    print(f"Runs: {total} total, {success} exec_success")
    print(f"by_arm: {by_arm}")
    print(f"by_problem: {by_problem}")


def main():
    if len(sys.argv) < 2:
        print("用法: py -3.12 k003_formal_runner.py [preflight|full|status]")
        return 1
    cmd = sys.argv[1]
    if cmd == "preflight":
        ok = run_preflight()
        return 0 if ok else 1
    elif cmd == "full":
        run_full()
        return 0
    elif cmd == "status":
        show_status()
        return 0
    else:
        print(f"未知命令: {cmd}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
