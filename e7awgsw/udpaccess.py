from __future__ import annotations
import socket
from typing import Final
from logging import Logger
from .uplpacket import UplPacket
from .logger import log_error

class RegAccess(object):
    
    def __init__(self, udp_rw: UdpRw, reg_size: int) -> None:
        self.__udp_rw = udp_rw
        self.__reg_size = reg_size # bytes


    def write(self, addr: int, offset: int, val: int) -> None:
        wr_addr = addr + offset
        val = val & ((1 << (self.__reg_size * 8)) - 1)
        wr_data = val.to_bytes(self.__reg_size, 'little')
        self.__udp_rw.write(wr_addr, wr_data)


    def read(self, addr: int, offset: int) -> int:
        rd_addr = addr + offset
        rd_data = self.__udp_rw.read(rd_addr, self.__reg_size)
        return int.from_bytes(rd_data, 'little')


    def write_bits(
        self, addr: int, offset: int, bit_pos: int, num_bits: int, val: int
    ) -> None:
        reg_val = self.read(addr, offset)
        reg_val = (reg_val & ~self.__get_mask(bit_pos, num_bits)) | \
            ((val << bit_pos) & self.__get_mask(bit_pos, num_bits))
        self.write(addr, offset, reg_val)


    def read_bits(self, addr: int, offset: int, bit_pos: int, num_bits: int) -> int:
        reg_val = self.read(addr, offset)
        reg_val = (reg_val & self.__get_mask(bit_pos, num_bits)) >> bit_pos
        return reg_val


    def multi_write(self, addr: int, offset: int, *vals: int) -> None:
        wr_addr = addr + offset
        wr_data = bytearray()
        for val in vals:
            val = val & ((1 << (self.__reg_size * 8)) - 1)
            wr_data += val.to_bytes(self.__reg_size, 'little')
        self.__udp_rw.write(wr_addr, wr_data)


    def multi_read(self, addr: int, offset: int, num_regs: int) -> list[int]:
        rd_addr = addr + offset
        rd_data = self.__udp_rw.read(rd_addr, self.__reg_size * num_regs)
        return [
            int.from_bytes(rd_data[i * self.__reg_size : (i + 1) * self.__reg_size], 'little') 
            for i in range(num_regs)]
    

    def __get_mask(self, index: int, size: int) -> int:
        return ((1 << size) - 1) << index


    def close(self) -> None:
        self.__udp_rw.close()


    @property
    def my_ip_addr(self) -> str:
        return self.__udp_rw.my_ip_addr


    @property
    def my_port(self) -> int:
        return self.__udp_rw.my_port


class AwgRegAccess(RegAccess):

    MIN_RW_SIZE: Final = 4 # bytes
    REG_SIZE: Final = 4 # bytes

    def __init__(self, ip_addr: str, port: int, *loggers: Logger) -> None:
        udp_rw = UdpRw(
            ip_addr,
            port,
            self.MIN_RW_SIZE,
            UplPacket.MODE_AWG_REG_WRITE,
            UplPacket.MODE_AWG_REG_READ,
            *loggers)

        super().__init__(udp_rw, self.REG_SIZE)


class CaptureRegAccess(RegAccess):

    MIN_RW_SIZE: Final = 4 # bytes
    REG_SIZE: Final = 4 # bytes

    def __init__(self, ip_addr: str, port: int, *loggers: Logger) -> None:
        udp_rw = UdpRw(
            ip_addr,
            port,
            self.MIN_RW_SIZE,
            UplPacket.MODE_CAPTURE_REG_WRITE,
            UplPacket.MODE_CAPTURE_REG_READ,
            *loggers)

        super().__init__(udp_rw, self.REG_SIZE)


class DoutRegAccess(RegAccess):

    MIN_RW_SIZE: Final = 4 # bytes
    REG_SIZE: Final = 4 # bytes

    def __init__(self, ip_addr: str, port: int, *loggers: Logger) -> None:
        udp_rw = UdpRw(
            ip_addr,
            port,
            self.MIN_RW_SIZE,
            UplPacket.MODE_DOUT_REG_WRITE,
            UplPacket.MODE_DOUT_REG_READ,
            *loggers)

        super().__init__(udp_rw, self.REG_SIZE)


class WaveRamAccess(object):

    def __init__(self, ip_addr: str, port: int, word_size: int, *loggers: Logger) -> None:
        self.__udp_rw = UdpRw(
            ip_addr,
            port,
            word_size,
            UplPacket.MODE_WAVE_RAM_WRITE,
            UplPacket.MODE_WAVE_RAM_READ,
            *loggers)


    def write(self, addr: int, data: bytes) -> None:
        self.__udp_rw.write(addr, data)


    def read(self, addr: int, size: int) -> bytes:
        return self.__udp_rw.read(addr, size)


    def close(self) -> None:
        self.__udp_rw.close()


class UdpRw(object):

    BUFSIZE: Final = 16384 # bytes
    #MAX_RW_SIZE: Final = 3616 # bytes
    MAX_RW_SIZE: Final = 1408 # bytes
    TIMEOUT: Final = 25 # sec

    def __init__(self,
        ip_addr: str,
        port: int,
        min_rw_size: int,
        wr_mode_id: int,
        rd_mode_id: int,
        *loggers: Logger
    ) -> None:
        self.__dest_addr = (ip_addr, port)
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.settimeout(self.TIMEOUT)
        self.__sock.bind((get_my_ip_addr(ip_addr), 0))
        self.__min_rw_size = min_rw_size
        self.__wr_mode_id = wr_mode_id
        self.__rd_mode_id = rd_mode_id
        self.__loggers = loggers
 

    def write(self, addr: int, data: bytes) -> None:
        size_remaining = len(data)
        pos = 0
        while (size_remaining > 0):
            size_to_send = self.MAX_RW_SIZE if (size_remaining >= self.MAX_RW_SIZE) else size_remaining
            self.__send_data(addr, data[pos : pos + size_to_send])
            addr += size_to_send
            pos += size_to_send
            size_remaining -= size_to_send


    def __send_data(self, addr: int, data: bytes) -> None:
        # アドレス端数調整
        frac_len = addr % self.__min_rw_size
        if frac_len != 0:
            addr = addr // self.__min_rw_size * self.__min_rw_size
            rd_data = self.read(addr, self.__min_rw_size)
            data = rd_data[0 : frac_len] + data
        
        # データ端数調整
        data_len = len(data)
        frac_len = data_len % self.__min_rw_size
        if frac_len != 0:
            rd_addr = addr + (data_len // self.__min_rw_size * self.__min_rw_size)
            rd_data = self.read(rd_addr, self.__min_rw_size)
            data = data + rd_data[frac_len : self.__min_rw_size]

        try:
            send_packet = UplPacket(self.__wr_mode_id, addr, len(data), data)
            self.__sock.sendto(send_packet.serialize(), self.__dest_addr)
            recv_data, dev_addr = self.__sock.recvfrom(self.BUFSIZE)
            recv_packet = UplPacket.deserialize(recv_data)
            if (recv_packet.num_bytes() != len(data)) or (recv_packet.addr() != addr):
                err_msg = self.__gen_err_msg(
                    'upl write err', dev_addr, recv_data,
                    addr, len(data), recv_packet.addr(), recv_packet.num_bytes())
                raise  ValueError(err_msg)
        except socket.timeout as e:
            log_error('{},  Dest {}'.format(e, self.__dest_addr), *self.__loggers)
            raise
        except Exception as e:
            log_error(e, *self.__loggers)
            raise


    def read(self, addr: int, size: int) -> bytes:
        size_remaining = size
        rd_data = bytearray()
        while (size_remaining > 0):
            size_to_recv = self.MAX_RW_SIZE if (size_remaining >= self.MAX_RW_SIZE) else size_remaining
            rd_data += self.__recv_data(addr, size_to_recv)
            addr += size_to_recv
            size_remaining -= size_to_recv
        return rd_data


    def __recv_data(self, addr: int, size: int) -> bytes:
        # 端数調整
        rd_addr = addr // self.__min_rw_size * self.__min_rw_size
        rd_offset = addr - rd_addr
        ext_size = size + rd_offset
        rd_size = (ext_size + self.__min_rw_size - 1) // self.__min_rw_size * self.__min_rw_size

        try:
            send_packet = UplPacket(self.__rd_mode_id, rd_addr, rd_size)
            self.__sock.sendto(send_packet.serialize(), self.__dest_addr)
            recv_data, dev_addr = self.__sock.recvfrom(self.BUFSIZE)
            recv_packet = UplPacket.deserialize(recv_data)
            if (recv_packet.num_bytes() != rd_size) or (recv_packet.addr() != rd_addr):
                err_msg = self.__gen_err_msg(
                    'upl read err', dev_addr, recv_data,
                    addr, rd_size, recv_packet.addr(), recv_packet.num_bytes())
                raise  ValueError(err_msg)
        except socket.timeout as e:
            log_error('{},  Dest {}'.format(e, self.__dest_addr), *self.__loggers)
            raise
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        return recv_packet.payload()[rd_offset : rd_offset + size]


    def __gen_err_msg(
        self,
        summary: str,
        devie_ip_addr: str,
        recv_data: object,
        exp_addr: int,
        exp_data_len: int,
        actual_addr: int,
        actual_data_len: int
    ) -> str:
        msg = '{}\n'.format(summary)
        msg += '  Server IP / Port : {}\n'.format(self.__sock.getsockname())
        msg += '  Target IP / Port : {}\n'.format(self.__dest_addr)
        msg += '  Device IP / Port : {}\n'.format(devie_ip_addr)
        msg += '  recv data : {}\n'.format(recv_data)
        msg += '  expected addr : {}, expected data len : {}\n'.format(exp_addr, exp_data_len)
        msg += '  actual addr : {}, actual data len : {}\n'.format(actual_addr, actual_data_len)
        return msg

    def close(self) -> None:
        self.__sock.close()


    @property
    def my_ip_addr(self) -> str:
        return self.__sock.getsockname()[0]


    @property
    def my_port(self) -> int:
        return self.__sock.getsockname()[1]


def get_my_ip_addr(ip_addr: str) -> str:
    """ip_addr にパケットを送る際のこのマシンの IP アドレスを取得する"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((ip_addr, 0))
    my_ip_addr = sock.getsockname()[0]
    sock.close()
    return my_ip_addr
