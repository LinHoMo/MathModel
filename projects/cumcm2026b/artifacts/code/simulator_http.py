#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""simulator_http.py —— CUMCM 2026 B 题「干扰源定位与清除」模拟器客户端 + 本地 Mock。

对齐《模拟器通信接口说明及编程指南》（B 题附件2）：
  * 4 条指令：POST /enter、/measure、/clear、/exit。
  * 请求体：UTF-8 JSON 对象，顶层必含 arena_id="default"、robot_id、request_id。
    /measure 与 /clear 另含 position:{x,y} 与 channel。
  * 响应：accepted(boolean) + real_timestamp_ms + virtual_time_s；
    /measure 附 measure_result ∈ {"no_signal","near","direction"} 与 svd_deg（仅 direction）；
    /clear 附 clear_result ∈ {"success","no_target_in_range"}；
    /exit 附 exit_reason；/enter 附限时字段与 remaining_real_duration_s。
  * 虚拟时间由服务端计算：移动 |Δp|/5 s；/measure 检测 5 s，且频道变化时 +1 s 切换；
    /clear 未发现 3 s、成功 5 s（不切频道）。
  * 真实模拟器**不返回信号强度**，仅返回示向度 svd_deg。

协议忠实化要点（逐条对回附件2 原文）：
  * §5.1 request_id 是本测试会话内的幂等键。
  * §5.3 幂等："每个新动作必须使用新的 request_id。只有在网络超时、连接中断等情况下重试
    完全相同的动作时，才复用原请求内容和原 request_id。"客户端 `_call` 据此重试；
    "同一ID改动路径、位置、频道等内容返回HTTP 409"——客户端不重试，Mock 端判 409。
    "结构错误（HTTP 400）以及未知字段、arena_id / robot_id 不匹配（HTTP 200且
    accepted=false）不占用该 request_id"——Mock 端只在 accepted=true 时登记该 id。
  * §5.2/§5.3 同时检查 HTTP 状态与 accepted；accepted=false 时 virtual_time_s=0
    不是当前虚拟时刻，本地已同步的虚拟时刻不被其回退。
  * §4.5 现实时间：消费 /enter 的 remaining_real_duration_s（0..max_real_duration_s），
    "不应固定假定每次都有1200秒"；据此做压哨退出。Mock 不再写死 1200。
  * §12 程序自行记录指令序列与响应（BaseClient.trace），不依赖模拟器。

换靶抽象：`BaseClient` 抽取策略依赖的接口（enter/measure/clear/exit + virtual_time_s +
remaining_real_s），本地 Mock 与官方模拟器共用同一份策略；SimulatorHTTP 是 HTTP 实现。

零第三方依赖（标准库 urllib + http.server + threading + json）。
"""
from __future__ import annotations

import json
import math
import random
import threading
import time
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable

# ---------------------------------------------------------------------------
# 规范常量（对齐题面附录 / 附件2）
# ---------------------------------------------------------------------------
R_AREA = 1800.0
EPS_BEARING = 1.0          # 示向度误差界 ±1°
R_REC_MIN, R_REC_MAX = 1000.0, 1500.0
N_CHANNEL = 20
N_SRC_MIN, N_SRC_MAX = 10, 16
V_DOG = 5.0                # 机器狗速度 m/s
T_DETECT = 5.0             # 检测动作耗时 s
T_SWITCH = 1.0             # 切换频道耗时 s（仅 /measure 且 channel 变化时）
T_OPTIC_NONE = 3.0         # /clear 未发现耗时 s
T_CLEAR_OK = 5.0           # /clear 成功耗时 s
D_NEAR = 5.0               # 近距离阈值（信号过强无法测向）m
D_CLEAR = 20.0             # 清除半径 m
DEFAULT_PORT = 2026
SEED = 42

# 附件2 §6.2：限时字段默认值（Mock 未显式配置时使用）
MAX_REAL_DURATION_S = 1200.0
MAX_VIRTUAL_DURATION_S = 360000.0

# 客户端重试策略（附件2 未规定次数/间隔，属实现选择）：仅用于网络类故障与 429/500
RETRY_ATTEMPTS = 5
RETRY_BASE_DELAY = 0.2
# 压哨退出安全余量（附件2 未规定，属客户端实现约定：留出 /exit 往返与收尾时间）
EXIT_MARGIN_S = 45.0


# ---------------------------------------------------------------------------
# 协议异常（均为 RuntimeError 子类，保持既有调用方的 except RuntimeError 兼容）
# ---------------------------------------------------------------------------
class ProtocolError(RuntimeError):
    """不可恢复的协议或通信错误。"""


class NotAccepted(ProtocolError):
    """HTTP 200 但 accepted=false：动作未生效，虚拟时刻未推进（附件2 §5.3）。"""

    def __init__(self, path: str, body: dict):
        super().__init__(f"{path} 未执行（accepted=false）：{body.get('error') or body}")
        self.path = path
        self.body = body


class RequestIdConflict(ProtocolError):
    """HTTP 409：同一 request_id 对应了不同动作或内容（附件2 §5.3）。"""

    def __init__(self, path: str, body: dict):
        super().__init__(f"{path} 幂等键冲突（HTTP 409）：{body.get('error') or body}")
        self.path = path
        self.body = body


# ===================================================================
# BaseClient —— 可换靶的客户端接口
# ===================================================================
class BaseClient(ABC):
    """策略只依赖这一个接口，因此本地 Mock 靶与官方模拟器靶可以互换。

    子类只需实现 `_send(path, payload) -> (http_status, response_body)` 与 4 条指令；
    基类提供全部协议语义：
      * 逐次等待响应，不并发发送不同动作（§12）；
      * 幂等重试：网络故障复用原 request_id 与原请求内容（§5.3）；
      * 虚拟时刻只用最近一次 accepted=true 的值（§4.1/§5.3）；
      * 消费 remaining_real_duration_s 做压哨退出（§4.5）；
      * 自行记录指令序列与响应（§12）。
    """

    # 附件2 §5.1：arena_id 必须逐字节等于 ASCII 字符串 "default"
    arena_id: str = "default"

    def __init__(self, robot_id: str = "TEAM000", trace: bool = True,
                 clock: "Callable[[], float] | None" = None):
        self.robot_id = robot_id
        self._clock = clock or time.monotonic
        self._seq = 0
        self.entered = False
        self.exited = False
        self.n_requests = 0
        self.trace: list[dict] | None = [] if trace else None
        # 附件2 §4.1/§5.3：只有 accepted=true 的响应才能推进本地虚拟时刻
        self._virtual_time = 0.0
        # 附件2 §4.5：/enter 返回的可用现实时间与其起算时刻
        self._remaining_at_enter: float | None = None
        self._enter_clock: float | None = None
        self.max_real_s: float | None = None
        self.max_virtual_s: float | None = None

    # ----- 子类实现：靶子 -----
    @abstractmethod
    def _send(self, path: str, payload: dict) -> tuple[int, dict]:
        """把一次请求送到靶子，返回 (HTTP 状态, JSON 体)。不得自行重试。"""
        raise NotImplementedError

    # ----- 接口属性（换靶契约）-----
    @property
    def virtual_time_s(self) -> float:
        """最近一次 accepted=true 的虚拟时刻（附件2 §4.1）。"""
        return self._virtual_time

    @property
    def remaining_real_s(self) -> float | None:
        """当前剩余现实时间（秒）；按 §4.5 从 /enter 起算随真实时间递减。"""
        if self._remaining_at_enter is None or self._enter_clock is None:
            return None
        return max(0.0, self._remaining_at_enter - (self._clock() - self._enter_clock))

    # ----- 子类实现：4 条指令 -----
    @abstractmethod
    def enter(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def measure(self, x: float, y: float, channel: int) -> dict:
        raise NotImplementedError

    @abstractmethod
    def clear(self, x: float, y: float, channel: int) -> str:
        raise NotImplementedError

    @abstractmethod
    def exit(self) -> dict:
        raise NotImplementedError

    # ----- 通用协议逻辑 -----
    def _req_id(self) -> str:
        self._seq += 1
        return f"{self.robot_id}-{self._seq:08d}"

    def _call(self, path: str, extra: dict | None = None,
              request_id: str | None = None,
              retries: int = RETRY_ATTEMPTS,
              base_delay: float = RETRY_BASE_DELAY) -> dict:
        """发送一个动作，返回 accepted=true 的完整响应体。

        附件2 §5.3：request_id 只在**本次动作**内生成一次，重试沿用同一个 id 与同一份
        请求内容，服务端据此幂等重放而不重复动作、不重复推进时间。
        """
        body = {"arena_id": self.arena_id, "robot_id": self.robot_id,
                "request_id": request_id or self._req_id(), **(extra or {})}
        delay = base_delay
        last: object = None
        for attempt in range(retries + 1):
            try:
                status, payload = self._send(path, body)
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                # 附件2 §5.3/§12：倒计时未结束、接口未开放、测试已结束或网络抖动时
                # 连接可能直接被关闭（没有 JSON 体）——复用原 id/原内容重试
                last = e
                if attempt >= retries:
                    raise ConnectionError(
                        f"无法连接模拟器 {getattr(self, 'base_url', '')}{path}"
                        f"（已重试 {retries} 次，每次复用同一 request_id）: {e}") from e
                time.sleep(delay)
                delay = min(delay * 2, 2.0)
                continue

            self.n_requests += 1
            self._record(path, body, status, payload, attempt)

            if status == 200:
                if payload.get("accepted") is True:
                    self._absorb(path, payload)
                    return payload
                # accepted=false：动作未生效，id 未被占用，重试无意义（需修正内容）
                raise NotAccepted(path, payload)
            if status == 409:
                # 同 id 改内容：程序 bug，重试只会重复 409
                raise RequestIdConflict(path, payload)
            if status in (429, 500):
                # 429（含本局幂等记录达上限）/500：复用原 id 与内容重试是安全的
                last = payload
                if attempt >= retries:
                    raise ProtocolError(f"{path} 反复返回 HTTP {status}: {payload}")
                time.sleep(delay)
                delay = min(delay * 2, 2.0)
                continue
            raise ProtocolError(f"HTTP {status} on {path}: {payload}")
        raise ProtocolError(f"{path} 失败: {last}")

    def _absorb(self, path: str, body: dict) -> None:
        """吸收 accepted=true 响应。"""
        if isinstance(body.get("virtual_time_s"), (int, float)):
            self._virtual_time = float(body["virtual_time_s"])
        if path == "/enter":
            self.entered = True
            self._remaining_at_enter = float(body.get("remaining_real_duration_s", 0.0))
            self._enter_clock = self._clock()
            self.max_real_s = float(body.get("max_real_duration_s", 0.0)) or None
            self.max_virtual_s = float(body.get("max_virtual_duration_s", 0.0)) or None
        elif path == "/exit":
            self.exited = True

    def _record(self, path: str, body: dict, status: int, payload: dict,
                attempt: int) -> None:
        """附件2 §12：机器狗程序自行记录指令序列与响应（模拟器不提供）。"""
        if self.trace is None:
            return
        self.trace.append({
            "seq": len(self.trace) + 1,
            "path": path,
            "request_id": body.get("request_id"),
            "x": (body.get("position") or {}).get("x"),
            "y": (body.get("position") or {}).get("y"),
            "channel": body.get("channel"),
            "http_status": status,
            "accepted": payload.get("accepted"),
            "virtual_time_s": payload.get("virtual_time_s"),
            "measure_result": payload.get("measure_result"),
            "svd_deg": payload.get("svd_deg"),
            "clear_result": payload.get("clear_result"),
            "exit_reason": payload.get("exit_reason"),
            "attempt": attempt,
        })

    # ----- 现实时间（附件2 §4.5）：压哨退出 -----
    def should_exit(self, safety_s: float = EXIT_MARGIN_S) -> bool:
        """剩余现实时间不足 safety_s 时应主动退出。未 /enter 时返回 False。"""
        left = self.remaining_real_s
        return left is not None and left <= safety_s

    def exit_if_deadline(self, safety_s: float = EXIT_MARGIN_S) -> bool:
        """压哨退出：到点则主动 /exit（避免被判「超时退出」）；已退出则不重复发送。"""
        if self.exited:
            return True
        if not self.should_exit(safety_s):
            return False
        self.exit()
        return True


# ===================================================================
# SimulatorHTTP —— 真实协议客户端
# ===================================================================
class SimulatorHTTP(BaseClient):
    """按《接口说明》与模拟器通信的客户端。

    时间由服务端计算，客户端从 accepted=true 的响应同步 virtual_time_s。
    使用前需模拟器已进入测试窗口；构造后调用 enter() 开始。

    参数
    ----
    base_url : 模拟器地址，默认 http://127.0.0.1:2026
    robot_id : 参赛队号（必须与模拟器登录账号逐字节一致）
    arena_id : 固定 "default"
    timeout  : 单次 HTTP 请求超时（秒）
    retries  : 网络类故障的最大重试次数（复用同一 request_id 与原内容）
    retry_delay : 网络类故障重试的初始退避（秒），指数增长、上限 2 s
    trace    : 是否记录指令序列与响应（附件2 §12）
    clock    : 单调时钟注入点，默认 time.monotonic（便于测试与复现）
    """

    def __init__(self, base_url: str = f"http://127.0.0.1:{DEFAULT_PORT}",
                 robot_id: str = "TEAM000", arena_id: str = "default",
                 timeout: float = 30.0, retries: int = RETRY_ATTEMPTS,
                 retry_delay: float = RETRY_BASE_DELAY, trace: bool = True,
                 clock: "Callable[[], float] | None" = None):
        super().__init__(robot_id=robot_id, trace=trace, clock=clock)
        self.base_url = base_url.rstrip("/")
        self.arena_id = arena_id
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay

        # 本地镜像的服务端状态
        self.pos = (0.0, 0.0)
        self.current_channel = 1
        self.cleared: set[int] = set()      # 本地记录已清除频道
        self.last_enter: dict = {}

    # ----- 换靶契约：HTTP 传输 -----
    def _send(self, path: str, payload: dict) -> tuple[int, dict]:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + path, data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            try:
                return e.code, json.loads(raw)
            except ValueError:
                return e.code, {"accepted": False, "error": raw[:200]}

    # ----- 兼容既有调用方的属性别名 -----
    @property
    def virtual_time(self) -> float:
        """solve_b_http.py 使用的旧名，与接口属性 virtual_time_s 同源。"""
        return self._virtual_time

    # ----- 兼容既有调用方的低层入口 -----
    def _post(self, path: str, extra: dict) -> dict:
        """旧签名保留：新动作取新 request_id，网络故障按 §5.3 复用原 id 重试。"""
        return self._call(path, extra)

    # ----- 4 条指令 -----
    def enter(self) -> dict:
        r = self._call("/enter", {}, retries=self.retries, base_delay=self.retry_delay)
        self.pos = (0.0, 0.0)
        self.current_channel = 1
        self.last_enter = r
        return r

    def measure(self, x: float, y: float, channel: int) -> dict:
        """检测。返回 {'measure_result': 'no_signal'|'near'|'direction', 'svd_deg': float|None}。"""
        if not (1 <= int(channel) <= N_CHANNEL):
            raise ValueError(f"channel 越界: {channel}")
        r = self._call("/measure", {"position": {"x": float(x), "y": float(y)},
                                    "channel": int(channel)},
                       retries=self.retries, base_delay=self.retry_delay)
        self.pos = (float(x), float(y))
        self.current_channel = int(channel)
        return {"measure_result": r.get("measure_result", "no_signal"),
                "svd_deg": (float(r["svd_deg"]) if "svd_deg" in r else None),
                "virtual_time_s": self.virtual_time}

    def clear(self, x: float, y: float, channel: int) -> str:
        """清除。返回 'success' | 'no_target_in_range'。"""
        r = self._call("/clear", {"position": {"x": float(x), "y": float(y)},
                                  "channel": int(channel)},
                       retries=self.retries, base_delay=self.retry_delay)
        self.pos = (float(x), float(y))
        res = r.get("clear_result", "no_target_in_range")
        if res == "success":
            self.cleared.add(int(channel))
        return res

    def exit(self) -> dict:
        return self._call("/exit", {}, retries=self.retries, base_delay=self.retry_delay)

    # ----- 便捷封装 -----
    def sweep(self, x: float, y: float, channels=None) -> dict:
        """在 (x,y) 依次检测指定频道，返回 {ch: svd_deg}（仅 direction）。"""
        if channels is None:
            channels = [c for c in range(1, N_CHANNEL + 1) if c not in self.cleared]
        found = {}
        for ch in channels:
            r = self.measure(x, y, ch)
            if r["measure_result"] == "direction":
                found[ch] = r["svd_deg"]
        return found

    def try_clear_any(self, x: float, y: float, channels=None) -> int | None:
        """在 (x,y) 依次尝试清除未清除频道，返回成功的频道号或 None。"""
        if channels is None:
            channels = [c for c in range(1, N_CHANNEL + 1) if c not in self.cleared]
        for ch in channels:
            if self.clear(x, y, ch) == "success":
                return ch
        return None


# ===================================================================
# MockSimulatorServer —— 规范忠实的本地 Mock
# ===================================================================
class _Src:
    __slots__ = ("sid", "x", "y", "channel", "r_rec", "kind", "heading")
    def __init__(self, sid, x, y, channel, r_rec, kind="omni", heading=None):
        self.sid, self.x, self.y = sid, x, y
        self.channel, self.r_rec = channel, r_rec
        self.kind, self.heading = kind, heading

    def in_beam(self, px, py):
        if self.kind == "omni":
            return True
        ang = math.degrees(math.atan2(py - self.y, px - self.x)) % 360.0
        diff = abs(((ang - (self.heading or 0.0) + 180.0) % 360.0) - 180.0)
        return diff <= 90.0 + 1e-9


class MockSimulatorServer:
    """本地 Mock：逐条复现《接口说明》的请求/响应契约、幂等语义与虚拟时间模型。

    与真实模拟器差异：源数量/位置/半径/朝向由本地随机生成（seed 可复现），
    不涉及登录与联网。用于开发与端到端验证客户端与策略。

    参数
    ----
    max_real_s : 本局现实世界限时（附件2 §6.2 的 max_real_duration_s，默认 1200）；
                 /enter 的 remaining_real_duration_s 由它派生，不再写死。
    clock      : 单调时钟注入点，默认 time.monotonic（便于测试现实倒计时）。
    """

    def __init__(self, port: int = DEFAULT_PORT, seed: int = SEED,
                 kind_mix: bool = False, dir_frac: float = 0.4, n_src: int | None = None,
                 max_real_s: float = MAX_REAL_DURATION_S,
                 clock: "Callable[[], float] | None" = None):
        self.port, self.seed = port, seed
        self.kind_mix, self.dir_frac, self.n_src = kind_mix, dir_frac, n_src
        self.max_real_s = float(max_real_s)
        self._clock = clock or time.monotonic
        self._httpd: HTTPServer | None = None
        self._thread: threading.Thread | None = None
        # 服务端状态
        self.rng: random.Random | None = None
        self.sources: list[_Src] = []
        self.cleared: set[int] = set()
        self.pos = (0.0, 0.0)
        self.channel = 1
        self.vtime = 0.0
        self.started = False
        # 附件2 §5.3 幂等记录：request_id -> (请求指纹, 首次响应)
        self._idem: dict[str, tuple[str, tuple[int, dict]]] = {}
        self._enter_wall: float | None = None

    # ----- 生命周期 -----
    def _reset(self):
        rng = random.Random(self.seed)
        n = self.n_src if self.n_src is not None else rng.randint(N_SRC_MIN, N_SRC_MAX)
        chans = list(range(1, N_CHANNEL + 1))
        rng.shuffle(chans)
        self.sources = []
        for i in range(n):
            r = R_AREA * math.sqrt(rng.random())
            a = rng.uniform(0.0, 2.0 * math.pi)
            kind, heading = "omni", None
            if self.kind_mix and rng.random() < self.dir_frac:
                kind, heading = "dir", rng.uniform(0.0, 360.0)
            self.sources.append(_Src(i, r * math.cos(a), r * math.sin(a),
                                     chans[i], rng.uniform(R_REC_MIN, R_REC_MAX),
                                     kind, heading))
        rng.shuffle(self.sources)
        self.rng = rng
        self.cleared, self.pos, self.channel, self.vtime = set(), (0.0, 0.0), 1, 0.0
        self.started, self._idem, self._enter_wall = True, {}, None

    def start(self, block: bool = False):
        parent = self

        class _H(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length > 0 else b""
                try:
                    body = json.loads(raw.decode("utf-8"))
                    status, resp = parent._handle(self.path, body)
                except Exception as e:  # noqa: BLE001
                    status, resp = parent._error(400, str(e))
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))

            def log_message(self, *a):
                pass

        self._httpd = HTTPServer(("127.0.0.1", self.port), _H)
        if block:
            print(f"Mock 模拟器启动 http://127.0.0.1:{self.port} (seed={self.seed})")
            self._httpd.serve_forever()
        else:
            self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
            self._thread.start()
            time.sleep(0.1)

    def stop(self):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd = None
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    # ----- 契约 -----
    def _envelope(self) -> dict:
        return {"accepted": True,
                "real_timestamp_ms": int(time.time() * 1000),
                "virtual_time_s": round(self.vtime, 6)}

    def _error(self, status: int, message: str, **extra) -> tuple[int, dict]:
        """附件2 §5.2/§5.3：能形成 HTTP 响应的错误也返回含业务字段的 JSON。"""
        return status, {"accepted": False,
                        "real_timestamp_ms": int(time.time() * 1000),
                        "virtual_time_s": 0.0,
                        "error": message, **extra}

    @staticmethod
    def _fingerprint(path: str, body: dict) -> str:
        """请求指纹（含路径）：同 id 时用于判定"是否完全相同的动作"（附件2 §5.3）。"""
        return path + "|" + json.dumps(body, sort_keys=True, ensure_ascii=False,
                                       separators=(",", ":"))

    def remaining_real_s(self) -> float:
        """本局剩余现实时间（附件2 §4.5：从 /enter 成功起算，范围 0..max_real_duration_s）。"""
        if self._enter_wall is None:
            return self.max_real_s
        used = max(0.0, self._clock() - self._enter_wall)
        return round(max(0.0, self.max_real_s - used), 6)

    def _handle(self, path, body):
        """附件2 §5.3 幂等层：新动作登记 id；同 id 同内容重放首次响应；同 id 改内容 409。"""
        if path not in ("/enter", "/measure", "/clear", "/exit"):
            return self._error(404, "path not found")
        if not isinstance(body, dict):
            return self._error(400, "body must be object")

        rid = body.get("request_id")
        fingerprint = self._fingerprint(path, body)
        cached = self._idem.get(rid) if rid else None
        if cached is not None:
            prev_fingerprint, prev_response = cached
            if prev_fingerprint != fingerprint:
                # 同一 id 改动路径、位置、频道等内容 → 409（不重复动作、不推进时间）
                return self._error(409, "request_id conflict")
            return prev_response

        status, resp = self._dispatch(path, body)
        # 结构错误(400)、未知字段与 arena_id/robot_id 不匹配(200+accepted=false)不占用该 id
        if rid and status == 200 and resp.get("accepted") is True:
            self._idem[rid] = (fingerprint, (status, resp))
        return status, resp

    def _dispatch(self, path, body):
        rid = body.get("request_id")
        if body.get("arena_id") != "default":
            return 200, {"accepted": False, "virtual_time_s": 0,
                         "real_timestamp_ms": int(time.time() * 1000)}
        if not body.get("robot_id") or not rid:
            return self._error(400, "missing robot_id/request_id")

        if path == "/enter":
            if not self.started:
                self._reset()
            self.pos, self.channel = (0.0, 0.0), 1
            self._enter_wall = self._clock()
            return 200, {**self._envelope(),
                         "max_virtual_duration_s": MAX_VIRTUAL_DURATION_S,
                         "max_real_duration_s": self.max_real_s,
                         "remaining_real_duration_s": self.max_real_s}

        if path == "/exit":
            return 200, {**self._envelope(), "exit_reason": "user_exit"}

        pos = body.get("position")
        ch = body.get("channel")
        if not isinstance(pos, dict) or "x" not in pos or "y" not in pos:
            return self._error(400, "position required")
        x, y = float(pos["x"]), float(pos["y"])
        if not (math.isfinite(x) and math.isfinite(y)):
            return self._error(400, "non-finite position")
        if abs(x) > 2_000_000 or abs(y) > 2_000_000:
            return self._error(400, "position out of range")
        if not isinstance(ch, (int, float)) or int(ch) != ch or not (1 <= int(ch) <= N_CHANNEL):
            return self._error(400, "channel invalid")
        ch = int(ch)

        # 移动耗时
        self.vtime += math.dist(self.pos, (x, y)) / V_DOG
        self.pos = (x, y)

        if path == "/measure":
            if ch != self.channel:
                self.vtime += T_SWITCH
                self.channel = ch
            self.vtime += T_DETECT
            return 200, {**self._envelope(), **self._measure(x, y, ch)}
        else:  # /clear
            if self._clear(x, y, ch):
                self.vtime += T_CLEAR_OK
                return 200, {**self._envelope(), "clear_result": "success"}
            self.vtime += T_OPTIC_NONE
            return 200, {**self._envelope(), "clear_result": "no_target_in_range"}

    def _measure(self, x, y, ch):
        best = None
        for s in self.sources:
            if s.channel != ch or s.sid in self.cleared:
                continue
            d = math.dist((x, y), (s.x, s.y))
            if d <= s.r_rec and s.in_beam(x, y):
                if best is None or d < best[0]:
                    best = (d, s)
        if best is None:
            return {"measure_result": "no_signal"}
        d, s = best
        if d <= D_NEAR:
            return {"measure_result": "near"}
        ang = math.degrees(math.atan2(s.y - y, s.x - x)) % 360.0
        err = self.rng.uniform(-EPS_BEARING, EPS_BEARING)
        return {"measure_result": "direction", "svd_deg": round((ang + err) % 360.0, 2)}

    def _clear(self, x, y, ch) -> bool:
        cands = [s for s in self.sources
                 if s.channel == ch and s.sid not in self.cleared
                 and math.dist((x, y), (s.x, s.y)) <= D_CLEAR]
        if not cands:
            return False
        s = min(cands, key=lambda t: math.dist((x, y), (t.x, t.y)))
        self.cleared.add(s.sid)
        return True

    def summary(self) -> dict:
        n = len(self.sources)
        n_omni = sum(1 for s in self.sources if s.kind == "omni")
        return {"total_sources": n, "omni_sources": n_omni,
                "dir_sources": n - n_omni, "cleared": len(self.cleared),
                "virtual_time_s": round(self.vtime, 6)}


# ===================================================================
# CLI
# ===================================================================
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="B 题模拟器客户端 / 本地 Mock")
    ap.add_argument("--server", action="store_true", help="启动本地 Mock 服务器")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--kind-mix", action="store_true")
    ap.add_argument("--max-real-s", type=float, default=MAX_REAL_DURATION_S,
                    help="本局现实世界限时（默认 1200，附件2 §6.2）")
    args = ap.parse_args()
    if args.server:
        MockSimulatorServer(port=args.port, seed=args.seed, kind_mix=args.kind_mix,
                            max_real_s=args.max_real_s).start(block=True)
    else:
        print("用法：py -3.12 -m simulator_http --server [--port 2026] [--kind-mix]")
