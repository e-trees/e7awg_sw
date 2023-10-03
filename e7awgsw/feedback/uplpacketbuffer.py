from abc import ABCMeta, abstractmethod
from enum import Enum
import logging
from typing import Union, Final, Tuple

logger = logging.getLogger(__name__)


class UplPacketMode(Enum):
    WAVE_RAM_READ = (0x00, "WAVE RAM READ", False, (0x01,))
    WAVE_RAM_READ_REPLY = (0x01, "WAVE RAM READ-REPLY", True, None)
    WAVE_RAM_WRITE = (0x02, "WAVE RAM WRITE", True, (0x03,))
    WAVE_RAM_WRITE_ACK = (0x03, "WAVE RAM WRITE-ACK", False, None)

    AWG_REG_READ = (0x10, "AWG REG READ", False, (0x11,))
    AWG_REG_READ_REPLY = (0x11, "AWG REG READ-REPLY", True, None)
    AWG_REG_WRITE = (0x12, "AWG REG WRITE", True, (0x13,))
    AWG_REG_WRITE_ACK = (0x13, "AWG REG WRITE-ACK", False, None)

    CAPTURE_REG_READ = (0x40, "CAP REG READ", False, (0x41,))
    CAPTURE_REG_READ_REPLY = (0x41, "CAP REG READ-REPLY", True, None)
    CAPTURE_REG_WRITE = (0x42, "CAP REG WRITE", True, (0x43,))
    CAPTURE_REG_WRITE_ACK = (0x43, "CAP REG WRITE-ACK", False, None)

    SEQUENCER_REG_READ = (0x20, "SEQ REG READ", False, (0x21,))
    SEQUENCER_REG_READ_REPLY = (0x21, "SEQ REG READ-REPLY", True, None)
    SEQUENCER_REG_WRITE = (0x22, "SEQ REG WRITE", True, (0x23,))
    SEQUENCER_REG_WRITE_ACK = (0x23, "SEQ REG WRITE-ACK", False, None)
    SEQUENCER_CMD_WRITE = (0x24, "SEQ CMD WRITE", True, (0x25,))
    SEQUENCER_CMD_WRITE_ACK = (0x25, "SEQ CMD WRITE-ACK", False, None)
    SEQUENCER_CMD_ERR_REPORT = (0x27, "SEQ CMD ERROR-REPORT", True, None)

    UNDEFINED = (0xFF, "UNDEFINED", False, None)

    def __init__(self, mode_octet: int, mode_label: str, has_payload: bool,
                 expected_modes_of_reply: Union[Tuple[int, ...], None]):
        self._octet = mode_octet
        self._label = mode_label
        self._has_payload = has_payload
        self._expected_modes_of_reply = expected_modes_of_reply

    def __repr__(self):
        return f"UplPacketMode:{self.label}"

    @property
    def octet(self) -> int:
        return self._octet

    @property
    def label(self) -> str:
        return self._label

    @property
    def has_payload(self) -> bool:
        return self._has_payload

    def is_expected_reply(self, replied_mode: "UplPacketMode"):
        return (self._expected_modes_of_reply is not None) and (replied_mode.octet in self._expected_modes_of_reply)

    @classmethod
    def from_int(cls, v: int) -> "UplPacketMode":
        for k, u in cls.__members__.items():
            if u.octet == v:
                return u
        else:
            raise ValueError("invalid octet for UplPacketMode")


class UplPacketAbstract(metaclass=ABCMeta):
    __slots__ = (
        "_num_max_payload_bytes",
        "_buffer",
        "_mode",
        "_addr",
        "_num_payload_bytes",
    )
    _HEADER_SIZE: Final[int] = 8

    def __init__(self, num_max_payload_bytes: int):
        if num_max_payload_bytes < 0:
            raise ValueError("negative num_max_payload_bytes is not allowed")

        self._mode = UplPacketMode.UNDEFINED
        self._addr: int = 0
        self._num_max_payload_bytes: int = num_max_payload_bytes
        self._num_payload_bytes: int = 0

    def __repr__(self):
        return f"mode: {self._mode.label:s} ({self._mode.octet:02x}), " \
               f"mem addr: {self.address}, " \
               f"payload bytes: {self._num_payload_bytes}" \
               f"has payload: {self._mode.has_payload}"

    def _init(self, mode: UplPacketMode, address: int, num_payload_bytes: int):
        if address < 0:
            raise ValueError("negative address is not allowed")
        if num_payload_bytes < 0:
            raise ValueError("negative num_payload_bytes is not allowed")
        if mode.has_payload:
            if self._num_max_payload_bytes < num_payload_bytes:
                raise ValueError("num_payload_bytes exceeds the maximum limit")

        self._mode = mode
        self._addr = address
        self._num_payload_bytes = num_payload_bytes

    @property
    def mode(self):
        return self._mode

    @property
    def num_payload_bytes(self) -> int:
        return self._num_payload_bytes

    @property
    def address(self) -> int:
        return self._addr

    def has_payload(self) -> bool:
        return self._mode.has_payload

    @abstractmethod
    def payload(self) -> memoryview:
        pass


class UplPacketBuffer(UplPacketAbstract):
    _DEFAULT_MAX_PAYLOAD_SIZE: Final[int] = 65535

    def __init__(self, num_max_payload_bytes: int = _DEFAULT_MAX_PAYLOAD_SIZE):
        """QuEL-1内部のモジュール群（AWG, CaptureModule, SequencerModule) と通信するためのパケット作成のためのバッファオブジェクト
        :param num_max_payload_bytes: 作成するパケットバッファの最大ペイロードサイズ。デフォルト値は_DEFAULT_MAX_PAYLOAD_SIZE。
        """
        super().__init__(num_max_payload_bytes)
        self._buffer = bytearray(self._num_max_payload_bytes + self._HEADER_SIZE)

    def init(self, mode: UplPacketMode, address: int, num_payload_bytes: int):
        self._init(mode, address, num_payload_bytes)

    @property
    def payload(self) -> memoryview:
        if self._mode.has_payload:
            return memoryview(self._buffer)[self._HEADER_SIZE:self._HEADER_SIZE + self._num_payload_bytes]
        else:
            raise ValueError(f"mode {self._mode} packet has no payload")

    def serialize(self) -> memoryview:
        """送信可能なパケットのバイト列の memoryview を返す"""
        if self._mode == UplPacketMode.UNDEFINED:
            raise RuntimeError("mode is not set yet")

        self._buffer[0:1] = self._mode.octet.to_bytes(1, "big")
        self._buffer[1:6] = self._addr.to_bytes(5, "big")
        self._buffer[6:8] = self._num_payload_bytes.to_bytes(2, "big")
        if self.has_payload():
            return memoryview(self._buffer)[:self._HEADER_SIZE + self._num_payload_bytes]
        else:
            return memoryview(self._buffer)[:self._HEADER_SIZE]


class UplPacket(UplPacketAbstract):
    def __init__(self, buffer: bytes):
        """QuEL-1内部のモジュール群（AWG, CaptureModule, SequencerModule) から受信したパケット解釈のためのバッファオブジェクト
        :param buffer: パケットの内容を含むbytesオブジェクト
        """
        super().__init__(len(buffer) - self._HEADER_SIZE)
        self._buffer = buffer
        self._init(
            UplPacketMode.from_int(int.from_bytes(self._buffer[0:1], "big")),
            int.from_bytes(self._buffer[1:6], "big"),
            int.from_bytes(self._buffer[6:8], "big")
        )

    @property
    def payload(self) -> memoryview:
        if self.has_payload():
            return memoryview(self._buffer)[self._HEADER_SIZE:self._HEADER_SIZE + self._num_payload_bytes]
        else:
            raise ValueError(f"mode {self._mode} packet has no payload")

    def validate(self, mode: UplPacketMode, address: int, num_payload_len: int):
        return mode.is_expected_reply(self.mode) \
               and self.address == address \
               and self.num_payload_bytes == num_payload_len
