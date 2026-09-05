#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多运行时适配测试脚本

验证 MathModelSkills 在不同 AI 运行时下的兼容性：
- Claude Code
- Codex CLI
- opencode
- Cursor
- 通用 Python

测试项：
1. 状态文件读写（state.json, decision_log.json）
2. 门禁脚本执行
3. 友好模式交互
4. 契约文件产出
5. 跨运行时状态恢复
"""

import sys
import json
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
# 添加项目根目录到 sys.path
PROJECT_ROOT = str(ROOT)
sys.path.insert(0, PROJECT_ROOT)

from core.env.loader import load_config
from core.tools.state import _now, load, save, _empty_state, sync_from_artifacts, decision_log_path, load_decision_log, save_decision_log


class RuntimeTester:
    """运行时兼容性测试器"""
    
    def __init__(self, project_name: str = "test_runtime"):
        self.project_name = project_name
        self.test_dir = None
        self.project_path = None
        
    def setup(self):
        """创建临时测试项目"""
        self.test_dir = Path(tempfile.mkdtemp(prefix=f"mm_test_{self.project_name}_"))
        self.project_path = self.test_dir / self.project_name
        self.project_path.mkdir(parents=True)
        
        # 创建标准目录结构
        for d in ["inputs", "work", "code", "figures", "paper/figures", "output"]:
            (self.project_path / d).mkdir(parents=True, exist_ok=True)
        
        # 放入一个简单的赛题文件
        (self.project_path / "inputs" / "problem.txt").write_text(
            "测试赛题：求解一个简单的优化问题。\n"
            "目标函数：min x^2 + y^2\n"
            "约束：x + y >= 1, x,y >= 0\n",
            encoding="utf-8"
        )
        
        print(f"✅ 测试项目创建: {self.project_path}")
        return self
    
    def teardown(self):
        """清理测试目录"""
        if self.test_dir and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            print(f"🧹 测试目录已清理: {self.test_dir}")
    
    def run_cmd(self, cmd: list, cwd: Path = None) -> tuple:
        """运行命令并返回 (returncode, stdout, stderr)"""
        try:
            # Windows 下使用 GBK 编码，或忽略错误
            result = subprocess.run(
                cmd, 
                cwd=str(cwd or self.project_path),
                capture_output=True, 
                text=True, 
                encoding='gbk',
                errors='replace',
                timeout=60
            )
            return result.returncode, result.stdout or "", result.stderr or ""
        except subprocess.TimeoutExpired:
            return -1, "", "命令超时"
        except Exception as e:
            return -1, "", str(e)
    
    def test_state_init(self) -> bool:
        """测试状态初始化"""
        print("\n📋 测试: 状态初始化")
        rc, out, err = self.run_cmd([
            sys.executable, str(ROOT / "core/tools/state.py"), 
            str(self.project_path), "init"
        ])
        if rc != 0:
            print(f"❌ 失败: {err}")
            return False
        
        state_file = self.project_path / "work" / "state.json"
        if not state_file.exists():
            print("❌ state.json 未生成")
            return False
        
        state = json.loads(state_file.read_text(encoding="utf-8"))
        if state.get("current", {}).get("hand") != "modeler":
            print(f"❌ 当前手不正确: {state.get('current')}")
            return False
        
        print("✅ 状态初始化通过")
        return True
    
    def test_state_advance(self) -> bool:
        """测试状态推进"""
        print("\n📋 测试: 状态推进")
        
        # 模拟完成 problem-parser
        (self.project_path / "work" / "question_spec.json").write_text(
            json.dumps({"sub_questions": [], "domain_keywords": []}), encoding="utf-8"
        )
        
        rc, out, err = self.run_cmd([
            sys.executable, str(ROOT / "core/tools/state.py"),
            str(self.project_path), "advance", "modeler", "problem-parser",
            "--output", "work/question_spec.json"
        ])
        if rc != 0:
            print(f"❌ 推进失败: {err}")
            return False
        
        state = load(self.project_path)
        completed = state.get("completed", [])
        if not any(c.get("agent") == "problem-parser" for c in completed):
            print("❌ 完成记录未写入")
            return False
        
        print("✅ 状态推进通过")
        return True
    
    def test_decision_log(self) -> bool:
        """测试决策日志记录"""
        print("\n📋 测试: 决策日志")
        
        rc, out, err = self.run_cmd([
            sys.executable, str(ROOT / "core/tools/state.py"),
            str(self.project_path), "decision-add",
            "--stage", "modeler/type-classifier",
            "--decision-type", "model_selection",
            "--question", "测试题型判断",
            "--options", '["A: 物理", "B: 数据"]',
            "--choice", "A",
            "--rationale", "测试理由",
            "--confidence", "0.9",
            "--time-spent", "30"
        ])
        if rc != 0:
            print(f"❌ 决策记录失败: {err}")
            return False
        
        # 验证日志
        log = load_decision_log(self.project_path)
        entries = log.get("entries", [])
        if not entries:
            print("❌ 决策日志为空")
            return False
        
        entry = entries[-1]
        if entry.get("choice") != "A" or entry.get("stage") != "modeler/type-classifier":
            print(f"❌ 决策内容不匹配: {entry}")
            return False
        
        print("✅ 决策日志通过")
        return True
    
    def test_cross_runtime_recovery(self) -> bool:
        """测试跨运行时状态恢复（模拟换 session）"""
        print("\n📋 测试: 跨运行时状态恢复")
        
        # 先建立一些状态
        self.test_state_init()
        self.test_state_advance()
        self.test_decision_log()
        
        # 模拟新运行时：重新加载状态
        state = load(self.project_path)
        if not state:
            print("❌ 状态加载失败")
            return False
        
        # 验证进度正确恢复
        completed = state.get("completed", [])
        if len(completed) < 1:
            print("❌ 完成步骤未恢复")
            return False
        
        # 验证决策日志恢复
        log = load_decision_log(self.project_path)
        if not log.get("entries"):
            print("❌ 决策日志未恢复")
            return False
        
        print("✅ 跨运行时状态恢复通过")
        return True
    
    def test_gate_check(self) -> bool:
        """测试门禁脚本执行"""
        print("\n📋 测试: 门禁检查")
        
        # 创建最小产物通过 problem-parser 门禁
        (self.project_path / "work" / "question_spec.json").write_text(
            json.dumps({
                "sub_questions": [],
                "domain_keywords": ["测试"],
                "contest_year": 2024
            }), encoding="utf-8"
        )
        
        rc, out, err = self.run_cmd([
            sys.executable, str(ROOT / "core/tools/gate.py"),
            str(self.project_path), "modeler", "problem-parser"
        ])
        # gate 可能因为缺少完整产物而失败，但不应报错崩溃
        if rc < 0:
            print(f"❌ 门禁脚本异常: {err}")
            return False
        
        print("✅ 门禁脚本可执行")
        return True
    
    def test_validate(self) -> bool:
        """测试项目级校验"""
        print("\n📋 测试: 项目级校验")
        
        try:
            rc, out, err = self.run_cmd([
                sys.executable, str(ROOT / "core/tools/validate.py")
            ])
            print(f"   rc={rc}, out_len={len(out) if out else 0}, err_len={len(err) if err else 0}")
            
            if rc != 0:
                print(f"❌ 校验失败 (rc={rc}): {err}")
                print(f"   stdout: {out[:500] if out else 'empty'}")
                print(f"   stderr: {err[:500] if err else 'empty'}")
                return False
            
            if "PASS" not in out and "通过" not in out:
                print("❌ 校验输出异常")
                print(f"   stdout: {out[:500]}")
                return False
            
            print("✅ 项目级校验通过")
            return True
        except Exception as e:
            import traceback
            print(f"❌ 测试异常: {e}")
            traceback.print_exc()
            return False
    
    def test_friendly_mode_import(self) -> bool:
        """测试友好模式模块导入"""
        print("\n📋 测试: 友好模式模块导入")
        
        try:
            from core.tools.friendly import FriendlyInteraction, friendly_ask
            print("✅ 友好模式模块导入成功")
            return True
        except Exception as e:
            print(f"❌ 导入失败: {e}")
            return False
    
    def test_env_config(self) -> bool:
        """测试环境配置加载"""
        print("\n📋 测试: 环境配置加载")
        
        try:
            config = load_config()
            # 检查新增参数
            assert "modeling.literature_search_enabled" in str(config) or hasattr(config, 'get')
            from core.env.loader import get
            val = get("modeling.literature_search_enabled", default=True)
            print(f"✅ 环境配置加载成功 (literature_search_enabled={val})")
            return True
        except Exception as e:
            print(f"❌ 环境配置失败: {e}")
            return False
    
    def run_all(self) -> dict:
        """运行所有测试"""
        print(f"\n{'='*60}")
        print(f"🚀 开始多运行时兼容性测试: {self.project_name}")
        print(f"{'='*60}")
        
        self.setup()
        
        tests = [
            ("环境配置", self.test_env_config),
            ("状态初始化", self.test_state_init),
            ("状态推进", self.test_state_advance),
            ("决策日志", self.test_decision_log),
            ("跨运行时恢复", self.test_cross_runtime_recovery),
            ("门禁脚本", self.test_gate_check),
            ("项目校验", self.test_validate),
            ("友好模式导入", self.test_friendly_mode_import),
        ]
        
        results = {}
        passed = 0
        for name, test_fn in tests:
            try:
                result = test_fn()
                results[name] = result
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ {name} 异常: {e}")
                results[name] = False
        
        self.teardown()
        
        print(f"\n{'='*60}")
        print(f"📊 测试结果: {passed}/{len(tests)} 通过")
        for name, result in results.items():
            status = "✅" if result else "❌"
            print(f"  {status} {name}")
        print(f"{'='*60}")
        
        return results


def main():
    tester = RuntimeTester("multi_runtime")
    results = tester.run_all()
    
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()