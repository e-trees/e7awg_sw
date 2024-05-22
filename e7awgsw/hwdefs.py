from __future__ import annotations

from typing import Final
from typing_extensions import Self
from enum import IntEnum, Enum

class DspUnit(IntEnum):
    """キャプチャユニットが持つ信号処理モジュールの列挙型"""
    COMPLEX_FIR: Final    = 0 #: 複素 FIR フィルタ
    DECIMATION: Final     = 1 #: 間引き
    REAL_FIR: Final       = 2 #: 実 FIR フィルタ
    COMPLEX_WINDOW: Final = 3 #: 窓関数
    SUM: Final            = 4 #: 総和
    INTEGRATION: Final    = 5 #: 積算
    CLASSIFICATION: Final = 6 #: 四値化
    
    @classmethod
    def all(cls) -> list[Self]:
        """信号処理モジュールの全列挙子をリストとして返す"""
        return list(DspUnit)

    @classmethod
    def includes(cls, *vals: int) -> bool:
        units = cls.all()
        return all([val in units for val in vals])


class CaptureUnit(IntEnum):
    """キャプチャユニットの ID"""
    U0: Final = 0
    U1: Final = 1
    U2: Final = 2
    U3: Final = 3
    U4: Final = 4
    U5: Final = 5
    U6: Final = 6
    U7: Final = 7
    U8: Final = 8
    U9: Final = 9

    @classmethod
    def all(cls) -> list[Self]:
        """全キャプチャユニットの ID をリストとして返す"""
        return list(CaptureUnit)

    @classmethod
    def of(cls, val: int) -> Self:
        if not CaptureUnit.includes(CaptureUnit(val)):
            raise ValueError("Cannot convert {} to CaptureUnit".format(val))
        return cls.all()[val]

    @classmethod
    def includes(cls, *vals: int) -> bool:
        units = cls.all()
        return all([val in units for val in vals])


class CaptureModule(IntEnum):
    """キャプチャモジュール (複数のキャプチャユニットをまとめて保持するモジュール) の列挙型"""
    U0: Final = 0
    U1: Final = 1
    U2: Final = 2
    U3: Final = 3

    @classmethod
    def all(cls) -> list[Self]:
        """全キャプチャモジュールの ID をリストとして返す"""
        return list(CaptureModule)

    @classmethod
    def of(cls, val: int) -> Self:
        if not CaptureModule.includes(val):
            raise ValueError("Cannot convert {} to CaptureModule".format(val))
        return cls.all()[val]

    @classmethod
    def includes(cls, *vals: int) -> bool:
        mods = cls.all()
        return all([val in mods for val in vals])


class DecisionFunc(IntEnum):
    """四値化処理の判定式の ID"""
    U0: Final = 0 #: 判定式 0
    U1: Final = 1 #: 判定式 1
    
    @classmethod
    def all(cls) -> list[Self]:
        """全ての四値化処理の判定式の IDをリストとして返す"""
        return list(DecisionFunc)

    @classmethod
    def of(cls, val: int) -> Self:
        if not cls.includes(val):
            raise ValueError("connot convert {} to DecisionFunc".format(val))
        return cls.all()[val]

    @classmethod
    def includes(cls, *vals: int) -> bool:
        funcs = cls.all()
        return all([val in funcs for val in vals])


class CaptureParamElem(IntEnum):
    """キャプチャパラメータの要素"""
    DSP_UNITS: Final           = 0  #: 有効化する DSP ユニット
    CAPTURE_DELAY: Final       = 1  #: キャプチャディレイ
    NUM_INTEG_SECTIONS: Final  = 2  #: 積算区間数
    NUM_SUM_SECTIONS: Final    = 3  #: 総和区間数
    SUM_TARGET_INTERVAL: Final = 4  #: 総和区間内で総和の対象となる部分の開始位置とワード数
    SUM_SECTION_LEN: Final     = 5  #: 総和区間長
    POST_BLANK_LEN: Final      = 6  #: ポストブランク長
    COMP_FIR_COEF: Final       = 7  #: 複素 FIR フィルタの係数
    REAL_FIR_COEF: Final       = 8  #: 実数 FIR フィルタの係数
    COMP_WINDOW_COEF: Final    = 9  #: 複素窓関数の係数
    DICISION_FUNC_PARAM: Final = 10 #: 四値化処理の判別式のパラメータ
    
    @classmethod
    def all(cls) -> list[Self]:
        """キャプチャパラメータの全要素をリストとして返す"""
        return list(CaptureParamElem)

    @classmethod
    def includes(cls, *vals: int) -> bool:
        params = cls.all()
        return all([val in params for val in vals])


class AWG(IntEnum):
    """AWG の ID"""
    U0: Final  = 0 
    U1: Final  = 1 
    U2: Final  = 2 
    U3: Final  = 3 
    U4: Final  = 4 
    U5: Final  = 5 
    U6: Final  = 6 
    U7: Final  = 7 
    U8: Final  = 8 
    U9: Final  = 9 
    U10: Final = 10
    U11: Final = 11
    U12: Final = 12
    U13: Final = 13
    U14: Final = 14
    U15: Final = 15

    @classmethod
    def all(cls) -> list[Self]:
        """全 AWG の ID をリストとして返す"""
        return list(AWG)

    @classmethod
    def of(cls, val: int) -> Self:
        if not cls.includes(val):
            raise ValueError("connot convert {} to AWG".format(val))
        return cls.all()[val]

    @classmethod
    def includes(cls, *vals: int) -> bool:
        awgs = cls.all()
        return all([val in awgs for val in vals])


class FeedbackChannel(IntEnum):
    """フィードバックチャネル (フィードバック値を読み書きするチャネル) の ID"""
    U0: Final = 0
    U1: Final = 1
    U2: Final = 2
    U3: Final = 3
    U4: Final = 4
    U5: Final = 5
    U6: Final = 6
    U7: Final = 7
    U8: Final = 8
    U9: Final = 9

    @classmethod
    def all(cls) -> list[Self]:
        """全フィードバックチャネル の ID をリストとして返す"""
        return list(FeedbackChannel)

    @classmethod
    def of(cls, val: int) -> Self:
        if not cls.includes(val):
            raise ValueError("connot convert {} to FeedbackChannel".format(val))
        return cls.all()[val]

    @classmethod
    def includes(cls, *vals: int) -> bool:
        channels = cls.all()
        return all([val in channels for val in vals])


class AwgErr(Enum):
    """AWG エラーの列挙型"""

    MEM_RD: Final          = 0
    SAMPLE_SHORTAGE: Final = 1

    @classmethod
    def all(cls) -> list[AwgErr]:
        """全 AWG エラーの列挙子をリストとして返す"""
        return list(AwgErr)

    @classmethod
    def includes(cls, *vals: int) -> bool:
        errs = cls.all()
        return all([val in errs for val in vals])


class CaptureErr(Enum):
    """キャプチャユニットエラーの列挙型"""

    MEM_WR: Final   = 0
    OVERFLOW: Final = 1

    @classmethod
    def all(cls) -> list[Self]:
        """全キャプチャユニットエラーの列挙子をリストとして返す"""
        return list(CaptureErr)

    @classmethod
    def includes(cls, *vals: int) -> bool:
        errs = cls.all()
        return all([val in errs for val in vals])


class SequencerErr(Enum):
    """シーケンサエラーの列挙型"""

    CMD_FIFO_OVERFLOW: Final = 0
    ERR_FIFO_OVERFLOW: Final = 1

    @classmethod
    def all(cls) -> list[Self]:
        """全キャプチャユニットエラーの列挙子をリストとして返す"""
        return list(SequencerErr)

    @classmethod
    def includes(cls, *vals: int) -> bool:
        errs = cls.all()
        return all([val in errs for val in vals])


class FourClassifierChannel(IntEnum):
    """四値化結果チャネル (四値化結果を読み書きするチャネル) の ID"""
    U0: Final = 0
    U1: Final = 1
    U2: Final = 2
    U3: Final = 3
    U4: Final = 4
    U5: Final = 5
    U6: Final = 6
    U7: Final = 7
    U8: Final = 8
    U9: Final = 9

    @classmethod
    def all(cls) -> list[Self]:
        """全四値化結果チャネル の ID をリストとして返す"""
        return list(FourClassifierChannel)

    @classmethod
    def of(cls, val: int) -> Self:
        if not cls.includes(val):
            raise ValueError("connot convert {} to FourClassifierChannel".format(val))
        return cls.all()[val]

    @classmethod
    def includes(cls, *vals: int) -> bool:
        channels = cls.all()
        return all([val in channels for val in vals])
