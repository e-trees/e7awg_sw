from __future__ import annotations

from typing import Final, cast
from typing_extensions import Self, deprecated
from enum import IntEnum, Enum

class E7AwgHwType(Enum):
    """e7awg_hw の種類"""
    SIMPLE_MULTI: Final = 0
    ZCU111: Final       = 1
    KR260: Final        = 2


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

    # @deprecated('Use CaptureUnit.on(...) instead')
    @classmethod
    def all(cls) -> list[Self]:
        """全キャプチャユニットの ID をリストとして返す
        
        | 特定の e7awg_hw デザインに含まれるキャプチャユニットの ID を取得する目的では使わないこと.
        
        """
        return list(CaptureUnit)

    @classmethod
    def of(cls, val) -> Self:
        units = list(CaptureUnit)
        if not val in units:
            raise ValueError("Cannot convert {} to CaptureUnit".format(val))
        return cast(Self, units[val])


    # @deprecated('Use CaptureUnit.on(...).issuperset(vals) instead')
    @classmethod
    def includes(cls, *vals: int) -> bool:
        units = list(CaptureUnit)
        return all([val in units for val in vals])

    @classmethod
    def on(cls, design_type: E7AwgHwType) -> set[Self]:
        """引数で指定した e7awg_hw デザインに含まれる全てのキャプチャユニットの ID をリストに格納して返す"""
        units = set()
        if design_type == E7AwgHwType.SIMPLE_MULTI:
            units = {
                CaptureUnit.U0, CaptureUnit.U1, CaptureUnit.U2, CaptureUnit.U3, CaptureUnit.U4,
                CaptureUnit.U5, CaptureUnit.U6, CaptureUnit.U7, CaptureUnit.U8, CaptureUnit.U9 }

        return cast(set[Self], units)


class CaptureModule(IntEnum):
    """キャプチャモジュール (複数のキャプチャユニットをまとめて保持するモジュール) の列挙型"""
    U0: Final = 0
    U1: Final = 1
    U2: Final = 2
    U3: Final = 3

    # @deprecated('Use CaptureModule.on(...) instead')
    @classmethod
    def all(cls) -> list[Self]:
        """全キャプチャモジュールの ID をリストとして返す"""
        return list(CaptureModule)

    @classmethod
    def of(cls, val: int) -> Self:
        mods = list(CaptureModule)
        if not val in mods:
            raise ValueError("Cannot convert {} to CaptureModule".format(val))
        return cast(Self, mods[val])


    # @deprecated('Use CaptureModule.on(...).issuperset(vals) instead')
    @classmethod
    def includes(cls, *vals: int) -> bool:
        mods = list(CaptureModule)
        return all([val in mods for val in vals])

    @classmethod
    def on(cls, design_type: E7AwgHwType) -> set[Self]:
        """引数で指定した e7awg_hw デザインに含まれる全てのキャプチャモジュールの ID をリストに格納して返す"""
        mods = set()
        if design_type == E7AwgHwType.SIMPLE_MULTI:
            mods = { CaptureModule.U0, CaptureModule.U1, CaptureModule.U2, CaptureModule.U3 }
        
        return cast(set[Self], mods)


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

    # @deprecated('Use AWG.on(...) instead')
    @classmethod
    def all(cls) -> list[Self]:
        """全 AWG の ID をリストとして返す
        
        | 特定の e7awg_hw デザインに含まれる AWG の ID を取得する目的では使わないこと.

        """
        return list(AWG)

    @classmethod
    def of(cls, val: int) -> Self:
        awgs = list(AWG)
        if not val in awgs:
            raise ValueError("connot convert {} to AWG".format(val))
        return cast(Self, awgs[val])

    # @deprecated('Use AWG.on(...).issuperset(vals) instead')
    @classmethod
    def includes(cls, *vals: int) -> bool:
        awgs = list(AWG)
        return all([val in awgs for val in vals])
    
    @classmethod
    def on(cls, design_type: E7AwgHwType) -> set[Self]:
        """引数で指定した e7awg_hw デザインに含まれる全ての AWG の ID をリストに格納して返す"""
        awgs = set()
        if design_type == E7AwgHwType.SIMPLE_MULTI:
            awgs = {
                AWG.U0, AWG.U1, AWG.U2, AWG.U3, AWG.U4, AWG.U5, AWG.U6, AWG.U7,
                AWG.U8, AWG.U9, AWG.U10, AWG.U11, AWG.U12, AWG.U13, AWG.U14, AWG.U15 }
        
        if design_type == E7AwgHwType.KR260:
            awgs = {
                AWG.U0, AWG.U1, AWG.U2, AWG.U3, AWG.U4, AWG.U5, AWG.U6, AWG.U7,
                AWG.U8, AWG.U9, AWG.U10, AWG.U11, AWG.U12, AWG.U13, AWG.U14, AWG.U15 }
        
        if design_type == E7AwgHwType.ZCU111:
            awgs = {
                AWG.U0, AWG.U1, AWG.U2, AWG.U3, AWG.U4, AWG.U5, AWG.U6, AWG.U7 }

        return cast(set[Self], awgs)


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
    