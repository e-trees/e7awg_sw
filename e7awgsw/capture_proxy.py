import logging
from typing import Final, TYPE_CHECKING, Tuple, Dict, List, Sequence
from pydantic import conlist, Field, conint

from e7awgsw.hal import (
    AbstractFpgaReg,
    AbstractFpgaBitArrayReg,
    AbstractFpgaRegfileU32,
    AbstractFpgaRegfileI32,
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


_MAX_SUM_SECTION_LEN: Final[int] = 0xFFFF_FFFE
_MAX_POST_BLANK_LEN: Final[int] = 0xFFFF_FFFF
_NUM_SUM_SECTIONS: Final[int] = 4096  # come from hwparam.MAX_INTEG_VEC_ELEMS


class DspSumSectionConfig(AbstractFpgaRegfileU32):
    if TYPE_CHECKING:
        num_sum_section_words: int = Field(default=0)
        num_post_blank_words: int = Field(default=0)
    else:
        num_sum_section_words: conint(ge=0, le=_MAX_SUM_SECTION_LEN) = Field(default=0)
        num_post_blank_words: conint(ge=0, le=_MAX_SUM_SECTION_LEN) = Field(default=0)

    def __repr__(self):
        if self.is_effective():
            return f"DspSumSec(slen={self.num_sum_section_words}, blen={self.num_post_blank_words})"
        else:
            return f"DspSumSec(disabled)"

    def is_effective(self) -> bool:
        return (self.num_sum_section_words >= 1 and self.num_post_blank_words >= 1)

    def clear(self) -> None:
        self.num_sum_section_words = 0
        self.num_post_blank_words = 0

    def _parse(self, v: npt.NDArray[np.uint32]):
        raise NotImplementedError

    def build(self) -> npt.NDArray[np.uint32]:
        raise NotImplementedError


class DspComplexFirConfig(AbstractFpgaRegfileI32):
    _MIN_COEFF: Final[int] = -32768
    _MAX_COEFF: Final[int] = 32767  # XXX: official document is wrong

    if TYPE_CHECKING:
        real: List[int] = Field(default=[0, 0, 0, 0, 0, 0, 0, 0])
        imag: List[int] = Field(default=[0, 0, 0, 0, 0, 0, 0, 0])
    else:
        real: conlist(conint(ge=_MIN_COEFF, le=_MAX_COEFF), min_length=8, max_length=8) = Field(default=[0, 0, 0, 0, 0, 0, 0, 0])
        imag: conlist(conint(ge=_MIN_COEFF, le=_MAX_COEFF), min_length=8, max_length=8) = Field(default=[0, 0, 0, 0, 0, 0, 0, 0])

    def _validate_coeff(self, v: int) -> bool:
        return self._MIN_COEFF <= v <= self._MAX_COEFF

    def __getitem__(self, item: int) -> Tuple[int, int]:
        return self.real[item], self.imag[item]

    def __setitem__(self, item: int, value: Tuple[int, int]):
        if not self._validate_coeff(value[0]):
            raise ValueError("invalid filter coefficient")
        if not self._validate_coeff(value[1]):
            raise ValueError("invalid filter coefficient")
        self.real[item], self.imag[item] = value

    def _parse(self, v: npt.NDArray[np.int32]) -> None:
        if len(v) != 16:
            raise ValueError("invalid data for DspComplexFirConfig")
        for i in range(8):
            self.real[i], self.imag[i] = v[i], v[i+8]

    def build(self) -> npt.NDArray[np.int32]:
        v = np.zeros(16, dtype=np.int32)
        for i in range(8):
            if not (self._validate_coeff(self.real[i]) and self._validate_coeff(self.imag[i])):
                raise ValueError("invalid coefficient, cannot pass to the device")
            v[i] = self.real[i]
            v[i+8] = self.imag[i]
        return v

    @classmethod
    def parse(cls, v: npt.NDArray[np.int32]) -> "DspComplexFirConfig":
        r = cls()
        r._parse(v)
        return r


class DspCtrlEnable(AbstractFpgaReg):
    complex_fir_en: bool = Field(default=False)  # [0]
    decimation_en: bool = Field(default=False)  # [1]
    real_fir_en: bool = Field(default=False)  # [2]
    window_en: bool = Field(default=False)  # [3]
    sum_en: bool = Field(default=False)  # [4]
    integration_en: bool = Field(default=False)  # [5]
    classification_en: bool = Field(default=False)  # [6]

    def _parse(self, v: np.uint32) -> None:
        self.complex_fir_en = p_1bf_bool(v, 0)
        self.decimation_en = p_1bf_bool(v, 1)
        self.real_fir_en = p_1bf_bool(v, 2)
        self.window_en = p_1bf_bool(v, 3)
        self.sum_en = p_1bf_bool(v, 4)
        self.integration_en = p_1bf_bool(v, 5)
        self.classification_en = p_1bf_bool(v, 6)

    def build(self) -> np.uint32:
        return (
            b_1bf_bool(self.complex_fir_en, 0)
            | b_1bf_bool(self.decimation_en, 1)
            | b_1bf_bool(self.real_fir_en, 2)
            | b_1bf_bool(self.window_en, 3)
            | b_1bf_bool(self.sum_en, 4)
            | b_1bf_bool(self.integration_en, 5)
            | b_1bf_bool(self.classification_en, 6)
        )

    @classmethod
    def parse(cls, v: np.uint32) -> "DspCtrlEnable":
        r = cls()
        r._parse(v)
        return r


class DspCtrl(AbstractFpgaRegfileU32):
    if TYPE_CHECKING:
        enable: DspCtrlEnable = Field(default=DspCtrlEnable())
        capture_delay: int = Field(default=0)
        capture_address: int = Field(default=0)
        num_captured_samples: int = Field(default=0)
        num_integration_section: int = Field(default=1)
        num_sum_section: int = Field(default=0)
        num_sum_begin: int = Field(default=0)
        num_sum_end: int = Field(default=0)
    else:
        enable: DspCtrlEnable = Field(default=DspCtrlEnable())
        capture_delay: conint(ge=0x00000000, le=0xFFFF_FFFE) = Field(default=0)
        capture_address: conint(ge=0x00000000, le=0x2_0000_0000//32) = Field(default=0)  # addr // 32, must be multiple of 16
        num_captured_samples: conint(ge=0x00000000, le=0xFFFFFFFF) = Field(default=0)
        num_integration_section: conint(ge=1, le=1048576) = Field(default=1)
        num_sum_section: conint(ge=1, le=4095) = Field(default=1)
        num_sum_begin: conint(ge=0x00000000, le=0xFFFFFFFF) = Field(default=0)
        num_sum_end: conint(ge=0x00000000, le=0xFFFFFFFF) = Field(default=0xFFFFFFFC)

    @classmethod
    def parse(cls, v: npt.NDArray[np.uint32]) -> "DspCtrl":
        r = cls()
        r._parse(v)
        return r


class CaptureProxy(AbstractFpgaProxy):
    REG_DECL: Dict[str, Tuple[int, type]] = {
        # "ctrl": (0x0, CaptureCtrlCtrl),
        # "status": (0x4, CaptureCtrlStatus),
        # "error": (0x8, CaptureCtrlError),
    }

    _DSP_MODULE_CTRL_BASE = 0x0000
    _DSP_MODULE_LEN_SUM_SECTION_BASE = 0x1000  #
    _DSP_MODULE_LEN_POST_BLANK_BASE = 0x5000  # (0x0000_0001 -- 0xFFFF_FFFF)
    _DSP_MODULE_CFIR_BASE = 0x9000  # -- 0x907F (i16)
    _DSP_MODULE_FIR_BASE = 0xA000  # -- 0xA03F (i16)
    _DSP_MODULE_WINDOW_BASE = 0xB000  # -- 0xEFFF, i32 (* 2^-30), fixed point
    _DSP_MODULE_DECISION_BASE = 0xF000  # -- 0xF017, f32

    def __init__(self, base: int, param_base: int, have_dsp: bool, udprw: AbstractFpgaIO):
        super().__init__(base, udprw)
        self._param_base = param_base
        self._have_dsp = have_dsp

    @property
    def have_dsp(self) -> bool:
        return self._have_dsp

    def get_dsp_ctrl(self) -> DspCtrl:
        if not self.have_dsp:
            raise ValueError("no dsp module is available")
        addr = self._param_base + self._DSP_MODULE_CTRL_BASE
        v = self._udprw.read_u32_vector(addr, DspCtrl.num_words())
        return DspCtrl.parse(v)

    def set_dsp_ctrl(self, data: DspCtrl) -> None:
        if not self.have_dsp:
            raise ValueError("no dsp module is available")
        addr = self._param_base + self._DSP_MODULE_CTRL_BASE
        self._udprw.write_u32_vector(addr, data.build())

    def get_dsp_sum_section_config(self, idx: int, num_sections: int) -> List[DspSumSectionConfig]:
        # Note: available for all capture units
        if not 0 <= idx < _NUM_SUM_SECTIONS:
            raise ValueError(f"index of sum section (={idx}) is out of range")
        if num_sections <= 0:
            raise ValueError(f"non-positive num_sections (={num_sections}) is not allowed")
        if not 0 <= idx+num_sections < _NUM_SUM_SECTIONS:
            raise ValueError(f"index of sum section (={idx}+{num_sections}) is out of range")
        ss_words = self._udprw.read_u32_vector(
            self._param_base + self._DSP_MODULE_LEN_SUM_SECTION_BASE + idx*4, num_sections
        )
        pb_words = self._udprw.read_u32_vector(
            self._param_base + self._DSP_MODULE_LEN_POST_BLANK_BASE + idx*4, num_sections
        )
        return [DspSumSectionConfig(num_sum_section_words=ss_words[i], num_post_blank_words=pb_words[i]) for i in range(num_sections)]

    def set_dsp_sum_section_config(self, idx, sections: Sequence[DspSumSectionConfig]):
        num_sections = len(sections)
        if not 0 <= idx < _NUM_SUM_SECTIONS:
            raise ValueError(f"index of sum section (={idx}) is out of range")
        if not 0 <= idx+num_sections < _NUM_SUM_SECTIONS:
            raise ValueError(f"too many sum sections from index ({idx}+{num_sections})")
        ss_words = np.zeros(num_sections, dtype=np.uint32)
        pb_words = np.zeros(num_sections, dtype=np.uint32)
        for i, s in enumerate(sections):
            ss_words[i] = s.num_sum_section_words
            pb_words[i] = s.num_post_blank_words

        self._udprw.write_u32_vector(self._param_base + self._DSP_MODULE_LEN_SUM_SECTION_BASE + idx * 4, ss_words)
        self._udprw.write_u32_vector(self._param_base + self._DSP_MODULE_LEN_POST_BLANK_BASE + idx * 4, pb_words)

    def get_cfir_config(self) -> DspComplexFirConfig:
        # Notes: contents of register is i16 sign-extended as i32.
        coeff = self._udprw.read_i32_vector(self._param_base + self._DSP_MODULE_CFIR_BASE, 8 * 2)
        return DspComplexFirConfig.parse(coeff)

    def set_cfir_config(self, data: DspComplexFirConfig) -> None:
        self._udprw.write_i32_vector(self._param_base + self._DSP_MODULE_CFIR_BASE, data.build())


class CaptureMasterBitmap10(AbstractFpgaBitArrayReg):
    NUM_CAPTURES: Final[int] = 10

    if TYPE_CHECKING:
        caps: List[bool] = Field(default=[False] * NUM_CAPTURES)
    else:
        caps: conlist(bool, min_length=NUM_CAPTURES, max_length=NUM_CAPTURES) = Field(default=[False] * NUM_CAPTURES)

    def _parse(self, v: np.uint32):
        u = int(v)  # for avoiding type check error
        for i in range(self.NUM_CAPTURES):
            self.caps[i] = ((u & 0b1) == 0b1)
            u >>= 1

    def build(self) -> np.uint32:
        v: int = 0
        for i in range(self.NUM_CAPTURES-1, -1, -1):
            v <<= 1
            v |= 0b1 if self.caps[i] else 0b0
        return np.uint32(v)

    def __getitem__(self, k: int) -> bool:
        return self.caps[k]

    def __setitem__(self, k: int, v: bool) -> None:
        self.caps[k] = v

    @classmethod
    def parse(cls, v) -> "CaptureMasterBitmap10":
        r = cls()
        r._parse(v)
        return r


class CaptureMasterProxy(AbstractFpgaProxy):
    NUM_CAPTURES: Final[int] = 10
    CaptureMasterBitmap = CaptureMasterBitmap10
    assert hasattr(CaptureMasterBitmap, "NUM_CAPTURES") and NUM_CAPTURES == CaptureMasterBitmap.NUM_CAPTURES

    REG_DECL: Dict[str, Tuple[int, type]] = {
        "version": (0x00, E7ModuleVersion),
        #"trigger_awg0": (0x04, CaptureMasterTriggerAwg),
        #"trigger_awg1": (0x08, CaptureMasterTriggerAwg),
        "trigger_mask": (0x0C, CaptureMasterBitmap),
        "ctrl_target_sel": (0x10, CaptureMasterBitmap),
        #"ctrl": (0x14, CaptureCtrlCtrl),
        "wakeup_status": (0x18, CaptureMasterBitmap),
        "busy_status": (0x1C, CaptureMasterBitmap),
        "done_status": (0x20, CaptureMasterBitmap),
        "fifo_ovreflow_err": (0x24, CaptureMasterBitmap),
        "write_err": (0x28, CaptureMasterBitmap),
        #"trigger_awg2": (0x2C, CaptureMasterTriggerAwg),
        #"trigger_awg3": (0x30, CaptureMasterTriggerAwg),
    }

    _CTRL_OFFSET: Final[Tuple[int, ...]] = tuple([a * 0x00100 + 0x00100 for a in range(NUM_CAPTURES)])
    _PARAMETER_OFFSET: Final[Tuple[int, ...]] = tuple([a * 0x10000 + 0x10000 for a in range(NUM_CAPTURES)])

    def __init__(self, base: int, udprw: AbstractFpgaIO):
        super().__init__(base, udprw)
        self._capture_proxy : List[CaptureProxy] = [
            CaptureProxy(
                self._base + self._CTRL_OFFSET[idx],
                self._base + self._PARAMETER_OFFSET[idx],
                (idx < 8),
                self._udprw
            ) for idx in range(self.NUM_CAPTURES)
        ]

    def get_capture_proxy(self, capture_idx: int) -> CaptureProxy:
        return self._capture_proxy[capture_idx]


if __name__ == "__main__":
    from e7awgsw.feedback.uplpacketbuffer import UplPacketMode

    logging.basicConfig(level=logging.INFO, format="{asctime} [{levelname:.4}] {name}: {message}", style="{")

    udprw_cap = UdpRw(
        ip_addr="10.1.0.42",
        port=16385,
        min_rw_size=4,
        bottom_address=0xAFFFF,
        wr_mode_id=UplPacketMode.CAPTURE_REG_WRITE,
        rd_mode_id=UplPacketMode.CAPTURE_REG_READ,
    )

    capture_master = CaptureMasterProxy(0x0000, udprw_cap)
    c0 = capture_master.get_capture_proxy(0)
    print(c0)
    dc0 = c0.get_dsp_ctrl()
    print(dc0)
    ss0 = c0.get_dsp_sum_section_config(0, 8)
    print(ss0)
    cfir0 = c0.get_cfir_config()
    print(cfir0)
