from __future__ import annotations

import labrad # type: ignore
import pickle
from types import TracebackType
from typing_extensions import Self, Any
from e7awgsw.awgctrl import AwgCtrlBase
from e7awgsw.logger import get_null_logger, log_error
from e7awgsw import AWG, WaveSequence, AwgErr
from logging import Logger


class RemoteAwgCtrl(AwgCtrlBase):
    """ LabRAD サーバを通して AWG を制御するためのクラス """

    def __init__(
        self,
        remote_server_ip_addr: str,
        awg_ctrl_ip_addr: str,
        *,
        enable_lib_log: bool = True,
        logger: Logger = get_null_logger()
    ) -> None:
        """
        Args:
            remote_server_ip_addr (string): LabRAD サーバの IP アドレス  (例 '192.168.0.2', 'localhost')
            awg_ctrl_ip_addr (string): AWG 制御モジュールに割り当てられた IP アドレス (例 '10.0.0.16')
            enable_lib_log (bool):
                | True -> ライブラリの標準のログ機能を有効にする.
                | False -> ライブラリの標準のログ機能を無効にする.
            logger (logging.Logger): ユーザ独自のログ出力に用いる Logger オブジェクト
        """
        super().__init__(awg_ctrl_ip_addr, True, enable_lib_log, logger)
        self.__client = None
        self.__handler = None

        try:
            self._validate_ip_addr(remote_server_ip_addr)
            self.__client = labrad.connect(
                remote_server_ip_addr, password='', port=7682, tls_mode='off')
            self.__server = self.__client.awg_capture_server
            self.__handler = self.__get_awg_ctrl_handler(awg_ctrl_ip_addr)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def __get_awg_ctrl_handler(self, ip_addr: str) -> str:
        """サーバ上の AWG Controller のハンドラを取得する"""
        handler = self.__server.create_awgctrl(ip_addr)
        return self.__decode_and_check(handler)


    def __enter__(self) -> Self:
        return self


    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None
    ) -> None:
        self.disconnect()


    def disconnect(self) -> None:
        """LabRAD サーバとの接続を切り, このコントローラと関連付けられたすべてのリソースを開放する.

        | このクラスのインスタンスを with 構文による後処理の対象にした場合, このメソッドを明示的に呼ぶ必要はない.
        | そうでない場合, プログラムを終了する前にこのメソッドを呼ぶこと.

        """
        try:
            if self.__handler is not None:
                result = self.__server.discard_awgctrl(self.__handler)
                self.__decode_and_check(result)
        except Exception as e:
            # 呼び出し側で後処理の失敗から復帰させる必要はないので再スローはしない
            log_error(e, *self._loggers)

        try:
            if self.__client is not None:
                self.__client.disconnect()
        except Exception as e:
            log_error(e, *self._loggers)
        
        self.__handler = None
        self.__client = None


    def _set_wave_sequence(self, awg_id: AWG, wave_seq: WaveSequence) -> None:
        try:
            wseq = pickle.dumps(wave_seq)
            result = self.__server.set_wave_sequence(self.__handler, int(awg_id), wseq)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _initialize(self, *awg_id_list: AWG) -> None:
        try:
            awgs = [int(awg_id) for awg_id in awg_id_list]
            result = self.__server.initialize_awgs(self.__handler, awgs)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _start_awgs(self, *awg_id_list: AWG) -> None:
        try:
            awgs = [int(awg_id) for awg_id in awg_id_list]
            result = self.__server.start_awgs(self.__handler, awgs)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _terminate_awgs(self, *awg_id_list: AWG) -> None:
        try:
            awgs = [int(awg_id) for awg_id in awg_id_list]
            result = self.__server.terminate_awgs(self.__handler, awgs)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _reset_awgs(self, *awg_id_list: AWG) -> None:
        try:
            awgs = [int(awg_id) for awg_id in awg_id_list]
            result = self.__server.reset_awgs(self.__handler, awgs)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _clear_awg_stop_flags(self, *awg_id_list: AWG) -> None:
        try:
            awgs = [int(awg_id) for awg_id in awg_id_list]
            result = self.__server.clear_awg_stop_flags(self.__handler, awgs)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _wait_for_awgs_to_stop(self, timeout: float, *awg_id_list: AWG) -> None:
        try:
            to = pickle.dumps(timeout)
            awgs = [int(awg_id) for awg_id in awg_id_list]
            result = self.__server.wait_for_awgs_to_stop(self.__handler, to, awgs)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _set_wave_startable_block_timing(self, interval: int, *awg_id_list: AWG) -> None:
        try:
            itrv = pickle.dumps(interval)
            awgs = [int(awg_id) for awg_id in awg_id_list]
            result = self.__server.set_wave_startable_block_timing(self.__handler, itrv, awgs)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _get_wave_startable_block_timing(self, *awg_id_list: AWG) -> dict[AWG, int]:
        try:
            awgs = [int(awg_id) for awg_id in awg_id_list]
            result = self.__server.get_wave_startable_block_timing(self.__handler, awgs)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _check_err(self, *awg_id_list: AWG) -> dict[AWG, list[AwgErr]]:
        try:
            awgs = [int(awg_id) for awg_id in awg_id_list]
            result = self.__server.check_awg_err(self.__handler, awgs)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _version(self) -> str:
        try:
            result = self.__server.awg_version(self.__handler)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def __decode_and_check(self, data: bytes) -> Any:
        data = pickle.loads(data)
        if isinstance(data, Exception):
            raise data
        return data
