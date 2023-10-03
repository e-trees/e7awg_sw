import logging
import socket
from typing import ByteString
import threading
import copy
from e7awgsw.feedback.uplpacketbuffer import UplPacketBuffer, UplPacketMode
from e7awgsw.logger import log_error
from e7awgsw.feedback.sequencercmd import AwgStartCmd, CaptureEndFenceCmd, WaveSequenceSetCmd, CaptureParamSetCmd, CaptureAddrSetCmd, FeedbackCalcOnClassificationCmd, WaveGenEndFenceCmd
from e7awgsw.feedback.sequencercmd import AwgStartCmdErr, CaptureEndFenceCmdErr, WaveSequenceSetCmdErr, CaptureParamSetCmdErr, CaptureAddrSetCmdErr, FeedbackCalcOnClassificationCmdErr, WaveGenEndFenceCmdErr
from e7awgsw.feedback.hwparam import CMD_ERR_REPORT_SIZE
from e7awgsw.feedback.hwdefs import AWG, CaptureUnit
from e7awgsw.feedback.udprw import UdpRw

logger = logging.getLogger(__name__)

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
    def my_ip_addr(self):
        return self.__udp_rw.my_ip_addr


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
            UplPacketBuffer.MODE_AWG_REG_WRITE,
            UplPacketBuffer.MODE_AWG_REG_READ,
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
            UplPacketBuffer.MODE_CAPTURE_REG_WRITE,
            UplPacketBuffer.MODE_CAPTURE_REG_READ,
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
            UplPacketBuffer.MODE_WAVE_RAM_WRITE,
            UplPacketBuffer.MODE_WAVE_RAM_READ,
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
            UplPacketBuffer.MODE_SEQUENCER_REG_WRITE,
            UplPacketBuffer.MODE_SEQUENCER_REG_READ,
            *loggers)

        super().__init__(udp_rw, self.REG_SIZE)


class SequencerCmdSender(object):

    MIN_RW_SIZE = 32 # bytes

    def __init__(self, ip_addr, port, *loggers):
        self.__udp_rw = UdpRw(
            ip_addr,
            port,
            1,
            UplPacketBuffer.MODE_SEQUENCER_CMD_WRITE,
            UplPacketBuffer.MODE_OTHERS,
            *loggers)


    def send(self, cmd_list):
        payload = bytearray()
        whole_size = 8
        num_cmds = 0
        while cmd_list:
            cmd = cmd_list[0]
            if (whole_size + cmd.size()) > UdpRw._ABSOLUTE_MAX_RW_SIZE:
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
    def my_ip_addr(self):
        return self.__udp_rw.my_ip_addr


    @property
    def my_port(self):
        return self.__udp_rw.my_port


class WaveRamAccess(object):

    MIN_RW_SIZE = 32 # bytes

    def __init__(self, ip_addr, port, *loggers):
        self.__udp_rw = UdpRw(
            ip_addr=ip_addr,
            port=port,
            min_rw_size=self.MIN_RW_SIZE,
            wr_mode_id=UplPacketMode.WAVE_RAM_WRITE,
            rd_mode_id=UplPacketMode.WAVE_RAM_READ,
            bottom_address=0x2_0000_0000,
            timeout=0.5,
        )

    def write(self, addr, data):
        self.__udp_rw.write(addr, data)


    def read(self, addr, size):
        return self.__udp_rw.read(addr, size)


    def close(self):
        self.__udp_rw.close()


class CmdErrReceiver(threading.Thread):

    BUFSIZE = 16384 # bytes

    def __init__(self, my_ip_addr, *loggers):
        #threading.Thread.__init__(self)
        super().__init__()
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.bind((my_ip_addr, 0))
        self.__rlock = threading.RLock()
        self.__reports = []
        self.__loggers = loggers
        self.__my_ip_addr = my_ip_addr


    def run(self):
        while True:
            try:
                recv_data, _ = self.__sock.recvfrom(self.BUFSIZE)
                recv_packet = UplPacketBuffer.deserialize(recv_data)
                if recv_packet.mode() == UplPacketBuffer.MODE_OTHERS:
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
        elif cmd_id == WaveGenEndFenceCmd.ID:
            return WaveGenEndFenceCmdErr(cmd_no, is_terminated, awg_id_list)

        assert False, ('Invalid cmd err.  cmd_id = {}'.format(cmd_id))


    def pop_err_reports(self):
        with self.__rlock:
            tmp = self.__reports
            self.__reports = []
            return tmp


    def stop(self):
        if self.is_alive():
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                stop_packet = UplPacketBuffer(UplPacketBuffer.MODE_OTHERS, 0, 0)
                sock.sendto(stop_packet.serialize(), (self.__my_ip_addr, self.my_port))
            self.join()


    def close(self):
        self.__sock.close()


    @property
    def my_ip_addr(self):
        return self.__sock.getsockname()[0]


    @property
    def my_port(self):
        return self.__sock.getsockname()[1]


class UdpRouter(threading.Thread):

    BUFSIZE = 16384 # bytes

    def __init__(self, my_ip_addr, table, *loggers):
        """受信した UPL パケットをそのモードに応じて転送する"""
        #threading.Thread.__init__(self)
        super().__init__()
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.bind((my_ip_addr, 0))
        self.__table = copy.copy(table)
        self.__rlock = threading.RLock()
        self.__loggers = loggers
        self.__my_ip_addr = my_ip_addr
    

    def run(self):
        while True:
            try:
                recv_data, _ = self.__sock.recvfrom(self.BUFSIZE)
                recv_packet = UplPacketBuffer.deserialize(recv_data)
                if recv_packet.mode() == UplPacketBuffer.MODE_OTHERS:
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
                stop_packet = UplPacketBuffer(UplPacketBuffer.MODE_OTHERS, 0, 0)
                sock.sendto(stop_packet.serialize(), (self.__my_ip_addr, self.my_port))
            self.join()


    def add_entry(self,packet_mode, ip_addr, port):
        with self.__rlock:
            self.__table[packet_mode] = (ip_addr, port)


    def close(self):
        self.__sock.close()


    @property
    def my_ip_addr(self):
        return self.__sock.getsockname()[0]


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
