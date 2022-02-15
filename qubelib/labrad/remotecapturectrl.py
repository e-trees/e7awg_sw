import sys
import pathlib
import labrad
import pickle

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from qubelib import *
from qubelib.awgctrl import AwgCaptureBase
from qubelib.logger import *


class RemoteCaptureCtrl(AwgCaptureBase):
    """ QuBE 制御サーバを通してキャプチャユニットを制御するためのクラス """

    def __init__(
        self,
        remote_server_ip_addr,
        capture_ctrl_ip_addr,
        *,
        enable_lib_log = True,
        logger = get_null_logger()):
        """
        Args:
            remote_server_ip_addr (string): QuBE 制御サーバの IP アドレス  (例 '192.168.0.2', 'localhost')
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
            self.__client = labrad.connect(remote_server_ip_addr)
            self.__handler = self.__get_capture_ctrl_handler(capture_ctrl_ip_addr)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def __get_capture_ctrl_handler(self, ip_addr):
        """サーバ上の AWG Controller のハンドラを取得する"""
        handler = self.__client.qube_server.create_capturectrl(ip_addr)
        return self.__decode_and_check(handler)


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()


    def disconnect(self):
        """QuBE 制御サーバとの接続を切り, このコントローラと関連付けられたすべてのリソースを開放する.

        | `with RemoteCaptureCtrl(...) as capturectrl` のように with ステートメント内部でこのクラスのインスタンスを生成する場合, このメソッドを明示的に呼ぶ必要はない.
        | そうでない場合, プログラムを終了する前にこのメソッドを呼ぶこと.

        """
        try:
            if self.__handler is not None:
                result = self.__client.qube_server.discard_capturectrl(self.__handler)
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


    def _set_capture_params(self, capture_unit_id, param):
        try:
            param = pickle.dumps(param)
            result = self.__client.qube_server.set_capture_params(self.__handler, capture_unit_id, param)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _initialize(self):
        try:
            result = self.__client.qube_server.initialize_capture_units(self.__handler)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _get_capture_data(self, capture_unit_id, num_samples):
        try:
            result = self.__client.qube_server.get_capture_data(
                self.__handler, capture_unit_id, num_samples)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _num_captured_samples(self, capture_unit_id):
        try:
            result = self.__client.qube_server.num_captured_samples(self.__handler, capture_unit_id)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _start_capture_units(self):
        try:
            result = self.__client.qube_server.start_capture_units(self.__handler)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _reset_capture_units(self, *capture_unit_id_list):
        try:
            result = self.__client.qube_server.reset_capture_units(self.__handler, capture_unit_id_list)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _enable_capture_units(self, *capture_unit_id_list):
        try:
            result = self.__client.qube_server.enable_capture_units(self.__handler, capture_unit_id_list)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _disable_capture_units(self, *capture_unit_id_list):
        try:
            result = self.__client.qube_server.disable_capture_units(self.__handler, capture_unit_id_list)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _select_trigger_awg(self, capture_module_id, awg_id):
        try:
            result = self.__client.qube_server.select_trigger_awg(self.__handler, capture_module_id, awg_id)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _wait_for_capture_units_to_stop(self, timeout, *capture_unit_id_list):
        try:
            timeout = pickle.dumps(timeout)
            result = self.__client.qube_server.wait_for_capture_units_to_stop(
                self.__handler, timeout, capture_unit_id_list)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _check_err(self, *capture_unit_id_list):
        try:
            result = self.__client.qube_server._check_err(self.__handler, capture_unit_id_list)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def __decode_and_check(self, data):
        data = pickle.loads(data)
        if isinstance(data, Exception):
            raise data
        return data
