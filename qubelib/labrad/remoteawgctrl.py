import sys
import pathlib
import labrad
import pickle

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from qubelib import *
from qubelib.awgctrl import AwgCtrlBase
from qubelib.logger import *


class RemoteAwgCtrl(AwgCtrlBase):
    """ QuBE 制御サーバを通して AWG を制御するためのクラス """

    def __init__(
        self,
        remote_server_ip_addr,
        awg_ctrl_ip_addr,
        *,
        enable_lib_log = True,
        logger = get_null_logger()):
        """
        Args:
            remote_server_ip_addr (string): QuBE 制御サーバの IP アドレス  (例 '192.168.0.2', 'localhost')
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
            self.__client = labrad.connect(remote_server_ip_addr)
            self.__handler = self.__get_awg_ctrl_handler(awg_ctrl_ip_addr)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def __get_awg_ctrl_handler(self, ip_addr):
        """サーバ上の AWG Controller のハンドラを取得する"""
        handler = self.__client.qube_server.create_awgctrl(ip_addr)
        return self.__decode_and_check(handler)


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()


    def disconnect(self):
        """QuBE 制御サーバとの接続を切り, このコントローラと関連付けられたすべてのリソースを開放する.

        | `with RemoteAwgCtrl(...) as awgctrl` のように with ステートメント内部でこのクラスのインスタンスを生成する場合, このメソッドを明示的に呼ぶ必要はない.
        | そうでない場合, プログラムを終了する前にこのメソッドを呼ぶこと.

        """
        try:
            if self.__handler is not None:
                result = self.__client.qube_server.discard_awgctrl(self.__handler)
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


    def _set_wave_sequence(self, awg_id, wave_seq):
        try:
            wave_seq = pickle.dumps(wave_seq)
            result = self.__client.qube_server.set_wave_sequence(self.__handler, awg_id, wave_seq)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _initialize(self):
        try:
            result = self.__client.qube_server.initialize_awgs(self.__handler)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _enable_awgs(self, *awg_id_list):
        try:
            result = self.__client.qube_server.enable_awgs(self.__handler, awg_id_list)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _disable_awgs(self, *awg_id_list):
        try:
            result = self.__client.qube_server.disable_awgs(self.__handler, awg_id_list)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _get_awg_enabled(self):
        try:
            result = self.__client.qube_server.get_awg_enabled(self.__handler)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _start_awgs(self):
        try:
            result = self.__client.qube_server.start_awgs(self.__handler)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _terminate_awgs(self, *awg_id_list):
        try:
            result = self.__client.qube_server.terminate_awgs(self.__handler, awg_id_list)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _reset_awgs(self, *awg_id_list):
        try:
            result = self.__client.qube_server.reset_awgs(self.__handler, awg_id_list)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _wait_for_awgs_to_stop(self, timeout, *awg_id_list):
        try:
            timeout = pickle.dumps(timeout)
            result = self.__client.qube_server.wait_for_awgs_to_stop(self.__handler, timeout, awg_id_list)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _set_wave_startable_block_timing(self, interval, *awg_id_list):
        try:
            interval = pickle.dumps(interval)
            result = self.__client.qube_server.set_wave_startable_block_timing(
                self.__handler, interval, awg_id_list)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _get_wave_startable_block_timing(self, *awg_id_list):
        try:
            result = self.__client.qube_server.get_wave_startable_block_timing(self.__handler, awg_id_list)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _check_err(self, *awg_id_list):
        try:
            result = self.__client.qube_server.check_awg_err(self.__handler, awg_id_list)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def __decode_and_check(self, data):
        data = pickle.loads(data)
        if isinstance(data, Exception):
            raise data
        return data
