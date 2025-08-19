from enum import IntEnum

class DspUnit(IntEnum):
    """キャプチャユニットが持つ信号処理モジュールの列挙型"""
    SUM            = 0 #: 総和
    BINARIZATION   = 1 #: 二値化
    REDUCTION      = 2 #: リダクション


class ReductionOperation(IntEnum):
    """リダクション処理の種類"""
    ANY = 0  #: キャプチャターゲットに値が 1 以上のサンプルが 1 つ以上ある場合リダクション結果が 1 になる
    ALL = 1  #: キャプチャターゲットのサンプルの値が全て 1 以上の場合 1 になる
