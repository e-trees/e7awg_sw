from __future__ import annotations

import time
import socket
import os
import stat
from types import TracebackType
from typing import Any
from typing_extensions import Self
from logging import Logger
from abc import ABCMeta, abstractmethod
from collections.abc import Sequence
from .doutdefs import DigitalOutTrigger, DigitalOut
from .digitaloutput import DigitalOutputDataList
from .memorymap import (
    DigitalOutMasterCtrlRegs, DigitalOutCtrlRegs, DigitalOutputDataListRegs)
from e7awgsw import E7AwgHwType
from .douterr import DigitalOutTimeoutError
from ..logger import get_file_logger, get_null_logger, log_error
from ..udpaccess import DoutRegAccess
from ..lock import ReentrantFileLock
from .doutparam import DigitalOutParams

class DigitalOutCtrllBase(object, metaclass = ABCMeta):

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
            self._dout_params = DigitalOutParams.of(design_type)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def initialize(self, *dout_id_list: DigitalOut) -> None:
        """引数で指定したディジタル出力モジュールを初期化する.

        Args:
            *dout_id_list (DigitalOut): 初期化するディジタル出力モジュールの ID
        """
        if self._validate_args:
            try:
                self._validate_dout_id(*dout_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._initialize(*dout_id_list)


    def set_output_data(self, data_list: DigitalOutputDataList, *dout_id_list: DigitalOut) -> None:
        """引数で指定したディジタル出力モジュールに出力データ設定する.

        Args:
            data_list (DigitalOutputDataList): 出力パターンを格納した DigitalOutputDataList オブジェクト
            dout_id_list (DigitalOut): 出力パターンを設定するディジタル出力モジュールの ID の リスト
        """
        if self._validate_args:
            try:
                self._validate_dout_data_list(data_list)
                self._validate_dout_id(*dout_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        self._set_output_data(data_list, *dout_id_list)


    def set_default_output_data(self, bits: int, *dout_id_list: DigitalOut) -> None:
        """引数で指定したディジタル出力モジュールにデフォルトの出力データ設定する.

        | このメソッドで指定した出力値は, ディジタル出力モジュールが動作していないときに常に出力される.
        | initialize メソッドでディジタルモジュールを初期化してもこの値は変わらない.
        | このメソッドを複数回呼び出すと, ディジタル出力モジュールは最後の呼び出しで設定した値を出力する.

        Args:
            bits (int) : デフォルトで出力されるビットデータ.  0 ~ 7 ビット目がディジタル出力ポートの電圧値に対応する.  0 が Lo で 1 が Hi.
            dout_id_list (DigitalOut): 出力パターンを設定するディジタル出力モジュールの ID の リスト
        """
        if self._validate_args:
            try:
                self._validate_default_output_data(bits)
                self._validate_dout_id(*dout_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        self._set_default_output_data(bits, *dout_id_list)


    def enable_trigger(
            self,
            trig_list: DigitalOutTrigger | Sequence[DigitalOutTrigger],
            *dout_id_list: DigitalOut
        ) -> None:
        """dout_id_list で指定したディジタル出力モジュールが trig_list で指定したトリガを受け付けるようになる.

        | トリガを受け付けるディジタル出力モジュールは Stimulus Generator の特定の動作に連動して動作する.
        | トリガの種類とディジタル出力モジュールの動作の対応は以下の通り
        |
        | DigitalOutTrigger.START
        |     ディジタル出力モジュールが Idle 状態のときに Stimulus Generator が波形出力を開始すると, 
        |     現在の設定に基づいてディジタル値の出力を開始して Active 状態になる.
        |
        | DigitalOutTrigger.RESTART
        |     ディジタル出力モジュールが Pause 状態のときに Stimulus Generator が波形出力を開始すると, 
        |     現在の設定に基づいてディジタル値の出力を最初から始めて Active 状態になる.
        | 
        | DigitalOutTrigger.PAUSE
        |     ディジタル出力モジュールが Active 状態のときに Stimulus Generator が一時停止すると, 
        |     ディジタル値の出力を中断して Pause 状態になる.
        | 
        | DigitalOutTrigger.RESUME
        |     ディジタル出力モジュールが Pause 状態のときに Stimulus Generator が動作を再開すると, 
        |     ディジタル値の出力を再開して Active 状態になる.
        
        Args:
            trig_list (DigitalOutTrigger, list of DigitalOutTrigger) :
                | ディジタル出力モジュールが受け付けるようになるトリガの種類.
                | DigitalOutTrigger のリストを指定した場合は, リスト内の全てのトリガを受け付けるようになる.

            *dout_id_list (DigitalOut) : トリガの設定を変更するディジタル出力モジュール.
        """
        triggers: Any = trig_list
        if not isinstance(triggers, Sequence): 
            triggers = [triggers]

        if self._validate_args:
            try:
                self._validate_trigger_type(*triggers)
                self._validate_dout_id(*dout_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._enable_trigger(triggers, *dout_id_list)


    def disable_trigger(
            self,
            trig_list: DigitalOutTrigger | Sequence[DigitalOutTrigger],
            *dout_id_list: DigitalOut
        ) -> None:
        """dout_id_list で指定したディジタル出力モジュールが trig_list で指定したトリガを受け付けなくなる.
        
        Args:
            trig_list (StgTrigger, list of StgTrigger) :
                | ディジタル出力モジュールが受け付けなくなるトリガの種類.
                | DigitalOutTrigger のリストを指定した場合は, リスト内の全てのトリガを受け付けなくなる.

            *dout_id_list (DigitalOut) : トリガの設定を変更するディジタル出力モジュール.
        """
        triggers: Any = trig_list
        if not isinstance(triggers, Sequence): 
            triggers = [triggers]

        if self._validate_args:
            try:
                self._validate_trigger_type(*triggers)
                self._validate_dout_id(*dout_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._disable_trigger(triggers, *dout_id_list)


    def start_douts(self, *dout_id_list: DigitalOut) -> None:
        """引数で指定したディジタル出力モジュールの動作を開始する.

        | スタートトリガの有効/無効は影響しない.

        Args:
            *dout_id_list (DigitalOut): 動作を開始するディジタル出力モジュールの ID
        """
        if self._validate_args:
            try:
                self._validate_dout_id(*dout_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._start_douts(*dout_id_list)


    def pause_douts(self, *dout_id_list: DigitalOut) -> None:
        """引数で指定したディジタル出力モジュールを一時停止させる.

        Args:
            *dout_id_list (DigitalOut): 一時停止するディジタル出力モジュールの ID
        """
        if self._validate_args:
            try:
                self._validate_dout_id(*dout_id_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        self._pause_douts(*dout_id_list)


    def resume_douts(self, *dout_id_list: DigitalOut) -> None:
        """引数で指定したディジタル出力モジュールが一時停止中であった場合, 動作を再開させる.

        Args:
            *dout_id_list (DigitalOut): 動作を再開するディジタル出力モジュールの ID
        """
        try:
            self._validate_dout_id(*dout_id_list)
        except Exception as e:
            log_error(e, *self._loggers)
            raise

        self._resume_douts(*dout_id_list)


    def restart_douts(self, *dout_id_list: DigitalOut) -> None:
        """引数で指定したディジタル出力モジュールが一時停止中であった場合, 再スタートさせる.

        | 再スタートしたディジタル出力モジュールは, 現在のディジタル値リストの先頭から出力を始める.

        Args:
            *dout_id_list (DigitalOut): 再スタートするディジタル出力モジュールの ID
        """
        try:
            self._validate_dout_id(*dout_id_list)
        except Exception as e:
            log_error(e, *self._loggers)
            raise

        self._restart_douts(*dout_id_list)


    def terminate_douts(self, *dout_id_list: DigitalOut) -> None:
        """引数で指定したディジタル出力モジュールを強制停止させる.

        Args:
            *dout_id_list (DigitalOut): 強制停止させるディジタル出力モジュールの ID
        """
        try:
            self._validate_dout_id(*dout_id_list)
        except Exception as e:
            log_error(e, *self._loggers)
            raise

        self._terminate_douts(*dout_id_list)


    def clear_dout_stop_flags(self, *dout_id_list: DigitalOut) -> None:
        """引数で指定した全てのディジタル出力モジュールの動作完了フラグを下げる

        Args:
            *dout_id_list (DigitalOut): 動作完了フラグを下げるディジタル出力モジュールの ID
        """
        try:
            self._validate_dout_id(*dout_id_list)
        except Exception as e:
            log_error(e, *self._loggers)
            raise

        self._clear_dout_stop_flags(*dout_id_list)


    def wait_for_douts_to_stop(self, timeout: float, *dout_id_list: DigitalOut) -> None:
        """引数で指定した全てのディジタル出力モジュールのディジタル値の出力が終了するのを待つ

        Args:
            timeout (int or float): タイムアウト値 (単位: 秒). タイムアウトした場合, 例外を発生させる.
            *dout_id_list (DigitalOut): ディジタル値の出力が終了するのを待つディジタル出力モジュールの ID
        
        Raises:
            DigitalOutTimeoutError: タイムアウトした場合
        """
        try:
            self._validate_timeout(timeout)
            self._validate_dout_id(*dout_id_list)
        except Exception as e:
            log_error(e, *self._loggers)
            raise

        self._wait_for_douts_to_stop(timeout, *dout_id_list)


    def version(self) -> str:
        """ディジタル出力モジュールのバージョンを取得する

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


    def _validate_dout_id(self, *dout_id_list: DigitalOut) -> None:
        if not DigitalOut.on(self._design_type).issuperset(dout_id_list):
            raise ValueError('DigitalOut ID {}'.format(dout_id_list))
    
    
    def _validate_timeout(self, timeout: float) -> None:
        if (not isinstance(timeout, (int, float))) or (timeout < 0):
            raise ValueError('Invalid timeout {}'.format(timeout))


    def _validate_trigger_type(self, *type: DigitalOutTrigger):
        if not set(DigitalOutTrigger).issuperset(type):
            raise ValueError('Invalid digital output trigger type {}'.format(type))


    def _validate_dout_data_list(self, data_list: DigitalOutputDataList) -> None:
        if not isinstance(data_list, DigitalOutputDataList):
            raise ValueError('Invalid digital output data list {}'.format(data_list))


    def _validate_default_output_data(self, val: int):
        if not isinstance(val, int):
            raise ValueError('Invalid default output value {}'.format(val))


    def _validate_design_type(self, design_type: E7AwgHwType) -> None:
        if design_type != E7AwgHwType.ZCU111:
            raise ValueError(
                "e7awg_hw ({}) doesn't have any digital output modules.".format(design_type))


    @abstractmethod
    def _initialize(self, *dout_id_list: DigitalOut) -> None:
        pass

    @abstractmethod
    def _set_output_data(
        self, data_list: DigitalOutputDataList, *dout_id_list: DigitalOut) -> None:
        pass

    @abstractmethod
    def _set_default_output_data(self, bits: int, *dout_id_list: DigitalOut) -> None:
        pass

    @abstractmethod
    def _enable_trigger(
        self, trig_list: Sequence[DigitalOutTrigger], *dout_id_list: DigitalOut) -> None:
        pass

    @abstractmethod
    def _disable_trigger(
        self, trig_list: Sequence[DigitalOutTrigger], *dout_id_list: DigitalOut) -> None:
        pass

    @abstractmethod
    def _start_douts(self, *dout_id_list: DigitalOut) -> None:
        pass

    @abstractmethod
    def _pause_douts(self, *dout_id_list: DigitalOut) -> None:
        pass

    @abstractmethod
    def _resume_douts(self, *dout_id_list: DigitalOut) -> None:
        pass

    @abstractmethod
    def _restart_douts(self, *dout_id_list: DigitalOut) -> None:
        pass

    @abstractmethod
    def _terminate_douts(self, *dout_id_list: DigitalOut) -> None:
        pass

    @abstractmethod
    def _clear_dout_stop_flags(self, *dout_id_list: DigitalOut) -> None:
        pass

    @abstractmethod
    def _wait_for_douts_to_stop(self, timeout: float, *dout_id_list: DigitalOut) -> None:
        pass

    @abstractmethod
    def _version(self) -> str:
        pass


class DigitalOutCtrl(DigitalOutCtrllBase):
    """ディジタル出力モジュールを制御するためのクラス"""

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
        ディジタル出力モジュールを持つ e7awg_hw 専用

        Args:
            ip_addr (string): ディジタル出力モジュールに割り当てられた IP アドレス (例 '10.0.0.16')
            design_type (E7AwgHwType):
                | このオブジェクトで制御する ディジタル出力モジュールが含まれる e7awg_hw の種類
                | ディジタル出力モジュールを持つデザインを指定すること.
            validate_args(bool):
                | True -> 引数のチェックを行う
                | False -> 引数のチェックを行わない
            enable_lib_log (bool):
                | True -> ライブラリの標準のログ機能を有効にする.
                | False -> ライブラリの標準のログ機能を無効にする.
            logger (logging.Logger): ユーザ独自のログ出力に用いる Logger オブジェクト
        """
        super().__init__(ip_addr, design_type, validate_args, enable_lib_log, logger)
        self.__reg_access = DoutRegAccess(ip_addr, self._dout_params.udp_port(), *self._loggers)
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


    def _initialize(self, *dout_id_list: DigitalOut) -> None:
        self.disable_trigger(list(DigitalOutTrigger), *dout_id_list)
        self.__deselect_ctrl_target(*dout_id_list)
        for dout_id in dout_id_list:
            self.__reg_access.write(
                DigitalOutCtrlRegs.Addr.dout(dout_id), DigitalOutCtrlRegs.Offset.CTRL, 0)

        self.__reset_douts(*dout_id_list)
        dout_data_list = DigitalOutputDataList(self._design_type).add(0, 2)
        self.set_output_data(dout_data_list, *dout_id_list)


    def _set_output_data(
        self, data_list: DigitalOutputDataList, *dout_id_list: DigitalOut) -> None:
        regs = []
        for i in range(len(data_list)):
            bits, time = data_list[i]
            regs.append(bits)
            regs.append(time - 1)
        
        for dout_id in dout_id_list:
            self.__reg_access.multi_write(
                DigitalOutputDataListRegs.Addr.dout(dout_id),
                DigitalOutputDataListRegs.Offset.pattern(0),
                *regs)
            self.__reg_access.write(
                DigitalOutCtrlRegs.Addr.dout(dout_id),
                DigitalOutCtrlRegs.Offset.NUM_PATTERNS,
                len(data_list))
            self.__reg_access.write(
                DigitalOutCtrlRegs.Addr.dout(dout_id),
                DigitalOutCtrlRegs.Offset.START_IDX,
                0)


    def _set_default_output_data(self, bits: int, *dout_id_list: DigitalOut) -> None:
        for dout_id in dout_id_list:
            self.__reg_access.write(
                DigitalOutputDataListRegs.Addr.dout(dout_id),
                DigitalOutputDataListRegs.Offset.DEFAULT_BIT_PATTERN,
                bits)


    def _enable_trigger(
        self, trig_list: Sequence[DigitalOutTrigger], *dout_id_list: DigitalOut) -> None:
        for trig in trig_list:
            if trig == DigitalOutTrigger.START:
                offset = DigitalOutMasterCtrlRegs.Offset.START_TRIG_MASK_0
            elif trig == DigitalOutTrigger.RESTART:
                offset = DigitalOutMasterCtrlRegs.Offset.RESTART_TRIG_MASK_0
            elif trig == DigitalOutTrigger.PAUSE:
                offset = DigitalOutMasterCtrlRegs.Offset.PAUSE_TRIG_MASK_0
            elif trig == DigitalOutTrigger.RESUME:
                offset = DigitalOutMasterCtrlRegs.Offset.RESUME_TRIG_MASK_0
            else:
                raise AssertionError('Unknown digital output trigger {}'.format(trig))

            self.__set_mask_bits(DigitalOutMasterCtrlRegs.ADDR, offset, *dout_id_list)
            

    def _disable_trigger(
        self, trig_list: Sequence[DigitalOutTrigger], *dout_id_list: DigitalOut) -> None:
        for trig in trig_list:
            if trig == DigitalOutTrigger.START:
                offset = DigitalOutMasterCtrlRegs.Offset.START_TRIG_MASK_0
            elif trig == DigitalOutTrigger.RESTART:
                offset = DigitalOutMasterCtrlRegs.Offset.RESTART_TRIG_MASK_0
            elif trig == DigitalOutTrigger.PAUSE:
                offset = DigitalOutMasterCtrlRegs.Offset.PAUSE_TRIG_MASK_0
            elif trig == DigitalOutTrigger.RESUME:
                offset = DigitalOutMasterCtrlRegs.Offset.RESUME_TRIG_MASK_0
            else:
                raise AssertionError('Unknown digital output trigger {}'.format(trig))

            self.__clear_mask_bits(DigitalOutMasterCtrlRegs.ADDR, offset, *dout_id_list)


    def _start_douts(self, *dout_id_list: DigitalOut) -> None:
        self.__select_ctrl_target(*dout_id_list)
        for val in [0, 1, 0]:
            self.__reg_access.write_bits(
                DigitalOutMasterCtrlRegs.ADDR,
                DigitalOutMasterCtrlRegs.Offset.CTRL,
                DigitalOutMasterCtrlRegs.Bit.CTRL_START,
                1, val)
        self.__deselect_ctrl_target(*dout_id_list)


    def _pause_douts(self, *dout_id_list: DigitalOut) -> None:
        self.__select_ctrl_target(*dout_id_list)
        for val in [0, 1, 0]:
            self.__reg_access.write_bits(
                DigitalOutMasterCtrlRegs.ADDR,
                DigitalOutMasterCtrlRegs.Offset.CTRL,
                DigitalOutMasterCtrlRegs.Bit.CTRL_PAUSE,
                1, val)
        self.__deselect_ctrl_target(*dout_id_list)


    def _resume_douts(self, *dout_id_list: DigitalOut) -> None:
        self.__select_ctrl_target(*dout_id_list)
        for val in [0, 1, 0]:
            self.__reg_access.write_bits(
                DigitalOutMasterCtrlRegs.ADDR,
                DigitalOutMasterCtrlRegs.Offset.CTRL,
                DigitalOutMasterCtrlRegs.Bit.CTRL_RESUME,
                1, val)
        self.__deselect_ctrl_target(*dout_id_list)


    def _restart_douts(self, *dout_id_list: DigitalOut) -> None:
        self.__select_ctrl_target(*dout_id_list)
        for val in [0, 1, 0]:
            self.__reg_access.write_bits(
                DigitalOutMasterCtrlRegs.ADDR,
                DigitalOutMasterCtrlRegs.Offset.CTRL,
                DigitalOutMasterCtrlRegs.Bit.CTRL_RESTART,
                1, val)
        self.__deselect_ctrl_target(*dout_id_list)


    def _terminate_douts(self, *dout_id_list: DigitalOut) -> None:
        for dout_id in dout_id_list:
            self.__reg_access.write_bits(
                DigitalOutCtrlRegs.Addr.dout(dout_id),
                DigitalOutCtrlRegs.Offset.CTRL,
                DigitalOutCtrlRegs.Bit.CTRL_TERMINATE,
                1, 0)
            self.__reg_access.write_bits(
                DigitalOutCtrlRegs.Addr.dout(dout_id),
                DigitalOutCtrlRegs.Offset.CTRL,
                DigitalOutCtrlRegs.Bit.CTRL_TERMINATE,
                1, 1)
            self.__wait_for_douts_idle(5, *dout_id_list)
            self.__reg_access.write_bits(
                DigitalOutCtrlRegs.Addr.dout(dout_id),
                DigitalOutCtrlRegs.Offset.CTRL,
                DigitalOutCtrlRegs.Bit.CTRL_TERMINATE,
                1, 0)

    def _clear_dout_stop_flags(self, *dout_id_list: DigitalOut) -> None:    
        self.__select_ctrl_target(*dout_id_list)
        for val in [0, 1, 0]:
            self.__reg_access.write_bits(
                DigitalOutMasterCtrlRegs.ADDR,
                DigitalOutMasterCtrlRegs.Offset.CTRL,
                DigitalOutMasterCtrlRegs.Bit.CTRL_DONE_CLR,
                1, val)
        self.__deselect_ctrl_target(*dout_id_list)


    def _wait_for_douts_to_stop(self, timeout: float, *dout_id_list: DigitalOut) -> None:
        start = time.time()
        while True:
            all_stopped = True
            for dout_id in dout_id_list:
                val = self.__reg_access.read_bits(
                    DigitalOutCtrlRegs.Addr.dout(dout_id),
                    DigitalOutCtrlRegs.Offset.STATUS,
                    DigitalOutCtrlRegs.Bit.STATUS_DONE,
                    1)
                if val == 0:
                    all_stopped = False
                    break
            if all_stopped:
                return

            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                err = DigitalOutTimeoutError('Digital output module stop timeout')
                log_error(err, *self._loggers)
                raise err
            time.sleep(0.01)


    def _version(self) -> str:
        data = self.__reg_access.read(
            DigitalOutMasterCtrlRegs.ADDR, DigitalOutMasterCtrlRegs.Offset.VERSION)
        ver_char = chr(0xFF & (data >> 24))
        ver_year = 0xFF & (data >> 16)
        ver_month = 0xF & (data >> 12)
        ver_day = 0xFF & (data >> 4)
        ver_id = 0xF & data
        return '{}:20{:02}/{:02}/{:02}-{}'.format(ver_char, ver_year, ver_month, ver_day, ver_id)


    def __select_ctrl_target(self, *dout_id_list: DigitalOut) -> None:
        """一括制御を有効にするディジタル出力モジュールを選択する"""
        self.__set_mask_bits(
            DigitalOutMasterCtrlRegs.ADDR,
            DigitalOutMasterCtrlRegs.Offset.CTRL_TARGET_SEL_0,
            *dout_id_list)


    def __deselect_ctrl_target(self, *dout_id_list: DigitalOut) -> None:
        """一括制御を無効にするディジタル出力モジュールを選択する"""
        self.__clear_mask_bits(
            DigitalOutMasterCtrlRegs.ADDR,
            DigitalOutMasterCtrlRegs.Offset.CTRL_TARGET_SEL_0,
            *dout_id_list)


    def __set_mask_bits(self, base_addr: int, offset: int, *dout_id_list: DigitalOut) -> None:
        """ビットマスクレジスタの特定のビットを 1 にする
        
        Args:
            base_addr (int): 値を変更するビットマスクレジスタのベースアドレス
            offset (int): 値を変更するビットマスクレジスタのアドレスオフセット
            *dout_id_list (DigitalOut): このリストのディジタル出力モジュールに対応するビットを全て 1 にする
        """
        reg_0, reg_1 = self.__reg_access.multi_read(base_addr, offset, 2)

        for dout_id in dout_id_list:
            bit_pos = DigitalOutMasterCtrlRegs.Bit.dout(dout_id)
            if dout_id <= DigitalOut.U31:
                reg_0 |= 1 << bit_pos
            else:
                reg_1 |= 1 << bit_pos

        self.__reg_access.multi_write(base_addr, offset, reg_0, reg_1)


    def __clear_mask_bits(self, base_addr: int, offset: int, *dout_id_list: DigitalOut) -> None:
        """ビットマスクレジスタの特定のビットを 0 にする
        
        Args:
            base_addr (int): 値を変更するビットマスクレジスタのベースアドレス
            offset (int): 値を変更するビットマスクレジスタのアドレスオフセット
            *dout_id_list (DigitalOut): このリストのディジタル出力モジュールに対応するビットを全て 0 にする
        """
        reg_0, reg_1 = self.__reg_access.multi_read(base_addr, offset, 2)

        for dout_id in dout_id_list:
            bit_pos = DigitalOutMasterCtrlRegs.Bit.dout(dout_id)
            if dout_id <= DigitalOut.U31:
                reg_0 &= 0xFFFFFFFF & (~(1 << bit_pos))
            else:
                reg_1 &= 0xFFFFFFFF & (~(1 << bit_pos))

        self.__reg_access.multi_write(base_addr, offset, reg_0, reg_1)


    def __reset_douts(self, *dout_id_list):
        self.__select_ctrl_target(*dout_id_list)
        self.__reg_access.write_bits(
            DigitalOutMasterCtrlRegs.ADDR,
            DigitalOutMasterCtrlRegs.Offset.CTRL,
            DigitalOutMasterCtrlRegs.Bit.CTRL_RESET,
            1, 1)
        time.sleep(10e-6)
        self.__reg_access.write_bits(
            DigitalOutMasterCtrlRegs.ADDR,
            DigitalOutMasterCtrlRegs.Offset.CTRL,
            DigitalOutMasterCtrlRegs.Bit.CTRL_RESET,
            1, 0)
        time.sleep(10e-6)
        self.__deselect_ctrl_target(*dout_id_list)


    def __wait_for_douts_idle(self, timeout, *dout_id_list):
        start = time.time()
        while True:
            all_idle = True
            for dout_id in dout_id_list:
                val = self.__reg_access.read_bits(
                    DigitalOutCtrlRegs.Addr.dout(dout_id),
                    DigitalOutCtrlRegs.Offset.STATUS,
                    DigitalOutCtrlRegs.Bit.STATUS_BUSY,
                    1)
                if val == 1:
                    all_idle = False
                    break
            if all_idle:
                return

            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                err = DigitalOutTimeoutError('Digital output module idle timed out')
                log_error(err, *self._loggers)
                raise err
            time.sleep(0.01)


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
