"""Catálogo avanzado de entities (exchanges/bridges/contracts)."""

from __future__ import annotations

from app.domain.enums import EntityType

EXCHANGE_CATALOG: dict[tuple[str, str], tuple[str, EntityType, float]] = {
    ("arbitrum", "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b"): ("okx", EntityType.EXCHANGE, 0.92),
    ("arbitrum", "0xb38e8c17e38363af6ebdcb3dae12e0243582891d"): ("binance", EntityType.EXCHANGE, 0.95),
    ("arbitrum", "0xf977814e90da44bfa03b6295a0616a897441acec"): ("binance", EntityType.EXCHANGE, 0.95),
    ("avalanche", "0x28c6c06298d514db089934071355e5743bf21d60"): ("binance", EntityType.EXCHANGE, 0.9),
    ("avalanche", "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b"): ("okx", EntityType.EXCHANGE, 0.9),
    ("avalanche", "0xf89d7b9c864f517ac87ea0efd6ea98e27c6a3f30"): ("bybit", EntityType.EXCHANGE, 0.9),
    ("avalanche", "0xf977814e90da44bfa03b6295a0616a897441acec"): ("binance", EntityType.EXCHANGE, 0.92),
    ("base", "0x28c6c06298d514db089934071355e5743bf21d60"): ("binance", EntityType.EXCHANGE, 0.9),
    ("base", "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b"): ("okx", EntityType.EXCHANGE, 0.9),
    ("base", "0xf89d7b9c864f517ac87ea0efd6ea98e27c6a3f30"): ("bybit", EntityType.EXCHANGE, 0.9),
    ("base", "0xf977814e90da44bfa03b6295a0616a897441acec"): ("binance", EntityType.EXCHANGE, 0.92),
    ("bitcoin", "1Kr6QSydW9bFQG1mXiPNNu6WpJGmUa9i1g"): ("bitfinex", EntityType.EXCHANGE, 0.87),
    ("bitcoin", "1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s"): ("binance", EntityType.EXCHANGE, 0.92),
    ("bitcoin", "1P5ZEDWTKTFGxQjZphgWPQUpe554WKDfHQ"): ("binance", EntityType.EXCHANGE, 0.88),
    ("bitcoin", "3LYJfcfHPXYJreMsASk2jkn69LMEY6NoyE"): ("binance", EntityType.EXCHANGE, 0.9),
    ("bitcoin", "3M219KR5vEneNb47ewrPfWyb5jQ2DjxRP6"): ("binance", EntityType.EXCHANGE, 0.88),
    ("bitcoin", "bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97"): ("bitfinex", EntityType.EXCHANGE, 0.9),
    ("bitcoin", "bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h"): ("binance", EntityType.EXCHANGE, 0.9),
    ("bsc", "0x0d0707963952f2fba59dd06f2b425ace40b492fe"): ("gate", EntityType.EXCHANGE, 0.9),
    ("bsc", "0x3c783c21a0383057d128bae431894a5c19f9cf86"): ("binance", EntityType.EXCHANGE, 0.93),
    ("bsc", "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b"): ("okx", EntityType.EXCHANGE, 0.92),
    ("bsc", "0x8894e0a0c962cb723c1976a4421c95949be2d4e3"): ("binance", EntityType.EXCHANGE, 0.97),
    ("bsc", "0xdccf3b77da55107280bd460e98189540bfa88a65"): ("binance", EntityType.EXCHANGE, 0.92),
    ("bsc", "0xe2fc31f816a9b943fc7061c2a5efc42aabfa23d4"): ("binance", EntityType.EXCHANGE, 0.96),
    ("bsc", "0xf977814e90da44bfa03b6295a0616a897441acec"): ("binance", EntityType.EXCHANGE, 0.97),
    ("ethereum", "0x0681d8db095565fe8a346fa0277bffb100cd53e8"): ("binance", EntityType.EXCHANGE, 0.96),
    ("ethereum", "0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13"): ("kraken", EntityType.EXCHANGE, 0.97),
    ("ethereum", "0x0d0707963952f2fba59dd06f2b425ace40b492fe"): ("gate", EntityType.EXCHANGE, 0.95),
    ("ethereum", "0x1151314c646ce4e0efd76d1af4760ae66a9fe30f"): ("bitfinex", EntityType.EXCHANGE, 0.97),
    ("ethereum", "0x1522900b6dafac587d499a862861c0869be6e428"): ("bitstamp", EntityType.EXCHANGE, 0.95),
    ("ethereum", "0x1db92e2eebc8e0c075a02bea49a2935bcd2dfcf4"): ("bybit", EntityType.EXCHANGE, 0.95),
    ("ethereum", "0x21a31ee1afc51d62c97c44679c74addcab53e5b6"): ("binance", EntityType.EXCHANGE, 0.98),
    ("ethereum", "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0"): ("kraken", EntityType.EXCHANGE, 0.96),
    ("ethereum", "0x28c6c06298d514db089934071355e5743bf21d60"): ("binance", EntityType.EXCHANGE, 0.98),
    ("ethereum", "0x2910543af39aba0cd09dbb2d50200b3e800a63d2"): ("kraken", EntityType.EXCHANGE, 0.97),
    ("ethereum", "0x2faf487a4414fe77e2327f0bf4ae2a264a776ad2"): ("ftx_estate", EntityType.EXCHANGE, 0.9),
    ("ethereum", "0x3154cf16ccdb4c6d922629664174b904d80f2c35"): ("base_bridge", EntityType.BRIDGE, 0.96),
    ("ethereum", "0x3cd751e6b0078be393132286c442345e5dc49699"): ("coinbase", EntityType.EXCHANGE, 0.97),
    ("ethereum", "0x3ee18b2214aff97000d974cf647e7c347e8fa585"): ("wormhole_bridge", EntityType.BRIDGE, 0.93),
    ("ethereum", "0x40b38765696e3d74d13a65c63c7cbe130e9d0b18"): ("robinhood", EntityType.EXCHANGE, 0.94),
    ("ethereum", "0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbd7"): ("polygon_bridge", EntityType.BRIDGE, 0.97),
    ("ethereum", "0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503"): ("binance", EntityType.EXCHANGE, 0.96),
    ("ethereum", "0x4dbd4fc535ac27206064b68ffcf827b0a60bab3f"): ("arbitrum_inbox", EntityType.BRIDGE, 0.92),
    ("ethereum", "0x4e9a414185df6b9657e0d6a86a64e9a1b6e1c0e0"): ("binance", EntityType.EXCHANGE, 0.9),
    ("ethereum", "0x503828976d22510aad0201ac7ec88293211d23da"): ("coinbase", EntityType.EXCHANGE, 0.98),
    ("ethereum", "0x5427fefa711eff984124bfbb1ab6fbf5e3bd62f0"): ("celer_bridge", EntityType.BRIDGE, 0.9),
    ("ethereum", "0x55fe002aeff02e8211623d97c2eb0111b6b8c8e0"): ("circle", EntityType.CONTRACT, 0.9),
    ("ethereum", "0x56eddb7aa87536c09ccc2793473599fd21a8b4f2"): ("binance", EntityType.EXCHANGE, 0.98),
    ("ethereum", "0x5754284f345afc66a98fbb0a0afe71e0f007b949"): ("tether_treasury", EntityType.CONTRACT, 0.98),
    ("ethereum", "0x5a52e96bacdabb82fd05763e253f94556d3c0a3e"): ("binance", EntityType.EXCHANGE, 0.97),
    ("ethereum", "0x5f65f7b609678448494de4c87521cdf6cef1e932"): ("gemini", EntityType.EXCHANGE, 0.92),
    ("ethereum", "0x6262998ced04146fa42253a5c0af90ca02dfd2bc"): ("crypto.com", EntityType.EXCHANGE, 0.96),
    ("ethereum", "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b"): ("okx", EntityType.EXCHANGE, 0.97),
    ("ethereum", "0x71660c4005ba85c37ccec55d0c4493e66fe775d3"): ("coinbase", EntityType.EXCHANGE, 0.98),
    ("ethereum", "0x72a53cdbbcc1b9efa39c834a540550e23463aacb"): ("kucoin", EntityType.EXCHANGE, 0.93),
    ("ethereum", "0x742d35cc6634c0532925a3b844bc454e4438f44e"): ("bitfinex", EntityType.EXCHANGE, 0.94),
    ("ethereum", "0x8315177ab297ba92a06054ce80a67ed4dbd7ed3a"): ("arbitrum_bridge", EntityType.BRIDGE, 0.92),
    ("ethereum", "0x8484ef722627bf18ca5ae6bcf031cdd998d974b0"): ("wormhole_bridge", EntityType.BRIDGE, 0.93),
    ("ethereum", "0x876eabf441b2ee5b5b0554fd502a8e0600950cfa"): ("bitfinex", EntityType.EXCHANGE, 0.95),
    ("ethereum", "0x8f22f2063d253846b53609231ed80fa571bc0c8f"): ("binance", EntityType.EXCHANGE, 0.94),
    ("ethereum", "0x9696f59e4d72e237be84ffd425dcad154bf96976"): ("binance", EntityType.EXCHANGE, 0.98),
    ("ethereum", "0x98ec059dc3adfbdd63429454aeb0c990fba4a128"): ("okx", EntityType.EXCHANGE, 0.93),
    ("ethereum", "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1"): ("optimism_bridge", EntityType.BRIDGE, 0.97),
    ("ethereum", "0xa090e606e30bd747d4e6245a1517ebe830b27185"): ("crypto.com", EntityType.EXCHANGE, 0.93),
    ("ethereum", "0xa3a7b6f88361f48403514059f1f16c8e78d60eec"): ("arbitrum_bridge", EntityType.BRIDGE, 0.97),
    ("ethereum", "0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43"): ("coinbase", EntityType.EXCHANGE, 0.97),
    ("ethereum", "0xb5d85cbf7cb3ee0d56b3bb207d5fc4b82f43f511"): ("coinbase", EntityType.EXCHANGE, 0.97),
    ("ethereum", "0xbe0eb53f46cd790cd13851f5c6f5b2e0f8f1c1b0"): ("binance", EntityType.EXCHANGE, 0.97),
    ("ethereum", "0xcffad3200574698b78f32232aa9d63eabd290703"): ("crypto.com", EntityType.EXCHANGE, 0.94),
    ("ethereum", "0xd24400ae8bfebb99e4380f2f5a4a779c3ada5f94"): ("gemini", EntityType.EXCHANGE, 0.96),
    ("ethereum", "0xddfaba61acdd45349c3217757449d477122401db"): ("coinbase", EntityType.EXCHANGE, 0.97),
    ("ethereum", "0xdfd5293d8e347dfe59e90efd55b2956a1343963d"): ("binance", EntityType.EXCHANGE, 0.98),
    ("ethereum", "0xe853c56864a2ebe4576a807d124608a7e95ef210"): ("kraken", EntityType.EXCHANGE, 0.96),
    ("ethereum", "0xe9172daf64b05b26eb18f07ac8d6d723acb48f99"): ("okx", EntityType.EXCHANGE, 0.92),
    ("ethereum", "0xf89d7b9c864f517ac87ea0efd6ea98e27c6a3f30"): ("bybit", EntityType.EXCHANGE, 0.97),
    ("ethereum", "0xf977814e90da44bfa03b6295a0616a897441acec"): ("binance", EntityType.EXCHANGE, 0.98),
    ("optimism", "0x28c6c06298d514db089934071355e5743bf21d60"): ("binance", EntityType.EXCHANGE, 0.9),
    ("optimism", "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b"): ("okx", EntityType.EXCHANGE, 0.9),
    ("optimism", "0xf89d7b9c864f517ac87ea0efd6ea98e27c6a3f30"): ("bybit", EntityType.EXCHANGE, 0.9),
    ("optimism", "0xf977814e90da44bfa03b6295a0616a897441acec"): ("binance", EntityType.EXCHANGE, 0.92),
    ("polygon", "0x28c6c06298d514db089934071355e5743bf21d60"): ("binance", EntityType.EXCHANGE, 0.9),
    ("polygon", "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b"): ("okx", EntityType.EXCHANGE, 0.9),
    ("polygon", "0xf89d7b9c864f517ac87ea0efd6ea98e27c6a3f30"): ("bybit", EntityType.EXCHANGE, 0.9),
    ("polygon", "0xf977814e90da44bfa03b6295a0616a897441acec"): ("binance", EntityType.EXCHANGE, 0.92),
    ("solana", "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"): ("raydium", EntityType.EXCHANGE, 0.9),
    ("solana", "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"): ("binance", EntityType.EXCHANGE, 0.88),
    ("tron", "TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf"): ("binance", EntityType.EXCHANGE, 0.95),
    ("tron", "TJCo98aj77zPrwH9fn3ZbYNhdgmx4i9qkf"): ("binance", EntityType.EXCHANGE, 0.94),
    ("tron", "TNaRAoLUyYEV2uF7GUrzSjRQTU8v5ZJ5VX"): ("binance", EntityType.EXCHANGE, 0.93),
    ("tron", "TQEuSEVRk1PpdQVzKtvZjT9tWgtvuN1s7"): ("binance", EntityType.EXCHANGE, 0.94),
    # DeFi / protocol treasuries
    ("ethereum", "0x7a250d5630b4cf539739df2c5dacb4c659f2488d"): ("uniswap_v2_router", EntityType.CONTRACT, 0.95),
    ("ethereum", "0x68b3465833fb72a70dcdca989936e6c4903e0a0b"): ("uniswap_v3_router", EntityType.CONTRACT, 0.95),
    ("ethereum", "0x1111111254eeb25477b68fb85ed929f73"): ("1inch_router", EntityType.CONTRACT, 0.92),
    ("ethereum", "0xae78736cd156f8bd6865a75540d270862df25d10b"): ("lido_steth", EntityType.CONTRACT, 0.94),
    ("ethereum", "0xae7ab96520de3a18e5e111b5eaab095312d7fe84"): ("lido_steth_token", EntityType.CONTRACT, 0.94),
    ("ethereum", "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0"): ("wsteth", EntityType.CONTRACT, 0.93),
    ("ethereum", "0xbe9895146f7af43049ca1c1ae358b0541ea49704"): ("coinbase_cbeth", EntityType.CONTRACT, 0.93),
    ("ethereum", "0xae2fc483527b8ef99eb5d9b44875f005ba1fae13"): ("jupiter_treasury", EntityType.CONTRACT, 0.85),
    ("ethereum", "0x28aa13f7217df793c52a8773e4e5f8306f660340"): ("aave_treasury", EntityType.CONTRACT, 0.91),
    ("ethereum", "0x464c71f6c08214e1310b1e1956b5402aebd62ed8"): ("aave_collector", EntityType.CONTRACT, 0.90),
    ("ethereum", "0xba12222222228d8ba445958a75a0704d566bf2c8"): ("balancer_vault", EntityType.CONTRACT, 0.94),
    ("ethereum", "0xc011a73ee8576fb46f5e1c5751ca3b9fe0af2a0f"): ("synthetix_proxy", EntityType.CONTRACT, 0.90),
    ("ethereum", "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"): ("aave_v3_pool", EntityType.CONTRACT, 0.95),
    ("ethereum", "0x3d9819210a31b4961b30ef54b2fed5b9b6a352b2"): ("compound_gov", EntityType.CONTRACT, 0.88),
    ("ethereum", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"): ("weth", EntityType.CONTRACT, 0.98),
    ("ethereum", "0xdac17f958d2ee523a2206206994597c13d831ec7"): ("tether_usdt", EntityType.CONTRACT, 0.99),
    ("ethereum", "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"): ("circle_usdc", EntityType.CONTRACT, 0.99),
    ("ethereum", "0x6b175474e89094c44da98b954eedeac495271d0f"): ("maker_dai", EntityType.CONTRACT, 0.98),
    # Mixers / privacy (risk-relevant)
    ("ethereum", "0x8589427373d6d587e39065c5462733250b830004"): ("tornado_cash", EntityType.CONTRACT, 0.97),
    ("ethereum", "0xd90e2f925da726b50c4ed8b0bb27a92d51c66393"): ("tornado_cash", EntityType.CONTRACT, 0.97),
    # Additional L2 hot wallets
    ("arbitrum", "0x489ee077994b6658eafa855c308275ead8097c4a"): ("gmx_treasury", EntityType.CONTRACT, 0.88),
    ("base", "0x4200000000000000000000000000000000000006"): ("weth_base", EntityType.CONTRACT, 0.95),
    ("solana", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"): ("circle_usdc", EntityType.CONTRACT, 0.96),
    ("solana", "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"): ("tether_usdt", EntityType.CONTRACT, 0.96),
}


def normalize_address(chain: str, address: str) -> str:
    chain = chain.lower()
    addr = address.strip()
    if chain in {"ethereum", "bsc", "polygon", "arbitrum", "optimism", "base", "avalanche"}:
        return addr.lower()
    return addr


def lookup_entity(chain: str, address: str) -> tuple[str, EntityType, float] | None:
    chain_l = chain.lower()
    addr = normalize_address(chain, address)
    hit = EXCHANGE_CATALOG.get((chain_l, addr))
    if hit:
        return hit
    if chain_l == "bitcoin":
        return EXCHANGE_CATALOG.get((chain_l, address)) or EXCHANGE_CATALOG.get((chain_l, address.lower()))
    if chain_l == "solana":
        return EXCHANGE_CATALOG.get((chain_l, address))
    return None


def catalog_entries() -> list[dict]:
    return [
        {
            "chain": chain,
            "address": address,
            "label": label,
            "entity_type": et.value,
            "confidence": conf,
        }
        for (chain, address), (label, et, conf) in EXCHANGE_CATALOG.items()
    ]


def catalog_stats() -> dict:
    by_label: dict[str, int] = {}
    by_chain: dict[str, int] = {}
    for (chain, _), (label, _, _) in EXCHANGE_CATALOG.items():
        by_label[label] = by_label.get(label, 0) + 1
        by_chain[chain] = by_chain.get(chain, 0) + 1
    return {"total": len(EXCHANGE_CATALOG), "by_label": by_label, "by_chain": by_chain}
