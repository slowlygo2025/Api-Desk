"""Tickets efímeros para WebSocket (handshake autenticado)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import Settings, get_settings


def _secret(settings: Settings | None = None) -> str:
    s = settings or get_settings()
    return s.ws_ticket_secret or s.secret_key


def create_ws_ticket(client_id: str, plan: str, ttl_sec: int = 15, settings: Settings | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": client_id,
        "plan": plan,
        "typ": "ws_ticket",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_sec)).timestamp()),
    }
    return jwt.encode(payload, _secret(settings), algorithm="HS256")


def verify_ws_ticket(token: str, settings: Settings | None = None) -> dict | None:
    try:
        payload = jwt.decode(token, _secret(settings), algorithms=["HS256"])
        if payload.get("typ") != "ws_ticket":
            return None
        return payload
    except JWTError:
        return None
