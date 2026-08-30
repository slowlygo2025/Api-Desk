# Plan de desarrollo API — versión completa-final
# (sin fases ni fechas; todo el producto API en un solo alcance)

## Producto (alineación)

1. **Principal:** whales on-chain multi-chain (BTC/ETH/stables/L2/Solana…) + clasificación/riesgo/impacto/alertas.
2. **Auxiliar:** señales de mercado CEX multi-asset (`/v1/market`) — BTC, ETH, SOL, BNB, XMR.
   XMR es un asset más (opaco on-chain), no el centro del producto.
   Compat: `/v1/xmr/*` redirige lógica a `asset=XMR`.

### Market signals

```http
GET /v1/market/assets
GET /v1/market/snapshot?asset=BTC
GET /v1/market/analysis?asset=ETH
GET /v1/market/signals?asset=SOL
```

---

Api-Desk API detecta transferencias cripto de gran volumen, las clasifica (exchange/OTC/mint-burn/bridge),
estima riesgo, predice impacto en precio, expone historial/stats, alertas y tiempo real.
Diseñada para panel web + RapidAPI + clientes institucionales sobre el mismo contrato `/v1`.

Umbral por defecto: **> $10M USD** (configurable).

---

## Alcance completo-final (todo incluido)

| Módulo | Qué incluye |
|--------|-------------|
| Multi-provider nodos | **Datos reales**: ETH (USDT/USDC/ETH), BTC outputs grandes, Tron USDT; failover sin mocks |
| Valoración USD | CoinGecko + caché + fallback |
| Detección / ingest | Filtro umbral, dedup `chain+tx+log_index`, persistencia |
| Clasificación | Entidades + flow_type contextual |
| Riesgo | Motor de reglas calibrable → score/level/factors |
| Impacto | Baseline predictivo `impact.score/horizon/confidence` |
| HTTP API | whales, stats, entities, clients, alerts |
| Auth & planes | API keys retail / pro / institutional + rate limits |
| Tiempo real | WebSocket `/v1/ws/whales` + webhooks HMAC |
| Alertas | Reglas por usuario, email/Telegram/webhook |
| Histórico | Listado con filtros + cursor |
| Observabilidad | `/health`, `/ready`, provider health |

---

## Stack

- **FastAPI** + Pydantic v2
- **SQLAlchemy async** (SQLite dev / Postgres prod)
- **Redis** (opcional; docker-compose listo)
- **httpx** para RPC/APIs externas

---

## Arranque rápido

```bash
cd api
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Docs interactivas: http://localhost:8000/docs

### Ciclo de detección (desarrollo)

```http
POST /v1/whales/ingest/run
```

Luego:

```http
GET /v1/whales
GET /v1/stats/overview
```

### Cliente + alertas

```http
POST /v1/clients
{ "name": "demo", "plan": "pro", "webhook_url": "https://example.com/hook" }

POST /v1/alerts/rules
Header: X-API-Key: <key>
```

En `development` los GET de whales/stats funcionan sin API key.

---

## Contrato JSON (objeto whale)

```json
{
  "id": "...",
  "tx_hash": "...",
  "asset": "USDT",
  "chain": "ethereum",
  "amount": 25000000,
  "amount_usd": 25000000,
  "from": { "address": "...", "label": "...", "entity_type": "..." },
  "to": { "address": "...", "label": "...", "entity_type": "..." },
  "flow_type": "exchange_inflow",
  "risk": { "score": 0.42, "level": "medium", "factors": ["..."] },
  "impact": { "score": 0.51, "horizon": "1h", "confidence": 0.62, "details": {} },
  "detected_at": "...",
  "block_time": "...",
  "provider": "eth_alchemy"
}
```

---

## Endpoints

| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/v1/chains` | Cobertura multi-chain |
| GET | `/v1/ready` | DB + providers |
| GET | `/v1/whales` | Listado filtrable |
| GET | `/v1/whales/{id}` | Detalle |
| GET | `/v1/whales/tx/{hash}` | Por transacción |
| POST | `/v1/whales/ingest/run` | Un ciclo ingest completo |
| GET | `/v1/stats/overview` | KPIs |
| GET | `/v1/entities/{address}` | Etiqueta / tipo |
| POST | `/v1/clients` | Alta cliente + API key |
| POST | `/v1/alerts/rules` | Crear regla |
| GET | `/v1/alerts/rules` | Listar reglas |
| DELETE | `/v1/alerts/rules/{id}` | Borrar regla |
| GET | `/v1/worker` | Estado worker continuo |
| GET | `/v1/entities/catalog/stats` | Catálogo exchanges |
| GET | `/v1/market/assets` | Assets auxiliares CEX |
| GET | `/v1/market/analysis` | Señales multi-asset (`?asset=BTC`) |
| WS | `/v1/ws/feed` | whale.detected + market.analysis + heartbeat |
| WS | `/v1/ws/whales` | Alias del feed |

---

## Estructura del código

```
api/
  app/
    main.py
    config.py
    domain/enums.py
    db/models.py, session.py
    providers/          # adapters + router failover
    services/           # pricing, classify, risk, impact, ingest, alerts, auth
    schemas/
    api/v1/             # HTTP + WS
  tests/
  docker-compose.yml    # Postgres + Redis
  requirements.txt
```

---

## Pipeline interno (único)

```
providers.fetch_all
  → price.to_usd
  → threshold filter
  → classify (flow_type + labels)
  → risk.assess
  → impact.predict
  → persist whale_events
  → alert.evaluate_and_dispatch
  → (WS broadcast)
```

---

## Monetización (en API)

- **retail**: rate limit bajo, whales + stats
- **pro**: histórico amplio, alertas, clasificación completa
- **institutional**: límites altos, webhook dedicado, soporte de scopes

Campos y módulos ya existen; el billing externo solo emite/revoca API keys.

---

## Producción

1. `DATABASE_URL` → Postgres (`docker compose up -d`)
2. API keys reales de Alchemy/Infura/etc. en `.env`
3. Sustituir `create_all` por migraciones Alembic
4. Worker periódico llamando `IngestService.run_once` + broadcast WS
5. Completar decode `eth_getLogs` / outputs BTC grandes en cada adapter
6. Ampliar catálogo `entities` y calibrar pesos de risk/impact con backtest

---

## Tests

```bash
cd api
pytest -q
```

---

## Cobertura on-chain (real, multi-chain)

| Cadena | Assets | Fuente |
|--------|--------|--------|
| Bitcoin | BTC | Mempool / Blockstream |
| Ethereum | ETH, USDT, USDC | Alchemy o RPC público |
| BNB Smart Chain | BNB, USDT, USDC | RPC público |
| Polygon | POL, USDT, USDC | RPC público |
| Arbitrum | ETH, USDT, USDC | RPC público |
| Optimism | ETH, USDT, USDC | RPC público |
| Base | ETH, USDT, USDC | RPC público |
| Avalanche C | AVAX, USDT, USDC | RPC público |
| Tron | USDT | TronGrid |
| Solana | SOL, USDT, USDC | RPC / Helius |
| (auxiliar CEX) | BTC, ETH, SOL, BNB, XMR | Kraken/KuCoin/HTX/Bitfinex/MEXC |

### Señales de mercado (auxiliar, multi-asset)

Microestructura CEX real: trades + order book + OHLC + dispersión cross-exchange.
No sustituye whales on-chain; complementa majors (XMR incluido como caso opaco).

```http
GET /v1/market/assets
GET /v1/market/snapshot?asset=BTC
GET /v1/market/analysis?asset=ETH
GET /v1/market/signals?asset=SOL
```

Compat legado: `/v1/xmr/*` → mismo motor con `asset=XMR`.
Si ningún venue responde → `503` (no inventa datos).

Ampliar cadenas on-chain = entrada en `app/providers/chains.py`. Ampliar assets CEX = `app/providers/market/registry.py`.
