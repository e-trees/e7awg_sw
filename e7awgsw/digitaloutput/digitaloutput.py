from __future__ import annotations

from typing_extensions import Self
from logging import Logger
from ..hwdefs import E7AwgHwType
from .doutparam import DigitalOutParams
from ..logger import get_file_logger, get_null_logger, log_error


class DigitalOutputDataList:

    def __init__(
        self,
        design_type: E7AwgHwType,
        *,
        enable_lib_log: bool = True,
        logger: Logger = get_null_logger()):
        """
        ディジタル出力モジュールが出力するビットパターンを定義するためのクラス

        Args:
            design_type (E7AwgHwType):
                | このオブジェクトで定義したビットパターンを出力するディジタル出力モジュールが含まれる e7awg_hw の種類
            enable_lib_log (bool):
                | True -> ライブラリの標準のログ機能を有効にする.
                | False -> ライブラリの標準のログ機能を無効にする.
            logger (logging.Logger): ユーザ独自のログ出力に用いる Logger オブジェクト
        """

        self.__loggers = [logger]
        if enable_lib_log:
            self.__loggers.append(get_file_logger())

        try:
            self.__validate_design_type(design_type)
            self.__dout_params: DigitalOutParams = DigitalOutParams.of(design_type) # type: ignore
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        self.__patterns: list[tuple[int, int]] = []
        self.__design_type = E7AwgHwType(design_type)


    def add(self, bits: int, time: int) -> Self:
        """出力データを追加する

        Args:
            bits (int): 出力されるビットデータ.  0 ~ 7 ビット目がディジタル出力ポートの電圧値に対応する.  0 が Lo で 1 が Hi.
            time (int):
                | bits の出力時間.  2 以上を指定すること.
                | 出力時間の単位
                |    - ZCU111 : 14.4676 [ns]
        """
        if (len(self.__patterns) == self.__dout_params.max_patterns()):
            raise ValueError('No more output patterns can be added. (max="{}")'
                             .format(self.__dout_params.max_patterns()))
        
        if not (isinstance(time, int) and
                self.__is_in_range(self.__dout_params.min_time(), self.__dout_params.max_time(), time)):
            raise ValueError(
                "Output time must be an integer between {} and {} inclusive.  '{}' was set."
                .format(self.__dout_params.min_time(), self.__dout_params.max_time(), time))

        if not isinstance(bits, int):
            raise ValueError("'bits' must be an integer.")

        self.__patterns.append((bits, time))
        return self


    def __getitem__(self, idx: int) -> tuple[int, int]:
        return self.__patterns[idx]
    

    def __len__(self) -> int:
        return len(self.__patterns)


    def __is_in_range(self, min: int, max: int, val: int) -> bool:
        return (min <= val) and (val <= max)


    def __validate_design_type(self, design_type: E7AwgHwType) -> None:
        if design_type != E7AwgHwType.ZCU111:
            raise ValueError('Invalid e7awg_hw type.  ({})'.format(design_type))


    @property
    def design_type(self) -> E7AwgHwType:
        """このオブジェクトに設定された e7awg_hw の種類
        
        Returns:
            E7AwgHwType: このオブジェクトに設定された e7awg_hw の種類
        """
        return self.__design_type
