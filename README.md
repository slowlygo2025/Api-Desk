# Api-Desk — API + Panel Web

Monorepo: **whales on-chain** (producto principal) + panel Next.js con BFF seguro.

## Arranque rápido (desarrollo)

### 1. API

```bash
cd api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

### 2. Panel

```bash
cd web
copy .env.example .env.local
npm install
npm run dev
```

Panel: http://localhost:3000  
API docs: http://localhost:8000/docs

### Login

1. Abre http://localhost:3000/login
2. En dev: **Crear cuenta demo** → pega la key → Entrar
3. La API key queda en cookie HttpOnly vía BFF (no en localStorage)

## Docker (api + web + postgres + redis)

```bash
docker compose up --build
```

## Estructura

```
Api-Desk/
├── api/          FastAPI /v1
├── web/          Next.js 15 panel + BFF
└── docker-compose.yml
```

## Seguridad

- BFF proxy: `/api/proxy/v1/*` inyecta `X-API-Key` server-side
- WebSocket: ticket efímero vía `POST /v1/auth/ws-ticket`
- CORS: `PANEL_ORIGINS` en producción
