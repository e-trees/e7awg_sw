from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any, Final
from collections.abc import Iterable, Sequence
from .hwdefs import CaptureParamElem, CaptureUnit, CaptureModule, AWG, FeedbackChannel, FourClassifierChannel
from .hwparam import \
    CLASSIFICATION_RESULT_SIZE, MAX_CAPTURE_SIZE, CAPTURE_RAM_WORD_SIZE, CAPTURE_DATA_ALIGNMENT_SIZE, \
    MAX_WAVE_REGISTRY_ENTRIES, MAX_CAPTURE_PARAM_REGISTRY_ENTRIES


class SequencerCmd(object, metaclass = ABCMeta):

    MAX_CMD_NO: Final = 0xFFFF #: 指定可能なコマンド番号の最大値

    def __init__(self, cmd_id: int, cmd_no: int, stop_seq: bool) -> None:

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
    def cmd_id(self) -> int:
        """このコマンドの種類を表す ID

        Returns:
            int: このコマンドの種類を表す ID
        """
        return self.__cmd_id


    @property
    def cmd_no(self) -> int:
        """このコマンドのコマンド番号
        
        Returns:
            int: このコマンドのコマンド番号
        """
        return self.__cmd_no


    @property
    def stop_seq(self) -> bool:
        """シーケンサ停止フラグ
        
        Returns:
            bool: シーケンサ停止フラグ
        """
        return self.__stop_seq


    def _validate_capture_unit_id(self, capture_unit_id_list: list[CaptureUnit]) -> None:
        if ((not isinstance(capture_unit_id_list, list)) or 
            (not capture_unit_id_list)                   or # 空だと False であることを保証するために list 型を指定する
            (not CaptureUnit.includes(*capture_unit_id_list))):
            raise ValueError("Invalid capture unit ID '{}'".format(capture_unit_id_list))


    def _validate_awg_id(self, awg_id_list: list[AWG]) -> None:
        if ((not isinstance(awg_id_list, list)) or
            (not awg_id_list)                   or
            (not AWG.includes(*awg_id_list))):
            raise ValueError("Invalid AWG ID '{}'".format(awg_id_list))


    def _validate_cap_param_elems(self, elems: list[CaptureParamElem]) -> None:
        if ((not isinstance(elems, list)) or
            (not elems)                   or
            (not CaptureParamElem.includes(*elems))):
            raise ValueError("Invalid capture parameter elements.  ({})".format(elems))


    def _validate_feedback_channel_id(self, feedback_channel_id: FeedbackChannel) -> None:
        if not FeedbackChannel.includes(feedback_channel_id):
            raise ValueError("Invalid feedback channel ID '{}'".format(feedback_channel_id))


    def _validate_key_table(
        self, key_table: int | Sequence[int], max_registry_key: int
    ) -> None:
        if isinstance(key_table, int) and self._is_in_range(0, max_registry_key, key_table):
            return

        if not isinstance(key_table, Sequence):
            raise ValueError(
                "The type of 'key_table' must be Sequence.  ({})".format(key_table))

        # 2022/08/02 現在, フィードバック値は四値化結果だけなので, レジストリキーの数 = 4 という制約を加えておく.
        if len(key_table) != 4:
            raise ValueError(
                "The number of elements in 'key_table' must be 4.  ({})".format(len(key_table)))

        for key in key_table:
            if not (isinstance(key, int) and self._is_in_range(0, max_registry_key, key)):
                raise ValueError(
                    "The elements in 'key_table' must be integers between {} and {} inclusive.  ({})"
                    .format(0, max_registry_key, key_table))


    def _validate_four_cls_channel_id(
        self, four_cls_channel_id: FourClassifierChannel, ext_trig_flag: bool
    ) -> None:
        if ext_trig_flag and four_cls_channel_id != FourClassifierChannel.U0:
            raise ValueError(
                "Invalid four-classifier value channel ID for External Trigger.'{}'."
                .format(four_cls_channel_id))

        if not FourClassifierChannel.includes(four_cls_channel_id):
            raise ValueError(
                "Invalid four-classifier value channel ID '{}'".format(four_cls_channel_id))


    def _validate_cmd_offset(self, offset: int, min: int, max: int) -> None:
        if isinstance(offset, int) and  self._is_in_range(min, max, offset):
            return
        
        raise ValueError(
            "The branch offset must be integers between {} and {} inclusive.  ({})"
            .format(min, max, offset))


    def _to_bit_field(self, bit_pos_list: Iterable[int]) -> int:
        bit_field = 0
        for bit_pos in bit_pos_list:
            bit_field |= 1 << bit_pos
        return bit_field


    def _is_in_range(self, min: int, max: int, val: int) -> bool:
        return (min <= val) and (val <= max)
    

    def _to_list(self, val: object) -> list:
        if isinstance(val, Iterable):
            return list(val)
        else:
            return [val]


    @abstractmethod
    def serialize(self) -> bytes:
        pass


    @abstractmethod
    def size(self) -> int:
        """serialize した際のコマンドのバイト数"""
        pass


class AwgStartCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID: Final = 1
    #: AWG スタート時刻に指定可能な最大値
    MAX_START_TIME: Final = 0x7FFFFFFF_FFFFFFFF
    #: AWG を即時スタートする場合に start_time に指定する値．
    IMMEDIATE: Final = -1

    def __init__(
        self,
        cmd_no: int,
        awg_id_list: Iterable[AWG] | AWG,
        start_time: int,
        wait: bool = False,
        stop_seq: bool = False
    ) -> None:
        """AWG を指定した時刻にスタートするコマンド

        Args:
            cmd_no (int): コマンド番号
            awg_id_list (Iterable of AWG | AWG): 波形の出力を開始する AWG のリスト
            start_time (int):
                | AWG をスタートする時刻.
                | シーケンサが動作を開始した時点を 0 として, start_time * 8[ns] 後に AWG がスタートする.
                | 負の値を入力した場合, AWG を即時スタートする．
                | このとき, AWG はコマンドの実行と同時に波形出力準備を行い, 
                | awg_id_list で指定した全ての AWG の準備が完了するとスタートする.
            wait (bool):
                | True -> AWG をスタートした後, 波形の出力完了を待ってからこのコマンドを終了する
                | False -> AWG をスタートした後, このコマンドを終了する.
            stop_seq (bool): 
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
        """
        super().__init__(self.ID, cmd_no, stop_seq)
        awg_id_list = self._to_list(awg_id_list)
        self._validate_awg_id(awg_id_list)

        if not (isinstance(start_time, int) and (start_time <= self.MAX_START_TIME)):
            raise ValueError(
                "'start_time' must be less than or equal to {}.  '{}' was set."
                .format(self.MAX_START_TIME, start_time))

        self.__awg_id_list: list[AWG] = awg_id_list
        self.__start_time = start_time
        self.__wait = wait
        self.__cmd_bytes = self.__gen_cmd_bytes()


    @property
    def awg_id_list(self) -> list[AWG]:
        return list(self.__awg_id_list)


    @property
    def start_time(self) -> int:
        return self.__start_time


    @property
    def wait(self) -> bool:
        return self.__wait


    def __gen_cmd_bytes(self) -> bytes:
        awg_id_list = self._to_bit_field(self.__awg_id_list)
        start_time = 0xFFFFFFFF_FFFFFFFF if self.start_time < 0 else self.start_time
        cmd = (
            int(self.stop_seq)          |
            self.cmd_id          << 1   |
            self.cmd_no          << 8   |
            awg_id_list          << 24  |
            start_time           << 40  |
            self.wait            << 104)
        return cmd.to_bytes(16, 'little')


    def serialize(self) -> bytes:
        return self.__cmd_bytes


    def size(self) -> int:
        return len(self.__cmd_bytes)


class CaptureEndFenceCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID: Final = 2
    #: キャプチャ完了確認時刻に指定可能な最大値
    MAX_END_TIME: Final = 0x7FFFFFFF_FFFFFFFF

    def __init__(
        self,
        cmd_no: int,
        capture_unit_id_list: Iterable[CaptureUnit] | CaptureUnit,
        end_time: int,
        wait: bool = True,
        terminate: bool = False,
        stop_seq: bool = False
    ) -> None:
        """キャプチャ終了フェンスコマンド
        
        | 'end_time' で指定した時刻まで待ってからキャプチャが完了しているかを調べるコマンド.

        Args:
            cmd_no (int): コマンド番号
            capture_unit_id_list (Iterable of CaptureUnit | CaptureUnit): キャプチャの完了を調べるキャプチャユニットのリスト.
            end_time (int):
                | キャプチャが完了しているかを調べる時刻.
                | シーケンサが動作を開始した時点を 0 として, end_time * 8[ns] 後にキャプチャの完了をチェックする.
            wait (bool):
                | True -> end_time の後もキャプチャが完了していないキャプチャユニットの終了を待つ.
                | False -> end_time の後, キャプチャの完了を待たずにコマンドを終了する.
                | 'end_time' で指定した時刻までにこのコマンドを実行できなかった場合, 引数に関係なくキャプチャの完了待ちは行われない.
            terminate (bool): 
                | キャプチャユニット停止フラグ.
                | True の場合 end_time の時点でキャプチャが完了していないキャプチャユニットを強制停止する.
                | 'end_time' で指定した時刻までにこのコマンドを実行できなかった場合, 引数に関係なくキャプチャユニットの強制停止は行われない.
            stop_seq (bool): 
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
        """
        super().__init__(self.ID, cmd_no, stop_seq)
        capture_unit_id_list = self._to_list(capture_unit_id_list)
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

        self.__capture_unit_id_list: list[CaptureUnit] = capture_unit_id_list
        self.__end_time = end_time
        self.__wait = wait
        self.__terminate = terminate
        self.__cmd_bytes = self.__gen_cmd_bytes()


    @property
    def capture_unit_id_list(self) -> list[CaptureUnit]:
        return list(self.__capture_unit_id_list)


    @property
    def end_time(self) -> int:
        return self.__end_time


    @property
    def wait(self) -> bool:
        return self.__wait


    @property
    def terminate(self) -> bool:
        return self.__terminate


    def __gen_cmd_bytes(self) -> bytes:
        capture_unit_id_bits = self._to_bit_field(self.__capture_unit_id_list)
        cmd = (
            int(self.stop_seq)              |
            self.cmd_id              << 1   |
            self.cmd_no              << 8   |
            capture_unit_id_bits     << 24  |
            self.end_time            << 40  |
            self.terminate           << 104 |
            self.wait                << 105)
        return cmd.to_bytes(16, 'little')


    def serialize(self) -> bytes:
        return self.__cmd_bytes


    def size(self) -> int:
        return len(self.__cmd_bytes)


class WaveSequenceSetCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID: Final = 3

    def __init__(
        self,
        cmd_no: int,
        awg_id_list: Iterable[AWG] | AWG,
        key_table: Sequence[int] | int,
        feedback_channel_id: FeedbackChannel = FeedbackChannel.U0,
        stop_seq: bool = False
    ) -> None:
        """フィードバック値に応じて波形シーケンスを AWG にセットするコマンド

        Args:
            cmd_no (int): コマンド番号
            awg_id_list (Iterable of AWG | AWG): 波形シーケンスをセットする AWG のリスト.
            key_table (Sequence of int | int):
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
        awg_id_list = self._to_list(awg_id_list)
        self._validate_awg_id(awg_id_list)
        self._validate_feedback_channel_id(feedback_channel_id)
        self._validate_key_table(key_table, MAX_WAVE_REGISTRY_ENTRIES - 1)
        if isinstance(key_table, int):
            key_table = [key_table] * 4

        self.__awg_id_list: list[AWG] = awg_id_list
        self.__feedback_channel_id = feedback_channel_id
        self.__key_table = list(key_table)
        self.__cmd_bytes = self.__gen_cmd_bytes()


    @property
    def awg_id_list(self) -> list[AWG]:
        return list(self.__awg_id_list)


    @property
    def feedback_channel_id(self) -> FeedbackChannel:
        return self.__feedback_channel_id


    @property
    def key_table(self) -> list[int]:
        return list(self.__key_table)


    def __gen_cmd_bytes(self) -> bytes:
        awg_id_bits = self._to_bit_field(self.__awg_id_list)
        key_table_bits = 0
        for i in range(len(self.__key_table)):
            key_table_bits |= self.__key_table[i] << (i * 10)

        cmd = (
            int(self.stop_seq)             |
            self.cmd_id              << 1  |
            self.cmd_no              << 8  |
            awg_id_bits              << 24 |
            self.feedback_channel_id << 40 |
            key_table_bits           << 44)
        return cmd.to_bytes(16, 'little')


    def serialize(self) -> bytes:
        return self.__cmd_bytes


    def size(self) -> int:
        return len(self.__cmd_bytes)


class CaptureParamSetCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID: Final = 4

    def __init__(
        self,
        cmd_no: int,
        capture_unit_id_list: Iterable[CaptureUnit] | CaptureUnit,
        key_table: Sequence[int] | int,
        feedback_channel_id: FeedbackChannel = FeedbackChannel.U0,
        param_elems: Iterable[CaptureParamElem] | CaptureParamElem = CaptureParamElem.all(),
        stop_seq: bool = False
    ) -> None:
        """フィードバック値に応じてキャプチャパラメータをキャプチャユニットにセットするコマンド

        Args:
            cmd_no (int): コマンド番号
            capture_unit_id_list (Iterable of CaptureUnit | CaptureUnit): キャプチャパラメータをセットするキャプチャユニットのリスト.
            key_table (Sequence of int | int):
                | キャプチャパラメータを登録したレジストリのキーのリスト.
                | key_table[フィードバック値] = 設定したいキャプチャパラメータを登録したレジストリのキー
                | となるように設定する.
                | レジストリキーに int 値 1 つを指定すると, フィードバック値によらず, 
                | その値のキーに登録されたキャプチャパラメータを設定する.
            feedback_channel_id (FeedbackChannel): 
                | 参照するフィードバックチャネルの ID.
            param_elems (Iterable of CaptureParamElem | CaptureParamElem):
                | キャプチャパラメータの中の設定したい要素のリスト.
                | ここに指定しなかった要素は, キャプチャユニットに設定済みの値のまま更新されない.
                | 特に, 「総和区間数」「総和区間長」「ポストブランク長」の 3 つは, セットで更新しない場合,
                | キャプチャユニットが保持するパラメータと不整合を起こす可能性がある点に注意.
            stop_seq (bool):
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
        """
        super().__init__(self.ID, cmd_no, stop_seq)
        capture_unit_id_list = self._to_list(capture_unit_id_list)
        self._validate_capture_unit_id(capture_unit_id_list)
        self._validate_feedback_channel_id(feedback_channel_id)
        param_elems = self._to_list(param_elems)
        self._validate_cap_param_elems(param_elems)
        self._validate_key_table(key_table, MAX_CAPTURE_PARAM_REGISTRY_ENTRIES - 1)
        if isinstance(key_table, int):
            key_table = [key_table] * 4
        
        self.__capture_unit_id_list: list[CaptureUnit] = capture_unit_id_list
        self.__feedback_channel_id = feedback_channel_id
        self.__key_table = list(key_table)
        self.__param_elems = param_elems
        self.__cmd_bytes = self.__gen_cmd_bytes()


    @property
    def capture_unit_id_list(self) -> list[CaptureUnit]:
        return list(self.__capture_unit_id_list)


    @property
    def feedback_channel_id(self) -> FeedbackChannel:
        return self.__feedback_channel_id


    @property
    def key_table(self) -> list[int]:
        return list(self.__key_table)


    @property
    def param_elems(self) -> list[CaptureParamElem]:
        return list(self.__param_elems)


    def __gen_cmd_bytes(self) -> bytes:
        capture_unit_id_bits = self._to_bit_field(self.__capture_unit_id_list)        
        param_elem_bits = self._to_bit_field(self.__param_elems)

        key_table_bits = 0
        for i in range(len(self.__key_table)):
            key_table_bits |= self.__key_table[i] << (i * 10)

        cmd = (
            int(self.stop_seq)             |
            self.cmd_id              << 1  |
            self.cmd_no              << 8  |
            capture_unit_id_bits     << 24 |
            self.feedback_channel_id << 40 |
            param_elem_bits          << 44 |
            key_table_bits           << 60)
        return cmd.to_bytes(16, 'little')


    def serialize(self) -> bytes:
        return self.__cmd_bytes


    def size(self) -> int:
        return len(self.__cmd_bytes)


class CaptureAddrSetCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID: Final = 5

    def __init__(
        self,
        cmd_no: int,
        capture_unit_id_list: Iterable[CaptureUnit] | CaptureUnit,
        byte_offset: int,
        stop_seq: bool = False
    ) -> None:
        """キャプチャアドレスをセットするコマンド

        Args:
            cmd_no (int): コマンド番号
            capture_unit_id_list (Iterable of CaptureUnit | CaptureUnit): キャプチャアドレスをセットするキャプチャユニットのリスト.
            byte_offset (int): 
                | 各キャプチャユニットのキャプチャ領域の先頭アドレス + byte_offset を, 次のキャプチャのデータの格納先とする.
            stop_seq (bool): 
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
        """
        super().__init__(self.ID, cmd_no, stop_seq)
        capture_unit_id_list = self._to_list(capture_unit_id_list)
        self._validate_capture_unit_id(capture_unit_id_list)

        if not (isinstance(byte_offset, int) and
                (0 <= byte_offset and byte_offset < MAX_CAPTURE_SIZE)):
            raise ValueError(
                "'byte_offset' must be an integer between {} and {} inclusive.  '{}' was set."
                .format(0, MAX_CAPTURE_SIZE - 1, byte_offset))

        if (byte_offset % CAPTURE_DATA_ALIGNMENT_SIZE) != 0:
            raise ValueError(
                "'byte_offset' must be a multiple of {}.  '{}' was set."
                .format(CAPTURE_DATA_ALIGNMENT_SIZE, byte_offset))
        
        self.__capture_unit_id_list: list[CaptureUnit] = capture_unit_id_list
        self.__byte_offset = byte_offset
        self.__cmd_bytes = self.__gen_cmd_bytes()


    @property
    def capture_unit_id_list(self) -> list[CaptureUnit]:
        return list(self.__capture_unit_id_list)


    @property
    def byte_offset(self) -> int:
        return self.__byte_offset


    def __gen_cmd_bytes(self) -> bytes:
        capture_unit_id_bits = self._to_bit_field(self.__capture_unit_id_list)
        cmd = (
            int(self.stop_seq)         |
            self.cmd_id          << 1  |
            self.cmd_no          << 8  |
            capture_unit_id_bits << 24 |
            self.byte_offset     << 40)
        return cmd.to_bytes(16, 'little')


    def serialize(self) -> bytes:
        return self.__cmd_bytes


    def size(self) -> int:
        return len(self.__cmd_bytes)


class FeedbackCalcOnClassificationCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID: Final = 6

    def __init__(
        self,
        cmd_no: int,
        capture_unit_id_list: Iterable[CaptureUnit] | CaptureUnit,
        byte_offset: int,
        elem_offset: int = 0,
        stop_seq: bool = False
    ) -> None:
        """四値化結果をフィードバック値とするフィードバック値計算コマンド

        | フィードバックチャネル i のフィードバック値 (FB_VAL(i)) は, 以下の式で求まる.
        | FB_VAL(i) = ビットアドレスが FB_BIT_ADDR(i) のビットとその次のビットを並べた 2 bits の値
        | FB_BIT_ADDR(i) = (CaptureUnitAddr(i) + byte_offset) * 8 + elem_offset * 2 (= 四値化結果のビットアドレス)
        | CaptureUnitAddr(i) = キャプチャユニット i に割り当てられたキャプチャ領域の先頭アドレス
        | i ∈ capture_unit_id_list

        Args:
            cmd_no (int): コマンド番号
            capture_unit_id_list (Iterable of CaptureUnit | CaptureUnit): 
                | フィードバック値とする四値化結果が格納されたキャプチャ領域を持つキャプチャユニットの ID のリスト.
                | 更新されるフィードバックチャネルの ID のリストでもある.
            byte_offset (int): フィードバック値とするデータのバイト単位での位置
            elem_offset (int): フィードバック値とするデータの四値化結果単位での位置
            stop_seq (bool): 
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
        """        
        super().__init__(self.ID, cmd_no, stop_seq)
        capture_unit_id_list = self._to_list(capture_unit_id_list)
        self._validate_capture_unit_id(capture_unit_id_list)

        if not (isinstance(byte_offset, int) and
                (0 <= byte_offset and byte_offset < MAX_CAPTURE_SIZE)):
           raise ValueError(
               "'byte_offset' must be an integer between {} and {} inclusive.  '{}' was set."
               .format(0, MAX_CAPTURE_SIZE - 1, byte_offset))

        max_results = MAX_CAPTURE_SIZE * (8 // CLASSIFICATION_RESULT_SIZE)
        if not (isinstance(elem_offset, int) and
                self._is_in_range(0, max_results - 1, elem_offset)):
           raise ValueError(
               "'elem_offset' must be an integer between {} and {} inclusive.  '{}' was set."
               .format(0, max_results - 1, elem_offset))

        self.__bit_offset = byte_offset * 8 + elem_offset * CLASSIFICATION_RESULT_SIZE
        if self.__bit_offset >= MAX_CAPTURE_SIZE * 8:
            raise ValueError(
                'The specified classification result is not in the capture data area.  ' + 
                'byte_offset = {}, elem_offset = {}'.format(byte_offset, elem_offset))
        
        self.__capture_unit_id_list: list[CaptureUnit] = capture_unit_id_list
        self.__byte_offset = byte_offset
        self.__elem_offset = elem_offset
        self.__cmd_bytes = self.__gen_cmd_bytes()
        

    @property
    def capture_unit_id_list(self) -> list[CaptureUnit]:
        return list(self.__capture_unit_id_list)


    @property
    def byte_offset(self) -> int:
        return self.__byte_offset


    @property
    def elem_offset(self) -> int:
        return self.__elem_offset


    def __gen_cmd_bytes(self) -> bytes:
        byte_offset = self.__bit_offset // (CAPTURE_RAM_WORD_SIZE * 8) * CAPTURE_RAM_WORD_SIZE
        elem_offset = (self.__bit_offset % (CAPTURE_RAM_WORD_SIZE * 8)) // CLASSIFICATION_RESULT_SIZE
        capture_unit_id_bits = self._to_bit_field(self.__capture_unit_id_list)
        cmd = (
            int(self.stop_seq)         |
            self.cmd_id          << 1  |
            self.cmd_no          << 8  |
            capture_unit_id_bits << 24 |
            byte_offset          << 40 |
            elem_offset          << 76)
        return cmd.to_bytes(16, 'little')


    def serialize(self) -> bytes:
        return self.__cmd_bytes


    def size(self) -> int:
        return len(self.__cmd_bytes)


class WaveGenEndFenceCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID: Final = 7
    #: AWG の波形出力完了を確認する時刻に指定可能な最大値
    MAX_END_TIME: Final = 0x7FFFFFFF_FFFFFFFF

    def __init__(
        self,
        cmd_no: int,
        awg_id_list: Iterable[AWG] | AWG,
        end_time: int,
        wait: bool = True,
        terminate: bool = False,
        stop_seq: bool = False
    ) -> None:
        """波形出力終了フェンスコマンド

        | 'end_time' で指定した時刻まで待ってから AWG の波形出力が完了しているかを調べるコマンド.

        Args:
            cmd_no (int): コマンド番号
            awg_id_list (Iterable of AWG | AWG): 波形出力完了を調べる AWG のリスト.
            end_time (int):
                | AWG の波形出力が完了しているかを調べる時刻.
                | シーケンサが動作を開始した時点を 0 として, end_time * 8[ns] 後に波形出力の完了をチェックする.
            wait (bool):
                | True -> end_time の後も波形出力が完了していない AWG の終了を待つ.
                | False -> end_time の後, 波形出力の完了を待たずにコマンドを終了する.
                | 'end_time' で指定した時刻までにこのコマンドを実行できなかった場合, 引数に関係なく波形出力の完了待ちは行われない.
            terminate (bool): 
                | AWG 停止フラグ.
                | True の場合 end_time の時点で波形の出力が完了していない AWG を強制停止する.
                | 'end_time' で指定した時刻までにこのコマンドを実行できなかった場合, 引数に関係なく AWG の強制停止は行われない.
            stop_seq (bool): 
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
        """
        super().__init__(self.ID, cmd_no, stop_seq)
        awg_id_list = self._to_list(awg_id_list)
        self._validate_awg_id(awg_id_list)

        if not (isinstance(end_time, int) and self._is_in_range(0, self.MAX_END_TIME, end_time)):
            raise ValueError(
                "'end_time' must be an integer between {} and {} inclusive.  '{}' was set."
                .format(0, self.MAX_END_TIME, end_time))

        if not isinstance(wait, bool):
            raise ValueError("The type of 'wait' must be 'bool'.  '{}' was set.".format(wait))

        if not isinstance(terminate, bool):
            raise ValueError("The type of 'terminate' must be 'bool'.  '{}' was set.".format(terminate))

        self.__awg_id_list: list[AWG] = awg_id_list
        self.__end_time = end_time
        self.__wait = wait
        self.__terminate = terminate
        self.__cmd_bytes = self.__gen_cmd_bytes()


    @property
    def awg_id_list(self) -> list[AWG]:
        return list(self.__awg_id_list)


    @property
    def end_time(self) -> int:
        return self.__end_time


    @property
    def wait(self) -> bool:
        return self.__wait


    @property
    def terminate(self) -> bool:
        return self.__terminate


    def __gen_cmd_bytes(self) -> bytes:
        awg_id_bits = self._to_bit_field(self.__awg_id_list)
        cmd = (
            int(self.stop_seq)              |
            self.cmd_id              << 1   |
            self.cmd_no              << 8   |
            awg_id_bits              << 24  |
            self.end_time            << 40  |
            self.terminate           << 104 |
            self.wait                << 105)
        return cmd.to_bytes(16, 'little')


    def serialize(self) -> bytes:
        return self.__cmd_bytes


    def size(self) -> int:
        return len(self.__cmd_bytes)


class ResponsiveFeedbackCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID: Final = 8
    #: 1 回目の AWG スタート時刻に指定可能な最大値
    MAX_START_TIME: Final = 0x7FFFFFFF_FFFFFFFF
    #: AWG を即時スタートする場合に start_time に指定する値．
    IMMEDIATE: Final = -1

    def __init__(
        self,
        cmd_no: int,
        awg_id_list: Iterable[AWG] | AWG,
        start_time: int,
        wait: bool = False,
        stop_seq: bool = False
    ) -> None:
        """高速フィードバック処理を行うコマンド

        | 高速フィードバック処理は
        |   1. AWG から波形を出力 (1 回目)
        |   2. キャプチャユニットで波形データを取得し四値化結果を算出
        |   3. 四値化結果に応じて波形シーケンスを AWG に設定
        |   4. AWG から波形を出力 (2 回目)
        | を行う.
        |
        | 高速フィードバック処理で参照する四値化結果のチャネルと波形シーケンスの ID は,
        | WaveSequenceSelectionCmd オブジェクトで作れるシーケンサコマンドを使って指定する.

        Args:
            cmd_no (int): コマンド番号
            awg_id_list (Iterable of AWG | AWG): 波形を出力する AWG のリスト
            start_time (int):
                | 1 回目に AWG をスタートする時刻.
                | シーケンサが動作を開始した時点を 0 として, start_time * 8[ns] 後に AWG がスタートする.
                | 負の値を入力した場合, AWG を即時スタートする．
                | このとき, AWG はコマンドの実行と同時に波形出力準備を行い, 
                | awg_id_list で指定した全ての AWG の準備が完了するとスタートする.
            wait (bool):
                | True -> 2 回目に AWG をスタートした後, 波形の出力完了を待ってからこのコマンドを終了する
                | False -> 2 回目に AWG をスタートした後, このコマンドを終了する.
            stop_seq (bool): 
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
        """
        super().__init__(self.ID, cmd_no, stop_seq)
        awg_id_list = self._to_list(awg_id_list)
        self._validate_awg_id(awg_id_list)

        if not (isinstance(start_time, int) and (start_time <= self.MAX_START_TIME)):
            raise ValueError(
                "'start_time' must be less than or equal to {}.  '{}' was set."
                .format(self.MAX_START_TIME, start_time))

        self.__awg_id_list: list[AWG] = awg_id_list
        self.__start_time = start_time
        self.__wait = wait
        self.__cmd_bytes = self.__gen_cmd_bytes()


    @property
    def awg_id_list(self) -> list[AWG]:
        return list(self.__awg_id_list)


    @property
    def start_time(self) -> int:
        return self.__start_time


    @property
    def wait(self) -> bool:
        return self.__wait


    def __gen_cmd_bytes(self) -> bytes:
        awg_id_list = self._to_bit_field(self.__awg_id_list)
        start_time = 0xFFFFFFFF_FFFFFFFF if self.start_time < 0 else self.start_time
        cmd = (
            int(self.stop_seq)          |
            self.cmd_id          << 1   |
            self.cmd_no          << 8   |
            awg_id_list          << 24  |
            start_time           << 40  |
            self.wait            << 104)
        return cmd.to_bytes(16, 'little')


    def serialize(self) -> bytes:
        return self.__cmd_bytes


    def size(self) -> int:
        return len(self.__cmd_bytes)


class WaveSequenceSelectionCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID: Final = 9

    def __init__(
        self,
        cmd_no: int,
        awg_id_list: Iterable[AWG] | AWG,
        key_table: Sequence[int] | int,
        four_cls_channel_id: FourClassifierChannel = FourClassifierChannel.U0,
        ext_trig_flag: bool = False,
        stop_seq: bool = False
    ) -> None:
        """以下の 2 つのコマンドで AWG に設定する波形シーケンスを選択するコマンド.
            - 高速フィードバックコマンド
            - 四値付き外部トリガ待ち AWG スタートコマンド

        Args:
            cmd_no (int): コマンド番号
            awg_id_list (Iterable of AWG | AWG): 波形シーケンスをセットする AWG のリスト.
            key_table (Sequence of int | int):
                | 波形シーケンスを登録したレジストリのキーのリスト.
                | key_table[四値化結果] = 設定したい波形シーケンスを登録したレジストリのキー
                | となるように設定する.
                | レジストリキーに int 値 1 つを指定すると, 四値化結果によらず, 
                | そのキーに登録された波形シーケンスを設定する.
            four_cls_channel_id (FourClassifierChannel): 
                | 参照する四値化結果チャネルの ID.
            stop_seq (bool):
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
            ext_trig_flag (bool):
                | true の場合, 外部トリガ用の四値チャネルセットから, four_cls_channel_id で指定した四値チャネルを参照する.
                | false の場合, e7awg_hw 内部のキャプチャユニットに対応する四値チャネルセットを参照する.
        """
        super().__init__(self.ID, cmd_no, stop_seq)
        awg_id_list = self._to_list(awg_id_list)
        self._validate_awg_id(awg_id_list)
        self._validate_four_cls_channel_id(four_cls_channel_id, ext_trig_flag)
        self._validate_key_table(key_table, MAX_WAVE_REGISTRY_ENTRIES - 1)
        if isinstance(key_table, int):
            key_table = [key_table] * 4

        self.__awg_id_list: list[AWG] = awg_id_list
        self.__four_cls_channel_id = four_cls_channel_id
        self.__key_table = list(key_table)
        self.__ext_trig_flag = ext_trig_flag
        self.__cmd_bytes = self.__gen_cmd_bytes()


    @property
    def awg_id_list(self) -> list[AWG]:
        return list(self.__awg_id_list)


    @property
    def four_cls_channel_id(self) -> FourClassifierChannel:
        return self.__four_cls_channel_id


    @property
    def key_table(self) -> list[int]:
        return list(self.__key_table)


    @property
    def ext_trig_flag(self) -> bool:
        return self.__ext_trig_flag


    def __gen_cmd_bytes(self) -> bytes:
        awg_id_bits = self._to_bit_field(self.__awg_id_list)
        key_table_bits = 0
        for i in range(len(self.__key_table)):
            key_table_bits |= self.__key_table[i] << (i * 10)

        cmd = (
            int(self.stop_seq)             |
            self.cmd_id              << 1  |
            self.cmd_no              << 8  |
            awg_id_bits              << 24 |
            self.four_cls_channel_id << 40 |
            key_table_bits           << 44 |
            self.ext_trig_flag       << 127)
        return cmd.to_bytes(16, 'little')


    def serialize(self) -> bytes:
        return self.__cmd_bytes


    def size(self) -> int:
        return len(self.__cmd_bytes)


class BranchByFlagCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID: Final = 10
    #: 分岐先として指定可能なコマンドオフセットの最大値
    MAX_CMD_OFFSET: Final = 32767
    #: 分岐先として指定可能なコマンドオフセットの最小値
    MIN_CMD_OFFSET: Final = -32768

    def __init__(
        self,
        cmd_no: int,
        cmd_offset: int,
        stop_seq: bool = False
    ) -> None:
        """シーケンサ内部の専用フラグを参照する条件分岐コマンド.

        | 分岐が成立したとき, 次に実行されるコマンドが cmd_offset で指定したコマンドになる.
        | 分岐が成立しなかったとき, 次に実行されるコマンドはコマンドキューに並んだ 1 つ後のコマンドとなる.

        Args:
            cmd_no (int): コマンド番号
            cmd_offset (int):
                | 分岐成立時にこのコマンドの次に処理されるコマンドが cmd_offset 個後のコマンドになる.
                | 次に実行されるコマンドの例
                |   0  : このコマンド
                |   1  : コマンドキューに並んだ 1 つ後のコマンド
                |   -2 : コマンドキューに並んだ 2 つ前のコマンド
            stop_seq (bool):
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
        """
        super().__init__(self.ID, cmd_no, stop_seq)
        self._validate_cmd_offset(
            cmd_offset, self.MIN_CMD_OFFSET, self.MAX_CMD_OFFSET)
        self.__cmd_offset = cmd_offset
        self.__cmd_bytes = self.__gen_cmd_bytes()


    @property
    def cmd_offset(self) -> int:
        return self.__cmd_offset


    def __gen_cmd_bytes(self) -> bytes:
        cmd = (
            int(self.stop_seq)              |
            self.cmd_id                << 1 |
            self.cmd_no                << 8 |
            (self.cmd_offset & 0xFFFF) << 24)
        return cmd.to_bytes(16, 'little')


    def serialize(self) -> bytes:
        return self.__cmd_bytes


    def size(self) -> int:
        return len(self.__cmd_bytes)


class AwgStartWithExtTrigAndClsValCmd(SequencerCmd):
    #: コマンドの種類を表す ID
    ID: Final = 11
    #: タイムアウト時間に指定可能な最大値
    MAX_TIMEOUT: Final = 0xFFFFFFFF_FFFFFFFF

    def __init__(
        self,
        cmd_no: int,
        awg_id_list: Iterable[AWG] | AWG,
        timeout: int,
        wait: bool = False,
        stop_seq: bool = False
    ) -> None:
        """四値付き外部トリガ待ち AWG スタートコマンド

        | 本コマンドは, 
        |   1. 四値化結果の更新待ち
        |   2. 更新された四値化結果に応じて波形シーケンスを AWG に設定
        |   3. 外部 AWG スタートトリガの入力待ち
        |   4. AWG から波形を出力
        | を行う.
        |
        | 本コマンドの処理で参照する四値化結果のチャネルと波形シーケンスの ID は,
        | WaveSequenceSelectionCmd オブジェクトで作れるシーケンサコマンドを使って指定する.

        Args:
            cmd_no (int): コマンド番号
            awg_id_list (Iterable of AWG | AWG): 波形を出力する AWG のリスト
            timeout (int):
                | 1 回目に AWG をスタートする時刻.
                | 本コマンドの処理開始時点を 0 として, timeout * 8[ns] までに外部 AWG スタートトリガが入力されない場合, 
                | 本コマンドはエラーとなる.
            wait (bool):
                | True -> AWG をスタートした後, 波形の出力完了を待ってからこのコマンドを終了する
                | False -> AWG をスタートした後, このコマンドを終了する.
            stop_seq (bool): 
                | シーケンサ停止フラグ.
                | True の場合, このコマンドを実行後シーケンサはコマンドの処理を止める.
        """
        super().__init__(self.ID, cmd_no, stop_seq)
        awg_id_list = self._to_list(awg_id_list)
        self._validate_awg_id(awg_id_list)

        if not (isinstance(timeout, int) and (timeout <= self.MAX_TIMEOUT)):
            raise ValueError(
                "'timeout' must be less than or equal to {}.  '{}' was set."
                .format(self.MAX_TIMEOUT, timeout))

        self.__awg_id_list: list[AWG] = awg_id_list
        self.__timeout = timeout
        self.__wait = wait
        self.__cmd_bytes = self.__gen_cmd_bytes()


    @property
    def awg_id_list(self) -> list[AWG]:
        return list(self.__awg_id_list)


    @property
    def timeout(self) -> int:
        return self.__timeout


    @property
    def wait(self) -> bool:
        return self.__wait


    def __gen_cmd_bytes(self) -> bytes:
        awg_id_list = self._to_bit_field(self.__awg_id_list)
        cmd = (
            int(self.stop_seq)          |
            self.cmd_id          << 1   |
            self.cmd_no          << 8   |
            awg_id_list          << 24  |
            self.timeout         << 40  |
            self.wait            << 104)
        return cmd.to_bytes(16, 'little')


    def serialize(self) -> bytes:
        return self.__cmd_bytes


    def size(self) -> int:
        return len(self.__cmd_bytes)


class SequencerCmdErr(object):

    def __init__(self, cmd_id: int, cmd_no: int, is_terminated: bool) -> None:
        self.__cmd_id = cmd_id
        self.__cmd_no = cmd_no
        self.__is_terminated = is_terminated


    @property
    def cmd_id(self) -> int:
        """このエラーを起こしたコマンドの種類を表す ID

        Returns:
            int: このエラーを起こしたコマンドの種類を表す ID
        """
        return self.__cmd_id


    @property
    def cmd_no(self) -> int:
        """このエラーを起こしたコマンドのコマンド番号
        
        Returns:
            int: このエラーを起こしたコマンドのコマンド番号
        """
        return self.__cmd_no


    @property
    def is_terminated(self) -> bool:
        """ このエラーを起こしたコマンドが実行中に強制終了させられたかどうか

        Returns:
            bool:
                | True -> コマンドが実行中に強制終了させられた
                | False -> コマンドは実行中に強制終了させれていない
        """        
        return self.__is_terminated


class AwgStartCmdErr(SequencerCmdErr):

    def __init__(
        self,
        cmd_no: int,
        is_terminated: bool,
        awg_id_list: Iterable[AWG]
    ) -> None:
        """AWG スタートコマンドのエラー情報を保持するクラス"""
        super().__init__(AwgStartCmd.ID, cmd_no, is_terminated)
        self.__awg_id_list = list(awg_id_list)


    @property
    def awg_id_list(self) -> list[AWG]:
        """指定した時刻にスタートできなかった AWG の ID のリスト
        
        Returns:
            list of AWG: 指定した時刻にスタートできなかった AWG の ID のリスト
        """
        return list(self.__awg_id_list)


    def __str__(self) -> str:
        awg_id_list = [int(awg_id) for awg_id in self.__awg_id_list]
        return (
            'AwgStartCmdErr\n' +
            '  - command ID : {}\n'.format(self.cmd_id) +
            '  - command No : {}\n'.format(self.cmd_no) +
            '  - terminated : {}\n'.format(self.is_terminated) +
            '  - AWG IDs    : {}'.format(awg_id_list))


class CaptureEndFenceCmdErr(SequencerCmdErr):
    
    def __init__(
        self,
        cmd_no: int,
        is_terminated: bool,
        capture_unit_id_list: Iterable[CaptureUnit],
        is_in_time: bool
    ) -> None:
        """キャプチャ完了確認コマンドのエラー情報を保持するクラス"""
        super().__init__(CaptureEndFenceCmd.ID, cmd_no, is_terminated)
        self.__capture_unit_id_list = list(capture_unit_id_list)
        self.__is_in_time = is_in_time


    @property
    def capture_unit_id_list(self) -> list[CaptureUnit]:
        """指定した時刻にキャプチャが完了していなかったキャプチャユニットの ID のリスト
        
        Returns:
            list of CaptureUnit: 指定した時刻にキャプチャが完了していなかったキャプチャユニットの ID のリスト
        """
        return list(self.__capture_unit_id_list)


    @property
    def is_in_time(self) -> bool:
        """このエラーを出したコマンドが指定した時刻に実行されていたかどうか.

        | キャプチャ終了フェンスコマンドで指定した時刻より後に同コマンドが実行された場合, そのコマンドは失敗扱いとなり
        | このプロパティは False となる.
        
        Returns:
            bool: 指定した時刻以前にコマンドが実行されていた場合 True
        """
        return self.__is_in_time


    def __str__(self) -> str:
        capture_unit_id_list = [int(awg_id) for awg_id in self.__capture_unit_id_list]
        return (
            'CaptureEndFenceCmdErr\n' +
            '  - command ID       : {}\n'.format(self.cmd_id) +
            '  - command No       : {}\n'.format(self.cmd_no) +
            '  - terminated       : {}\n'.format(self.is_terminated) +
            '  - capture unit IDs : {}\n'.format(capture_unit_id_list) +
            '  - in time          : {}'.format(self.__is_in_time))


class WaveSequenceSetCmdErr(SequencerCmdErr):
    
    def __init__(
        self,
        cmd_no: int,
        is_terminated: bool,
        read_err: bool,
        write_err: bool
    ) -> None:
        """波形シーケンスセットコマンドのエラー情報を保持するクラス"""
        super().__init__(WaveSequenceSetCmd.ID, cmd_no, is_terminated)
        self.__read_err = read_err
        self.__write_err = write_err


    @property
    def read_err(self) -> bool:
        """読み出しエラーフラグ

        Returns:
            bool: コマンドの実行中に波形シーケンスの読み出しエラーが発生した場合 True
        """
        return self.__read_err


    @property
    def write_err(self) -> bool:
        """書き込みエラーフラグ

        Returns:
            bool: コマンドの実行中に波形シーケンスの書き込みエラーが発生した場合 True
        """
        return self.__write_err


    def __str__(self) -> str:
        return (
            'WaveSequenceSetCmdErr\n' +
            '  - command ID  : {}\n'.format(self.cmd_id) +
            '  - command No  : {}\n'.format(self.cmd_no) +
            '  - terminated  : {}\n'.format(self.is_terminated) +
            '  - read error  : {}\n'.format(self.read_err) +
            '  - write error : {}'.format(self.write_err))


class CaptureParamSetCmdErr(SequencerCmdErr):
    
    def __init__(
        self,
        cmd_no: int,
        is_terminated: bool,
        read_err: bool,
        write_err: bool
    ) -> None:
        """キャプチャパラメータセットコマンドのエラー情報を保持するクラス"""
        super().__init__(CaptureParamSetCmd.ID, cmd_no, is_terminated)
        self.__read_err = read_err
        self.__write_err = write_err


    @property
    def read_err(self) -> bool:
        """読み出しエラーフラグ

        Returns:
            bool: コマンドの実行中にキャプチャパラメータの読み出しエラーが発生した場合 True
        """
        return self.__read_err


    @property
    def write_err(self) -> bool:
        """書き込みエラーフラグ

        Returns:
            bool: コマンドの実行中にキャプチャパラメータの書き込みエラーが発生した場合 True
        """
        return self.__write_err


    def __str__(self) -> str:
        return (
            'CaptureParamSetCmdErr\n' +
            '  - command ID  : {}\n'.format(self.cmd_id) +
            '  - command No  : {}\n'.format(self.cmd_no) +
            '  - terminated  : {}\n'.format(self.is_terminated) +
            '  - read error  : {}\n'.format(self.read_err) +
            '  - write error : {}'.format(self.write_err))


class CaptureAddrSetCmdErr(SequencerCmdErr):
    
    def __init__(
        self,
        cmd_no: int,
        is_terminated: bool,
        write_err: bool
    ) -> None:
        """キャプチャアドレスセットコマンドのエラー情報を保持するクラス"""
        super().__init__(CaptureAddrSetCmd.ID, cmd_no, is_terminated)
        self.__write_err = write_err


    @property
    def write_err(self) -> bool:
        """書き込みエラーフラグ

        Returns:
            bool: コマンドの実行中にキャプチャアドレスの書き込みエラーが発生した場合 True
        """
        return self.__write_err


    def __str__(self) -> str:
        return (
            'CaptureAddrSetCmdErr\n' +
            '  - command ID  : {}\n'.format(self.cmd_id) +
            '  - command No  : {}\n'.format(self.cmd_no) +
            '  - terminated  : {}\n'.format(self.is_terminated) +
            '  - write error : {}'.format(self.write_err))


class FeedbackCalcOnClassificationCmdErr(SequencerCmdErr):
    
    def __init__(
        self,
        cmd_no: int,
        is_terminated: bool,
        read_err: bool
    ) -> None:
        """四値化結果をフィードバック値とするフィードバック値計算コマンドのエラー情報を保持するクラス"""
        super().__init__(FeedbackCalcOnClassificationCmd.ID, cmd_no, is_terminated)
        self.__read_err = read_err


    @property
    def read_err(self) -> bool:
        """読み出しエラーフラグ

        Returns:
            bool: コマンドの実行中に四値化結果の読み出しエラーが発生した場合 True
        """
        return self.__read_err


    def __str__(self) -> str:
        return (
            'FeedbackCalcOnClassificationCmdErr\n' +
            '  - command ID : {}\n'.format(self.cmd_id) +
            '  - command No : {}\n'.format(self.cmd_no) +
            '  - terminated : {}\n'.format(self.is_terminated) +
            '  - read error : {}'.format(self.read_err))


class WaveGenEndFenceCmdErr(SequencerCmdErr):
    
    def __init__(
        self,
        cmd_no: int,
        is_terminated: bool,
        awg_id_list: Iterable[AWG],
        is_in_time: bool
    ) -> None:
        """波形出力完了確認コマンドのエラー情報を保持するクラス"""
        super().__init__(WaveGenEndFenceCmd.ID, cmd_no, is_terminated)
        self.__awg_id_list = list(awg_id_list)
        self.__is_in_time = is_in_time


    @property
    def awg_id_list(self) -> list[AWG]:
        """指定した時刻に波形出力が完了していなかった AWG の ID のリスト
        
        Returns:
            list of AWG: 指定した時刻に波形出力が完了していなかった AWG の ID のリスト
        """
        return list(self.__awg_id_list)

    @property
    def is_in_time(self) -> bool:
        """このエラーを出したコマンドが指定した時刻に実行されていたかどうか.

        | 波形出力終了フェンスコマンドで指定した時刻より後に同コマンドが実行された場合, そのコマンドは失敗扱いとなり
        | このプロパティは False となる.
        
        Returns:
            bool: 指定した時刻以前にコマンドが実行されていた場合 True
        """
        return self.__is_in_time


    def __str__(self) -> str:
        awg_id_list = [int(awg_id) for awg_id in self.__awg_id_list]
        return (
            'WaveGenEndFenceCmdErr\n' +
            '  - command ID : {}\n'.format(self.cmd_id) +
            '  - command No : {}\n'.format(self.cmd_no) +
            '  - terminated : {}\n'.format(self.is_terminated) +
            '  - AWG IDs    : {}\n'.format(awg_id_list) + 
            '  - in time    : {}'.format(self.__is_in_time))


class ResponsiveFeedbackCmdErr(SequencerCmdErr):

    def __init__(
        self,
        cmd_no: int,
        is_terminated: bool,
        awg_id_list: Iterable[AWG],
        read_err: bool,
        write_err: bool
    ) -> None:
        """高速フィードバックコマンドのエラー情報を保持するクラス"""
        super().__init__(ResponsiveFeedbackCmd.ID, cmd_no, is_terminated)
        self.__awg_id_list = list(awg_id_list)
        self.__read_err = read_err
        self.__write_err = write_err


    @property
    def awg_id_list(self) -> list[AWG]:
        """指定した時刻にスタートできなかった AWG の ID のリスト
        
        Returns:
            list of AWG: 指定した時刻にスタートできなかった AWG の ID のリスト
        """
        return list(self.__awg_id_list)


    @property
    def read_err(self) -> bool:
        """読み出しエラーフラグ

        Returns:
            bool: コマンドの実行中に波形シーケンスの読み出しエラーが発生した場合 True
        """
        return self.__read_err


    @property
    def write_err(self) -> bool:
        """書き込みエラーフラグ

        Returns:
            bool: コマンドの実行中に波形シーケンスの書き込みエラーが発生した場合 True
        """
        return self.__write_err


    def __str__(self) -> str:
        awg_id_list = [int(awg_id) for awg_id in self.__awg_id_list]
        return (
            'ResponsiveFeedbackCmdErr\n' +
            '  - command ID  : {}\n'.format(self.cmd_id) +
            '  - command No  : {}\n'.format(self.cmd_no) +
            '  - terminated  : {}\n'.format(self.is_terminated) +
            '  - AWG IDs     : {}\n'.format(awg_id_list) +
            '  - read error  : {}\n'.format(self.read_err) +
            '  - write error : {}'.format(self.write_err))


class WaveSequenceSelectionCmdErr(SequencerCmdErr):

    def __init__(self, cmd_no: int, is_terminated: bool):
        """波形シーケンス選択コマンドのエラー情報を保持するクラス"""
        super().__init__(WaveSequenceSelectionCmd.ID, cmd_no, is_terminated)


    def __str__(self) -> str:
        return (
            'WaveSequenceSelectionCmdErr\n' +
            '  - command ID : {}\n'.format(self.cmd_id) +
            '  - command No : {}\n'.format(self.cmd_no) +
            '  - terminated : {}'.format(self.is_terminated))


class BranchByFlagCmdErr(SequencerCmdErr):

    def __init__(
        self,
        cmd_no: int,
        is_terminated: bool,
        out_of_range_err: bool,
        cmd_counter: int):
        """条件分岐コマンドのエラー情報を保持するクラス"""
        super().__init__(BranchByFlagCmd.ID, cmd_no, is_terminated)
        self.__out_of_range_err = out_of_range_err
        self.__cmd_counter = cmd_counter


    @property
    def out_of_range_err(self) -> bool:
        """範囲外分岐エラーフラグ

        Returns:
            bool: 分岐が成立してかつ分岐先となるコマンドカウンタ値が不正な値であった場合 True
        """
        return self.__out_of_range_err


    @property
    def cmd_counter(self) -> int:
        """範囲外分岐エラーが発生したときに分岐先となったコマンドカウンタ値

        Returns:
            int: 範囲外分岐エラーが発生したときに分岐先となったコマンドカウンタ値
        """
        return self.__cmd_counter


    def __str__(self) -> str:
        return (
            'BranchByFlagCmdErr\n' +
            '  - command ID         : {}\n'.format(self.cmd_id) +
            '  - command No         : {}\n'.format(self.cmd_no) +
            '  - terminated         : {}\n'.format(self.is_terminated) +
            '  - out of range error : {}\n'.format(self.out_of_range_err) +
            '  - cmd_counter        : {}'.format(self.cmd_counter))


class AwgStartWithExtTrigAndClsValCmdErr(SequencerCmdErr):

    def __init__(
        self,
        cmd_no: int,
        is_terminated: bool,
        awg_id_list: Iterable[AWG],
        read_err: bool,
        write_err: bool,
        timeout_err: bool
    ) -> None:
        """四値付き外部トリガ待ち AWG スタートコマンドのエラー情報を保持するクラス"""
        super().__init__(AwgStartWithExtTrigAndClsValCmd.ID, cmd_no, is_terminated)
        self.__awg_id_list = list(awg_id_list)
        self.__read_err = read_err
        self.__write_err = write_err
        self.__timeout_err = timeout_err


    @property
    def awg_id_list(self) -> list[AWG]:
        """スタートできなかった AWG の ID のリスト
        
        Returns:
            list of AWG: スタートできなかった AWG の ID のリスト
        """
        return list(self.__awg_id_list)


    @property
    def read_err(self) -> bool:
        """読み出しエラーフラグ

        Returns:
            bool: コマンドの実行中に波形シーケンスの読み出しエラーが発生した場合 True
        """
        return self.__read_err


    @property
    def write_err(self) -> bool:
        """書き込みエラーフラグ

        Returns:
            bool: コマンドの実行中に波形シーケンスの書き込みエラーが発生した場合 True
        """
        return self.__write_err


    @property
    def timeout_err(self) -> bool:
        """タイムアウトフラグ

        Returns:
            bool: 
                | 四値付き外部トリガ待ち AWG スタートコマンドで指定したタイムアウト時間が過ぎるまでに,
                | 外部 AWG スタートトリガが入力されなかった場合 true
        """
        return self.__timeout_err


    def __str__(self) -> str:
        awg_id_list = [int(awg_id) for awg_id in self.__awg_id_list]
        return (
            'AwgStartWithExtTrigAndClsValCmdErr\n' +
            '  - command ID    : {}\n'.format(self.cmd_id) +
            '  - command No    : {}\n'.format(self.cmd_no) +
            '  - terminated    : {}\n'.format(self.is_terminated) +
            '  - AWG IDs       : {}\n'.format(awg_id_list) +
            '  - read error    : {}\n'.format(self.read_err) +
            '  - write error   : {}\n'.format(self.write_err) +
            '  - timeout error : {}'.format(self.timeout_err))
