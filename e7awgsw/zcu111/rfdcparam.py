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
    """ZCU111 デザインの RF Data Converter のパラメータを保持するクラス"""

    def inf_mixer_phase(self) -> float:
        return -180
    
    def sup_mixer_phase(self) -> float:
        return 180
    
    def min_mixer_freq(self) -> float:
        return -10000

    def max_mixer_freq(self) -> float:
        return 10000
