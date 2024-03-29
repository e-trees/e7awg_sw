from __future__ import annotations

import time
import socket
from types import TracebackType
from typing_extensions import Self
from abc import ABCMeta, abstractmethod
from deprecated import deprecated
from collections.abc import Sequence
from logging import Logger
from .logger import get_file_logger, get_null_logger, log_error
from .hwparam import CMD_ERR_REPORT_SIZE, SEQUENCER_REG_PORT, SEQUENCER_CMD_PORT
from .udpaccess import SequencerRegAccess, SequencerCmdSender, CmdErrReceiver, UdpRouter, get_my_ip_addr
from .uplpacket import UplPacket
from .memorymap import SequencerCtrlRegs as SeqRegs
from .sequencercmd import SequencerCmd, SequencerCmdErr
from .exception import TooLittleFreeSpaceInCmdFifoError, SequencerTimeoutError
from .hwdefs import SequencerErr

class SequencerCtrlBase(object, metaclass = ABCMeta):

    def __init__(
        self,
        ip_addr: str,
        validate_args: bool,
        enable_lib_log: bool,
        logger: Logger
    ) -> None:
        self._ip_addr = ip_addr
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


    def initialize(self) -> None:
        """シーケンサを初期化する

        | このクラスの他のメソッドを呼び出す前に呼ぶこと.
        """
        self._initialize()


    def push_commands(self, cmd_list: Sequence[SequencerCmd] | SequencerCmd) -> None:
        """シーケンサにコマンドを追加する

        | コマンドキューに cmd_list のための十分な空き領域がない場合, 例外を投げる.
        | このとき cmd_list のコマンドは 1 つも追加されない.

        Args:
            cmd_list (list of SequencerCmd): シーケンサに追加するコマンド

        Raises:
            TooLittleFreeSpaceInCmdFifoError: コマンドキューの空き領域が足りない
        """
        if self._validate_args:
            try:
                self._validate_seq_cmds(cmd_list)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        if isinstance(cmd_list, SequencerCmd):
            cmd_list = [cmd_list]

        self._push_commands(cmd_list)

    
    def start_sequencer(self) -> None:
        """シーケンサのコマンドの処理を開始する"""
        self._start_sequencer()


    def terminate_sequencer(self) -> None:
        """シーケンサを強制停止させる

        | 実行中のコマンドは途中で終了する.  途中で終了したコマンドは, 処理に失敗したコマンドとしてカウントされる.
        """
        self._terminate_sequencer()


    @deprecated(reason='You should use "clear_commands"')
    def clear_unprocessed_commands(self) -> None:
        """コマンドキューのコマンドをすべて削除する (非推奨)
        
        | このメソッドを呼ぶとコマンドカウンタ (コマンドキューの中で次に実行するコマンドの位置を指すポインタ) が
        | コマンドキューの先頭に移動する.
        """
        self._clear_commands()


    def clear_commands(self) -> None:
        """コマンドキューのコマンドをすべて削除する
        
        | このメソッドを呼ぶとコマンドカウンタ (コマンドキューの中で次に実行するコマンドの位置を指すポインタ) が
        | コマンドキューの先頭に移動する.
        """
        self._clear_commands()


    def clear_unsent_cmd_err_reports(self) -> None:
        """シーケンサにある未送信のコマンドエラーレポートをすべて削除する"""
        self._clear_unsent_cmd_err_reports()


    def clear_sequencer_stop_flag(self) -> None:
        """シーケンサのコマンド処理終了フラグを下げる"""
        self._clear_sequencer_stop_flag()


    def enable_cmd_err_report(self) -> None:
        """コマンドエラーの送信機能を有効化する"""
        self._enable_cmd_err_report()


    def disable_cmd_err_report(self) -> None:
        """コマンドエラーの送信機能を無効化する"""
        self._disable_cmd_err_report()


    def wait_for_sequencer_to_stop(self, timeout: float) -> None:
        """シーケンサのコマンドの処理が終了するのを待つ

        | シーケンサのコマンドの処理が終了するのは, シーケンサ停止フラグが有効なコマンドを実行した場合と,
        | シーケンサを強制停止した場合である.

        Args:
            timeout (int or float): タイムアウト値 (単位: 秒). タイムアウトした場合, 例外を発生させる.
        
        Raises:
            SequencerTimeoutError: タイムアウトした場合
        """
        if self._validate_args:
            try:
                self._validate_timeout(timeout)
            except Exception as e:
                log_error(e, *self._loggers)
                raise

        self._wait_for_sequencer_to_stop(timeout)


    def num_unprocessed_commands(self) -> int:
        """シーケンサが次に実行するコマンドからコマンドキューの末尾のコマンドまでのコマンド数を取得する
        
        Returns:
            int: シーケンサが次に実行するコマンドからコマンドキューの末尾のコマンドまでのコマンド数
        """
        return self._num_unprocessed_commands()


    def num_successful_commands(self) -> int:
        """シーケンサのコマンドの処理開始から現在までに, コマンドの処理に成功した回数を取得する

        | この数は, シーケンサのコマンドの処理を開始するたびに 0 に戻る.
        
        Returns:
            int: コマンドの処理に成功した回数
        """
        return self._num_successful_commands()


    def num_err_commands(self) -> int:
        """シーケンサのコマンドの処理開始から現在までに, コマンドの処理に失敗した回数を取得する

        | この数は, シーケンサのコマンドの処理を開始するたびに 0 に戻る.
        
        Returns:
            int: コマンドの処理に失敗した回数
        """
        return self._num_err_commands()


    def num_unsent_cmd_err_reports(self) -> int:
        """未送信のコマンドエラーレポートの数を取得する
        
        Returns:
            int: 未送信のコマンドエラーレポートの数
        """
        return self._num_unsent_cmd_err_reports()


    def cmd_fifo_free_space(self) -> int:
        """コマンドキューの空き領域を取得する

        Returns:
            int: コマンドキューの空き領域 (Bytes)
        """
        return self._cmd_fifo_free_space()


    def check_err(self) -> list[SequencerErr]:
        """シーケンサのエラーをチェックし, エラーに応じた列挙子のリストを返す.

        Returns:
            list of SequencerErr: 発生したエラーのリスト. エラーが無かった場合は空のリスト.
        """
        return self._check_err()


    def pop_cmd_err_reports(self) -> list[SequencerCmdErr]:
        """シーケンサから送られたコマンドエラーレポートを取得する.

        | 古いレポートから順に戻り値のリストに格納される.
        | 取得したレポートは, このオブジェクトの管理から外れる.
        
        Returns:
            list of SequencerCmdErr: 
                | シーケンサから送られたコマンドエラーレポートのリスト.
                | コマンドエラーレポートがない場合は, 空のリスト
        """
        return self._pop_cmd_err_reports()


    def get_branch_flag(self) -> bool:
        """シーケンサが実行する分岐コマンドの条件フラグを取得する

        Returns:
            bool: 分岐コマンドの条件フラグ.
        """
        return self._get_branch_flag()


    def set_branch_flag(self, val: bool) -> None:
        """シーケンサが実行する分岐コマンドの条件フラグを設定する

        Args:
            val (bool):
                | False : 分岐コマンドの分岐が成立しない.
                | True : 分岐コマンドの分岐が成立する.
        """
        if self._validate_args:
            try:
                self._validate_flag(val)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        self._set_branch_flag(val)


    def version(self) -> str:
        """シーケンサのバージョンを取得する

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


    def _validate_seq_cmds(self, cmd_list: Sequence[SequencerCmd] | SequencerCmd) -> None:
        if isinstance(cmd_list, SequencerCmd):
            return

        if not isinstance(cmd_list, Sequence):
            raise('Invalid sequencer command list.  ({})'.format(cmd_list))

        for cmd in cmd_list:
            if not isinstance(cmd, SequencerCmd):
                raise('Invalid sequencer command list.  ({})'.format(cmd_list))


    def _validate_timeout(self, timeout: float) -> None:
        if (not isinstance(timeout, (int, float))) or (timeout < 0):
            raise ValueError('Invalid timeout {}'.format(timeout))


    def _validate_flag(self, flag: bool) -> None:
        if (not isinstance(flag, bool)):
            raise ValueError('Invalid flag {}'.format(flag))

    @abstractmethod
    def _initialize(self) -> None:
        pass

    @abstractmethod
    def _push_commands(self, cmd_list: Sequence[SequencerCmd]) -> None:
        pass

    @abstractmethod
    def _start_sequencer(self) -> None:
        pass

    @abstractmethod
    def _terminate_sequencer(self) -> None:
        pass

    @abstractmethod
    def _clear_commands(self) -> None:
        pass

    @abstractmethod
    def _clear_unsent_cmd_err_reports(self) -> None:
        pass

    @abstractmethod
    def _clear_sequencer_stop_flag(self) -> None:
        pass

    @abstractmethod
    def _enable_cmd_err_report(self) -> None:
        pass

    @abstractmethod
    def _disable_cmd_err_report(self) -> None:
        pass
    
    @abstractmethod
    def _wait_for_sequencer_to_stop(self, timeout: float) -> None:
        pass

    @abstractmethod
    def _num_unprocessed_commands(self) -> int:
        pass

    @abstractmethod
    def _num_stored_commands(self) -> int:
        """コマンドキューにあるコマンドの数を取得する"""
        pass

    @abstractmethod
    def _num_successful_commands(self) -> int:
        pass

    @abstractmethod
    def _num_err_commands(self) -> int:
        pass

    @abstractmethod
    def _num_unsent_cmd_err_reports(self) -> int:
        pass

    @abstractmethod
    def _cmd_fifo_free_space(self) -> int:
        pass

    @abstractmethod
    def _check_err(self) -> list[SequencerErr]:
        pass

    @abstractmethod
    def _pop_cmd_err_reports(self) -> list[SequencerCmdErr]:
        pass

    @abstractmethod
    def _cmd_counter(self) -> int:
        """コマンドカウンタの値を取得する"""
        pass

    @abstractmethod
    def _reset_cmd_counter(self) -> None:
        """コマンドカウンタの値を0にする"""
        pass

    @abstractmethod
    def _get_branch_flag(self) -> bool:
        pass

    @abstractmethod
    def _set_branch_flag(self, val: bool) -> None:
        pass

    @abstractmethod
    def _get_external_branch_flag(self) -> bool:
        """シーケンサの外部から入力される分岐フラグの値を取得する"""
        pass

    @abstractmethod
    def _version(self) -> str:
        pass


class SequencerCtrl(SequencerCtrlBase):
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
            ip_addr (string): シーケンサに割り当てられた IP アドレス (例 '10.0.0.16')
            validate_args(bool):
                | True -> 引数のチェックを行う
                | False -> 引数のチェックを行わない
            enable_lib_log (bool):
                | True -> ライブラリの標準のログ機能を有効にする.
                | False -> ライブラリの標準のログ機能を無効にする.
            logger (logging.Logger): ユーザ独自のログ出力に用いる Logger オブジェクト
        """
        super().__init__(ip_addr, validate_args, enable_lib_log, logger)
        self.__reg_access = SequencerRegAccess(ip_addr, SEQUENCER_REG_PORT, *self._loggers)
        self.__cmd_sender = SequencerCmdSender(ip_addr, SEQUENCER_CMD_PORT, *self._loggers)
        self.__err_receiver: CmdErrReceiver | None = None
        self.__my_ip_addr = get_my_ip_addr(self._ip_addr) # シーケンサから来るパケットを受けるときの IP アドレス
        reg_access_addr = (self.__reg_access.my_ip_addr, self.__reg_access.my_port)
        cmd_sender_addr = (self.__cmd_sender.my_ip_addr, self.__cmd_sender.my_port)
        routing_table = {
            UplPacket.MODE_SEQUENCER_REG_READ_REPLY : reg_access_addr,
            UplPacket.MODE_SEQUENCER_REG_WRITE_ACK : reg_access_addr,
            UplPacket.MODE_SEQUENCER_CMD_WRITE_ACK : cmd_sender_addr
        }
        self.__router = UdpRouter(self.__my_ip_addr, routing_table, *self._loggers)
        self.__router.start()


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
        if self.__err_receiver is not None:
            self.__err_receiver.stop()
            self.__err_receiver.close()
        self.__router.stop()
        self.__router.close()
        self.__reg_access.close()
        self.__cmd_sender.close()


    def __set_dest_port(self, port: int) -> None:
        """シーケンサからサーバに送られるパケットの宛先ポートをシーケンサに設定する"""
        self.__reg_access.write(SeqRegs.ADDR, SeqRegs.Offset.DEST_UDP_PORT, port)


    def __set_dest_ip_addr(self, ip_addr: str) -> None:
        """シーケンサからサーバに送られるエラーレポートの宛先ポートをシーケンサに設定する"""
        val = int.from_bytes(socket.inet_aton(ip_addr), 'big')
        self.__reg_access.write(SeqRegs.ADDR, SeqRegs.Offset.DEST_IP_ADDR, val)


    def _initialize(self) -> None:
        self.__set_dest_port(self.__router.my_port)
        self.__set_dest_ip_addr(self.__my_ip_addr)
        self.__reg_access.write(SeqRegs.ADDR, SeqRegs.Offset.CTRL, 0)
        self.__reset_sequencer()
        self.set_branch_flag(True)
        # 古いエラーレポートを受信しないように, エラー送信を止めてリセットしてからエラーレポート受信ポートを作成する.
        if self.__err_receiver is None:
            self.__err_receiver = CmdErrReceiver(self.__my_ip_addr, *self._loggers)
            self.__router.add_entry(
                UplPacket.MODE_SEQUENCER_CMD_ERR_REPORT,
                self.__err_receiver.my_ip_addr,
                self.__err_receiver.my_port)
            self.__err_receiver.start()
        else:
            self.__err_receiver.pop_err_reports()


    def __reset_sequencer(self) -> None:
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_RESET, 1, 1)
        time.sleep(1e-4)
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_RESET, 1, 0)
        time.sleep(1e-4)


    def _push_commands(self, cmd_list: Sequence[SequencerCmd]) -> None:
        free_space = self._cmd_fifo_free_space()
        cmd_bytes = sum([cmd.size() for cmd in cmd_list])
        if cmd_bytes > free_space:
            msg = 'required : {} bytes,   free : {} bytes'.format(cmd_bytes, free_space)
            log_error(msg, *self._loggers)
            raise TooLittleFreeSpaceInCmdFifoError(msg)

        self.__cmd_sender.send(cmd_list)


    def _start_sequencer(self) -> None:
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_START, 1, 0)
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_START, 1, 1)
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_START, 1, 0)


    def _terminate_sequencer(self) -> None:
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_TERMINATE, 1, 0)
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_TERMINATE, 1, 1)
        self.__wait_for_sequencer_idle(4)
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_TERMINATE, 1, 0)


    def _clear_commands(self) -> None:
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_CMD_CLR, 1, 1)
        time.sleep(1e-4)
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_CMD_CLR, 1, 0)
        time.sleep(1e-4)
        self._reset_cmd_counter()


    def _clear_unsent_cmd_err_reports(self) -> None:
        self.__reg_access.write_bits(
            SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_ERR_REPORT_CLR, 1, 1)
        time.sleep(1e-4)
        self.__reg_access.write_bits(
            SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_ERR_REPORT_CLR, 1, 0)
        time.sleep(1e-4)


    def _clear_sequencer_stop_flag(self) -> None:
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_DONE_CLR, 1, 0)
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_DONE_CLR, 1, 1)
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_DONE_CLR, 1, 0)


    def _enable_cmd_err_report(self) -> None:
        self.__reg_access.write_bits(
            SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_ERR_REPORT_SEND_ENABLE, 1, 1)
        self.__wait_for_cmd_err_report_status_to_change(4, True)


    def _disable_cmd_err_report(self) -> None:
        self.__reg_access.write_bits(
            SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_ERR_REPORT_SEND_ENABLE, 1, 0)
        self.__wait_for_cmd_err_report_status_to_change(4, False)


    def _wait_for_sequencer_to_stop(self, timeout: float) -> None:
        start = time.time()
        while True:
            stopped = self.__reg_access.read_bits(
                SeqRegs.ADDR, SeqRegs.Offset.STATUS, SeqRegs.Bit.STATUS_DONE, 1)

            if stopped:
                return

            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                msg = 'Sequencer stop timed out'
                log_error(msg, *self._loggers)
                raise SequencerTimeoutError(msg)
            time.sleep(0.01)


    def __wait_for_sequencer_idle(self, timeout: float) -> None:
        start = time.time()
        while True:
            busy = self.__reg_access.read_bits(
                SeqRegs.ADDR, SeqRegs.Offset.STATUS, SeqRegs.Bit.STATUS_BUSY, 1)

            if not busy:
                return

            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                msg = 'Sequencer idle timed out'
                log_error(msg, *self._loggers)
                raise SequencerTimeoutError(msg)
            time.sleep(0.01)

    
    def __wait_for_cmd_err_report_status_to_change(
        self, timeout: float, wait_for_active: bool
    ) -> None:
        start = time.time()
        while True:
            active = self.__reg_access.read_bits(
                SeqRegs.ADDR, SeqRegs.Offset.STATUS, SeqRegs.Bit.STATUS_ERR_REPORT_SEND_ACTIVE, 1)

            if not (active ^ wait_for_active):
                return

            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                msg = 'Sequencer cmd err report status change timed out'
                log_error(msg, *self._loggers)
                raise SequencerTimeoutError(msg)
            time.sleep(0.01)


    def _num_unprocessed_commands(self) -> int:
        return self._num_stored_commands() - self._cmd_counter()


    def _num_stored_commands(self) -> int:
        return self.__reg_access.read(SeqRegs.ADDR, SeqRegs.Offset.NUM_STORED_CMDS)


    def _num_successful_commands(self) -> int:
        return self.__reg_access.read(SeqRegs.ADDR, SeqRegs.Offset.NUM_SUCCESSFUL_CMDS)


    def _num_err_commands(self) -> int:
        return self.__reg_access.read(SeqRegs.ADDR, SeqRegs.Offset.NUM_ERR_CMDS)


    def _num_unsent_cmd_err_reports(self) -> int:
        return self.__reg_access.read(SeqRegs.ADDR, SeqRegs.Offset.NUM_ERR_REPORTS)


    def _cmd_fifo_free_space(self) -> int:
        return self.__reg_access.read(SeqRegs.ADDR, SeqRegs.Offset.CMD_BUF_FREE_SPACE)


    def _check_err(self) -> list[SequencerErr]:
        err_list = []
        err = self.__reg_access.read_bits(
            SeqRegs.ADDR, SeqRegs.Offset.ERR, SeqRegs.Bit.ERR_CMD_BUF_OVERFLOW, 1)
        if err == 1:
            err_list.append(SequencerErr.CMD_FIFO_OVERFLOW)

        err = self.__reg_access.read_bits(
            SeqRegs.ADDR, SeqRegs.Offset.ERR, SeqRegs.Bit.ERR_ERR_FIFO_OVERFLOW, 1)
        if err == 1:
            err_list.append(SequencerErr.ERR_FIFO_OVERFLOW)
        
        return err_list


    def _pop_cmd_err_reports(self) -> list[SequencerCmdErr]:
        if self.__err_receiver is None:
            return []

        return self.__err_receiver.pop_err_reports()


    def _cmd_counter(self) -> int:
        return self.__reg_access.read(SeqRegs.ADDR, SeqRegs.Offset.CMD_COUNTER)


    def _reset_cmd_counter(self) -> None:
        self.__reg_access.write_bits(
            SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_CMD_COUNTER_RESET, 1, 0)
        self.__reg_access.write_bits(
            SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_CMD_COUNTER_RESET, 1, 1)
        self.__reg_access.write_bits(
            SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_CMD_COUNTER_RESET, 1, 0)


    def _get_branch_flag(self) -> bool:
        return not bool(self.__reg_access.read_bits(
            SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_BRANCH_FLAG_NEG, 1))


    def _set_branch_flag(self, val: bool) -> None:
        self.__reg_access.write_bits(
            SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_BRANCH_FLAG_NEG, 1, int(not val))
    

    def _get_external_branch_flag(self) -> bool:
        return not bool(self.__reg_access.read_bits(
            SeqRegs.ADDR, SeqRegs.Offset.STATUS, SeqRegs.Bit.STATUS_EXT_BRANCH_FLAG_NEG, 1))


    def _version(self) -> str:
        data = self.__reg_access.read(SeqRegs.ADDR, SeqRegs.Offset.VERSION)
        ver_char = chr(0xFF & (data >> 24))
        ver_year = 0xFF & (data >> 16)
        ver_month = 0xF & (data >> 12)
        ver_day = 0xFF & (data >> 4)
        ver_id = 0xF & data
        return '{}:20{:02}/{:02}/{:02}-{}'.format(ver_char, ver_year, ver_month, ver_day, ver_id)
