
class UplPacket(object):

    MODE_WAVE_RAM_READ       = 0x00
    MODE_WAVE_RAM_READ_REPLY = 0x01
    MODE_WAVE_RAM_WRITE      = 0x02
    MODE_WAVE_RAM_WRITE_ACK  = 0x03

    MODE_AWG_REG_READ       = 0x10
    MODE_AWG_REG_READ_REPLY = 0x11
    MODE_AWG_REG_WRITE      = 0x12
    MODE_AWG_REG_WRITE_ACK  = 0x13

    MODE_CAPTURE_REG_READ       = 0x40
    MODE_CAPTURE_REG_READ_REPLY = 0x41
    MODE_CAPTURE_REG_WRITE      = 0x42
    MODE_CAPTURE_REG_WRITE_ACK  = 0x43

    MODE_SEQUENCER_REG_READ       = 0x20
    MODE_SEQUENCER_REG_READ_REPLY = 0x21
    MODE_SEQUENCER_REG_WRITE      = 0x22
    MODE_SEQUENCER_REG_WRITE_ACK  = 0x23
    MODE_SEQUENCER_CMD_WRITE      = 0x24
    MODE_SEQUENCER_CMD_WRITE_ACK  = 0x25
    MODE_SEQUENCER_CMD_ERR_REPORT = 0x27

    MODE_OTHERS = 0xFF

    def __init__(
        self,
        mode,
        addr,
        num_bytes,
        payload = b''):

        self.__mode = mode
        self.__num_bytes = num_bytes
        self.__addr = addr
        self.__payload = payload
        return

    def mode(self):
        return self.__mode

    def num_bytes(self):
        return self.__num_bytes

    def addr(self):
        return self.__addr

    def payload(self):
        return self.__payload

    def serialize(self):
        data = bytearray()
        data += self.__mode.to_bytes(1, "big")
        data += self.__addr.to_bytes(5, "big")
        data += self.__num_bytes.to_bytes(2, "big")
        data += self.__payload
        return data

    def __mode_to_str(self, mode):
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
        return ""


    def __str__(self):
        ret = ('mode : {} ({})'.format(self.__mode_to_str(self.__mode), self.__mode) + '\n' + 
            'mem addr : {}'.format(self.__addr) + '\n' + 
            'payload bytes : {}'.format(self.__num_bytes))
        return ret


    @classmethod
    def deserialize(cls, data):
        mode = int.from_bytes(data[0:1], 'big')
        addr = int.from_bytes(data[1:6], 'big')
        num_bytes = int.from_bytes(data[6:8], 'big')
        payload = b''
        if ((num_bytes != 0) and 
            ((mode == cls.MODE_AWG_REG_READ_REPLY)       or
             (mode == cls.MODE_CAPTURE_REG_READ_REPLY)   or
             (mode == cls.MODE_WAVE_RAM_READ_REPLY)      or
             (mode == cls.MODE_AWG_REG_WRITE)            or 
             (mode == cls.MODE_CAPTURE_REG_WRITE)        or 
             (mode == cls.MODE_WAVE_RAM_WRITE)           or
             (mode == cls.MODE_SEQUENCER_REG_READ_REPLY) or
             (mode == cls.MODE_SEQUENCER_REG_WRITE)      or
             (mode == cls.MODE_SEQUENCER_CMD_WRITE)      or
             (mode == cls.MODE_SEQUENCER_CMD_ERR_REPORT))):
            payload = data[8 : 8 + num_bytes]

        return UplPacket(mode, addr, num_bytes, payload)
