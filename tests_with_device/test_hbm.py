import time

import pytest
import logging

from e7awgsw.feedback.udpaccess import WaveRamAccess
from e7awgsw.feedback.uplpacketbuffer import UplPacketMode
from e7awgsw.feedback.udprw import UdpRw
from e7awgsw.hwparam import WAVE_RAM_PORT, AWG_REG_PORT

logger = logging.getLogger()


TEST_SETTINGS = [
    {
        "name": "staging-042",
        "ipaddr_wss": "10.1.0.42",
    }
]

@pytest.fixture(scope="session", params=TEST_SETTINGS)
def fixtures(request):
    #wra = WaveRamAccess(request.param["ipaddr_wss"], WAVE_RAM_PORT)
    wra = UdpRw(
        ip_addr=request.param["ipaddr_wss"],
        port=WAVE_RAM_PORT,
        min_rw_size=32,
        wr_mode_id=UplPacketMode.WAVE_RAM_WRITE,
        rd_mode_id=UplPacketMode.WAVE_RAM_READ,
        bottom_address=0x1_ffff_ffff,
        timeout=0.5,
    )
    return {
        "hbm_access": wra,
    }


@pytest.mark.parametrize(
    ("address", "size"),
    (
            (0x0_0000_0000, 0x100),
            (0x0_1000_1000, 0x600),
            (0x0_4100_0000, 0x10_0000),
            (0x1_4FFF_0000, 0x10_0000),
    )
)
def test_hbm_basic(address, size, fixtures):
    wra = fixtures["hbm_access"]
    data0 = bytes([x & 0xff for x in range(0, size)])
    wra.write(address, memoryview(data0))
    data1 = wra.read(address, size)
    assert data0 == data1


@pytest.mark.parametrize(
    ("address", "size"),
    (
            (0x0_1000_1004, 0x1),
            (0x0_1000_1008, 0x9),
            (0x0_1000_100c, 0x13),
            (0x0_1000_102c, 0x14),
            (0x0_1000_1050, 0x2f),
            (0x0_1000_1061, 0x600),
            (0x0_1FFF_FF81, 0xE5),
            (0x0_0000_000F, 0x5A0),  # original implementation causes timeout
    )
)
def test_hbm_unaligned(address, size, fixtures):
    wra = fixtures["hbm_access"]
    data0 = bytes([x & 0xff for x in range(0, size)])
    wra.write(address, memoryview(data0))
    data1 = wra.read(address, size)
    assert data0 == data1


@pytest.mark.parametrize(
    ("address", "size"),
    (
            (0x2_0000_0000, 0x100),
            (0x0_0000_0000, -1),
    )
)
def test_hbm_invalid_parameters(address, size, fixtures):
    wra = fixtures["hbm_access"]
    with pytest.raises(ValueError):
        wra.read(address, size)


@pytest.mark.parametrize(
    ("address", "size"),
    (
            (0x0_5100_0000, 0x100_0000),
            (0x0_6FFF_000F, 0x100_0000),
            (0x0_8000_0000, 0x400_0000),
    )
)
def test_hbm_perf(address, size, fixtures):
    wra = fixtures["hbm_access"]
    data0 = bytes([x & 0xff for x in range(0, size)])
    t0 = time.perf_counter()
    wra.write(address, memoryview(data0))
    t1 = time.perf_counter()
    data1 = wra.read(address, size)
    t2 = time.perf_counter()
    logger.info(f"write: {t1-t0}s, {size/(t1-t0):.0f}B/s")
    logger.info(f"read: {t2-t1}s, {size/(t2-t1):.0f}B/s")
    assert data0 == data1
