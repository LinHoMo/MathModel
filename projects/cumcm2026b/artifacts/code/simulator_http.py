#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""simulator_http.py —— B 题 HTTP 模拟器客户端 + 本地 Mock 服务器。

双角色：
  1) 作为模块导入 → SimulatorHTTP 连接官方模拟器（或 Mock 服务器），
     duck-type 兼容 solve_b.py 的 Simulator。
  2) 作为脚本运行 → `py -3.12 -m simulator_http --server` 启动本地 Mock。

Mock 模式（mock_mode=True）：
  MockServer 在 /enter 时返回源元数据（sid/channel/kind），在 /clear 时返回
  cleared_sid。SimulatorHTTP 据此维护 self.sources 与 self.cleared（sid 集合），
  与本地 Simulator 完全 duck-type 兼容，可直接代入 dog_strategy / run_trials。

官方模式（mock_mode=False）：
  时间由本地近似累加（官方 API 不返回 vtime）；/exit 后填充 sources 占位。
  需使用适配后的 run_http_trials（在 solve_b.py 中），因官方不返回 per-source 元数据。

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
# 常量（与 solve_b.py 对齐）
# ---------------------------------------------------------------------------
R_AREA = 1800.0
EPS_BEARING = 1.0
R_REC_MIN, R_REC_MAX = 1000.0, 1500.0
R_REC_NOM = 1250.0
N_CHANNEL = 20
N_SRC_MIN, N_SRC_MAX = 10, 16

T_DETECT = 5.0
T_OPTIC = 3.0
T_LASER = 2.0
D_OPTIC = 20.0
D_DIRECT = 5.0
V_DOG = 5.0
SEED = 42


# ===================================================================
# SimulatorHTTP —— HTTP 客户端
# ===================================================================
class SimulatorHTTP:
    """通过 HTTP+JSON 与模拟器通信。

    mock_mode=True：连接到 MockServer，服务端管理全部时间（响应含 vtime），
     /enter 预填 sources、/clear 返回 cleared_sid → 与本地 Simulator 完全兼容。

    mock_mode=False：连接到官方模拟器，本地近似计时，/exit 后获取源总数。
    """

    def __init__(self, base_url: str = "http://127.0.0.1:2026",
                 robot_id: str = "TEAM000", mock_mode: bool = False):
        self.base_url = base_url.rstrip("/")
        self.robot_id = robot_id
        self._mock_mode = mock_mode
        self._req_seq = 0

        # 公共状态
        self.dog_pos = (0.0, 0.0)
        self.vtime = 0.0
        self.path_len = 0.0
        self.n_detect = 0
        self.n_move = 0
        self.cleared: set = set()          # mock: 源 sid 集合；否则频道号集合
        self.sources: list = []            # mock: _Src 对象；否则 _PlaceholderSource
        self._exited = False
        self._ch_cleared: dict[int, bool] = {}

        self._enter()

    # ----- HTTP 原语 -----
    def _next_req_id(self) -> str:
        self._req_seq += 1
        return f"{self.robot_id}-{self._req_seq}"

    def _post(self, path: str, payload: dict) -> dict:
        payload["robot_id"] = self.robot_id
        payload["request_id"] = self._next_req_id()
        data = json.dumps(payload).encode("utf-8")
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise ConnectionError(f"无法连接模拟器 {url}: {e}") from e
        except json.JSONDecodeError as e:
            body = ""
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    body = resp.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            raise ValueError(f"模拟器响应非 JSON: {body[:200]}") from e

    def _enter(self):
        resp = self._post("/enter", {})
        if resp.get("status") != "ok":
            raise RuntimeError(f"/enter 失败: {resp}")
        if self._mock_mode and "sources" in resp:
            self.sources = [_Src(**s) for s in resp["sources"]]
        self._sync_state(resp)

    def exit(self):
        if self._exited:
            return
        resp = self._post("/exit", {})
        self._exited = True
        self._sync_state(resp)
        if not self._mock_mode and not self.sources:
            n = resp.get("total_sources", 0)
            self.sources = [_PlaceholderSource(i) for i in range(n)]

    def _sync_state(self, resp: dict):
        if "vtime" in resp:
            self.vtime = float(resp["vtime"])
        if "path_len" in resp:
            self.path_len = float(resp["path_len"])

    # ----- 模拟器接口（对齐 Simulator） -----
    def move_to(self, x: float, y: float):
        d = math.dist(self.dog_pos, (x, y))
        self.path_len += d
        if not self._mock_mode:
            self.vtime += d / V_DOG
        self.dog_pos = (x, y)
        self.n_move += 1

    def is_channel_cleared(self, ch: int) -> bool:
        return self._ch_cleared.get(ch, False)

    def detect(self, px: float, py: float, channel: int
               ) -> tuple[float | None, float | None]:
        """检测频道 channel。返回 (bearing_deg|None, rel|None)。"""
        resp = self._post("/measure", {
            "position": [round(px, 4), round(py, 4)],
            "channel": channel,
        })
        self._sync_state(resp)
        if not self._mock_mode:
            self.vtime += T_DETECT
        self.n_detect += 1

        result = resp.get("result", "")
        if result == "direction":
            bearing = float(resp["bearing"])
            rel = float(resp.get("signal_strength", 0.5))
            return bearing % 360.0, rel
        elif result == "near":
            return None, 0.0
        else:
            return None, None

    def sweep_all_channels(self, px: float, py: float,
                           channels: list[int] | None = None
                           ) -> dict[int, tuple[float, float]]:
        if channels is None:
            channels = list(range(1, N_CHANNEL + 1))
        found = {}
        for ch in channels:
            if self.is_channel_cleared(ch):
                continue
            b, rel = self.detect(px, py, ch)
            if b is not None and rel is not None and rel > 0.0:
                found[ch] = (b, rel)
        return found

    def try_clear(self, x: float, y: float) -> bool:
        """发送 /clear 请求（逐个未清除频道）；返回 True 表示清除了某源。"""
        for ch in range(1, N_CHANNEL + 1):
            if self.is_channel_cleared(ch):
                continue
            resp = self._post("/clear", {
                "position": [round(x, 4), round(y, 4)],
                "channel": ch,
            })
            self._sync_state(resp)
            result = resp.get("result", "")
            if result == "success":
                if not self._mock_mode:
                    self.vtime += T_OPTIC + T_LASER
                sid = resp.get("cleared_sid")
                if sid is not None:
                    self.cleared.add(sid)
                else:
                    self.cleared.add(ch)
                self._ch_cleared[ch] = True
                return True
            elif result == "no_target_in_range":
                if not self._mock_mode:
                    self.vtime += T_OPTIC
        return False


class _Src:
    """Mock 模式下由 /enter 预填充的源元数据。"""
    __slots__ = ("sid", "channel", "kind")
    def __init__(self, sid: int, channel: int, kind: str = "omni"):
        self.sid = sid
        self.channel = channel
        self.kind = kind


class _PlaceholderSource:
    __slots__ = ("sid", "channel", "kind")
    def __init__(self, sid: int):
        self.sid = sid
        self.channel = 0
        self.kind = "omni"


# ===================================================================
# MockServer —— 本地 Mock HTTP 服务器
# ===================================================================
class MockServer:
    """启动本地 HTTP 服务器，内部包装 Simulator。

    /enter 返回源元数据列表，/measure/clear 返回 vtime+path_len+cleared_sid，
    使 SimulatorHTTP(mock_mode=True) 可与本地 Simulator 完全互换。

    用法：
        server = MockServer(port=2026, seed=42, kind_mix=False)
        server.start()
        sim = SimulatorHTTP(mock_mode=True)
        ...  # 运行策略
        sim.exit()
        server.stop()
    """

    def __init__(self, port: int = 2026, seed: int = SEED,
                 kind_mix: bool = False, dir_frac: float = 0.4,
                 n_src: int | None = None):
        self.port = port
        self.seed = seed
        self.kind_mix = kind_mix
        self.dir_frac = dir_frac
        self.n_src = n_src
        self._httpd: HTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._sim = None

    def start(self, block: bool = False):
        from solve_b import Simulator as _Sim
        self._sim = _Sim(seed=self.seed, n_src=self.n_src,
                         kind_mix=self.kind_mix, dir_frac=self.dir_frac)

        parent = self

        class _Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = (json.loads(self.rfile.read(length))
                        if length > 0 else {})
                resp = parent._handle(self.path, body)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode("utf-8"))

            def log_message(self, format, *args):
                pass

        self._httpd = HTTPServer(("127.0.0.1", self.port), _Handler)
        if block:
            print(f"Mock 模拟器启动于 http://127.0.0.1:{self.port}")
            print(f"  seed={self.seed}  kind_mix={self.kind_mix}")
            self._httpd.serve_forever()
        else:
            self._thread = threading.Thread(
                target=self._httpd.serve_forever, daemon=True)
            self._thread.start()
            time.sleep(0.1)

    def stop(self):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd = None
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _state(self) -> dict:
        sim = self._sim
        return {"vtime": round(sim.vtime, 6),
                "path_len": round(sim.path_len, 4)}

    def _handle(self, path: str, body: dict) -> dict:
        sim = self._sim
        if path == "/enter":
            sim.dog_pos = (0.0, 0.0)
            sim.vtime = 0.0
            sim.path_len = 0.0
            return {
                "status": "ok", "message": "entered",
                "sources": [{"sid": s.sid, "channel": s.channel, "kind": s.kind}
                            for s in sim.sources],
                **self._state(),
            }

        elif path == "/measure":
            x, y = body.get("position", [0, 0])[:2]
            ch = body.get("channel", 1)
            sim.move_to(x, y)
            b, rel = sim.detect(x, y, ch)
            base = {"position": [round(x, 4), round(y, 4)], "channel": ch,
                    **self._state()}
            if b is not None and rel is not None:
                if rel <= 0.0:
                    return {**base, "result": "near"}
                return {**base, "result": "direction", "bearing": round(b, 4),
                        "signal_strength": round(rel, 6)}
            if rel is not None and rel <= 0.0:
                return {**base, "result": "near"}
            return {**base, "result": "no_signal"}

        elif path == "/clear":
            x, y = body.get("position", [0, 0])[:2]
            ch = body.get("channel", 1)
            sim.move_to(x, y)

            cands = [s for s in sim.sources
                     if s.sid not in sim.cleared
                     and s.channel == ch
                     and math.dist((x, y), (s.x, s.y)) <= D_OPTIC]
            if cands:
                src = min(cands, key=lambda s: math.dist((x, y), (s.x, s.y)))
                sim.vtime += T_OPTIC + T_LASER
                sim.cleared.add(src.sid)
                return {"result": "success", "cleared_sid": src.sid,
                        "channel": ch, **self._state()}
            sim.vtime += T_OPTIC
            return {"result": "no_target_in_range", "channel": ch,
                    **self._state()}

        elif path == "/exit":
            n_total = len(sim.sources)
            n_omni = sum(1 for s in sim.sources if s.kind == "omni")
            return {"status": "ok", "reason": "user_exit",
                    "total_sources": n_total, "omni_sources": n_omni,
                    "dir_sources": n_total - n_omni, **self._state()}

        return {"status": "error", "message": f"unknown path {path}"}


# ===================================================================
# CLI 入口
# ===================================================================
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="B 题 HTTP 模拟器客户端/服务器")
    ap.add_argument("--server", action="store_true", help="启动 Mock 服务器")
    ap.add_argument("--port", type=int, default=2026)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--kind-mix", action="store_true",
                    help="混合全向+定向源（问题4）")
    args = ap.parse_args()

    if args.server:
        server = MockServer(port=args.port, seed=args.seed,
                            kind_mix=args.kind_mix)
        server.start(block=True)
    else:
        print("用法：py -3.12 -m simulator_http --server [--port 2026]")