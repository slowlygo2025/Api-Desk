"""Solana real: SOL nativo + SPL USDT/USDC en slots recientes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import Settings
from app.providers.base import FetchLimits, RawTransfer

USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
MINT_META = {
    USDT_MINT: ("USDT", 6),
    USDC_MINT: ("USDC", 6),
}

SOLANA_RPCS = (
    "https://api.mainnet-beta.solana.com",
    "https://solana-rpc.publicnode.com",
    "https://rpc.ankr.com/solana",
)

# slots a mirar (Solana ~400ms/slot; 40 ≈ 16s). Público rate-limita fuerte.
SOL_LOOKBACK_SLOTS = 25


class SolanaProvider:
    chain = "solana"
    name = "solana_rpc"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def rpc_urls(self) -> list[str]:
        urls: list[str] = []
        if self.settings.helius_api_key:
            urls.append(f"https://mainnet.helius-rpc.com/?api-key={self.settings.helius_api_key}")
        urls.extend(SOLANA_RPCS)
        return urls

    async def _rpc(self, method: str, params: list[Any]) -> Any:
        last_err: Exception | None = None
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        async with httpx.AsyncClient(timeout=35.0) as client:
            for url in self.rpc_urls():
                try:
                    r = await client.post(url, json=payload)
                    data = r.json()
                    if "error" in data:
                        last_err = RuntimeError(str(data["error"]))
                        continue
                    return data.get("result")
                except Exception as exc:
                    last_err = exc
                    continue
        raise RuntimeError(f"solana RPC failed: {last_err}")

    async def health(self) -> bool:
        try:
            slot = await self._rpc("getSlot", [])
            return slot is not None
        except Exception:
            return False

    async def fetch_recent_transfers(self, limits: FetchLimits) -> list[RawTransfer]:
        tip = await self._rpc("getSlot", [])
        if tip is None:
            return []
        results: list[RawTransfer] = []
        seen: set[tuple[str, int]] = set()

        # Muestrear slots (cada 2) para no matar RPC público
        slots = list(range(tip - SOL_LOOKBACK_SLOTS, tip + 1, 2))
        for slot in reversed(slots):
            try:
                block = await self._rpc(
                    "getBlock",
                    [
                        slot,
                        {
                            "encoding": "jsonParsed",
                            "transactionDetails": "full",
                            "rewards": False,
                            "maxSupportedTransactionVersion": 0,
                        },
                    ],
                )
            except Exception:
                continue
            if not block:
                continue
            block_time = None
            if block.get("blockTime"):
                block_time = datetime.fromtimestamp(int(block["blockTime"]), tz=timezone.utc)

            for idx, entry in enumerate(block.get("transactions") or []):
                meta = entry.get("meta") or {}
                if meta.get("err"):
                    continue
                tx = entry.get("transaction") or {}
                message = tx.get("message") or {}
                sigs = tx.get("signatures") or []
                tx_hash = sigs[0] if sigs else f"slot{slot}_{idx}"

                # SOL nativo: balance changes
                pre_bal = meta.get("preBalances") or []
                post_bal = meta.get("postBalances") or []
                keys = []
                for k in message.get("accountKeys") or []:
                    if isinstance(k, dict):
                        keys.append(k.get("pubkey", ""))
                    else:
                        keys.append(str(k))

                for i, (pre, post) in enumerate(zip(pre_bal, post_bal)):
                    delta_lamports = int(post) - int(pre)
                    if delta_lamports <= 0:
                        continue
                    amount_sol = delta_lamports / 1e9
                    if amount_sol < limits.min_sol:
                        continue
                    # origen: mayor caída de balance
                    from_addr = "unknown"
                    max_drop = 0
                    for j, (p0, p1) in enumerate(zip(pre_bal, post_bal)):
                        drop = int(p0) - int(p1)
                        if drop > max_drop:
                            max_drop = drop
                            from_addr = keys[j] if j < len(keys) else "unknown"
                    to_addr = keys[i] if i < len(keys) else "unknown"
                    dedup = (tx_hash, i)
                    if dedup in seen:
                        continue
                    seen.add(dedup)
                    results.append(
                        RawTransfer(
                            tx_hash=tx_hash,
                            chain="solana",
                            asset="SOL",
                            amount=amount_sol,
                            from_address=from_addr,
                            to_address=to_addr,
                            block_time=block_time,
                            log_index=i,
                            provider=self.name,
                            raw={"slot": slot, "type": "native"},
                        )
                    )

                # SPL USDT/USDC vía token balance diffs
                pre_tok = meta.get("preTokenBalances") or []
                post_tok = meta.get("postTokenBalances") or []
                pre_map = {(b.get("accountIndex"), b.get("mint")): b for b in pre_tok}
                for post in post_tok:
                    mint = post.get("mint")
                    if mint not in MINT_META:
                        continue
                    asset, decimals = MINT_META[mint]
                    key = (post.get("accountIndex"), mint)
                    pre = pre_map.get(key)
                    pre_amt = float(((pre or {}).get("uiTokenAmount") or {}).get("uiAmount") or 0)
                    post_amt = float((post.get("uiTokenAmount") or {}).get("uiAmount") or 0)
                    delta = post_amt - pre_amt
                    if delta < limits.min_stable:
                        continue
                    owner = post.get("owner") or "unknown"
                    # from: owner del pre con mayor salida mismo mint
                    from_addr = "unknown"
                    max_out = 0.0
                    for pb in pre_tok:
                        if pb.get("mint") != mint:
                            continue
                        pb_amt = float((pb.get("uiTokenAmount") or {}).get("uiAmount") or 0)
                        # matching post
                        pkey = (pb.get("accountIndex"), mint)
                        pt = next((x for x in post_tok if (x.get("accountIndex"), x.get("mint")) == pkey), None)
                        pt_amt = float(((pt or {}).get("uiTokenAmount") or {}).get("uiAmount") or 0)
                        out_amt = pb_amt - pt_amt
                        if out_amt > max_out:
                            max_out = out_amt
                            from_addr = pb.get("owner") or "unknown"

                    log_index = int(post.get("accountIndex") or 0)
                    dedup = (tx_hash, 10_000 + log_index)
                    if dedup in seen:
                        continue
                    seen.add(dedup)
                    results.append(
                        RawTransfer(
                            tx_hash=tx_hash,
                            chain="solana",
                            asset=asset,
                            amount=delta,
                            from_address=from_addr,
                            to_address=owner,
                            block_time=block_time,
                            log_index=log_index,
                            provider=self.name,
                            raw={"slot": slot, "mint": mint},
                        )
                    )
        return results

    async def get_transfer(self, tx_hash: str) -> RawTransfer | None:
        tx = await self._rpc(
            "getTransaction",
            [tx_hash, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
        )
        if not tx:
            return None
        # Reutilizar lógica mínima: mayor delta stable o SOL
        limits = FetchLimits(min_btc=0, min_eth=0, min_stable=0, min_sol=0)
        # parse one tx as pseudo-block
        block = {"blockTime": tx.get("blockTime"), "transactions": [tx]}
        # hack: call internal by temp structure — simplificado
        tip_slot = 0
        _ = tip_slot
        meta = tx.get("meta") or {}
        if meta.get("err"):
            return None
        sigs = ((tx.get("transaction") or {}).get("signatures")) or [tx_hash]
        # prefer largest stable delta
        best: RawTransfer | None = None
        post_tok = meta.get("postTokenBalances") or []
        pre_tok = meta.get("preTokenBalances") or []
        pre_map = {(b.get("accountIndex"), b.get("mint")): b for b in pre_tok}
        for post in post_tok:
            mint = post.get("mint")
            if mint not in MINT_META:
                continue
            asset, _ = MINT_META[mint]
            pre = pre_map.get((post.get("accountIndex"), mint))
            pre_amt = float(((pre or {}).get("uiTokenAmount") or {}).get("uiAmount") or 0)
            post_amt = float((post.get("uiTokenAmount") or {}).get("uiAmount") or 0)
            delta = post_amt - pre_amt
            if delta <= 0:
                continue
            cand = RawTransfer(
                tx_hash=sigs[0],
                chain="solana",
                asset=asset,
                amount=delta,
                from_address="unknown",
                to_address=post.get("owner") or "unknown",
                provider=self.name,
                raw={"mint": mint},
            )
            if best is None or cand.amount > best.amount:
                best = cand
        return best
