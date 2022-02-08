import socket
import select
from .uplpacket import *
from .hwdefs import *
from .logger import *

class RegAccess(object):
    
    REG_SIZE = 4 # bytes

    def __init__(self, ip_addr, port, wr_mode_id, rd_mode_id, *loggers):
        self.__udp_rw = UdpRw(
            ip_addr, port, self.REG_SIZE, wr_mode_id, rd_mode_id, *loggers)


    def write(self, addr, offset, val):
        wr_addr = addr + offset
        val = val & ((1 << (self.REG_SIZE * 8)) - 1)
        wr_data = val.to_bytes(self.REG_SIZE, 'little')
        self.__udp_rw.write(wr_addr, wr_data)


    def read(self, addr, offset):
        rd_addr = addr + offset
        rd_data = self.__udp_rw.read(rd_addr, self.REG_SIZE)
        return int.from_bytes(rd_data, 'little')


    def write_bits(self, addr, offset, bit_pos, num_bits, val):
        reg_val = self.read(addr, offset)
        reg_val = (reg_val & ~self.__get_mask(bit_pos, num_bits)) | ((val << bit_pos) & self.__get_mask(bit_pos, num_bits))
        self.write(addr, offset, reg_val)


    def read_bits(self, addr, offset, bit_pos, num_bits):
        reg_val = self.read(addr, offset)
        reg_val = (reg_val & self.__get_mask(bit_pos, num_bits)) >> bit_pos
        return reg_val


    def multi_write(self, addr, offset, *vals):
        wr_addr = addr + offset
        wr_data = bytearray()
        for val in vals:
            val = val & ((1 << (self.REG_SIZE * 8)) - 1)
            wr_data += val.to_bytes(self.REG_SIZE, 'little')
        self.__udp_rw.write(wr_addr, wr_data)


    def multi_read(self, addr, offset, num_regs):
        rd_addr = addr + offset
        rd_data = self.__udp_rw.read(rd_addr, self.REG_SIZE * num_regs)
        return [
            int.from_bytes(rd_data[i * self.REG_SIZE : (i + 1) * self.REG_SIZE], 'little') 
            for i in range(num_regs)]
    

    def __get_mask(self, index, size):
        return ((1 << size) - 1) << index


class AwgRegAccess(object):

    def __init__(self, ip_addr, port, *loggers):
        self.__reg_access = RegAccess(
            ip_addr, port, UplPacket.MODE_AWG_REG_WRITE, UplPacket.MODE_AWG_REG_READ, *loggers)

    def write(self, addr, offset, val):
        self.__reg_access.write(addr, offset, val)

    def read(self, addr, offset):
        return self.__reg_access.read(addr, offset)

    def write_bits(self, addr, offset, bit_pos, num_bits, val):
        self.__reg_access.write_bits(addr, offset, bit_pos, num_bits, val)

    def read_bits(self, addr, offset, bit_pos, num_bits):
        return self.__reg_access.read_bits(addr, offset, bit_pos, num_bits)


class CaptureRegAccess(object):

    def __init__(self, ip_addr, port, *loggers):
        self.__reg_access = RegAccess(
            ip_addr,
            port,
            UplPacket.MODE_CAPTURE_REG_WRITE,
            UplPacket.MODE_CAPTURE_REG_READ,
            *loggers)

    def write(self, addr, offset, val):
        self.__reg_access.write(addr, offset, val)

    def read(self, addr, offset):
        return self.__reg_access.read(addr, offset)

    def write_bits(self, addr, offset, bit_pos, num_bits, val):
        self.__reg_access.write_bits(addr, offset, bit_pos, num_bits, val)

    def read_bits(self, addr, offset, bit_pos, num_bits):
        return self.__reg_access.read_bits(addr, offset, bit_pos, num_bits)

    def multi_write(self, addr, offset, *vals):
        self.__reg_access.multi_write(addr, offset, *vals)

    def multi_read(self, addr, offset, num_regs):
        return self.__reg_access.multi_read(addr, offset, num_regs)


class WaveRamAccess(object):

    MIN_RW_SIZE = 32 # bytes

    def __init__(self, ip_addr, port, *loggers):
        self.__udp_rw = UdpRw(
            ip_addr,
            port,
            self.MIN_RW_SIZE,
            UplPacket.MODE_WAVE_RAM_WRITE,
            UplPacket.MODE_WAVE_RAM_READ,
            *loggers)

    def write(self, addr, data):
        self.__udp_rw.write(addr, data)

    def read(self, addr, size):
        return self.__udp_rw.read(addr, size)


class UdpRw(object):

    BUFSIZE = 16384 # bytes
    #MAX_RW_SIZE = 3616 # bytes
    MAX_RW_SIZE = 1440 # bytes
    TIMEOUT = 12 # sec

    def __init__(self, ip_addr, port, min_rw_size, wr_mode_id, rd_mode_id, *loggers):
        self.__dest_addr = (ip_addr, port)
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.settimeout(self.TIMEOUT)
        self.__min_rw_size = min_rw_size
        self.__wr_mode_id = wr_mode_id
        self.__rd_mode_id = rd_mode_id
        self.__loggers = loggers

    def write(self, addr, data):
        size_remaining = len(data)
        pos = 0
        while (size_remaining > 0):
            size_to_send = self.MAX_RW_SIZE if (size_remaining >= self.MAX_RW_SIZE) else size_remaining
            self.__send_data(addr, data[pos : pos + size_to_send])
            addr += size_to_send
            pos += size_to_send
            size_remaining -= size_to_send


    def __send_data(self, addr, data):
        data_len = len(data)
        frac_len = data_len % self.__min_rw_size
        # 端数調整
        if frac_len != 0:
            rd_addr = addr + (data_len // self.__min_rw_size * self.__min_rw_size)
            rd_data = self.read(rd_addr, self.__min_rw_size)
            additional_data = rd_data[frac_len : self.__min_rw_size]
            data = data + additional_data
        try:
            send_packet = UplPacket(self.__wr_mode_id, addr, len(data), data)
            self.__sock.sendto(send_packet.serialize(), self.__dest_addr)
            recv_data, _ = self.__sock.recvfrom(self.BUFSIZE)
            recv_packet = UplPacket.deserialize(recv_data)
            if (recv_packet.num_bytes() != len(data)) or (recv_packet.addr() != addr):
                raise  ValueError(
                    'upl write err : addr {:x},  Dest {}'.format(addr, self.__dest_addr))
        except socket.timeout as e:
            log_error('{},  Dest {}'.format(e, self.__dest_addr), *self.__loggers)
            raise
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

    def read(self, addr, size):
        size_remaining = size
        rd_data = bytearray()
        while (size_remaining > 0):
            size_to_recv = self.MAX_RW_SIZE if (size_remaining >= self.MAX_RW_SIZE) else size_remaining
            rd_data += self.__recv_data(addr, size_to_recv)
            addr += size_to_recv
            size_remaining -= size_to_recv
        return rd_data


    def __recv_data(self, addr, size):
        # 端数調整
        rd_size = (size + self.__min_rw_size - 1) // self.__min_rw_size * self.__min_rw_size
        
        try:
            send_packet = UplPacket(self.__rd_mode_id, addr, rd_size)
            self.__sock.sendto(send_packet.serialize(), self.__dest_addr)
            recv_data, _ = self.__sock.recvfrom(self.BUFSIZE)
            recv_packet = UplPacket.deserialize(recv_data)
            if (recv_packet.num_bytes() != rd_size) or (recv_packet.addr() != addr):
                raise ValueError(
                    'upl read err : addr {:x}  size {},   Dest {}'.format(addr, size, self.__dest_addr))
        except socket.timeout as e:
            log_error('{},  Dest {}'.format(e, self.__dest_addr), *self.__loggers)
            raise
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        return recv_packet.payload()[0 : size]
