"""Métricas in-process estilo Prometheus (texto /v1/metrics)."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self.counters: dict[str, float] = defaultdict(float)
        self.gauges: dict[str, float] = {}
        self.started_at = time.time()

    def inc(self, name: str, value: float = 1.0, **labels: str) -> None:
        key = self._key(name, labels)
        with self._lock:
            self.counters[key] += value

    def set_gauge(self, name: str, value: float, **labels: str) -> None:
        key = self._key(name, labels)
        with self._lock:
            self.gauges[key] = value

    def _key(self, name: str, labels: dict[str, str]) -> str:
        if not labels:
            return name
        parts = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{parts}}}"

    def render_prometheus(self) -> str:
        lines: list[str] = [
            f"# HELP apidesk_up Api-Desk process up",
            f"# TYPE apidesk_up gauge",
            "apidesk_up 1",
            f"# HELP apidesk_uptime_seconds Uptime",
            f"# TYPE apidesk_uptime_seconds gauge",
            f"apidesk_uptime_seconds {time.time() - self.started_at:.0f}",
        ]
        with self._lock:
            for k, v in sorted(self.counters.items()):
                lines.append(f"# TYPE {k.split('{')[0]} counter")
                lines.append(f"{k} {v}")
            for k, v in sorted(self.gauges.items()):
                lines.append(f"# TYPE {k.split('{')[0]} gauge")
                lines.append(f"{k} {v}")
        return "\n".join(lines) + "\n"


metrics = MetricsRegistry()
