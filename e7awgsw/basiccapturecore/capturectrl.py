from __future__ import annotations

import socket
import time
import os
import stat
from types import TracebackType
from typing import cast
from typing_extensions import Self
from collections.abc import Sequence, Iterable
from abc import ABCMeta, abstractmethod
from logging import Logger
from ..logger import get_file_logger, get_null_logger, log_error, log_warning
from ..hwspec import E7AwgHwSpecs
from .hwspec import CaptureUnitSpecs
from ..hwdefs import CaptureUnit, AWG, CaptureErr, SampleDataType, E7AwgHwType
from .hwdefs import DspUnit
from ..hwparam import CaptureRamParams
from .hwparam import CaptureUnitParams
from .captureparam import CaptureParam
from ..exception import CaptureUnitTimeoutError
from .memorymap import CaptureMasterCtrlRegs, CaptureCtrlRegs, CaptureParamRegs
from ..udpaccess import CaptureRegAccess, WaveRamAccess
from ..lock import ReentrantFileLock

class CaptureCtrlBase(object, metaclass = ABCMeta):
    
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
        if enable_lib_log:
            self._loggers.append(get_file_logger())

        try:
            if self._validate_args:
                self._validate_ip_addr(ip_addr)
                self._validate_design_type(design_type)

            self._design_type = design_type
            self._cap_specs: CaptureUnitSpecs = \
                cast(CaptureUnitSpecs, E7AwgHwSpecs(self._design_type).cap_units[CaptureUnit.U0])
            self._unit_params = CaptureUnitParams.of(self._design_type)
            self._ram_params = CaptureRamParams.of(self._design_type)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def set_capture_params(self, capture_unit_id: CaptureUnit, param: CaptureParam) -> None:
        """引数で指定したキャプチャユニットにキャプチャパラメータを設定する

        Args:
            capture_unit_id (CaptureUnit): キャプチャパラメータを設定するキャプチャユニットの ID 
            param (CaptureParam): 設定するキャプチャパラメータ
        """
        if self._validate_args:
            try:
                self._validate_capture_unit_id(capture_unit_id)
                self._validate_capture_param(param)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._set_capture_params(capture_unit_id, param)


    def initialize(self, *capture_unit_id_list: CaptureUnit) -> None:
        """引数で指定したキャプチャユニットを初期化する

        Args:
            *capture_unit_id_list (CaptureUnit): 初期化するキャプチャユニットの ID
        """
        if self._validate_args:
            try:
                self._validate_capture_unit_id(*capture_unit_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._initialize(*capture_unit_id_list)


    def get_capture_data(
        self,
        capture_unit_id: CaptureUnit,
        param: CaptureParam,
    ) -> list[int] | list[tuple[int, int]]:
        """引数で指定したキャプチャユニットが保存したサンプルデータを取得する.

        | ここでは, サンプルとはキャプチャユニットに入力された生データだけでなく, 
        | 総和や二値化などの信号処理で算出される個々のデータのことも指す.

        Args:
            capture_unit_id (CaptureUnit): この ID のキャプチャユニットが保存したサンプルデータを取得する
            param (CaptureParam): capture_unit_id で指定したキャプチャユニットがキャプチャの際に使用したパラメータ

        Returns:
            list[tuple[int, int] | int]:
                | I/Q データを処理してそれぞれの相から結果が得られた場合, リストの要素は
                | I データから得られた結果 と Q データから得られた結果をこの順番で格納したタプルとなる.
                | そうでない場合, リストの要素は単一のサンプル値となる.
        """
        if self._validate_args:
            try:
                self._validate_capture_unit_id(capture_unit_id)
                self._validate_capture_param(param)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._get_capture_data(capture_unit_id, param)


    def num_captured_samples(self, capture_unit_id: CaptureUnit) -> int:
        """引数で指定したキャプチャユニットが保存したサンプル数を取得する.

        | ここでは, サンプルとはキャプチャユニットに入力された生データだけでなく, 
        | 総和や二値化などの信号処理で算出される個々のデータのことも指す.
        |
        | I/Q データを処理してそれぞれの相から結果が得られた場合, まとめて 1 サンプルとカウントする.
        
        Args:
            capture_unit_id (CaptureUnit): この ID のキャプチャユニットが保存したサンプルの個数を取得する
        
        Returns:
            int: 保存されたサンプル数
        """
        if self._validate_args:
            try:
                self._validate_capture_unit_id(capture_unit_id)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        return self._num_captured_samples(capture_unit_id)


    def start_capture_units(self, *capture_unit_id_list: CaptureUnit) -> None:
        """引数で指定したキャプチャユニットのキャプチャを開始する

        Args:
            *capture_unit_id_list (list of CaptureUnit): キャプチャを開始するキャプチャユニットの ID
        """
        if self._validate_args:
            try:
                self._validate_capture_unit_id(*capture_unit_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        self._start_capture_units(*capture_unit_id_list)


    def reset_capture_units(self, *capture_unit_id_list: CaptureUnit) -> None:
        """引数で指定したキャプチャユニットをリセットする

        Args:
            *capture_unit_id_list (list of CaptureUnit): リセットするキャプチャユニットの ID
        """
        if self._validate_args:
            try:
                self._validate_capture_unit_id(*capture_unit_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        self._reset_capture_units(*capture_unit_id_list)


    def clear_capture_stop_flags(self, *capture_unit_id_list: CaptureUnit) -> None:
        """引数で指定した全てのキャプチャユニットのキャプチャ終了フラグを下げる

        Args:
            *capture_unit_id_list (list of CaptureUnit): キャプチャ終了フラグを下げるキャプチャユニットの ID
        """
        if self._validate_args:
            try:
                self._validate_capture_unit_id(*capture_unit_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._clear_capture_stop_flags(*capture_unit_id_list)


    def set_trigger_awgs(self, capture_unit_id: CaptureUnit, *awg_id_list: AWG) -> None:
        """キャプチャユニットをスタートする AWG を選択する

        Args:
            capture_unit_id (CaptureUnit): 
                | この ID のキャプチャユニットが, awg_id_list で指定した AWG の波形送信開始に合わせてキャプチャを開始する.
            *awg_id_list (AWG):
                | キャプチャユニットのキャプチャをスタートさせる AWG の ID.
                | 複数指定した場合は, その中の何れかが波形送信を開始したタイミングでキャプチャユニットのキャプチャをスタートさせる.
        """
        if self._validate_args:
            try:
                self._validate_capture_unit_id(capture_unit_id)
                self._validate_awg_id(*awg_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._set_trigger_awgs(capture_unit_id, *awg_id_list)


    def get_trigger_awgs(self, capture_unit_id: CaptureUnit) -> set[AWG]:
        """キャプチャユニットをスタートする AWG を取得する

        Args:
            capture_unit_id (CaptureUnit): 
                | この ID のキャプチャユニットをスタートさせる AWG の ID を取得する.
        
        Returns:
            set[AWG]: capture_unit_id で指定したキャプチャユニットをスタートさせる AWG のセット
        """
        if self._validate_args:
            try:
                self._validate_capture_unit_id(capture_unit_id)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        return self._get_trigger_awgs(capture_unit_id)


    def wait_for_capture_units_to_stop(
        self, timeout: float, *capture_unit_id_list: CaptureUnit
    ) -> None:
        """引数で指定した全てのキャプチャユニットの波形の保存が終了するのを待つ

        Args:
            timeout (int or float): タイムアウト値 (単位: 秒). タイムアウトした場合, 例外を発生させる.
            *capture_unit_id_list (list of CaptureUnit): 波形の保存が終了するのを待つキャプチャユニットの ID
        
        Raises:
            CaptureUnitTimeoutError: タイムアウトした場合
        """
        if self._validate_args:
            try:
                self._validate_timeout(timeout)
                self._validate_capture_unit_id(*capture_unit_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._wait_for_capture_units_to_stop(timeout, *capture_unit_id_list)


    def wait_for_capture_units_idle(
        self, timeout: float, *capture_unit_id_list: CaptureUnit
    ) -> None:
        """引数で指定した全てのキャプチャユニットが IDLE 状態になるのを待つ

        Args:
            timeout (int or float): タイムアウト値 (単位: 秒). タイムアウトした場合, 例外を発生させる.
            *capture_unit_id_list (list of CaptureUnit): 波形の保存が終了するのを待つキャプチャユニットの ID
        
        Raises:
            CaptureUnitTimeoutError: タイムアウトした場合
        """
        if self._validate_args:
            try:
                self._validate_timeout(timeout)
                self._validate_capture_unit_id(*capture_unit_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._wait_for_capture_units_idle(timeout, *capture_unit_id_list)


    def check_err(self, *capture_unit_id_list: CaptureUnit) -> dict[CaptureUnit, list[CaptureErr]]:
        """引数で指定したキャプチャユニットのエラーをチェックする.

        エラーのあったキャプチャユニットごとにエラーの種類を返す.

        Args:
            *capture_unit_id_list (list of CaptureUnit): エラーを調べるキャプチャユニットの ID
        Returns:
            {CaptureUnit -> list of CaptureErr}:
            | key = Capture Unit ID
            | value = 発生したエラーのリスト
            | エラーが無かった場合は空の Dict.
        """
        if self._validate_args:
            try:
                self._validate_capture_unit_id(*capture_unit_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._check_err(*capture_unit_id_list)


    def design_type(self) -> E7AwgHwType:
        """このオブジェクトが制御対象とする e7awg_hw の種類を取得する.

        Returns:
            このオブジェクトが制御対象とする e7awg_hw の種類
        """
        return self._design_type


    def version(self) -> str:
        """キャプチャユニットのバージョンを取得する

        Returns:
            string: バージョンを表す文字列
        """
        return self._version()


    def _validate_ip_addr(self, ip_addr: str) -> None:
        try:
            if ip_addr != 'localhost':
                socket.inet_aton(ip_addr)
        except socket.error:
            raise ValueError(f"Invalid IP address {ip_addr}")


    def _validate_capture_unit_id(self, *capture_unit_id: CaptureUnit) -> None:
        if not CaptureUnit.on(self._design_type).issuperset(capture_unit_id):
            raise ValueError(f"Invalid capture unit ID  {capture_unit_id}")


    def _validate_capture_param(self, param: CaptureParam) -> None:
        if not isinstance(param, CaptureParam):
            raise ValueError(f"Invalid capture param  {param}")


    def _validate_addr_offset(self, addr_offset: int) -> None:
        if not isinstance(addr_offset, int):
            raise ValueError(f"The address offset must be an integer.  '{addr_offset}' was set.")


    def _validate_num_classification_results(self, num_results: int) -> None:
        if not isinstance(num_results, int):
            raise ValueError(
                f"The number of classification results must be an integer.  '{num_results}' was set.")


    def _validate_awg_id(self, *awg_id_list: AWG) -> None:
        if not AWG.on(self._design_type).issuperset(awg_id_list):
            raise ValueError(f"Invalid AWG ID  {awg_id_list}")


    def _validate_timeout(self, timeout: float) -> None:
        if (not isinstance(timeout, (int, float))) or (timeout < 0):
            raise ValueError(f"Invalid timeout value  {timeout}")


    def _validate_design_type(self, design_type: E7AwgHwType) -> None:
        if design_type != E7AwgHwType.ZCU111_DAC_6G_URAM_X2:
            raise ValueError(f"Invalid design type  {design_type}.")


    @abstractmethod
    def _set_capture_params(self, capture_unit_id: CaptureUnit, param: CaptureParam) -> None:
        pass

    @abstractmethod
    def _initialize(self, *capture_unit_id_list: CaptureUnit) -> None:
        pass

    @abstractmethod
    def _get_capture_data(
        self, capture_unit_id: CaptureUnit, param: CaptureParam,
    ) -> list[int] | list[tuple[int, int]]:
        pass

    @abstractmethod
    def _num_captured_samples(self, capture_unit_id: CaptureUnit) -> int:
        pass

    @abstractmethod
    def _start_capture_units(self, *capture_unit_id_list: CaptureUnit) -> None:
        pass

    @abstractmethod
    def _reset_capture_units(self, *capture_unit_id_list: CaptureUnit) -> None:
        pass

    @abstractmethod
    def _clear_capture_stop_flags(self, *capture_unit_id_list: CaptureUnit) -> None:
        pass

    @abstractmethod
    def _get_capture_stop_flags(self, *capture_unit_id_list: CaptureUnit) -> list[bool]:
        """キャプチャ停止フラグを取得する (デバッグ用)"""
        pass

    @abstractmethod
    def _set_trigger_awgs(self, capture_unit_id: CaptureUnit, *awg_id_list: AWG) -> None:
        pass
    
    @abstractmethod
    def _get_trigger_awgs(self, capture_unit_id: CaptureUnit) -> set[AWG]:
        pass

    @abstractmethod
    def _wait_for_capture_units_to_stop(
        self, timeout: float, *capture_unit_id_list: CaptureUnit
    ) -> None:
        pass
    
    @abstractmethod
    def _wait_for_capture_units_idle(
        self, timeout: float, *capture_unit_id_list: CaptureUnit
    ) -> None:
        pass

    @abstractmethod
    def _check_err(
        self, *capture_unit_id_list: CaptureUnit
    ) -> dict[CaptureUnit, list[CaptureErr]]:
        pass

    @abstractmethod
    def _version(self) -> str:
        pass



class CaptureCtrl(CaptureCtrlBase):

    def __init__(
        self,
        ip_addr: str,
        design_type: E7AwgHwType,
        *,
        validate_args: bool = True,
        enable_lib_log: bool = True,
        logger: Logger = get_null_logger()):
        """
        キャプチャユニットを持つ e7awg_hw 専用

        Args:
            ip_addr (string): キャプチャユニット制御モジュールに割り当てられた IP アドレス (例 '10.0.0.16')
            design_type (E7AwgHwType):
                | このオブジェクトで制御するキャプチャユニットが含まれる e7awg_hw の種類
                | キャプチャユニットを持つデザインを指定すること.
            validate_args(bool):
                | True -> 引数のチェックを行う
                | False -> 引数のチェックを行わない
            enable_lib_log (bool):
                | True -> ライブラリの標準のログ機能を有効にする.
                | False -> ライブラリの標準のログ機能を無効にする.
            logger (logging.Logger): ユーザ独自のログ出力に用いる Logger オブジェクト
        """
        super().__init__(ip_addr, design_type, validate_args, enable_lib_log, logger)
        self.__reg_access = CaptureRegAccess(ip_addr, self._unit_params.udp_port(), *self._loggers)
        self.__wave_ram_access = WaveRamAccess(
            ip_addr, self._ram_params.udp_port(), self._ram_params.word_size(), *self._loggers)
        if ip_addr == 'localhost':
            ip_addr = '127.0.0.1'
        filepath = '{}/e7capture_{}.lock'.format(
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


    def _set_capture_params(self, capture_unit_id: CaptureUnit, param: CaptureParam) -> None:
        self.__check_capture_steps(param)
        self.__check_capture_size(f"Capture unit {capture_unit_id}", param)
        self.__check_capture_delay(param.capture_delay)
        self.__check_num_sum_words(param)
        self.__check_bin_threshold(param)

        addr = CaptureParamRegs.Addr.capture(capture_unit_id)
        self.__enable_dsp_units(self.__reg_access, addr, param.dsp_list)
        self.__set_capture_data_type(self.__reg_access, addr, param.capture_data_type)
        self.__set_capture_delay(self.__reg_access, addr, param.capture_delay)
        cap_addr = self._ram_params.capture_data_addr(capture_unit_id)
        self.__set_capture_addr(self.__reg_access, addr, cap_addr)
        self.__set_capture_steps(self.__reg_access, addr, param.capture_steps)
        
        for dsp in param.dsp_list:
            if dsp == DspUnit.SUM:
                self.__set_num_sum_words(self.__reg_access, addr, param.num_sum_words)
            if dsp == DspUnit.BINARIZATION:
                self.__set_bin_thresholds(self.__reg_access, addr, param)
            if dsp == DspUnit.REDUCTION:
                self.__set_reduction_ops(self.__reg_access, addr, param)    


    def __set_capture_steps(
        self,
        accessor: CaptureRegAccess,
        addr: int,
        cap_steps: Sequence[tuple[int, int]]
    ) -> None:
        """キャプチャターゲット長とポストブランク長の設定"""
        num_sum_secs = len(cap_steps)
        accessor.write(addr, CaptureParamRegs.Offset.NUM_CAPTURE_STEPS, num_sum_secs)
        cap_target_len_list = [cap_target_len for cap_target_len, _ in cap_steps]
        accessor.multi_write(addr, CaptureParamRegs.Offset.cap_target_len(0), *cap_target_len_list)
        post_blank_len_list = [post_blank_len for _, post_blank_len in cap_steps]
        accessor.multi_write(addr, CaptureParamRegs.Offset.post_blank_len(0), *post_blank_len_list)


    def __enable_dsp_units(
        self,
        accessor: CaptureRegAccess,
        addr: int,
        dsp_list: Iterable[DspUnit]
    ) -> None:
        """DSP ユニットの有効化"""
        reg_val = 0
        for dsp in dsp_list:
            reg_val |= 1 << dsp
        accessor.write(addr, CaptureParamRegs.Offset.DSP_MODULE_ENABLE, reg_val)


    def __set_capture_data_type(
        self,
        accessor: CaptureRegAccess,
        addr: int,
        data_type: SampleDataType):
        accessor.write(addr, CaptureParamRegs.Offset.CAPTURE_DATA_TYPE, data_type)


    def __set_capture_delay(
        self,
        accessor: CaptureRegAccess,
        addr: int,
        capture_delay: int
    ) -> None:
        """キャプチャディレイの設定"""
        accessor.write(addr, CaptureParamRegs.Offset.CAPTURE_DELAY, capture_delay)


    def __set_capture_addr(
        self,
        accessor: CaptureRegAccess,
        addr: int,
        capture_addr: int
    ) -> None:
        """キャプチャアドレスの設定"""
        accessor.write(addr, CaptureParamRegs.Offset.CAPTURE_ADDR, capture_addr // 32)

    
    def __set_num_sum_words(
        self,
        accessor: CaptureRegAccess,
        addr: int,
        num_sum_words: int
    ) -> None:
        """総和ワード数の設定"""
        accessor.write(addr, CaptureParamRegs.Offset.NUM_SUM_WORDS, num_sum_words)
        

    def __set_bin_thresholds(
        self,
        accessor: CaptureRegAccess,
        addr: int,
        param: CaptureParam
    ) -> None:
        """二値化閾値の設定"""
        if param.capture_data_type == SampleDataType.IQ:
            accessor.write(
                addr, CaptureParamRegs.Offset.I_OR_REAL_BIN_THRESHOLD, param.i_bin_threshold)
            accessor.write(
                addr, CaptureParamRegs.Offset.Q_BIN_THRESHOLD, param.q_bin_threshold)
        
        elif param.capture_data_type == SampleDataType.REAL:
            accessor.write(
                addr, CaptureParamRegs.Offset.I_OR_REAL_BIN_THRESHOLD, param.real_bin_threshold)

    def __set_reduction_ops(
        self,
        accessor: CaptureRegAccess,
        addr: int,
        param: CaptureParam
    ) -> None:
        """リダクションの種類の設定"""
        if param.capture_data_type == SampleDataType.IQ:
            accessor.write(
                addr, CaptureParamRegs.Offset.I_OR_REAL_REDUCTION_OP, param.i_reduction_op)
            accessor.write(
                addr, CaptureParamRegs.Offset.Q_REDUCTION_OP, param.q_reduction_op)
        
        elif param.capture_data_type == SampleDataType.REAL:
            accessor.write(
                addr, CaptureParamRegs.Offset.I_OR_REAL_REDUCTION_OP, param.real_reduction_op)


    def _initialize(self, *capture_unit_id_list: CaptureUnit) -> None:
        self.__deselect_ctrl_target(*capture_unit_id_list)
        for capture_unit_id in capture_unit_id_list:
            self.__reg_access.write(
                CaptureCtrlRegs.Addr.capture(capture_unit_id), CaptureCtrlRegs.Offset.CTRL, 0)
            self._set_trigger_awgs(capture_unit_id)
        self.reset_capture_units(*capture_unit_id_list)
        for capture_unit_id in capture_unit_id_list:
            param = CaptureParam()
            param.add_capture_step(1, 0)
            self.set_capture_params(capture_unit_id, param)


    def _get_capture_data(
        self, capture_unit_id: CaptureUnit, param: CaptureParam,
    ) -> list[int] | list[tuple[int, int]]:
        dsp_list = param.dsp_list
        sample_size = self._unit_params.capture_sample_size(param.capture_data_type, *dsp_list)
        num_samples = self._cap_specs.num_capture_samples(param)
        data_size = (sample_size * num_samples + 7) // 8 * 8  # bits -> bytes
        wd_size = self._ram_params.word_size()
        data_size = (data_size + wd_size - 1) // wd_size * wd_size
        rd_addr = self._ram_params.capture_data_addr(capture_unit_id)
        cap_data = self.__wave_ram_access.read(rd_addr, data_size)
        is_signed = self._unit_params.is_capture_sample_signed(*dsp_list)
        if param.capture_data_type == SampleDataType.IQ:
            return self.to_iq_samples(cap_data, sample_size, num_samples, is_signed)
    
        return self.to_real_samples(cap_data, sample_size, num_samples, is_signed)


    @classmethod
    def __get_sample(cls, data: bytes, bit_start_pos: int, sample_size: int, is_signed: bool) -> int:
        bytes_start_idx = bit_start_pos // 8
        bytes_end_idx = (bit_start_pos + sample_size) // 8
        sample_bytes = data[bytes_start_idx : bytes_end_idx + 1]
        sample_val = int.from_bytes(sample_bytes, byteorder='little')
        bit_offset = bit_start_pos - bytes_start_idx * 8
        sample_val = (sample_val >> bit_offset) & ~(-1 << sample_size)
        if is_signed:
            minval = (1 << (sample_size - 1))
            sample_val = (sample_val ^ minval) - minval

        return sample_val

    
    @classmethod
    def to_iq_samples(
        cls, capture_data: bytes, iq_sample_size: int, num_samples: int, is_signed: bool
    ) -> list[tuple[int, int]]:
        """capture_data を I/Q サンプルデータに変換する"""
        samples: list[tuple[int, int]] = []
        sample_size = iq_sample_size // 2
        for i in range(num_samples):
            sample_pos = 2 * i * sample_size
            i_sample = cls.__get_sample(capture_data, sample_pos, sample_size, is_signed)
            sample_pos += sample_size
            q_sample = cls.__get_sample(capture_data, sample_pos, sample_size, is_signed)
            samples.append((i_sample, q_sample))

        return samples


    @classmethod
    def to_real_samples(
        cls, capture_data: bytes, sample_size: int, num_samples: int, is_signed: bool
    ) -> list[int]:
        """capture_data を Real サンプルデータに変換する"""
        samples: list[int] = []
        for i in range(num_samples):
            sample = cls.__get_sample(capture_data, i * sample_size, sample_size, is_signed)
            samples.append(sample)

        return samples


    def _num_captured_samples(self, capture_unit_id: CaptureUnit) -> int:
        base_addr = CaptureParamRegs.Addr.capture(capture_unit_id)
        return self.__reg_access.read(base_addr, CaptureParamRegs.Offset.NUM_CAPTURED_SAMPLES)


    def _start_capture_units(self, *capture_unit_id_list: CaptureUnit) -> None:
        with self.__flock:
            self.__select_ctrl_target(*capture_unit_id_list)
            for val in [0, 1, 0]:
                self.__reg_access.write_bits(
                    CaptureMasterCtrlRegs.ADDR,
                    CaptureMasterCtrlRegs.Offset.CTRL,
                    CaptureMasterCtrlRegs.Bit.CTRL_START,
                    1,
                    val)
            self.__deselect_ctrl_target(*capture_unit_id_list)


    def _reset_capture_units(self, *capture_unit_id_list: CaptureUnit) -> None:
        with self.__flock:
            self.__select_ctrl_target(*capture_unit_id_list)
            for val in [1, 0]:
                self.__reg_access.write_bits(
                    CaptureMasterCtrlRegs.ADDR,
                    CaptureMasterCtrlRegs.Offset.CTRL,
                    CaptureMasterCtrlRegs.Bit.CTRL_RESET,
                    1,
                    val)
                time.sleep(10e-6)
            self.__deselect_ctrl_target(*capture_unit_id_list)


    def _clear_capture_stop_flags(self, *capture_unit_id_list: CaptureUnit) -> None:
        with self.__flock:
            self.__select_ctrl_target(*capture_unit_id_list)
            for val in [0, 1, 0]:
                self.__reg_access.write_bits(
                    CaptureMasterCtrlRegs.ADDR,
                    CaptureMasterCtrlRegs.Offset.CTRL,
                    CaptureMasterCtrlRegs.Bit.CTRL_DONE_CLR,
                    1,
                    val)            
            self.__deselect_ctrl_target(*capture_unit_id_list)


    def _get_capture_stop_flags(self, *capture_unit_id_list: CaptureUnit) -> list[bool]:
        with self.__flock:
            return [
                bool(self.__reg_access.read_bits(
                    CaptureCtrlRegs.Addr.capture(capture_unit_id),
                    CaptureCtrlRegs.Offset.STATUS,
                    CaptureCtrlRegs.Bit.STATUS_DONE, 1))
                for capture_unit_id in capture_unit_id_list]

    
    def __select_ctrl_target(self, *capture_unit_id_list: CaptureUnit) -> None:
        """一括制御を有効にするキャプチャユニットを選択する"""
        with self.__flock:
            for capture_unit_id in capture_unit_id_list:
                self.__reg_access.write_bits(
                    CaptureMasterCtrlRegs.ADDR,
                    CaptureMasterCtrlRegs.Offset.CTRL_TARGET_SEL, 
                    capture_unit_id, 1, 1)


    def __deselect_ctrl_target(self, *capture_unit_id_list: CaptureUnit) -> None:
        """一括制御を無効にするキャプチャユニットを選択する"""
        with self.__flock:
            for capture_unit_id in capture_unit_id_list:
                self.__reg_access.write_bits(
                    CaptureMasterCtrlRegs.ADDR,
                    CaptureMasterCtrlRegs.Offset.CTRL_TARGET_SEL, 
                    capture_unit_id, 1, 0)


    def _set_trigger_awgs(self, capture_unit_id: CaptureUnit, *awg_id_list: AWG) -> None:
        with self.__flock:
            reg_val = 0
            for awg_id in awg_id_list:
                reg_val |= 1 << awg_id
            self.__reg_access.write(
                CaptureCtrlRegs.Addr.capture(capture_unit_id),
                CaptureCtrlRegs.Offset.START_TRIG_MASK,
                reg_val)


    def _get_trigger_awgs(self, capture_unit_id: CaptureUnit) -> set[AWG]:
        with self.__flock:
            reg_val = self.__reg_access.read(
                CaptureCtrlRegs.Addr.capture(capture_unit_id),
                CaptureCtrlRegs.Offset.START_TRIG_MASK)            
            awgs: set[AWG] = set()
            for awg in AWG.on(self._design_type):
                if reg_val | (1 << awg) != 0:
                    awgs.add(awg)

            return awgs


    def _wait_for_capture_units_to_stop(
        self, timeout: float, *capture_unit_id_list: CaptureUnit
    ) -> None:
        start = time.time()
        while True:
            all_stopped = True
            for capture_unit_id in capture_unit_id_list:
                val = self.__reg_access.read_bits(
                    CaptureCtrlRegs.Addr.capture(capture_unit_id),
                    CaptureCtrlRegs.Offset.STATUS,
                    CaptureCtrlRegs.Bit.STATUS_DONE, 1)
                if val == 0:
                    all_stopped = False
                    break
            if all_stopped:
                return

            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                msg = 'Capture unit stop timeout'
                log_error(msg, *self._loggers)
                raise CaptureUnitTimeoutError(msg)
            time.sleep(0.01)


    def _wait_for_capture_units_idle(
        self, timeout: float, *capture_unit_id_list: CaptureUnit
    ) -> None:
        start = time.time()
        while True:
            all_stopped = True
            for capture_unit_id in capture_unit_id_list:
                val = self.__reg_access.read_bits(
                    CaptureCtrlRegs.Addr.capture(capture_unit_id),
                    CaptureCtrlRegs.Offset.STATUS,
                    CaptureCtrlRegs.Bit.STATUS_BUSY, 1)
                if val == 1:
                    all_stopped = False
                    break
            if all_stopped:
                return

            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                msg = 'Capture unit idle timeout'
                log_error(msg, *self._loggers)
                raise CaptureUnitTimeoutError(msg)
            time.sleep(0.01)


    def _check_err(
        self, *capture_unit_id_list: CaptureUnit
    ) -> dict[CaptureUnit, list[CaptureErr]]:
        capture_unit_to_err = {}
        for capture_unit_id in capture_unit_id_list:
            err_list = []
            base_addr = CaptureCtrlRegs.Addr.capture(capture_unit_id)
            err = self.__reg_access.read_bits(
                base_addr, CaptureCtrlRegs.Offset.ERR, CaptureCtrlRegs.Bit.ERR_OVERFLOW, 1)
            if err == 1:
                err_list.append(CaptureErr.OVERFLOW)
            err = self.__reg_access.read_bits(
                base_addr, CaptureCtrlRegs.Offset.ERR, CaptureCtrlRegs.Bit.ERR_WRITE, 1)
            if err == 1:
                err_list.append(CaptureErr.MEM_WR)
            if err_list:
                capture_unit_to_err[capture_unit_id] = err_list
        
        return capture_unit_to_err


    def __check_capture_steps(self, param: CaptureParam) -> None:
        """キャプチャステップが正常かどうか調べる"""
        if not self.__is_in_range(
            self._cap_specs.min_capture_steps,
            self._cap_specs.max_capture_steps,
            param.num_capture_steps):
            msg = f"The number of capture steps must be between {self._cap_specs.min_capture_steps}" \
                f" and {self._cap_specs.max_capture_steps} inclusive.  " \
                f"{param.num_capture_steps} was set."
            log_error(msg, *self._loggers)
            raise ValueError(msg)
            
        for cap_target_len, post_blank_len in param.capture_steps:
            if not self.__is_in_range(
                self._cap_specs.min_capture_target_len,
                self._cap_specs.max_capture_target_len,
                cap_target_len):
                msg = f"Capture Target Length must be between {self._cap_specs.min_capture_target_len}" \
                    f" and {self._cap_specs.max_capture_target_len} inclusive.  " \
                    f"{cap_target_len} was set."
                log_error(msg, *self._loggers)
                raise ValueError(msg)
            
            if not self.__is_in_range(
                self._cap_specs.min_post_blank_len,
                self._cap_specs.max_post_blank_len,
                cap_target_len):
                msg = f"Post Blank Length must be between {self._cap_specs.min_post_blank_len}" \
                    f" and {self._cap_specs.max_post_blank_len} inclusive.  " \
                    f"{post_blank_len} was set."
                log_error(msg, *self._loggers)
                raise ValueError(msg)


    def __check_capture_size(self, target_name: str, param: CaptureParam) -> None:
        """キャプチャするサンプル数が最大値を超えていないかどうか調べる"""
        num_capture_samples = self._cap_specs.num_capture_samples(param)
        max_capture_samples = \
            self._cap_specs.max_capture_samples(param.capture_data_type, param.dsp_list)
        if num_capture_samples > max_capture_samples:
            msg = f"{target_name} has too many capture samples.  " \
                f"(max = {max_capture_samples}, setting = {num_capture_samples})"
            log_error(msg, *self._loggers)
            raise ValueError(msg)


    def __check_capture_delay(self, capture_delay: int):
        if not self.__is_in_range(
            self._cap_specs.min_capture_delay,
            self._cap_specs.max_capture_delay,
            capture_delay):
            msg = f"Capture Delay must be between {self._cap_specs.min_capture_delay}" \
                f" and {self._cap_specs.max_capture_delay} inclusive.  " \
                f"{capture_delay} was set."
            log_error(msg, *self._loggers)
            raise ValueError(msg)
        

    def __check_num_sum_words(self, param: CaptureParam):
        if not DspUnit.SUM in param.dsp_list:
            return
        
        if not self.__is_in_range(
            self._cap_specs.min_sum_words,
            self._cap_specs.max_sum_words,
            param.num_sum_words):
            msg = f"The number of words to be added up must be between {self._cap_specs.min_sum_words}" \
                f" and {self._cap_specs.max_sum_words} inclusive.  " \
                f"{param.num_sum_words} was set."
            log_error(msg, *self._loggers)
            raise ValueError(msg)


    def __check_bin_threshold(self, param: CaptureParam):
        if not DspUnit.BINARIZATION in param.dsp_list:
            return

        create_msg = lambda data_type, bin_threshold: \
            f"{data_type} Binarization Threshold must be between {self._cap_specs.min_bin_threshold}" \
            f" and {self._cap_specs.max_bin_threshold} inclusive.  " \
            f"{bin_threshold} was set."

        if param.capture_data_type == SampleDataType.IQ:
            if not self.__is_in_range(
                self._cap_specs.min_bin_threshold,
                self._cap_specs.max_bin_threshold,
                param.i_bin_threshold):
                msg = create_msg('I', param.i_bin_threshold)
                log_error(msg, *self._loggers)
                raise ValueError(msg)
    
            if not self.__is_in_range(
                self._cap_specs.min_bin_threshold,
                self._cap_specs.max_bin_threshold,
                param.q_bin_threshold):
                msg = create_msg('Q', param.q_bin_threshold)
                log_error(msg, *self._loggers)
                raise ValueError(msg)
            
        if param.capture_data_type == SampleDataType.REAL:
            if not self.__is_in_range(
                self._cap_specs.min_bin_threshold,
                self._cap_specs.max_bin_threshold,
                param.real_bin_threshold):
                msg = create_msg('Real', param.q_bin_threshold)
                log_error(msg, *self._loggers)
                raise ValueError(msg)


    def _version(self) -> str:
        data = self.__reg_access.read(CaptureMasterCtrlRegs.ADDR, CaptureMasterCtrlRegs.Offset.VERSION)
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

    @classmethod
    def __is_in_range(self, min: int, max: int, val: int) -> bool:
        return (min <= val) and (val <= max)
