from logging import Logger
from collections.abc import Collection
from ..logger import get_file_logger, get_null_logger, log_error
from .hwdefs import DspUnit, ReductionOperation
from ..hwdefs import SampleDataType


class CaptureParam(object):
    """キャプチャパラメータを保持するクラス"""

    def __init__(
        self,
        *,
        enable_lib_log: bool = True,
        logger: Logger = get_null_logger()
    ) -> None:
        """
        Args:
            enable_lib_log (bool):
                | True -> ライブラリの標準のログ機能を有効にする.
                | False -> ライブラリの標準のログ機能を無効にする.
            logger (logging.Logger): ユーザ独自のログ出力に用いる Logger オブジェクト
        """
        self.__loggers = [logger]
        if enable_lib_log:
            self.__loggers.append(get_file_logger())

        self.__capture_delay: int = 0
        self.__capture_steps: list[tuple[int, int]] = []
        self.__dsp_list: set[DspUnit] = set()
        self.__capture_data_type: SampleDataType = SampleDataType.REAL
        self.__num_sum_words: int = 1
        self.__i_bin_threshold: int = 0
        self.__q_bin_threshold: int = 0
        self.__real_bin_threshold: int = 0
        self.__i_reduction_op: ReductionOperation = ReductionOperation.ANY
        self.__q_reduction_op: ReductionOperation = ReductionOperation.ANY
        self.__real_reduction_op: ReductionOperation = ReductionOperation.ANY 


    def add_capture_step(
        self,
        capture_target_len: int,
        post_blank_len: int) -> None:
        """キャプチャステップを追加する

        Args:
            capture_target_len (int): 
                | 追加するキャプチャステップのキャプチャターゲットの長さ. (単位: キャプチャワード)
            post_blank_len (int):
                | 追加するキャプチャステップのポストブランクの長さ. (単位: キャプチャワード)
        """
        try:
            if not isinstance(capture_target_len, int):
                raise ValueError(
                    f"Capture Target Length must be an integer.  {capture_target_len} was set.")

            if not isinstance(post_blank_len, int):
                raise ValueError(
                    f"Post Blank Length must be an integer.  {post_blank_len} was set.")
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        self.__capture_steps.append((capture_target_len, post_blank_len))


    @property
    def capture_steps(self) -> list[tuple[int, int]]:
        """登録されているキャプチャステップのリスト

        | キャプチャ区間の中の n 番目のキャプチャステップの情報がリストの n 番目に格納される.
        | 各キャプチャステップの情報はキャプチャターゲットとポストブランクのタプルで構成される.

        Returns:
            list[tuple[int, int]]: [(キャプチャターゲット長, ポストブランク長)]
        """
        return list(self.__capture_steps)


    @property
    def num_capture_steps(self) -> int:
        """現在登録されているキャプチャステップの数
        
        Returns:
            int: 現在登録されているキャプチャステップの数
        """
        return len(self.__capture_steps)
    

    @property
    def capture_delay(self) -> int:
        """キャプチャディレイ (単位: キャプチャワード)

        Args:
            val (int): キャプチャディレイ値

        Returns:
            int: 現在設定されているキャプチャディレイ
        """
        return self.__capture_delay


    @capture_delay.setter
    def capture_delay(self, val: int) -> None:
        if not isinstance(val, int):
            msg = f"Capture Delay must be an integer.  {val} was set."
            log_error(msg, *self.__loggers)
            raise ValueError(msg)
        self.__capture_delay = val


    @property
    def dsp_list(self) -> set[DspUnit]:
        """キャプチャの対象となるデータに適用する信号処理

        Args:
            *dsp_list (Collection[DspUnit]): キャプチャの対象となるデータに適用する信号処理
        
        Returns:
            set[DspUnit]: キャプチャの対象となるデータに適用する信号処理
        """
        return set(self.__dsp_list)
    

    @dsp_list.setter
    def dsp_list(self, val: Collection[DspUnit]) -> None:
        if not set(DspUnit).issuperset(val):
            msg = f"Invalid DSP Unit  {val}"
            log_error(msg, *self.__loggers)
            raise ValueError(msg)
        self.__dsp_list = set(val)


    @property
    def capture_data_type(self) -> SampleDataType:
        """キャプチャの対象となるデータの種類

        Args:
            val (SampleDataType): キャプチャの対象となるデータの種類

        Returns:
            SampleDataType: キャプチャの対象となるデータの種類
        """
        return self.__capture_data_type


    @capture_data_type.setter
    def capture_data_type(self, val: SampleDataType) -> None:
        if not isinstance(val, SampleDataType):
            msg = f"Invalide Capture Data Type.  {val} was set."
            log_error(msg, *self.__loggers)
            raise ValueError(msg)
        self.__capture_data_type = val


    @property
    def capture_section_len(self) -> int:
        """現在登録されているキャプチャステップから求められるキャプチャ区間の長さ (単位: キャプチャワード)"""
        length = 0
        for cap_step in self.__capture_steps:
            length += cap_step[0] + cap_step[1]

        return length


    @property
    def num_sum_words(self) -> int:
        """総和区間に含まれるキャプチャワードの数

        Args:
            val (int): 総和区間に含まれるキャプチャワードの数.

        Returns:
            int: 総和区間に含まれるキャプチャワードの数
        """
        return self.__num_sum_words


    @num_sum_words.setter
    def num_sum_words(self, val: int) -> None:
        if not isinstance(val, int):
            msg = f"The number of capture words to be added up must be an integer.  {val} was set."
            log_error(msg, *self.__loggers)
            raise ValueError(msg)

        self.__num_sum_words = val


    @property
    def i_bin_threshold(self) -> int:
        """I データに適用される二値化処理の二値化閾値

        Args:
            val (int): I データに適用される二値化処理の二値化閾値

        Returns:
            int: I データに適用される二値化処理の二値化閾値
        """
        return self.__i_bin_threshold


    @i_bin_threshold.setter
    def i_bin_threshold(self, val: int) -> None:
        if not isinstance(val, int):
            msg = f"I Binarization Threshold must be an integer.  {val} was set."
            log_error(msg, *self.__loggers)
            raise ValueError(msg)

        self.__i_bin_threshold = val


    @property
    def q_bin_threshold(self) -> int:
        """Q データに適用される二値化処理の二値化閾値

        Args:
            val (int): Q データに適用される二値化処理の二値化閾値

        Returns:
            int: Q データに適用される二値化処理の二値化閾値
        """
        return self.__q_bin_threshold


    @q_bin_threshold.setter
    def q_bin_threshold(self, val: int) -> None:
        if not isinstance(val, int):
            msg = f"Q Binarization Threshold must be an integer.  {val} was set."
            log_error(msg, *self.__loggers)
            raise ValueError(msg)

        self.__q_bin_threshold = val


    @property
    def real_bin_threshold(self) -> int:
        """Real データに適用される二値化処理の二値化閾値

        Args:
            val (int): Real データに適用される二値化処理の二値化閾値

        Returns:
            int: Real データに適用される二値化処理の二値化閾値
        """
        return self.__real_bin_threshold


    @real_bin_threshold.setter
    def real_bin_threshold(self, val: int) -> None:
        if not isinstance(val, int):
            msg = f"Real Binarization Threshold must be an integer.  {val} was set."
            log_error(msg, *self.__loggers)
            raise ValueError(msg)

        self.__real_bin_threshold = val


    @property
    def i_reduction_op(self) -> ReductionOperation:
        """I データに適用されるリダクション処理の種類

        Args:
            val (ReductionOperation): I データに適用されるリダクション処理の種類

        Returns:
            ReductionOperation: I データに適用されるリダクション処理の種類
        """
        return self.__i_reduction_op


    @i_reduction_op.setter
    def i_reduction_op(self, val: ReductionOperation) -> None:
        if not isinstance(val, ReductionOperation):
            msg = f"Invalid I Reduction Operation  {val}"
            log_error(msg, *self.__loggers)
            raise ValueError(msg)

        self.__i_reduction_op = val


    @property
    def q_reduction_op(self) -> ReductionOperation:
        """Q データに適用されるリダクション処理の種類

        Args:
            val (ReductionOperation): Q データに適用されるリダクション処理の種類

        Returns:
            ReductionOperation: Q データに適用されるリダクション処理の種類
        """
        return self.__q_reduction_op


    @q_reduction_op.setter
    def q_reduction_op(self, val: ReductionOperation) -> None:
        if not isinstance(val, ReductionOperation):
            msg = f"Invalid Q Reduction Operation  {val}"
            log_error(msg, *self.__loggers)
            raise ValueError(msg)

        self.__q_reduction_op = val


    @property
    def real_reduction_op(self) -> ReductionOperation:
        """Real データに適用されるリダクション処理の種類

        Args:
            val (ReductionOperation): Real データに適用されるリダクション処理の種類

        Returns:
            ReductionOperation: Real データに適用されるリダクション処理の種類
        """
        return self.__real_reduction_op


    @real_reduction_op.setter
    def real_reduction_op(self, val: ReductionOperation) -> None:
        if not isinstance(val, ReductionOperation):
            msg = f"Invalid Real Reduction Operation  {val}"
            log_error(msg, *self.__loggers)
            raise ValueError(msg)

        self.__real_reduction_op = val
