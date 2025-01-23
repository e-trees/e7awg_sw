from __future__ import annotations

from typing import cast
from abc import ABCMeta, abstractmethod
from typing_extensions import Self
from ..hwdefs import E7AwgHwType

class RfdcParams(object, metaclass = ABCMeta):
    """各種デザインの RF Data Converter に関連するパラメータを取得するためのインタフェースを規定するクラス."""

    @classmethod
    def of(self, design_type: E7AwgHwType) -> Self:
        if design_type == E7AwgHwType.ZCU111:
            return cast(Self, RfdcParamsZcu111())
        if design_type == E7AwgHwType.ZCU111_DAC_6G:
            return cast(Self, RfdcParamsZcu111Dac6G())
        if design_type == E7AwgHwType.ZCU111_URAM_X2:
            return cast(Self, RfdcParamsZcu111UramX2())

        raise ValueError('Invalid e7awg_hw type.  ({})'.format(design_type))

    @abstractmethod
    def inf_mixer_phase(self) -> float:
        """ミキサの初期位相の下限 (degrees)"""
        pass
    
    @abstractmethod
    def sup_mixer_phase(self) -> float:
        """ミキサの初期位相の上限 (degrees)"""
        pass
    
    @abstractmethod
    def min_mixer_freq(self) -> float:
        """ミキサ周波数の最小値 (MHz)"""
        pass

    @abstractmethod
    def max_mixer_freq(self) -> float:
        """ミキサ周波数の最大値 (MHz)"""
        pass


class RfdcParamsZcu111(RfdcParams):
    """以下の構成の ZCU111 デザインの RF Data Converter のパラメータを保持するクラス
    
    | DAC : 1.10592 Gsps
    | 波形データ RAM : DRAM x1

    """
    def inf_mixer_phase(self) -> float:
        return -180
    
    def sup_mixer_phase(self) -> float:
        return 180
    
    def min_mixer_freq(self) -> float:
        return -10000

    def max_mixer_freq(self) -> float:
        return 10000


class RfdcParamsZcu111Dac6G(RfdcParams):
    """以下の構成の ZCU111 デザインの RF Data Converter のパラメータを保持するクラス
    
    | DAC : 6.51264 Gsps
    | 波形データ RAM : DRAM x1

    """
    def inf_mixer_phase(self) -> float:
        return -180
    
    def sup_mixer_phase(self) -> float:
        return 180
    
    def min_mixer_freq(self) -> float:
        return -10000

    def max_mixer_freq(self) -> float:
        return 10000


class RfdcParamsZcu111UramX2(RfdcParams):
    """以下の構成の ZCU111 デザインの RF Data Converter のパラメータを保持するクラス
    
    | DAC : 1.10592 Gsps
    | 波形データ RAM : DRAM x1, URAM x2

    """
    def inf_mixer_phase(self) -> float:
        return -180
    
    def sup_mixer_phase(self) -> float:
        return 180
    
    def min_mixer_freq(self) -> float:
        return -10000

    def max_mixer_freq(self) -> float:
        return 10000
