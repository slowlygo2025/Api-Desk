from app.providers.chains import EVM_CHAINS, NON_EVM_CHAINS, SUPPORTED_CHAIN_IDS


def test_coverage_includes_major_chains():
    assert "ethereum" in EVM_CHAINS
    assert "bsc" in EVM_CHAINS
    assert "solana" in NON_EVM_CHAINS
    assert "bitcoin" in SUPPORTED_CHAIN_IDS
    assert len(SUPPORTED_CHAIN_IDS) >= 10
