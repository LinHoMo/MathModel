# -*- coding: utf-8 -*-
"""Constructor 注册表（P1-1）：注册 / 获取 / 把 bundle 应用到 RuntimeSession。

apply_bundle 是"外部 Constructor 产物 → handlers 注入"的官方通道：
vs001_driver.inject / m3_driver.inject_candidates 的手写注入统一走这里，
保证同一契约（external_model_irs/external_code/output_mappings/
validation_specs）。

LLM-free：纯注册与映射，无 LLM 调用。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .protocol import ConstructionBundle, ConstructorAdapter

if TYPE_CHECKING:
    from modeling_harness.runtime.execution.session import RuntimeSession


class ConstructorError(RuntimeError):
    pass


class ConstructorRegistry:
    """Adapter 注册表（单例即可；构造可换）。"""

    def __init__(self) -> None:
        self._adapters: dict[str, ConstructorAdapter] = {}

    def register(self, adapter: ConstructorAdapter) -> None:
        if not isinstance(adapter, ConstructorAdapter):
            raise ConstructorError(
                f"{adapter!r} 不是 ConstructorAdapter 实例")
        if adapter.name in self._adapters:
            raise ConstructorError(f"Constructor 已注册: {adapter.name}")
        self._adapters[adapter.name] = adapter

    def get(self, name: str) -> ConstructorAdapter:
        if name not in self._adapters:
            raise ConstructorError(
                f"Constructor 未注册: {name}（可选: {sorted(self._adapters)}）")
        return self._adapters[name]

    def list(self) -> list[dict]:
        return [a.describe() for a in self._adapters.values()]

    def has(self, name: str) -> bool:
        return name in self._adapters


def apply_bundle(session: "RuntimeSession", bundle: ConstructionBundle,
                 workdir: str | None = None) -> dict:
    """把 ConstructionBundle 应用到 RuntimeSession 的 shared 注入区。

    - external_model_irs: {question: model_ir}
    - external_code: {question: code}
    - output_mappings: {question: output_mapping}
    - validation_specs: {question: validation_spec}
    - external_revision: {question: revision_of}（M2 场景）
    返回 shared 字典（供测试/驱动读取）。
    """
    shared = session.executor_impl.shared
    q = bundle.question
    shared.setdefault("external_model_irs", {})[q] = bundle.model_ir
    if bundle.code:
        shared.setdefault("external_code", {})[q] = bundle.code
    if bundle.output_mapping:
        shared.setdefault("output_mappings", {})[q] = bundle.output_mapping
    if bundle.validation_spec:
        shared.setdefault("validation_specs", {})[q] = bundle.validation_spec
    if bundle.revision_of:
        shared.setdefault("external_revision", {})[q] = bundle.revision_of
    if workdir is not None:
        shared["_workdir"] = str(workdir)
    return shared
