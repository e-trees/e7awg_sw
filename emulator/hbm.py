import sys
import threading
import pathlib

lib_path = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(lib_path)
from e7awgsw import *
from e7awgsw.logger import *

class Hbm(object):
    """HBM をエミュレートするクラス"""

    __PAGE_SIZE = 0x2000
    __ALIGNMENT_SIZE = 32 # bytes

    def __init__(self, mem_size):
        """
        Args:
            mem_size (int): メモリサイズ
        """
        self.__mem_size = mem_size
        num_entries = mem_size // self.__PAGE_SIZE
        self.__page_list = [None] * num_entries
        self.__rlock = threading.RLock()
        self.__loggers = [get_file_logger(), get_stderr_logger()]


    def write(self, addr, data):
        """HBM にデータを書き込む

        Args:
            addr (int): 書き込みアドレス
            data (bytes): 書き込みデータ
        """
        wr_size = len(data)
        try:
            if ((addr + wr_size) >= self.__mem_size) or (addr < 0):
                raise ValueError(
                    'Tried to write outside of HBM address range.  (addr:{}, size:{})'
                    .format(addr, wr_size))
            if (addr % self.__ALIGNMENT_SIZE != 0) or (wr_size % self.__ALIGNMENT_SIZE != 0):
                raise ValueError(
                    'HBM write address and data size must be a multiple of {}.  (addr:{}, size:{})'
                    .format(self.__ALIGNMENT_SIZE, addr, wr_size))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise
        
        wr_blocks = self.__split_to_wr_block(addr, data)
        offset = addr % self.__PAGE_SIZE
        page_idx = addr // self.__PAGE_SIZE
        for wr_block in wr_blocks:
            self.__write_to_page(page_idx, offset, wr_block)
            page_idx += 1
            offset = 0


    def __split_to_wr_block(self, addr, data):
        size = len(data)
        offset = addr % self.__PAGE_SIZE
        num_blocks = (size + offset + self.__PAGE_SIZE - 1) // self.__PAGE_SIZE
        begin = 0
        end = size if (size + offset) <= self.__PAGE_SIZE else (self.__PAGE_SIZE - offset)
        wr_blocks = []
        for _ in range(num_blocks):
            wr_blocks.append(data[begin : end])
            begin = end
            end += self.__PAGE_SIZE
        
        return wr_blocks


    def __write_to_page(self, idx, offset, data):
        with self.__rlock:
            if self.__page_list[idx] is None:
                self.__page_list[idx] = bytearray([0] * self.__PAGE_SIZE)

            self.__page_list[idx][offset : offset + len(data)] = data

    def read(self, addr, size):
        """HBM からデータを読みだす

        Args:
            addr (int): 読み出しアドレス
            size (int): 読み出しバイト数
        
        Returns:
            bytearray: 読み出しデータ
        """
        try:
            if ((addr + size) >= self.__mem_size) or (addr < 0):
                raise ValueError(
                    'Tried to read outside of HBM address range.   addr:{}, size:{}'
                    .format(addr, size))
            if (addr % self.__ALIGNMENT_SIZE != 0) or (size % self.__ALIGNMENT_SIZE != 0):
                raise ValueError(
                    'HBM read address and data size must be a multiple of {}.  addr:{}, size:{}'
                    .format(self.__ALIGNMENT_SIZE, addr, size))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        rd_data = bytearray()
        start_idx = addr // self.__PAGE_SIZE
        offset = addr % self.__PAGE_SIZE
        num_entries = (offset + size + self.__PAGE_SIZE - 1) // self.__PAGE_SIZE
        for idx in range(start_idx, start_idx + num_entries):
            rd_data.extend(self.__read_from_page(idx))
        
        return rd_data[offset : size + offset]


    def __read_from_page(self, idx):
        with self.__rlock:
            if self.__page_list[idx] is None:
                return bytearray([0] * self.__PAGE_SIZE)
            
            return self.__page_list[idx]
