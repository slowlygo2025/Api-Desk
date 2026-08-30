from app.providers.ethereum import _hex_to_int, _topic_to_address


def test_topic_to_address():
    topic = "0x000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec7"
    assert _topic_to_address(topic) == "0xdac17f958d2ee523a2206206994597c13d831ec7"


def test_hex_to_int():
    assert _hex_to_int("0x10") == 16
    assert _hex_to_int("0x0") == 0
