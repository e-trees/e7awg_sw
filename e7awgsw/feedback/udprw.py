import logging
import socket
from threading import Lock
from typing import Final, Tuple
from e7awgsw.feedback.uplpacketbuffer import UplPacket, UplPacketBuffer, UplPacketMode

logger = logging.getLogger(__name__)


class UdpRw(object):
    _MAX_PKT_SIZE: Final[int] = 65536  # Bytes
    _ABSOLUTE_MAX_RW_SIZE: Final[int] = 1440  # Bytes
    _DEFAULT_TIMEOUT: Final[float] = 2  # sec

    def __init__(self, *,
                 ip_addr: str,
                 port: int,
                 wr_mode_id: UplPacketMode,
                 rd_mode_id: UplPacketMode,
                 min_rw_size: int,
                 max_rw_size: int = _ABSOLUTE_MAX_RW_SIZE,
                 top_address: int = 0,
                 bottom_address: int,
                 timeout: float = _DEFAULT_TIMEOUT):
        # networking
        self.__dest_addrport: Tuple[str, int] = (ip_addr, port)
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.settimeout(timeout)
        self.__sock.bind((get_my_ip_addr(ip_addr), 0))  # TODO:

        # data handling
        self.__min_rw_size = min_rw_size
        self.__wr_mode_id = wr_mode_id
        self.__rd_mode_id = rd_mode_id
        self._top_address = top_address
        self._bottom_address = bottom_address
        if max_rw_size <= 0:
            raise ValueError(f"invalid max_raw_size: {max_rw_size}")
        self._max_rw_size = (self._ABSOLUTE_MAX_RW_SIZE // self.__min_rw_size) * self.__min_rw_size
        if self._max_rw_size == 0:
            raise ValueError(f"invalid min_rw_size: {min_rw_size}")
        if self._max_rw_size != max_rw_size:
            logger.info("max_rw_size is limited to {self._max_rw_size} due to word constraints")
        self.buf: UplPacketBuffer = UplPacketBuffer(num_max_payload_bytes=self._max_rw_size)  # transmit buffer

        # control
        self._lock = Lock()

    def _floor_aligned(self, v: int):
        return (v // self.__min_rw_size) * self.__min_rw_size

    def _roundup_aligned(self, v: int):
        return ((v + self.__min_rw_size - 1) // self.__min_rw_size) * self.__min_rw_size

    def _check_address_validity(self, a: int):
        return self._top_address <= a < self._bottom_address

    def _validate_sender(self, addrport):
        # TODO: implement it!
        return True

    def write(self, addr: int, data: memoryview) -> None:
        with self._lock:
            self._write(addr, data)

    def _write(self, addr: int, data: memoryview) -> None:
        if len(data) == 0:
            logger.warning(f"writing 0 byte data to address {addr:010x}, do nothing.")
            return

        wr_addr_start = self._floor_aligned(addr)
        wr_addr_end = self._roundup_aligned(addr + len(data))
        if not (self._check_address_validity(wr_addr_start) and self._check_address_validity(wr_addr_end - 1)):
            raise ValueError(f"trying to access invalid address range: {wr_addr_start:010x} -- {wr_addr_end:010x}")

        wr_size = wr_addr_end - wr_addr_start
        ofst = addr - wr_addr_start
        apdx = wr_addr_end - (addr + len(data))
        logger.debug(f"ofst = {ofst}, apdx = {apdx}")

        pos = 0
        wr_addr = wr_addr_start
        n = (wr_size + self._max_rw_size - 1) // self._max_rw_size
        for i in range(0, n):
            use_read_afer_write: bool = (i == 0 and ofst > 0) or (i == n - 1 and apdx > 0)
            size0: int = min(wr_size, self._max_rw_size)
            self.buf.init(UplPacketMode.WAVE_RAM_WRITE, wr_addr, size0)
            # logger.debug(f"i = {i}/{n}, wr_addr = {wr_addr}, wr_size = {wr_size}, use_raw = {use_read_afer_write}")

            if use_read_afer_write:
                head0 = 0
                tail0 = size0

                if i == 0 and ofst > 0:
                    self._recv_data(
                        wr_addr_start,
                        self.__min_rw_size,
                        self.buf.payload,
                        0,
                        0
                    )
                    head0 += ofst

                if i == n - 1 and apdx > 0:
                    # note: avoiding read the same memory line twice.
                    if wr_addr_end - self.__min_rw_size > wr_addr_start:
                        self._recv_data(
                            wr_addr_end - self.__min_rw_size,
                            self.__min_rw_size,
                            self.buf.payload[wr_size - self.__min_rw_size:],
                            0,
                            0
                        )
                    tail0 -= apdx

                # logger.debug(f"head0 = {head0}, tail0 = {tail0}, pos = {pos}")
                self.buf.payload[head0:tail0] = data[pos:pos + (tail0 - head0)]  # NOTE: Copy! (hard to avoid)
                self._send_data()
                pos += (tail0 - head0)
            else:
                self.buf.payload[:] = data[pos:pos+size0]  # NOTE: Copy!
                self._send_data()
                pos += size0

            wr_addr += size0
            wr_size -= size0

    def _send_data(self):
        try:
            self.__sock.sendto(self.buf.serialize(), self.__dest_addrport)
            while True:
                recv_data, recv_addr = self.__sock.recvfrom(self._MAX_PKT_SIZE)
                if self._validate_sender(recv_addr):
                    break
            send_rpl = UplPacket(recv_data)
            if not send_rpl.validate(self.buf.mode, self.buf.address, self.buf.num_payload_bytes):
                err_msg = self._gen_err_msg('upl read err', recv_addr, self.buf, send_rpl)
                raise ValueError(err_msg)
        except socket.timeout as e:
            logger.error(e)
            raise
        except Exception as e:
            logger.error(e)
            raise

    def read(self, addr: int, size: int) -> bytearray:
        with self._lock:
            return self._read(addr, size)

    def _read(self, addr: int, size: int) -> bytearray:
        if size < 0:
            raise ValueError(f"invalid size to read: {size}")
        if size == 0:
            logger.warning(f"reading 0 byte data from address {addr:010x}, do noting actually.")
            return bytearray(0)

        rd_addr_start = self._floor_aligned(addr)
        rd_addr_end = self._roundup_aligned(addr + size)
        if not (self._check_address_validity(rd_addr_start) and self._check_address_validity(rd_addr_end - 1)):
            raise ValueError(f"trying to access invalid address range: {rd_addr_start:010x} -- {rd_addr_end:010x}")

        rd_data = bytearray(size)
        rd_data_view = memoryview(rd_data)

        rd_size = rd_addr_end - rd_addr_start
        ofst = addr - rd_addr_start
        apdx = rd_addr_end - (addr + size)

        logger.debug(
            f"rd_addr = {rd_addr_start:010x}:{rd_addr_end:010x}, rd_size = {rd_size}, ofst = {ofst}, apdx = {apdx}"
        )

        pos = 0
        rd_addr = rd_addr_start
        n = (rd_size + self._max_rw_size - 1) // self._max_rw_size
        for i in range(0, n):
            size0 = min(rd_size, self._max_rw_size)
            head0 = ofst if i == 0 else 0
            tail0 = size0 - (apdx if i == n - 1 else 0)
            pos += self._recv_data(rd_addr, size0, rd_data_view[pos:], head0, tail0)
            rd_addr += size0
            rd_size -= size0

        return rd_data

    def _recv_data(self, addr: int, size: int, buf: memoryview, head: int, tail: int) -> int:
        # logger.debug(f"_recv_data: addr = {addr}, size = {size}, head = {head}, tail = {tail}")
        try:
            read_req = UplPacketBuffer(num_max_payload_bytes=0)
            read_req.init(self.__rd_mode_id, addr, size)
            self.__sock.sendto(read_req.serialize(), self.__dest_addrport)
            while True:
                recv_pkt, recv_addr = self.__sock.recvfrom(self._MAX_PKT_SIZE)
                if self._validate_sender(recv_addr):
                    break
            read_rpl = UplPacket(recv_pkt)
            if not read_rpl.validate(read_req.mode, addr, size):
                err_msg = self._gen_err_msg('upl read err', recv_addr, read_req, read_rpl)
                raise ValueError(err_msg)
        except socket.timeout as e:
            logger.error(f"{e}, destination: {self.__dest_addrport}")
            raise
        except Exception as e:
            logger.error(e)
            raise

        buf[0:tail - head] = read_rpl.payload[head:tail]
        return tail - head

    def _gen_err_msg(
            self,
            summary: str,
            device_ip_addr: Tuple[str, int],
            req: UplPacketBuffer,
            rpl: UplPacket) -> str:
        msg = f"{summary}\n" \
              f"  Server IP / Port : {self.__sock.getsockname()}\n" \
              f"  Target IP / Port : {self.__dest_addrport}\n" \
              f"  Device IP / Port : {device_ip_addr}\n" \
              f"  request mode: {req.mode}, reply mode: {rpl.mode}\n" \
              f"  recv data : {rpl.payload if rpl.has_payload() else b''}\n" \
              f"  expected addr : {req.address}, expected data len : {req.num_payload_bytes}\n" \
              f"  actual addr   : {rpl.address}, actual_data_len   : {rpl.num_payload_bytes}\n"
        return msg

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
