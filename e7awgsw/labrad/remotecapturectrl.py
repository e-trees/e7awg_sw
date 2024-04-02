from __future__ import annotations

import labrad # type: ignore
import pickle
from typing_extensions import Self, Any
from types import TracebackType
from collections.abc import Sequence
from logging import Logger
from e7awgsw import CaptureUnit, CaptureParam, CaptureModule, AWG, CaptureErr
from e7awgsw.capturectrl import CaptureCtrlBase
from e7awgsw.logger import get_null_logger, log_error

class RemoteCaptureCtrl(CaptureCtrlBase):
    """ LabRAD サーバを通してキャプチャユニットを制御するためのクラス """

    def __init__(
        self,
        remote_server_ip_addr: str,
        capture_ctrl_ip_addr: str,
        *,
        enable_lib_log: bool = True,
        logger: Logger = get_null_logger()
    ) -> None:
        """
        Args:
            remote_server_ip_addr (string): LabRAD サーバの IP アドレス  (例 '192.168.0.2', 'localhost')
            capture_ctrl_ip_addr (string): キャプチャユニット制御モジュールに割り当てられた IP アドレス (例 '10.0.0.16')
            enable_lib_log (bool):
                | True -> ライブラリの標準のログ機能を有効にする.
                | False -> ライブラリの標準のログ機能を無効にする.
            logger (logging.Logger): ユーザ独自のログ出力に用いる Logger オブジェクト
        """
        super().__init__(capture_ctrl_ip_addr, True, enable_lib_log, logger)
        self.__client = None
        self.__handler = None

        try:
            self._validate_ip_addr(remote_server_ip_addr)
            self.__client = labrad.connect(
                remote_server_ip_addr, password='', port=7682, tls_mode='off')
            self.__server = self.__client.awg_capture_server
            self.__handler = self.__get_capture_ctrl_handler(capture_ctrl_ip_addr)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def __get_capture_ctrl_handler(self, ip_addr: str) -> str:
        """サーバ上の AWG Controller のハンドラを取得する"""
        handler = self.__server.create_capturectrl(ip_addr)
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
                result = self.__server.discard_capturectrl(self.__handler)
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


    def _set_capture_params(self, capture_unit_id: CaptureUnit, param: CaptureParam) -> None:
        try:
            cap_unit = int(capture_unit_id)
            cap_param = pickle.dumps(param)
            result = self.__server.set_capture_params(self.__handler, cap_unit, cap_param)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _register_capture_params(self, key: int, param: CaptureParam) -> None:
        try:
            reg_key = pickle.dumps(key)
            cap_param = pickle.dumps(param)
            result = self.__server.register_capture_params(self.__handler, reg_key, cap_param)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _initialize(self, *capture_unit_id_list: CaptureUnit) -> None:
        try:
            cap_units = [int(capture_unit_id) for capture_unit_id in capture_unit_id_list]
            result = self.__server.initialize_capture_units(self.__handler, cap_units)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _get_capture_data(
        self, capture_unit_id: CaptureUnit, num_samples: int, addr_offset: int
    ) -> list[tuple[float, float]]:
        try:
            cap_unit = int(capture_unit_id)
            n_samples = pickle.dumps(num_samples)
            addr_ofst = pickle.dumps(addr_offset)
            result = self.__server.get_capture_data(self.__handler, cap_unit, n_samples, addr_ofst)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _get_classification_results(
        self, capture_unit_id: CaptureUnit, num_samples: int, addr_offset: int
    ) -> Sequence[int]:
        try:
            cap_unit = int(capture_unit_id)
            n_samples = pickle.dumps(num_samples)
            addr_ofst = pickle.dumps(addr_offset)
            result = self.__server.get_classification_results(
                self.__handler, cap_unit, n_samples, addr_ofst)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _num_captured_samples(self, capture_unit_id: CaptureUnit) -> int:
        try:
            cap_unit = int(capture_unit_id)
            result = self.__server.num_captured_samples(self.__handler, cap_unit)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _start_capture_units(self, *capture_unit_id_list: CaptureUnit) -> None:
        try:
            cap_units = [int(capture_unit_id) for capture_unit_id in capture_unit_id_list]
            result = self.__server.start_capture_units(self.__handler, cap_units)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _reset_capture_units(self, *capture_unit_id_list: CaptureUnit) -> None:
        try:
            cap_units = [int(capture_unit_id) for capture_unit_id in capture_unit_id_list]
            result = self.__server.reset_capture_units(self.__handler, cap_units)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _clear_capture_stop_flags(self, *capture_unit_id_list: CaptureUnit) -> None:
        try:
            cap_units = [int(capture_unit_id) for capture_unit_id in capture_unit_id_list]
            result = self.__server.clear_capture_stop_flags(self.__handler, cap_units)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _select_trigger_awg(self, capture_module_id: CaptureModule, awg_id: AWG | None) -> None:
        try:
            cap_mod = int(capture_module_id)
            awg = pickle.dumps(awg_id)
            result = self.__server.select_trigger_awg(self.__handler, cap_mod, awg)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _wait_for_capture_units_to_stop(
        self, timeout: float, *capture_unit_id_list: CaptureUnit
    ) -> None:
        try:
            to = pickle.dumps(timeout)
            cap_units = [int(capture_unit_id) for capture_unit_id in capture_unit_id_list]
            result = self.__server.wait_for_capture_units_to_stop(self.__handler, to, cap_units)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _check_err(
        self, *capture_unit_id_list: CaptureUnit
    ) -> dict[CaptureUnit, list[CaptureErr]]:
        try:
            cap_units = [int(capture_unit_id) for capture_unit_id in capture_unit_id_list]
            result = self.__server.check_capture_unit_err(self.__handler, cap_units)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _enable_start_trigger(self, *capture_unit_id_list: CaptureUnit) -> None:
        try:
            cap_units = [int(capture_unit_id) for capture_unit_id in capture_unit_id_list]
            result = self.__server.enable_start_trigger(self.__handler, cap_units)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _disable_start_trigger(self, *capture_unit_id_list: CaptureUnit) -> None:
        try:
            cap_units = [int(capture_unit_id) for capture_unit_id in capture_unit_id_list]
            result = self.__server.disable_start_trigger(self.__handler, cap_units)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _enable_dsp(self) -> None:
        try:
            result = self.__server.enable_dsp(self.__handler)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _disable_dsp(self) -> None:
        try:
            result = self.__server.disable_dsp(self.__handler)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _version(self) -> str:
        try:
            result = self.__server.capture_unit_version(self.__handler)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def __decode_and_check(self, data: bytes) -> Any:
        data = pickle.loads(data)
        if isinstance(data, Exception):
            raise data
        return data
