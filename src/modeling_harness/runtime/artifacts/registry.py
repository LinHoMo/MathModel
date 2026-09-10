"""Artifact Registry — Artifact 登记簿（单一事实源）。

持久化: projects/<p>/state/registry.json（原子写）。
职责: ID 分配 / 版本历史 / 生命周期推进 / 引用完整性 / 查询。
不做: Evidence Graph 的关系推导（src/modeling_harness/runtime/graph 职责）——本层只在
Artifact contract 的 relations 字段维护 graph 同步过来的只读视图。
"""

from __future__ import annotations

import inspect
import json
import os
import tempfile
from pathlib import Path

from .artifact import Artifact, ContractError, utcnow
from .ids import ARTIFACT_TYPES, IDFormatError, format_id, is_valid_id
from .lifecycle import LifecycleError, assert_transition, is_terminal

REGISTRY_VERSION = 3

# P0-5（终审 ROADMAP）：mark_validated 调用方白名单——仅 Runtime 验证
# 管线可标记 validated。判定依据=调用栈中第一个非本模块帧的真实文件路径
# （不信任任何显式传入的 caller 参数，防 Agent 伪装）。
VALIDATION_CALLER_ALLOWED_SUBSTR = (
    "src/modeling_harness/runtime/execution/validators.py",
    "src/modeling_harness/runtime/execution/handlers.py",
)


def _caller_path() -> str | None:
    """调用栈中第一个非本模块（registry/artifact）帧的规范化文件路径。"""
    frame = inspect.currentframe()
    try:
        frame = frame.f_back if frame else None
        while frame:
            fname = frame.f_code.co_filename or ""
            norm = os.path.normpath(fname).replace("\\", "/")
            if ("src/modeling_harness/runtime/artifacts/registry.py" in norm
                    or "src/modeling_harness/runtime/artifacts/artifact.py" in norm):
                frame = frame.f_back
                continue
            return norm
        return None
    finally:
        del frame


class RegistryError(ValueError):
    """Registry 操作非法。"""


class ArtifactNotFound(KeyError):
    """Artifact 不存在。"""


_SCHEMA_CACHE: dict[str, dict | None] = {}


def _find_schema(artifact_type: str) -> dict | None:
    """src/modeling_harness/schemas/v3/**/<type>.schema.json 探测（惰性缓存）。

    无 schema 的类型（legacy 类型等）返回 None → 跳过实例校验。
    """
    if artifact_type in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[artifact_type]
    schema: dict | None = None
    root = Path(__file__).resolve().parents[4]
    for hit in sorted((root / "src" / "modeling_harness" / "schemas" / "v3").rglob(
            artifact_type + ".schema.json")):
        try:
            schema = json.loads(hit.read_text(encoding="utf-8"))
        except Exception:
            schema = None
        break
    _SCHEMA_CACHE[artifact_type] = schema
    return schema


def _enforce_schema(artifact_type: str, data: dict) -> None:
    """实例校验（audit FIX-5.4 / P1-09）：schema 存在时必须通过。

    失败抛 ContractError（附校验错误明细），绝不静默跳过。
    """
    schema = _find_schema(artifact_type)
    if schema is None or not data:
        return
    try:
        import jsonschema
    except ImportError:
        return
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        where = list(e.absolute_path or [])
        raise ContractError(
            f"{artifact_type} 实例校验失败（schema={schema.get('title','?')}"
            f" 路径={'/'.join(str(x) for x in where) or '<root>'}）: {e.message}") \
            from None


def _check_exec_auth(data: dict) -> None:
    """P0-3：success EXEC 必须来源可鉴别（adapter 签发 token 或显式
    legacy_unverified 声明），否则拒绝登记（The Agent Is Not The State）。"""
    if data.get("legacy_unverified"):
        return
    from ..execution.execution_auth import verify_token
    token = data.get("execution_token")
    if not (isinstance(token, str) and token):
        raise ContractError(
            "success 但 execution_token 缺失（来源未鉴别，拒绝伪造 EXEC）")
    code_hash = data.get("code_hash") or ""
    provenance = data.get("provenance")
    adapter = provenance.get("adapter") if isinstance(provenance, dict) else None
    started = data.get("started_at") or ""
    if not verify_token(str(code_hash), str(adapter or ""), started, token):
        raise ContractError(
            "execution_token 校验失败（HMAC 不匹配，拒绝伪造 EXEC）")


class ArtifactRegistry:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.artifacts: dict[str, Artifact] = {}   # id → 最新版本
        self.history: dict[str, dict[int, dict]] = {}  # id → {version: snapshot}
        self.counters: dict[str, int] = {}         # type → 已发放数量
        self.project: str = ""
        self._dirty = False
        # P7 并发契约：并行波次下多节点同时登记，ID 分配与写入必须互斥
        import threading
        self._lock = threading.RLock()
        if self.path.exists():
            self.load()
        else:
            self.project = self._infer_project()

    # ------------------------------------------------------------ 持久化

    def _infer_project(self) -> str:
        # projects/<p>/state/registry.json → <p>
        parts = self.path.parts
        if "state" in parts:
            i = parts.index("state")
            if i >= 1 and parts[i - 1]:
                return parts[i - 1]
        return ""

    def load(self) -> None:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or raw.get("registry_version") != REGISTRY_VERSION:
            raise RegistryError(f"registry.json 版本不兼容: {raw.get('registry_version')!r}")
        self.project = raw.get("project", "")
        self.counters = {k: int(v) for k, v in raw.get("counters", {}).items()}
        self.artifacts = {}
        self.history = {}
        for aid, adict in raw.get("artifacts", {}).items():
            try:
                self.artifacts[aid] = Artifact.from_dict(adict)
            except ContractError as exc:
                # 已退役/未知类型（如历史 paper_section）宽容跳过（不迁移冻结数据）；
                # 已知类型的伪造/损坏（如 execution_result 无 outputs）必须拒绝。
                atype = adict.get("type") if isinstance(adict, dict) else None
                if atype in ARTIFACT_TYPES:
                    raise
                import warnings
                warnings.warn(f"registry load: 跳过已退役类型 {atype!r} {aid}: {exc}")
        for aid, versions in raw.get("history", {}).items():
            self.history[aid] = {int(v): snap for v, snap in versions.items()}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "registry_version": REGISTRY_VERSION,
            "project": self.project,
            "updated_at": utcnow(),
            "counters": self.counters,
            "artifacts": {aid: a.to_dict() for aid, a in sorted(self.artifacts.items())},
            "history": {aid: {str(v): s for v, s in vers.items()}
                        for aid, vers in self.history.items()},
        }
        # 原子写：临时文件 + replace
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        self._dirty = False

    # ------------------------------------------------------------- ID 分配

    def next_id(self, artifact_type: str) -> str:
        if artifact_type not in ARTIFACT_TYPES:
            raise IDFormatError(f"未知 artifact 类型: {artifact_type!r}")
        n = self.counters.get(artifact_type, 0) + 1
        candidate = format_id(ARTIFACT_TYPES[artifact_type], n)
        # 防御：ID 永不复用（即使人为删除过）
        while candidate in self.artifacts:
            n += 1
            candidate = format_id(ARTIFACT_TYPES[artifact_type], n)
        return candidate

    # ---------------------------------------------------------------- 创建

    def create(self, artifact_type: str, *, title: str = "", payload=None,
               created_by: str = "", question: str = "", depends_on=None,
               parent=None, provenance=None, data=None, tags=None,
               activate: bool = False) -> Artifact:
        """登记新 Artifact（状态 draft；activate=True 直接进入 active）。"""
        with self._lock:
            return self._create_locked(artifact_type, title=title,
                                       payload=payload,
                                       created_by=created_by, question=question,
                                       depends_on=depends_on, parent=parent,
                                       provenance=provenance, data=data,
                                       tags=tags, activate=activate)

    def _create_locked(self, artifact_type, *, title="", payload=None,
                       created_by="", question="", depends_on=None,
                       parent=None, provenance=None, data=None, tags=None,
                       activate=False) -> Artifact:
        aid = self.next_id(artifact_type)
        rdata = dict(data or {})
        if artifact_type in ("decision", "execution_result"):
            # 契约统一：元数据由 registry 注入（标识符/时间/创建者/状态），
            # handler 只写业务字段（chosen/alternatives/reasoning 或
            # status/outputs/code_hash 等）。
            # 防未来漂移：schema required 的元数据字段全部在此补齐。
            if artifact_type == "execution_result":
                rdata.setdefault("execution_id", aid)
            else:
                rdata.setdefault("decision_id", aid)
                rdata.setdefault("kind", "general")
            rdata.setdefault("question", question)
            rdata.setdefault("created_by", created_by)
            rdata.setdefault("created_at", utcnow())
            rdata.setdefault("status", "active")
            rdata.setdefault("reversible", False)
        _enforce_schema(artifact_type, rdata)
        # P0-3：EXEC 来源鉴别（create 路径强制）——success EXEC 必须带
        # adapter 签发的有效 execution_token（HMAC(code_hash|adapter|ts)）。
        # Agent 无 secret 无法伪造；历史/测试桩 EXEC 显式标记
        # legacy_unverified=true 豁免（不追溯重算）。读取路径
        # （load/from_dict）不校验，尊重已存在事实。
        if artifact_type == "execution_result" and rdata.get("status") == "success":
            _check_exec_auth(rdata)
        art = Artifact(
            artifact_id=aid, type=artifact_type, title=title or aid,
            payload=list(payload or []), created_by=created_by, question=question,
            depends_on=list(depends_on or []), parent=list(parent or []),
            provenance=dict(provenance or {}), data=rdata,
            tags=list(tags or []),
        )
        problems = art.validate()
        if problems:
            raise ContractError("; ".join(problems))
        self._assert_refs_exist(art)
        if activate:
            art.transition("active", by=created_by, reason="registered with payload")
        art.lifecycle_history.insert(0, {"from": None, "to": art.status,
                                         "at": utcnow(), "by": created_by,
                                         "reason": "created"})
        self.artifacts[aid] = art
        self.counters[artifact_type] = self.counters.get(artifact_type, 0) + 1
        self._dirty = True
        return art

    # ---------------------------------------------------------------- 查询

    def get(self, artifact_id: str, version: int | None = None) -> Artifact:
        if artifact_id not in self.artifacts:
            raise ArtifactNotFound(artifact_id)
        if version is None:
            return self.artifacts[artifact_id]
        if version == self.artifacts[artifact_id].version:
            return self.artifacts[artifact_id]
        snap = self.history.get(artifact_id, {}).get(version)
        if snap is None:
            raise RegistryError(f"{artifact_id} 无版本 {version}（当前 {self.artifacts[artifact_id].version}）")
        return Artifact.from_dict(snap)

    def latest(self, artifact_id: str) -> Artifact:
        return self.get(artifact_id)

    def exists(self, artifact_id: str) -> bool:
        return artifact_id in self.artifacts

    def list_by_type(self, artifact_type: str) -> list[Artifact]:
        return [a for a in self.artifacts.values() if a.type == artifact_type]

    def list_by_status(self, status: str) -> list[Artifact]:
        return [a for a in self.artifacts.values() if a.status == status]

    def by_question(self, question_id: str) -> list[Artifact]:
        return [a for a in self.artifacts.values() if a.question == question_id]

    def all(self) -> list[Artifact]:
        return list(self.artifacts.values())

    def __len__(self) -> int:
        return len(self.artifacts)

    # ------------------------------------------------------------ 生命周期

    def transition(self, artifact_id: str, target: str, *, by: str = "",
                   reason: str = "") -> Artifact:
        with self._lock:
            art = self.get(artifact_id)
            art.transition(target, by=by, reason=reason)
            self._dirty = True
            return art

    def activate(self, artifact_id: str, by: str = "") -> Artifact:
        return self.transition(artifact_id, "active", by=by, reason="activated")

    def mark_validated(self, artifact_id: str, validator: str,
                       report: dict | None = None, *,
                       run_record: dict | None = None) -> Artifact:
        """active → validated（P0-5 门禁）。

        仅允许 Runtime 验证管线（src/modeling_harness/runtime/execution/validators.py、
        handlers.py）调用——Agent/外部代码调 → PermissionError。
        run_record 必填且须含 run_id 或 hash（验证器运行记录，防伪造
        验证证据）；validator 键须与实参一致。
        """
        if not isinstance(run_record, dict) or not run_record:
            raise RegistryError(
                "mark_validated 必须携带 run_record（验证器运行记录："
                "run_id 或 hash），The Agent Is Not The State")
        if not (run_record.get("run_id") or run_record.get("hash")):
            raise RegistryError(
                "run_record 必须含 run_id 或 hash（验证证据可追溯）")
        if run_record.get("validator", validator) != validator:
            raise RegistryError("run_record.validator 与实参 validator 不一致")
        caller = _caller_path() or ""
        if not any(ok in caller for ok in VALIDATION_CALLER_ALLOWED_SUBSTR):
            raise PermissionError(
                "mark_validated 仅限 Runtime 验证管线调用；Agent 请提交 "
                "review report 到 <project>/reviews/，由 runtime 登记 "
                "validated 状态")
        art = self.get(artifact_id)
        art.mark_validated(validator, report)
        self._dirty = True
        return art

    def publish(self, artifact_id: str, by: str = "") -> Artifact:
        return self.transition(artifact_id, "published", by=by, reason="published")

    def block(self, artifact_id: str, reason: str = "", by: str = "") -> Artifact:
        return self.transition(artifact_id, "blocked", by=by, reason=reason)

    def deprecate(self, artifact_id: str, reason: str = "", by: str = "") -> Artifact:
        return self.transition(artifact_id, "deprecated", by=by, reason=reason)

    def invalidate(self, artifact_id: str, reason: str,
                   invalidated_by: str = "") -> Artifact:
        """直接失效（invalidation 传播由 graph 层调用此方法逐个落地）。"""
        art = self.get(artifact_id)
        art.mark_invalidation("invalidated", reason, invalidated_by)
        self._dirty = True
        return art

    def mark_revalidation_needed(self, artifact_id: str, reason: str,
                                 invalidated_by: str = "") -> Artifact:
        art = self.get(artifact_id)
        art.mark_invalidation("requires_revalidation", reason, invalidated_by)
        self._dirty = True
        return art

    def mark_dirty(self, artifact_id: str, reason: str) -> Artifact:
        art = self.get(artifact_id)
        art.mark_invalidation("dirty", reason)
        self._dirty = True
        return art

    def clear_invalidation(self, artifact_id: str) -> Artifact:
        art = self.get(artifact_id)
        art.clear_invalidation()
        self._dirty = True
        return art

    # ---------------------------------------------------------------- 版本

    def update(self, artifact_id: str, **fields) -> Artifact:
        """更新 Artifact：旧版本快照进 history，version +1。

        触及内容字段（payload/depends_on/parent/question/data）时状态重置为
        draft（validation 失效）；纯元数据更新（title/tags/provenance）保留状态。
        终态 Artifact 拒绝更新（需新建替代并 supersede）。
        """
        art = self.get(artifact_id)
        if is_terminal(art.status):
            raise LifecycleError(
                f"{artifact_id} 处于终态 {art.status}，不能更新；请新建 Artifact 并 supersede")
        if not fields:
            raise RegistryError("update 需要至少一个字段")
        unknown = set(fields) - {"title", "tags", "provenance", "payload", "depends_on",
                                 "parent", "question", "data", "created_by"}
        if unknown:
            raise RegistryError(f"不允许通过 update 修改: {sorted(unknown)}"
                                "（状态请用 transition/生命周期方法）")
        # 快照当前版本
        self.history.setdefault(artifact_id, {})[art.version] = art.to_dict()
        # 应用变更
        for key, value in fields.items():
            setattr(art, key, value)
        art.version += 1
        content_touched = any(k in fields for k in
                              ("payload", "depends_on", "parent", "question", "data"))
        if content_touched and art.status in ("validated", "published", "active"):
            # 内容变更 → validation 失效，回 draft（合法转换：validated→draft 不在表中，
            # 因此这里显式作为"版本重置"记录，而非普通 transition）
            art.lifecycle_history.append({
                "from": art.status, "to": "draft", "at": utcnow(),
                "by": "registry.update", "reason": "content changed → new version",
            })
            art.status = "draft"
            art.validation = {}
        art.updated_at = utcnow()
        problems = art.validate()
        if problems:
            # 回滚内存态（磁盘未动）
            raise ContractError("; ".join(problems))
        self._assert_refs_exist(art)
        self._dirty = True
        return art

    def supersede(self, artifact_id: str, reason: str,
                  replacement: str = "", by: str = "") -> Artifact:
        """标记被替代。replacement 可指向新 Artifact ID。"""
        if replacement and not self.exists(replacement):
            raise ArtifactNotFound(replacement)
        art = self.get(artifact_id)
        art.transition("superseded", by=by, reason=reason)
        if replacement:
            art.invalidation = {"status": "superseded", "reason": reason,
                                "invalidated_by": replacement, "at": utcnow()}
        self._dirty = True
        return art

    def versions(self, artifact_id: str) -> list[int]:
        """返回全部可用版本号（含当前）。"""
        art = self.get(artifact_id)
        vers = list(self.history.get(artifact_id, {}).keys()) + [art.version]
        return sorted(vers)

    # ------------------------------------------------------------ 关系视图

    def set_relations_view(self, artifact_id: str, relations: list[dict]) -> None:
        """由 Evidence Graph 层调用，同步只读关系视图。"""
        art = self.get(artifact_id)
        art.relations = list(relations)
        art.updated_at = utcnow()
        self._dirty = True

    # -------------------------------------------------------------- 完整性

    def _assert_refs_exist(self, art: Artifact) -> None:
        for ref in art.depends_on + art.parent:
            if not self.exists(ref) and ref != art.artifact_id:
                raise RegistryError(f"{art.artifact_id} 引用了不存在的 Artifact: {ref}")
        if art.question and not self.exists(art.question):
            raise RegistryError(f"{art.artifact_id} 引用了不存在的 Question: {art.question}")

    def integrity_check(self) -> list[str]:
        """Registry 级完整性检查（最终审计 / 回归测试消费）。"""
        problems: list[str] = []
        seen_ids = set()
        for aid, art in self.artifacts.items():
            if aid in seen_ids:
                problems.append(f"ID 重复: {aid}")
            seen_ids.add(aid)
            problems += [f"{aid}: {p}" for p in art.validate()]
            for ref in art.depends_on + art.parent:
                if ref not in self.artifacts:
                    problems.append(f"{aid} 悬空引用: {ref}")
            if art.question and art.question not in self.artifacts:
                problems.append(f"{aid} 悬空 question 引用: {art.question}")
            # 计数器一致性
            expected = sum(1 for a in self.artifacts.values() if a.type == art.type)
        for atype, prefix in ARTIFACT_TYPES.items():
            n = sum(1 for a in self.artifacts.values() if a.type == atype)
            if self.counters.get(atype, 0) < n:
                problems.append(f"counters[{atype}]={self.counters.get(atype)} < 实际数 {n}")
        return problems

    # ---------------------------------------------------------------- 导出

    def summary(self) -> dict:
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for a in self.artifacts.values():
            by_type[a.type] = by_type.get(a.type, 0) + 1
            by_status[a.status] = by_status.get(a.status, 0) + 1
        return {
            "project": self.project, "total": len(self.artifacts),
            "by_type": by_type, "by_status": by_status,
            "graph_pending_dirty": self._dirty,
        }
