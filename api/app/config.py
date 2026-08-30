from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Api-Desk"
    app_env: str = "development"
    api_prefix: str = "/v1"
    secret_key: str = "change-me-in-production"
    # Producción: postgresql+asyncpg://... (Railway suele dar postgres://)
    database_url: str = "sqlite+aiosqlite:///./apidesk.db"

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> object:
        if not isinstance(value, str) or not value:
            return value
        url = value.strip()
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://") :]
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = "postgresql+asyncpg://" + url[len("postgresql://") :]
        # Railway Postgres exige TLS; asyncpg usa ssl=require
        if "+asyncpg" in url and "ssl=" not in url and "localhost" not in url and "127.0.0.1" not in url:
            url += ("&" if "?" in url else "?") + "ssl=require"
        return url
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = False

    whale_threshold_usd: float = 10_000_000
    # Umbrales por asset (override del global si > 0)
    threshold_btc_usd: float = 10_000_000
    threshold_eth_usd: float = 8_000_000
    threshold_stable_usd: float = 10_000_000
    threshold_alt_usd: float = 5_000_000

    default_plan: str = "retail"
    require_api_key: bool = False  # True automático si app_env=production
    allow_client_registration: bool = True  # False automático si app_env=production
    # Alta pública solo puede crear este plan (Pro/Institutional → admin)
    public_registration_plan: str = "retail"
    panel_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    ws_ticket_secret: str = ""
    ws_ticket_ttl_sec: int = 15

    # RapidAPI Gateway
    rapidapi_proxy_secret: str = ""
    # true = exige proxy secret en casi todas las rutas (deploy solo-Hub)
    rapidapi_require_proxy: bool = False
    # en production, si hay secret configurado, exigir proxy
    rapidapi_enforce_in_production: bool = True
    # si el request trae secret válido, solo permitir rutas whitelist Hub
    rapidapi_hub_only: bool = True

    worker_enabled: bool = True
    worker_whale_interval_sec: float = 45
    worker_market_interval_sec: float = 60
    worker_xmr_interval_sec: float = 60  # compat → market
    worker_catalog_interval_sec: float = 3600
    worker_backfill_blocks: int = 200
    worker_lag_alert_sec: float = 180

    # Señales de mercado auxiliares (no whales). Vacío = BTC,ETH,SOL,BNB,XMR
    market_assets: str = "BTC,ETH,SOL,BNB,XMR"
    market_venues: str = ""
    xmr_large_trade_usd: float = 25_000
    xmr_venues: str = ""

    alchemy_api_key: str = ""
    infura_api_key: str = ""
    ankr_api_key: str = ""
    mempool_base_url: str = "https://mempool.space/api"
    blockstream_base_url: str = "https://blockstream.info/api"
    trongrid_api_key: str = ""
    helius_api_key: str = ""
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"

    telegram_bot_token: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_from_email: str = "alerts@apidesk.local"

    rate_limit_retail: int = 60
    rate_limit_pro: int = 600
    rate_limit_institutional: int = 6000
    daily_quota_retail: int = 5_000
    daily_quota_pro: int = 100_000
    daily_quota_institutional: int = 2_000_000

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def effective_require_api_key(self) -> bool:
        return self.require_api_key or self.is_production

    @property
    def effective_allow_client_registration(self) -> bool:
        if self.is_production:
            return False
        return self.allow_client_registration


@lru_cache
def get_settings() -> Settings:
    return Settings()
