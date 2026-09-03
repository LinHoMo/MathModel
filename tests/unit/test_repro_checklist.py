# -*- coding: utf-8 -*-
"""repro_checklist.py 的单元测试：清单生成、哈希漂移检测、一等方依赖过滤。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "tools"))

import repro_checklist as R  # noqa: E402


def _setup(tmp_path, monkeypatch):
    proj = tmp_path / "projects" / "demo"
    (proj / "code").mkdir(parents=True)
    (proj / "figures").mkdir(parents=True)
    (proj / "output").mkdir(parents=True)
    (proj / "code" / "main.py").write_text("import numpy\n", encoding="utf-8")
    (proj / "figures" / "all_results.json").write_text(
        json.dumps({"a": 12.34}), encoding="utf-8")
    monkeypatch.setattr(R, "project_dir", lambda p: tmp_path / "projects" / p)
    return proj


def test_generate_writes_manifest(tmp_path, monkeypatch):
    proj = _setup(tmp_path, monkeypatch)
    assert R.generate("demo") == 0
    m = json.loads((proj / "output/reproducibility.json").read_text(encoding="utf-8"))
    assert m["reproduce_command"].startswith("python code/main.py")
    assert m["random_seed"] == 42
    assert "all_results_json" in m["file_hashes"]
    assert any(d["name"] == "numpy" for d in m["dependencies"])


def test_verify_pass_when_unchanged(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    assert R.generate("demo") == 0
    assert R.verify("demo") == 0


def test_verify_fail_when_code_changed(tmp_path, monkeypatch):
    proj = _setup(tmp_path, monkeypatch)
    assert R.generate("demo") == 0
    (proj / "code" / "main.py").write_text("import numpy\nx = 1\n", encoding="utf-8")
    assert R.verify("demo") == 1


def test_verify_fail_when_artifact_missing(tmp_path, monkeypatch):
    proj = _setup(tmp_path, monkeypatch)
    assert R.generate("demo") == 0
    (proj / "figures" / "all_results.json").unlink()
    assert R.verify("demo") == 1


def test_first_party_modules_not_third_party(tmp_path, monkeypatch):
    """仓库自有模块（code/ 内的 chain.py）不应被误判为第三方依赖。"""
    proj = _setup(tmp_path, monkeypatch)
    (proj / "code" / "chain.py").write_text("def f(): pass\n", encoding="utf-8")
    (proj / "code" / "main.py").write_text("import chain\nimport numpy\n",
                                          encoding="utf-8")
    assert R.generate("demo") == 0
    m = json.loads((proj / "output/reproducibility.json").read_text(encoding="utf-8"))
    pkgs = {d["name"] for d in m["dependencies"]}
    assert "chain" not in pkgs, f"一等方模块被误判: {pkgs}"
    assert "numpy" in pkgs


def test_show_returns_zero(tmp_path, monkeypatch, capsys):
    _setup(tmp_path, monkeypatch)
    assert R.generate("demo") == 0
    assert R.show("demo") == 0
    out = capsys.readouterr().out
    assert "python code/main.py" in out
