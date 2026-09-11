# -*- coding: utf-8 -*-
"""协议忠实化回归测试：simulator_http.py 对齐 B 题附件2。

依据（附件2 原文条款）：
* §4.5  现实时间：/enter 返回 remaining_real_duration_s（0..max_real_duration_s），
        程序应使用该值，"不应固定假定每次都有1200秒"。
* §5.1  request_id 是本测试会话内的幂等键（UTF-8 1..128 字节）。
* §5.3  "每个新动作必须使用新的 request_id。只有在网络超时、连接中断等情况下重试
        完全相同的动作时，才复用原请求内容和原 request_id。同一ID、同一内容返回第一次的
        完整响应，不重复移动、检测、清除、退出或推进时间；同一ID改动路径、位置、频道等
        内容返回HTTP 409。结构错误（HTTP 400）以及未知字段、arena_id/robot_id 不匹配
        （HTTP 200且 accepted=false）不占用该 request_id，修正后可以复用。"
* §12   逐次等待响应、不得并发；同时检查 HTTP 状态和 accepted；使用
        remaining_real_duration_s 控制现实运行时间；自行记录指令序列与响应。

覆盖三处必修：
1. request_id 幂等——新动作新 id；网络故障重试复用同一 id 与同一内容；同 id 改内容 409。
2. remaining_real_duration_s——Mock 不再写死 1200；客户端消费该字段并据此压哨退出。
3. BaseClient 抽象接口（enter/measure/clear/exit + virtual_time_s + remaining_real_s）。

同时锁定 SimulatorHTTP / MockSimulatorServer 既有公开方法签名的向后兼容
（solve_b_http.py 依赖 enter/measure/clear/exit/sweep/try_clear_any 与
 start/stop/summary、以及 pos/virtual_time/cleared 等属性）。
"""
from __future__ import annotations

import io
import json
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

CODE_DIR = (Path(__file__).resolve().parents[2]
            / "projects" / "cumcm2026b" / "artifacts" / "code")
sys.path.insert(0, str(CODE_DIR))

from simulator_http import (  # noqa: E402
    BaseClient,
    MockSimulatorServer,
    NotAccepted,
    RequestIdConflict,
    SimulatorHTTP,
)

ROBOT = "TESTTEAM"


# --------------------------------------------------------------------------- 工具
def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = int(sock.getsockname()[1])
    sock.close()
    return port


def _body(request_id: str, **extra) -> dict:
    return {"arena_id": "default", "robot_id": ROBOT, "request_id": request_id, **extra}


def _raw_post(base_url: str, path: str, body: dict) -> tuple[int, dict]:
    """绕过客户端直发 HTTP，用于观察服务端原始行为。"""
    req = urllib.request.Request(
        base_url + path, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        return e.code, json.loads(raw) if raw else {}


class _FakeHTTPResponse:
    """urlopen 的替身：只需 status / read / 上下文管理器。"""

    def __init__(self, payload: dict, status: int = 200):
        self.status = status
        self._raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, *exc) -> None:
        return None


class _ScriptedTransport:
    """按脚本回放的传输层替身，记录每一次发出的请求体（原始 dict）。

    脚本项：
      "timeout"          —— 模拟读超时/连接中断（无 JSON 体，附件2 §5.3）
      "url_error"        —— 模拟连接被直接关闭（urllib.error.URLError）
      (status, payload)  —— 返回该 HTTP 状态与 JSON 体

    脚本耗尽后重复最后一步（便于表达"始终失败"）。
    """

    def __init__(self, script: list):
        self.script = list(script)
        self.bodies: list[dict] = []
        self._last: object = (200, {"accepted": True, "virtual_time_s": 0.0})

    def __call__(self, req, timeout=None):
        self.bodies.append(json.loads(req.data.decode("utf-8")))
        step = self.script.pop(0) if self.script else self._last
        self._last = step
        if step == "timeout":
            raise TimeoutError("read timed out")       # 3.10+ 与 socket.timeout 同义
        if step == "url_error":
            raise urllib.error.URLError("connection reset")
        status, payload = step
        if status != 200:
            raise urllib.error.HTTPError(
                req.full_url, status, "err", {},
                io.BytesIO(json.dumps(payload, ensure_ascii=False).encode("utf-8")))
        return _FakeHTTPResponse(payload, status)


@pytest.fixture
def mock_server():
    """按需创建本地 Mock，测试结束统一 stop()。"""
    created: list[MockSimulatorServer] = []

    def _make(**kw) -> MockSimulatorServer:
        srv = MockSimulatorServer(port=_free_port(), **kw)
        srv.start()
        created.append(srv)
        return srv

    yield _make
    for srv in created:
        srv.stop()


# =========================================================== 1. request_id 幂等
def test_new_action_uses_new_request_id(monkeypatch):
    """§5.3：每个新动作必须使用新的 request_id。"""
    transport = _ScriptedTransport([
        (200, {"accepted": True, "virtual_time_s": 5.0, "measure_result": "no_signal"}),
        (200, {"accepted": True, "virtual_time_s": 15.0, "clear_result": "success"}),
    ])
    monkeypatch.setattr(urllib.request, "urlopen", transport)
    sim = SimulatorHTTP(robot_id=ROBOT, retry_delay=0.0)

    sim.measure(10.0, 20.0, 3)
    sim.clear(10.0, 20.0, 3)

    ids = [b["request_id"] for b in transport.bodies]
    assert len(ids) == 2 and ids[0] != ids[1]


def test_network_retry_reuses_original_request_id_and_content(monkeypatch):
    """§5.3：网络超时/中断重试完全相同的动作时，复用原 request_id 与原请求内容。"""
    transport = _ScriptedTransport([
        "timeout",
        "url_error",
        (200, {"accepted": True, "virtual_time_s": 105.0, "measure_result": "direction",
               "svd_deg": 33.5}),
    ])
    monkeypatch.setattr(urllib.request, "urlopen", transport)
    sim = SimulatorHTTP(robot_id=ROBOT, retries=4, retry_delay=0.0)

    result = sim.measure(300.0, 400.0, 2)

    assert result["measure_result"] == "direction"
    assert len(transport.bodies) == 3
    first = transport.bodies[0]
    assert all(b == first for b in transport.bodies)          # 原请求内容逐字节不变
    assert len({b["request_id"] for b in transport.bodies}) == 1


def test_conflict_is_not_retried(monkeypatch):
    """§5.3：同一 id 改动内容 → HTTP 409。这是程序 bug，客户端不得重试。"""
    transport = _ScriptedTransport([(409, {"accepted": False, "error": "request_id conflict"})])
    monkeypatch.setattr(urllib.request, "urlopen", transport)
    sim = SimulatorHTTP(robot_id=ROBOT, retries=4, retry_delay=0.0)

    with pytest.raises(RequestIdConflict):
        sim.measure(1.0, 2.0, 1)
    assert len(transport.bodies) == 1


def test_accepted_false_raises_and_keeps_virtual_time(monkeypatch):
    """§4.1/§5.3：accepted=false 时 virtual_time_s=0 不是当前时刻，不得据此回退本地时钟。"""
    transport = _ScriptedTransport([
        (200, {"accepted": True, "virtual_time_s": 30.0, "measure_result": "no_signal"}),
        (200, {"accepted": False, "virtual_time_s": 0, "error": "arena_id 不匹配"}),
    ])
    monkeypatch.setattr(urllib.request, "urlopen", transport)
    sim = SimulatorHTTP(robot_id=ROBOT, retry_delay=0.0)

    sim.measure(0.0, 0.0, 1)
    assert sim.virtual_time == 30.0

    with pytest.raises(NotAccepted):
        sim.measure(0.0, 0.0, 1)
    assert sim.virtual_time == 30.0            # 未被 accepted=false 的 0 覆盖


def test_retries_exhausted_raises_connection_error(monkeypatch):
    """§5.3/§12：倒计时未结束或接口未开放时连接直接失败（无 JSON 体），需如实抛出。"""
    transport = _ScriptedTransport(["timeout"])
    monkeypatch.setattr(urllib.request, "urlopen", transport)
    sim = SimulatorHTTP(robot_id=ROBOT, retries=2, retry_delay=0.0)

    with pytest.raises(ConnectionError):
        sim.measure(0.0, 0.0, 1)
    assert len(transport.bodies) == 3          # 首次 + 2 次重试
    assert len({b["request_id"] for b in transport.bodies}) == 1


# ============================================ 2. remaining_real_duration_s / 压哨
def test_mock_enter_reports_configured_real_duration(mock_server):
    """§4.5：remaining_real_duration_s 不应写死 1200，而应来自本局配置。"""
    srv = mock_server(seed=42, max_real_s=300.0)
    base = f"http://127.0.0.1:{srv.port}"

    status, resp = _raw_post(base, "/enter", _body("enter-1"))

    assert status == 200 and resp["accepted"] is True
    assert resp["max_real_duration_s"] == 300.0
    assert 0.0 < resp["remaining_real_duration_s"] <= 300.0


def test_mock_enter_default_real_duration_is_1200(mock_server):
    """§6.2：默认 max_real_duration_s 为 1200。"""
    srv = mock_server(seed=42)
    base = f"http://127.0.0.1:{srv.port}"

    _, resp = _raw_post(base, "/enter", _body("enter-1"))

    assert resp["max_real_duration_s"] == 1200.0
    assert resp["remaining_real_duration_s"] == 1200.0


def test_client_consumes_remaining_and_exits_before_deadline(monkeypatch):
    """§4.5/§12：客户端消费 remaining_real_duration_s，压哨前主动 /exit（不重复发送）。"""
    now = [1000.0]
    transport = _ScriptedTransport([
        (200, {"accepted": True, "virtual_time_s": 0.0,
               "max_virtual_duration_s": 360000.0, "max_real_duration_s": 1200.0,
               "remaining_real_duration_s": 1200.0}),
        (200, {"accepted": True, "virtual_time_s": 0.0, "exit_reason": "user_exit"}),
    ])
    monkeypatch.setattr(urllib.request, "urlopen", transport)
    sim = SimulatorHTTP(robot_id=ROBOT, retry_delay=0.0, clock=lambda: now[0])

    sim.enter()
    assert sim.remaining_real_s == pytest.approx(1200.0)
    assert sim.should_exit(safety_s=45.0) is False

    now[0] += 1160.0
    assert sim.remaining_real_s == pytest.approx(40.0)
    assert sim.should_exit(safety_s=45.0) is True

    assert sim.exit_if_deadline(safety_s=45.0) is True
    assert sim.exit_if_deadline(safety_s=45.0) is True      # 已退出 → 不重复发送
    assert [b["request_id"] for b in transport.bodies][-1] != transport.bodies[0]["request_id"]
    assert len(transport.bodies) == 2
    assert transport.bodies[1]["request_id"].startswith(ROBOT)   # /exit 也是新 id 的新动作


def test_client_does_not_exit_while_time_remains(monkeypatch):
    """未到压哨阈值时不得退出。"""
    now = [0.0]
    transport = _ScriptedTransport([
        (200, {"accepted": True, "virtual_time_s": 0.0,
               "max_real_duration_s": 1200.0, "remaining_real_duration_s": 1200.0}),
    ])
    monkeypatch.setattr(urllib.request, "urlopen", transport)
    sim = SimulatorHTTP(robot_id=ROBOT, retry_delay=0.0, clock=lambda: now[0])

    sim.enter()
    now[0] += 10.0

    assert sim.exit_if_deadline(safety_s=45.0) is False
    assert sim.exited is False
    assert len(transport.bodies) == 1


def test_remaining_is_none_before_enter(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", _ScriptedTransport([]))
    sim = SimulatorHTTP(robot_id=ROBOT, retry_delay=0.0)

    assert sim.remaining_real_s is None
    assert sim.should_exit() is False


# ================================================== 3. BaseClient 可换靶抽象接口
def test_base_client_declares_swappable_interface():
    assert issubclass(SimulatorHTTP, BaseClient)
    for name in ("enter", "measure", "clear", "exit", "virtual_time_s", "remaining_real_s"):
        assert hasattr(BaseClient, name), name
    # 4 条指令与传输原语必须由具体靶子实现；两个观测属性由基类统一提供
    assert BaseClient.__abstractmethods__ >= {"_send", "enter", "measure", "clear", "exit"}
    assert "virtual_time_s" not in BaseClient.__abstractmethods__


def test_base_client_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseClient(robot_id=ROBOT)  # type: ignore[abstract]


def test_virtual_time_legacy_alias_agrees_with_interface(mock_server):
    """向后兼容：solve_b_http.py 读 sim.virtual_time，接口新名 virtual_time_s 必须一致。"""
    srv = mock_server(seed=42, n_src=12)
    sim = SimulatorHTTP(base_url=f"http://127.0.0.1:{srv.port}", robot_id=ROBOT, timeout=10.0)

    sim.enter()
    assert sim.virtual_time == sim.virtual_time_s == 0.0
    measured = sim.measure(300.0, 400.0, 3)
    assert sim.virtual_time == sim.virtual_time_s == measured["virtual_time_s"] > 0.0


def test_same_strategy_runs_against_interface(mock_server):
    """同一份只依赖 BaseClient 的策略，可在本地 Mock 靶子上跑通（换靶契约）。"""
    srv = mock_server(seed=42, n_src=12)

    def strategy(client: BaseClient) -> float:
        client.enter()
        assert client.remaining_real_s is not None and client.remaining_real_s > 0.0
        result = client.measure(0.0, 0.0, 1)
        assert result["measure_result"] in {"no_signal", "near", "direction"}
        client.exit()
        return client.virtual_time_s

    sim = SimulatorHTTP(base_url=f"http://127.0.0.1:{srv.port}", robot_id=ROBOT, timeout=10.0)
    assert strategy(sim) >= 0.0
    assert sim.exited is True


def test_public_signatures_stay_backward_compatible(mock_server):
    """solve_b_http.py 依赖的公开方法/属性必须仍在且可调用。"""
    srv = mock_server(seed=42, n_src=12)
    sim = SimulatorHTTP(base_url=f"http://127.0.0.1:{srv.port}", robot_id=ROBOT, timeout=10.0)

    sim.enter()
    assert sim.sweep(300.0, 400.0, channels=[1, 2]) is not None
    assert sim.try_clear_any(0.0, 0.0, channels=[1]) in (None, 1)
    for attr in ("pos", "current_channel", "virtual_time", "cleared", "last_enter", "entered"):
        assert hasattr(sim, attr), attr
    assert isinstance(srv.summary(), dict)
    assert set(srv.summary()) >= {"total_sources", "cleared", "virtual_time_s"}


# ============================================ 4. Mock 侧 §5.3 幂等语义（服务端）
def test_mock_replays_first_response_without_advancing_time(mock_server):
    """§5.3：同一 ID、同一内容返回第一次的完整响应，不重复移动/检测/推进时间。"""
    srv = mock_server(seed=42, n_src=12)
    base = f"http://127.0.0.1:{srv.port}"
    body = _body("measure-1", position={"x": 300.0, "y": 400.0}, channel=1)

    status1, resp1 = _raw_post(base, "/measure", body)
    vtime_after_first = srv.vtime
    status2, resp2 = _raw_post(base, "/measure", dict(body))

    assert (status1, status2) == (200, 200)
    assert resp2 == resp1                       # 逐字段（含 real_timestamp_ms）重放首次响应
    assert srv.vtime == vtime_after_first       # 未推进虚拟时钟


def test_mock_returns_409_when_same_id_changes_content(mock_server):
    """§5.3：同一 ID 改动路径、位置、频道等内容返回 HTTP 409。"""
    srv = mock_server(seed=42, n_src=12)
    base = f"http://127.0.0.1:{srv.port}"

    s1, _ = _raw_post(base, "/measure", _body("m-9", position={"x": 10.0, "y": 10.0}, channel=2))
    s2, r2 = _raw_post(base, "/measure", _body("m-9", position={"x": 20.0, "y": 20.0}, channel=2))
    s3, _ = _raw_post(base, "/clear", _body("m-9", position={"x": 10.0, "y": 10.0}, channel=2))

    assert s1 == 200
    assert (s2, s3) == (409, 409)
    assert r2["accepted"] is False


def test_mock_rejects_reused_id_when_channel_changes(mock_server):
    """§5.3 的"频道等内容"：同 id 同位置但换频道 → 409。"""
    srv = mock_server(seed=42, n_src=12)
    base = f"http://127.0.0.1:{srv.port}"

    s1, _ = _raw_post(base, "/measure", _body("m-5", position={"x": 5.0, "y": 5.0}, channel=1))
    s2, _ = _raw_post(base, "/measure", _body("m-5", position={"x": 5.0, "y": 5.0}, channel=4))

    assert s1 == 200 and s2 == 409


def test_mock_error_does_not_occupy_request_id(mock_server):
    """§5.3：结构错误（400）与 arena_id/robot_id 不匹配（200+accepted=false）不占用 id。"""
    srv = mock_server(seed=42, n_src=12)
    base = f"http://127.0.0.1:{srv.port}"

    s1, _ = _raw_post(base, "/measure", _body("m-7", position={"x": 1.0, "y": 1.0}, channel=99))
    s2, r2 = _raw_post(base, "/measure", _body("m-7", position={"x": 1.0, "y": 1.0}, channel=3))
    assert s1 == 400
    assert s2 == 200 and r2["accepted"] is True

    bad = {"arena_id": "other", "robot_id": ROBOT, "request_id": "m-8",
           "position": {"x": 1.0, "y": 1.0}, "channel": 3}
    s3, r3 = _raw_post(base, "/measure", bad)
    s4, r4 = _raw_post(base, "/measure", {**bad, "arena_id": "default"})
    assert s3 == 200 and r3["accepted"] is False
    assert s4 == 200 and r4["accepted"] is True


def test_mock_error_bodies_carry_business_fields(mock_server):
    """§5.2/§5.3：能形成 HTTP 响应的错误也返回含 accepted/real_timestamp_ms/virtual_time_s 的 JSON。"""
    srv = mock_server(seed=42, n_src=12)
    base = f"http://127.0.0.1:{srv.port}"

    _, resp = _raw_post(base, "/unknown", _body("x-1"))
    assert resp["accepted"] is False
    assert "real_timestamp_ms" in resp and "virtual_time_s" in resp
