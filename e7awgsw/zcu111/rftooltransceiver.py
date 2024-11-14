from __future__ import annotations

import socket
from typing import Final
from typing_extensions import Self
from types import TracebackType
from logging import Logger
from .rftinterface import RftoolInterface
from ..logger import get_file_logger, get_null_logger, log_error


class RftoolTransceiver:
    """ZCU111 上で動作する FPGA 制御プログラム (rftool-mod) との通信インタフェースを提供するクラス."""

    # rftool-mod が listen する TCP ポート
    __RFTOOL_CTRL_TCP_PORT: Final = 8081
    __RFTOOL_DATA_TCP_PORT: Final = 8082

    def __init__(
        self,
        ip_addr: str,
        timeout: float,
        *,
        validate_args: bool = True,
        enable_lib_log: bool = True,
        logger: Logger = get_null_logger()
    ) -> None:
        """
        Args:
            ip_addr (string): ZCU111 に割り当てられた IP アドレス (例 '192.168.1.3')
            timeout (float): ZCU111 との通信時に適用されるタイムアウト時間. (単位: second)
            validate_args(bool):
                | True -> 引数のチェックを行う
                | False -> 引数のチェックを行わない
            enable_lib_log (bool):
                | True -> ライブラリの標準のログ機能を有効にする.
                | False -> ライブラリの標準のログ機能を無効にする.
            logger (logging.Logger): ユーザ独自のログ出力に用いる Logger オブジェクト
        """
        self._loggers = [logger]
        if enable_lib_log:
            self._loggers.append(get_file_logger())

        if validate_args:
            try:
                self._validate_ip_addr(ip_addr)
                self._validate_timeout(timeout)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        if ip_addr == 'localhost':
            ip_addr = '127.0.0.1'

        self.__ip_addr = ip_addr
        self.__ctrl_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__ctrl_sock.settimeout(timeout)
        self.__data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__data_sock.settimeout(timeout)
        self.__ctrl_if = RftoolInterface(*self._loggers)
        self.__ctrl_if.attach_socket(self.__ctrl_sock)
        self.__is_connection_established = False
        self.__connect(ip_addr)


    def __connect(self, address: str) -> None:
        try:
            # Ctrl ポートと Data ポートの両方に接続しないと, rftool-mod はコマンド受付可能な状態にならない.
            self.__data_sock.connect((address, self.__RFTOOL_DATA_TCP_PORT))
            self.__ctrl_sock.connect((address, self.__RFTOOL_CTRL_TCP_PORT))
            self.__is_connection_established = True
        except Exception as e:
            log_error(e, *self._loggers)
            raise

    def __enter__(self) -> Self:
        return self


    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None
    ) -> None:
        self.close()


    @property
    def ctrl_if(self) -> RftoolInterface:
        """通信インタフェース"""
        return self.__ctrl_if


    @property
    def ip_addr(self) -> str:
        return self.__ip_addr


    def close(self) -> None:
        """このコントローラと関連付けられたすべてのリソースを開放する.

        | このクラスのインスタンスを with 構文による後処理の対象にした場合, このメソッドを明示的に呼ぶ必要はない.
        | そうでない場合, プログラムを終了する前にこのメソッドを呼ぶこと.

        """
        if self.__is_connection_established and (not self.__ctrl_if.err_connection):
            self.__ctrl_if.put("disconnect")
            self.__ctrl_sock.shutdown(socket.SHUT_RDWR)

        self.__ctrl_sock.close()


    def _validate_ip_addr(self, ip_addr: str) -> None:
        try:
            if ip_addr != 'localhost':
                socket.inet_aton(ip_addr)
        except socket.error:
            raise ValueError('Invalid IP address {}'.format(ip_addr))
        

    def _validate_timeout(self, timeout: float) -> None:
        if not (isinstance(timeout, (float, int)) and 0 <= timeout):
            raise ValueError('Invalid timeout value {}'.format(timeout))
