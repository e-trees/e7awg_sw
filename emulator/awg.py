import threading
import struct
from typing import Final, Callable, Any
from collections.abc import Sequence
from enum import IntEnum
from e7awgsw import WaveSequence, AWG
from e7awgsw.memorymap import WaveParamRegs
from e7awgsw.hwparam import WAVE_SAMPLE_SIZE
from e7awgsw.logger import get_file_logger, get_stderr_logger, log_error


class Awg:

    PARAM_REG_SIZE: Final = 4 # bytes
    __NUM_PARAM_REGS: Final = 256
    __MAX_PARAM_REG_ADDR: Final = __NUM_PARAM_REGS * PARAM_REG_SIZE

    def __init__(self, id: AWG, mem_reader: Callable[[int, int], bytearray]) -> None:
        self.__state = AwgState.IDLE
        self.__state_lock = threading.RLock()
        self.__param_regs = [0] * self.__NUM_PARAM_REGS
        self.__mem_reader = mem_reader
        self.__id = id
        self.__loggers = [get_file_logger(), get_stderr_logger()]
        self.__set_default_params()

    @property
    def id(self) -> AWG:
        return self.__id

    def assert_reset(self) -> None:
        """AWG をリセット状態にする"""
        with self.__state_lock:
            self.__state = AwgState.RESET


    def deassert_reset(self) -> None:
        """AWG のリセットを解除する"""
        with self.__state_lock:
            if self.__state == AwgState.RESET:
                self.__state = AwgState.IDLE


    def preload(self) -> None:
        """AWG の波形出力準備を行う"""
        with self.__state_lock:
            if (self.__state == AwgState.IDLE) or (self.__state == AwgState.COMPLETE):
                self.__state = AwgState.READY


    def terminate(self) -> None:
        """AWG を強制停止する"""
        with self.__state_lock:
            if (self.__state == AwgState.READY) or (self.__state == AwgState.GEN_WAVE):
                self.__state = AwgState.COMPLETE


    def set_to_idle(self) -> None:
        """AWG が complete 状態のとき IDLE 状態にする"""
        with self.__state_lock:
            if (self.__state == AwgState.COMPLETE):
                self.__state = AwgState.IDLE


    def generate_wave(self) -> tuple[bool, Sequence[tuple[int, int]]]:
        """波形を生成する"""
        with self.__state_lock:
            if self.__state != AwgState.READY:
                return (False, [])
            self.__state = AwgState.GEN_WAVE

        num_wait_words = self.get_param(WaveParamRegs.Offset.NUM_WAIT_WORDS)
        num_repeats = self.get_param(WaveParamRegs.Offset.NUM_REPEATS)
        num_chunks = self.get_param(WaveParamRegs.Offset.NUM_CHUNKS)
        wave_seq = WaveSequence(num_wait_words, num_repeats, logger = self.__loggers[1])
        for chunk_no in range(num_chunks):
            base_addr = WaveParamRegs.Offset.chunk(chunk_no)
            num_balnk_words = self.get_param(base_addr + WaveParamRegs.Offset.NUM_BLANK_WORDS)
            num_repeats = self.get_param(base_addr + WaveParamRegs.Offset.NUM_CHUNK_REPEATS)
            chunk_addr = self.get_param(base_addr + WaveParamRegs.Offset.CHUNK_START_ADDR) << 4
            num_wave_words = self.get_param(base_addr + WaveParamRegs.Offset.NUM_WAVE_PART_WORDS)
            chunk_data = self.__read_chunk(chunk_addr, num_wave_words)
            wave_seq.add_chunk(chunk_data, num_balnk_words, num_repeats)
        wave = wave_seq.all_samples_lazy(True)

        with self.__state_lock:
            if self.__state == AwgState.GEN_WAVE:
                self.__state = AwgState.COMPLETE
                return (True, wave)
        
        return (False, [])


    def __read_chunk(self, addr: int, num_words: int) -> list[tuple[int, int]]:
        rd_size = num_words * WaveSequence.NUM_SAMPLES_IN_AWG_WORD * WAVE_SAMPLE_SIZE
        rd_data = self.__mem_reader(addr, rd_size)
        half_sample_size = WAVE_SAMPLE_SIZE // 2
        num_samples = len(rd_data) // half_sample_size
        samples: Any = [rd_data[i * half_sample_size : (i + 1) * half_sample_size]
                        for i in range(num_samples)]
        samples = [struct.unpack('<h', sample)[0] for sample in samples]
        return list(zip(samples[0::2], samples[1::2]))


    def is_ready(self) -> bool:
        """AWG が ready 状態かどうか調べる"""
        return self.__state == AwgState.READY


    def is_complete(self) -> bool:
        """AWG が complete 状態かどうか調べる"""
        return self.__state == AwgState.COMPLETE


    def is_busy(self) -> bool:
        """AWG が busy 状態かどうか調べる"""
        state = self.__state
        return (state == AwgState.GEN_WAVE) or (state == AwgState.READY)


    def is_wakeup(self) -> bool:
        """AWG が wakeup 状態かどうか調べる"""
        return self.__state != AwgState.RESET


    def set_param(self, addr: int, data: int) -> None:
        """波形パラメータを設定する
        
        Args:
            addr (int): パラメータレジスタのアドレス
            data (int): 設定値
        """
        try:
            if (addr % self.PARAM_REG_SIZE != 0):
                raise ValueError(
                    ('AWG parameter register address must be a multiple of {}.  ({}, AWG_{})'
                    .format(self.PARAM_REG_SIZE, addr, self.__id)))

            if (addr < 0) or (self.__MAX_PARAM_REG_ADDR < addr):
                raise ValueError(
                    ('AWG parameter register address must be between 0x0 and 0x{:x} inclusive.  ({}, AWG_{})'
                    .format(self.__MAX_PARAM_REG_ADDR, addr, self.__id)))
            
            if (data < 0) or (0xFFFFFFFF < data):
                raise ValueError(
                    'AWG parameter register value must be between 0 and {} inclusive.  ({}, AWG_{})'
                    .format(0xFFFFFFFF, data, self.__id))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        reg_idx = addr // self.PARAM_REG_SIZE
        self.__param_regs[reg_idx] = data


    def get_param(self, addr: int) -> int:
        """波形パラメータを取得する
        
        Args:
            addr (int): パラメータレジスタのアドレス

        Returns:
            int: 波形パラメータ
        """
        try:
            if (addr % self.PARAM_REG_SIZE != 0):
                raise ValueError(
                    ('AWG parameter register address must be a multiple of {}.  ({}, AWG_{})'
                    .format(self.PARAM_REG_SIZE, addr, self.__id)))

            if (addr < 0) or (self.__MAX_PARAM_REG_ADDR < addr):
                raise ValueError(
                    ('AWG parameter register address must be between 0x0 and 0x{:x} inclusive.  ({}, AWG_{})'
                    .format(self.__MAX_PARAM_REG_ADDR, addr, self.__id)))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise
        
        reg_idx = addr // self.PARAM_REG_SIZE
        return self.__param_regs[reg_idx]


    def __set_default_params(self) -> None:
        self.set_param(WaveParamRegs.Offset.NUM_REPEATS, 1)
        self.set_param(WaveParamRegs.Offset.NUM_CHUNKS, 1)
        for chunk_no in range(WaveSequence.MAX_CHUNKS):
            chunk_base_addr = WaveParamRegs.Offset.chunk(chunk_no)
            self.set_param(chunk_base_addr + WaveParamRegs.Offset.NUM_WAVE_PART_WORDS, 16)
            self.set_param(chunk_base_addr + WaveParamRegs.Offset.NUM_CHUNK_REPEATS, 1)



class AwgState(IntEnum):
    RESET: Final = 0
    IDLE: Final  = 1
    READY: Final = 2
    GEN_WAVE: Final = 3
    COMPLETE: Final = 4
