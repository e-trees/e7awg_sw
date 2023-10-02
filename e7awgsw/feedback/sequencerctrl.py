import time
import socket
from abc import ABCMeta, abstractmethod
from e7awgsw.logger import get_file_logger, get_null_logger, log_error
from e7awgsw.feedback.hwparam import SEQUENCER_REG_PORT, SEQUENCER_CMD_PORT
from e7awgsw.feedback.udpaccess import SequencerRegAccess, SequencerCmdSender, CmdErrReceiver, UdpRouter, get_my_ip_addr
from e7awgsw.feedback.uplpacket import UplPacket
from e7awgsw.feedback.memorymap import SequencerCtrlRegs as SeqRegs
from e7awgsw.feedback.sequencercmd import SequencerCmd
from e7awgsw.feedback.exception import TooLittleFreeSpaceInCmdFifoError, SequencerTimeoutError
from e7awgsw.feedback.hwdefs import SequencerErr

class SequencerCtrlBase(object, metaclass = ABCMeta):

    def __init__(self, ip_addr, validate_args, enable_lib_log, logger):
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


    def initialize(self):
        """シーケンサを初期化する

        | このクラスの他のメソッドを呼び出す前に呼ぶこと.
        """
        self._initialize()


    def push_commands(self, cmd_list):
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

    
    def start_sequencer(self):
        """シーケンサのコマンドの処理を開始する"""
        self._start_sequencer()


    def terminate_sequencer(self):
        """シーケンサを強制停止させる

        | 実行中のコマンドは途中で終了する.  途中で終了したコマンドは, 処理に失敗したコマンドとしてカウントされる.        
        """
        self._terminate_sequencer()


    def clear_unprocessed_commands(self):
        """シーケンサにある未実行のコマンドをすべて削除する"""
        self._clear_unprocessed_commands()


    def clear_unsent_cmd_err_reports(self):
        """シーケンサにある未送信のコマンドエラーレポートをすべて削除する"""
        self._clear_unsent_cmd_err_reports()


    def clear_sequencer_stop_flag(self):
        """シーケンサのコマンド処理終了フラグを下げる"""
        self._clear_sequencer_stop_flag()


    def enable_cmd_err_report(self):
        """コマンドエラーの送信機能を有効化する"""
        self._enable_cmd_err_report()


    def disable_cmd_err_report(self):
        """コマンドエラーの送信機能を無効化する"""
        self._disable_cmd_err_report()


    def wait_for_sequencer_to_stop(self, timeout):
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


    def num_unprocessed_commands(self):
        """シーケンサにある未実行のコマンドの数を取得する
        
        Returns:
            int: シーケンサにある未実行のコマンドの数
        """
        return self._num_unprocessed_commands()


    def num_successful_commands(self):
        """シーケンサのコマンドの処理開始から現在までに, 処理に成功したコマンドの数を取得する

        | この数は, シーケンサのコマンドの処理を開始するたびに 0 に戻る.
        
        Returns:
            int: シーケンサが処理に成功したコマンドの数
        """
        return self._num_successful_commands()


    def num_err_commands(self):
        """シーケンサのコマンドの処理開始から現在までに, 処理に失敗したコマンドの数を取得する

        | この数は, シーケンサのコマンドの処理を開始するたびに 0 に戻る.
        
        Returns:
            int: シーケンサが処理に失敗したコマンドの数
        """
        return self._num_err_commands()


    def num_unsent_cmd_err_reports(self):
        """未送信のコマンドエラーレポートの数を取得する
        
        Returns:
            int: 未送信のコマンドエラーレポートの数
        """
        return self._num_unsent_cmd_err_reports()


    def cmd_fifo_free_space(self):
        """コマンドキューの空き領域を取得する

        Returns:
            int: コマンドキューの空き領域 (Bytes)
        """
        return self._cmd_fifo_free_space()


    def check_err(self):
        """シーケンサのエラーをチェックし, エラーに応じた列挙子のリストを返す.

        Returns:
            list of SequencerErr: 発生したエラーのリスト. エラーが無かった場合は空のリスト.
        """
        return self._check_err()


    def pop_cmd_err_reports(self):
        """シーケンサから送られたコマンドエラーレポートを取得する.

        | 古いレポートから順に戻り値のリストに格納される.
        | 取得したレポートは, このオブジェクトの管理から外れる.
        
        Returns:
            cmd_list (list of SequencerCmdErr): 
                | シーケンサから送られたコマンドエラーレポートのリスト.
                | コマンドエラーレポートがない場合は, 空のリスト
        """
        return self._pop_cmd_err_reports()


    def version(self):
        """シーケンサのバージョンを取得する

        Returns:
            string: バージョンを表す文字列
        """
        return self._version()


    def _validate_ip_addr(self, ip_addr):
        try:
            if ip_addr != 'localhost':
                socket.inet_aton(ip_addr)
        except socket.error:
            raise ValueError('Invalid IP address {}'.format(ip_addr))


    def _validate_seq_cmds(self, cmd_list):
        if isinstance(cmd_list, SequencerCmd):
            return

        if not isinstance(cmd_list, (list, tuple)):
            raise('Invalid sequencer command list.  ({})'.format(cmd_list))

        for cmd in cmd_list:
            if not isinstance(cmd, SequencerCmd):
                raise('Invalid sequencer command list.  ({})'.format(cmd_list))


    def _validate_timeout(self, timeout):
        if (not isinstance(timeout, (int, float))) or (timeout < 0):
            raise ValueError('Invalid timeout {}'.format(timeout))


    @abstractmethod
    def _initialize(self):
        pass

    @abstractmethod
    def _push_commands(self, cmd_list):
        pass

    @abstractmethod
    def _start_sequencer(self):
        pass

    @abstractmethod
    def _terminate_sequencer(self):
        pass

    @abstractmethod
    def _clear_unprocessed_commands(self):
        pass

    @abstractmethod
    def _clear_unsent_cmd_err_reports(self):
        pass

    @abstractmethod
    def _clear_sequencer_stop_flag(self):
        pass

    @abstractmethod
    def _enable_cmd_err_report(self):
        pass

    @abstractmethod
    def _disable_cmd_err_report(self):
        pass
    
    @abstractmethod
    def _wait_for_sequencer_to_stop(self, timeout):
        pass

    @abstractmethod
    def _num_unprocessed_commands(self):
        pass

    @abstractmethod
    def _num_successful_commands(self):
        pass

    @abstractmethod
    def _num_err_commands(self):
        pass

    @abstractmethod
    def _num_unsent_cmd_err_reports(self):
        pass

    @abstractmethod
    def _cmd_fifo_free_space(self):
        pass

    @abstractmethod
    def _check_err(self):
        pass

    @abstractmethod
    def _pop_cmd_err_reports(self):
        pass

    @abstractmethod
    def _version(self):
        pass


class SequencerCtrl(SequencerCtrlBase):
    def __init__(
        self,
        ip_addr,
        *,
        validate_args = True,
        enable_lib_log = True,
        logger = get_null_logger()):
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
        self.__err_receiver = None
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


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


    def close(self):
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


    def __set_dest_port(self, port):
        """シーケンサからサーバに送られるパケットの宛先ポートをシーケンサに設定する"""
        self.__reg_access.write(SeqRegs.ADDR, SeqRegs.Offset.DEST_UDP_PORT, port)


    def __set_dest_ip_addr(self, ip_addr):
        """シーケンサからサーバに送られるエラーレポートの宛先ポートをシーケンサに設定する"""
        ip_addr = int.from_bytes(socket.inet_aton(ip_addr), 'big')
        self.__reg_access.write(SeqRegs.ADDR, SeqRegs.Offset.DEST_IP_ADDR, ip_addr)


    def _initialize(self):
        self.__set_dest_port(self.__router.my_port)
        self.__set_dest_ip_addr(self.__my_ip_addr)
        self.__reg_access.write(SeqRegs.ADDR, SeqRegs.Offset.CTRL, 0)
        self.__reset_sequencer()
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


    def __reset_sequencer(self):
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_RESET, 1, 1)
        time.sleep(1e-4)
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_RESET, 1, 0)
        time.sleep(1e-4)


    def _push_commands(self, cmd_list):
        free_space = self._cmd_fifo_free_space()
        cmd_bytes = sum([cmd.size() for cmd in cmd_list])
        if cmd_bytes > free_space:
            msg = 'required : {} bytes,   free : {} bytes'.format(cmd_bytes, free_space)
            log_error(msg, *self._loggers)
            raise TooLittleFreeSpaceInCmdFifoError(msg)

        self.__cmd_sender.send(cmd_list)


    def _start_sequencer(self):
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_START, 1, 0)
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_START, 1, 1)
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_START, 1, 0)


    def _terminate_sequencer(self):
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_TERMINATE, 1, 0)
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_TERMINATE, 1, 1)
        self.__wait_for_sequencer_idle(4)
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_TERMINATE, 1, 0)


    def _clear_unprocessed_commands(self):
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_CMD_CLR, 1, 1)
        time.sleep(1e-4)
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_CMD_CLR, 1, 0)
        time.sleep(1e-4)


    def _clear_unsent_cmd_err_reports(self):
        self.__reg_access.write_bits(
            SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_ERR_REPORT_CLR, 1, 1)
        time.sleep(1e-4)
        self.__reg_access.write_bits(
            SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_ERR_REPORT_CLR, 1, 0)
        time.sleep(1e-4)


    def _clear_sequencer_stop_flag(self):
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_DONE_CLR, 1, 0)
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_DONE_CLR, 1, 1)
        self.__reg_access.write_bits(SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_DONE_CLR, 1, 0)


    def _enable_cmd_err_report(self):
        self.__reg_access.write_bits(
            SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_ERR_REPORT_SEND_ENABLE, 1, 1)
        self.__wait_for_cmd_err_report_status_to_change(4, True)


    def _disable_cmd_err_report(self):
        self.__reg_access.write_bits(
            SeqRegs.ADDR, SeqRegs.Offset.CTRL, SeqRegs.Bit.CTRL_ERR_REPORT_SEND_ENABLE, 1, 0)
        self.__wait_for_cmd_err_report_status_to_change(4, False)


    def _wait_for_sequencer_to_stop(self, timeout):
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


    def __wait_for_sequencer_idle(self, timeout):
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

    
    def __wait_for_cmd_err_report_status_to_change(self, timeout, wait_for_active):
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


    def _num_unprocessed_commands(self):
        return self.__reg_access.read(SeqRegs.ADDR, SeqRegs.Offset.NUM_UNPROCESSED_CMDS)


    def _num_successful_commands(self):
        return self.__reg_access.read(SeqRegs.ADDR, SeqRegs.Offset.NUM_SUCCESSFUL_CMDS)


    def _num_err_commands(self):
        return self.__reg_access.read(SeqRegs.ADDR, SeqRegs.Offset.NUM_ERR_CMDS)


    def _num_unsent_cmd_err_reports(self):
        return self.__reg_access.read(SeqRegs.ADDR, SeqRegs.Offset.NUM_ERR_REPORTS)


    def _cmd_fifo_free_space(self):
        return self.__reg_access.read(SeqRegs.ADDR, SeqRegs.Offset.CMD_FIFO_FREE_SPACE)


    def _check_err(self):
        err_list = []
        err = self.__reg_access.read_bits(
            SeqRegs.ADDR, SeqRegs.Offset.ERR, SeqRegs.Bit.ERR_CMD_FIFO_OVERFLOW, 1)
        if err == 1:
            err_list.append(SequencerErr.CMD_FIFO_OVERFLOW)

        err = self.__reg_access.read_bits(
            SeqRegs.ADDR, SeqRegs.Offset.ERR, SeqRegs.Bit.ERR_ERR_FIFO_OVERFLOW, 1)
        if err == 1:
            err_list.append(SequencerErr.ERR_FIFO_OVERFLOW)
        
        return err_list


    def _pop_cmd_err_reports(self):
        if self.__err_receiver is None:
            return []

        return self.__err_receiver.pop_err_reports()


    def _version(self):
        data = self.__reg_access.read(SeqRegs.ADDR, SeqRegs.Offset.VERSION)
        ver_char = chr(0xFF & (data >> 24))
        ver_year = 0xFF & (data >> 16)
        ver_month = 0xF & (data >> 12)
        ver_day = 0xFF & (data >> 4)
        ver_id = 0xF & data
        return '{}:20{:02}/{:02}/{:02}-{}'.format(ver_char, ver_year, ver_month, ver_day, ver_id)
