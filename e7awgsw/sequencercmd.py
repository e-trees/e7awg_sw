import copy
from abc import ABCMeta, abstractmethod
from .hwdefs import CaptureParamElem, CaptureUnit, AWG, FeedbackChannel
from .hwparam import CLASSIFICATION_RESULT_SIZE, MAX_CAPTURE_SIZE, CAPTURE_RAM_WORD_SIZE, CAPTURE_DATA_ALIGNMENT_SIZE, MAX_WAVE_REGISTRY_ENTRIES, MAX_CAPTURE_PARAM_REGISTRY_ENTRIES
from .wavesequence import WaveSequence

class SequencerCmd(object, metaclass = ABCMeta):

    MAX_CMD_NO = 0xFFFF #: 指定可能なコマンド番号の最大値

    def __init__(self, cmd_id, cmd_no, stop_seq):

        if not (isinstance(cmd_no, int) and
                (0 <= cmd_no and cmd_no <= self.MAX_CMD_NO)):
            raise ValueError(
                "Command number must be an integer between {} and {} inclusive.  '{}' was set."
                .format(0, self.MAX_CMD_NO, cmd_no))
        
        if not isinstance(stop_seq, bool):
            raise ValueError("The type of 'stop_seq' must be 'bool'.  '{}' was set.".format(stop_seq))

        self.__cmd_id = cmd_id
        self.__cmd_no = cmd_no
        self.__stop_seq = stop_seq


    @property
    def cmd_id(self):
        """このコマンドの種類を表す ID

        Returns:
            int: このコマンドの種類を表す ID
        """
        return self.__cmd_id


    @property
    def cmd_no(self):
        """このコマンドのコマンド番号
        
        Returns:
            int: このコマンドのコマンド番号
        """
        return self.__cmd_no


    @property
    def stop_seq(self):
        """シーケンサ停止フラグ
        
        Returns:
            int: シーケンサ停止フラグ
        """
        return self.__stop_seq


    def _validate_capture_unit_id(self, capture_unit_id_list):        
        if ((not isinstance(capture_unit_id_list, (list, tuple))) or 
            (not capture_unit_id_list)                            or
            (not CaptureUnit.includes(*capture_unit_id_list))):
            raise ValueError("Invalid capture unit ID '{}'".format(capture_unit_id_list))


    def _validate_awg_id(self, awg_id_list):
        if ((not isinstance(awg_id_list, (list, tuple))) or 
            (not awg_id_list)                            or
            (not AWG.includes(*awg_id_list))):
            raise ValueError("Invalid AWG ID '{}'".format(awg_id_list))


    def _validate_feedback_channel_id(self, feedback_channel_id):
        if not FeedbackChannel.includes(feedback_channel_id):
            raise ValueError("Invalid feedback channel ID '{}'".format(feedback_channel_id))


    def _validate_key_table(self, key_table, max_registry_key):
        if isinstance(key_table, int) and (0 <= key_table and key_table <= max_registry_key):
            return

        if not isinstance(key_table, (list, tuple)):
            raise ValueError(
                "The type of 'key_table' must be 'list' or 'tuple'.  ({})".format(key_table))

        # 2022/08/02 現在, フィードバック値は四値化結果だけなので, レジストリキーの数 = 4 という制約を加えておく.
        if len(key_table) != 4:
            raise ValueError(
                "The number of elements in 'key_table' must be 4.  ({})".format(len(key_table)))

        for key in key_table:
            if not (isinstance(key, int) and (0 <= key and key <= max_registry_key)):
                raise ValueError(
                    "The elements in 'key_table' must be integers between {} and {} inclusive.  ({})"
                    .format(0, max_registry_key, key_table))


    def _to_bit_field(self, bit_pos_list):
        bit_field = 0
        for bit_pos in bit_pos_list:
            bit_field |= 1 << bit_pos
        return bit_field


    @abstractmethod
    def serialize(self):
        pass


    @abstractmethod
    def size(self):
        """serialize した際のコマンドのバイト数"""
        pass


class AwgStartCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID = 1
    #: AWG スタート時刻に指定可能な最大値
    MAX_START_TIME = 0x7FFFFFFF_FFFFFFFF
    #: AWG を即時スタートする場合に start_time に指定する値．
    IMMEDIATE = -1

    def __init__(
        self,
        cmd_no,
        awg_id_list,
        start_time,
        wait = False,
        stop_seq = False):
        """AWG を指定した時刻にスタートするコマンド

        Args:
            cmd_no (int): コマンド番号
            awg_id_list (list of AWG): 波形の出力を開始する AWG のリスト
            start_time (int):
                | AWG をスタートする時刻.
                | シーケンサが動作を開始した時点を 0 として, start_time * 8[ns] 後に AWG がスタートする.
                | 負の値を入力した場合, AWG を即時スタートする．
                | このとき, AWG はコマンドの実行と同時に波形出力準備を行い, 1.92 [us] 後にスタートする.
            wait (bool):
                | True -> AWG をスタートした後, 波形の出力完了を待ってからこのコマンドを終了する
                | False -> AWG をスタートした後, このコマンドを終了する.
            stop_seq (bool): 
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
        """
        super().__init__(self.ID, cmd_no, stop_seq)
        if AWG.includes(awg_id_list):
            awg_id_list = [awg_id_list]
        self._validate_awg_id(awg_id_list)

        if not (isinstance(start_time, int) and (start_time <= self.MAX_START_TIME)):
            raise ValueError(
                "'start_time' must be less than or equal to {}.  '{}' was set."
                .format(self.MAX_START_TIME, start_time))

        self.__awg_id_list = copy.copy(awg_id_list)
        self.__start_time = start_time
        self.__wait = wait
        self.__cmd_bytes = self.__gen_cmd_bytes()


    @property
    def awg_id_list(self):
        return copy.copy(self.__awg_id_list)


    @property
    def start_time(self):
        return self.__start_time


    @property
    def wait(self):
        return self.__wait


    def __gen_cmd_bytes(self):
        stop_seq = 1 if self.stop_seq else 0
        awg_id_list = self._to_bit_field(self.__awg_id_list)
        start_time = 0xFFFFFFFF_FFFFFFFF if self.start_time < 0 else self.start_time
        cmd = (
            stop_seq                    |
            self.cmd_id          << 1   |
            self.cmd_no          << 8   |
            awg_id_list          << 24  |
            start_time           << 40  |
            self.wait            << 104)
        return cmd.to_bytes(16, 'little')


    def serialize(self):
        return self.__cmd_bytes


    def size(self):
        return len(self.__cmd_bytes)


class CaptureEndFenceCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID = 2
    #: キャプチャ完了確認時刻に指定可能な最大値
    MAX_END_TIME = 0x7FFFFFFF_FFFFFFFF

    def __init__(
        self,
        cmd_no,
        capture_unit_id_list,
        end_time,
        wait = True,
        terminate = False,
        stop_seq = False):
        """指定した時刻まで待ってからキャプチャが完了しているかを調べるコマンド

        Args:
            cmd_no (int): コマンド番号
            capture_unit_id_list (list of CaptureUnit): キャプチャの完了を調べるキャプチャユニットのリスト.
            end_time (int):
                | キャプチャが完了しているかを調べる時刻.
                | シーケンサが動作を開始した時点を 0 として, end_time * 8[ns] 後にキャプチャの完了をチェックする.
            wait (bool):
                | True -> end_time の後もキャプチャが完了していないキャプチャユニットの終了を待つ.
                | False -> end_time の後, キャプチャの完了を待たずにコマンドを終了する.
            terminate (bool): 
                | キャプチャユニット停止フラグ.
                | True の場合 end_time の時点でキャプチャが完了していないキャプチャユニットを強制停止する.
            stop_seq (bool): 
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
        """
        super().__init__(self.ID, cmd_no, stop_seq)
        if CaptureUnit.includes(capture_unit_id_list):
            capture_unit_id_list = [capture_unit_id_list]
        self._validate_capture_unit_id(capture_unit_id_list)

        if not (isinstance(end_time, int) and
                (0 <= end_time and end_time <= self.MAX_END_TIME)):
            raise ValueError(
                "'end_time' must be an integer between {} and {} inclusive.  '{}' was set."
                .format(0, self.MAX_END_TIME, end_time))

        if not isinstance(wait, bool):
            raise ValueError("The type of 'wait' must be 'bool'.  '{}' was set.".format(wait))

        if not isinstance(terminate, bool):
            raise ValueError("The type of 'terminate' must be 'bool'.  '{}' was set.".format(terminate))

        self.__capture_unit_id_list = copy.copy(capture_unit_id_list)
        self.__end_time = end_time
        self.__wait = wait
        self.__terminate = terminate
        self.__cmd_bytes = self.__gen_cmd_bytes()


    @property
    def capture_unit_id_list(self):
        return copy.copy(self.__capture_unit_id_list)


    @property
    def end_time(self):
        return self.__end_time


    @property
    def wait(self):
        return self.__wait


    @property
    def terminate(self):
        return self.__terminate


    def __gen_cmd_bytes(self):
        stop_seq = 1 if self.stop_seq else 0
        capture_unit_id_bits = self._to_bit_field(self.__capture_unit_id_list)
        cmd = (
            stop_seq                        |
            self.cmd_id              << 1   |
            self.cmd_no              << 8   |
            capture_unit_id_bits     << 24  |
            self.end_time            << 40  |
            self.terminate           << 104 |
            self.wait                << 105)
        return cmd.to_bytes(16, 'little')


    def serialize(self):
        return self.__cmd_bytes


    def size(self):
        return len(self.__cmd_bytes)


class WaveSequenceSetCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID = 3

    def __init__(
        self,
        cmd_no,
        awg_id_list,
        key_table,
        feedback_channel_id = FeedbackChannel.U0,
        stop_seq = False):
        """フィードバック値に応じて波形シーケンスを AWG にセットするコマンド

        Args:
            cmd_no (int): コマンド番号
            awg_id_list (list of AWG): 波形シーケンスをセットする AWG のリスト.
            key_table (list of int, int):
                | 波形シーケンスを登録したレジストリのキーのリスト.
                | key_table[フィードバック値] = 設定したい波形シーケンスを登録したレジストリのキー
                | となるように設定する.
                | レジストリキーに int 値 1 つを指定すると, フィードバック値によらず, 
                | そのキーに登録された波形シーケンスを設定する.
            feedback_channel_id (FeedbackChannel): 
                | 参照するフィードバックチャネルの ID.
            stop_seq (bool):
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
        """
        super().__init__(self.ID, cmd_no, stop_seq)
        if AWG.includes(awg_id_list):
            awg_id_list = [awg_id_list]
        self._validate_awg_id(awg_id_list)
        self._validate_feedback_channel_id(feedback_channel_id)
        self._validate_key_table(key_table, MAX_WAVE_REGISTRY_ENTRIES - 1)
        if isinstance(key_table, int):
            key_table = [key_table] * 4

        self.__awg_id_list = awg_id_list
        self.__feedback_channel_id = feedback_channel_id
        self.__key_table = copy.copy(key_table)
        self.__cmd_bytes = self.__gen_cmd_bytes()


    @property
    def awg_id_list(self):
        return copy.copy(self.__awg_id_list)


    @property
    def feedback_channel_id(self):
        return self.__feedback_channel_id


    @property
    def key_table(self):
        return copy.copy(self.__key_table)

    def __gen_cmd_bytes(self):
        stop_seq = 1 if self.stop_seq else 0
        awg_id_bits = self._to_bit_field(self.__awg_id_list)
        last_chunk_no = WaveSequence.MAX_CHUNKS - 1
        key_table_bits = 0
        for i in range(len(self.__key_table)):
            key_table_bits |= self.__key_table[i] << (i * 10)

        cmd = (
            stop_seq                       |
            self.cmd_id              << 1  |
            self.cmd_no              << 8  |
            awg_id_bits              << 24 |
            self.feedback_channel_id << 40 |
            last_chunk_no            << 44 |
            key_table_bits           << 60)
        return cmd.to_bytes(16, 'little')


    def serialize(self):
        return self.__cmd_bytes


    def size(self):
        return len(self.__cmd_bytes)


class CaptureParamSetCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID = 4

    def __init__(
        self,
        cmd_no,
        capture_unit_id_list,
        key_table,
        feedback_channel_id = FeedbackChannel.U0,
        param_elems = CaptureParamElem.all(),
        stop_seq = False):
        """フィードバック値に応じてキャプチャパラメータをキャプチャユニットにセットするコマンド

        Args:
            cmd_no (int): コマンド番号
            capture_unit_id_list (list of CaptureUnit): 波形シーケンスをセットするキャプチャユニットのリスト.
            key_table (list of int, int):
                | キャプチャパラメータを登録したレジストリのキーのリスト.
                | key_table[フィードバック値] = 設定したいキャプチャパラメータを登録したレジストリのキー
                | となるように設定する.
                | レジストリキーに int 値 1 つを指定すると, フィードバック値によらず, 
                | そのキーに登録されたキャプチャパラメータを設定する.
            feedback_channel_id (FeedbackChannel): 
                | 参照するフィードバックチャネルの ID.
            param_elems (list of CaptureParamElem):
                | キャプチャパラメータの中の設定したい要素のリスト.
                | ここに指定しなかった要素は, キャプチャユニットに設定済みの値のまま更新されない.
                | 特に, 「総和区間数」「総和区間長」「ポストブランク長」の 3 つは, セットで更新しない場合,
                | キャプチャユニットが保持するパラメータと不整合を起こす可能性がある点に注意.
            stop_seq (bool):
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
        """
        super().__init__(self.ID, cmd_no, stop_seq)
        if CaptureUnit.includes(capture_unit_id_list):
            capture_unit_id_list = [capture_unit_id_list]
        self._validate_capture_unit_id(capture_unit_id_list)
        self._validate_feedback_channel_id(feedback_channel_id)
        self._validate_key_table(key_table, MAX_CAPTURE_PARAM_REGISTRY_ENTRIES - 1)
        if isinstance(key_table, int):
            key_table = [key_table] * 4

        if not (isinstance(param_elems, (list, tuple)) and CaptureParamElem.includes(*param_elems)):
            raise ValueError("Invalid capture parameter elements.  ({})".format(param_elems))
        
        self.__capture_unit_id_list = copy.copy(capture_unit_id_list)
        self.__feedback_channel_id = feedback_channel_id
        self.__key_table = copy.copy(key_table)
        self.__param_elems = copy.copy(param_elems)
        self.__cmd_bytes = self.__gen_cmd_bytes()


    @property
    def capture_unit_id_list(self):
        return copy.copy(self.__capture_unit_id_list)


    @property
    def feedback_channel_id(self):
        return self.__feedback_channel_id


    @property
    def key_table(self):
        return copy.copy(self.__key_table)


    @property
    def param_elems(self):
        return copy.copy(self.__param_elems)


    def __gen_cmd_bytes(self):
        stop_seq = 1 if self.stop_seq else 0
        capture_unit_id_bits = self._to_bit_field(self.__capture_unit_id_list)        
        param_elem_bits = self._to_bit_field(self.__param_elems)

        key_table_bits = 0
        for i in range(len(self.__key_table)):
            key_table_bits |= self.__key_table[i] << (i * 10)

        cmd = (
            stop_seq                       |
            self.cmd_id              << 1  |
            self.cmd_no              << 8  |
            capture_unit_id_bits     << 24 |
            self.feedback_channel_id << 40 |
            param_elem_bits          << 44 |
            key_table_bits           << 60)
        return cmd.to_bytes(16, 'little')


    def serialize(self):
        return self.__cmd_bytes


    def size(self):
        return len(self.__cmd_bytes)


class CaptureAddrSetCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID = 5

    def __init__(
        self,
        cmd_no,
        capture_unit_id_list,
        byte_offset,
        stop_seq = False):
        """キャプチャアドレスをセットするコマンド

        Args:
            cmd_no (int): コマンド番号
            capture_unit_id_list (list of CaptureUnit): キャプチャアドレスをセットするキャプチャユニットのリスト.
            byte_offset (int): 
                | 各キャプチャユニットのキャプチャ領域の先頭アドレス + byte_offset を, 次のキャプチャのデータの格納先とする.
            stop_seq (bool): 
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
        """
        super().__init__(self.ID, cmd_no, stop_seq)
        self._validate_capture_unit_id(capture_unit_id_list)
        if CaptureUnit.includes(capture_unit_id_list):
            capture_unit_id_list = [capture_unit_id_list]

        if not (isinstance(byte_offset, int) and
                (0 <= byte_offset and byte_offset < MAX_CAPTURE_SIZE)):
            raise ValueError(
                "'byte_offset' must be an integer between {} and {} inclusive.  '{}' was set."
                .format(0, MAX_CAPTURE_SIZE - 1, byte_offset))

        if (byte_offset % CAPTURE_DATA_ALIGNMENT_SIZE) != 0:
            raise ValueError(
                "'byte_offset' must be a multiple of {}.  '{}' was set."
                .format(CAPTURE_DATA_ALIGNMENT_SIZE, byte_offset))
        
        self.__capture_unit_id_list = copy.copy(capture_unit_id_list)
        self.__byte_offset = byte_offset
        self.__cmd_bytes = self.__gen_cmd_bytes()


    @property
    def capture_unit_id_list(self):
        return copy.copy(self.__capture_unit_id_list)


    @property
    def byte_offset(self):
        return self.__byte_offset


    def __gen_cmd_bytes(self):
        stop_seq = 1 if self.stop_seq else 0
        capture_unit_id_bits = self._to_bit_field(self.__capture_unit_id_list)

        cmd = (
            stop_seq                   |
            self.cmd_id          << 1  |
            self.cmd_no          << 8  |
            capture_unit_id_bits << 24 |
            self.byte_offset     << 40)
        return cmd.to_bytes(16, 'little')


    def serialize(self):
        return self.__cmd_bytes


    def size(self):
        return len(self.__cmd_bytes)


class FeedbackCalcOnClassificationCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID = 6

    def __init__(
        self,
        cmd_no,
        capture_unit_id_list,
        byte_offset,
        elem_offset = 0,
        stop_seq = False):
        """四値化結果をフィードバック値とするフィードバック値計算コマンド

        | フィードバックチャネル i のフィードバック値 (FB_VAL(i)) は, 以下の式で求まる.
        | FB_VAL(i) = ビットアドレスが FB_BIT_ADDR(i) のビットとその次のビットを並べた 2 bits の値
        | FB_BIT_ADDR(i) = (CaptureUnitAddr(i) + byte_offset) * 8 + elem_offset * 2 (= 四値化結果のビットアドレス)
        | CaptureUnitAddr(i) = キャプチャユニット i に割り当てられたキャプチャ領域の先頭アドレス
        | i ∈ capture_unit_id_list

        Args:
            cmd_no (int): コマンド番号
            capture_unit_id_list (list of CaptureUnit): 
                | フィードバック値とする四値化結果が格納されたキャプチャ領域を持つキャプチャユニットの ID のリスト.
                | 更新されるフィードバックチャネルの ID のリストでもある.
            byte_offset (int): フィードバック値とするデータのバイト単位での位置
            elem_offset (int): フィードバック値とするデータの四値化結果単位での位置
            stop_seq (bool): 
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
        """        
        super().__init__(self.ID, cmd_no, stop_seq)
        if CaptureUnit.includes(capture_unit_id_list):
            capture_unit_id_list = [capture_unit_id_list]
        self._validate_capture_unit_id(capture_unit_id_list)

        if not (isinstance(byte_offset, int) and
                (0 <= byte_offset and byte_offset < MAX_CAPTURE_SIZE)):
           raise ValueError(
               "'byte_offset' must be an integer between {} and {} inclusive.  '{}' was set."
               .format(0, MAX_CAPTURE_SIZE - 1, byte_offset))

        max_results = MAX_CAPTURE_SIZE * (8 // CLASSIFICATION_RESULT_SIZE)
        if not (isinstance(elem_offset, int) and
                (0 <= elem_offset and elem_offset < max_results)):
           raise ValueError(
               "'elem_offset' must be an integer between {} and {} inclusive.  '{}' was set."
               .format(0, max_results - 1, elem_offset))

        self.__bit_offset = byte_offset * 8 + elem_offset * CLASSIFICATION_RESULT_SIZE
        if self.__bit_offset >= MAX_CAPTURE_SIZE * 8:
            raise ValueError(
                'The specified classification result is not in the capture data area.  ' + 
                'byte_offset = {}, elem_offset = {}'.format(byte_offset, elem_offset))
        
        self.__capture_unit_id_list = copy.copy(capture_unit_id_list)
        self.__byte_offset = byte_offset
        self.__elem_offset = elem_offset
        self.__cmd_bytes = self.__gen_cmd_bytes()
        

    @property
    def capture_unit_id_list(self):
        return copy.copy(self.__capture_unit_id_list)


    @property
    def byte_offset(self):
        return self.__byte_offset


    @property
    def elem_offset(self):
        return self.__elem_offset


    def __gen_cmd_bytes(self):
        stop_seq = 1 if self.stop_seq else 0
        byte_offset = self.__bit_offset // (CAPTURE_RAM_WORD_SIZE * 8) * CAPTURE_RAM_WORD_SIZE
        elem_offset = (self.__bit_offset % (CAPTURE_RAM_WORD_SIZE * 8)) // CLASSIFICATION_RESULT_SIZE
        capture_unit_id_bits = self._to_bit_field(self.__capture_unit_id_list)
        cmd = (
            stop_seq                   |
            self.cmd_id          << 1  |
            self.cmd_no          << 8  |
            capture_unit_id_bits << 24 |
            byte_offset          << 40 |
            elem_offset          << 76)
        return cmd.to_bytes(16, 'little')


    def serialize(self):
        return self.__cmd_bytes


    def size(self):
        return len(self.__cmd_bytes)


class WaveGenEndFenceCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID = 7
    #: AWG の波形出力完了を確認する時刻に指定可能な最大値
    MAX_END_TIME = 0x7FFFFFFF_FFFFFFFF

    def __init__(
        self,
        cmd_no,
        awg_id_list,
        end_time,
        wait = True,
        terminate = False,
        stop_seq = False):
        """指定した時刻まで待ってから AWG の波形出力が完了しているかを調べるコマンド

        Args:
            cmd_no (int): コマンド番号
            awg_id_list (list of AWG): 波形出力完了を調べる AWG のリスト.
            end_time (int):
                | AWG の波形出力が完了しているかを調べる時刻.
                | シーケンサが動作を開始した時点を 0 として, end_time * 8[ns] 後に波形出力の完了をチェックする.
            wait (bool):
                | True -> end_time の後も波形出力が完了していない AWG の終了を待つ.
                | False -> end_time の後, 波形出力の完了を待たずにコマンドを終了する.
            terminate (bool): 
                | AWG 停止フラグ.
                | True の場合 end_time の時点で波形の出力が完了していない AWG を強制停止する.
            stop_seq (bool): 
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
        """
        super().__init__(self.ID, cmd_no, stop_seq)
        if AWG.includes(awg_id_list):
            awg_id_list = [awg_id_list]
        self._validate_awg_id(awg_id_list)

        if not (isinstance(end_time, int) and
                (0 <= end_time and end_time <= self.MAX_END_TIME)):
            raise ValueError(
                "'end_time' must be an integer between {} and {} inclusive.  '{}' was set."
                .format(0, self.MAX_END_TIME, end_time))

        if not isinstance(wait, bool):
            raise ValueError("The type of 'wait' must be 'bool'.  '{}' was set.".format(wait))

        if not isinstance(terminate, bool):
            raise ValueError("The type of 'terminate' must be 'bool'.  '{}' was set.".format(terminate))

        self.__awg_id_list = copy.copy(awg_id_list)
        self.__end_time = end_time
        self.__wait = wait
        self.__terminate = terminate
        self.__cmd_bytes = self.__gen_cmd_bytes()


    @property
    def awg_id_list(self):
        return copy.copy(self.__awg_id_list)


    @property
    def end_time(self):
        return self.__end_time


    @property
    def wait(self):
        return self.__wait


    @property
    def terminate(self):
        return self.__terminate


    def __gen_cmd_bytes(self):
        stop_seq = 1 if self.stop_seq else 0
        awg_id_bits = self._to_bit_field(self.__awg_id_list)
        cmd = (
            stop_seq                        |
            self.cmd_id              << 1   |
            self.cmd_no              << 8   |
            awg_id_bits              << 24  |
            self.end_time            << 40  |
            self.terminate           << 104 |
            self.wait                << 105)
        return cmd.to_bytes(16, 'little')


    def serialize(self):
        return self.__cmd_bytes


    def size(self):
        return len(self.__cmd_bytes)


class SequencerCmdErr(object):

    def __init__(self, cmd_id, cmd_no, is_terminated):
        self.__cmd_id = cmd_id
        self.__cmd_no = cmd_no
        self.__is_terminated = is_terminated


    @property
    def cmd_id(self):
        """このエラーを起こしたコマンドの種類を表す ID

        Returns:
            int: このエラーを起こしたコマンドの種類を表す ID
        """
        return self.__cmd_id


    @property
    def cmd_no(self):
        """このエラーを起こしたコマンドのコマンド番号
        
        Returns:
            int: このエラーを起こしたコマンドのコマンド番号
        """
        return self.__cmd_no


    @property
    def is_terminated(self):
        """ このエラーを起こしたコマンドが実行中に強制終了させられたかどうか

        Returns:
            bool:
                | True -> コマンドが実行中に強制終了させられた
                | False -> コマンドは実行中に強制終了させれていない
        """        
        return self.__is_terminated


class AwgStartCmdErr(SequencerCmdErr):

    def __init__(self, cmd_no, is_terminated, awg_id_list):
        """AWG スタートコマンドのエラー情報を保持するクラス"""
        super().__init__(AwgStartCmd.ID, cmd_no, is_terminated)
        self.__awg_id_list = copy.copy(awg_id_list)


    @property
    def awg_id_list(self):
        """指定した時刻にスタートできなかった AWG の ID のリスト
        
        Returns:
            list of AWG: 指定した時刻にスタートできなかった AWG の ID のリスト
        """
        return copy.copy(self.__awg_id_list)


    def __str__(self):
        awg_id_list = [int(awg_id) for awg_id in self.__awg_id_list]
        return  (
            'AwgStartCmdErr\n' +
            '  - command ID : {}\n'.format(self.cmd_id) +
            '  - command No : {}\n'.format(self.cmd_no) +
            '  - terminated : {}\n'.format(self.is_terminated) +
            '  - AWG IDs    : {}'.format(awg_id_list))


class CaptureEndFenceCmdErr(SequencerCmdErr):
    
    def __init__(self, cmd_no, is_terminated, capture_unit_id_list):
        """キャプチャ完了確認コマンドのエラー情報を保持するクラス"""
        super().__init__(CaptureEndFenceCmd.ID, cmd_no, is_terminated)
        self.__capture_unit_id_list = copy.copy(capture_unit_id_list)


    @property
    def capture_unit_id_list(self):
        """指定した時刻にキャプチャが完了していなかったキャプチャユニットの ID のリスト
        
        Returns:
            list of CaptureUnit: 指定した時刻にキャプチャが完了していなかったキャプチャユニットの ID のリスト
        """
        return copy.copy(self.__capture_unit_id_list)


    def __str__(self):
        capture_unit_id_list = [int(awg_id) for awg_id in self.__capture_unit_id_list]
        return  (
            'CaptureEndFenceCmdErr\n' +
            '  - command ID       : {}\n'.format(self.cmd_id) +
            '  - command No       : {}\n'.format(self.cmd_no) +
            '  - terminated       : {}\n'.format(self.is_terminated) +
            '  - capture unit IDs : {}'.format(capture_unit_id_list))


class WaveSequenceSetCmdErr(SequencerCmdErr):
    
    def __init__(self, cmd_no, is_terminated, read_err, write_err):
        """波形シーケンスセットコマンドのエラー情報を保持するクラス"""
        super().__init__(WaveSequenceSetCmd.ID, cmd_no, is_terminated)
        self.__read_err = read_err
        self.__write_err = write_err


    @property
    def read_err(self):
        """読み出しエラーフラグ

        Returns:
            bool: コマンドの実行中に波形シーケンスの読み出しエラーが発生した場合 True
        """
        return self.__read_err


    @property
    def write_err(self):
        """書き込みエラーフラグ

        Returns:
            bool: コマンドの実行中に波形シーケンスの書き込みエラーが発生した場合 True
        """
        return self.__write_err


    def __str__(self):
        return  (
            'WaveSequenceSetCmdErr\n' +
            '  - command ID  : {}\n'.format(self.cmd_id) +
            '  - command No  : {}\n'.format(self.cmd_no) +
            '  - terminated  : {}\n'.format(self.is_terminated) +
            '  - read error  : {}\n'.format(self.read_err) +
            '  - write error : {}'.format(self.write_err))


class CaptureParamSetCmdErr(SequencerCmdErr):
    
    def __init__(self, cmd_no, is_terminated, read_err, write_err):
        """キャプチャパラメータセットコマンドのエラー情報を保持するクラス"""
        super().__init__(CaptureParamSetCmd.ID, cmd_no, is_terminated)
        self.__read_err = read_err
        self.__write_err = write_err


    @property
    def read_err(self):
        """読み出しエラーフラグ

        Returns:
            bool: コマンドの実行中にキャプチャパラメータの読み出しエラーが発生した場合 True
        """
        return self.__read_err


    @property
    def write_err(self):
        """書き込みエラーフラグ

        Returns:
            bool: コマンドの実行中にキャプチャパラメータの書き込みエラーが発生した場合 True
        """
        return self.__write_err


    def __str__(self):
        return  (
            'CaptureParamSetCmdErr\n' +
            '  - command ID  : {}\n'.format(self.cmd_id) +
            '  - command No  : {}\n'.format(self.cmd_no) +
            '  - terminated  : {}\n'.format(self.is_terminated) +
            '  - read error  : {}\n'.format(self.read_err) +
            '  - write error : {}'.format(self.write_err))


class CaptureAddrSetCmdErr(SequencerCmdErr):
    
    def __init__(self, cmd_no, is_terminated, write_err):
        """キャプチャアドレスセットコマンドのエラー情報を保持するクラス"""
        super().__init__(CaptureAddrSetCmd.ID, cmd_no, is_terminated)
        self.__write_err = write_err


    @property
    def write_err(self):
        """書き込みエラーフラグ

        Returns:
            bool: コマンドの実行中にキャプチャアドレスの書き込みエラーが発生した場合 True
        """
        return self.__write_err


    def __str__(self):
        return  (
            'CaptureAddrSetCmdErr\n' +
            '  - command ID  : {}\n'.format(self.cmd_id) +
            '  - command No  : {}\n'.format(self.cmd_no) +
            '  - terminated  : {}\n'.format(self.is_terminated) +
            '  - write error : {}'.format(self.write_err))


class FeedbackCalcOnClassificationCmdErr(SequencerCmdErr):
    
    def __init__(self, cmd_no, is_terminated, read_err):
        """四値化結果をフィードバック値とするフィードバック値計算コマンドのエラー情報を保持するクラス"""
        super().__init__(FeedbackCalcOnClassificationCmd.ID, cmd_no, is_terminated)
        self.__read_err = read_err


    @property
    def read_err(self):
        """読み出しエラーフラグ

        Returns:
            bool: コマンドの実行中に四値化結果の読み出しエラーが発生した場合 True
        """
        return self.__read_err


    def __str__(self):
        return  (
            'FeedbackCalcOnClassificationCmdErr\n' +
            '  - command ID : {}\n'.format(self.cmd_id) +
            '  - command No : {}\n'.format(self.cmd_no) +
            '  - terminated : {}\n'.format(self.is_terminated) +
            '  - read error : {}'.format(self.read_err))


class WaveGenEndFenceCmdErr(SequencerCmdErr):
    
    def __init__(self, cmd_no, is_terminated, awg_id_list):
        """波形出力完了確認コマンドのエラー情報を保持するクラス"""
        super().__init__(WaveGenEndFenceCmd.ID, cmd_no, is_terminated)
        self.__awg_id_list = copy.copy(awg_id_list)


    @property
    def awg_id_list(self):
        """指定した時刻に波形出力が完了していなかった AWG の ID のリスト
        
        Returns:
            list of AWG: 指定した時刻に波形出力が完了していなかった AWG の ID のリスト
        """
        return copy.copy(self.__awg_id_list)


    def __str__(self):
        awg_id_list = [int(awg_id) for awg_id in self.__awg_id_list]
        return  (
            'WaveGenEndFenceCmdErr\n' +
            '  - command ID : {}\n'.format(self.cmd_id) +
            '  - command No : {}\n'.format(self.cmd_no) +
            '  - terminated : {}\n'.format(self.is_terminated) +
            '  - AWG IDs    : {}'.format(awg_id_list))
