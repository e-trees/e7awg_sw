import socket
import threading
import copy
from .uplpacket import UplPacket
from .logger import log_error
from .sequencercmd import AwgStartCmd, CaptureEndFenceCmd, WaveSequenceSetCmd, CaptureParamSetCmd, CaptureAddrSetCmd, FeedbackCalcOnClassificationCmd
from .sequencercmd import AwgStartCmdErr, CaptureEndFenceCmdErr, WaveSequenceSetCmdErr, CaptureParamSetCmdErr, CaptureAddrSetCmdErr, FeedbackCalcOnClassificationCmdErr
from .hwparam import CMD_ERR_REPORT_SIZE
from .hwdefs import AWG, CaptureUnit

class RegAccess(object):
    
    def __init__(self, udp_rw, reg_size):
        self.__udp_rw = udp_rw
        self.__reg_size = reg_size # bytes


    def write(self, addr, offset, val):
        wr_addr = addr + offset
        val = val & ((1 << (self.__reg_size * 8)) - 1)
        wr_data = val.to_bytes(self.__reg_size, 'little')
        self.__udp_rw.write(wr_addr, wr_data)


    def read(self, addr, offset):
        rd_addr = addr + offset
        rd_data = self.__udp_rw.read(rd_addr, self.__reg_size)
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
            val = val & ((1 << (self.__reg_size * 8)) - 1)
            wr_data += val.to_bytes(self.__reg_size, 'little')
        self.__udp_rw.write(wr_addr, wr_data)


    def multi_read(self, addr, offset, num_regs):
        rd_addr = addr + offset
        rd_data = self.__udp_rw.read(rd_addr, self.__reg_size * num_regs)
        return [
            int.from_bytes(rd_data[i * self.__reg_size : (i + 1) * self.__reg_size], 'little') 
            for i in range(num_regs)]
    

    def __get_mask(self, index, size):
        return ((1 << size) - 1) << index


    def close(self):
        self.__udp_rw.close()


    @property
    def my_port(self):
        return self.__udp_rw.my_port


class AwgRegAccess(RegAccess):

    MIN_RW_SIZE = 4 # bytes
    REG_SIZE = 4 # bytes

    def __init__(self, ip_addr, port, *loggers):
        udp_rw = UdpRw(
            ip_addr,
            port,
            self.MIN_RW_SIZE,
            UplPacket.MODE_AWG_REG_WRITE,
            UplPacket.MODE_AWG_REG_READ,
            *loggers)

        super().__init__(udp_rw, self.REG_SIZE)


class CaptureRegAccess(RegAccess):

    MIN_RW_SIZE = 4 # bytes
    REG_SIZE = 4 # bytes

    def __init__(self, ip_addr, port, *loggers):
        udp_rw = UdpRw(
            ip_addr,
            port,
            self.MIN_RW_SIZE,
            UplPacket.MODE_CAPTURE_REG_WRITE,
            UplPacket.MODE_CAPTURE_REG_READ,
            *loggers)

        super().__init__(udp_rw, self.REG_SIZE)


class ParamRegistryAccess(RegAccess):

    MIN_RW_SIZE = 32 # bytes
    REG_SIZE = 4 # bytes

    def __init__(self, ip_addr, port, *loggers):
        udp_rw = UdpRw(
            ip_addr,
            port,
            self.MIN_RW_SIZE,
            UplPacket.MODE_WAVE_RAM_WRITE,
            UplPacket.MODE_WAVE_RAM_READ,
            *loggers)

        super().__init__(udp_rw, self.REG_SIZE)


class SequencerRegAccess(RegAccess):

    MIN_RW_SIZE = 4 # bytes
    REG_SIZE = 4 # bytes

    def __init__(self, ip_addr, port, *loggers):
        udp_rw = UdpRw(
            ip_addr,
            port,
            self.MIN_RW_SIZE,
            UplPacket.MODE_SEQUENCER_REG_WRITE,
            UplPacket.MODE_SEQUENCER_REG_READ,
            *loggers)

        super().__init__(udp_rw, self.REG_SIZE)


class SequencerCmdSender(object):

    MIN_RW_SIZE = 32 # bytes

    def __init__(self, ip_addr, port, *loggers):
        self.__udp_rw = UdpRw(
            ip_addr,
            port,
            1,
            UplPacket.MODE_SEQUENCER_CMD_WRITE,
            UplPacket.MODE_OTHERS,
            *loggers)


    def send(self, cmd_list):
        payload = bytearray()
        whole_size = 8
        num_cmds = 0
        while cmd_list:
            cmd = cmd_list[0]
            if (whole_size + cmd.size()) > UdpRw.MAX_RW_SIZE:
                payload = num_cmds.to_bytes(8, 'little') + payload
                self.__udp_rw.write(0, payload)
                payload = bytearray()
                whole_size = 8
                num_cmds = 0
            else:
                payload.extend(cmd.serialize())
                whole_size += cmd.size()
                num_cmds += 1
                cmd_list.pop(0)
        

        payload = num_cmds.to_bytes(8, 'little') + payload
        self.__udp_rw.write(0, payload)


    def close(self):
        self.__udp_rw.close()


    @property
    def my_port(self):
        return self.__udp_rw.my_port


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


    def close(self):
        self.__udp_rw.close()


class CmdErrReceiver(threading.Thread):

    BUFSIZE = 16384 # bytes

    def __init__(self, *loggers):
        #threading.Thread.__init__(self)
        super().__init__()
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.bind(('', 0))
        self.__rlock = threading.RLock()
        self.__reports = []
        self.__loggers = loggers


    def run(self):
        while True:
            try:
                recv_data, _ = self.__sock.recvfrom(self.BUFSIZE)
                recv_packet = UplPacket.deserialize(recv_data)
                if recv_packet.mode() == UplPacket.MODE_OTHERS:
                    return

                payload = recv_packet.payload()[8:]
                num_reports = len(payload) // CMD_ERR_REPORT_SIZE
                with self.__rlock:
                    for i in range(num_reports):
                        report_bytes = payload[i * CMD_ERR_REPORT_SIZE : (i + 1) * CMD_ERR_REPORT_SIZE]
                        self.__reports.append(self.__gen_seq_cmd_err_from_bytes(report_bytes))
            except Exception as e:
                log_error(e, *self.__loggers)
                raise

    @classmethod
    def __gen_seq_cmd_err_from_bytes(cls, data):
        bit_field = int.from_bytes(data, byteorder='little')
        is_terminated = bit_field & 0x1
        cmd_id = (bit_field >> 1) & 0x7F
        cmd_no = (bit_field >> 8) & 0xFFFF
        read_err = bool((bit_field >> 24) & 0x1)
        write_err = bool((bit_field >> 25) & 0x1)
        awg_id_bits = bit_field >> 24
        awg_id_list = list(filter(lambda awg_id: awg_id_bits & (1 << awg_id), AWG.all()))
        cap_unit_id_bits = bit_field >> 24
        cap_unit_id_list = list(filter(
            lambda cap_unit_id: cap_unit_id_bits & (1 << cap_unit_id), CaptureUnit.all()))

        if cmd_id == AwgStartCmd.ID:
            return AwgStartCmdErr(cmd_no, is_terminated, awg_id_list)
        elif cmd_id == CaptureEndFenceCmd.ID:
            return CaptureEndFenceCmdErr(cmd_no, is_terminated, cap_unit_id_list)
        elif cmd_id == WaveSequenceSetCmd.ID:
            return WaveSequenceSetCmdErr(cmd_no, is_terminated, read_err, write_err)
        elif cmd_id == CaptureParamSetCmd.ID:
            return CaptureParamSetCmdErr(cmd_no, is_terminated, read_err, write_err)
        elif cmd_id == CaptureAddrSetCmd.ID:
            return CaptureAddrSetCmdErr(cmd_no, is_terminated, write_err)
        elif cmd_id == FeedbackCalcOnClassificationCmd.ID:
            return FeedbackCalcOnClassificationCmdErr(cmd_no, is_terminated, read_err)

        assert False, ('Invalid cmd err.  cmd_id = {}'.format(cmd_id))


    def pop_err_reports(self):
        with self.__rlock:
            tmp = self.__reports
            self.__reports = []
            return tmp


    def stop(self):
        if self.is_alive():
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                stop_packet = UplPacket(UplPacket.MODE_OTHERS, 0, 0)
                sock.sendto(stop_packet.serialize(), ('127.0.0.1', self.my_port))
            self.join()


    def close(self):
        self.__sock.close()


    @property
    def my_port(self):
        return self.__sock.getsockname()[1]


class UdpRouter(threading.Thread):

    BUFSIZE = 16384 # bytes

    def __init__(self, table, *loggers):
        """受信した UPL パケットをそのモードに応じて転送する"""
        #threading.Thread.__init__(self)
        super().__init__()
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.bind(('', 0))
        self.__table = copy.copy(table)
        self.__rlock = threading.RLock()
        self.__loggers = loggers
    

    def run(self):
        while True:
            try:
                recv_data, _ = self.__sock.recvfrom(self.BUFSIZE)
                recv_packet = UplPacket.deserialize(recv_data)
                if recv_packet.mode() == UplPacket.MODE_OTHERS:
                    return

                with self.__rlock:
                    if recv_packet.mode() in self.__table:
                        addr = self.__table[recv_packet.mode()]
                    else:
                        continue
                
                self.__sock.sendto(recv_data, addr)                
            except Exception as e:
                log_error(e, *self.__loggers)
                raise


    def stop(self):
        if self.is_alive():
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                stop_packet = UplPacket(UplPacket.MODE_OTHERS, 0, 0)
                sock.sendto(stop_packet.serialize(), ('127.0.0.1', self.my_port))
            self.join()


    def add_entry(self,packet_mode, ip_addr, port):
        with self.__rlock:
            self.__table[packet_mode] = (ip_addr, port)


    def close(self):
        self.__sock.close()


    @property
    def my_port(self):
        return self.__sock.getsockname()[1]


class UdpRw(object):

    BUFSIZE = 16384 # bytes
    #MAX_RW_SIZE = 3616 # bytes
    MAX_RW_SIZE = 1440 # bytes
    TIMEOUT = 25 # sec

    def __init__(self, ip_addr, port, min_rw_size, wr_mode_id, rd_mode_id, *loggers):
        self.__dest_addr = (ip_addr, port)
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.settimeout(self.TIMEOUT)
        self.__sock.bind(('', 0))
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
        rd_addr = addr // self.__min_rw_size * self.__min_rw_size
        rd_offset = addr - rd_addr
        ext_size = size + rd_offset
        rd_size = (ext_size + self.__min_rw_size - 1) // self.__min_rw_size * self.__min_rw_size

        try:
            send_packet = UplPacket(self.__rd_mode_id, rd_addr, rd_size)
            self.__sock.sendto(send_packet.serialize(), self.__dest_addr)
            recv_data, _ = self.__sock.recvfrom(self.BUFSIZE)
            recv_packet = UplPacket.deserialize(recv_data)
            if (recv_packet.num_bytes() != rd_size) or (recv_packet.addr() != rd_addr):
                raise ValueError(
                    'upl read err : addr {:x}  size {},   Dest {}'.format(rd_addr, size, self.__dest_addr))
        except socket.timeout as e:
            log_error('{},  Dest {}'.format(e, self.__dest_addr), *self.__loggers)
            raise
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        return recv_packet.payload()[rd_offset : rd_offset + size]


    def close(self):
        self.__sock.close()


    @property
    def my_port(self):
        return self.__sock.getsockname()[1]


def get_my_ip_addr(ip_addr):
    """ip_addr にパケットを送る際のこのマシンの IP アドレスを取得する"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((ip_addr, 0))
    my_ip_addr = sock.getsockname()[0]
    sock.close()
    return my_ip_addr
