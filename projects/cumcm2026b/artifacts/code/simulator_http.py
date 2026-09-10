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
from http.server import HTTPServer, BaseHTTPRequestHandler

# ---------------------------------------------------------------------------
# 规范常量（对齐题面附录）
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


# ===================================================================
# SimulatorHTTP —— 真实协议客户端
# ===================================================================
class SimulatorHTTP:
    """按《接口说明》与模拟器通信的客户端。

    时间由服务端计算，客户端从响应同步 virtual_time_s。
    使用前需模拟器已进入测试窗口；构造后调用 enter() 开始。

    参数
    ----
    base_url : 模拟器地址，默认 http://127.0.0.1:2026
    robot_id : 参赛队号（必须与模拟器登录账号逐字节一致）
    arena_id : 固定 "default"
    """

    def __init__(self, base_url: str = f"http://127.0.0.1:{DEFAULT_PORT}",
                 robot_id: str = "TEAM000", arena_id: str = "default",
                 timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.robot_id = robot_id
        self.arena_id = arena_id
        self.timeout = timeout
        self._seq = 0

        # 本地镜像的服务端状态
        self.pos = (0.0, 0.0)
        self.current_channel = 1
        self.virtual_time = 0.0
        self.cleared: set[int] = set()      # 本地记录已清除频道
        self.last_enter: dict = {}
        self.entered = False

    # ----- HTTP 原语 -----
    def _req_id(self) -> str:
        self._seq += 1
        return f"{self.robot_id}-{self._seq:08d}"

    def _post(self, path: str, extra: dict) -> dict:
        body = {"arena_id": self.arena_id, "robot_id": self.robot_id,
                "request_id": self._req_id(), **extra}
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + path, data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")[:200]
            raise RuntimeError(f"HTTP {e.code} on {path}: {detail}") from e
        except urllib.error.URLError as e:
            raise ConnectionError(f"无法连接模拟器 {self.base_url}{path}: {e}") from e
        if not payload.get("accepted", False):
            raise RuntimeError(f"{path} 未被接受: {payload}")
        if "virtual_time_s" in payload:
            self.virtual_time = float(payload["virtual_time_s"])
        return payload

    # ----- 4 条指令 -----
    def enter(self) -> dict:
        r = self._post("/enter", {})
        self.entered = True
        self.pos = (0.0, 0.0)
        self.current_channel = 1
        self.last_enter = r
        return r

    def measure(self, x: float, y: float, channel: int) -> dict:
        """检测。返回 {'measure_result': 'no_signal'|'near'|'direction', 'svd_deg': float|None}。"""
        if not (1 <= int(channel) <= N_CHANNEL):
            raise ValueError(f"channel 越界: {channel}")
        r = self._post("/measure", {"position": {"x": float(x), "y": float(y)},
                                    "channel": int(channel)})
        self.pos = (float(x), float(y))
        self.current_channel = int(channel)
        return {"measure_result": r.get("measure_result", "no_signal"),
                "svd_deg": (float(r["svd_deg"]) if "svd_deg" in r else None),
                "virtual_time_s": self.virtual_time}

    def clear(self, x: float, y: float, channel: int) -> str:
        """清除。返回 'success' | 'no_target_in_range'。"""
        r = self._post("/clear", {"position": {"x": float(x), "y": float(y)},
                                  "channel": int(channel)})
        self.pos = (float(x), float(y))
        res = r.get("clear_result", "no_target_in_range")
        if res == "success":
            self.cleared.add(int(channel))
        return res

    def exit(self) -> dict:
        return self._post("/exit", {})

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
    """本地 Mock：逐条复现《接口说明》的请求/响应契约与虚拟时间模型。

    与真实模拟器差异：源数量/位置/半径/朝向由本地随机生成（seed 可复现），
    不涉及登录与联网。用于开发与端到端验证客户端与策略。
    """

    def __init__(self, port: int = DEFAULT_PORT, seed: int = SEED,
                 kind_mix: bool = False, dir_frac: float = 0.4, n_src: int | None = None):
        self.port, self.seed = port, seed
        self.kind_mix, self.dir_frac, self.n_src = kind_mix, dir_frac, n_src
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
        self._seen_req: dict[str, str] = {}

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
        self.started, self._seen_req = True, {}

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
                    status, resp = 400, {"error": str(e)}
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

    def _handle(self, path, body):
        if path not in ("/enter", "/measure", "/clear", "/exit"):
            return 404, {"error": "path not found"}
        if not isinstance(body, dict):
            return 400, {"error": "body must be object"}

        # 幂等键：同一 request_id 不允许不同动作
        rid = body.get("request_id")
        if rid is not None:
            if rid in self._seen_req and self._seen_req[rid] != path:
                return 409, {"error": "request_id conflict"}
            self._seen_req[rid] = path

        if body.get("arena_id") != "default":
            return 200, {"accepted": False, "virtual_time_s": 0,
                         "real_timestamp_ms": int(time.time() * 1000)}
        if not body.get("robot_id") or not rid:
            return 400, {"error": "missing robot_id/request_id"}

        if path == "/enter":
            if not self.started:
                self._reset()
            self.pos, self.channel = (0.0, 0.0), 1
            return 200, {**self._envelope(),
                         "max_virtual_duration_s": 360000,
                         "max_real_duration_s": 1200,
                         "remaining_real_duration_s": 1200}

        if path == "/exit":
            return 200, {**self._envelope(), "exit_reason": "user_exit"}

        pos = body.get("position")
        ch = body.get("channel")
        if not isinstance(pos, dict) or "x" not in pos or "y" not in pos:
            return 400, {"error": "position required"}
        x, y = float(pos["x"]), float(pos["y"])
        if not (math.isfinite(x) and math.isfinite(y)):
            return 400, {"error": "non-finite position"}
        if abs(x) > 2_000_000 or abs(y) > 2_000_000:
            return 400, {"error": "position out of range"}
        if not isinstance(ch, (int, float)) or int(ch) != ch or not (1 <= int(ch) <= N_CHANNEL):
            return 400, {"error": "channel invalid"}
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
    args = ap.parse_args()
    if args.server:
        MockSimulatorServer(port=args.port, seed=args.seed,
                            kind_mix=args.kind_mix).start(block=True)
    else:
        print("用法：py -3.12 -m simulator_http --server [--port 2026] [--kind-mix]")