# -*- coding: utf-8 -*-
"""P2-2 / P3-3 验收：外部 Constructor 适配器（目录加载真实可用，
未配置通道如实报错；禁止 fallback/伪造）。"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest  # noqa: E402

from runtime.constructors.adapters.mathmodel_agent import (  # noqa: E402
    ConstructorNotConfigured, MathModelAgentAdapter,
)
from runtime.constructors.adapters.pi import PiAdapter  # noqa: E402
from runtime.constructors.adapters.reference import ReferenceConstructor  # noqa: E402
from runtime.constructors.protocol import ConstructionBundle  # noqa: E402
from runtime.constructors.registry import (  # noqa: E402
    ConstructorRegistry, apply_bundle,
)


def _write_bundle_dir(root: Path, qid: str = "Q001") -> Path:
    d = root / "mma_out"
    d.mkdir(parents=True, exist_ok=True)
    (d / "model_ir.json").write_text(json.dumps({
        "ir_version": "1.0", "model_id": f"M-{qid}",
        "problem_binding": {"problem_id": "P1", "sub_question_id": qid,
                            "problem_sha256": "0" * 64},
        "model_family": {"primary": "queueing"},
    }), encoding="utf-8")
    (d / "code.py").write_text("def solve(inputs):\n    return {'x': 1}\n",
                               encoding="utf-8")
    (d / "output_mapping.json").write_text(
        json.dumps({"x": "result_x"}), encoding="utf-8")
    (d / "specs.json").write_text(json.dumps({"limits": []}), encoding="utf-8")
    return d


class TestMathModelAgentAdapter:
    def test_unconfigured_raises_honest_error(self):
        a = MathModelAgentAdapter()
        with pytest.raises(ConstructorNotConfigured):
            a.construct({"question": "Q001"})

    def test_directory_loading_builds_bundle(self, tmp_path):
        d = _write_bundle_dir(tmp_path)
        a = MathModelAgentAdapter(source_dir=d)
        b = a.construct({"question": "Q001"})
        assert isinstance(b, ConstructionBundle)
        assert b.model_ir["model_family"]["primary"] == "queueing"
        assert b.code.startswith("def solve")
        assert b.output_mapping == {"x": "result_x"}
        assert b.constructor == "mathmodel-agent"
        assert a.describe()["mode"] == "directory-loading"


class TestPiAdapter:
    def test_unconfigured_raises(self):
        with pytest.raises(ConstructorNotConfigured):
            PiAdapter().construct({"question": "Q001"})

    def test_directory_loading(self, tmp_path):
        d = _write_bundle_dir(tmp_path)
        b = PiAdapter(source_dir=d).construct({"question": "Q001"})
        assert b.constructor == "pi"
        assert b.model_ir["model_id"] == "M-Q001"


class TestReferenceConstructor:
    def test_unknown_question_raises(self):
        with pytest.raises(KeyError):
            ReferenceConstructor({}).construct({"question": "Q9"})

    def test_template_bundle_and_revision_of(self):
        tpl = {"Q001": {"model_ir": {"model_id": "M1"},
                        "code": "def solve(i): return {}",
                        "output_mapping": {"x": "y"},
                        "validation_spec": {"limits": []},
                        "revision_of": "M0"}}
        b = ReferenceConstructor(tpl).construct(
            {"question": "Q001"}, {"revision_of": "M0"})
        assert b.capability_level == "C5"
        assert b.revision_of == "M0"


class TestRegistryIntegration:
    def test_register_and_apply_bundle(self, tmp_path):
        reg = ConstructorRegistry()
        d = _write_bundle_dir(tmp_path)
        reg.register(MathModelAgentAdapter(source_dir=d))
        assert reg.has("mathmodel-agent")
        b = reg.get("mathmodel-agent").construct({"question": "Q001"})
        # apply_bundle 需要 RuntimeSession——构造最小 fake
        class FakeShared:
            def __init__(self):
                self.shared = {}
        class FakeExecutor:
            def __init__(self):
                self.shared = {}
        class FakeSession:
            def __init__(self):
                self.executor_impl = FakeExecutor()
        shared = apply_bundle(FakeSession(), b, workdir=str(tmp_path))
        assert shared["external_model_irs"]["Q001"]["model_id"] == "M-Q001"
        assert shared["external_code"]["Q001"].startswith("def solve")
        assert shared["_workdir"] == str(tmp_path)
