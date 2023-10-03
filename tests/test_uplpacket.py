import logging
import pytest

from e7awgsw.feedback.uplpacketbuffer import UplPacket, UplPacketBuffer, UplPacketMode

logger = logging.getLogger(__name__)

@pytest.mark.parametrize(
    ("mode", "address", "num_max_payload_len", "num_payload_len"),
    (
            (UplPacketMode.AWG_REG_WRITE, 0x1234567890, 128, 128),
            (UplPacketMode.SEQUENCER_CMD_WRITE, 0x0, 65536, 256),
    )
)
def test_nominal_write(mode, address, num_max_payload_len, num_payload_len):
    buf = UplPacketBuffer(num_max_payload_bytes=num_max_payload_len)
    buf.init(mode, address, num_payload_len)
    assert buf.has_payload()
    payload = buf.payload
    assert len(payload) == num_payload_len

    for i in range(num_payload_len):
        payload[i] = i & 0xff
    pkt = buf.serialize()
    assert len(pkt) == num_payload_len + 8  # size of the UPL packet header is 8

    copied_pkt = bytearray(pkt)  # emulating the network transfer
    parsed = UplPacket(copied_pkt)
    assert parsed.mode == mode
    assert parsed.address == address

    parsed_payload = parsed.payload
    assert len(parsed_payload) == num_payload_len
    assert payload == parsed_payload


@pytest.mark.parametrize(
    ("mode", "address", "num_max_payload_len", "num_payload_len"),
    (
            (UplPacketMode.AWG_REG_READ, 0x1234567890, 128, 128),
            (UplPacketMode.SEQUENCER_REG_READ, 0x0, 65536, 256),
    )
)
def test_nominal_read(mode, address, num_max_payload_len, num_payload_len):
    buf = UplPacketBuffer(num_max_payload_bytes=num_max_payload_len)
    buf.init(mode, address, num_payload_len)
    assert not buf.has_payload()

    pkt = buf.serialize()
    assert len(pkt) == 8  # size of the UPL packet header is 8

    copied_pkt = bytearray(pkt)  # emulating the network transfer
    parsed = UplPacket(copied_pkt)
    assert parsed.mode == mode
    assert parsed.address == address
    assert parsed.num_payload_bytes == num_payload_len
    assert not parsed.has_payload()


@pytest.mark.parametrize(
    ("mode", "address", "num_max_payload_len", "num_payload_len"),
    (
            (UplPacketMode.AWG_REG_WRITE, 0, 128, 129),
    )
)
def test_oversize(mode, address, num_max_payload_len, num_payload_len):
    buf = UplPacketBuffer(num_max_payload_bytes=num_max_payload_len)
    with pytest.raises(ValueError):
        buf.init(mode, address, num_payload_len)


@pytest.mark.parametrize(
    ("mode", "address", "num_max_payload_len", "num_payload_len"),
    (
            (UplPacketMode.AWG_REG_WRITE, 0, -1, 129),
    )
)
def test_invalid_size(mode, address, num_max_payload_len, num_payload_len):
    with pytest.raises(ValueError):
        logger.info(f"num_max_payload_len = {num_max_payload_len}")
        _ = UplPacketBuffer(num_max_payload_bytes=num_max_payload_len)


@pytest.mark.parametrize(
    ("mode", "address", "num_max_payload_len", "num_payload_len"),
    (
            (UplPacketMode.AWG_REG_READ, 0, 256, 128),
    )
)
def test_no_payload(mode, address, num_max_payload_len, num_payload_len):
    buf = UplPacketBuffer(num_max_payload_bytes=num_max_payload_len)
    buf.init(mode, address, num_payload_len)
    assert not buf.has_payload()
    with pytest.raises(ValueError):
        _ = buf.payload
