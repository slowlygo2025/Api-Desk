"""Venues CEX genéricos multi-asset (trades + book + OHLC)."""

from __future__ import annotations

import time
from datetime import datetime, timezone

import httpx

HTTP_HEADERS = {"User-Agent": "Api-Desk/2.0 (market-signals; +https://apidesk.local)"}

from app.providers.market.types import (
    MarketCandle,
    MarketTrade,
    VenueSnapshot,
    build_book,
)


class KrakenMarketVenue:
    name = "kraken"
    base = "https://api.kraken.com/0/public"

    async def fetch(self, asset: str, pair: str, trade_limit: int, book_depth: int, candle_limit: int) -> VenueSnapshot:
        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=HTTP_HEADERS) as client:
                tr = await client.get(f"{self.base}/Trades", params={"pair": pair})
                dp = await client.get(f"{self.base}/Depth", params={"pair": pair, "count": book_depth})
                oh = await client.get(f"{self.base}/OHLC", params={"pair": pair, "interval": 1})
            for resp in (tr, dp, oh):
                resp.raise_for_status()
                if resp.json().get("error"):
                    raise RuntimeError(resp.json()["error"])

            trades_raw = next(iter(tr.json()["result"].values()))
            trades = []
            for row in trades_raw[-trade_limit:]:
                price, amount = float(row[0]), float(row[1])
                side = "buy" if row[3] == "b" else "sell" if row[3] == "s" else "unknown"
                trades.append(
                    MarketTrade(
                        exchange=self.name,
                        pair=pair,
                        asset=asset,
                        price=price,
                        amount=amount,
                        notional_usd=price * amount,
                        side=side,
                        ts=datetime.fromtimestamp(float(row[2]), tz=timezone.utc),
                        trade_id=str(row[6]) if len(row) > 6 else f"{row[2]}",
                    )
                )
            depth = next(iter(dp.json()["result"].values()))
            book = build_book(self.name, pair, asset, depth.get("bids", []), depth.get("asks", []), book_depth)
            candles = []
            for row in next(iter(oh.json()["result"].values()))[-candle_limit:]:
                o, h, l, c = map(float, (row[1], row[2], row[3], row[4]))
                vol = float(row[6])
                candles.append(
                    MarketCandle(
                        self.name, pair, asset, "1m",
                        datetime.fromtimestamp(int(row[0]), tz=timezone.utc),
                        o, h, l, c, vol, vol * c,
                    )
                )
            return VenueSnapshot(
                self.name, pair, asset, True, trades=trades, book=book, candles=candles,
                latency_ms=(time.perf_counter() - t0) * 1000,
            )
        except Exception as exc:
            return VenueSnapshot(self.name, pair, asset, False, error=str(exc), latency_ms=(time.perf_counter() - t0) * 1000)


class KucoinMarketVenue:
    name = "kucoin"
    base = "https://api.kucoin.com/api/v1/market"

    async def fetch(self, asset: str, pair: str, trade_limit: int, book_depth: int, candle_limit: int) -> VenueSnapshot:
        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=HTTP_HEADERS) as client:
                tr = await client.get(f"{self.base}/histories", params={"symbol": pair})
                ob = await client.get(f"{self.base}/orderbook/level2_20", params={"symbol": pair})
                cd = await client.get(f"{self.base}/candles", params={"symbol": pair, "type": "1min"})
            for resp in (tr, ob, cd):
                resp.raise_for_status()
                if resp.json().get("code") != "200000":
                    raise RuntimeError(resp.json())

            trades = []
            for row in (tr.json().get("data") or [])[:trade_limit]:
                price, amount = float(row["price"]), float(row["size"])
                raw_t = int(row["time"])
                ts_s = raw_t / 1_000_000_000 if raw_t > 10_000_000_000_000 else raw_t / 1000
                trades.append(
                    MarketTrade(
                        self.name, pair, asset, price, amount, price * amount,
                        row.get("side") or "unknown",
                        datetime.fromtimestamp(ts_s, tz=timezone.utc),
                        str(row.get("sequence") or row["time"]),
                    )
                )
            data = ob.json().get("data") or {}
            book = build_book(self.name, pair, asset, data.get("bids") or [], data.get("asks") or [], min(book_depth, 20))
            candles = []
            rows = list(cd.json().get("data") or [])[:candle_limit]
            rows.reverse()
            for row in rows:
                o, c, h, l = map(float, (row[1], row[2], row[3], row[4]))
                candles.append(
                    MarketCandle(
                        self.name, pair, asset, "1m",
                        datetime.fromtimestamp(int(row[0]), tz=timezone.utc),
                        o, h, l, c, float(row[5]), float(row[6]),
                    )
                )
            return VenueSnapshot(
                self.name, pair, asset, True, trades=trades, book=book, candles=candles,
                latency_ms=(time.perf_counter() - t0) * 1000,
            )
        except Exception as exc:
            return VenueSnapshot(self.name, pair, asset, False, error=str(exc), latency_ms=(time.perf_counter() - t0) * 1000)


class MexcMarketVenue:
    name = "mexc"
    base = "https://api.mexc.com/api/v3"

    async def fetch(self, asset: str, pair: str, trade_limit: int, book_depth: int, candle_limit: int) -> VenueSnapshot:
        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=HTTP_HEADERS) as client:
                tr = await client.get(f"{self.base}/trades", params={"symbol": pair, "limit": min(trade_limit, 1000)})
                ob = await client.get(f"{self.base}/depth", params={"symbol": pair, "limit": min(book_depth, 100)})
                cd = await client.get(f"{self.base}/klines", params={"symbol": pair, "interval": "1m", "limit": candle_limit})
            tr.raise_for_status()
            ob.raise_for_status()
            cd.raise_for_status()
            trades = []
            for row in tr.json()[-trade_limit:]:
                price, amount = float(row["price"]), float(row["qty"])
                side = "sell" if row.get("isBuyerMaker") else "buy"
                trades.append(
                    MarketTrade(
                        self.name, pair, asset, price, amount, price * amount, side,
                        datetime.fromtimestamp(int(row["time"]) / 1000, tz=timezone.utc),
                        str(row.get("id") or row["time"]),
                    )
                )
            depth = ob.json()
            book = build_book(self.name, pair, asset, depth.get("bids", []), depth.get("asks", []), book_depth)
            candles = []
            for row in cd.json():
                o, h, l, c = map(float, (row[1], row[2], row[3], row[4]))
                candles.append(
                    MarketCandle(
                        self.name, pair, asset, "1m",
                        datetime.fromtimestamp(int(row[0]) / 1000, tz=timezone.utc),
                        o, h, l, c, float(row[5]), float(row[7]),
                    )
                )
            return VenueSnapshot(
                self.name, pair, asset, True, trades=trades, book=book, candles=candles,
                latency_ms=(time.perf_counter() - t0) * 1000,
            )
        except Exception as exc:
            return VenueSnapshot(self.name, pair, asset, False, error=str(exc), latency_ms=(time.perf_counter() - t0) * 1000)


class BitfinexMarketVenue:
    name = "bitfinex"
    base = "https://api-pub.bitfinex.com/v2"

    async def fetch(self, asset: str, pair: str, trade_limit: int, book_depth: int, candle_limit: int) -> VenueSnapshot:
        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=HTTP_HEADERS) as client:
                tr = await client.get(f"{self.base}/trades/{pair}/hist", params={"limit": trade_limit})
                ob = await client.get(f"{self.base}/book/{pair}/P0", params={"len": min(book_depth, 25)})
                cd = await client.get(f"{self.base}/candles/trade:1m:{pair}/hist", params={"limit": candle_limit})
            tr.raise_for_status()
            ob.raise_for_status()
            cd.raise_for_status()
            trades = []
            for row in tr.json():
                amount = float(row[2])
                price = float(row[3])
                side = "buy" if amount > 0 else "sell"
                amt = abs(amount)
                trades.append(
                    MarketTrade(
                        self.name, pair, asset, price, amt, price * amt, side,
                        datetime.fromtimestamp(int(row[1]) / 1000, tz=timezone.utc),
                        str(row[0]),
                    )
                )
            bids_raw, asks_raw = [], []
            for row in ob.json():
                price, amount = float(row[0]), float(row[2])
                (bids_raw if amount > 0 else asks_raw).append([price, abs(amount)])
            book = build_book(self.name, pair, asset, bids_raw, asks_raw, book_depth)
            rows = list(cd.json())
            rows.reverse()
            candles = []
            for row in rows[-candle_limit:]:
                o, c, h, l = map(float, (row[1], row[2], row[3], row[4]))
                vol = float(row[5])
                candles.append(
                    MarketCandle(
                        self.name, pair, asset, "1m",
                        datetime.fromtimestamp(int(row[0]) / 1000, tz=timezone.utc),
                        o, h, l, c, vol, vol * c,
                    )
                )
            return VenueSnapshot(
                self.name, pair, asset, True, trades=trades, book=book, candles=candles,
                latency_ms=(time.perf_counter() - t0) * 1000,
            )
        except Exception as exc:
            return VenueSnapshot(self.name, pair, asset, False, error=str(exc), latency_ms=(time.perf_counter() - t0) * 1000)


class HtxMarketVenue:
    name = "htx"
    base = "https://api.htx.com"

    async def fetch(self, asset: str, pair: str, trade_limit: int, book_depth: int, candle_limit: int) -> VenueSnapshot:
        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=HTTP_HEADERS) as client:
                tr = await client.get(f"{self.base}/market/history/trade", params={"symbol": pair, "size": min(trade_limit, 2000)})
                ob = await client.get(f"{self.base}/market/depth", params={"symbol": pair, "type": "step0", "depth": min(book_depth, 20)})
                cd = await client.get(f"{self.base}/market/history/kline", params={"symbol": pair, "period": "1min", "size": candle_limit})
            for resp in (tr, ob, cd):
                resp.raise_for_status()
                if resp.json().get("status") != "ok":
                    raise RuntimeError(resp.json())
            trades = []
            for block in tr.json().get("data") or []:
                for row in block.get("data") or []:
                    price, amount = float(row["price"]), float(row["amount"])
                    trades.append(
                        MarketTrade(
                            self.name, pair, asset, price, amount, price * amount,
                            row.get("direction") or "unknown",
                            datetime.fromtimestamp(int(row["ts"]) / 1000, tz=timezone.utc),
                            str(row.get("trade-id") or row["ts"]),
                        )
                    )
            trades = trades[:trade_limit]
            tick = ob.json().get("tick") or {}
            book = build_book(self.name, pair, asset, tick.get("bids") or [], tick.get("asks") or [], book_depth)
            rows = list(cd.json().get("data") or [])
            rows.reverse()
            candles = []
            for row in rows[-candle_limit:]:
                o, c, h, l = float(row["open"]), float(row["close"]), float(row["high"]), float(row["low"])
                vol = float(row["amount"])
                quote = float(row.get("vol") or vol * c)
                candles.append(
                    MarketCandle(
                        self.name, pair, asset, "1m",
                        datetime.fromtimestamp(int(row["id"]), tz=timezone.utc),
                        o, h, l, c, vol, quote,
                    )
                )
            return VenueSnapshot(
                self.name, pair, asset, True, trades=trades, book=book, candles=candles,
                latency_ms=(time.perf_counter() - t0) * 1000,
            )
        except Exception as exc:
            return VenueSnapshot(self.name, pair, asset, False, error=str(exc), latency_ms=(time.perf_counter() - t0) * 1000)


VENUES = {
    "kraken": KrakenMarketVenue(),
    "kucoin": KucoinMarketVenue(),
    "mexc": MexcMarketVenue(),
    "bitfinex": BitfinexMarketVenue(),
    "htx": HtxMarketVenue(),
}
