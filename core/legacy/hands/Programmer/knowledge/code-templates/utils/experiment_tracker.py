"""
实验记录系统
来源: 高教杯论文实验管理需求
适用问题: 记录实验参数、结果、时间，支持追溯和复现
输入: 实验配置
输出: 实验日志、结果对比
"""

import json
import time
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from pathlib import Path
import numpy as np
import pandas as pd


@dataclass
class Experiment:
    """实验记录"""
    name: str
    description: str
    params: Dict[str, Any]
    metrics: Dict[str, float] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: str = "running"
    notes: str = ""
    git_hash: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ExperimentTracker:
    """
    实验记录器
    
    支持：
    1. 实验创建和记录
    2. 参数和指标跟踪
    3. 实验对比
    4. 结果复现
    """
    
    def __init__(self, project_dir: str = "experiments"):
        self.project_dir = Path(project_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        self.experiments: Dict[str, Experiment] = {}
        self.current_experiment: Optional[Experiment] = None
        
        # 加载历史实验
        self._load_experiments()
    
    def _load_experiments(self):
        """加载历史实验"""
        for exp_file in self.project_dir.glob("*.json"):
            try:
                with open(exp_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    exp = Experiment(**data)
                    self.experiments[exp.name] = exp
            except:
                pass
    
    def _save_experiment(self, exp: Experiment):
        """保存实验"""
        exp_file = self.project_dir / f"{exp.name}.json"
        with open(exp_file, 'w', encoding='utf-8') as f:
            json.dump(exp.to_dict(), f, indent=2, ensure_ascii=False, default=str)
    
    def create_experiment(self, name: str, description: str, 
                         params: Dict[str, Any], tags: List[str] = None) -> Experiment:
        """创建新实验"""
        # 检查是否已存在
        if name in self.experiments:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"{name}_{timestamp}"
        
        exp = Experiment(
            name=name,
            description=description,
            params=params,
            tags=tags or [],
            start_time=time.time()
        )
        
        self.experiments[name] = exp
        self.current_experiment = exp
        
        print(f"实验 '{name}' 已创建")
        print(f"  描述: {description}")
        print(f"  参数: {params}")
        
        return exp
    
    def log_params(self, params: Dict[str, Any]):
        """记录参数"""
        if self.current_experiment:
            self.current_experiment.params.update(params)
            print(f"  参数已更新: {params}")
    
    def log_metrics(self, metrics: Dict[str, float]):
        """记录指标"""
        if self.current_experiment:
            self.current_experiment.metrics.update(metrics)
            print(f"  指标已记录: {metrics}")
    
    def log_artifact(self, artifact_path: str):
        """记录产物（模型、图表等）"""
        if self.current_experiment:
            self.current_experiment.artifacts.append(artifact_path)
            print(f"  产物已记录: {artifact_path}")
    
    def log_note(self, note: str):
        """记录笔记"""
        if self.current_experiment:
            self.current_experiment.notes += f"\n{note}"
    
    def finish_experiment(self, status: str = "completed"):
        """完成实验"""
        if self.current_experiment:
            self.current_experiment.end_time = time.time()
            self.current_experiment.duration = (
                self.current_experiment.end_time - self.current_experiment.start_time
            )
            self.current_experiment.status = status
            
            # 保存
            self._save_experiment(self.current_experiment)
            
            print(f"\n实验 '{self.current_experiment.name}' {status}")
            print(f"  耗时: {self.current_experiment.duration:.2f}秒")
            print(f"  指标: {self.current_experiment.metrics}")
            
            self.current_experiment = None
    
    def compare_experiments(self, exp_names: List[str]) -> pd.DataFrame:
        """对比多个实验"""
        records = []
        
        for name in exp_names:
            if name in self.experiments:
                exp = self.experiments[name]
                record = {
                    'name': name,
                    'description': exp.description,
                    'duration': exp.duration,
                    'status': exp.status,
                    **exp.params,
                    **exp.metrics
                }
                records.append(record)
        
        return pd.DataFrame(records)
    
    def get_best_experiment(self, metric: str, higher_better: bool = True) -> Optional[Experiment]:
        """获取最优实验"""
        best_exp = None
        best_value = None
        
        for exp in self.experiments.values():
            if exp.status != "completed":
                continue
            
            if metric not in exp.metrics:
                continue
            
            value = exp.metrics[metric]
            
            if best_value is None:
                best_value = value
                best_exp = exp
            elif higher_better and value > best_value:
                best_value = value
                best_exp = exp
            elif not higher_better and value < best_value:
                best_value = value
                best_exp = exp
        
        return best_exp
    
    def generate_report(self) -> str:
        """生成实验报告"""
        report = [
            "=" * 60,
            "实验报告",
            "=" * 60,
            f"总实验数: {len(self.experiments)}",
            f"已完成: {sum(1 for e in self.experiments.values() if e.status == 'completed')}",
            ""
        ]
        
        for name, exp in sorted(self.experiments.items()):
            report.append(f"实验: {name}")
            report.append(f"  描述: {exp.description}")
            report.append(f"  状态: {exp.status}")
            report.append(f"  耗时: {exp.duration or 0:.2f}秒")
            report.append(f"  指标: {exp.metrics}")
            report.append("")
        
        return "\n".join(report)


def run_example():
    """
    示例：优化实验记录
    """
    print("=" * 60)
    print("实验记录系统示例")
    print("=" * 60)
    
    # 创建跟踪器
    tracker = ExperimentTracker("my_experiments")
    
    # 实验1: 基线模型
    exp1 = tracker.create_experiment(
        name="baseline_rf",
        description="随机森林基线模型",
        params={"n_estimators": 100, "max_depth": 10},
        tags=["baseline", "rf"]
    )
    tracker.log_metrics({"accuracy": 0.85, "f1": 0.83})
    tracker.finish_experiment()
    
    # 实验2: 优化模型
    exp2 = tracker.create_experiment(
        name="optimized_xgb",
        description="XGBoost优化模型",
        params={"n_estimators": 200, "max_depth": 6, "learning_rate": 0.1},
        tags=["optimized", "xgb"]
    )
    tracker.log_metrics({"accuracy": 0.89, "f1": 0.87})
    tracker.finish_experiment()
    
    # 对比实验
    print("\n" + "=" * 60)
    print("实验对比")
    print("=" * 60)
    
    comparison = tracker.compare_experiments(["baseline_rf", "optimized_xgb"])
    print(comparison.to_string())
    
    # 获取最优实验
    best = tracker.get_best_experiment("accuracy")
    if best:
        print(f"\n最优实验: {best.name}")
        print(f"  准确率: {best.metrics['accuracy']:.4f}")
    
    # 生成报告
    print("\n" + tracker.generate_report())


if __name__ == "__main__":
    run_example()
