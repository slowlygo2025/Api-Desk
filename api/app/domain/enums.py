from enum import Enum


class Plan(str, Enum):
    RETAIL = "retail"
    PRO = "pro"
    INSTITUTIONAL = "institutional"


class Chain(str, Enum):
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    AVALANCHE = "avalanche"
    TRON = "tron"
    SOLANA = "solana"


class EntityType(str, Enum):
    EXCHANGE = "exchange"
    WALLET = "wallet"
    CONTRACT = "contract"
    MIXER = "mixer"
    BRIDGE = "bridge"
    OTC_DESK = "otc_desk"
    UNKNOWN = "unknown"


class FlowType(str, Enum):
    EXCHANGE_INFLOW = "exchange_inflow"
    EXCHANGE_OUTFLOW = "exchange_outflow"
    OTC = "otc"
    MINT = "mint"
    BURN = "burn"
    WALLET_TO_WALLET = "wallet_to_wallet"
    BRIDGE = "bridge"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AlertChannel(str, Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
