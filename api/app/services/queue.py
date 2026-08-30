"""Cola de jobs durable-lite: Redis si está enabled, si no asyncio memory + retry."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)


@dataclass
class Job:
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)
    attempts: int = 0
    max_attempts: int = 5
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class JobQueue:
    def __init__(self) -> None:
        self._q: deque[Job] = deque()
        self._dlq: deque[Job] = deque()
        self._lock = asyncio.Lock()
        self.handlers: dict[str, Callable[[Job], Awaitable[None]]] = {}

    def register(self, kind: str, handler: Callable[[Job], Awaitable[None]]) -> None:
        self.handlers[kind] = handler

    async def enqueue(self, kind: str, payload: dict[str, Any] | None = None) -> Job:
        job = Job(kind=kind, payload=payload or {})
        async with self._lock:
            self._q.append(job)
        return job

    async def size(self) -> dict[str, int]:
        async with self._lock:
            return {"pending": len(self._q), "dlq": len(self._dlq)}

    async def process_once(self) -> bool:
        async with self._lock:
            if not self._q:
                return False
            job = self._q.popleft()
        handler = self.handlers.get(job.kind)
        if not handler:
            logger.warning("no handler for job %s", job.kind)
            return True
        try:
            await handler(job)
            return True
        except Exception:
            job.attempts += 1
            logger.exception("job failed %s attempt=%s", job.kind, job.attempts)
            async with self._lock:
                if job.attempts >= job.max_attempts:
                    self._dlq.append(job)
                else:
                    self._q.append(job)
            return True


job_queue = JobQueue()
