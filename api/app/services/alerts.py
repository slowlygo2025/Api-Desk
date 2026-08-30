"""Alertas: whales (principal) + market signals (auxiliar)."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import smtplib
from email.message import EmailMessage
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.models import AlertDelivery, AlertRule, ApiClient, MarketSignalEvent, WhaleEvent
from app.services.metrics import metrics

logger = logging.getLogger(__name__)
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


class AlertService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def matches_whale(self, rule: AlertRule, whale: WhaleEvent) -> bool:
        kinds = rule.alert_kinds or ["whale"]
        if "whale" not in kinds and "both" not in kinds:
            return False
        if not rule.is_active:
            return False
        if whale.amount_usd < rule.min_usd:
            return False
        if rule.assets and whale.asset not in rule.assets:
            return False
        if rule.chains and whale.chain not in rule.chains:
            return False
        if rule.flow_types and whale.flow_type not in rule.flow_types:
            return False
        if RISK_ORDER.get(whale.risk_level, 0) < RISK_ORDER.get(rule.min_risk_level, 0):
            return False
        return True

    def matches_market(self, rule: AlertRule, asset: str, stress: float) -> bool:
        kinds = rule.alert_kinds or ["whale"]
        # compat: "xmr" cuenta como market para XMR
        if "market" not in kinds and "both" not in kinds and not ("xmr" in kinds and asset == "XMR"):
            return False
        if rule.signal_assets and asset.upper() not in [a.upper() for a in rule.signal_assets]:
            return False
        min_stress = float(getattr(rule, "min_market_stress", None) or getattr(rule, "min_xmr_stress", None) or 0.45)
        return bool(rule.is_active) and stress >= min_stress

    def sign_payload(self, secret: str, body: bytes) -> str:
        return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    async def _send_webhook(self, client: ApiClient, payload: dict[str, Any]) -> tuple[str, dict]:
        if not client.webhook_url:
            return "skipped", {"error": "no_webhook_url"}
        body = json.dumps(payload).encode()
        headers = {"Content-Type": "application/json"}
        if client.webhook_secret:
            headers["X-Api-Desk-Signature"] = self.sign_payload(client.webhook_secret, body)
        try:
            async with httpx.AsyncClient(timeout=10.0) as http:
                r = await http.post(client.webhook_url, content=body, headers=headers)
            return ("sent" if r.status_code < 300 else "failed"), {"status_code": r.status_code}
        except Exception as exc:
            return "failed", {"error": str(exc)}

    async def _send_telegram(self, destination: dict[str, Any], text: str) -> tuple[str, dict]:
        token = self.settings.telegram_bot_token
        chat_id = destination.get("telegram_chat_id") or destination.get("chat_id")
        if not token or not chat_id:
            return "skipped", {"error": "telegram_not_configured"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as http:
                r = await http.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat_id, "text": text},
                )
            return ("sent" if r.status_code < 300 else "failed"), {"status_code": r.status_code}
        except Exception as exc:
            return "failed", {"error": str(exc)}

    def _send_email(self, destination: dict[str, Any], subject: str, body: str) -> tuple[str, dict]:
        to_addr = destination.get("email")
        if not to_addr or not self.settings.smtp_host:
            return "skipped", {"error": "email_not_configured"}
        msg = EmailMessage()
        msg["From"] = self.settings.alert_from_email
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.set_content(body)
        try:
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=15) as smtp:
                smtp.starttls()
                if self.settings.smtp_user:
                    smtp.login(self.settings.smtp_user, self.settings.smtp_password)
                smtp.send_message(msg)
            return "sent", {"to": to_addr}
        except Exception as exc:
            return "failed", {"error": str(exc)}

    async def _dispatch_channels(
        self,
        session: AsyncSession,
        rule: AlertRule,
        client: ApiClient | None,
        *,
        dedup_key: str,
        payload: dict[str, Any],
        text: str,
        whale_id: str | None = None,
        market_signal_id: str | None = None,
    ) -> list[AlertDelivery]:
        deliveries: list[AlertDelivery] = []
        dest = rule.destination or {}
        for channel in rule.channels or ["webhook"]:
            key = f"{dedup_key}:{channel}"
            if channel == "webhook" and client:
                status, response = await self._send_webhook(client, payload)
            elif channel == "telegram":
                status, response = await self._send_telegram(dest, text)
            elif channel == "email":
                status, response = self._send_email(dest, payload.get("event", "alert"), text)
            else:
                status, response = "skipped", {"error": f"unknown_channel:{channel}"}

            delivery = AlertDelivery(
                rule_id=rule.id,
                whale_id=whale_id,
                xmr_signal_id=market_signal_id,
                channel=channel,
                dedup_key=key,
                status=status,
                response=response,
            )
            session.add(delivery)
            try:
                await session.commit()
                deliveries.append(delivery)
                metrics.inc("apidesk_alerts_sent_total", channel=channel, status=status)
            except IntegrityError:
                await session.rollback()
                metrics.inc("apidesk_alerts_dedup_total", channel=channel)
        return deliveries

    async def evaluate_and_dispatch(self, session: AsyncSession, whale: WhaleEvent) -> list[AlertDelivery]:
        rules = (await session.execute(select(AlertRule).where(AlertRule.is_active.is_(True)))).scalars().all()
        out: list[AlertDelivery] = []
        payload = {
            "event": "whale.detected",
            "whale_id": whale.id,
            "tx_hash": whale.tx_hash,
            "asset": whale.asset,
            "chain": whale.chain,
            "amount_usd": whale.amount_usd,
            "flow_type": whale.flow_type,
            "risk_level": whale.risk_level,
            "impact_score": whale.impact_score,
            "from_label": whale.from_label,
            "to_label": whale.to_label,
        }
        text = f"Whale {whale.asset} ${whale.amount_usd:,.0f} {whale.chain} {whale.flow_type}\n{whale.tx_hash}"
        for rule in rules:
            if not self.matches_whale(rule, whale):
                continue
            client = await session.get(ApiClient, rule.client_id)
            out.extend(
                await self._dispatch_channels(
                    session,
                    rule,
                    client,
                    dedup_key=f"whale:{whale.id}:{rule.id}",
                    payload=payload,
                    text=text,
                    whale_id=whale.id,
                )
            )
        return out

    async def evaluate_market(
        self,
        session: AsyncSession,
        *,
        asset: str,
        stress: float,
        spillover: float,
        regime: str,
        signal: MarketSignalEvent | None = None,
    ) -> list[AlertDelivery]:
        rules = (await session.execute(select(AlertRule).where(AlertRule.is_active.is_(True)))).scalars().all()
        out: list[AlertDelivery] = []
        payload = {
            "event": "market.stress",
            "asset": asset,
            "stress_score": stress,
            "spillover_hint": spillover,
            "regime": regime,
            "signal_id": signal.id if signal else None,
        }
        text = f"{asset} market stress={stress:.2f} spillover={spillover:.2f} regime={regime}"
        for rule in rules:
            if not self.matches_market(rule, asset, stress):
                continue
            client = await session.get(ApiClient, rule.client_id)
            sid = signal.id if signal else "none"
            out.extend(
                await self._dispatch_channels(
                    session,
                    rule,
                    client,
                    dedup_key=f"market:{asset}:{sid}:{rule.id}:{regime}",
                    payload=payload,
                    text=text,
                    market_signal_id=signal.id if signal else None,
                )
            )
        return out

    # compat
    async def evaluate_xmr(self, session, **kwargs):
        return await self.evaluate_market(session, asset="XMR", **kwargs)
