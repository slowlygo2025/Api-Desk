from app.data.exchange_catalog import catalog_stats, lookup_entity
from app.domain.enums import EntityType


def test_catalog_has_major_exchanges():
    stats = catalog_stats()
    assert stats["total"] >= 50
    assert "binance" in stats["by_label"]
    assert "coinbase" in stats["by_label"]
    assert "ethereum" in stats["by_chain"]


def test_lookup_binance_hot():
    hit = lookup_entity("ethereum", "0x28C6c06298d514Db089934071355E5743bf21d60")
    assert hit is not None
    label, et, conf = hit
    assert label == "binance"
    assert et == EntityType.EXCHANGE
    assert conf >= 0.9
