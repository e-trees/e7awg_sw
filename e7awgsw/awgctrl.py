from __future__ import annotations

import time
import socket
import os
import stat
from types import TracebackType
from typing import Final
from typing_extensions import Self
from collections.abc import Sequence, Mapping
from logging import Logger
from abc import ABCMeta, abstractmethod
from .wavesequence import WaveSequence, WaveChunk
from .hwparam import WAVE_RAM_PORT, AWG_REG_PORT, MAX_WAVE_REGISTRY_ENTRIES, WAVE_RAM_WORD_SIZE
from .memorymap import AwgMasterCtrlRegs, AwgCtrlRegs, WaveParamRegs
from .udpaccess import AwgRegAccess, WaveRamAccess, ParamRegistryAccess
from .exception import AwgTimeoutError
from .logger import get_file_logger, get_null_logger, log_error
from .lock import ReentrantFileLock
from .hwdefs import AWG, AwgErr

class AwgCtrlBase(object, metaclass = ABCMeta):
    #: AWG のサンプリングレート (単位=サンプル数/秒)
    SAMPLING_RATE: Final = 500000000
    #: 波形レジストリの最大エントリ数
    MAX_WAVE_REGISTRY_ENTRIES: Final = MAX_WAVE_REGISTRY_ENTRIES

    def __init__(    
        self,
        ip_addr: str,
        validate_args: bool,
        enable_lib_log: bool,
        logger: Logger
    ) -> None:
        self._validate_args = validate_args
        self._loggers = [logger]
        if enable_lib_log:
            self._loggers.append(get_file_logger())

        if self._validate_args:
            try:
                self._validate_ip_addr(ip_addr)
            except Exception as e:
                log_error(e, *self._loggers)
                raise


    def set_wave_sequence(self, awg_id: AWG, wave_seq: WaveSequence) -> None:
        """波形シーケンスを AWG に設定する.

        | この関数を呼んだ後で register_wave_sequences を呼ぶと, AWG に設定したデータが消えることに注意.

        Args:
            awg_id (AWG): 波形シーケンスを設定する AWG の ID
            wave_seq (WaveSequence): 設定する波形シーケンス
        """
        if self._validate_args:
            try:
                self._validate_awg_id(awg_id)
                self._validate_wave_sequence(wave_seq)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._set_wave_sequence(awg_id, wave_seq)


    def register_wave_sequences(
        self,
        awg_id: AWG,
        key_to_wave_seq: Mapping[int | None, WaveSequence]
    ) -> None:
        """awg_id で指定した AWG が持つ波形レジストリに波形シーケンスを登録する

        | 同じ awg_id で複数回呼ぶと, 前回レジストリに登録したデータが消えることに注意.
        | この関数を呼んだ後で set_wave_sequence を呼ぶと, レジストリに登録したデータが消えることに注意.

        Args:
            awg_id (AWG): 登録先の波形レジストリを持つ AWG の ID
            key_to_wave_seq ({int -> WaveSequence}):
                | 波形レジストリの登録位置を示すキーと登録する波形シーケンスの Map.
                | キーは 0 ~ 511 まで指定可能.
                | キーを None にした場合, 対応する波形シーケンスはレジストリではなく, AWG に直接セットされる.
        """
        if self._validate_args:
            try:
                if not isinstance(key_to_wave_seq, dict):
                    raise ValueError("'key_to_wave_seq' must be a dict.")
                self._validate_awg_id(awg_id)
                for key in key_to_wave_seq.keys():
                    self._validate_wave_registry_key(key)
                for wave_seq in key_to_wave_seq.values():
                    self._validate_wave_sequence(wave_seq)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        self._register_wave_sequences(awg_id, key_to_wave_seq)


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

        | JESD204C の送信カウンタと AWG の SOF カウンタがずれる可能性があるため, HW で対処するまでは呼んではならない. (2022/07/06)

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

        | AWG は出力した波形ブロックの数をカウントしており, これが interval の倍数となるブロックの先頭から波形の送信を始める.
        | (※本来このメソッドは, 全 AWG のブロックカウントを同時にリセットする機能と組み合わせて使うものであるが, 
        | リセット機能が未実装であるため, 全 AWG が同時に特定のタイミングで波形を出力するという目的のためには使えない.)

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
        if not AWG.includes(*awg_id_list):
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


    def _validate_wave_registry_key(self, key: int | None) -> None:
        if key is None:
            return
        if ((not isinstance(key, int)) or
            (key < 0)                  or
            (key >= self.MAX_WAVE_REGISTRY_ENTRIES)):
            raise ValueError(
                "The wave registry key must be 'None' or an integer between {} and {} inclusive.  '{}' was set."
                .format(0, self.MAX_WAVE_REGISTRY_ENTRIES -1, key))


    @abstractmethod
    def _set_wave_sequence(self, awg_id: AWG, wave_seq: WaveSequence) -> None:
        pass

    @abstractmethod
    def _register_wave_sequences(
        self, awg_id: AWG, key_to_wave_seq: Mapping[int | None, WaveSequence]) -> None:
        pass

    @abstractmethod
    def _initialize(self, *awg_id_list: AWG) -> None:
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
    def _version(self) -> str:
        pass


class AwgCtrl(AwgCtrlBase):

    # AWG が読み取る波形データの格納先アドレス
    __AWG_WAVE_SRC_ADDR: Final = [
        0x0,         0x20000000,  0x40000000,  0x60000000,
        0x80000000,  0xA0000000,  0xC0000000,  0xE0000000,
        0x100000000, 0x120000000, 0x140000000, 0x160000000, 
        0x180000000, 0x1A0000000, 0x1C0000000, 0x1E0000000]
    # 波形 RAM のワードサイズ (bytes)
    __WAVE_RAM_WORD_SIZE: Final = WAVE_RAM_WORD_SIZE
    # 1 波形シーケンスのサンプルデータに割り当てられる最大 RAM サイズ (bytes)
    __MAX_RAM_SIZE_FOR_WAVE_SEQUENCE: Final = 256 * 1024 * 1024
    # 波形レジストリの先頭アドレス
    __WAVE_REGISTRY_ADDR_LIST: Final = [
        0x01FF00000, 0x03FF00000, 0x05FF00000, 0x07FF00000,
        0x09FF00000, 0x0BFF00000, 0x0DFF00000, 0x0FFF00000,
        0x11FF00000, 0x13FF00000, 0x15FF00000, 0x17FF00000,
        0x19FF00000, 0x1BFF00000, 0x1DFF00000, 0x1F2000000]
    # 波形シーケンス 1 つ当たりのレジストリのサイズ (bytes)
    __WAVE_SEQ_REGISTRY_SIZE: Final = 0x400


    def __init__(
        self,
        ip_addr: str,
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
        super().__init__(ip_addr, validate_args, enable_lib_log, logger)
        self.__reg_access = AwgRegAccess(ip_addr, AWG_REG_PORT, *self._loggers)
        self.__wave_ram_access = WaveRamAccess(ip_addr, WAVE_RAM_PORT, *self._loggers)
        self.__registry_access = ParamRegistryAccess(ip_addr, WAVE_RAM_PORT, *self._loggers)
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
        self.__flock = None  # type: ignore
        self.__reg_access.close()
        self.__wave_ram_access.close()
        self.__registry_access.close()


    def _set_wave_sequence(self, awg_id: AWG, wave_seq: WaveSequence) -> None:
        self.__check_wave_seq_data_size(awg_id, wave_seq)
        chunk_addr_list = self.__calc_chunk_addr(awg_id, wave_seq, 0)
        addr = WaveParamRegs.Addr.awg(awg_id)
        self.__set_wave_params(self.__reg_access, addr, wave_seq, chunk_addr_list)
        self.__send_wave_samples(wave_seq, chunk_addr_list)

    
    def _register_wave_sequences(
        self, awg_id: AWG, key_to_wave_seq: Mapping[int | None, WaveSequence]) -> None:
        self.__check_wave_seq_data_size(awg_id, *key_to_wave_seq.values())
        addr_offset = 0
        for key, wave_seq in key_to_wave_seq.items():
            if key is None:
                self._set_wave_sequence(awg_id, wave_seq)
                continue
            
            chunk_addr_list = self.__calc_chunk_addr(awg_id, wave_seq, addr_offset)
            addr = self.__WAVE_REGISTRY_ADDR_LIST[awg_id] + self.__WAVE_SEQ_REGISTRY_SIZE * key
            self.__set_wave_params(self.__registry_access, addr, wave_seq, chunk_addr_list)
            self.__send_wave_samples(wave_seq, chunk_addr_list)
            addr_offset += self.__calc_wave_seq_data_size(wave_seq)


    def __set_wave_params(
        self,
        accessor: AwgRegAccess | ParamRegistryAccess,
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
            wave_data = wave_seq.chunk(chunk_idx).wave_data
            self.__wave_ram_access.write(chunk_addr_list[chunk_idx], wave_data.serialize())


    def __calc_chunk_addr(
        self, awg_id: AWG, wave_seq: WaveSequence, addr_offset: int
    ) -> list[int]:
        addr_list = []
        for chunk in wave_seq.chunk_list:
            addr_list.append(self.__AWG_WAVE_SRC_ADDR[awg_id] + addr_offset)
            addr_offset += self.__calc_wave_chunk_data_size(chunk)
        return addr_list


    def __calc_wave_seq_data_size(self, wave_seq: WaveSequence) -> int:
        size = 0
        for chunk in wave_seq.chunk_list:
            size += self.__calc_wave_chunk_data_size(chunk)
        return size


    def __calc_wave_chunk_data_size(self, chunk: WaveChunk) -> int:
        return ((chunk.wave_data.num_bytes + self.__WAVE_RAM_WORD_SIZE - 1) // self.__WAVE_RAM_WORD_SIZE) \
            * self.__WAVE_RAM_WORD_SIZE


    def __check_wave_seq_data_size(self, awg_id: AWG, *wave_seq_list: WaveSequence) -> None:
        """波形シーケンスのサンプルデータが格納領域に収まるかチェックする"""
        size = sum([self.__calc_wave_seq_data_size(wave_seq) for wave_seq in wave_seq_list])
        if size > self.__MAX_RAM_SIZE_FOR_WAVE_SEQUENCE:
            msg = ("Too much RAM space is required for the wave sequence(s) for AWG {}.  ({} bytes)\n"
                   .format(awg_id, size) +
                   "The maximum RAM size for wave sequence(s) is {} bytes."
                   .format(self.__MAX_RAM_SIZE_FOR_WAVE_SEQUENCE))
            log_error(msg, *self._loggers)
            raise ValueError(msg)


    def _initialize(self, *awg_id_list: AWG) -> None:
        self.__deselect_ctrl_target(*awg_id_list)
        for awg_id in awg_id_list:
            self.__reg_access.write(AwgCtrlRegs.Addr.awg(awg_id), AwgCtrlRegs.Offset.CTRL, 0)
        #self.reset_awgs(*awg_id_list)
        wave_seq = WaveSequence(0, 1)
        wave_seq.add_chunk([(0,0)] * 64, 0, 1)
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


    def _start_awgs(self, *awg_id_list: AWG) -> None:
        with self.__flock:
            self.__select_ctrl_target(*awg_id_list)
            
            self.__reg_access.write_bits(
                AwgMasterCtrlRegs.ADDR, AwgMasterCtrlRegs.Offset.CTRL, AwgMasterCtrlRegs.Bit.CTRL_PREPARE, 1, 0)
            self.__reg_access.write_bits(
                AwgMasterCtrlRegs.ADDR, AwgMasterCtrlRegs.Offset.CTRL, AwgMasterCtrlRegs.Bit.CTRL_PREPARE, 1, 1)
            self.__wait_for_awgs_ready(5, *awg_id_list)
            self.__reg_access.write_bits(
                AwgMasterCtrlRegs.ADDR, AwgMasterCtrlRegs.Offset.CTRL, AwgMasterCtrlRegs.Bit.CTRL_PREPARE, 1, 0)

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
