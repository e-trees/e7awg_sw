from __future__ import annotations

import time
import socket
import os
import stat
from types import TracebackType
from typing import Final
from typing_extensions import Self
from collections.abc import Sequence
from logging import Logger
from abc import ABCMeta, abstractmethod
from .wavesequence import WaveSequence, WaveChunk
from .hwparam import AwgParams, WaveRamParams
from .memorymap import AwgMasterCtrlRegs, AwgCtrlRegs, WaveParamRegs
from .udpaccess import AwgRegAccess, WaveRamAccess
from .exception import AwgTimeoutError
from .logger import get_file_logger, get_null_logger, log_error
from .lock import ReentrantFileLock
from .hwdefs import AWG, AwgErr, E7AwgHwType

class AwgCtrlBase(object, metaclass = ABCMeta):

    ##### 後方互換性維持のために存在しているので使用しないこと. ####
    #: [非推奨] AWG のサンプリングレート (単位=サンプル数/秒)
    SAMPLING_RATE: Final = 500000000

    def __init__(
        self,
        ip_addr: str,
        design_type: E7AwgHwType,
        validate_args: bool,
        enable_lib_log: bool,
        logger: Logger
    ) -> None:
        self._validate_args = validate_args
        self._loggers = [logger]
        self._design_type = design_type
        if enable_lib_log:
            self._loggers.append(get_file_logger())

        if self._validate_args:
            try:
                self._awg_params = AwgParams.of(design_type)
                self._ram_params = WaveRamParams.of(design_type)
                self._validate_ip_addr(ip_addr)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
    

    def set_wave_sequence(self, awg_id: AWG, wave_seq: WaveSequence) -> None:
        """ユーザ定義波形を AWG に設定する.

        Args:
            awg_id (AWG): ユーザ定義波形を設定する AWG の ID
            wave_seq (WaveSequence): 設定するユーザ定義波形
        """
        if self._validate_args:
            try:
                self._validate_awg_id(awg_id)
                self._validate_wave_sequence(wave_seq)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._set_wave_sequence(awg_id, wave_seq)


    def initialize(self, *awg_id_list: AWG) -> None:
        """引数で指定した AWG を初期化する.

        | このクラスの他のメソッドを呼び出す前に呼ぶこと.

        Args:
            *awg_id_list (list of AWG): 初期化する AWG の ID
        """
        if self._validate_args:
            try:
                self._validate_awg_id(*awg_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._initialize(*awg_id_list)


    def prepare_awgs(self, *awg_id_list: AWG) -> None:
        """引数で指定した AWG が波形を出力するための準備を行う.

        | このメソッドは, HW の外部から AWG にスタートトリガを入力する前に呼ぶことを想定している.
        | SW から AWG の波形出力を開始する際は, このメソッドを呼ばずに start_awgs だけを呼ぶこと.

        Args:
            *awg_id_list (AWG): 波形送信を開始する AWG の ID
        """
        if self._validate_args:
            try:
                self._validate_awg_id(*awg_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._prepare_awgs(*awg_id_list)   
        
        
    def start_awgs(self, *awg_id_list: AWG) -> None:
        """引数で指定した AWG の波形送信を開始する.

        Args:
            *awg_id_list (list of AWG): 波形送信を開始する AWG の ID
        """
        if self._validate_args:
            try:
                self._validate_awg_id(*awg_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._start_awgs(*awg_id_list)


    def terminate_awgs(self, *awg_id_list: AWG) -> None:
        """引数で指定した AWG を強制終了する.

        Args:
            *awg_id_list (list of AWG): 強制終了する AWG の ID
        """
        if self._validate_args:
            try:
                self._validate_awg_id(*awg_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        self._terminate_awgs(*awg_id_list)


    def reset_awgs(self, *awg_id_list: AWG) -> None:
        """引数で指定したAWGをリセットする

        Args:
            *awg_id_list (list of AWG): リセットする AWG の ID
        """
        if self._validate_args:
            try:
                self._validate_awg_id(*awg_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._reset_awgs(*awg_id_list)


    def clear_awg_stop_flags(self, *awg_id_list: AWG) -> None:
        """引数で指定した全ての AWG の波形出力終了フラグを下げる

        Args:
            *awg_id_list (list of AWG): 波形出力終了フラグを下げる AWG の ID
        """
        if self._validate_args:
            try:
                self._validate_awg_id(*awg_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._clear_awg_stop_flags(*awg_id_list)


    def wait_for_awgs_to_stop(self, timeout: float, *awg_id_list: AWG) -> None:
        """引数で指定した全ての AWG の波形の送信が終了するのを待つ

        Args:
            timeout (int or float): タイムアウト値 (単位: 秒). タイムアウトした場合, 例外を発生させる.
            *awg_id_list (list of AWG): 波形の送信が終了するのを待つ AWG の ID
        
        Raises:
            AwgTimeoutError: タイムアウトした場合
        """
        if self._validate_args:
            try:
                self._validate_timeout(timeout)
                self._validate_awg_id(*awg_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        self._wait_for_awgs_to_stop(timeout, *awg_id_list)


    def set_wave_startable_block_timing(self, interval: int, *awg_id_list: AWG) -> None:
        """引数で指定した AWG に波形を送信可能なタイミングを設定する.

        Args:
            interval (int):
                | この値の波形ブロック数ごとに波形を送信可能なタイミングが来る.
                | 単位は波形ブロック. (1 波形ブロックは 64 サンプル)
            *awg_id_list (list of AWG): 波形を送信可能なタイミングを設定する AWG の ID
        """
        if self._validate_args:
            try:
                self._validate_wave_start_interval(interval)
                self._validate_awg_id(*awg_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        self._set_wave_startable_block_timing(interval, *awg_id_list)


    def get_wave_startable_block_timing(self, *awg_id_list: AWG) -> dict[AWG, int]:
        """引数で指定した AWG から波形を送信可能なタイミングを取得する.

        Args:
            *awg_id_list (list of AWG): 波形を送信可能なタイミングを取得する AWG の ID

        Returns:
            {awg_id -> int}: 
                | key = AWG ID
                | value =  波形を送信可能なタイミング
                | 単位は波形ブロック. (1 波形ブロックは 64 サンプル)
        """
        if self._validate_args:
            try:
                self._validate_awg_id(*awg_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._get_wave_startable_block_timing(*awg_id_list)


    def check_err(self, *awg_id_list: AWG) -> dict[AWG, list[AwgErr]]:
        """引数で指定した AWG のエラーをチェックする.

        エラーのあった AWG ごとにエラーの種類を返す.

        Args:
            *awg_id_list (AWG): エラーを調べる AWG の ID

        Returns:
            {AWG -> list of AwgErr}:
            | key = AWG ID
            | value = 発生したエラーのリスト
            | エラーが無かった場合は空の dict.
        """
        if self._validate_args:
            try:
                self._validate_awg_id(*awg_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        return self._check_err(*awg_id_list)


    def sampling_rate(self) -> int:
        """AWG のサンプリングレートを取得する.

        Returns:
            AWG のサンプリングレート (単位: サンプル数/秒)
        """
        return self._sampling_rate()


    def version(self) -> str:
        """AWG のバージョンを取得する

        Returns:
            string: バージョンを表す文字列
        """
        return self._version()


    def _validate_ip_addr(self, ip_addr: str) -> None:
        try:
            if ip_addr != 'localhost':
                socket.inet_aton(ip_addr)
        except socket.error:
            raise ValueError('Invalid IP address {}'.format(ip_addr))


    def _validate_awg_id(self, *awg_id_list: AWG) -> None:
        if not AWG.on(self._design_type).issuperset(awg_id_list):
            raise ValueError('Invalid AWG ID {}'.format(awg_id_list))


    def _validate_wave_sequence(self, wave_seq: WaveSequence) -> None:
        if not isinstance(wave_seq, WaveSequence):
            raise ValueError('Invalid wave sequence {}'.format(wave_seq))
        if wave_seq.num_chunks <= 0:
            raise ValueError('A wave sequence must have at least one chunk.')


    def _validate_timeout(self, timeout: float) -> None:
        if (not isinstance(timeout, (int, float))) or (timeout < 0):
            raise ValueError('Invalid timeout {}'.format(timeout))


    def _validate_wave_start_interval(self, interval: int) -> None:
        if not (isinstance(interval, int) and (1 <= interval and interval <= 0xFFFFFFFF)):
            raise ValueError(
                "The wave start interval must be an integer between {} and {} inclusive.  '{}' was set."
                .format(1, 0xFFFFFFFF, interval))


    @abstractmethod
    def _set_wave_sequence(self, awg_id: AWG, wave_seq: WaveSequence) -> None:
        pass

    @abstractmethod
    def _initialize(self, *awg_id_list: AWG) -> None:
        pass

    @abstractmethod
    def _prepare_awgs(self, *awg_id_list: AWG) -> None:
        pass

    @abstractmethod
    def _start_awgs(self, *awg_id_list: AWG) -> None:
        pass

    @abstractmethod
    def _terminate_awgs(self, *awg_id_list: AWG) -> None:
        pass

    @abstractmethod
    def _reset_awgs(self, *awg_id_list: AWG) -> None:
        pass

    @abstractmethod
    def _clear_awg_stop_flags(self, *awg_id_list: AWG) -> None:
        pass

    @abstractmethod
    def _wait_for_awgs_to_stop(self, timeout: float, *awg_id_list: AWG) -> None:
        pass

    @abstractmethod
    def _set_wave_startable_block_timing(self, interval: int, *awg_id_list: AWG) -> None:
        pass

    @abstractmethod
    def _get_wave_startable_block_timing(self, *awg_id_list: AWG) -> dict[AWG, int]:
        pass

    @abstractmethod
    def _check_err(self, *awg_id_list: AWG) -> dict[AWG, list[AwgErr]]:
        pass

    @abstractmethod
    def _sampling_rate(self) -> int:
        pass

    @abstractmethod
    def _version(self) -> str:
        pass


class AwgCtrl(AwgCtrlBase):

    def __init__(
        self,
        ip_addr: str,
        design_type: E7AwgHwType = E7AwgHwType.SIMPLE_MULTI,
        *,
        validate_args: bool = True,
        enable_lib_log: bool = True,
        logger: Logger = get_null_logger()
    ) -> None:
        """
        Args:
            ip_addr (string): AWG 制御モジュールに割り当てられた IP アドレス (例 '10.0.0.16')
            validate_args(bool):
                | True -> 引数のチェックを行う
                | False -> 引数のチェックを行わない
            enable_lib_log (bool):
                | True -> ライブラリの標準のログ機能を有効にする.
                | False -> ライブラリの標準のログ機能を無効にする.
            logger (logging.Logger): ユーザ独自のログ出力に用いる Logger オブジェクト
        """
        super().__init__(ip_addr, design_type, validate_args, enable_lib_log, logger)
        self.__reg_access = AwgRegAccess(ip_addr, self._awg_params.udp_port(), *self._loggers)
        self.__wave_ram_access = WaveRamAccess(
            ip_addr, self._ram_params.udp_port(), self._ram_params.word_size(), *self._loggers)
        if ip_addr == 'localhost':
            ip_addr = '127.0.0.1'
        filepath = '{}/e7awg_{}.lock'.format(
            self.__get_lock_dir(), socket.inet_ntoa(socket.inet_aton(ip_addr)))
        self.__flock = ReentrantFileLock(filepath)


    def __enter__(self) -> Self:
        return self


    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None
    ) -> None:
        self.close()


    def close(self) -> None:
        """このコントローラと関連付けられたすべてのリソースを開放する.

        | このクラスのインスタンスを with 構文による後処理の対象にした場合, このメソッドを明示的に呼ぶ必要はない.
        | そうでない場合, プログラムを終了する前にこのメソッドを呼ぶこと.

        """
        try:
            self.__flock.discard()
        except Exception as e:
            log_error(e, *self._loggers)
        self.__flock = None # type: ignore
        self.__reg_access.close()
        self.__wave_ram_access.close()


    def _set_wave_sequence(self, awg_id: AWG, wave_seq: WaveSequence) -> None:
        self.__check_wave_seq_data_size(awg_id, wave_seq)
        chunk_addr_list = self.__calc_chunk_addr(awg_id, wave_seq, 0)
        addr = WaveParamRegs.Addr.awg(awg_id)
        self.__set_wave_params(self.__reg_access, addr, wave_seq, chunk_addr_list)
        self.__send_wave_samples(wave_seq, chunk_addr_list)


    def __set_wave_params(
        self,
        accessor: AwgRegAccess,
        addr: int,
        wave_seq: WaveSequence,
        chunk_addr_list: Sequence[int]
    ) -> None:
        accessor.write(addr, WaveParamRegs.Offset.NUM_WAIT_WORDS, wave_seq.num_wait_words)
        accessor.write(addr, WaveParamRegs.Offset.NUM_REPEATS, wave_seq.num_repeats)
        accessor.write(addr, WaveParamRegs.Offset.NUM_CHUNKS, wave_seq.num_chunks)

        for chunk_idx in range(wave_seq.num_chunks):
            chunk_offs = WaveParamRegs.Offset.chunk(chunk_idx)
            chunk = wave_seq.chunk(chunk_idx)
            accessor.write(
                addr, chunk_offs + WaveParamRegs.Offset.CHUNK_START_ADDR, chunk_addr_list[chunk_idx] >> 4)
            wave_part_words = chunk.num_words - chunk.num_blank_words
            accessor.write(addr, chunk_offs + WaveParamRegs.Offset.NUM_WAVE_PART_WORDS, wave_part_words)
            accessor.write(addr, chunk_offs + WaveParamRegs.Offset.NUM_BLANK_WORDS, chunk.num_blank_words)
            accessor.write(addr, chunk_offs + WaveParamRegs.Offset.NUM_CHUNK_REPEATS, chunk.num_repeats)


    def __send_wave_samples(self, wave_seq: WaveSequence, chunk_addr_list: Sequence[int]) -> None:
        for chunk_idx in range(wave_seq.num_chunks):
            if self._design_type == E7AwgHwType.KR260:
                wave_data = wave_seq.chunk(chunk_idx).wave_data.serialize_i_data()
            else:
                wave_data = wave_seq.chunk(chunk_idx).wave_data.serialize()

            self.__wave_ram_access.write(chunk_addr_list[chunk_idx], wave_data)


    def __calc_chunk_addr(
        self, awg_id: AWG, wave_seq: WaveSequence, addr_offset: int
    ) -> list[int]:
        addr_list = []
        for chunk in wave_seq.chunk_list:
            addr_list.append(self._ram_params.wave_data_addr(awg_id) + addr_offset)
            addr_offset += self.__calc_wave_chunk_data_size(chunk)
        return addr_list


    def __calc_wave_seq_data_size(self, wave_seq: WaveSequence) -> int:
        size = 0
        for chunk in wave_seq.chunk_list:
            size += self.__calc_wave_chunk_data_size(chunk)
        return size


    def __calc_wave_chunk_data_size(self, chunk: WaveChunk) -> int:
        # AWG は I データだけ出力するので 2 で割る.
        if self._design_type == E7AwgHwType.KR260:
            num_bytes = (chunk.wave_data.num_bytes // 2)
        else:
            num_bytes = chunk.wave_data.num_bytes

        wd_size = self._ram_params.word_size()
        return (num_bytes + wd_size - 1) // wd_size * wd_size


    def __check_wave_seq_data_size(self, awg_id: AWG, *wave_seq_list: WaveSequence) -> None:
        """ユーザ定義波形のサンプルデータが格納領域に収まるかチェックする"""
        size = sum([self.__calc_wave_seq_data_size(wave_seq) for wave_seq in wave_seq_list])
        if size > self._ram_params.max_size_for_wave_seq():
            msg = ("Too much RAM space is required for the wave sequence(s) for AWG {}.  ({} bytes)\n"
                   .format(awg_id, size) +
                   "The maximum RAM size for wave sequence(s) is {} bytes."
                   .format(self._ram_params.max_size_for_wave_seq()))
            log_error(msg, *self._loggers)
            raise ValueError(msg)


    def _initialize(self, *awg_id_list: AWG) -> None:
        self.__deselect_ctrl_target(*awg_id_list)
        for awg_id in awg_id_list:
            self.__reg_access.write(AwgCtrlRegs.Addr.awg(awg_id), AwgCtrlRegs.Offset.CTRL, 0)
        self.reset_awgs(*awg_id_list)
        wave_seq = WaveSequence(0, 1)
        wave_seq.add_chunk([(0,0)] * self._awg_params.smallest_unit_of_wave_len() , 0, 1)
        for awg_id in awg_id_list:
            self.set_wave_startable_block_timing(1, awg_id)
            self.set_wave_sequence(awg_id, wave_seq)


    def __select_ctrl_target(self, *awg_id_list: AWG) -> None:
        """一括制御を有効にする AWG を選択する"""
        with self.__flock:
            for awg_id in awg_id_list:
                self.__reg_access.write_bits(
                    AwgMasterCtrlRegs.ADDR,
                    AwgMasterCtrlRegs.Offset.CTRL_TARGET_SEL,
                    AwgMasterCtrlRegs.Bit.awg(awg_id), 1, 1)


    def __deselect_ctrl_target(self, *awg_id_list: AWG) -> None:
        """一括制御を無効にする AWG を選択する"""
        with self.__flock:
            for awg_id in awg_id_list:
                self.__reg_access.write_bits(
                    AwgMasterCtrlRegs.ADDR,
                    AwgMasterCtrlRegs.Offset.CTRL_TARGET_SEL,
                    AwgMasterCtrlRegs.Bit.awg(awg_id), 1, 0)


    def _prepare_awgs(self, *awg_id_list: AWG) -> None:
        with self.__flock:
            self.__select_ctrl_target(*awg_id_list)
            self.__reg_access.write_bits(
                AwgMasterCtrlRegs.ADDR, AwgMasterCtrlRegs.Offset.CTRL, AwgMasterCtrlRegs.Bit.CTRL_PREPARE, 1, 0)
            self.__reg_access.write_bits(
                AwgMasterCtrlRegs.ADDR, AwgMasterCtrlRegs.Offset.CTRL, AwgMasterCtrlRegs.Bit.CTRL_PREPARE, 1, 1)
            self.__wait_for_awgs_ready(5, *awg_id_list)
            self.__reg_access.write_bits(
                AwgMasterCtrlRegs.ADDR, AwgMasterCtrlRegs.Offset.CTRL, AwgMasterCtrlRegs.Bit.CTRL_PREPARE, 1, 0)
            self.__deselect_ctrl_target(*awg_id_list)


    def _start_awgs(self, *awg_id_list: AWG) -> None:
        with self.__flock:
            self._prepare_awgs(*awg_id_list)

            self.__select_ctrl_target(*awg_id_list)
            self.__reg_access.write_bits(
                AwgMasterCtrlRegs.ADDR, AwgMasterCtrlRegs.Offset.CTRL, AwgMasterCtrlRegs.Bit.CTRL_START, 1, 0)
            self.__reg_access.write_bits(
                AwgMasterCtrlRegs.ADDR, AwgMasterCtrlRegs.Offset.CTRL, AwgMasterCtrlRegs.Bit.CTRL_START, 1, 1)
            self.__reg_access.write_bits(
                AwgMasterCtrlRegs.ADDR, AwgMasterCtrlRegs.Offset.CTRL, AwgMasterCtrlRegs.Bit.CTRL_START, 1, 0)
            self.__deselect_ctrl_target(*awg_id_list)


    def _terminate_awgs(self, *awg_id_list: AWG) -> None:
        for awg_id in awg_id_list:
            self.__reg_access.write_bits(
                AwgCtrlRegs.Addr.awg(awg_id), AwgCtrlRegs.Offset.CTRL, AwgCtrlRegs.Bit.CTRL_TERMINATE, 1, 1)
            self.__wait_for_awgs_idle(3, awg_id)
            self.__reg_access.write_bits(
                AwgCtrlRegs.Addr.awg(awg_id), AwgCtrlRegs.Offset.CTRL, AwgCtrlRegs.Bit.CTRL_TERMINATE, 1, 0)


    def _reset_awgs(self, *awg_id_list: AWG) -> None:
        with self.__flock:
            self.__select_ctrl_target(*awg_id_list)
            self.__reg_access.write_bits(
                AwgMasterCtrlRegs.ADDR, AwgMasterCtrlRegs.Offset.CTRL, AwgMasterCtrlRegs.Bit.CTRL_RESET, 1, 1)
            time.sleep(10e-6)
            self.__reg_access.write_bits(
                AwgMasterCtrlRegs.ADDR, AwgMasterCtrlRegs.Offset.CTRL, AwgMasterCtrlRegs.Bit.CTRL_RESET, 1, 0)
            time.sleep(10e-6)
            self.__deselect_ctrl_target(*awg_id_list)


    def _clear_awg_stop_flags(self, *awg_id_list: AWG) -> None:
        with self.__flock:
            self.__select_ctrl_target(*awg_id_list)
            self.__reg_access.write_bits(
                AwgMasterCtrlRegs.ADDR, AwgMasterCtrlRegs.Offset.CTRL, AwgMasterCtrlRegs.Bit.CTRL_DONE_CLR, 1, 0)
            self.__reg_access.write_bits(
                AwgMasterCtrlRegs.ADDR, AwgMasterCtrlRegs.Offset.CTRL, AwgMasterCtrlRegs.Bit.CTRL_DONE_CLR, 1, 1)
            self.__reg_access.write_bits(
                AwgMasterCtrlRegs.ADDR, AwgMasterCtrlRegs.Offset.CTRL, AwgMasterCtrlRegs.Bit.CTRL_DONE_CLR, 1, 0)
            self.__deselect_ctrl_target(*awg_id_list)


    def _wait_for_awgs_to_stop(self, timeout: float, *awg_id_list: AWG) -> None:
        start = time.time()
        while True:
            all_stopped = True
            for awg_id in awg_id_list:
                val = self.__reg_access.read_bits(
                    AwgCtrlRegs.Addr.awg(awg_id), AwgCtrlRegs.Offset.STATUS, AwgCtrlRegs.Bit.STATUS_DONE, 1)
                if val == 0:
                    all_stopped = False
                    break
            if all_stopped:
                return

            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                msg = 'AWG stop timeout'
                log_error(msg, *self._loggers)
                raise AwgTimeoutError(msg)
            time.sleep(0.01)


    def __wait_for_awgs_ready(self, timeout: float, *awg_id_list: AWG) -> None:
        start = time.time()
        while True:
            all_ready = True
            for awg_id in awg_id_list:
                val = self.__reg_access.read_bits(
                    AwgCtrlRegs.Addr.awg(awg_id),
                    AwgCtrlRegs.Offset.STATUS,
                    AwgCtrlRegs.Bit.STATUS_READY, 1)
                if val == 0:
                    all_ready = False
                    break
            if all_ready:
                return

            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                err = AwgTimeoutError('AWG ready timed out')
                log_error(err, *self._loggers)
                raise err
            time.sleep(0.01)


    def __wait_for_awgs_idle(self, timeout: float, *awg_id_list: AWG) -> None:
        start = time.time()
        while True:
            all_idle = True
            for awg_id in awg_id_list:
                val = self.__reg_access.read_bits(
                    AwgCtrlRegs.Addr.awg(awg_id), AwgCtrlRegs.Offset.STATUS, AwgCtrlRegs.Bit.STATUS_BUSY, 1)
                if val == 1:
                    all_idle = False
                    break
            if all_idle:
                return

            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                err = AwgTimeoutError('AWG idle timed out')
                log_error(err, *self._loggers)
                raise err
            time.sleep(0.01)


    def _set_wave_startable_block_timing(self, interval: int, *awg_id_list: AWG) -> None:
        for awg_id in awg_id_list:
            self.__reg_access.write(
                WaveParamRegs.Addr.awg(awg_id), WaveParamRegs.Offset.WAVE_STARTABLE_BLOCK_INTERVAL, interval)


    def _get_wave_startable_block_timing(self, *awg_id_list: AWG) -> dict[AWG, int]:
        awg_id_to_timimg = {}
        for awg_id in awg_id_list:
            timing = self.__reg_access.read(
                WaveParamRegs.Addr.awg(awg_id), WaveParamRegs.Offset.WAVE_STARTABLE_BLOCK_INTERVAL)
            awg_id_to_timimg[awg_id] = timing
        return awg_id_to_timimg


    def _check_err(self, *awg_id_list: AWG) -> dict[AWG, list[AwgErr]]:
        awg_to_err = {}
        for awg_id in awg_id_list:
            err_list = []
            base_addr = AwgCtrlRegs.Addr.awg(awg_id)
            err = self.__reg_access.read_bits(
                base_addr, AwgCtrlRegs.Offset.ERR, AwgCtrlRegs.Bit.ERR_READ, 1)
            if err == 1:
                err_list.append(AwgErr.MEM_RD)
            err = self.__reg_access.read_bits(
                base_addr, AwgCtrlRegs.Offset.ERR, AwgCtrlRegs.Bit.ERR_SAMPLE_SHORTAGE, 1)
            if err == 1:
                err_list.append(AwgErr.SAMPLE_SHORTAGE)
            if err_list:
                awg_to_err[awg_id] = err_list
        
        return awg_to_err


    def _sampling_rate(self) -> int:
        return self._awg_params.sampling_rate()


    def _version(self) -> str:
        data = self.__reg_access.read(AwgMasterCtrlRegs.ADDR, AwgMasterCtrlRegs.Offset.VERSION)
        ver_char = chr(0xFF & (data >> 24))
        ver_year = 0xFF & (data >> 16)
        ver_month = 0xF & (data >> 12)
        ver_day = 0xFF & (data >> 4)
        ver_id = 0xF & data
        return '{}:20{:02}/{:02}/{:02}-{}'.format(ver_char, ver_year, ver_month, ver_day, ver_id)


    def __get_lock_dir(self) -> str:
        """
        ロックファイルを置くディレクトリを取得する.
        このディレクトリは環境変数 (E7AWG_HW_LOCKDIR) で指定され, アクセス権限は 777 でなければならない.
        環境変数がない場合は /usr/local/etc/e7awg_hw/lock となる.
        """
        dirpath = os.getenv('E7AWG_HW_LOCKDIR', '/usr/local/etc/e7awg_hw/lock')
        if not os.path.isdir(dirpath):
            err: OSError = FileNotFoundError(
                'Cannot find the directory for lock files.\n'
                "Create a directory '/usr/local/etc/e7awg_hw/lock' "
                "or set the E7AWG_HW_LOCKDIR environment variable to the path of another directory"
                ', and then set its permission to 777.')
            log_error(err, *self._loggers)
            raise err

        permission_flags = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO  
        if (os.stat(dirpath).st_mode & permission_flags) != permission_flags:
            err = PermissionError(
                'Set the permission of the directory for lock files to 777.  ({})'.format(dirpath))
            log_error(err, *self._loggers)
            raise err
        
        return os.path.abspath(dirpath)
