from typing_extensions import Self
from typing import Final

class UplPacket(object):

    MODE_WAVE_RAM_READ: Final       = 0x00
    MODE_WAVE_RAM_READ_REPLY: Final = 0x01
    MODE_WAVE_RAM_WRITE: Final      = 0x02
    MODE_WAVE_RAM_WRITE_ACK: Final  = 0x03

    MODE_AWG_REG_READ: Final       = 0x10
    MODE_AWG_REG_READ_REPLY: Final = 0x11
    MODE_AWG_REG_WRITE: Final      = 0x12
    MODE_AWG_REG_WRITE_ACK: Final  = 0x13

    MODE_CAPTURE_REG_READ: Final       = 0x40
    MODE_CAPTURE_REG_READ_REPLY: Final = 0x41
    MODE_CAPTURE_REG_WRITE: Final      = 0x42
    MODE_CAPTURE_REG_WRITE_ACK: Final  = 0x43

    def __init__(
        self,
        mode: int,
        addr: int,
        num_bytes: int,
        payload: bytes = b''
    ) -> None:
        self.__mode = mode
        self.__num_bytes = num_bytes
        self.__addr = addr
        self.__payload = payload
        return

    def mode(self) -> int:
        return self.__mode

    def num_bytes(self) -> int:
        return self.__num_bytes

    def addr(self) -> int:
        return self.__addr

    def payload(self) -> bytes:
        return self.__payload

    def serialize(self) -> bytes:
        data = bytearray()
        data += self.__mode.to_bytes(1, "big")
        data += self.__addr.to_bytes(5, "big")
        data += self.__num_bytes.to_bytes(2, "big")
        data += self.__payload
        return data

    def __mode_to_str(self, mode: int) -> str:
        if mode == self.MODE_WAVE_RAM_READ:
            return "WAVE RAM READ"
        elif mode == self.MODE_WAVE_RAM_WRITE:
            return "WAVE RAM WRITE"
        elif mode == self.MODE_WAVE_RAM_WRITE_ACK:
            return "WAVE RAM WRITE-ACK"
        elif mode == self.MODE_WAVE_RAM_READ_REPLY:
            return "WAVE RAM READ-REPLY"
        elif mode == self.MODE_AWG_REG_READ:
            return "AWG REG READ"
        elif mode == self.MODE_AWG_REG_WRITE:
            return "AWG REG WRITE"
        elif mode == self.MODE_AWG_REG_WRITE_ACK:
            return "AWG REG WRITE-ACK"
        elif mode == self.MODE_AWG_REG_READ_REPLY:
            return "AWG REG READ-REPLY"
        elif mode == self.MODE_CAPTURE_REG_READ:
            return "CAPTURE REG READ"
        elif mode == self.MODE_CAPTURE_REG_WRITE:
            return "CAPTURE REG WRITE"
        elif mode == self.MODE_CAPTURE_REG_WRITE_ACK:
            return "CAPTURE REG WRITE-ACK"
        elif mode == self.MODE_CAPTURE_REG_READ_REPLY:
            return "CAPTURE REG READ-REPLY"
        return ""


    def __str__(self) -> str:
        ret = ('mode : {} ({})'.format(self.__mode_to_str(self.__mode), self.__mode) + '\n' + 
            'mem addr : {}'.format(self.__addr) + '\n' + 
            'payload bytes : {}'.format(self.__num_bytes))
        return ret


    @classmethod
    def deserialize(cls, data: bytes) -> Self:
        mode = int.from_bytes(data[0:1], 'big')
        addr = int.from_bytes(data[1:6], 'big')
        num_bytes = int.from_bytes(data[6:8], 'big')
        payload = b''
        if ((num_bytes != 0) and 
            ((mode == cls.MODE_AWG_REG_READ_REPLY)     or
             (mode == cls.MODE_CAPTURE_REG_READ_REPLY) or
             (mode == cls.MODE_WAVE_RAM_READ_REPLY)    or
             (mode == cls.MODE_AWG_REG_WRITE)          or 
             (mode == cls.MODE_CAPTURE_REG_WRITE)      or 
             (mode == cls.MODE_WAVE_RAM_WRITE))):
            payload = data[8 : 8 + num_bytes]

        return cls(mode, addr, num_bytes, payload)
