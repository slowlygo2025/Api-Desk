# Api-Desk — RapidAPI Pricing (Opción A) — DECIDIDO
# Actualizar Studio Hub Listing con estos números.

## Posicionamiento
Whale-first multi-chain feed (threshold ~>$10M), classification, risk & impact.
No competir en precio con crypto-APIs genéricas a $9; anclar a Whale Alert Alerts (~$30)
sin el salto a Enterprise ($699).

## Packs RapidAPI

| Pack Hub | Precio | Requests / mes | Rate limit orientativo | Plan interno backend |
|----------|--------|----------------|------------------------|----------------------|
| BASIC (Free) | $0 | 1_000 | 30 req/hora | retail (cuota baja) |
| PRO | $29 | 50_000 | 600 req/hora | retail/pro soft |
| ULTRA | $79 | 250_000 | 2_000 req/hora | pro |
| MEGA | $199 | 1_000_000 | 6_000 req/hora | institutional soft |

Hard limit = sí (bloquear al superar el cupo del mes en RapidAPI).

## Features por pack (qué listar en Studio)

### BASIC ($0) y PRO ($29) — mismos endpoints; PRO = más cuota
- GET /v1/health
- GET /v1/ready
- GET /v1/chains
- GET /v1/whales
- GET /v1/whales/{id}
- GET /v1/whales/tx/{tx_hash}
- GET /v1/stats/overview
- GET /v1/entities/{address}

### ULTRA ($79) y MEGA ($199) — todo lo anterior +
- GET /v1/stats/timeseries
- GET /v1/market/assets
- GET /v1/market/analysis   (auxiliar CEX; no es whale)

### Nunca en el Hub (ningún pack)
- POST /v1/clients
- POST /v1/whales/ingest/run
- /v1/admin/*, /v1/ops/*, /v1/metrics
- /v1/alerts/*, /v1/workspaces/*
- WebSockets /v1/ws/*

## Auth backend (recomendado)
1. RapidAPI valida X-RapidAPI-Key del consumidor (cobro + cuota mes).
2. Gateway inyecta X-RapidAPI-Proxy-Secret (ya validado en R1).
3. Opcional: hidden header X-API-Key = una key interna por pack
   (rapid-free / rapid-pro / rapid-ultra / rapid-mega) para cuotas diarias propias.

## Copy corto para la ficha Hub (EN)
"Multi-chain whale transfer API (>$10M USD): live feed, entity labels,
risk score and impact estimate. Free tier to try. REST without the $699 jump."

## Copy límites (EN)
"BASIC: 1,000 req/mo. PRO: 50,000 req/mo. ULTRA: 250,000 req/mo + timeseries/market.
MEGA: 1,000,000 req/mo. Hard limits apply. Not a price/honeypot aggregator."

## Anclas competitivas
- vs Whale Alert: Free + REST desde $29; ellos ~$30 alerts o $699 enterprise
- vs ChainSight RapidAPI: nosotros whale-first; ellos $9 genérico (precios/honeypot/widgets)
