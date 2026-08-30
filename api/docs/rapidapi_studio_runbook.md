# RapidAPI Studio — guía de alta (Opción A)

Studio corre en un **iframe**: el agente no puede hacer clic dentro.
Sigue estos pasos; cuando termines cada bloque, avisa y revisamos juntos.

## Bloqueantes reales

1. **URL pública HTTPS** (R3) — RapidAPI no puede llamar a `127.0.0.1`.
   Hasta tenerla, deja el proyecto en **draft / private** con host placeholder.
2. Archivo listo para importar: `api/docs/openapi_rapidapi_hub.json`

## Paso 1 — Crear proyecto

1. En Rapid Studio → **+ Add API Project**
2. Nombre: `Api-Desk Whales`
3. Descripción corta (EN):
   `Multi-chain whale transfers (>$10M), classification, risk & impact. Free tier to try.`
4. Categoría: **Cryptocurrency** / Blockchain
5. Base URL: pegar dominio Railway HTTPS cuando R3 esté listo (`*.up.railway.app`)

Host R3 elegido: **Railway** — ver `api/docs/railway_deploy_runbook.md`

## Paso 2 — Importar OpenAPI

1. Hub Listing / Definitions / Import OpenAPI
2. Sube `api/docs/openapi_rapidapi_hub.json`
3. Verifica que solo aparecen los GET de la whitelist
4. (Opcional) Renombrar en Studio → Edit → Name (display):

| operationId actual (auto) | Name en Hub |
|---------------------------|-------------|
| `health_v1_health_get` | Health |
| `ready_v1_ready_get` | Ready |
| `list_chains_v1_chains_get` | List chains |
| `list_whales_v1_whales_get` | List whales |
| `get_by_tx_v1_whales_tx__tx_hash__get` | Get whale by tx |
| `get_whale_v1_whales__whale_id__get` | Get whale by id |
| `stats_overview_v1_stats_overview_get` | Stats overview |
| `stats_timeseries_v1_stats_timeseries_get` | Stats timeseries |
| `get_entity_v1_entities__address__get` | Get entity |
| `market_assets_v1_market_assets_get` | Market assets |
| `market_analysis_v1_market_analysis_get` | Market analysis |

El OpenAPI del repo ya usa `operationId` cortos (`listWhales`, etc.) para futuros imports.

## Paso 3 — Gateway / seguridad

1. Hub Listing → **Gateway**
2. Copia **X-RapidAPI-Proxy-Secret**
3. Guárdalo en el servidor (R3) como `RAPIDAPI_PROXY_SECRET=...`
4. (Opcional) Secret Headers: `X-API-Key` = key interna del pack

## Paso 4 — Pricing (Opción A)

| Plan Studio | Precio | Requests/mes | Hard limit |
|-------------|--------|--------------|------------|
| BASIC | $0 | 1,000 | Yes |
| PRO | $29 | 50,000 | Yes |
| ULTRA | $79 | 250,000 | Yes |
| MEGA | $199 | 1,000,000 | Yes |

Endpoints por plan (en Studio restringe qué ve cada plan):

- **BASIC + PRO:** health, ready, chains, whales, whales/{id}, whales/tx/{hash}, stats/overview, entities/{address}
- **ULTRA + MEGA:** lo anterior + stats/timeseries, market/assets, market/analysis

## Paso 5 — Visibilidad

- Dejar **Private / Draft** hasta smoke con URL HTTPS real
- NO poner Active hasta R3 + 20 llamadas playground OK

## Paso 6 — Después de R3

1. Actualizar Base URL al HTTPS real
2. `APP_ENV=production` + `RAPIDAPI_PROXY_SECRET` + `RAPIDAPI_REQUIRE_PROXY=true`
3. Probar playground Free y Pro
4. Entonces Active
