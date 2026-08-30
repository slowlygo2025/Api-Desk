# Railway — deploy Api-Desk API (R3)

Host elegido para el Hub RapidAPI. Solo la carpeta `api/` (el panel Next.js no va aquí).

## Estado cuenta

- Login OK en Railway
- Trial / créditos visibles (p. ej. 30 días o $5)
- Fair Use aceptada (API de datos whales ≠ crypto mining)
- Proyecto creado: **Api-Desk** (antes charismatic-mindfulness)  
  URL: https://railway.com/project/1f61e6c2-1ed8-4627-ad40-77e5ea442e18  
- **PostgreSQL Online** (+ volume)

## Bloqueo actual

El monorepo **aún no tiene git remote**. Railway prefiere GitHub. Opciones:

1. **Recomendada:** crear repo GitHub `Api-Desk` → deploy desde root con Dockerfile en `api/`
2. **Rápida:** proyecto vacío + Postgres + `railway up` desde `api/` (CLI)

## Pasos UI (proyecto vacío)

1. New project → **Empty Project** → nombre `Api-Desk`
2. **+ New** → **Database** → **PostgreSQL**
3. **+ New** → **GitHub Repo** (cuando exista) o deploy CLI
4. Root Directory / Dockerfile path: `api` (si monorepo)
5. Variables (servicio API):

```env
APP_ENV=production
API_PREFIX=/v1
REQUIRE_API_KEY=true
ALLOW_CLIENT_REGISTRATION=false
RAPIDAPI_PROXY_SECRET=<desde Studio Gateway>
RAPIDAPI_REQUIRE_PROXY=true
RAPIDAPI_ENFORCE_IN_PRODUCTION=true
RAPIDAPI_HUB_ONLY=true
SECRET_KEY=<generar>
WS_TICKET_SECRET=<generar>
DATABASE_URL=${{Postgres.DATABASE_URL}}
# Ajustar driver async si Railway da postgres:// → postgresql+asyncpg://
WORKER_ENABLED=true
ALCHEMY_API_KEY=
ANKR_API_KEY=
HELIUS_API_KEY=
TRONGRID_API_KEY=
```

6. Networking → **Generate Domain** → HTTPS `*.up.railway.app`
7. Pegar ese dominio en RapidAPI Studio → General → **Base URL**
8. Smoke: `GET https://TU-DOMINIO/v1/health` y `/v1/ready`

## Notas

- `DATABASE_URL` de Railway suele ser `postgres://...`; la app usa `postgresql+asyncpg://` — convertir en var o en código de arranque.
- No subir `.env` al repo (ya en `.gitignore`).
- Redis opcional; rate limit in-memory vale para 1 réplica.
