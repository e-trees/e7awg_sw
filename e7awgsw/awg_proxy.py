import logging
from typing import Final, TYPE_CHECKING, Tuple, Dict, List
from pydantic import conlist, Field, conint

from e7awgsw.hal import (
    AbstractFpgaReg,
    AbstractFpgaBitArrayReg,
    AbstractFpgaRegfileU32,
    AbstractFpgaProxy,
    AbstractFpgaIO,
    b_1bf_bool,
    p_1bf_bool,
)
from e7awgsw.common_proxy import E7ModuleVersion
from e7awgsw.feedback.udprw import UdpRw
import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)


class AwgMasterAwgBitmap16(AbstractFpgaBitArrayReg):
    NUM_AWGS: Final[int] = 16

    if TYPE_CHECKING:
        awgs: List[bool] = Field(default=[False] * NUM_AWGS)
    else:
        awgs: conlist(bool, min_length=NUM_AWGS, max_length=NUM_AWGS) = Field(default=[False] * NUM_AWGS)


    def _parse(self, v: np.uint32):
        u = int(v)  # Notes: for avoiding type check error
        for i in range(self.NUM_AWGS):
            self.awgs[i] = ((u & 0b1) == 0b1)
            u >>= 1

    def build(self) -> np.uint32:
        v: int = 0
        for i in range(self.NUM_AWGS-1, -1, -1):
            v <<= 1
            v |= 0b1 if self.awgs[i] else 0b0
        return np.uint32(v)

    def __getitem__(self, k: int) -> bool:
        return self.awgs[k]

    def __setitem__(self, k: int, v: bool) -> None:
        self.awgs[k] = v

    @classmethod
    def parse(cls, v: np.uint32) -> "AwgMasterAwgBitmap16":
        r = cls()
        r._parse(v)
        return r


class AwgCtrlCtrl(AbstractFpgaReg):
    reset: bool = Field(default=False)  # [0]
    prepare: bool = Field(default=False)  # [1]
    start: bool = Field(default=False)  # [2]
    terminate: bool = Field(default=False)  # [3]
    done_clr: bool = Field(default=False)  # [4]

    def _parse(self, v: np.uint32) -> None:
        self.reset = p_1bf_bool(v, 0)
        self.prepare = p_1bf_bool(v, 1)
        self.start = p_1bf_bool(v, 2)
        self.terminate = p_1bf_bool(v, 3)
        self.done_clr = p_1bf_bool(v, 4)

    def build(self) -> np.uint32:
        return (
                b_1bf_bool(self.reset, 0)
                | b_1bf_bool(self.prepare, 1)
                | b_1bf_bool(self.start, 2)
                | b_1bf_bool(self.terminate, 3)
                | b_1bf_bool(self.done_clr, 4)
        )

    @classmethod
    def parse(cls, v: np.uint32) -> "AwgCtrlCtrl":
        r = cls()
        r._parse(v)
        return r


class AwgCtrlStatus(AbstractFpgaReg):
    wakeup: bool = Field(default=False)  # [0]
    busy: bool = Field(default=False)  # [1]
    ready: bool = Field(default=False)  # [2]
    done: bool = Field(default=False)  # [3]

    def _parse(self, v: np.uint32) -> None:
        self.wakeup = p_1bf_bool(v, 0)
        self.busy = p_1bf_bool(v, 1)
        self.ready = p_1bf_bool(v, 2)
        self.done = p_1bf_bool(v, 3)

    def build(self) -> np.uint32:
        return (
                b_1bf_bool(self.wakeup, 0)
                | b_1bf_bool(self.busy, 1)
                | b_1bf_bool(self.ready, 2)
                | b_1bf_bool(self.done, 3)
        )

    @classmethod
    def parse(cls, v: np.uint32) -> "AwgCtrlStatus":
        r = cls()
        r._parse(v)
        return r


class AwgCtrlError(AbstractFpgaReg):
    read_err: bool = Field(default=False)  # [0]
    sample_shotage: bool = Field(default=False)  # [1]

    def _parse(self, v: np.uint32):
        self.read_err = p_1bf_bool(v, 0)
        self.sample_shotage = p_1bf_bool(v, 1)

    def build(self) -> np.uint32:
        return (
                b_1bf_bool(self.read_err, 0)
                | b_1bf_bool(self.sample_shotage, 1)
        )

    @classmethod
    def parse(cls, v: np.uint32) -> "AwgCtrlError":
        r = cls()
        r._parse(v)
        return r


class AwgChunkParameter(AbstractFpgaRegfileU32):
    if TYPE_CHECKING:
        wave_start_addr: int = Field(default=0)
        num_wave_words: int = Field(default=0)
        num_blank_words: int = Field(default=0)
        num_chunk_repeats: int = Field(default=0)
    else:
        wave_start_addr: conint(ge=0, le=0x1ffffffff) = Field(default=0)  # TODO: define it as a constant
        num_wave_words: conint(ge=0, le=0xffffffff) = Field(default=0)  # TODO: reconsider the maximum value
        num_blank_words: conint(ge=0, le=0xffffffff) = Field(default = 0)
        num_chunk_repeats: conint(ge=1, le=0xffffffff) = Field(default = 1)

    @classmethod
    def parse(cls, v: npt.NDArray[np.uint32]) -> "AwgChunkParameter":
        r = cls()
        r._parse(v)
        return r


class AwgWaveParameter(AbstractFpgaRegfileU32):
    if TYPE_CHECKING:
        num_wait_word: int = Field(default=0)
        num_seq_repeats: int = Field(default=1)
        num_chunks: int = Field(default=1)
        wave_block_interval: int = Field(default=1)
    else:
        num_wait_word: conint(ge=0, le=0xffffffff) = Field(default=0)
        num_seq_repeats: conint(ge=1, le=0xffffffff) = Field(default=1)
        num_chunks: conint(ge=1, le=16) = Field(default=1)
        wave_block_interval: conint(ge=1, le=0xffffffff) = Field(default=1)

    @classmethod
    def parse(cls, v: npt.NDArray[np.uint32]) -> "AwgWaveParameter":
        r = cls()
        r._parse(v)
        return r


class AwgProxy(AbstractFpgaProxy):
    REG_DECL: Dict[str, Tuple[int, type]] = {
        "ctrl": (0x0, AwgCtrlCtrl),
        "status": (0x4, AwgCtrlStatus),
        "error": (0x8, AwgCtrlError),
    }

    _CHUNK_PARAMETER_OFFSET: Final[Tuple[int, ...]] = tuple([a * 0x0010 + 0x0040 for a in range(16)])

    def __init__(self, base: int, wave_base: int, udprw: AbstractFpgaIO):
        super().__init__(base, udprw)
        self._wave_base = wave_base

    def get_wave_parameter(self) -> AwgWaveParameter:
        addr = self._wave_base
        v = self._udprw.read_u32_vector(addr, AwgWaveParameter.num_words())
        return AwgWaveParameter.parse(v)

    def set_wave_parameter(self, data: AwgWaveParameter) -> None:
        addr = self._wave_base
        self._udprw.write_u32_vector(addr, data.build())

    def get_chunk_parameter(self, chunk_idx: int) -> AwgChunkParameter:
        addr = self._wave_base + self._CHUNK_PARAMETER_OFFSET[chunk_idx]
        v = self._udprw.read_u32_vector(addr, AwgChunkParameter.num_words())
        return AwgChunkParameter.parse(v)

    def set_chunk_parameter(self, chunk_idx: int, data: AwgChunkParameter) -> None:
        addr = self._wave_base + self._CHUNK_PARAMETER_OFFSET[chunk_idx]
        self._udprw.write_u32_vector(addr, data.build())


class AwgMasterProxy(AbstractFpgaProxy):
    NUM_AWGS: Final[int] = 16
    AwgMasterAwgBitmap: Final[type] = AwgMasterAwgBitmap16
    assert hasattr(AwgMasterAwgBitmap, "NUM_AWGS") and NUM_AWGS == AwgMasterAwgBitmap.NUM_AWGS

    REG_DECL: Dict[str, Tuple[int, type]] = {
        "version": (0x00, E7ModuleVersion),
        "ctrl_target_sel": (0x4, AwgMasterAwgBitmap),
        "ctrl": (0x8, AwgCtrlCtrl),
        "wakeup_status": (0xC, AwgMasterAwgBitmap),
        "busy_status": (0x10, AwgMasterAwgBitmap),
        "ready_status": (0x14, AwgMasterAwgBitmap),
        "done_status": (0x18, AwgMasterAwgBitmap),
        "read_err": (0x1C, AwgMasterAwgBitmap),
        "sample_shortage_err": (0x20, AwgMasterAwgBitmap),
    }

    _CTRL_OFFSET: Final[Tuple[int, ...]] = tuple([a * 0x0080 + 0x0080 for a in range(NUM_AWGS)])
    _WAVE_PARAMETER_OFFSET: Final[Tuple[int, ...]] = tuple([a * 0x0400 + 0x1000 for a in range(NUM_AWGS)])

    def __init__(self, base: int, udprw: AbstractFpgaIO):
        super().__init__(base, udprw)
        self._awg_proxy : List[AwgProxy] = [
            AwgProxy(
                self._base + self._CTRL_OFFSET[idx],
                self._base + self._WAVE_PARAMETER_OFFSET[idx],
                self._udprw
            ) for idx in range(self.NUM_AWGS)
        ]

    def get_awg_proxy(self, awg_idx: int) -> AwgProxy:
        return self._awg_proxy[awg_idx]


if __name__ == '__main__':
    from e7awgsw.feedback.uplpacketbuffer import UplPacketMode

    udprw = UdpRw(
        ip_addr="10.1.0.42",
        port=16385,
        min_rw_size=4,
        bottom_address=0x4fff,
        wr_mode_id=UplPacketMode.AWG_REG_WRITE,
        rd_mode_id=UplPacketMode.AWG_REG_READ,
    )

    awg_master = AwgMasterProxy(0x0000, udprw)
