from __future__ import annotations

import labrad # type: ignore
import pickle
from types import TracebackType
from typing_extensions import Self, Any
from collections.abc import Sequence
from e7awgsw import SequencerCmd, SequencerErr, SequencerCmdErr
from e7awgsw.sequencerctrl import SequencerCtrlBase
from e7awgsw.logger import get_null_logger, log_error
from logging import Logger

class RemoteSequencerCtrl(SequencerCtrlBase):
    """ LabRAD サーバを通してシーケンサを制御するためのクラス """

    def __init__(
        self,
        remote_server_ip_addr: str,
        sequencer_ip_addr: str,
        *,
        enable_lib_log: bool = True,
        logger: Logger = get_null_logger()
    ) -> None:
        """
        Args:
            remote_server_ip_addr (string): LabRAD サーバの IP アドレス  (例 '192.168.0.2', 'localhost')
            sequencer_ip_addr (string): シーケンサに割り当てられた IP アドレス (例 '10.0.0.16')
            enable_lib_log (bool):
                | True -> ライブラリの標準のログ機能を有効にする.
                | False -> ライブラリの標準のログ機能を無効にする.
            logger (logging.Logger): ユーザ独自のログ出力に用いる Logger オブジェクト
        """
        super().__init__(sequencer_ip_addr, True, enable_lib_log, logger)
        self.__client = None
        self.__handler = None

        try:
            self._validate_ip_addr(remote_server_ip_addr)
            self.__client = labrad.connect(
                remote_server_ip_addr, password='', port=7682, tls_mode='off')
            self.__server = self.__client.awg_capture_server
            self.__handler = self.__get_sequencer_ctrl_handler(sequencer_ip_addr)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def __get_sequencer_ctrl_handler(self, ip_addr: str) -> str:
        """サーバ上のシーケンサコントローラのハンドラを取得する"""
        handler = self.__server.create_sequencerctrl(ip_addr)
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
                result = self.__server.discard_sequencerctrl(self.__handler)
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


    def _initialize(self) -> None:
        try:
            result = self.__server.initialize_sequencer(self.__handler)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _push_commands(self, cmd_list: Sequence[SequencerCmd] | SequencerCmd) -> None:
        try:
            cmds = pickle.dumps(cmd_list)
            result = self.__server.push_commands(self.__handler, cmds)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _start_sequencer(self) -> None:
        try:
            result = self.__server.start_sequencer(self.__handler)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _terminate_sequencer(self) -> None:
        try:
            result = self.__server.terminate_sequencer(self.__handler)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _clear_commands(self) -> None:
        try:
            result = self.__server.clear_commands(self.__handler)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _clear_unsent_cmd_err_reports(self) -> None:
        try:
            result = self.__server.clear_unsent_cmd_err_reports(self.__handler)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _clear_sequencer_stop_flag(self) -> None:
        try:
            result = self.__server.clear_sequencer_stop_flag(self.__handler)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _enable_cmd_err_report(self) -> None:
        try:
            result = self.__server.enable_cmd_err_report(self.__handler)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _disable_cmd_err_report(self) -> None:
        try:
            result = self.__server.disable_cmd_err_report(self.__handler)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _wait_for_sequencer_to_stop(self, timeout: float) -> None:
        try:
            to = pickle.dumps(timeout)
            result = self.__server.wait_for_sequencer_to_stop(self.__handler, to)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _num_unprocessed_commands(self) -> int:
        try:
            result = self.__server.num_unprocessed_commands(self.__handler)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _num_stored_commands(self) -> int:
        try:
            result = self.__server.num_stored_commands(self.__handler)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _num_successful_commands(self) -> int:
        try:
            result = self.__server.num_successful_commands(self.__handler)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _num_err_commands(self) -> int:
        try:
            result = self.__server.num_err_commands(self.__handler)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _num_unsent_cmd_err_reports(self) -> int:
        try:
            result = self.__server.num_unsent_cmd_err_reports(self.__handler)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise

    
    def _cmd_fifo_free_space(self) -> int:
        try:
            result = self.__server.cmd_fifo_free_space(self.__handler)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _check_err(self) -> list[SequencerErr]:
        try:
            result = self.__server.check_sequencer_err(self.__handler)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _pop_cmd_err_reports(self) -> list[SequencerCmdErr]:
        try:
            result = self.__server.pop_cmd_err_reports(self.__handler)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _cmd_counter(self) -> int:
        try:
            result = self.__server.cmd_counter(self.__handler)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise
        

    def _reset_cmd_counter(self) -> None:
        try:
            result = self.__server.reset_cmd_counter(self.__handler)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise

    
    def _get_branch_flag(self) -> bool:
        try:
            result = self.__server.get_branch_flag(self.__handler)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _set_branch_flag(self, val: bool) -> None:
        try:
            result = self.__server.set_branch_flag(self.__handler, val)
            self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _get_external_branch_flag(self) -> bool:
        try:
            result = self.__server.get_external_branch_flag(self.__handler)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def _version(self) -> str:
        try:
            result = self.__server.sequencer_version(self.__handler)
            return self.__decode_and_check(result)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def __decode_and_check(self, data: bytes) -> Any:
        data = pickle.loads(data)
        if isinstance(data, Exception):
            raise data
        return data
