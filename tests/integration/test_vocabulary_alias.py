# -*- coding: utf-8 -*-
"""G3 Vocabulary validity — 词表别名解析回归测试（K001 RQ5 词表错位回归）。

背景：K001 RQ5 中 allowed_model_families（dynamic_programming）与生成侧
model_family.primary（discrete_recurrence）严格字符串匹配产生 false negative。
K002 起：单一受控词表 catalog/model_families.yaml，命中判定 = 任意名词可解析
到 canonical id（primary OR secondary OR mechanism OR solver）。

本测试锁定 K001/B0-R2 出现过的所有错位对，防止词表回归。
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import pytest
import yaml

FAMILIES_YAML = REPO / "src" / "modeling_harness" / "catalog" / "model_families.yaml"


@pytest.fixture(scope="module")
def vocab():
    doc = yaml.safe_load(FAMILIES_YAML.read_text(encoding="utf-8"))
    aliases = {}
    for fam in doc["canonical_families"]:
        aliases[fam["id"]] = fam["id"]
        for a in fam.get("aliases", []):
            aliases[a] = fam["id"]
        for m in fam.get("mechanism", []):
            aliases[m] = fam["id"]
        for m in fam.get("methods", []):
            aliases[m] = fam["id"]
        for s in fam.get("solvers", []):
            aliases[s] = fam["id"]
    return aliases


def resolve(term, vocab):
    return vocab.get(term, "OUT_OF_CATALOG")


class TestVocabularyAliasResolution:
    """K001/B0-R2 出现过的词表错位对必须全部解析到同一 canonical。"""

    @pytest.mark.parametrize("alias,canonical", [
        # K001 RQ5 核心错位对
        ("discrete_recurrence", "dynamic_programming"),
        ("dp", "dynamic_programming"),
        ("bellman_recurrence", "dynamic_programming"),
        # B0-R2 2018_A
        ("pde_transient_heat_conduction", "numerical_pde"),
        ("heat_transfer", "numerical_pde"),
        ("finite_difference", "numerical_pde"),
        # K001 2019_C
        ("queueing_threshold_decision", "queuing_theory"),
        ("queueing_theory", "queuing_theory"),
        ("mmc_analysis", "queuing_theory"),
        # K001 2024_A
        ("hybrid_geometry_optimization", "kinematic_geometry"),
        ("geometric", "kinematic_geometry"),
        ("multibody_dynamics", "kinematic_geometry"),
        # K001/B0 2020_B
        ("resource_allocation_optimization", "optimization"),
        ("integer_programming", "optimization"),
        ("constrained_optimization", "optimization"),
        # K001 2022_C
        ("supervised_classification", "statistical_modeling"),
        ("classical_timeseries", "statistical_modeling"),
        # 泛化
        ("nash_equilibrium", "game_theory"),
        ("network_flow", "graph_algorithm"),
        ("monte_carlo", "simulation"),
        ("kmeans", "clustering"),
        ("pca", "dimensionality_reduction"),
    ])
    def test_alias_resolves(self, alias, canonical, vocab):
        assert resolve(alias, vocab) == canonical, \
            f"词表错位回归：{alias} 未解析到 {canonical}"

    def test_out_of_catalog_not_auto_judged(self, vocab):
        """未命名词 → OUT_OF_CATALOG（不自动判错，与 K001 口径一致）。"""
        assert resolve("some_exotic_method", vocab) == "OUT_OF_CATALOG"

    def test_all_families_roundtrip(self, vocab):
        """canonical id 自身可解析（18 族全部可往返）。"""
        doc = yaml.safe_load(FAMILIES_YAML.read_text(encoding="utf-8"))
        for fam in doc["canonical_families"]:
            assert resolve(fam["id"], vocab) == fam["id"], fam["id"]

    def test_vocab_aliases_unique(self):
        """命名层（canonical id + aliases）唯一：同一别名不得映射多个族。

        mechanism/method/solver 是跨族共享的语义原语（如 state_transition
        同时是 dynamic_programming 与 markov_decision_process 的机制），
        允许共享——K002 族命中判定只用命名层（canonical/alias）解析，
        机制层仅用于"机制覆盖"报告，不做族判别（GATES G3 记录）。
        """
        doc = yaml.safe_load(FAMILIES_YAML.read_text(encoding="utf-8"))
        owner = {}
        for fam in doc["canonical_families"]:
            for key in ([fam["id"]] + fam.get("aliases", [])):
                if key in owner and owner[key] != fam["id"]:
                    pytest.fail(f"alias 冲突：{key} 同时属于 "
                                f"{owner[key]} 和 {fam['id']}")
                owner[key] = fam["id"]
