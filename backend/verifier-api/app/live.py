"""Live scanning background task and SSE broadcast.

Runs a periodic scan loop over configured targets and broadcasts results
to all connected SSE clients via ``asyncio.Queue`` per subscriber.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

from app.adapters.factory import build_scanner
from app.state_machine import STATE_LABELS, build_recommendations

LOGGER = logging.getLogger(__name__)

_DEFAULT_TARGETS = [
    ("localhost", 8443),
    ("localhost", 8444),
    ("localhost", 8445),
    ("localhost", 8446),
    ("localhost", 2222),
]

_SCAN_INTERVAL = float(os.getenv("LIVE_SCAN_INTERVAL", "10"))


def _parse_targets() -> list[tuple[str, int]]:
    raw = os.getenv("SCAN_TARGETS", "")
    if not raw:
        return list(_DEFAULT_TARGETS)
    targets: list[tuple[str, int]] = []
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if ":" in entry:
            host, port_str = entry.rsplit(":", 1)
            targets.append((host, int(port_str)))
        else:
            targets.append((entry, 443))
    return targets


class LiveScanner:
    def __init__(self) -> None:
        self._scanner = build_scanner()
        self._targets = _parse_targets()
        self._subscribers: dict[int, asyncio.Queue[str]] = {}
        self._latest: dict[str, dict[str, Any]] = {}
        self._task: asyncio.Task[None] | None = None
        self._counter = 0

    @property
    def latest_connections(self) -> list[dict[str, Any]]:
        return list(self._latest.values())

    def subscribe(self) -> asyncio.Queue[str]:
        self._counter += 1
        q: asyncio.Queue[str] = asyncio.Queue()
        self._subscribers[self._counter] = q
        LOGGER.info(
            "SSE subscriber %d connected (total: %d)",
            self._counter,
            len(self._subscribers),
        )
        return q

    def unsubscribe(self, uid: int) -> None:
        self._subscribers.pop(uid, None)
        LOGGER.info(
            "SSE subscriber %d disconnected (total: %d)",
            uid,
            len(self._subscribers),
        )

    def _broadcast(self, data: str) -> None:
        for uid, q in list(self._subscribers.items()):
            try:
                q.put_nowait(data)
            except asyncio.QueueFull:
                LOGGER.warning("Dropping event for slow subscriber %d", uid)

    def _scan_target(self, hostname: str, port: int) -> dict[str, Any]:
        try:
            result = self._scanner.scan(hostname, port)
            return result.model_dump()
        except Exception:
            LOGGER.exception("Live scan failed for %s:%d", hostname, port)
            return {
                "endpoint": f"{hostname}:{port}",
                "state": "S0_CLASSICAL",
                "state_label": STATE_LABELS.get("S0_CLASSICAL", "Classical"),
                "evidence": {
                    "negotiated_group": "scan-failed",
                    "certificate_algorithm": "unknown",
                    "certificate_chain_bytes": 0,
                    "handshake_bytes": 0,
                    "latency_ms": 0,
                    "pqc_library_detected": False,
                    "details": {},
                },
                "recommendations": build_recommendations("S0_CLASSICAL"),
                "error": True,
            }

    async def _loop(self) -> None:
        LOGGER.info(
            "Live scanner started: %d targets, %.0fs interval",
            len(self._targets),
            _SCAN_INTERVAL,
        )
        while True:
            for hostname, port in self._targets:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self._scan_target, hostname, port
                )
                self._latest[result["endpoint"]] = result
                payload = json.dumps(result, default=str)
                self._broadcast(payload)
            await asyncio.sleep(_SCAN_INTERVAL)

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._loop())
            LOGGER.info("Live scanner background task created")

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            LOGGER.info("Live scanner background task cancelled")


LIVE_SCANNER = LiveScanner()
