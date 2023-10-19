from enum import IntEnum

class DspUnit(IntEnum):
    """キャプチャユニットが持つ信号処理モジュールの列挙型"""
    COMPLEX_FIR = 0  #: 複素 FIR フィルタ
    DECIMATION = 1  #: 間引き
    REAL_FIR = 2  #: 実 FIR フィルタ
    COMPLEX_WINDOW = 3  #: 窓関数
    SUM = 4  #: 総和
    INTEGRATION = 5  #: 積算
    CLASSIFICATION = 6  #: 四値化

    @classmethod
    def all(cls):
        """信号処理モジュールの全列挙子をリストとして返す"""
        return list(DspUnit)

    @classmethod
    def includes(cls, *vals):
        units = cls.all()
        return all([val in units for val in vals])


class DecisionFunc(IntEnum):
    """四値化処理の判定式の ID"""
    U0 = 0  #: 判定式 0
    U1 = 1  #: 判定式 1

    @classmethod
    def all(cls):
        """全ての四値化処理の判定式の IDをリストとして返す"""
        return list(DecisionFunc)

    @classmethod
    def of(cls, val):
        if not cls.includes(val):
            raise ValueError("connot convert {} to DecisionFunc".format(val))
        return cls.all()[val]

    @classmethod
    def includes(cls, *vals):
        funcs = cls.all()
        return all([val in funcs for val in vals])


