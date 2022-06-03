import sys
import socket
import pathlib
from concurrent.futures import ThreadPoolExecutor
from awg import Awg
import capture as cap

lib_path = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(lib_path)
from e7awgsw.uplpacket import UplPacket
from e7awgsw.logger import get_file_logger, get_stderr_logger, log_error
from e7awgsw.hwparam import WAVE_RAM_PORT, AWG_REG_PORT


class UplDispatcher:

    __BUF_SIZE = 16384

    def __init__(self, hbm, awg_ctrl, cap_ctrl):
        self.__hbm = hbm
        self.__awg_ctrl = awg_ctrl
        self.__cap_ctrl = cap_ctrl
        self.__hbm_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__hbm_sock.bind(('', WAVE_RAM_PORT))
        self.__awg_cap_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__awg_cap_sock.bind(('', AWG_REG_PORT))
        self.__executor = ThreadPoolExecutor(max_workers = 2)
        self.__loggers = [get_file_logger(), get_stderr_logger()]


    def start(self):
        self.__executor.submit(self.__process_hbm_packet)
        self.__executor.submit(self.__process_awg_cap_packet)


    def __process_hbm_packet(self):
        """HBM へのアクセスを行うためのパケットを処理する"""
        # ThreadPoolExecutor 上で実行されるタスクの例外は, そのタスクの Future が保持するため, 標準エラー出力に表示されない.
        # 意図しない例外が発生したとき, シミュレータの停止をユーザに伝えるために try-except を使ってエラーメッセージを表示する.
        try:
            while True:
                recv_data, src_addr = self.__hbm_sock.recvfrom(self.__BUF_SIZE)
                recv_packet = UplPacket.deserialize(recv_data)
                if recv_packet.mode() == UplPacket.MODE_WAVE_RAM_READ:
                    self.__read_from_hbm(recv_packet, src_addr)
                elif recv_packet.mode() == UplPacket.MODE_WAVE_RAM_WRITE:
                    self.__write_to_hbm(recv_packet, src_addr)
                else:
                    msg = 'Invalid HBM access mode {}'.format(recv_packet.mode())
                    log_error(msg, *self.__loggers)
                    raise ValueError(msg)
        except Exception as e:
            print('ERR [process_hbm_packet] : {}'.format(e), file = sys.stderr)
            print('The e7awg_hw emulator has stopped!\n', file = sys.stderr)
            raise


    def __read_from_hbm(self, packet, reply_addr):
        rd_data = self.__hbm.read(packet.addr(), packet.num_bytes())
        reply = UplPacket(UplPacket.MODE_WAVE_RAM_READ_REPLY, packet.addr(), len(rd_data), rd_data)
        self.__hbm_sock.sendto(reply.serialize(), reply_addr)


    def __write_to_hbm(self, packet, reply_addr):
        self.__hbm.write(packet.addr(), packet.payload())
        reply = UplPacket(UplPacket.MODE_WAVE_RAM_WRITE_ACK, packet.addr(), len(packet.payload()))
        self.__hbm_sock.sendto(reply.serialize(), reply_addr)


    def __process_awg_cap_packet(self):
        try:
            while True:
                recv_data, src_addr = self.__awg_cap_sock.recvfrom(self.__BUF_SIZE)
                recv_packet = UplPacket.deserialize(recv_data)
                if recv_packet.mode() == UplPacket.MODE_AWG_REG_READ:
                    self.__read_awg_reg(recv_packet, src_addr)
                elif recv_packet.mode() == UplPacket.MODE_AWG_REG_WRITE:
                    self.__write_awg_reg(recv_packet, src_addr)
                elif recv_packet.mode() == UplPacket.MODE_CAPTURE_REG_READ:
                    self.__read_cap_reg(recv_packet, src_addr)
                elif recv_packet.mode() == UplPacket.MODE_CAPTURE_REG_WRITE:
                    self.__write_cap_reg(recv_packet, src_addr)
                else:
                    msg = 'Invalid register access mode {}'.format(recv_packet.mode())
                    log_error(msg, *self.__loggers)
                    raise ValueError(msg)
        except Exception as e:
            print('ERR [process_awg_cap_packet] : {}'.format(e), file = sys.stderr)
            print('The e7awg_hw emulator has stopped!\n', file = sys.stderr)
            raise

    def __read_awg_reg(self, packet, reply_addr):
        num_regs = packet.num_bytes() // Awg.PARAM_REG_SIZE
        rd_data = bytearray()
        for i in range(num_regs):
            addr = packet.addr() + i * Awg.PARAM_REG_SIZE
            val = self.__awg_ctrl.read_reg(addr)
            rd_data += val.to_bytes(Awg.PARAM_REG_SIZE, 'little')

        reply = UplPacket(UplPacket.MODE_AWG_REG_READ_REPLY, packet.addr(), len(rd_data), rd_data)
        self.__awg_cap_sock.sendto(reply.serialize(), reply_addr)


    def __write_awg_reg(self, packet, reply_addr):
        num_regs = packet.num_bytes() // Awg.PARAM_REG_SIZE
        for i in range(num_regs):
            addr = packet.addr() + i * Awg.PARAM_REG_SIZE
            val = packet.payload()[i * Awg.PARAM_REG_SIZE : (i + 1) * Awg.PARAM_REG_SIZE]
            val = int.from_bytes(val, 'little')
            self.__awg_ctrl.write_reg(addr, val)

        reply = UplPacket(UplPacket.MODE_AWG_REG_WRITE_ACK, packet.addr(), len(packet.payload()))
        self.__awg_cap_sock.sendto(reply.serialize(), reply_addr)


    def __read_cap_reg(self, packet, reply_addr):
        num_regs = packet.num_bytes() // cap.CaptureUnit.PARAM_REG_SIZE
        rd_data = bytearray()
        for i in range(num_regs):
            addr = packet.addr() + i * cap.CaptureUnit.PARAM_REG_SIZE
            val = self.__cap_ctrl.read_reg(addr)
            rd_data += val.to_bytes(cap.CaptureUnit.PARAM_REG_SIZE, 'little')

        reply = UplPacket(UplPacket.MODE_CAPTURE_REG_READ_REPLY, packet.addr(), len(rd_data), rd_data)
        self.__awg_cap_sock.sendto(reply.serialize(), reply_addr)


    def __write_cap_reg(self, packet, reply_addr):
        num_regs = packet.num_bytes() // cap.CaptureUnit.PARAM_REG_SIZE
        for i in range(num_regs):
            addr = packet.addr() + i * cap.CaptureUnit.PARAM_REG_SIZE
            val = packet.payload()[i * cap.CaptureUnit.PARAM_REG_SIZE : (i + 1) * cap.CaptureUnit.PARAM_REG_SIZE]
            val = int.from_bytes(val, 'little')
            self.__cap_ctrl.write_reg(addr, val)

        reply = UplPacket(UplPacket.MODE_CAPTURE_REG_WRITE_ACK, packet.addr(), len(packet.payload()))
        self.__awg_cap_sock.sendto(reply.serialize(), reply_addr)
